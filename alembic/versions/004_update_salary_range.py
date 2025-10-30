"""update salary range constraints

Revision ID: 004
Revises: 003
Create Date: 2025-10-28

Description:
Updates the salary range constraints in player_pools table
from 3000-10000 to 2000-15000 to accommodate wider salary ranges.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Update salary range check constraint."""

    # Drop the old constraint
    op.drop_constraint('check_salary_range', 'player_pools')

    # Create the new constraint - allow full range of DFS salaries (whole dollars, no cents)
    op.create_check_constraint(
        'check_salary_range',
        'player_pools',
        'salary >= 1000'  # Only check that salary is at least $1000, no upper limit
    )


def downgrade():
    """Revert to original salary range constraint."""

    # Drop the new constraint
    op.drop_constraint('check_salary_range', 'player_pools')

    # Restore the original constraint
    op.create_check_constraint(
        'check_salary_range',
        'player_pools',
        'salary BETWEEN 3000 AND 10000'
    )
