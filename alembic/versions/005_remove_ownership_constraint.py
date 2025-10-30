"""remove ownership range constraint

Revision ID: 005
Revises: 004
Create Date: 2025-10-28

Description:
Removes the check_ownership_range constraint from player_pools table.
Ownership values should be accepted as-is from the file with no validation.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """Remove ownership range check constraint."""

    # Drop the ownership range constraint
    op.drop_constraint('check_ownership_range', 'player_pools')


def downgrade():
    """Restore ownership range check constraint."""

    # Restore the original constraint
    op.create_check_constraint(
        'check_ownership_range',
        'player_pools',
        'ownership BETWEEN 0 AND 1'
    )
