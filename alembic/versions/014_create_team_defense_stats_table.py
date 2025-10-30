"""Create team_defense_stats table for seasonal defensive rankings

Revision ID: 014
Revises: 013
Create Date: 2025-10-30 00:00:00.000000

Description:
Creates new team_defense_stats table to store seasonal team defensive rankings:
- season: NFL season year
- team_abbr: Team abbreviation (3 letters)
- pass_defense_rank: Pass defense ranking (1-32)
- rush_defense_rank: Rush defense ranking (1-32)
- Unique constraint on (season, team_abbr)
- Indexed for efficient lookups
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create team_defense_stats table."""

    # Create table only if it doesn't exist
    op.create_table(
        'team_defense_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('team_abbr', sa.String(10), nullable=False),
        sa.Column('pass_defense_rank', sa.Integer(), nullable=True),
        sa.Column('rush_defense_rank', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('season', 'team_abbr', name='uq_team_defense_stats_season_team')
    )

    # Create index for efficient lookups
    op.create_index(
        'idx_team_defense_stats_season_team',
        'team_defense_stats',
        ['season', 'team_abbr']
    )

    # Create index for looking up by pass defense rank
    op.create_index(
        'idx_team_defense_stats_pass_rank',
        'team_defense_stats',
        ['pass_defense_rank']
    )


def downgrade() -> None:
    """Drop team_defense_stats table."""

    # Drop indexes
    op.drop_index('idx_team_defense_stats_pass_rank', table_name='team_defense_stats')
    op.drop_index('idx_team_defense_stats_season_team', table_name='team_defense_stats')

    # Drop table
    op.drop_table('team_defense_stats')
