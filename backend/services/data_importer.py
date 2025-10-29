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
                # DraftKings: FE sheet, skip row 1, row 2 as header
                df = pd.read_excel(file_obj, sheet_name="FE", header=1, skiprows=[0])

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
                }

            elif source.lower() == "draftkings":
                columns = self.DRAFTKINGS_COLUMNS
                data_types = {
                    "S": "int",
                    "Proj": "float",
                    "Ceil": "float",
                    "Flr": "float",
                    "Own": "float",
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

                    # Validate business rules
                    self.validator.validate_player_data(player)

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

            # Prepare records for insertion
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
                }
                for p in players
            ]

            # Bulk insert using raw SQL for better performance
            if insert_records:
                stmt = text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership, ceiling, floor, notes, source)
                    VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, :ceiling, :floor, :notes, :source)
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
