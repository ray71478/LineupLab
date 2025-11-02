"""
DataImporter service for parsing and importing XLSX files.

Handles parsing XLSX files from three sources (LineStar, DraftKings, ComprehensiveStats),
data validation, player normalization, and bulk insertion to database.
"""

import logging
from io import BytesIO
from typing import Optional

import pandas as pd
from fastapi import UploadFile
from sqlalchemy import delete, insert, text
from sqlalchemy.orm import Session

from backend.exceptions import DataImportError
from backend.services.player_matcher import PlayerMatcher
from backend.services.validation_service import ValidationService
from backend.services.calibration_service import CalibrationService

logger = logging.getLogger(__name__)


class DataImporter:
    """Service for importing player data from XLSX files."""

    # Column mappings for each source format
    LINESTAR_COLUMNS = {
        "Name": "name",
        "Position": "position",
        "Team": "team",
        "Salary": "salary",
        "Projected": "projection",
        "Ceiling": "ceiling",
        "Floor": "floor",
        "ProjOwn": "ownership",
        "OppRank": "opponent_rank",  # Add OppRank for categorization
    }

    DRAFTKINGS_COLUMNS = {
        "Name": "name",
        "Pos": "position",
        "T": "team",
        "S": "salary",
        "Proj": "projection",
        "Ceil": "ceiling",
        "Flr": "floor",
        "Own": "ownership",
        "Notes": "notes",
        "ID": "draftkings_id",
        "Game Info": "game_info",
        "ITT": "implied_team_total",
    }

    COMPREHENSIVE_STATS_COLUMNS = {
        "Player": "player_name",
        "Tm": "team",
        "Pos": "position",
        "Wk": "week",
        "Opp": "opponent",
        "Snaps": "snaps",
        "Snp %": "snap_pct",
        "Ratt": "rush_attempts",
        "Rsh_yds": "rush_yards",
        "Rsh_td": "rush_tds",
        "CTGT": "targets",
        "CTGT%": "target_share",
        "Rec": "receptions",
        "Rc_yds": "rec_yards",
        "Rc_td": "rec_tds",
        "Tot TD": "total_tds",
        "Touch": "touches",
        "DK Pts": "actual_points",
        "Sal": "salary",
        "P_yds": "pass_yards",
        "P_TD": "pass_tds",
        "Int": "interceptions",
        "Ratt": "rush_attempts",
        "TPRR": "tprr",
        "S Yds Q": "sack_yards_q",
        "S Yds S": "sack_yards_s",
    }

    def __init__(self, session: Session):
        """
        Initialize DataImporter.

        Args:
            session: SQLAlchemy Session for database operations
        """
        self.session = session
        self.validator = ValidationService()
        self.matcher = PlayerMatcher(session)
        self.calibration_service = CalibrationService(session)

    async def parse_xlsx(
        self, file: UploadFile, source: str
    ) -> pd.DataFrame:
        """
        Parse XLSX file and return DataFrame based on source format.

        Handles three source formats:
        - LineStar: First sheet (index 0), row 1 as header
        - DraftKings: FE sheet, skip row 1, row 2 as header
        - Comprehensive Stats: Points sheet, row 1 as header

        Args:
            file: Uploaded XLSX file
            source: Source type ('linestar', 'draftkings', 'comprehensive_stats')

        Returns:
            Parsed pandas DataFrame

        Raises:
            DataImportError: If file parsing fails
        """
        try:
            # Read file into memory
            content = await file.read()
            file_obj = BytesIO(content)

            if source.lower() == "linestar":
                # LineStar: First sheet, row 1 as header
                df = pd.read_excel(file_obj, sheet_name=0, header=0)

            elif source.lower() == "draftkings":
                # DraftKings: FE sheet, row 1 as header (row 0 contains numeric values)
                df = pd.read_excel(file_obj, sheet_name="FE", header=1)

            elif source.lower() == "comprehensive_stats":
                # Comprehensive Stats: Points sheet, row 1 as header
                df = pd.read_excel(file_obj, sheet_name="Points", header=0)

            else:
                raise DataImportError(f"Unknown source type: {source}")

            # Validate file has data
            if df.empty:
                raise DataImportError("File contains no player data")

            logger.info(f"Parsed {len(df)} rows from {source} file: {file.filename}")

            return df

        except pd.errors.ParserError as e:
            raise DataImportError(f"Failed to parse XLSX file: {str(e)}")
        except Exception as e:
            raise DataImportError(f"Error reading file: {str(e)}")

    def validate_data(
        self, df: pd.DataFrame, source: str
    ) -> pd.DataFrame:
        """
        Validate data and convert data types.

        Runs validation rules based on source format.

        Args:
            df: DataFrame to validate
            source: Source type for column validation

        Returns:
            Validated DataFrame with converted types

        Raises:
            DataImportError: If validation fails
        """
        try:
            if source.lower() == "linestar":
                columns = self.LINESTAR_COLUMNS
                data_types = {
                    "Salary": "int",
                    "Projected": "float",
                    "Ceiling": "float",
                    "Floor": "float",
                    "ProjOwn": "float",
                    "OppRank": "int",  # Opponent rank (1-32)
                }

            elif source.lower() == "draftkings":
                columns = self.DRAFTKINGS_COLUMNS
                data_types = {
                    "S": "int",
                    "Proj": "float",
                    "Ceil": "float",
                    "Flr": "float",
                    "Own": "float",
                    "ID": "int",
                    "ITT": "float",
                }

            elif source.lower() == "comprehensive_stats":
                columns = self.COMPREHENSIVE_STATS_COLUMNS
                data_types = {
                    "Wk": "int",
                    "Snaps": "int",
                    "Snp %": "float",
                    "Ratt": "int",
                    "Rsh_yds": "int",
                    "Rsh_td": "int",
                    "CTGT": "float",
                    "CTGT%": "float",
                    "Rec": "int",
                    "Rc_yds": "int",
                    "Rc_td": "int",
                    "Tot TD": "int",
                    "Touch": "float",
                    "DK Pts": "float",
                    "Sal": "int",
                }

            else:
                raise DataImportError(f"Unknown source type: {source}")

            # For comprehensive stats, only require core columns (optional columns will be handled gracefully)
            if source.lower() == "comprehensive_stats":
                required_columns = ["Player", "Tm", "Pos", "Wk"]
            elif source.lower() == "draftkings":
                # DraftKings: Core columns required, Game Info is optional (used for opponent extraction)
                required_columns = ["Name", "Pos", "T", "S", "Proj", "Ceil", "Flr", "Own"]
            else:
                required_columns = list(columns.keys())

            # Validate required columns exist
            self.validator.validate_columns(df, required_columns)

            # Validate and convert data types
            self.validator.validate_data_types(df, data_types)

            logger.info(f"Validated {len(df)} rows for {source}")

            return df

        except Exception as e:
            raise DataImportError(f"Data validation failed: {str(e)}")

    def normalize_players(
        self, df: pd.DataFrame, source: str
    ) -> list[dict]:
        """
        Normalize player data and generate player keys.

        Converts DataFrame rows to dictionaries with normalized player keys
        and validates business rules.

        Args:
            df: Validated DataFrame
            source: Source type for column mapping

        Returns:
            List of normalized player dictionaries

        Raises:
            DataImportError: If normalization fails
        """
        try:
            if source.lower() == "linestar":
                columns = self.LINESTAR_COLUMNS
            elif source.lower() == "draftkings":
                columns = self.DRAFTKINGS_COLUMNS
            elif source.lower() == "comprehensive_stats":
                columns = self.COMPREHENSIVE_STATS_COLUMNS
            else:
                raise DataImportError(f"Unknown source type: {source}")

            # Rename columns to normalized names
            df_normalized = df.rename(columns=columns)

            # Convert to list of dictionaries
            players = []
            for _, row in df_normalized.iterrows():
                player = {col: row.get(col) for col in columns.values()}

                # Skip rows with missing critical data
                # Different sources use different keys for player name
                name_key = "player_name" if source.lower() == "comprehensive_stats" else "name"
                if pd.isna(player.get(name_key)):
                    logger.warning(f"Skipping player with missing {name_key}")
                    continue

                # Convert NaN to None
                player = {k: (None if pd.isna(v) else v) for k, v in player.items()}

                # For player pools: process salary
                if source.lower() in ["linestar", "draftkings"]:
                    # Ensure salary is an integer (store as-is from file)
                    if player.get("salary") is not None:
                        player["salary"] = int(player["salary"])

                    # Generate player_key for player pools
                    player["player_key"] = self.matcher.generate_player_key(
                        player["name"], player["team"], player["position"]
                    )

                    # DraftKings-specific processing: extract opponent and game_time from game_info
                    if source.lower() == "draftkings":
                        game_info = player.get("game_info")
                        if game_info and isinstance(game_info, str):
                            # Parse Game Info: 'CAR@GB  01:00PM' -> Away: CAR, Home: GB
                            parts = game_info.split('@')
                            if len(parts) == 2:
                                away_team = parts[0].strip()
                                rest = parts[1].split()
                                home_team = rest[0].strip() if rest else None
                                game_time = rest[1] if len(rest) > 1 else None

                                # Determine opponent based on player's team
                                player_team = player.get("team")
                                if player_team and home_team and away_team:
                                    if player_team == home_team:
                                        player["opponent"] = away_team
                                    elif player_team == away_team:
                                        player["opponent"] = home_team
                                    else:
                                        player["opponent"] = None
                                    player["game_time"] = game_time
                                else:
                                    player["opponent"] = None
                                    player["game_time"] = None
                            else:
                                player["opponent"] = None
                                player["game_time"] = None
                        else:
                            player["opponent"] = None
                            player["game_time"] = None

                        # Ensure draftkings_id is integer if present
                        if player.get("draftkings_id") is not None:
                            try:
                                player["draftkings_id"] = int(player["draftkings_id"])
                            except (ValueError, TypeError):
                                player["draftkings_id"] = None

                        # Ensure implied_team_total is float if present
                        if player.get("implied_team_total") is not None:
                            try:
                                player["implied_team_total"] = float(player["implied_team_total"])
                            except (ValueError, TypeError):
                                player["implied_team_total"] = None

                    # Categorize opponent rank (LineStar only)
                    if source.lower() == "linestar":
                        opp_rank = player.get("opponent_rank")
                        player["opponent_rank_category"] = self._categorize_opponent_rank(opp_rank)
                    else:
                        player["opponent_rank_category"] = None

                    # Set projection_source based on source
                    # For DraftKings, we'll default to LineStar unless ETR is specified
                    # ETR can be specified via a parameter, but for now default to source name
                    if source.lower() == "linestar":
                        player["projection_source"] = "LineStar"
                    elif source.lower() == "draftkings":
                        # Default to LineStar for DraftKings imports (can be overridden to ETR)
                        player["projection_source"] = "LineStar"
                    else:
                        player["projection_source"] = None

                    # Validate business rules
                    self.validator.validate_player_data(player)

                    # Append player to list
                    players.append(player)

                # For historical stats: generate player_key differently
                elif source.lower() == "comprehensive_stats":
                    # Use original name (not normalized) for historical stats
                    player["player_key"] = self.matcher.generate_player_key(
                        player["player_name"], player["team"], player["position"]
                    )

                    players.append(player)

            logger.info(f"Normalized {len(players)} players for {source}")

            return players

        except Exception as e:
            raise DataImportError(f"Player normalization failed: {str(e)}")

    def bulk_insert_player_pools(
        self,
        players: list[dict],
        week_id: int,
        source: str,
        delete_existing: bool = False,
        delete_all_sources: bool = False,
    ) -> int:
        """
        Bulk insert players into player_pools table.

        Applies calibration before insertion if active calibration exists for the week.
        Optionally deletes existing data before insertion based on source type:
        - LineStar: Delete only LineStar data for this week
        - DraftKings: Delete ALL data for this week (replaces LineStar)

        Args:
            players: List of normalized player dictionaries
            week_id: Week ID for insertion
            source: Source type ('LineStar' or 'DraftKings')
            delete_existing: If True, delete existing LineStar data for week
            delete_all_sources: If True, delete ALL data for week regardless of source

        Returns:
            Number of rows inserted

        Raises:
            DataImportError: If insertion fails
        """
        try:
            # Apply calibration to players before insertion
            try:
                players = self.calibration_service.apply_calibration(
                    players, week_id, self.session
                )
                logger.info(f"Applied calibration to players for week {week_id}")
            except Exception as e:
                logger.error(f"Calibration application failed: {str(e)}")
                # Continue with import without calibration - set default values
                for player in players:
                    player['projection_floor_original'] = player.get('floor')
                    player['projection_median_original'] = player.get('projection')
                    player['projection_ceiling_original'] = player.get('ceiling')
                    player['projection_floor_calibrated'] = player.get('floor')
                    player['projection_median_calibrated'] = player.get('projection')
                    player['projection_ceiling_calibrated'] = player.get('ceiling')
                    player['calibration_applied'] = False

            # Delete existing data if requested
            if delete_all_sources:
                # DraftKings: Delete ALL players for this week
                delete_stmt = delete(
                    text("player_pools")
                ).where(text("week_id = :week_id"))
                self.session.execute(delete_stmt, {"week_id": week_id})
                logger.info(f"Deleted all existing players for week {week_id}")

            elif delete_existing:
                # LineStar: Delete only LineStar data for this week
                delete_stmt = delete(text("player_pools")).where(
                    text("week_id = :week_id AND source = :source")
                )
                self.session.execute(
                    delete_stmt, {"week_id": week_id, "source": source}
                )
                logger.info(
                    f"Deleted existing {source} players for week {week_id}"
                )

            # Prepare records for insertion with calibrated columns
            insert_records = [
                {
                    "week_id": week_id,
                    "player_key": p.get("player_key"),
                    "name": p.get("name"),
                    "team": p.get("team"),
                    "position": p.get("position"),
                    "salary": p.get("salary"),
                    "projection": p.get("projection"),
                    "ownership": p.get("ownership"),
                    "ceiling": p.get("ceiling"),
                    "floor": p.get("floor"),
                    "notes": p.get("notes"),
                    "source": source,
                    "projection_source": p.get("projection_source"),
                    "opponent_rank_category": p.get("opponent_rank_category"),
                    "projection_floor_original": p.get("projection_floor_original"),
                    "projection_floor_calibrated": p.get("projection_floor_calibrated"),
                    "projection_median_original": p.get("projection_median_original"),
                    "projection_median_calibrated": p.get("projection_median_calibrated"),
                    "projection_ceiling_original": p.get("projection_ceiling_original"),
                    "projection_ceiling_calibrated": p.get("projection_ceiling_calibrated"),
                    "calibration_applied": p.get("calibration_applied", False),
                }
                for p in players
            ]

            # Bulk insert using raw SQL for better performance
            if insert_records:
                stmt = text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership,
                     ceiling, floor, notes, source, projection_source, opponent_rank_category,
                     projection_floor_original, projection_floor_calibrated,
                     projection_median_original, projection_median_calibrated,
                     projection_ceiling_original, projection_ceiling_calibrated,
                     calibration_applied)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary,
                            :projection, :ownership, :ceiling, :floor, :notes, :source,
                            :projection_source, :opponent_rank_category,
                            :projection_floor_original, :projection_floor_calibrated,
                            :projection_median_original, :projection_median_calibrated,
                            :projection_ceiling_original, :projection_ceiling_calibrated,
                            :calibration_applied)
                """)

                for record in insert_records:
                    try:
                        self.session.execute(stmt, record)
                    except Exception as e:
                        logger.warning(
                            f"Failed to insert player {record.get('name')}: {str(e)}"
                        )

            self.session.flush()

            logger.info(
                f"Bulk inserted {len(insert_records)} players for week {week_id}"
            )

            return len(insert_records)

        except Exception as e:
            raise DataImportError(f"Bulk insert failed: {str(e)}")

    def bulk_insert_historical_stats(self, records: list[dict]) -> int:
        """
        Bulk insert records into historical_stats table.

        Args:
            records: List of stat record dictionaries

        Returns:
            Number of rows inserted

        Raises:
            DataImportError: If insertion fails
        """
        try:
            if not records:
                return 0

            # Bulk insert using raw SQL
            stmt = text("""
                INSERT INTO historical_stats
                (player_key, week, season, team, opponent, snaps, snap_pct,
                 rush_attempts, rush_yards, rush_tds, targets, target_share,
                 receptions, rec_yards, rec_tds, total_tds, touches, actual_points, salary)
                VALUES (:player_key, :week, :season, :team, :opponent, :snaps, :snap_pct,
                        :rush_attempts, :rush_yards, :rush_tds, :targets, :target_share,
                        :receptions, :rec_yards, :rec_tds, :total_tds, :touches, :actual_points, :salary)
            """)

            for record in records:
                try:
                    self.session.execute(stmt, record)
                except Exception as e:
                    logger.warning(
                        f"Failed to insert stat record for "
                        f"{record.get('player_key')} week {record.get('week')}: {str(e)}"
                    )

            self.session.flush()

            logger.info(f"Bulk inserted {len(records)} historical stat records")

            return len(records)

        except Exception as e:
            raise DataImportError(f"Historical stats bulk insert failed: {str(e)}")

    def _categorize_opponent_rank(self, opp_rank: Optional[int]) -> str:
        """
        Categorize opponent defensive rank into top_5, middle, bottom_5.

        Args:
            opp_rank: Opponent rank (1-32, where 1 is best defense)

        Returns:
            Category string: "top_5", "middle", or "bottom_5"
        """
        if opp_rank is None:
            return "middle"

        # Rank 1-5 = top_5 (best defenses)
        if opp_rank <= 5:
            return "top_5"
        # Rank 28-32 = bottom_5 (worst defenses)
        elif opp_rank >= 28:
            return "bottom_5"
        # Everything else is middle
        else:
            return "middle"
