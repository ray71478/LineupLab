"""Add contest_mode to player_pools table

Revision ID: 022
Revises: 021
Create Date: 2025-11-02 12:00:00.000000

Description:
Adds contest_mode column to player_pools table to support DraftKings Showdown slates.
- Adds contest_mode VARCHAR(20) DEFAULT 'main' NOT NULL column
- Creates composite index on (week_id, contest_mode) for efficient filtering
- Updates unique constraint to include contest_mode (week_id, player_key, contest_mode)
- Ensures backward compatibility (existing data defaults to 'main')

This migration is part of Task 1.2 in the Showdown Mode implementation.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add contest_mode column and composite index to player_pools table."""

    # Step 1: Add contest_mode column with default value 'main'
    # This ensures backward compatibility - all existing records will be 'main'
    op.add_column(
        'player_pools',
        sa.Column('contest_mode', sa.String(20), nullable=False, server_default='main')
    )

    # Step 2: Create composite index on (week_id, contest_mode)
    # This enables efficient filtering by mode and supports data isolation
    op.create_index(
        'idx_player_pools_week_mode',
        'player_pools',
        ['week_id', 'contest_mode']
    )

    # Step 3: Drop old unique constraint (week_id, player_key)
    # We need to recreate it to include contest_mode
    op.drop_constraint('unique_week_player', 'player_pools', type_='unique')

    # Step 4: Create new unique constraint (week_id, player_key, contest_mode)
    # This allows same player in different modes for the same week
    op.create_unique_constraint(
        'unique_week_player_mode',
        'player_pools',
        ['week_id', 'player_key', 'contest_mode']
    )

    # Add check constraint to ensure valid contest_mode values
    op.create_check_constraint(
        'check_contest_mode_valid',
        'player_pools',
        "contest_mode IN ('main', 'showdown')"
    )


def downgrade() -> None:
    """Remove contest_mode column and restore original constraints."""

    # Drop check constraint
    op.drop_constraint('check_contest_mode_valid', 'player_pools', type_='check')

    # Drop new unique constraint
    op.drop_constraint('unique_week_player_mode', 'player_pools', type_='unique')

    # Restore old unique constraint
    op.create_unique_constraint(
        'unique_week_player',
        'player_pools',
        ['week_id', 'player_key']
    )

    # Drop composite index
    op.drop_index('idx_player_pools_week_mode', table_name='player_pools')

    # Drop contest_mode column
    op.drop_column('player_pools', 'contest_mode')
