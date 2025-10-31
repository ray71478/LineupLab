"""Add moneyline odds column to vegas_lines table.

Revision ID: 015
Revises: 014
Create Date: 2025-10-30 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add moneyline_odds column to vegas_lines table."""
    op.add_column(
        "vegas_lines",
        sa.Column("moneyline_odds", sa.Float, nullable=True),
    )


def downgrade() -> None:
    """Remove moneyline_odds column from vegas_lines table."""
    op.drop_column("vegas_lines", "moneyline_odds")
