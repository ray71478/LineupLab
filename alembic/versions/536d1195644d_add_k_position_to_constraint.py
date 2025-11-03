"""add_k_position_to_constraint

Revision ID: 536d1195644d
Revises: f4afa6188f12
Create Date: 2025-11-02 18:41:22.231306

Description:
Adds 'K' (kicker) position to the check_player_position constraint.
Required for Showdown mode which supports kickers as eligible positions.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '536d1195644d'
down_revision = 'f4afa6188f12'
branch_labels = None
depends_on = None


def upgrade():
    """Add 'K' position to player_pools position constraint."""
    # Drop the existing constraint
    op.drop_constraint('check_player_position', 'player_pools')
    
    # Create new constraint that includes 'K' position
    op.create_check_constraint(
        'check_player_position',
        'player_pools',
        "position IN ('QB', 'RB', 'WR', 'TE', 'K', 'DST')"
    )


def downgrade():
    """Remove 'K' position from constraint."""
    # Drop the new constraint
    op.drop_constraint('check_player_position', 'player_pools')
    
    # Restore the original constraint without 'K'
    op.create_check_constraint(
        'check_player_position',
        'player_pools',
        "position IN ('QB', 'RB', 'WR', 'TE', 'DST')"
    )
