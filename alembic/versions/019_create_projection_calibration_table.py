"""Create projection_calibration table

Revision ID: 019
Revises: 018
Create Date: 2025-11-01 00:00:00.000000

Description:
Creates projection_calibration table to store position-based calibration factors
for adjusting ETR projection floor, median, and ceiling values. Supports weekly
calibration profiles with active/inactive toggles.

Table Schema:
- id: Primary key
- week_id: Foreign key to weeks table
- position: NFL position (QB, RB, WR, TE, K, DST)
- floor_adjustment_percent: Percentage adjustment for floor projection (-50 to +50)
- median_adjustment_percent: Percentage adjustment for median projection (-50 to +50)
- ceiling_adjustment_percent: Percentage adjustment for ceiling projection (-50 to +50)
- is_active: Boolean flag to enable/disable calibration
- created_at: Timestamp of creation
- updated_at: Timestamp of last update

Constraints:
- UNIQUE (week_id, position): One calibration per position per week
- CHECK position IN ('QB', 'RB', 'WR', 'TE', 'K', 'DST')
- CHECK adjustment percentages BETWEEN -50 AND 50
- FOREIGN KEY week_id REFERENCES weeks(id) ON DELETE CASCADE

Indexes:
- idx_projection_calibration_week: On (week_id) for weekly lookups
- idx_projection_calibration_active: On (week_id, is_active) for active calibration queries
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create projection_calibration table with constraints and indexes."""

    # Create projection_calibration table
    op.create_table(
        'projection_calibration',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('week_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.String(10), nullable=False),
        sa.Column('floor_adjustment_percent', sa.Numeric(5, 2), nullable=False),
        sa.Column('median_adjustment_percent', sa.Numeric(5, 2), nullable=False),
        sa.Column('ceiling_adjustment_percent', sa.Numeric(5, 2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),

        # Primary key
        sa.PrimaryKeyConstraint('id'),

        # Foreign key to weeks table with CASCADE delete
        sa.ForeignKeyConstraint(
            ['week_id'],
            ['weeks.id'],
            ondelete='CASCADE'
        ),

        # Unique constraint: one calibration per position per week
        sa.UniqueConstraint('week_id', 'position', name='unique_week_position'),

        # Check constraint: valid NFL positions only
        sa.CheckConstraint(
            "position IN ('QB', 'RB', 'WR', 'TE', 'K', 'DST')",
            name='check_position_valid'
        ),

        # Check constraint: adjustment percentages within reasonable range
        sa.CheckConstraint(
            """
            floor_adjustment_percent BETWEEN -50 AND 50 AND
            median_adjustment_percent BETWEEN -50 AND 50 AND
            ceiling_adjustment_percent BETWEEN -50 AND 50
            """,
            name='check_adjustment_range'
        )
    )

    # Create index on week_id for efficient weekly lookups
    op.create_index(
        'idx_projection_calibration_week',
        'projection_calibration',
        ['week_id']
    )

    # Create composite index on week_id and is_active for active calibration queries
    op.create_index(
        'idx_projection_calibration_active',
        'projection_calibration',
        ['week_id', 'is_active']
    )


def downgrade() -> None:
    """Drop projection_calibration table and all related indexes."""

    # Drop indexes
    op.drop_index('idx_projection_calibration_active', table_name='projection_calibration')
    op.drop_index('idx_projection_calibration_week', table_name='projection_calibration')

    # Drop table
    op.drop_table('projection_calibration')
