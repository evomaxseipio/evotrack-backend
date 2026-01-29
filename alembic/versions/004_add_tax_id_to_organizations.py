"""add tax_id to organizations table

Revision ID: 004_add_tax_id_to_organizations
Revises: 003_create_invitations
Create Date: 2026-01-09

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_add_tax_id_to_organizations'
down_revision = '003_create_invitations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add tax_id column to organizations table
    # Note: Making it nullable=True initially to allow existing organizations.
    # Organizations should be updated with their tax_id, then a follow-up migration
    # can make it nullable=False if needed.
    op.add_column('organizations', sa.Column('tax_id', sa.String(length=50), nullable=True))
    
    # Create unique index on tax_id (allows NULL values in unique index)
    op.create_index(op.f('ix_organizations_tax_id'), 'organizations', ['tax_id'], unique=True)


def downgrade() -> None:
    # Drop unique index
    op.drop_index(op.f('ix_organizations_tax_id'), table_name='organizations')
    
    # Drop tax_id column
    op.drop_column('organizations', 'tax_id')
