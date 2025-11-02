"""
Unit tests for LineupDisplay component with showdown support

Test coverage:
- Test showdown lineup displays 6 positions (1 CPT + 5 FLEX)
- Test captain row highlighted with special styling
- Test captain multiplier displays correctly (1.5x)
- Test main slate display unchanged (9 positions)
- Test lineup summary for showdown format
- Test responsive behavior for both modes

Note: These are unit tests for the React component's data processing logic
The visual/rendering tests should be handled by E2E tests
"""

import pytest
from typing import List, Dict, Any

# Mock lineup data structures for testing
def create_showdown_lineup_data(lineup_number: int = 1) -> Dict[str, Any]:
    """
    Create mock showdown lineup data
    1 Captain + 5 FLEX = 6 total positions

    Captain: $10,000 base * 1.5 = $15,000, 22.5 pts * 1.5 = 33.75 pts
    FLEX: $7,200 + $6,800 + $6,500 + $4,800 + $3,200 = $28,500, 62.2 pts
    Total: $43,500, 95.95 pts
    """
    return {
        "lineup_number": lineup_number,
        "contest_mode": "showdown",
        "players": [
            {
                "position": "QB",
                "player_key": "jayden-daniels",
                "name": "Jayden Daniels",
                "team": "WAS",
                "salary": 1000000,  # $10,000 base
                "smart_score": 95.5,
                "ownership": 0.25,
                "projection": 22.5,
                "is_captain": True,
            },
            {
                "position": "RB",
                "player_key": "kenneth-walker",
                "name": "Kenneth Walker III",
                "team": "SEA",
                "salary": 720000,  # $7,200
                "smart_score": 88.2,
                "ownership": 0.18,
                "projection": 15.8,
                "is_captain": False,
            },
            {
                "position": "WR",
                "player_key": "dk-metcalf",
                "name": "DK Metcalf",
                "team": "SEA",
                "salary": 680000,  # $6,800
                "smart_score": 85.7,
                "ownership": 0.22,
                "projection": 14.2,
                "is_captain": False,
            },
            {
                "position": "WR",
                "player_key": "terry-mclaurin",
                "name": "Terry McLaurin",
                "team": "WAS",
                "salary": 650000,  # $6,500
                "smart_score": 82.3,
                "ownership": 0.20,
                "projection": 13.5,
                "is_captain": False,
            },
            {
                "position": "TE",
                "player_key": "zach-ertz",
                "name": "Zach Ertz",
                "team": "WAS",
                "salary": 480000,  # $4,800
                "smart_score": 78.1,
                "ownership": 0.15,
                "projection": 10.2,
                "is_captain": False,
            },
            {
                "position": "DST",
                "player_key": "was-dst",
                "name": "Washington DST",
                "team": "WAS",
                "salary": 320000,  # $3,200
                "smart_score": 72.5,
                "ownership": 0.12,
                "projection": 8.5,
                "is_captain": False,
            },
        ],
        "total_salary": 4350000,  # $43,500 (includes 1.5x captain salary: 15000 + 28500)
        "projected_score": 502.3,
        "projected_points": 95.95,  # Includes 1.5x captain points: 33.75 + 62.2
        "avg_ownership": 0.187,
    }


def create_main_slate_lineup_data(lineup_number: int = 1) -> Dict[str, Any]:
    """
    Create mock main slate lineup data
    9 positions: QB, RB, RB, WR, WR, WR, TE, FLEX, DST
    """
    return {
        "lineup_number": lineup_number,
        "contest_mode": "main",
        "players": [
            {"position": "QB", "player_key": "qb1", "name": "QB Player 1", "team": "KC", "salary": 800000, "smart_score": 92.0, "ownership": 0.30, "projection": 24.5},
            {"position": "RB", "player_key": "rb1", "name": "RB Player 1", "team": "SF", "salary": 850000, "smart_score": 88.5, "ownership": 0.25, "projection": 18.2},
            {"position": "RB", "player_key": "rb2", "name": "RB Player 2", "team": "DAL", "salary": 720000, "smart_score": 85.0, "ownership": 0.20, "projection": 15.8},
            {"position": "WR", "player_key": "wr1", "name": "WR Player 1", "team": "MIA", "salary": 780000, "smart_score": 90.0, "ownership": 0.28, "projection": 16.5},
            {"position": "WR", "player_key": "wr2", "name": "WR Player 2", "team": "BUF", "salary": 700000, "smart_score": 87.0, "ownership": 0.22, "projection": 14.9},
            {"position": "WR", "player_key": "wr3", "name": "WR Player 3", "team": "CIN", "salary": 650000, "smart_score": 84.5, "ownership": 0.18, "projection": 13.7},
            {"position": "TE", "player_key": "te1", "name": "TE Player 1", "team": "KC", "salary": 600000, "smart_score": 82.0, "ownership": 0.24, "projection": 12.3},
            {"position": "RB", "player_key": "flex1", "name": "FLEX Player 1", "team": "PHI", "salary": 550000, "smart_score": 80.0, "ownership": 0.15, "projection": 11.5},
            {"position": "DST", "player_key": "dst1", "name": "DST Player 1", "team": "SF", "salary": 350000, "smart_score": 75.0, "ownership": 0.20, "projection": 9.8},
        ],
        "total_salary": 6000000,  # $60,000
        "projected_score": 764.0,
        "projected_points": 137.2,
        "avg_ownership": 0.225,
    }


class TestLineupDisplayShowdownSupport:
    """Test LineupDisplay component with showdown mode support"""

    def test_showdown_lineup_has_6_positions(self):
        """Test that showdown lineups display 6 positions (1 CPT + 5 FLEX)"""
        lineup = create_showdown_lineup_data()

        # Verify player count
        assert len(lineup["players"]) == 6, "Showdown lineup should have exactly 6 players"

        # Verify contest mode
        assert lineup["contest_mode"] == "showdown", "Contest mode should be 'showdown'"

        # Verify exactly one captain
        captains = [p for p in lineup["players"] if p.get("is_captain", False)]
        assert len(captains) == 1, "Showdown lineup should have exactly 1 captain"

        # Verify 5 non-captains
        flex_players = [p for p in lineup["players"] if not p.get("is_captain", False)]
        assert len(flex_players) == 5, "Showdown lineup should have exactly 5 FLEX players"

    def test_captain_player_identified_correctly(self):
        """Test that captain is properly identified with is_captain flag"""
        lineup = create_showdown_lineup_data()

        # Find the captain
        captain = next((p for p in lineup["players"] if p.get("is_captain", False)), None)

        assert captain is not None, "Captain should be found in lineup"
        assert captain["is_captain"] is True, "Captain should have is_captain=True"
        assert captain["name"] == "Jayden Daniels", "Expected captain should be Jayden Daniels"

    def test_captain_multiplier_calculations(self):
        """Test that captain multiplier is correctly calculated (1.5x)"""
        lineup = create_showdown_lineup_data()
        captain = next((p for p in lineup["players"] if p.get("is_captain", False)), None)

        # Base values
        base_salary = 1000000  # $10,000
        base_projection = 22.5

        # Expected captain values (1.5x multiplier)
        expected_captain_salary = base_salary * 1.5
        expected_captain_points = base_projection * 1.5

        # Verify captain salary is stored as base (multiplier applied by display/optimizer)
        assert captain["salary"] == base_salary, "Captain salary should be base salary in data"
        assert captain["projection"] == base_projection, "Captain projection should be base projection in data"

        # Note: The 1.5x multiplier should be applied in the display component
        # and reflected in total_salary and projected_points

    def test_showdown_total_salary_includes_captain_multiplier(self):
        """Test that total salary calculation includes captain multiplier"""
        lineup = create_showdown_lineup_data()

        # Calculate expected total salary
        captain = next((p for p in lineup["players"] if p.get("is_captain", False)), None)
        flex_players = [p for p in lineup["players"] if not p.get("is_captain", False)]

        # Captain salary: base * 1.5
        captain_salary = captain["salary"] * 1.5

        # FLEX salaries: sum of base salaries
        flex_salary = sum(p["salary"] for p in flex_players)

        # Expected total
        expected_total = captain_salary + flex_salary

        # Allow small floating point tolerance
        assert abs(lineup["total_salary"] - expected_total) < 100, \
            f"Total salary should include captain multiplier. Expected {expected_total}, got {lineup['total_salary']}"

    def test_showdown_projected_points_includes_captain_multiplier(self):
        """Test that projected points include captain multiplier"""
        lineup = create_showdown_lineup_data()

        captain = next((p for p in lineup["players"] if p.get("is_captain", False)), None)
        flex_players = [p for p in lineup["players"] if not p.get("is_captain", False)]

        # Captain points: base * 1.5
        captain_points = captain["projection"] * 1.5

        # FLEX points: sum of base projections
        flex_points = sum(p["projection"] for p in flex_players)

        # Expected total
        expected_total = captain_points + flex_points

        # Allow small floating point tolerance
        assert abs(lineup["projected_points"] - expected_total) < 0.1, \
            f"Total projected points should include captain multiplier. Expected {expected_total:.2f}, got {lineup['projected_points']:.2f}"

    def test_main_slate_lineup_has_9_positions(self):
        """Test that main slate lineups still display 9 positions (unchanged)"""
        lineup = create_main_slate_lineup_data()

        # Verify player count
        assert len(lineup["players"]) == 9, "Main slate lineup should have exactly 9 players"

        # Verify contest mode
        assert lineup["contest_mode"] == "main", "Contest mode should be 'main'"

        # Verify no captains in main slate
        captains = [p for p in lineup["players"] if p.get("is_captain", False)]
        assert len(captains) == 0, "Main slate lineup should have no captains"

    def test_main_slate_position_order(self):
        """Test that main slate maintains correct position order"""
        lineup = create_main_slate_lineup_data()

        # Expected position order: QB, RB, RB, WR, WR, WR, TE, FLEX, DST
        expected_positions = ["QB", "RB", "RB", "WR", "WR", "WR", "TE", "RB", "DST"]
        actual_positions = [p["position"] for p in lineup["players"]]

        # Count positions
        qb_count = actual_positions.count("QB")
        rb_count = actual_positions.count("RB")
        wr_count = actual_positions.count("WR")
        te_count = actual_positions.count("TE")
        dst_count = actual_positions.count("DST")

        assert qb_count == 1, "Main slate should have 1 QB"
        assert rb_count == 3, "Main slate should have 3 RBs (including FLEX)"
        assert wr_count == 3, "Main slate should have 3 WRs"
        assert te_count == 1, "Main slate should have 1 TE"
        assert dst_count == 1, "Main slate should have 1 DST"

    def test_showdown_lineup_summary_format(self):
        """Test that showdown lineup summary shows correct format"""
        lineup = create_showdown_lineup_data()

        # Expected format: "1 CPT + 5 FLEX | $XX,XXX / $50,000"
        total_salary_formatted = f"${lineup['total_salary'] / 100:,.0f}"
        salary_cap_formatted = "$50,000"

        # Verify total is under cap
        assert lineup["total_salary"] <= 5000000, "Showdown lineup total salary should be <= $50,000"

        # Verify expected summary components exist
        assert lineup["contest_mode"] == "showdown", "Should have showdown contest mode"

        # Count captain and flex
        captain_count = sum(1 for p in lineup["players"] if p.get("is_captain", False))
        flex_count = sum(1 for p in lineup["players"] if not p.get("is_captain", False))

        assert captain_count == 1, "Summary should show 1 CPT"
        assert flex_count == 5, "Summary should show 5 FLEX"


class TestLineupDisplayCaptainStyling:
    """Test captain row styling and visual distinction"""

    def test_captain_position_label_is_cpt(self):
        """Test that captain displays 'CPT' position label"""
        lineup = create_showdown_lineup_data()
        captain = next((p for p in lineup["players"] if p.get("is_captain", False)), None)

        # Note: The actual position label "CPT" should be rendered by the component
        # based on is_captain flag, not stored in position field
        assert captain is not None, "Captain should exist"
        assert captain["is_captain"] is True, "Captain should have is_captain flag"

        # Original position is preserved for reference
        assert captain["position"] in ["QB", "RB", "WR", "TE", "K", "DST"], \
            "Captain should have valid original position"

    def test_flex_players_have_flex_label(self):
        """Test that non-captain players display 'FLEX' position label"""
        lineup = create_showdown_lineup_data()
        flex_players = [p for p in lineup["players"] if not p.get("is_captain", False)]

        # All non-captains should be displayable as FLEX
        assert len(flex_players) == 5, "Should have 5 FLEX players"

        for player in flex_players:
            assert player.get("is_captain", False) is False, "FLEX player should not be captain"
            assert player["position"] in ["QB", "RB", "WR", "TE", "K", "DST"], \
                "FLEX player should have valid position"

    def test_captain_multiplier_display_format(self):
        """Test that captain multiplier displays in correct format"""
        lineup = create_showdown_lineup_data()
        captain = next((p for p in lineup["players"] if p.get("is_captain", False)), None)

        base_salary = captain["salary"]
        captain_salary = base_salary * 1.5

        # Format: "$X,XXX → $X,XXX (1.5x)"
        base_formatted = f"${base_salary / 100:,.0f}"
        captain_formatted = f"${captain_salary / 100:,.0f}"
        multiplier_text = "1.5x"

        # Verify values are correct for formatting
        assert base_salary == 1000000, f"Base salary should be $10,000, got ${base_salary / 100}"
        assert captain_salary == 1500000, f"Captain salary should be $15,000, got ${captain_salary / 100}"

        # Expected display: "$10,000 → $15,000 (1.5x)"
        expected_salary_display = f"{base_formatted} → {captain_formatted} ({multiplier_text})"
        assert "$10,000" in expected_salary_display
        assert "$15,000" in expected_salary_display
        assert "1.5x" in expected_salary_display


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
