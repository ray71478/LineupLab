"""
Debug script to diagnose lineup optimizer infeasibility issues.

This script will:
1. Check the actual player data being used
2. Enable verbose CBC solver output to see exact constraint failures
3. Test constraints individually to isolate the issue
"""

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = "postgresql://ray@localhost:5432/cortex"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def check_player_data(week_id=9):
    """Check the actual player data that would be used for optimization."""
    session = Session()

    try:
        # Get all players for the week with Smart Scores
        query = text("""
            WITH player_scores AS (
                SELECT
                    pp.id as player_id,
                    pp.player_key,
                    pp.name,
                    pp.team,
                    pp.position,
                    pp.salary,
                    pp.ownership,
                    pp.projection_etr,
                    pp.projection_linestar
                FROM player_pool pp
                WHERE pp.week_id = :week_id
                AND pp.is_active = TRUE
            )
            SELECT
                player_id,
                player_key,
                name,
                team,
                position,
                salary,
                ownership,
                projection_etr,
                projection_linestar,
                CASE
                    WHEN salary IS NULL THEN 'NULL_SALARY'
                    WHEN salary = 0 THEN 'ZERO_SALARY'
                    WHEN projection_etr IS NULL AND projection_linestar IS NULL THEN 'NULL_PROJECTION'
                    ELSE 'OK'
                END as data_status
            FROM player_scores
            ORDER BY position, salary DESC
        """)

        players = session.execute(query, {"week_id": week_id}).fetchall()

        print(f"\n=== PLAYER DATA CHECK FOR WEEK {week_id} ===")
        print(f"Total players: {len(players)}\n")

        # Group by position
        by_position = {}
        data_issues = []

        for p in players:
            pos = p.position
            if pos not in by_position:
                by_position[pos] = []
            by_position[pos].append(p)

            if p.data_status != 'OK':
                data_issues.append({
                    'name': p.name,
                    'position': p.position,
                    'team': p.team,
                    'issue': p.data_status,
                    'salary': p.salary,
                    'proj_etr': p.projection_etr,
                    'proj_linestar': p.projection_linestar
                })

        print("Position counts:")
        for pos in sorted(by_position.keys()):
            print(f"  {pos}: {len(by_position[pos])}")

        if data_issues:
            print(f"\n⚠️  Found {len(data_issues)} players with data issues:")
            for issue in data_issues[:10]:  # Show first 10
                print(f"  - {issue['name']} ({issue['position']}, {issue['team']}): {issue['issue']}")
                print(f"    Salary: {issue['salary']}, ETR: {issue['proj_etr']}, LineStar: {issue['proj_linestar']}")
        else:
            print("\n✓ No data issues found")

        # Check for salary distribution
        print("\nSalary distribution:")
        for pos in ['QB', 'RB', 'WR', 'TE', 'DST']:
            if pos in by_position:
                salaries = [p.salary for p in by_position[pos] if p.salary is not None]
                if salaries:
                    print(f"  {pos}: ${min(salaries)} - ${max(salaries)}")
                else:
                    print(f"  {pos}: NO VALID SALARIES!")

    finally:
        session.close()

def check_vegas_lines_data(week_id=9):
    """Check vegas lines opponent data."""
    session = Session()

    try:
        query = text("""
            SELECT team, opponent, implied_team_total, over_under
            FROM vegas_lines
            WHERE week_id = :week_id
            ORDER BY team
        """)

        lines = session.execute(query, {"week_id": week_id}).fetchall()

        print(f"\n=== VEGAS LINES CHECK FOR WEEK {week_id} ===")
        print(f"Total teams: {len(lines)}\n")

        missing_opponent = [l for l in lines if l.opponent is None]

        if missing_opponent:
            print(f"⚠️  {len(missing_opponent)} teams missing opponent data:")
            for l in missing_opponent:
                print(f"  - {l.team}: opponent=NULL")
        else:
            print("✓ All teams have opponent data")

        print("\nSample data (first 5):")
        for l in lines[:5]:
            print(f"  {l.team} vs {l.opponent}: ITT={l.implied_team_total}, O/U={l.over_under}")

    finally:
        session.close()

def test_manual_lineup_feasibility(week_id=9):
    """
    Test if the manual lineup the user provided is actually in the player pool.

    Manual lineup:
    - QB: Geno Smith
    - RB: RJ Harvey, Tyrone Tracy Jr.
    - WR: Justin Jefferson, Jayden Higgins, Jakobi Meyers
    - TE: Brock Bowers
    - FLEX: Kenneth Gainwell (RB)
    - DST: Falcons
    """
    session = Session()

    try:
        manual_players = [
            ("Geno Smith", "QB", "SEA"),
            ("RJ Harvey", "RB", None),  # Don't know team
            ("Tyrone Tracy Jr.", "RB", "NYG"),
            ("Justin Jefferson", "WR", "MIN"),
            # Try variations for Higgins
            ("Jayden Higgins", "WR", None),
            ("Tee Higgins", "WR", "CIN"),
            ("Jakobi Meyers", "WR", "LV"),
            ("Brock Bowers", "TE", "LV"),
            ("Kenneth Gainwell", "RB", "PHI"),
            ("Falcons", "DST", "ATL"),
        ]

        print(f"\n=== MANUAL LINEUP FEASIBILITY CHECK ===")
        print("Checking if user's manual lineup players exist in player pool...\n")

        found = []
        not_found = []
        total_salary = 0

        for name, pos, team in manual_players:
            query = text("""
                SELECT player_key, name, team, position, salary, ownership, projection_etr
                FROM player_pool
                WHERE week_id = :week_id
                AND LOWER(name) = LOWER(:name)
                AND position = :position
                LIMIT 1
            """)

            result = session.execute(query, {
                "week_id": week_id,
                "name": name,
                "position": pos
            }).fetchone()

            if result:
                found.append(result)
                total_salary += (result.salary or 0)
                print(f"✓ {result.name} ({result.position}, {result.team}): ${result.salary}")
            else:
                not_found.append((name, pos, team))
                print(f"✗ {name} ({pos}): NOT FOUND")

        print(f"\nTotal found: {len(found)}/9 players")
        print(f"Total salary: ${total_salary} (cap: $50,000)")

        if len(found) == 9 and total_salary <= 50000:
            print("\n✓ Manual lineup is feasible!")
        elif len(found) < 9:
            print(f"\n✗ Manual lineup missing {9 - len(found)} players")
        elif total_salary > 50000:
            print(f"\n✗ Manual lineup over salary cap by ${total_salary - 50000}")

    finally:
        session.close()

if __name__ == "__main__":
    print("=" * 60)
    print("LINEUP OPTIMIZER DEBUG TOOL")
    print("=" * 60)

    week_id = 9
    if len(sys.argv) > 1:
        week_id = int(sys.argv[1])

    check_player_data(week_id)
    check_vegas_lines_data(week_id)
    test_manual_lineup_feasibility(week_id)

    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. If data issues found above, fix them first")
    print("2. Enable CBC verbose output in lineup_optimizer_service.py line 349:")
    print("   Change: prob.solve(pulp.PULP_CBC_CMD(msg=0))")
    print("   To:     prob.solve(pulp.PULP_CBC_CMD(msg=1))")
    print("3. Try generating 1 lineup and check backend logs for CBC output")
    print("4. The CBC output will show EXACTLY which constraint is failing")
