"""Add implied_team_total column to vegas_lines table

Revision ID: 013
Revises: 012
Create Date: 2025-10-30 00:00:00.000000

Description:
Adds implied_team_total (ITT) column to vegas_lines for storing MySportsFeeds Vegas data:
- implied_team_total: FLOAT for storing Vegas Implied Team Total
- opponent_team: VARCHAR(10) for storing opponent team abbreviation
- Includes index for efficient lookups by week and team
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add ITT columns to vegas_lines table."""

    # Check if columns already exist before adding
    # This handles idempotency if migration is re-run

    # Add implied_team_total column if not exists
    try:
        op.add_column(
            'vegas_lines',
            sa.Column('implied_team_total', sa.Float(), nullable=True)
        )
    except Exception:
        # Column may already exist
        pass

    # Add opponent_team column if not exists
    try:
        op.add_column(
            'vegas_lines',
            sa.Column('opponent_team', sa.String(10), nullable=True)
        )
    except Exception:
        # Column may already exist
        pass

    # Create index for efficient lookups
    try:
        op.create_index(
            'idx_vegas_lines_week_team_itt',
            'vegas_lines',
            ['week_id', 'team', 'implied_team_total']
        )
    except Exception:
        # Index may already exist
        pass


def downgrade() -> None:
    """Remove ITT columns from vegas_lines table."""

    # Drop index
    try:
        op.drop_index('idx_vegas_lines_week_team_itt', table_name='vegas_lines')
    except Exception:
        pass

    # Drop columns
    try:
        op.drop_column('vegas_lines', 'opponent_team')
    except Exception:
        pass

    try:
        op.drop_column('vegas_lines', 'implied_team_total')
    except Exception:
        pass
