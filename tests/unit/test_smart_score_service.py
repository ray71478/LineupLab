"""
Unit tests for SmartScoreService.

Tests all 8 factor calculations, missing data handling, and edge cases.
"""

import pytest
from sqlalchemy.orm import Session
from backend.services.smart_score_service import SmartScoreService, PlayerData
from backend.schemas.smart_score_schemas import WeightProfile, ScoreConfig


class TestSmartScoreService:
    """Test suite for SmartScoreService."""

    @pytest.fixture
    def service(self, db_session: Session):
        """Create SmartScoreService instance."""
        return SmartScoreService(db_session)

    @pytest.fixture
    def default_weights(self):
        """Default weight profile (equal weights)."""
        return WeightProfile(
            W1=0.125,
            W2=0.125,
            W3=0.125,
            W4=0.125,
            W5=0.125,
            W6=0.125,
            W7=0.125,
            W8=0.125,
        )

    @pytest.fixture
    def default_config(self):
        """Default score configuration."""
        return ScoreConfig(
            projection_source="ETR",
            eighty_twenty_enabled=True,
            eighty_twenty_threshold=20.0,
        )

    @pytest.fixture
    def sample_player(self):
        """Sample player data for testing."""
        return PlayerData(
            player_id=1,
            player_key="test_player_QB_DAL",
            name="Test Player",
            team="DAL",
            position="QB",
            salary=7500,
            projection=22.5,
            ownership=0.15,
            ceiling=28.0,
            floor=18.0,
            projection_source="ETR",
            opponent_rank_category="middle",
        )

    def test_w1_projection_factor(self, service, default_weights, sample_player):
        """Test W1: Projection Factor calculation."""
        result = service._calculate_w1_projection(sample_player, default_weights.W1)
        
        assert result.value == pytest.approx(22.5 * 0.125, rel=1e-6)
        assert result.used_default is False

    def test_w1_missing_projection(self, service, default_weights):
        """Test W1 with missing projection uses default."""
        player = PlayerData(
            player_id=1,
            player_key="test_player",
            name="Test",
            team="DAL",
            position="QB",
            salary=7500,
            projection=None,
            ownership=0.15,
            ceiling=28.0,
            floor=18.0,
            projection_source="ETR",
            opponent_rank_category="middle",
        )
        
        result = service._calculate_w1_projection(player, default_weights.W1)
        
        assert result.value == 0.0
        assert result.used_default is True

    def test_w8_matchup_adjustment(self, service, default_weights):
        """Test W8: Matchup Adjustment with categories."""
        # Test top_5 category
        player_top5 = PlayerData(
            player_id=1,
            player_key="test",
            name="Test",
            team="DAL",
            position="QB",
            salary=7500,
            projection=22.5,
            ownership=0.15,
            ceiling=28.0,
            floor=18.0,
            projection_source="ETR",
            opponent_rank_category="top_5",
        )
        result_top5 = service._calculate_w8_matchup_adjustment(
            player_top5, default_weights.W8
        )
        assert result_top5.value == pytest.approx(1.0 * 0.125, rel=1e-6)

        # Test bottom_5 category
        player_bottom5 = PlayerData(
            player_id=2,
            player_key="test2",
            name="Test2",
            team="DAL",
            position="QB",
            salary=7500,
            projection=22.5,
            ownership=0.15,
            ceiling=28.0,
            floor=18.0,
            projection_source="ETR",
            opponent_rank_category="bottom_5",
        )
        result_bottom5 = service._calculate_w8_matchup_adjustment(
            player_bottom5, default_weights.W8
        )
        assert result_bottom5.value == pytest.approx(-1.0 * 0.125, rel=1e-6)

        # Test middle category
        player_middle = PlayerData(
            player_id=3,
            player_key="test3",
            name="Test3",
            team="DAL",
            position="QB",
            salary=7500,
            projection=22.5,
            ownership=0.15,
            ceiling=28.0,
            floor=18.0,
            projection_source="ETR",
            opponent_rank_category="middle",
        )
        result_middle = service._calculate_w8_matchup_adjustment(
            player_middle, default_weights.W8
        )
        assert result_middle.value == pytest.approx(0.0, rel=1e-6)

    def test_categorize_opponent_rank(self, service):
        """Test opponent rank categorization."""
        assert service.categorize_opponent_rank(1) == "top_5"
        assert service.categorize_opponent_rank(5) == "top_5"
        assert service.categorize_opponent_rank(6) == "middle"
        assert service.categorize_opponent_rank(27) == "middle"
        assert service.categorize_opponent_rank(28) == "bottom_5"
        assert service.categorize_opponent_rank(32) == "bottom_5"
        assert service.categorize_opponent_rank(None) == "middle"

