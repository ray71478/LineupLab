"""Create sportsbook_odds table for multi-book Vegas data.

Revision ID: 016
Revises: 015
Create Date: 2025-10-30 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create sportsbook_odds table for storing odds from multiple books."""
    op.create_table(
        "sportsbook_odds",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("week_id", sa.Integer, sa.ForeignKey("weeks.id"), nullable=False),
        sa.Column("team", sa.String(10), nullable=False),
        sa.Column("opponent", sa.String(10), nullable=False),
        sa.Column("sportsbook", sa.String(50), nullable=False),  # DraftKings, FanDuel, etc.
        sa.Column("spread", sa.Float, nullable=True),
        sa.Column("moneyline_odds", sa.Float, nullable=True),
        sa.Column("over_under", sa.Float, nullable=True),
        sa.Column("home_team", sa.Boolean, nullable=False, default=False),
        sa.Column("fetched_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint(
            "week_id", "team", "sportsbook",
            name="uq_week_team_sportsbook"
        ),
    )

    # Create indexes for common queries
    op.create_index(
        "ix_sportsbook_odds_week_team",
        "sportsbook_odds",
        ["week_id", "team"],
    )
    op.create_index(
        "ix_sportsbook_odds_sportsbook",
        "sportsbook_odds",
        ["sportsbook"],
    )


def downgrade() -> None:
    """Drop sportsbook_odds table."""
    op.drop_index("ix_sportsbook_odds_sportsbook")
    op.drop_index("ix_sportsbook_odds_week_team")
    op.drop_table("sportsbook_odds")
