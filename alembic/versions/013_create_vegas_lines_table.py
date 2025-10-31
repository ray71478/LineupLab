"""Create vegas_lines table for Vegas ITT data

Revision ID: 013
Revises: 012
Create Date: 2025-10-30

Description:
Creates the vegas_lines table to store Vegas Implied Team Total (ITT) data
fetched from MySportsFeeds API. This table is used by SmartScoreService
to calculate the W7 (Vegas Context) factor in the Smart Score formula.

The table stores one row per team per week with their implied team total
(projected points for that team in the game).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade():
    """Create vegas_lines table."""

    op.create_table(
        'vegas_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('week_id', sa.Integer(), nullable=False),
        sa.Column('team', sa.String(10), nullable=False),
        sa.Column('opponent', sa.String(10), nullable=True),
        sa.Column('implied_team_total', sa.Float(), nullable=True),
        sa.Column('over_under', sa.Float(), nullable=True),
        sa.Column('spread', sa.Float(), nullable=True),
        sa.Column('home_team', sa.Boolean(), nullable=True),
        sa.Column('fetched_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('implied_team_total > 0 OR implied_team_total IS NULL', name='check_itt_positive'),
        sa.CheckConstraint('over_under > 0 OR over_under IS NULL', name='check_over_under_positive'),
        sa.ForeignKeyConstraint(['week_id'], ['weeks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('week_id', 'team', name='unique_week_team_vegas')
    )

    # Create indexes for efficient queries
    op.create_index('idx_vegas_lines_week_id', 'vegas_lines', ['week_id'])
    op.create_index('idx_vegas_lines_team', 'vegas_lines', ['team'])
    op.create_index('idx_vegas_lines_week_team', 'vegas_lines', ['week_id', 'team'])
    op.create_index('idx_vegas_lines_fetched_at', 'vegas_lines', ['fetched_at'])


def downgrade():
    """Drop vegas_lines table."""
    op.drop_table('vegas_lines')
