"""create invitations table

Revision ID: 003_create_invitations
Revises: 002_create_organizations
Create Date: 2026-01-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_create_invitations'
down_revision = '002_create_organizations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create invitationstatus enum if it doesn't exist
    invitationstatus_enum = postgresql.ENUM('pending', 'accepted', 'expired', 'cancelled', name='invitationstatus')
    invitationstatus_enum.create(op.get_bind(), checkfirst=True)
    
    # Create invitations table
    # Note: organizationrole enum already exists from previous migration (002_create_organizations)
    # We reference it without creating it
    organizationrole_enum = postgresql.ENUM('owner', 'admin', 'manager', 'employee', name='organizationrole', create_type=False)
    # Also set create_type=False for status enum to prevent double creation
    invitationstatus_enum_for_table = postgresql.ENUM('pending', 'accepted', 'expired', 'cancelled', name='invitationstatus', create_type=False)
    
    op.create_table(
        'invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invited_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', organizationrole_enum, nullable=False),
        sa.Column('token', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', invitationstatus_enum_for_table, nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invitations_id'), 'invitations', ['id'], unique=False)
    op.create_index(op.f('ix_invitations_email'), 'invitations', ['email'], unique=False)
    op.create_index(op.f('ix_invitations_token'), 'invitations', ['token'], unique=True)
    op.create_index(op.f('ix_invitations_organization_id'), 'invitations', ['organization_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_invitations_organization_id'), table_name='invitations')
    op.drop_index(op.f('ix_invitations_token'), table_name='invitations')
    op.drop_index(op.f('ix_invitations_email'), table_name='invitations')
    op.drop_index(op.f('ix_invitations_id'), table_name='invitations')
    op.drop_table('invitations')
    
    # Drop invitationstatus enum if it exists (checkfirst=True prevents error if already dropped)
    invitationstatus_enum = postgresql.ENUM('pending', 'accepted', 'expired', 'cancelled', name='invitationstatus')
    invitationstatus_enum.drop(op.get_bind(), checkfirst=True)