"""Add injury_status column to player_pools table

Revision ID: 012
Revises: 011
Create Date: 2025-10-30 00:00:00.000000

Description:
Adds injury status column to player_pools for storing MySportsFeeds injury data:
- injury_status: VARCHAR(20) with values PROBABLE, QUESTIONABLE, DOUBTFUL, OUT, NULL
- Includes check constraint for valid values
- Includes index for efficient filtering
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add injury_status column to player_pools table."""

    # Add injury_status column
    op.add_column(
        'player_pools',
        sa.Column('injury_status', sa.String(20), nullable=True)
    )

    # Add check constraint for valid injury status values
    op.create_check_constraint(
        'check_injury_status',
        'player_pools',
        "injury_status IS NULL OR injury_status IN ('PROBABLE', 'QUESTIONABLE', 'DOUBTFUL', 'OUT')"
    )

    # Create index for efficient filtering by injury status
    op.create_index(
        'idx_player_pools_injury_status',
        'player_pools',
        ['injury_status']
    )


def downgrade() -> None:
    """Remove injury_status column from player_pools table."""

    # Drop index
    op.drop_index('idx_player_pools_injury_status', table_name='player_pools')

    # Drop constraint
    op.drop_constraint('check_injury_status', 'player_pools', type_='check')

    # Drop column
    op.drop_column('player_pools', 'injury_status')
