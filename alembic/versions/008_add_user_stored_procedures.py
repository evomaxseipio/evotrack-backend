"""add user stored procedures

Revision ID: 008_add_user_stored_procedures
Revises: 007_create_departments
Create Date: 2026-01-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008_add_user_stored_procedures'
down_revision = '007_create_departments'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create function for user creation
    op.execute("""
    CREATE OR REPLACE FUNCTION create_user_sp(
        p_email VARCHAR,
        p_password_hash VARCHAR,
        p_first_name VARCHAR,
        p_last_name VARCHAR,
        p_timezone VARCHAR DEFAULT 'UTC'
    ) RETURNS UUID AS $$
    DECLARE
        v_user_id UUID;
    BEGIN
        v_user_id := gen_random_uuid();
        
        INSERT INTO users (id, email, password_hash, first_name, last_name, timezone, is_active, created_at, updated_at)
        VALUES (v_user_id, LOWER(p_email), p_password_hash, p_first_name, p_last_name, p_timezone, TRUE, NOW(), NOW());
        
        RETURN v_user_id;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Create function for user update
    op.execute("""
    CREATE OR REPLACE FUNCTION update_user_sp(
        p_user_id UUID,
        p_first_name VARCHAR DEFAULT NULL,
        p_last_name VARCHAR DEFAULT NULL,
        p_email VARCHAR DEFAULT NULL
    ) RETURNS BOOLEAN AS $$
    BEGIN
        UPDATE users
        SET 
            first_name = COALESCE(p_first_name, first_name),
            last_name = COALESCE(p_last_name, last_name),
            email = COALESCE(LOWER(p_email), email),
            updated_at = NOW()
        WHERE id = p_user_id;
        
        RETURN FOUND;
    END;
    $$ LANGUAGE plpgsql;
    """)

def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS create_user_sp(VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR)")
    op.execute("DROP FUNCTION IF EXISTS update_user_sp(UUID, VARCHAR, VARCHAR, VARCHAR)")
