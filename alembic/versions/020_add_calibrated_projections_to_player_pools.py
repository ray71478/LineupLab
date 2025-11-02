"""Add calibrated projection columns to player_pools table

Revision ID: 020
Revises: 019
Create Date: 2025-11-01 00:00:00.000000

Description:
Adds columns to player_pools table to store both original and calibrated projection values.
This preserves historical projection data while allowing calibration adjustments to be applied
and stored for use in Smart Score calculations and lineup optimization.

New Columns:
- projection_floor_original: Original floor projection from data source
- projection_floor_calibrated: Calibrated floor projection after adjustment
- projection_median_original: Original median/projection from data source
- projection_median_calibrated: Calibrated median projection after adjustment
- projection_ceiling_original: Original ceiling projection from data source
- projection_ceiling_calibrated: Calibrated ceiling projection after adjustment
- calibration_applied: Boolean flag indicating if calibration was applied

Migration Strategy:
1. Add new columns (nullable initially)
2. Backfill original columns with existing floor/projection/ceiling values
3. Set calibration_applied = false for all existing records
4. Create index for efficient calibration-based queries

Note: Existing 'floor', 'projection', and 'ceiling' columns remain unchanged
for backward compatibility.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add calibrated projection columns to player_pools table."""

    # Add original projection columns
    op.add_column(
        'player_pools',
        sa.Column('projection_floor_original', sa.Float(), nullable=True)
    )

    op.add_column(
        'player_pools',
        sa.Column('projection_median_original', sa.Float(), nullable=True)
    )

    op.add_column(
        'player_pools',
        sa.Column('projection_ceiling_original', sa.Float(), nullable=True)
    )

    # Add calibrated projection columns
    op.add_column(
        'player_pools',
        sa.Column('projection_floor_calibrated', sa.Float(), nullable=True)
    )

    op.add_column(
        'player_pools',
        sa.Column('projection_median_calibrated', sa.Float(), nullable=True)
    )

    op.add_column(
        'player_pools',
        sa.Column('projection_ceiling_calibrated', sa.Float(), nullable=True)
    )

    # Add calibration applied flag
    op.add_column(
        'player_pools',
        sa.Column('calibration_applied', sa.Boolean(), nullable=False, server_default='false')
    )

    # Backfill existing data: copy current projection values to *_original columns
    # This preserves historical data for existing player pools
    connection = op.get_bind()

    connection.execute(
        text("""
            UPDATE player_pools
            SET
                projection_floor_original = floor,
                projection_median_original = projection,
                projection_ceiling_original = ceiling,
                calibration_applied = false
            WHERE projection_floor_original IS NULL
        """)
    )

    # Create composite index for efficient calibration queries
    op.create_index(
        'idx_player_pools_calibration',
        'player_pools',
        ['week_id', 'calibration_applied']
    )


def downgrade() -> None:
    """Remove calibrated projection columns from player_pools table."""

    # Drop index
    op.drop_index('idx_player_pools_calibration', table_name='player_pools')

    # Drop columns
    op.drop_column('player_pools', 'calibration_applied')
    op.drop_column('player_pools', 'projection_ceiling_calibrated')
    op.drop_column('player_pools', 'projection_median_calibrated')
    op.drop_column('player_pools', 'projection_floor_calibrated')
    op.drop_column('player_pools', 'projection_ceiling_original')
    op.drop_column('player_pools', 'projection_median_original')
    op.drop_column('player_pools', 'projection_floor_original')
