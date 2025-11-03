"""lower_salary_minimum_for_showdown

Revision ID: f4afa6188f12
Revises: 023
Create Date: 2025-11-02 18:18:34.232423

Description:
Lowers the minimum salary constraint from $1000 to $100 to accommodate
Showdown mode players who can have lower salaries (e.g., kickers, deep bench players).
DraftKings Showdown contests can have players priced as low as $200-$300.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f4afa6188f12'
down_revision = '023'
branch_labels = None
depends_on = None


def upgrade():
    """Lower minimum salary constraint to allow Showdown mode low-priced players."""
    # Drop the existing constraint
    op.drop_constraint('check_salary_range', 'player_pools')
    
    # Create new constraint with lower minimum ($100 instead of $1000)
    # This allows Showdown mode players with salaries as low as $200-$300
    op.create_check_constraint(
        'check_salary_range',
        'player_pools',
        'salary >= 100'  # Minimum $100 to accommodate Showdown mode
    )


def downgrade():
    """Revert to previous minimum salary constraint."""
    # Drop the new constraint
    op.drop_constraint('check_salary_range', 'player_pools')
    
    # Restore the previous constraint
    op.create_check_constraint(
        'check_salary_range',
        'player_pools',
        'salary >= 1000'  # Previous minimum was $1000
    )
