"""fix percentage constraints to allow 0-100 range

Revision ID: 007
Revises: 006
Create Date: 2025-10-29

Description:
Updates snap_pct and target_share constraints in historical_stats and 
historical_stats_backup tables to accept percentages as 0-100 instead of 0-1.
This matches the natural format of the data in the source files.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    """Update percentage constraints to 0-100 range."""
    
    # Drop old constraints for historical_stats
    op.drop_constraint('check_snap_pct_range', 'historical_stats', type_='check')
    op.drop_constraint('check_target_share_range', 'historical_stats', type_='check')
    
    # Add new constraints with 0-100 range
    op.create_check_constraint(
        'check_snap_pct_range',
        'historical_stats',
        'snap_pct BETWEEN 0 AND 100'
    )
    op.create_check_constraint(
        'check_target_share_range',
        'historical_stats',
        'target_share BETWEEN 0 AND 100'
    )
    
    # Drop old constraints for historical_stats_backup
    op.drop_constraint('check_backup_snap_pct_range', 'historical_stats_backup', type_='check')
    op.drop_constraint('check_backup_target_share_range', 'historical_stats_backup', type_='check')
    
    # Add new constraints with 0-100 range
    op.create_check_constraint(
        'check_backup_snap_pct_range',
        'historical_stats_backup',
        'snap_pct BETWEEN 0 AND 100'
    )
    op.create_check_constraint(
        'check_backup_target_share_range',
        'historical_stats_backup',
        'target_share BETWEEN 0 AND 100'
    )


def downgrade():
    """Revert percentage constraints to 0-1 range."""
    
    # Drop new constraints for historical_stats
    op.drop_constraint('check_snap_pct_range', 'historical_stats', type_='check')
    op.drop_constraint('check_target_share_range', 'historical_stats', type_='check')
    
    # Restore old constraints with 0-1 range
    op.create_check_constraint(
        'check_snap_pct_range',
        'historical_stats',
        'snap_pct BETWEEN 0 AND 1'
    )
    op.create_check_constraint(
        'check_target_share_range',
        'historical_stats',
        'target_share BETWEEN 0 AND 1'
    )
    
    # Drop new constraints for historical_stats_backup
    op.drop_constraint('check_backup_snap_pct_range', 'historical_stats_backup', type_='check')
    op.drop_constraint('check_backup_target_share_range', 'historical_stats_backup', type_='check')
    
    # Restore old constraints with 0-1 range
    op.create_check_constraint(
        'check_backup_snap_pct_range',
        'historical_stats_backup',
        'snap_pct BETWEEN 0 AND 1'
    )
    op.create_check_constraint(
        'check_backup_target_share_range',
        'historical_stats_backup',
        'target_share BETWEEN 0 AND 1'
    )

