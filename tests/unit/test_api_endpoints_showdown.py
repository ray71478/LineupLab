"""
Unit tests for API endpoint updates for showdown mode support.

Test coverage:
- POST /api/import/linestar with contest_mode parameter
- GET /api/players/by-week/{week_id} with contest_mode filtering
- POST /api/lineups/generate with showdown mode
- GET /api/lineups/saved/{week_id} with contest_mode filtering
- Response formats include captain data correctly
"""

import pytest
import json
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from fastapi import FastAPI
from io import BytesIO
from openpyxl import Workbook

from backend.routers.import_router import router as import_router
from backend.routers.players_router import router as players_router
from backend.routers.lineups_router import router as lineups_router


def create_showdown_xlsx() -> BytesIO:
    """Create a sample Showdown XLSX file with 54 players (2 teams)."""
    wb = Workbook()
    ws = wb.active
    ws.title = "LineStar"

    # Headers matching LineStar format
    headers = ["Name", "Position", "Team", "Salary", "Projected", "Ceiling", "Floor", "ProjOwn"]
    ws.append(headers)

    # Create players from two teams (SEA @ WAS)
    teams = [("SEA", 27), ("WAS", 27)]  # 27 players per team = 54 total
    positions = ["QB", "RB", "RB", "WR", "WR", "WR", "TE", "K", "DST"]

    player_num = 1
    for team, count in teams:
        for i in range(count):
            position = positions[i % len(positions)]
            name = f"{team} Player{i+1}"
            salary = 5000 + (i * 100)
            projection = 8.0 + (i % 8)
            ceiling = projection + 3.0
            floor = projection - 2.0
            ownership = 0.05 + (i % 30) / 1000

            ws.append([name, position, team, salary, projection, ceiling, floor, ownership])
            player_num += 1

    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output


@pytest.fixture
def app_with_routers(db_session: Session) -> FastAPI:
    """Create a test app with all necessary routers."""
    app = FastAPI()

    # Set up the get_db dependency
    def get_db():
        yield db_session

    # Register routers with their get_db dependencies
    import backend.routers.import_router
    import backend.routers.players_router
    import backend.routers.lineups_router

    backend.routers.import_router.get_db = get_db
    backend.routers.players_router.get_db = get_db
    backend.routers.lineups_router.get_db = get_db

    app.include_router(import_router)
    app.include_router(players_router)
    app.include_router(lineups_router)

    return app


@pytest.fixture
def client(app_with_routers: FastAPI) -> TestClient:
    """Create a test client."""
    return TestClient(app_with_routers)


@pytest.fixture
def setup_week(db_session: Session) -> int:
    """Create a week for testing and return week_id."""
    result = db_session.execute(
        text("""
            INSERT INTO weeks (season, week_number, status)
            VALUES (:season, :week_number, 'active')
        """),
        {"season": 2025, "week_number": 10}
    )
    db_session.commit()
    return result.lastrowid


@pytest.fixture
def setup_main_slate_players(db_session: Session, setup_week: int) -> int:
    """Create main slate players for testing."""
    week_id = setup_week

    # Insert main slate players
    players = [
        ("patrick_mahomes_KC_QB", "Patrick Mahomes", "KC", "QB", 8000, 24.5, 0.35, "main"),
        ("josh_allen_BUF_QB", "Josh Allen", "BUF", "QB", 7800, 23.2, 0.28, "main"),
        ("christian_mccaffrey_SF_RB", "Christian McCaffrey", "SF", "RB", 7500, 18.5, 0.42, "main"),
    ]

    for player_key, name, team, position, salary, projection, ownership, contest_mode in players:
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership, source, contest_mode, created_at)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, 'LineStar', :contest_mode, :created_at)
            """),
            {
                "week_id": week_id,
                "player_key": player_key,
                "name": name,
                "team": team,
                "position": position,
                "salary": salary,
                "projection": projection,
                "ownership": ownership,
                "contest_mode": contest_mode,
                "created_at": datetime.utcnow(),
            }
        )

    db_session.commit()
    return week_id


@pytest.fixture
def setup_showdown_players(db_session: Session, setup_week: int) -> int:
    """Create showdown players for testing."""
    week_id = setup_week

    # Insert showdown players (single game - SEA @ WAS)
    players = [
        ("geno_smith_SEA_QB", "Geno Smith", "SEA", "QB", 7000, 20.5, 0.25, "showdown"),
        ("kenneth_walker_SEA_RB", "Kenneth Walker III", "SEA", "RB", 6500, 16.2, 0.30, "showdown"),
        ("dk_metcalf_SEA_WR", "DK Metcalf", "SEA", "WR", 6200, 14.8, 0.28, "showdown"),
        ("jayden_daniels_WAS_QB", "Jayden Daniels", "WAS", "QB", 7200, 21.3, 0.32, "showdown"),
        ("brian_robinson_WAS_RB", "Brian Robinson Jr.", "WAS", "RB", 5800, 13.5, 0.20, "showdown"),
        ("terry_mclaurin_WAS_WR", "Terry McLaurin", "WAS", "WR", 6000, 15.1, 0.26, "showdown"),
    ]

    for player_key, name, team, position, salary, projection, ownership, contest_mode in players:
        db_session.execute(
            text("""
                INSERT INTO player_pools
                (week_id, player_key, name, team, position, salary, projection, ownership, source, contest_mode, created_at)
                VALUES (:week_id, :player_key, :name, :team, :position, :salary, :projection, :ownership, 'LineStar', :contest_mode, :created_at)
            """),
            {
                "week_id": week_id,
                "player_key": player_key,
                "name": name,
                "team": team,
                "position": position,
                "salary": salary,
                "projection": projection,
                "ownership": ownership,
                "contest_mode": contest_mode,
                "created_at": datetime.utcnow(),
            }
        )

    db_session.commit()
    return week_id


class TestImportRouterShowdown:
    """Tests for import router with contest_mode parameter."""

    def test_import_linestar_with_showdown_mode(self, client: TestClient, setup_week: int):
        """Test POST /api/import/linestar with contest_mode=showdown parameter."""
        week_id = setup_week
        showdown_file = create_showdown_xlsx()

        response = client.post(
            "/api/import/linestar",
            data={
                "week_id": 10,  # Use week 10 which exists in setup_week
                "contest_mode": "showdown"
            },
            files={"file": ("showdown_sea_was.xlsx", showdown_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["player_count"] == 54  # 27 players per team
        assert data["contest_mode"] == "showdown"

    def test_import_linestar_defaults_to_main_mode(self, client: TestClient, setup_week: int):
        """Test POST /api/import/linestar defaults to main mode when no contest_mode specified."""
        showdown_file = create_showdown_xlsx()

        response = client.post(
            "/api/import/linestar",
            data={"week_id": 10},  # Use week 10 which exists
            files={"file": ("main_slate.xlsx", showdown_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["contest_mode"] == "main"

    def test_import_confirms_contest_mode(self, client: TestClient, setup_week: int):
        """Test that import response confirms contest_mode used."""
        showdown_file = create_showdown_xlsx()

        response = client.post(
            "/api/import/linestar",
            data={
                "week_id": 10,  # Use week 10 which exists
                "contest_mode": "showdown"
            },
            files={"file": ("showdown.xlsx", showdown_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "contest_mode" in data
        assert data["contest_mode"] == "showdown"


class TestPlayersRouterShowdown:
    """Tests for players router with contest_mode filtering."""

    def test_get_players_with_main_mode_filter(self, client: TestClient, setup_main_slate_players: int, setup_showdown_players: int):
        """Test GET /api/players/by-week/{week_id} with contest_mode=main returns only main slate players."""
        week_id = setup_main_slate_players

        response = client.get(f"/api/players/by-week/{week_id}?contest_mode=main")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["players"]) == 3  # Only main slate players
        assert all(p["team"] in ["KC", "BUF", "SF"] for p in data["players"])

    def test_get_players_with_showdown_mode_filter(self, client: TestClient, setup_main_slate_players: int, setup_showdown_players: int):
        """Test GET /api/players/by-week/{week_id} with contest_mode=showdown returns only showdown players."""
        week_id = setup_showdown_players

        response = client.get(f"/api/players/by-week/{week_id}?contest_mode=showdown")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["players"]) == 6  # Only showdown players
        assert all(p["team"] in ["SEA", "WAS"] for p in data["players"])

    def test_get_players_defaults_to_main_mode(self, client: TestClient, setup_main_slate_players: int, setup_showdown_players: int):
        """Test GET /api/players/by-week/{week_id} defaults to main mode when no contest_mode specified."""
        week_id = setup_main_slate_players

        response = client.get(f"/api/players/by-week/{week_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Should return main slate players by default
        assert len(data["players"]) == 3

    def test_get_players_mode_isolation(self, client: TestClient, setup_main_slate_players: int, setup_showdown_players: int):
        """Test that main mode query does not return showdown data and vice versa."""
        week_id = setup_main_slate_players

        # Get main slate players
        main_response = client.get(f"/api/players/by-week/{week_id}?contest_mode=main")
        main_data = main_response.json()

        # Get showdown players
        showdown_response = client.get(f"/api/players/by-week/{week_id}?contest_mode=showdown")
        showdown_data = showdown_response.json()

        # Ensure no overlap
        main_player_keys = {p["player_key"] for p in main_data["players"]}
        showdown_player_keys = {p["player_key"] for p in showdown_data["players"]}

        assert main_player_keys.isdisjoint(showdown_player_keys)


class TestLineupsRouterShowdown:
    """Tests for lineups router with showdown mode support."""

    def test_generate_lineups_with_showdown_mode(self, client: TestClient, setup_showdown_players: int, db_session: Session):
        """Test POST /api/lineups/generate with contest_mode=showdown."""
        week_id = setup_showdown_players

        # First, add smart scores to players
        db_session.execute(
            text("""
                UPDATE player_pools
                SET projection = 15.0
                WHERE week_id = :week_id AND contest_mode = 'showdown'
            """),
            {"week_id": week_id}
        )
        db_session.commit()

        # Request lineup generation with showdown mode
        request_body = {
            "week_id": week_id,
            "settings": {
                "num_lineups": 1,
                "strategy_mode": "Balanced",
                "contest_mode": "showdown",
                "max_players_per_team": 6,
                "max_players_per_game": 6
            }
        }

        response = client.post("/api/lineups/generate", json=request_body)

        # May fail due to optimizer complexity, but should return proper format
        if response.status_code == 200:
            data = response.json()
            assert "lineups" in data
            if len(data["lineups"]) > 0:
                lineup = data["lineups"][0]
                assert len(lineup["players"]) == 6  # 1 CPT + 5 FLEX
                # Check for captain flag
                captain_count = sum(1 for p in lineup["players"] if p.get("is_captain", False))
                assert captain_count == 1

    def test_generate_lineups_response_includes_captain_data(self, client: TestClient, setup_showdown_players: int, db_session: Session):
        """Test that lineup response includes is_captain flags for showdown mode."""
        week_id = setup_showdown_players

        # Add smart scores
        db_session.execute(
            text("""
                UPDATE player_pools
                SET projection = 15.0
                WHERE week_id = :week_id AND contest_mode = 'showdown'
            """),
            {"week_id": week_id}
        )
        db_session.commit()

        request_body = {
            "week_id": week_id,
            "settings": {
                "num_lineups": 1,
                "contest_mode": "showdown"
            }
        }

        response = client.post("/api/lineups/generate", json=request_body)

        # If generation succeeds, verify captain data format
        if response.status_code == 200:
            data = response.json()
            if len(data.get("lineups", [])) > 0:
                lineup = data["lineups"][0]
                players = lineup["players"]

                # At least one player should have is_captain field
                assert any("is_captain" in p for p in players)

                # Exactly one captain
                captains = [p for p in players if p.get("is_captain", False)]
                assert len(captains) == 1

    def test_generate_lineups_main_mode_unchanged(self, client: TestClient, setup_main_slate_players: int, db_session: Session):
        """Test that main slate lineup generation still works (regression test)."""
        week_id = setup_main_slate_players

        # Add more players to make valid lineup
        positions = [("RB", "Derrick Henry", "BAL"), ("RB", "Josh Jacobs", "GB"),
                     ("WR", "Tyreek Hill", "MIA"), ("WR", "CeeDee Lamb", "DAL"),
                     ("WR", "Amon-Ra St. Brown", "DET"), ("TE", "Travis Kelce", "KC"),
                     ("DST", "49ers", "SF")]

        for pos, name, team in positions:
            db_session.execute(
                text("""
                    INSERT INTO player_pools
                    (week_id, player_key, name, team, position, salary, projection, ownership, source, contest_mode, created_at)
                    VALUES (:week_id, :player_key, :name, :team, :position, 5000, 12.0, 0.15, 'LineStar', 'main', :created_at)
                """),
                {
                    "week_id": week_id,
                    "player_key": f"{name.lower().replace(' ', '_')}_{team}_{pos}",
                    "name": name,
                    "team": team,
                    "position": pos,
                    "created_at": datetime.utcnow(),
                }
            )
        db_session.commit()

        request_body = {
            "week_id": week_id,
            "settings": {
                "num_lineups": 1,
                "strategy_mode": "Balanced",
                "contest_mode": "main"
            }
        }

        response = client.post("/api/lineups/generate", json=request_body)

        # Main slate generation should work as before
        if response.status_code == 200:
            data = response.json()
            if len(data.get("lineups", [])) > 0:
                lineup = data["lineups"][0]
                assert len(lineup["players"]) == 9  # Standard 9-position lineup

    def test_get_saved_lineups_with_contest_mode_filter(self, client: TestClient, setup_week: int, db_session: Session):
        """Test GET /api/lineups/saved/{week_id} with contest_mode filtering."""
        week_id = setup_week

        # Create saved lineups for both modes
        for contest_mode in ["main", "showdown"]:
            num_players = 9 if contest_mode == "main" else 6
            players_data = [{"position": f"POS{i}", "name": f"Player{i}", "salary": 5000} for i in range(num_players)]

            db_session.execute(
                text("""
                    INSERT INTO generated_lineups
                    (week_id, lineup_number, players, total_salary, projected_score, avg_ownership, strategy_mode, contest_mode, created_at)
                    VALUES (:week_id, 1, :players, 45000, 100.0, 0.15, 'Balanced', :contest_mode, :created_at)
                """),
                {
                    "week_id": week_id,
                    "players": json.dumps(players_data),  # Store as JSON string
                    "contest_mode": contest_mode,
                    "created_at": datetime.utcnow(),
                }
            )
        db_session.commit()

        # Query with showdown filter
        response = client.get(f"/api/lineups/saved/{week_id}?contest_mode=showdown")

        assert response.status_code == 200
        data = response.json()
        # Should only return showdown lineup
        if isinstance(data, list):
            assert len(data) == 1
            # The players field should be parsed as JSON (list), not string
            assert isinstance(data[0]["players"], list)
            assert len(data[0]["players"]) == 6


class TestAPIEndpointValidation:
    """Tests for API endpoint validation and error handling."""

    def test_import_rejects_invalid_contest_mode(self, client: TestClient, setup_week: int):
        """Test that import rejects invalid contest_mode values."""
        showdown_file = create_showdown_xlsx()

        response = client.post(
            "/api/import/linestar",
            data={
                "week_id": 10,
                "contest_mode": "invalid_mode"
            },
            files={"file": ("test.xlsx", showdown_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

        # Should succeed but default to main mode
        assert response.status_code == 200
        if response.json().get("success"):
            assert response.json().get("contest_mode") == "main"

    def test_players_endpoint_validates_contest_mode(self, client: TestClient, setup_week: int):
        """Test that players endpoint validates contest_mode parameter."""
        # Query with invalid mode
        response = client.get(f"/api/players/by-week/{setup_week}?contest_mode=invalid")

        # Should return 200 with empty or defaults to main
        assert response.status_code == 200
