"""make week_id nullable for comprehensive stats

Revision ID: 006
Revises: 005
Create Date: 2025-10-28

Description:
Makes week_id nullable in import_history table to support ComprehensiveStats
imports which are cross-season and don't belong to a specific week.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    """Make week_id nullable in import_history table."""

    # Drop the foreign key constraint first
    op.drop_constraint('import_history_week_id_fkey', 'import_history', type_='foreignkey')

    # Modify the column to be nullable
    op.alter_column('import_history', 'week_id', existing_type=sa.Integer(), nullable=True)

    # Re-add the foreign key constraint but with on_delete=SET NULL
    op.create_foreign_key(
        'import_history_week_id_fkey',
        'import_history',
        'weeks',
        ['week_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    """Revert week_id to NOT NULL in import_history table."""

    # Drop the foreign key constraint
    op.drop_constraint('import_history_week_id_fkey', 'import_history', type_='foreignkey')

    # Modify the column to be NOT NULL
    op.alter_column('import_history', 'week_id', existing_type=sa.Integer(), nullable=False)

    # Re-add the original foreign key constraint
    op.create_foreign_key(
        'import_history_week_id_fkey',
        'import_history',
        'weeks',
        ['week_id'],
        ['id'],
        ondelete='CASCADE'
    )
