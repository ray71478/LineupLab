"""Create team_defense_stats table for defensive rankings

Revision ID: 014
Revises: 013
Create Date: 2025-10-30

Description:
Creates the team_defense_stats table to store NFL defensive rankings
fetched from MySportsFeeds API. This table is used by SmartScoreService
to calculate the W8 (Matchup Strength) factor in the Smart Score formula.

The table stores defensive rankings for each team by position group,
allowing the system to adjust player projections based on opponent strength.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade():
    """Create team_defense_stats table."""

    op.create_table(
        'team_defense_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('week_id', sa.Integer(), nullable=False),
        sa.Column('team', sa.String(10), nullable=False),
        sa.Column('position', sa.String(10), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('points_allowed', sa.Float(), nullable=True),
        sa.Column('defense_strength_category', sa.String(20), nullable=True),
        sa.Column('fetched_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('rank > 0 OR rank IS NULL', name='check_rank_positive'),
        sa.CheckConstraint("position IN ('QB', 'RB', 'WR', 'TE', 'DEF', 'OVERALL')", name='check_defense_position'),
        sa.CheckConstraint("defense_strength_category IN ('Elite', 'Good', 'Average', 'Poor') OR defense_strength_category IS NULL", name='check_defense_category'),
        sa.ForeignKeyConstraint(['week_id'], ['weeks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('week_id', 'team', 'position', name='unique_week_team_position_defense')
    )

    # Create indexes for efficient queries
    op.create_index('idx_team_defense_stats_week_id', 'team_defense_stats', ['week_id'])
    op.create_index('idx_team_defense_stats_team', 'team_defense_stats', ['team'])
    op.create_index('idx_team_defense_stats_position', 'team_defense_stats', ['position'])
    op.create_index('idx_team_defense_stats_week_team', 'team_defense_stats', ['week_id', 'team'])
    op.create_index('idx_team_defense_stats_fetched_at', 'team_defense_stats', ['fetched_at'])


def downgrade():
    """Drop team_defense_stats table."""
    op.drop_table('team_defense_stats')
