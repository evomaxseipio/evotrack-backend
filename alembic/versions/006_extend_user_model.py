"""extend user model

Revision ID: 006_extend_user_model
Revises: 005_add_slug_to_organizations
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_extend_user_model'
down_revision = '005_add_slug_to_organizations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add profile fields
    op.add_column('users', sa.Column('identification', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('date_of_birth', sa.Date(), nullable=True))
    op.add_column('users', sa.Column('nationality', sa.String(length=100), nullable=True))
    
    # Add settings fields
    op.add_column('users', sa.Column('language', sa.String(length=10), nullable=False, server_default='en'))
    op.add_column('users', sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Add email verification fields
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(), nullable=True))
    
    # Add authentication tracking
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Drop authentication tracking
    op.drop_column('users', 'last_login_at')
    
    # Drop email verification fields
    op.drop_column('users', 'email_verified_at')
    op.drop_column('users', 'email_verified')
    
    # Drop settings fields
    op.drop_column('users', 'preferences')
    op.drop_column('users', 'language')
    
    # Drop profile fields
    op.drop_column('users', 'nationality')
    op.drop_column('users', 'date_of_birth')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'identification')
