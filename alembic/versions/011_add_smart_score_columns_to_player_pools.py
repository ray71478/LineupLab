"""Add Smart Score columns to player_pools table

Revision ID: 011
Revises: 010
Create Date: 2025-10-30 00:00:00.000000

Description:
Adds Smart Score related columns to player_pools table:
- smart_score: Calculated Smart Score value
- projection_source: Source of projection (ETR or LineStar)
- opponent_rank_category: Categorized opponent rank (top_5, middle, bottom_5)
- games_with_20_plus_snaps: Count of games with 20+ snaps for trend calculation
- regression_risk: Boolean flag for WR regression risk detection
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add Smart Score columns to player_pools table."""
    
    # Add Smart Score columns
    op.add_column('player_pools', sa.Column('smart_score', sa.Float(), nullable=True))
    op.add_column('player_pools', sa.Column('projection_source', sa.String(50), nullable=True))
    op.add_column('player_pools', sa.Column('opponent_rank_category', sa.String(10), nullable=True))
    op.add_column('player_pools', sa.Column('games_with_20_plus_snaps', sa.Integer(), nullable=True))
    op.add_column('player_pools', sa.Column('regression_risk', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add constraint for opponent_rank_category valid values
    op.create_check_constraint(
        'check_opponent_rank_category',
        'player_pools',
        "opponent_rank_category IS NULL OR opponent_rank_category IN ('top_5', 'middle', 'bottom_5')"
    )
    
    # Add constraint for projection_source valid values
    op.create_check_constraint(
        'check_projection_source',
        'player_pools',
        "projection_source IS NULL OR projection_source IN ('ETR', 'LineStar')"
    )
    
    # Create composite index for filtering by week_id and smart_score
    op.create_index(
        'idx_player_pools_smart_score',
        'player_pools',
        ['week_id', 'smart_score']
    )
    
    # Create index for filtering by opponent_rank_category
    op.create_index(
        'idx_player_pools_opponent_rank',
        'player_pools',
        ['opponent_rank_category']
    )


def downgrade() -> None:
    """Remove Smart Score columns from player_pools table."""
    op.drop_index('idx_player_pools_opponent_rank', table_name='player_pools')
    op.drop_index('idx_player_pools_smart_score', table_name='player_pools')
    op.drop_constraint('check_projection_source', 'player_pools', type_='check')
    op.drop_constraint('check_opponent_rank_category', 'player_pools', type_='check')
    op.drop_column('player_pools', 'regression_risk')
    op.drop_column('player_pools', 'games_with_20_plus_snaps')
    op.drop_column('player_pools', 'opponent_rank_category')
    op.drop_column('player_pools', 'projection_source')
    op.drop_column('player_pools', 'smart_score')

