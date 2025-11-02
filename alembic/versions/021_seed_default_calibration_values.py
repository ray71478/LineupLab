"""Seed default calibration values for current week

Revision ID: 021
Revises: 020
Create Date: 2025-11-01 00:00:00.000000

Description:
Seeds default calibration factors for all NFL positions based on historical
ETR projection accuracy analysis. These defaults represent observed patterns:
- RB/WR/TE: Floor too low, median skewed low, ceiling too high
- QB: Slight range compression needed
- K/DST: No observed calibration needed

Default Calibration Factors (per position):
- QB:  Floor +5%,  Median  0%, Ceiling -5%  (compress range slightly)
- RB:  Floor +10%, Median +8%, Ceiling -10% (median too low, range too wide)
- WR:  Floor +8%,  Median +5%, Ceiling -12% (median skewed low, ceiling too high)
- TE:  Floor +10%, Median +7%, Ceiling -10% (similar to RB pattern)
- K:   Floor  0%,  Median  0%, Ceiling  0%  (no observed issues)
- DST: Floor  0%,  Median  0%, Ceiling  0%  (no observed issues)

The migration applies these defaults to the current active week only.
All calibrations are set to is_active = true.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Seed default calibration values for current active week."""

    connection = op.get_bind()

    # Get the current active week (most recent active week)
    result = connection.execute(
        text("""
            SELECT id FROM weeks
            WHERE status = 'active'
            ORDER BY season DESC, week_number DESC
            LIMIT 1
        """)
    )
    row = result.fetchone()

    if row is None:
        # No active week found - skip seeding
        # This is not an error; calibration can be added later
        print("No active week found. Skipping default calibration seeding.")
        return

    current_week_id = row[0]
    print(f"Seeding default calibration values for week_id: {current_week_id}")

    # Default calibration factors per position
    # Based on ETR projection accuracy analysis from spec lines 253-263
    default_calibrations = [
        {
            'position': 'QB',
            'floor': 5.0,
            'median': 0.0,
            'ceiling': -5.0,
            'rationale': 'Compress range slightly'
        },
        {
            'position': 'RB',
            'floor': 10.0,
            'median': 8.0,
            'ceiling': -10.0,
            'rationale': 'Median too low, range too wide'
        },
        {
            'position': 'WR',
            'floor': 8.0,
            'median': 5.0,
            'ceiling': -12.0,
            'rationale': 'Median skewed low, ceiling too high'
        },
        {
            'position': 'TE',
            'floor': 10.0,
            'median': 7.0,
            'ceiling': -10.0,
            'rationale': 'Similar to RB - median low, range wide'
        },
        {
            'position': 'K',
            'floor': 0.0,
            'median': 0.0,
            'ceiling': 0.0,
            'rationale': 'No observed issues'
        },
        {
            'position': 'DST',
            'floor': 0.0,
            'median': 0.0,
            'ceiling': 0.0,
            'rationale': 'No observed issues'
        }
    ]

    # Insert default calibration values for each position
    for calibration in default_calibrations:
        connection.execute(
            text("""
                INSERT INTO projection_calibration
                (week_id, position, floor_adjustment_percent, median_adjustment_percent,
                 ceiling_adjustment_percent, is_active)
                VALUES (:week_id, :position, :floor, :median, :ceiling, true)
                ON CONFLICT (week_id, position) DO NOTHING
            """),
            {
                'week_id': current_week_id,
                'position': calibration['position'],
                'floor': calibration['floor'],
                'median': calibration['median'],
                'ceiling': calibration['ceiling']
            }
        )

    print(f"Seeded {len(default_calibrations)} default calibration profiles for week {current_week_id}")


def downgrade() -> None:
    """Remove seeded default calibration values."""

    connection = op.get_bind()

    # Get the current active week
    result = connection.execute(
        text("""
            SELECT id FROM weeks
            WHERE status = 'active'
            ORDER BY season DESC, week_number DESC
            LIMIT 1
        """)
    )
    row = result.fetchone()

    if row is None:
        print("No active week found. Nothing to remove.")
        return

    current_week_id = row[0]

    # Delete calibrations for current week that match default values
    # Only delete exact matches to avoid removing user customizations
    connection.execute(
        text("""
            DELETE FROM projection_calibration
            WHERE week_id = :week_id
            AND (
                (position = 'QB' AND floor_adjustment_percent = 5.0 AND median_adjustment_percent = 0.0 AND ceiling_adjustment_percent = -5.0)
                OR (position = 'RB' AND floor_adjustment_percent = 10.0 AND median_adjustment_percent = 8.0 AND ceiling_adjustment_percent = -10.0)
                OR (position = 'WR' AND floor_adjustment_percent = 8.0 AND median_adjustment_percent = 5.0 AND ceiling_adjustment_percent = -12.0)
                OR (position = 'TE' AND floor_adjustment_percent = 10.0 AND median_adjustment_percent = 7.0 AND ceiling_adjustment_percent = -10.0)
                OR (position = 'K' AND floor_adjustment_percent = 0.0 AND median_adjustment_percent = 0.0 AND ceiling_adjustment_percent = 0.0)
                OR (position = 'DST' AND floor_adjustment_percent = 0.0 AND median_adjustment_percent = 0.0 AND ceiling_adjustment_percent = 0.0)
            )
        """),
        {'week_id': current_week_id}
    )

    print(f"Removed default calibration values for week {current_week_id}")
