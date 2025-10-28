"""
Pytest configuration and fixtures for Cortex integration tests.

Provides database setup/teardown, sample data generation, and common assertions.
"""

import os
import pytest
from io import BytesIO
from typing import List, Dict, Any
from datetime import datetime

import pandas as pd
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Use test database or in-memory SQLite for speed
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite:///:memory:"
)


@pytest.fixture(scope="function")
def db_engine():
    """Create test database engine."""
    # For SQLite in-memory, use StaticPool to prevent "database is locked" errors
    if "sqlite" in TEST_DATABASE_URL:
        engine = create_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(TEST_DATABASE_URL)

    # Create all tables using raw SQL
    # This is simpler than running alembic migrations for tests
    try:
        with engine.begin() as conn:
            # Create weeks table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS weeks (
                    id INTEGER PRIMARY KEY,
                    season INTEGER NOT NULL,
                    week_number INTEGER NOT NULL CHECK (week_number BETWEEN 1 AND 18),
                    status VARCHAR(20) DEFAULT 'upcoming' CHECK (status IN ('upcoming', 'active', 'completed')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(season, week_number)
                )
            """))

            # Create player_pools table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS player_pools (
                    id INTEGER PRIMARY KEY,
                    week_id INTEGER NOT NULL REFERENCES weeks(id) ON DELETE CASCADE,
                    player_key VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    team VARCHAR(10) NOT NULL,
                    position VARCHAR(10) NOT NULL CHECK (position IN ('QB', 'RB', 'WR', 'TE', 'DST')),
                    salary INTEGER NOT NULL CHECK (salary BETWEEN 3000 AND 10000),
                    projection FLOAT CHECK (projection >= 0),
                    ownership FLOAT CHECK (ownership BETWEEN 0 AND 1),
                    ceiling FLOAT,
                    floor FLOAT,
                    source VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(week_id, player_key)
                )
            """))

            # Create historical_stats table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS historical_stats (
                    id INTEGER PRIMARY KEY,
                    week_id INTEGER REFERENCES weeks(id) ON DELETE CASCADE,
                    player_name VARCHAR(255) NOT NULL,
                    team VARCHAR(10) NOT NULL,
                    position VARCHAR(10) NOT NULL,
                    week INTEGER CHECK (week BETWEEN 1 AND 18),
                    opponent VARCHAR(10),
                    snaps INTEGER,
                    snap_pct FLOAT,
                    rush_attempts INTEGER,
                    rush_yards INTEGER,
                    rush_tds INTEGER,
                    targets INTEGER,
                    target_share FLOAT,
                    receptions INTEGER,
                    rec_yards INTEGER,
                    rec_tds INTEGER,
                    total_tds INTEGER,
                    touches INTEGER,
                    actual_points FLOAT,
                    salary INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Create historical_stats_backup table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS historical_stats_backup (
                    id INTEGER PRIMARY KEY,
                    backup_timestamp TIMESTAMP,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Create player_aliases table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS player_aliases (
                    id INTEGER PRIMARY KEY,
                    unmatched_name VARCHAR(255) NOT NULL,
                    canonical_player_key VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(unmatched_name, canonical_player_key)
                )
            """))

            # Create import_history table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS import_history (
                    id TEXT PRIMARY KEY,
                    week_id INTEGER NOT NULL REFERENCES weeks(id) ON DELETE CASCADE,
                    source VARCHAR(50) NOT NULL,
                    player_count INTEGER NOT NULL,
                    unmatched_count INTEGER DEFAULT 0,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Create player_pool_history table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS player_pool_history (
                    id INTEGER PRIMARY KEY,
                    import_id TEXT NOT NULL REFERENCES import_history(id) ON DELETE CASCADE,
                    player_key VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    team VARCHAR(10) NOT NULL,
                    position VARCHAR(10) NOT NULL,
                    salary INTEGER NOT NULL,
                    projection FLOAT,
                    ownership FLOAT,
                    ceiling FLOAT,
                    floor FLOAT,
                    source VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Create unmatched_players table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS unmatched_players (
                    id INTEGER PRIMARY KEY,
                    import_id TEXT NOT NULL REFERENCES import_history(id) ON DELETE CASCADE,
                    player_name VARCHAR(255) NOT NULL,
                    team VARCHAR(10),
                    position VARCHAR(10),
                    salary INTEGER,
                    source VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'mapped', 'ignored')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            conn.commit()
    except Exception as e:
        print(f"Error creating tables: {e}")

    yield engine

    # Drop all tables
    try:
        with engine.begin() as conn:
            tables = [
                "unmatched_players",
                "player_pool_history",
                "import_history",
                "player_aliases",
                "historical_stats_backup",
                "historical_stats",
                "player_pools",
                "weeks",
            ]
            for table in tables:
                conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
            conn.commit()
    except Exception as e:
        print(f"Error dropping tables: {e}")

    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create test database session."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, expire_on_commit=False)()

    yield session

    session.close()
    try:
        transaction.rollback()
    except:
        pass
    connection.close()


def create_week(session: Session, season: int = 2024, week_number: int = 1) -> int:
    """Create a week and return its ID."""
    try:
        result = session.execute(
            text("""
                INSERT INTO weeks (season, week_number, status)
                VALUES (:season, :week_number, 'active')
            """),
            {"season": season, "week_number": week_number}
        )
        session.commit()
        return result.lastrowid
    except Exception as e:
        session.rollback()
        # Week might already exist
        result = session.execute(
            text("SELECT id FROM weeks WHERE season = :season AND week_number = :week_number"),
            {"season": season, "week_number": week_number}
        )
        row = result.fetchone()
        return row[0] if row else None


def create_linestar_xlsx() -> BytesIO:
    """Create a sample LineStar XLSX file with 153 players."""
    wb = Workbook()
    ws = wb.active
    ws.title = "LineStar"

    # Headers
    headers = ["Name", "Position", "Team", "Salary", "Projected", "Ceiling", "Floor", "ProjOwn"]
    ws.append(headers)

    # Generate 153 players
    # Simple approach: create enough players to reach 153 total
    positions = ["QB", "RB", "WR", "TE", "DST"]
    teams = ["KC", "LAC", "PHI", "DAL", "CIN", "BAL", "BUF", "NYG", "NO", "TB", "CAR", "GB", "MIN", "SF", "LAR", "TB", "TEN", "LV", "WAS", "DEN", "HOU", "IND"]

    player_count = 0
    for i in range(153):
        team = teams[i % len(teams)]
        position = positions[i % len(positions)]
        name = f"Player{i+1}"
        salary = 5000 + (i % 2000)
        projection = 10.0 + (i % 5)
        ceiling = projection + 2.0
        floor = projection - 2.0
        ownership = 0.05 + (i % 100) / 1000

        ws.append([name, position, team, salary, projection, ceiling, floor, ownership])
        player_count += 1

    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def create_draftkings_xlsx() -> BytesIO:
    """Create a sample DraftKings XLSX file with 174 players."""
    wb = Workbook()
    ws = wb.active
    ws.title = "FE"

    # DraftKings header row (row 1, which we skip)
    ws.append(["Skip Row"])

    # Actual headers (row 2)
    headers = ["Name", "Pos", "T", "S", "Proj", "Ceil", "Flr", "Own", "Notes"]
    ws.append(headers)

    # Generate 174 players
    positions = ["QB", "RB", "WR", "TE", "DST"]
    teams = ["KC", "LAC", "PHI", "DAL", "CIN", "BAL", "BUF", "NYG", "NO", "TB", "CAR", "GB", "MIN", "SF", "LAR", "TEN", "LV", "MIA", "WAS", "DEN", "HOU", "IND", "SEA", "ARI"]

    for i in range(174):
        team = teams[i % len(teams)]
        position = positions[i % len(positions)]
        name = f"DKPlayer{i+1}"
        salary = 4500 + (i % 2500)
        projection = 12.0 + (i % 5)
        ceiling = projection + 2.5
        floor = projection - 2.5
        ownership = 0.03 + (i % 100) / 1000

        ws.append([name, position, team, salary, projection, ceiling, floor, ownership, ""])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def create_comprehensive_stats_xlsx() -> BytesIO:
    """Create a sample Comprehensive Stats XLSX file with 2690 records."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Points"

    # Headers
    headers = [
        "Player", "Tm", "Pos", "Wk", "Opp", "Snaps", "Snp %", "Ratt", "Rsh_yds",
        "Rsh_td", "CTGT", "CTGT%", "Rec", "Rc_yds", "Rc_td", "Tot TD", "Touch",
        "DK Pts", "Sal"
    ]
    ws.append(headers)

    # Generate 2690 records
    # Simple approach: create enough records
    positions = ["QB", "RB", "WR", "TE", "DST"]
    teams = ["KC", "LAC", "PHI", "DAL", "CIN", "BAL", "BUF", "NYG", "NO", "TB"]

    for i in range(2690):
        week = (i % 18) + 1
        team = teams[i % len(teams)]
        pos = positions[i % len(positions)]
        player_name = f"Stat{i}"
        snaps = 30 + (i % 50)
        snap_pct = (snaps / 80) if snaps > 0 else 0.0
        rush_attempts = i % 20
        rush_yards = rush_attempts * 4
        rush_tds = i % 3
        targets = i % 10
        target_share = (targets / 80) if targets > 0 else 0.0
        receptions = int(targets * 0.65)
        rec_yards = receptions * 8
        rec_tds = i % 2
        total_tds = rush_tds + rec_tds
        touches = rush_attempts + receptions
        actual_points = (rush_yards * 0.1) + (rec_yards * 0.1) + (total_tds * 6)
        salary = 5000 + (i % 2000)

        ws.append([
            player_name, team, pos, week, "OPP", snaps, snap_pct,
            rush_attempts, rush_yards, rush_tds, targets, target_share,
            receptions, rec_yards, rec_tds, total_tds, touches, actual_points, salary
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def verify_import_success(
    session: Session,
    week_id: int,
    expected_count: int,
    source: str
) -> Dict[str, Any]:
    """
    Verify import success by checking database state.

    Returns stats about the import.
    """
    # Count players
    result = session.execute(
        text("SELECT COUNT(*) FROM player_pools WHERE week_id = :week_id AND source = :source"),
        {"week_id": week_id, "source": source}
    )
    count = result.scalar()

    # Check import history
    result = session.execute(
        text("SELECT id, source, player_count FROM import_history WHERE week_id = :week_id AND source = :source ORDER BY created_at DESC LIMIT 1"),
        {"week_id": week_id, "source": source}
    )
    import_record = result.fetchone()

    # Verify player_keys
    result = session.execute(
        text("SELECT COUNT(*) FROM player_pools WHERE week_id = :week_id AND player_key LIKE '%_%_%'"),
        {"week_id": week_id}
    )
    valid_keys = result.scalar()

    # Check ownership normalization
    result = session.execute(
        text("SELECT MIN(ownership), MAX(ownership) FROM player_pools WHERE week_id = :week_id"),
        {"week_id": week_id}
    )
    min_own, max_own = result.fetchone()

    return {
        "player_count": count,
        "expected_count": expected_count,
        "import_record": import_record,
        "valid_player_keys": valid_keys,
        "min_ownership": min_own,
        "max_ownership": max_own,
        "count_matches": count == expected_count,
    }


@pytest.fixture
def linestar_sample() -> BytesIO:
    """Fixture providing LineStar sample file."""
    return create_linestar_xlsx()


@pytest.fixture
def draftkings_sample() -> BytesIO:
    """Fixture providing DraftKings sample file."""
    return create_draftkings_xlsx()


@pytest.fixture
def comprehensive_stats_sample() -> BytesIO:
    """Fixture providing Comprehensive Stats sample file."""
    return create_comprehensive_stats_xlsx()
