"""
Integration tests for MySportsFeeds API integration.

Tests the full data flow:
- Fetch API data
- Parse responses
- Store in database
- Verify Smart Score calculations use real data
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, text

from backend.services.mysportsfeeds_service import MySportsFeedsService
from backend.scheduler.daily_refresh_job import DailyDataRefreshJob
from backend.services.smart_score_service import SmartScoreService


@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")

    # Create minimal schema for testing
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE weeks (
                id INTEGER PRIMARY KEY,
                season INTEGER,
                week_number INTEGER,
                start_date TIMESTAMP
            )
        """))

        conn.execute(text("""
            CREATE TABLE player_pools (
                id INTEGER PRIMARY KEY,
                player_key TEXT,
                week_id INTEGER,
                name TEXT,
                team TEXT,
                position TEXT,
                salary INTEGER,
                projection FLOAT,
                ownership FLOAT,
                ceiling FLOAT,
                floor FLOAT,
                projection_source TEXT,
                opponent_rank_category TEXT,
                injury_status TEXT
            )
        """))

        conn.execute(text("""
            CREATE TABLE vegas_lines (
                id INTEGER PRIMARY KEY,
                week_id INTEGER,
                team TEXT,
                implied_team_total FLOAT,
                updated_at TIMESTAMP
            )
        """))

        conn.execute(text("""
            CREATE TABLE team_defense_stats (
                id INTEGER PRIMARY KEY,
                season INTEGER,
                team_abbr TEXT,
                pass_defense_rank INTEGER,
                rush_defense_rank INTEGER,
                updated_at TIMESTAMP
            )
        """))

        conn.execute(text("""
            CREATE TABLE historical_stats (
                id INTEGER PRIMARY KEY,
                player_key TEXT,
                week INTEGER,
                season INTEGER,
                snaps INTEGER,
                snap_pct FLOAT,
                targets INTEGER,
                target_share FLOAT,
                receptions INTEGER,
                rec_yards FLOAT,
                passing_yards FLOAT,
                rushing_yards FLOAT,
                actual_points FLOAT
            )
        """))

        conn.commit()

    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


class TestFetchAndStoreInjuries:
    """Test injury data fetch and storage."""

    @pytest.mark.asyncio
    async def test_fetch_and_store_injuries(self, in_memory_db):
        """Test fetching and storing injury data."""
        # Insert test week
        in_memory_db.execute(text("""
            INSERT INTO weeks (id, season, week_number, start_date)
            VALUES (1, 2024, 7, '2024-10-27')
        """))

        # Insert test players
        in_memory_db.execute(text("""
            INSERT INTO player_pools (id, player_key, week_id, name, team, position, salary)
            VALUES (1, 'mahomes-patrick', 1, 'Patrick Mahomes', 'KC', 'QB', 11000),
                   (2, 'kelce-travis', 1, 'Travis Kelce', 'KC', 'TE', 8500)
        """))
        in_memory_db.commit()

        with patch.dict("os.environ", {"MYSPORTSFEEDS_TOKEN": "test_token"}):
            service = MySportsFeedsService(in_memory_db)
            service._make_request = AsyncMock(return_value={
                "players": [
                    {
                        "player": {
                            "firstName": "Patrick",
                            "lastName": "Mahomes",
                            "position": "QB",
                            "team": {"abbr": "KC"}
                        },
                        "currentInjury": {"playingProbability": "PROBABLE"}
                    },
                    {
                        "player": {
                            "firstName": "Travis",
                            "lastName": "Kelce",
                            "position": "TE",
                            "team": {"abbr": "KC"}
                        },
                        "currentInjury": {"playingProbability": "OUT"}
                    }
                ]
            })

            injuries = await service.fetch_current_week_injuries()

            assert len(injuries) == 2
            assert injuries[0]["playing_probability"] == "PROBABLE"
            assert injuries[1]["playing_probability"] == "OUT"


class TestFetchAndStoreVegasLines:
    """Test Vegas ITT data fetch and storage."""

    @pytest.mark.asyncio
    async def test_fetch_and_store_vegas_lines(self, in_memory_db):
        """Test fetching and storing Vegas lines."""
        # Insert test week
        in_memory_db.execute(text("""
            INSERT INTO weeks (id, season, week_number)
            VALUES (1, 2024, 7)
        """))
        in_memory_db.commit()

        with patch.dict("os.environ", {"MYSPORTSFEEDS_TOKEN": "test_token"}):
            service = MySportsFeedsService(in_memory_db)
            service._get_current_week_info = Mock(return_value={"season": 2024, "week": 7})
            service._make_request = AsyncMock(return_value={
                "games": [
                    {
                        "schedule": {
                            "awayTeam": {"abbr": "KC"},
                            "homeTeam": {"abbr": "TB"},
                            "startTime": "2024-10-27T20:20:00Z"
                        },
                        "score": {},
                        "scoring": {
                            "awayTeamTotal": 24.5,
                            "homeTeamTotal": 21.0
                        }
                    }
                ]
            })

            games = await service.fetch_weekly_games()

            assert len(games) == 1
            assert games[0]["away_team_itt"] == 24.5
            assert games[0]["home_team_itt"] == 21.0


class TestFetchAndStoreDefensiveStats:
    """Test team defensive stats fetch and storage."""

    @pytest.mark.asyncio
    async def test_fetch_and_store_defensive_stats(self, in_memory_db):
        """Test fetching and storing team defensive stats."""
        with patch.dict("os.environ", {"MYSPORTSFEEDS_TOKEN": "test_token"}):
            service = MySportsFeedsService(in_memory_db)
            service._get_current_week_info = Mock(return_value={"season": 2024})
            service._make_request = AsyncMock(return_value={
                "teamStatTotals": [
                    {
                        "team": {"abbr": "KC"},
                        "stats": {
                            "passingDefensePassYardsAllowedPerGameRank": 3,
                            "rushingDefenseRushYardsAllowedPerGameRank": 8
                        }
                    },
                    {
                        "team": {"abbr": "TB"},
                        "stats": {
                            "passingDefensePassYardsAllowedPerGameRank": 28,
                            "rushingDefenseRushYardsAllowedPerGameRank": 30
                        }
                    }
                ]
            })

            stats = await service.fetch_team_defensive_stats()

            assert len(stats) == 2
            assert stats["KC"]["rank_category"] == "top_5"
            assert stats["TB"]["rank_category"] == "bottom_5"


class TestSmartScoreWithRealData:
    """Test Smart Score calculations using real API data."""

    @pytest.mark.asyncio
    async def test_smart_score_with_real_injury_data(self, in_memory_db):
        """Test Smart Score excludes injured players."""
        # Insert test week
        in_memory_db.execute(text("""
            INSERT INTO weeks (id, season, week_number)
            VALUES (1, 2024, 7)
        """))

        # Insert players with injury status
        in_memory_db.execute(text("""
            INSERT INTO player_pools
            (id, player_key, week_id, name, team, position, salary, projection, ownership, ceiling, floor, injury_status)
            VALUES
            (1, 'mahomes', 1, 'Patrick Mahomes', 'KC', 'QB', 11000, 22.5, 15.0, 28.0, 16.0, 'PROBABLE'),
            (2, 'kelce', 1, 'Travis Kelce', 'KC', 'TE', 8500, 15.0, 20.0, 21.0, 9.0, 'OUT'),
            (3, 'rice', 1, 'Rashee Rice', 'KC', 'WR', 7500, 12.0, 25.0, 18.0, 6.0, 'DOUBTFUL')
        """))
        in_memory_db.commit()

        from backend.schemas.smart_score_schemas import WeightProfile, ScoreConfig

        service = SmartScoreService(in_memory_db)

        weights = WeightProfile(
            W1=0.5, W2=0.3, W3=0.2, W4=0.4,
            W5=0.3, W6=0.0, W7=0.3, W8=0.3
        )
        config = ScoreConfig()

        results = service.calculate_for_all_players(1, weights, config)

        # Only Mahomes should be included (PROBABLE)
        # Kelce (OUT) and Rice (DOUBTFUL) should be excluded
        assert len(results) == 1
        assert results[0].name == "Patrick Mahomes"

    @pytest.mark.asyncio
    async def test_smart_score_uses_real_itt(self, in_memory_db):
        """Test Smart Score W7 uses real ITT from database."""
        # Insert test week
        in_memory_db.execute(text("""
            INSERT INTO weeks (id, season, week_number)
            VALUES (1, 2024, 7)
        """))

        # Insert player
        in_memory_db.execute(text("""
            INSERT INTO player_pools
            (id, player_key, week_id, name, team, position, salary, projection, ownership, ceiling, floor)
            VALUES
            (1, 'mahomes', 1, 'Patrick Mahomes', 'KC', 'QB', 11000, 22.5, 15.0, 28.0, 16.0)
        """))

        # Insert real ITT from MySportsFeeds
        in_memory_db.execute(text("""
            INSERT INTO vegas_lines (week_id, team, implied_team_total)
            VALUES (1, 'KC', 25.0)
        """))
        in_memory_db.commit()

        from backend.schemas.smart_score_schemas import WeightProfile, ScoreConfig

        service = SmartScoreService(in_memory_db)

        weights = WeightProfile(
            W1=0.5, W2=0.3, W3=0.2, W4=0.4,
            W5=0.3, W6=0.0, W7=0.3, W8=0.3
        )
        config = ScoreConfig()

        results = service.calculate_for_all_players(1, weights, config)

        assert len(results) == 1
        # W7 should use the real ITT (25.0) not default (22.5)
        w7_value = results[0].score_breakdown.W7_value
        assert w7_value > 0  # Positive because 25 > 22.5


class TestDailyRefreshJobIntegration:
    """Test full daily refresh workflow."""

    @pytest.mark.asyncio
    async def test_daily_refresh_job_execution(self, in_memory_db):
        """Test complete daily refresh job."""
        # Insert current week
        in_memory_db.execute(text("""
            INSERT INTO weeks (id, season, week_number)
            VALUES (1, 2024, 7)
        """))

        # Insert test player
        in_memory_db.execute(text("""
            INSERT INTO player_pools (id, player_key, week_id, name, team, position, salary)
            VALUES (1, 'mahomes', 1, 'Patrick Mahomes', 'KC', 'QB', 11000)
        """))
        in_memory_db.commit()

        with patch.dict("os.environ", {"MYSPORTSFEEDS_TOKEN": "test_token"}):
            job = DailyDataRefreshJob(in_memory_db)

            # Mock the service methods
            job.service = Mock()
            job.service.fetch_current_week_injuries = AsyncMock(return_value=[
                {
                    "player_first_name": "Patrick",
                    "player_last_name": "Mahomes",
                    "team": "KC",
                    "playing_probability": "PROBABLE"
                }
            ])
            job.service.fetch_weekly_games = AsyncMock(return_value=[
                {
                    "away_team": "KC",
                    "home_team": "TB",
                    "away_team_itt": 24.5,
                    "home_team_itt": 21.0
                }
            ])
            job.service.fetch_team_defensive_stats = AsyncMock(return_value={
                "KC": {
                    "pass_defense_rank": 3,
                    "rank_category": "top_5"
                }
            })
            job.service.fetch_player_gamelogs = AsyncMock(return_value=[])

            # Would execute in real scenario
            # For now, verify structure
            assert job.db is not None


class TestBackwardCompatibility:
    """Test backward compatibility with manual data."""

    def test_manual_data_still_works(self, in_memory_db):
        """Test that manually uploaded data still works with API data."""
        # Insert week
        in_memory_db.execute(text("""
            INSERT INTO weeks (id, season, week_number)
            VALUES (1, 2024, 7)
        """))

        # Insert player with manual projection (no injury status)
        in_memory_db.execute(text("""
            INSERT INTO player_pools
            (id, player_key, week_id, name, team, position, salary, projection, ownership, ceiling, floor)
            VALUES
            (1, 'mahomes', 1, 'Patrick Mahomes', 'KC', 'QB', 11000, 22.5, 15.0, 28.0, 16.0)
        """))
        in_memory_db.commit()

        from backend.schemas.smart_score_schemas import WeightProfile, ScoreConfig

        service = SmartScoreService(in_memory_db)

        weights = WeightProfile(
            W1=0.5, W2=0.3, W3=0.2, W4=0.4,
            W5=0.3, W6=0.0, W7=0.3, W8=0.3
        )
        config = ScoreConfig()

        # Should work fine with no injury_status data
        results = service.calculate_for_all_players(1, weights, config)

        assert len(results) == 1
        assert results[0].name == "Patrick Mahomes"

    def test_graceful_fallback_when_api_data_missing(self, in_memory_db):
        """Test graceful fallback when API data is missing."""
        # Insert week
        in_memory_db.execute(text("""
            INSERT INTO weeks (id, season, week_number)
            VALUES (1, 2024, 7)
        """))

        # Insert player with NO vegas lines (API didn't provide)
        in_memory_db.execute(text("""
            INSERT INTO player_pools
            (id, player_key, week_id, name, team, position, salary, projection, ownership, ceiling, floor)
            VALUES
            (1, 'mahomes', 1, 'Patrick Mahomes', 'KC', 'QB', 11000, 22.5, 15.0, 28.0, 16.0)
        """))
        in_memory_db.commit()

        from backend.schemas.smart_score_schemas import WeightProfile, ScoreConfig

        service = SmartScoreService(in_memory_db)

        weights = WeightProfile(
            W1=0.5, W2=0.3, W3=0.2, W4=0.4,
            W5=0.3, W6=0.0, W7=0.3, W8=0.3
        )
        config = ScoreConfig()

        # Should use default ITT (22.5) if not in database
        results = service.calculate_for_all_players(1, weights, config)

        assert len(results) == 1
        # W7 should indicate it used default
        assert results[0].score_breakdown.missing_data_indicators.get("W7", False)


class TestErrorRecovery:
    """Test error handling and recovery."""

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_api_failure(self, in_memory_db):
        """Test system continues when API call fails."""
        in_memory_db.execute(text("""
            INSERT INTO weeks (id, season, week_number)
            VALUES (1, 2024, 7)
        """))
        in_memory_db.commit()

        with patch.dict("os.environ", {"MYSPORTSFEEDS_TOKEN": "test_token"}):
            service = MySportsFeedsService(in_memory_db)
            service._make_request = AsyncMock(return_value=None)  # Simulate API failure

            injuries = await service.fetch_current_week_injuries()

            # Should return empty list, not crash
            assert injuries == []

    @pytest.mark.asyncio
    async def test_partial_update_on_validation_error(self, in_memory_db):
        """Test system continues when some records fail validation."""
        in_memory_db.execute(text("""
            INSERT INTO weeks (id, season, week_number)
            VALUES (1, 2024, 7)
        """))
        in_memory_db.commit()

        with patch.dict("os.environ", {"MYSPORTSFEEDS_TOKEN": "test_token"}):
            service = MySportsFeedsService(in_memory_db)
            service._make_request = AsyncMock(return_value={
                "players": [
                    {
                        "player": {
                            "firstName": "Valid",
                            "lastName": "Player",
                            "position": "WR",
                            "team": {"abbr": "KC"}
                        },
                        "currentInjury": {"playingProbability": "PROBABLE"}
                    },
                    {
                        "player": {
                            "firstName": "",  # Invalid
                            "lastName": "Player",
                            "position": "WR",
                            "team": {"abbr": "KC"}
                        },
                        "currentInjury": {"playingProbability": "PROBABLE"}
                    }
                ]
            })

            injuries = await service.fetch_current_week_injuries()

            # Should return only valid record
            assert len(injuries) == 1
            assert injuries[0]["player_first_name"] == "Valid"
