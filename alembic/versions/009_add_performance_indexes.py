"""Add performance indexes for player management queries.

Revision ID: 009
Revises: 008
Create Date: 2025-10-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add indexes for optimized player management queries."""
    # Index for filtering by week, position, team (most common query)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_player_pools_week_position_team
        ON player_pools(week_id, position, team)
        """
    )

    # Index for player lookups by key within a week
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_player_pools_week_key
        ON player_pools(week_id, player_key)
        """
    )

    # Index for unmatched player queries (import_id, status)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_unmatched_import_status
        ON unmatched_players(import_id, status)
        """
    )

    # Index for alias lookups during import
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_player_aliases_name
        ON player_aliases(alias_name)
        """
    )

    # Index for canonical player key lookups
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_player_aliases_canonical_key
        ON player_aliases(canonical_player_key)
        """
    )

    # Index for name search performance
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_player_pools_name_pattern
        ON player_pools(name)
        WHERE player_pools.week_id IS NOT NULL
        """
    )


def downgrade() -> None:
    """Drop performance indexes."""
    op.execute("DROP INDEX IF EXISTS idx_player_pools_week_position_team")
    op.execute("DROP INDEX IF EXISTS idx_player_pools_week_key")
    op.execute("DROP INDEX IF EXISTS idx_unmatched_import_status")
    op.execute("DROP INDEX IF EXISTS idx_player_aliases_name")
    op.execute("DROP INDEX IF EXISTS idx_player_aliases_canonical_key")
    op.execute("DROP INDEX IF EXISTS idx_player_pools_name_pattern")
