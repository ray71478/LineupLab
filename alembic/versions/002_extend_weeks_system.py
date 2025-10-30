"""extend weeks system

Revision ID: 002
Revises: 001
Create Date: 2025-10-28

Description:
Extends the weeks table and creates new tables for the week management feature:
- Extends weeks table with new columns: nfl_slate_date, status_override, metadata, is_locked, locked_at, updated_at
- Creates week_metadata table for rich week information
- Creates nfl_schedule table for NFL schedule data
- Creates week_status_overrides table for manual status overrides
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """Extend weeks table and create new tables for week management."""

    # =====================================================================
    # 1. Extend weeks table with new columns
    # =====================================================================

    # Add nfl_slate_date column
    op.add_column(
        'weeks',
        sa.Column('nfl_slate_date', sa.Date(), nullable=True)
    )

    # Add status_override column
    op.add_column(
        'weeks',
        sa.Column('status_override', sa.String(20), nullable=True)
    )

    # Add metadata JSONB column
    op.add_column(
        'weeks',
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )

    # Add is_locked column
    op.add_column(
        'weeks',
        sa.Column('is_locked', sa.Boolean(), nullable=False, server_default='false')
    )

    # Add locked_at column
    op.add_column(
        'weeks',
        sa.Column('locked_at', sa.TIMESTAMP(), nullable=True)
    )

    # Note: updated_at column already exists from migration 001, no need to add it again

    # =====================================================================
    # 2. Create week_metadata table
    # =====================================================================
    op.create_table(
        'week_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('week_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('nfl_slate_date', sa.Date(), nullable=False),
        sa.Column('kickoff_time', sa.Time(), nullable=False),
        sa.Column('slate_start_time', sa.TIMESTAMP(), nullable=True),
        sa.Column('slate_end_time', sa.TIMESTAMP(), nullable=True),
        sa.Column('espn_schedule_url', sa.Text(), nullable=True),
        sa.Column('import_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('import_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('import_timestamp', sa.TIMESTAMP(), nullable=True),
        sa.Column('import_error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('week_number BETWEEN 1 AND 18', name='check_week_metadata_week_number'),
        sa.CheckConstraint("import_status IN ('pending', 'imported', 'error')", name='check_week_metadata_import_status'),
        sa.ForeignKeyConstraint(['week_id'], ['weeks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('week_id', name='unique_week_metadata_week_id'),
        sa.UniqueConstraint('season', 'week_number', name='unique_season_week_metadata')
    )

    # Create indexes for week_metadata
    op.create_index('idx_week_metadata_week_id', 'week_metadata', ['week_id'])
    op.create_index('idx_week_metadata_nfl_slate_date', 'week_metadata', ['nfl_slate_date'])
    op.create_index('idx_week_metadata_import_status', 'week_metadata', ['import_status'])

    # =====================================================================
    # 3. Create nfl_schedule table
    # =====================================================================
    op.create_table(
        'nfl_schedule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('week', sa.Integer(), nullable=False),
        sa.Column('slate_date', sa.Date(), nullable=False),
        sa.Column('kickoff_time', sa.Time(), nullable=False),
        sa.Column('game_count', sa.Integer(), nullable=True),
        sa.Column('is_playoff', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('week BETWEEN 1 AND 18', name='check_nfl_schedule_week'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('season', 'week', name='unique_season_week_schedule')
    )

    # Create indexes for nfl_schedule
    op.create_index('idx_nfl_schedule_season', 'nfl_schedule', ['season'])
    op.create_index('idx_nfl_schedule_slate_date', 'nfl_schedule', ['slate_date'])

    # =====================================================================
    # 4. Create week_status_overrides table
    # =====================================================================
    op.create_table(
        'week_status_overrides',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('week_id', sa.Integer(), nullable=False),
        sa.Column('override_status', sa.String(20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('overridden_by', sa.String(255), nullable=True),
        sa.Column('overridden_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("override_status IN ('active', 'upcoming', 'completed')", name='check_override_status'),
        sa.ForeignKeyConstraint(['week_id'], ['weeks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('week_id', name='unique_week_status_override')
    )

    # Create index for week_status_overrides
    op.create_index('idx_week_status_overrides_week_id', 'week_status_overrides', ['week_id'])

    # =====================================================================
    # 5. Create indexes on weeks table
    # =====================================================================
    op.create_index('idx_weeks_nfl_slate_date', 'weeks', ['nfl_slate_date'])
    op.create_index('idx_weeks_is_locked', 'weeks', ['is_locked'])
    op.create_index('idx_weeks_status_override', 'weeks', ['status_override'])


def downgrade():
    """Remove week management extensions."""

    # Drop indexes
    op.drop_index('idx_weeks_status_override', table_name='weeks')
    op.drop_index('idx_weeks_is_locked', table_name='weeks')
    op.drop_index('idx_weeks_nfl_slate_date', table_name='weeks')

    # Drop week_status_overrides table
    op.drop_index('idx_week_status_overrides_week_id', table_name='week_status_overrides')
    op.drop_table('week_status_overrides')

    # Drop nfl_schedule table
    op.drop_index('idx_nfl_schedule_slate_date', table_name='nfl_schedule')
    op.drop_index('idx_nfl_schedule_season', table_name='nfl_schedule')
    op.drop_table('nfl_schedule')

    # Drop week_metadata table
    op.drop_index('idx_week_metadata_import_status', table_name='week_metadata')
    op.drop_index('idx_week_metadata_nfl_slate_date', table_name='week_metadata')
    op.drop_index('idx_week_metadata_week_id', table_name='week_metadata')
    op.drop_table('week_metadata')

    # Remove columns from weeks table
    # Note: updated_at column is owned by migration 001, don't drop it here
    op.drop_column('weeks', 'locked_at')
    op.drop_column('weeks', 'is_locked')
    op.drop_column('weeks', 'metadata')
    op.drop_column('weeks', 'status_override')
    op.drop_column('weeks', 'nfl_slate_date')
