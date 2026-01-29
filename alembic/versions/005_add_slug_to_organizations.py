"""add slug to organizations table

Revision ID: 005_add_slug_to_organizations
Revises: 004_add_tax_id_to_organizations
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_add_slug_to_organizations'
down_revision = '004_add_tax_id_to_organizations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add slug column to organizations table (nullable initially)
    op.add_column('organizations', sa.Column('slug', sa.String(length=200), nullable=True))
    
    # Generate slugs for existing organizations based on name
    # This is a simple slug generation - you may want to customize this
    op.execute("""
        UPDATE organizations 
        SET slug = LOWER(REGEXP_REPLACE(name, '[^a-zA-Z0-9]+', '-', 'g'))
        WHERE slug IS NULL
    """)
    
    # Now make slug non-nullable and create unique index
    op.alter_column('organizations', 'slug', nullable=False)
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)


def downgrade() -> None:
    # Drop unique index
    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    
    # Drop slug column
    op.drop_column('organizations', 'slug')
