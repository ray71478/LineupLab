"""Add weight_profiles table for Smart Score Engine

Revision ID: 010
Revises: 009
Create Date: 2025-10-30 00:00:00.000000

Description:
Creates weight_profiles table for storing custom weight profiles for Smart Score calculations.
Includes default "Base" profile with equal weights (0.125 each for W1-W8).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create weight_profiles table with default Base profile."""
    
    # Create weight_profiles table
    op.create_table(
        'weight_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('weights', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='unique_weight_profile_name')
    )
    
    # Create index on name column for faster lookups
    op.create_index('idx_weight_profiles_name', 'weight_profiles', ['name'])
    
    # Create index on is_default for quick default profile lookup
    op.create_index('idx_weight_profiles_is_default', 'weight_profiles', ['is_default'])
    
    # Insert default "Base" profile with equal weights (0.125 each)
    op.execute("""
        INSERT INTO weight_profiles (name, weights, config, is_default)
        VALUES (
            'Base',
            '{"W1": 0.125, "W2": 0.125, "W3": 0.125, "W4": 0.125, "W5": 0.125, "W6": 0.125, "W7": 0.125, "W8": 0.125}'::jsonb,
            '{"projection_source": "ETR", "eighty_twenty_enabled": true, "eighty_twenty_threshold": 20.0}'::jsonb,
            true
        )
    """)


def downgrade() -> None:
    """Drop weight_profiles table."""
    op.drop_index('idx_weight_profiles_is_default', table_name='weight_profiles')
    op.drop_index('idx_weight_profiles_name', table_name='weight_profiles')
    op.drop_table('weight_profiles')

