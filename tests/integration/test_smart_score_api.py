"""
Integration tests for Smart Score API endpoints.

Tests complete API workflows including calculation, profile management, and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.main import app
from backend.schemas.smart_score_schemas import WeightProfile, ScoreConfig


class TestSmartScoreAPI:
    """Integration tests for Smart Score API endpoints."""

    @pytest.fixture
    def client(self, db_session: Session):
        """Create test client with database dependency override."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides.clear()
        from backend.routers import smart_score_router
        smart_score_router.get_db = override_get_db
        
        return TestClient(app)

    @pytest.fixture
    def default_weights(self):
        """Default weight profile."""
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
        """Default config."""
        return ScoreConfig(
            projection_source="ETR",
            eighty_twenty_enabled=True,
            eighty_twenty_threshold=20.0,
        )

    @pytest.fixture
    def setup_week_and_players(self, db_session: Session):
        """Set up test week and players."""
        # Create week
        db_session.execute(
            "INSERT INTO weeks (season, week_number) VALUES (2025, 1)"
        )
        db_session.commit()
        week_id = db_session.execute("SELECT id FROM weeks LIMIT 1").scalar()
        
        # Create test players
        players_data = [
            ("QB", "DAL", 7500, 22.5, 0.15, 28.0, 18.0),
            ("RB", "SF", 8000, 18.0, 0.20, 25.0, 12.0),
            ("WR", "KC", 6500, 15.0, 0.12, 22.0, 8.0),
        ]
        
        for i, (position, team, salary, projection, ownership, ceiling, floor) in enumerate(players_data):
            db_session.execute(
                """
                INSERT INTO player_pools 
                (week_id, player_key, name, team, position, salary, projection, ownership, ceiling, floor, source, projection_source, opponent_rank_category)
                VALUES (:week_id, :key, :name, :team, :position, :salary, :projection, :ownership, :ceiling, :floor, 'LineStar', 'ETR', 'middle')
                """,
                {
                    "week_id": week_id,
                    "key": f"test_player_{i}_{position}_{team}",
                    "name": f"Test {position} {i}",
                    "team": team,
                    "position": position,
                    "salary": salary,
                    "projection": projection,
                    "ownership": ownership,
                    "ceiling": ceiling,
                    "floor": floor,
                }
            )
        
        db_session.commit()
        return week_id

    def test_get_profiles_endpoint(self, client):
        """Test GET /api/smart-score/profiles endpoint."""
        response = client.get("/api/smart-score/profiles")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "profiles" in data

    def test_create_profile_endpoint(self, client, default_weights, default_config):
        """Test POST /api/smart-score/profiles endpoint."""
        response = client.post(
            "/api/smart-score/profiles",
            json={
                "name": "Test Profile",
                "weights": default_weights.dict(),
                "config": default_config.dict(),
                "is_default": False,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Profile"

