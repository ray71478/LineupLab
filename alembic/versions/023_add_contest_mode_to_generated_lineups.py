"""Add contest_mode to generated_lineups table

Revision ID: 023
Revises: 022
Create Date: 2025-11-02 12:15:00.000000

Description:
Adds contest_mode column to generated_lineups table to support DraftKings Showdown slates.
- Adds contest_mode VARCHAR(20) DEFAULT 'main' NOT NULL column
- Creates index on contest_mode for filtering saved lineups
- Updates players JSON structure to support is_captain BOOLEAN field
- Ensures backward compatibility (existing lineups default to 'main')

This migration is part of Task 1.3 in the Showdown Mode implementation.

Note: The is_captain field is stored within the players JSONB column and doesn't
require schema changes - it's documented here for reference.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '023'
down_revision = '022'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add contest_mode column and index to generated_lineups table."""

    # Step 1: Add contest_mode column with default value 'main'
    # This ensures backward compatibility - all existing lineups will be 'main'
    op.add_column(
        'generated_lineups',
        sa.Column('contest_mode', sa.String(20), nullable=False, server_default='main')
    )

    # Step 2: Create index on contest_mode for filtering lineups by mode
    op.create_index(
        'idx_generated_lineups_contest_mode',
        'generated_lineups',
        ['contest_mode']
    )

    # Step 3: Create composite index on (week_id, contest_mode) for efficient filtering
    op.create_index(
        'idx_generated_lineups_week_mode',
        'generated_lineups',
        ['week_id', 'contest_mode']
    )

    # Add check constraint to ensure valid contest_mode values
    op.create_check_constraint(
        'check_lineup_contest_mode_valid',
        'generated_lineups',
        "contest_mode IN ('main', 'showdown')"
    )


def downgrade() -> None:
    """Remove contest_mode column and indexes."""

    # Drop check constraint
    op.drop_constraint('check_lineup_contest_mode_valid', 'generated_lineups', type_='check')

    # Drop composite index
    op.drop_index('idx_generated_lineups_week_mode', table_name='generated_lineups')

    # Drop contest_mode index
    op.drop_index('idx_generated_lineups_contest_mode', table_name='generated_lineups')

    # Drop contest_mode column
    op.drop_column('generated_lineups', 'contest_mode')
