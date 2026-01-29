"""add user status and activation fields

Revision ID: 5f2bbe251005
Revises: 008_add_user_stored_procedures
Create Date: 2026-01-28 17:48:59.048120

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import app.modules.organizations.models

# revision identifiers, used by Alembic.
revision = '5f2bbe251005'
down_revision = '008_add_user_stored_procedures'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Handle the transition of enums to custom type decorators if they weren't already
    op.execute("ALTER TABLE invitations ALTER COLUMN role TYPE VARCHAR(20)")
    op.execute("ALTER TABLE invitations ALTER COLUMN status TYPE VARCHAR(20)")
    op.execute("ALTER TABLE user_organizations ALTER COLUMN role TYPE VARCHAR(20)")
    
    # Add new status column with Enum
    # In PostgreSQL we need to create the type first
    op.execute("CREATE TYPE userstatus AS ENUM ('PENDING_ACTIVATION', 'ACTIVE', 'INACTIVE')")
    
    op.add_column('users', sa.Column('status', sa.Enum('PENDING_ACTIVATION', 'ACTIVE', 'INACTIVE', name='userstatus'), nullable=False, server_default='ACTIVE'))
    op.add_column('users', sa.Column('activation_token', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('activation_token_expires', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('activated_at', sa.DateTime(), nullable=True))
    
    op.alter_column('users', 'password_hash',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
               
    op.create_index(op.f('ix_users_activation_token'), 'users', ['activation_token'], unique=True)
    op.create_index(op.f('ix_users_status'), 'users', ['status'], unique=False)
    
    # Allow organizations tax_id to be NOT NULL if it was nullable before (sync with model)
    # Check if organizations table exists and adjust
    op.alter_column('organizations', 'tax_id',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_status'), table_name='users')
    op.drop_index(op.f('ix_users_activation_token'), table_name='users')
    op.alter_column('users', 'password_hash',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
    op.drop_column('users', 'activated_at')
    op.drop_column('users', 'activation_token_expires')
    op.drop_column('users', 'activation_token')
    op.drop_column('users', 'status')
    
    op.execute("DROP TYPE userstatus")
    
    op.alter_column('organizations', 'tax_id',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
               
    # Revert role types if necessary (though VARCHAR(20) is usually compatible with ENUM)
    # This part might be tricky if we want to go back to actual ENUM types
