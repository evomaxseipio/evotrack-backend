"""create organizations tables

Revision ID: 002_create_organizations
Revises: 001_create_users
Create Date: 2026-01-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_create_organizations'
down_revision = '001_create_users'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('currency_code', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    
    # Create user_organizations table
    op.create_table(
        'user_organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.Enum('owner', 'admin', 'manager', 'employee', name='organizationrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_organizations_id'), 'user_organizations', ['id'], unique=False)
    op.create_index(op.f('ix_user_organizations_user_id'), 'user_organizations', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_organizations_organization_id'), 'user_organizations', ['organization_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_organizations_organization_id'), table_name='user_organizations')
    op.drop_index(op.f('ix_user_organizations_user_id'), table_name='user_organizations')
    op.drop_index(op.f('ix_user_organizations_id'), table_name='user_organizations')
    op.drop_table('user_organizations')
    
    op.drop_index(op.f('ix_organizations_id'), table_name='organizations')
    op.drop_table('organizations')