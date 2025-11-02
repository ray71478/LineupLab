"""Add DraftKings-specific fields to player_pools table

Revision ID: 018
Revises: 017
Create Date: 2025-11-01 00:00:00.000000

Description:
Adds DraftKings-specific fields to player_pools table:
- draftkings_id: INTEGER - DraftKings player ID
- opponent: VARCHAR(10) - Opponent team abbreviation (extracted from Game Info)
- game_time: VARCHAR(20) - Game time (e.g., "01:00PM")
- implied_team_total: FLOAT - Vegas implied team total (ITT)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add DraftKings-specific fields to player_pools table."""
    
    # Add draftkings_id column
    op.add_column(
        'player_pools',
        sa.Column('draftkings_id', sa.Integer(), nullable=True)
    )
    
    # Add opponent column
    op.add_column(
        'player_pools',
        sa.Column('opponent', sa.String(10), nullable=True)
    )
    
    # Add game_time column
    op.add_column(
        'player_pools',
        sa.Column('game_time', sa.String(20), nullable=True)
    )
    
    # Add implied_team_total column
    op.add_column(
        'player_pools',
        sa.Column('implied_team_total', sa.Float(), nullable=True)
    )
    
    # Create indexes for efficient queries
    op.create_index(
        'idx_player_pools_draftkings_id',
        'player_pools',
        ['draftkings_id']
    )
    
    op.create_index(
        'idx_player_pools_opponent',
        'player_pools',
        ['opponent']
    )


def downgrade() -> None:
    """Remove DraftKings-specific fields from player_pools table."""
    
    # Drop indexes
    op.drop_index('idx_player_pools_opponent', table_name='player_pools')
    op.drop_index('idx_player_pools_draftkings_id', table_name='player_pools')
    
    # Drop columns
    op.drop_column('player_pools', 'implied_team_total')
    op.drop_column('player_pools', 'game_time')
    op.drop_column('player_pools', 'opponent')
    op.drop_column('player_pools', 'draftkings_id')

