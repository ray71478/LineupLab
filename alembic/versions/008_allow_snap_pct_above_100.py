"""allow snap_pct above 100

Revision ID: 008
Revises: 007
Create Date: 2025-10-29

Description:
Updates snap_pct constraint to allow values above 100 since some players
can have snap percentages over 100% in certain game situations.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    """Remove upper limit on snap_pct."""
    
    # Drop old constraints for historical_stats
    op.drop_constraint('check_snap_pct_range', 'historical_stats', type_='check')
    
    # Add new constraint with no upper limit (just non-negative)
    op.create_check_constraint(
        'check_snap_pct_range',
        'historical_stats',
        'snap_pct >= 0'
    )
    
    # Drop old constraints for historical_stats_backup
    op.drop_constraint('check_backup_snap_pct_range', 'historical_stats_backup', type_='check')
    
    # Add new constraint with no upper limit
    op.create_check_constraint(
        'check_backup_snap_pct_range',
        'historical_stats_backup',
        'snap_pct >= 0'
    )


def downgrade():
    """Revert to 0-100 range."""
    
    # Drop new constraints for historical_stats
    op.drop_constraint('check_snap_pct_range', 'historical_stats', type_='check')
    
    # Restore old constraints with 0-100 range
    op.create_check_constraint(
        'check_snap_pct_range',
        'historical_stats',
        'snap_pct BETWEEN 0 AND 100'
    )
    
    # Drop new constraints for historical_stats_backup
    op.drop_constraint('check_backup_snap_pct_range', 'historical_stats_backup', type_='check')
    
    # Restore old constraints
    op.create_check_constraint(
        'check_backup_snap_pct_range',
        'historical_stats_backup',
        'snap_pct BETWEEN 0 AND 100'
    )

