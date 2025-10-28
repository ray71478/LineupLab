"""create data import tables

Revision ID: 001
Revises:
Create Date: 2025-10-27

Description:
Creates all 8 tables required for the Data Import System:
- weeks: Track NFL weeks (season, week_number, status)
- player_pools: DFS players for each week (salary, projection, ownership)
- historical_stats: NFL stats by player/week/season
- historical_stats_backup: Backup of historical stats before full replace
- player_aliases: Map alternate names to canonical player keys
- import_history: Track all data imports with metadata
- player_pool_history: Snapshot of player pools after each import
- unmatched_players: Players skipped during import due to low fuzzy match confidence
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create all tables, constraints, and indexes for Data Import System."""

    # =====================================================================
    # Table 1: weeks
    # =====================================================================
    op.create_table(
        'weeks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='upcoming'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('week_number BETWEEN 1 AND 18', name='check_week_number_range'),
        sa.CheckConstraint("status IN ('upcoming', 'active', 'completed')", name='check_week_status'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('season', 'week_number', name='unique_season_week')
    )

    # Create indexes for weeks table
    op.create_index('idx_weeks_week_number', 'weeks', ['week_number'])
    op.create_index('idx_weeks_status', 'weeks', ['status'])

    # =====================================================================
    # Table 2: player_pools
    # =====================================================================
    op.create_table(
        'player_pools',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('week_id', sa.Integer(), nullable=False),
        sa.Column('player_key', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('team', sa.String(10), nullable=False),
        sa.Column('position', sa.String(10), nullable=False),
        sa.Column('salary', sa.Integer(), nullable=False),
        sa.Column('projection', sa.Float(), nullable=True),
        sa.Column('ownership', sa.Float(), nullable=True),
        sa.Column('ceiling', sa.Float(), nullable=True),
        sa.Column('floor', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('uploaded_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("position IN ('QB', 'RB', 'WR', 'TE', 'DST')", name='check_player_position'),
        sa.CheckConstraint('salary BETWEEN 3000 AND 10000', name='check_salary_range'),
        sa.CheckConstraint('projection >= 0', name='check_projection_positive'),
        sa.CheckConstraint('ownership BETWEEN 0 AND 1', name='check_ownership_range'),
        sa.CheckConstraint("source IN ('LineStar', 'DraftKings')", name='check_player_source'),
        sa.ForeignKeyConstraint(['week_id'], ['weeks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('week_id', 'player_key', name='unique_week_player')
    )

    # Create indexes for player_pools table
    op.create_index('idx_player_pools_week_id', 'player_pools', ['week_id'])
    op.create_index('idx_player_pools_player_key', 'player_pools', ['player_key'])
    op.create_index('idx_player_pools_position', 'player_pools', ['position'])
    op.create_index('idx_player_pools_team', 'player_pools', ['team'])
    op.create_index('idx_player_pools_source', 'player_pools', ['source'])

    # =====================================================================
    # Table 3: historical_stats
    # =====================================================================
    op.create_table(
        'historical_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_key', sa.String(255), nullable=False),
        sa.Column('week', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('team', sa.String(10), nullable=False),
        sa.Column('opponent', sa.String(10), nullable=True),
        sa.Column('snaps', sa.Integer(), nullable=True),
        sa.Column('snap_pct', sa.Float(), nullable=True),
        sa.Column('rush_attempts', sa.Integer(), nullable=True),
        sa.Column('rush_yards', sa.Integer(), nullable=True),
        sa.Column('rush_tds', sa.Integer(), nullable=True),
        sa.Column('targets', sa.Integer(), nullable=True),
        sa.Column('target_share', sa.Float(), nullable=True),
        sa.Column('receptions', sa.Integer(), nullable=True),
        sa.Column('rec_yards', sa.Integer(), nullable=True),
        sa.Column('rec_tds', sa.Integer(), nullable=True),
        sa.Column('total_tds', sa.Integer(), nullable=True),
        sa.Column('touches', sa.Integer(), nullable=True),
        sa.Column('actual_points', sa.Float(), nullable=True),
        sa.Column('salary', sa.Integer(), nullable=True),
        sa.CheckConstraint('week BETWEEN 1 AND 18', name='check_historical_week_range'),
        sa.CheckConstraint('snap_pct BETWEEN 0 AND 1', name='check_snap_pct_range'),
        sa.CheckConstraint('target_share BETWEEN 0 AND 1', name='check_target_share_range'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player_key', 'week', 'season', name='unique_player_week_season')
    )

    # Create indexes for historical_stats table
    op.create_index('idx_historical_stats_player_key', 'historical_stats', ['player_key'])
    op.create_index('idx_historical_stats_week', 'historical_stats', ['week'])
    op.create_index('idx_historical_stats_season', 'historical_stats', ['season'])

    # =====================================================================
    # Table 4: historical_stats_backup
    # =====================================================================
    op.create_table(
        'historical_stats_backup',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_key', sa.String(255), nullable=False),
        sa.Column('week', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('team', sa.String(10), nullable=False),
        sa.Column('opponent', sa.String(10), nullable=True),
        sa.Column('snaps', sa.Integer(), nullable=True),
        sa.Column('snap_pct', sa.Float(), nullable=True),
        sa.Column('rush_attempts', sa.Integer(), nullable=True),
        sa.Column('rush_yards', sa.Integer(), nullable=True),
        sa.Column('rush_tds', sa.Integer(), nullable=True),
        sa.Column('targets', sa.Integer(), nullable=True),
        sa.Column('target_share', sa.Float(), nullable=True),
        sa.Column('receptions', sa.Integer(), nullable=True),
        sa.Column('rec_yards', sa.Integer(), nullable=True),
        sa.Column('rec_tds', sa.Integer(), nullable=True),
        sa.Column('total_tds', sa.Integer(), nullable=True),
        sa.Column('touches', sa.Integer(), nullable=True),
        sa.Column('actual_points', sa.Float(), nullable=True),
        sa.Column('salary', sa.Integer(), nullable=True),
        sa.Column('backed_up_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('week BETWEEN 1 AND 18', name='check_backup_week_range'),
        sa.CheckConstraint('snap_pct BETWEEN 0 AND 1', name='check_backup_snap_pct_range'),
        sa.CheckConstraint('target_share BETWEEN 0 AND 1', name='check_backup_target_share_range'),
        sa.PrimaryKeyConstraint('id')
    )

    # =====================================================================
    # Table 5: player_aliases
    # =====================================================================
    op.create_table(
        'player_aliases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alias_name', sa.String(255), nullable=False),
        sa.Column('canonical_player_key', sa.String(255), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('alias_name', name='unique_alias_name')
    )

    # Create indexes for player_aliases table
    op.create_index('idx_player_aliases_alias_name', 'player_aliases', ['alias_name'])
    op.create_index('idx_player_aliases_canonical_key', 'player_aliases', ['canonical_player_key'])

    # =====================================================================
    # Table 6: import_history
    # =====================================================================
    op.create_table(
        'import_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('week_id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=True),
        sa.Column('player_count', sa.Integer(), nullable=False),
        sa.Column('import_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('imported_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("source IN ('LineStar', 'DraftKings', 'ComprehensiveStats')", name='check_import_source'),
        sa.ForeignKeyConstraint(['week_id'], ['weeks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for import_history table
    op.create_index('idx_import_history_week_source', 'import_history', ['week_id', 'source'])
    op.create_index('idx_import_history_imported_at', 'import_history', ['imported_at'])

    # =====================================================================
    # Table 7: player_pool_history
    # =====================================================================
    op.create_table(
        'player_pool_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('import_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('player_key', sa.String(255), nullable=False),
        sa.Column('salary', sa.Integer(), nullable=True),
        sa.Column('projection', sa.Float(), nullable=True),
        sa.Column('ownership', sa.Float(), nullable=True),
        sa.Column('ceiling', sa.Float(), nullable=True),
        sa.Column('floor', sa.Float(), nullable=True),
        sa.Column('imported_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['import_id'], ['import_history.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for player_pool_history table
    op.create_index('idx_player_pool_history_import_id', 'player_pool_history', ['import_id'])
    op.create_index('idx_player_pool_history_player_key', 'player_pool_history', ['player_key'])

    # =====================================================================
    # Table 8: unmatched_players
    # =====================================================================
    op.create_table(
        'unmatched_players',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('import_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('imported_name', sa.String(255), nullable=False),
        sa.Column('team', sa.String(10), nullable=False),
        sa.Column('position', sa.String(10), nullable=False),
        sa.Column('suggested_player_key', sa.String(255), nullable=True),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('similarity_score BETWEEN 0 AND 1', name='check_similarity_score_range'),
        sa.CheckConstraint("status IN ('pending', 'mapped', 'ignored')", name='check_unmatched_status'),
        sa.ForeignKeyConstraint(['import_id'], ['import_history.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for unmatched_players table
    op.create_index('idx_unmatched_players_import_id', 'unmatched_players', ['import_id'])
    op.create_index('idx_unmatched_players_status', 'unmatched_players', ['status'])


def downgrade():
    """Drop all tables in reverse order to handle foreign key constraints."""

    # Drop tables in reverse order
    op.drop_table('unmatched_players')
    op.drop_table('player_pool_history')
    op.drop_table('import_history')
    op.drop_table('player_aliases')
    op.drop_table('historical_stats_backup')
    op.drop_table('historical_stats')
    op.drop_table('player_pools')
    op.drop_table('weeks')
