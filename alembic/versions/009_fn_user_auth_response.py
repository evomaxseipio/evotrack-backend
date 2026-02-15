"""add fn_get_user_auth_response function

Revision ID: 009_add_fn_get_user_auth_response
Revises: 2026_01_28_1748-5f2bbe251005_add_user_status_and_activation_fields
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009_fn_user_auth'
down_revision = '5f2bbe251005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE OR REPLACE FUNCTION fn_get_user_auth_response(p_user_id UUID)
    RETURNS JSONB
    LANGUAGE plpgsql
    STABLE
    AS $$
    DECLARE
        v_user_record RECORD;
        v_organizations JSONB;
        v_has_organization BOOLEAN;
    BEGIN
        -- 1. GET USER DATA
        SELECT
            id,
            email,
            first_name,
            last_name,
            CONCAT(first_name, ' ', last_name) as full_name,
            avatar_url,
            phone,
            timezone,
            language,
            status,
            is_active,
            created_at,
            updated_at,
            activated_at,
            last_login_at
        INTO v_user_record
        FROM users
        WHERE id = p_user_id;

        -- Check if user exists
        IF NOT FOUND THEN
            RETURN jsonb_build_object(
                'success', false,
                'error', 'User not found',
                'code', 'USER_NOT_FOUND'
            );
        END IF;

        -- 2. GET USER ORGANIZATIONS WITH COUNTS
        SELECT COALESCE(
            jsonb_agg(
                jsonb_build_object(
                    'id', org.id,
                    'name', org.name,
                    'slug', org.slug,
                    'logoUrl', org.logo_url,
                    'role', uo.role,
                    'membersCount', (
                        SELECT COUNT(*)
                        FROM user_organizations uo2
                        WHERE uo2.organization_id = org.id
                          AND uo2.is_active = true
                    ),
                    'departmentsCount', (
                        SELECT COUNT(*)
                        FROM departments d
                        WHERE d.organization_id = org.id
                          AND d.is_active = true
                    ),
                    'projectsCount', 0  -- No projects table yet
                )
                ORDER BY uo.created_at ASC
            ),
            '[]'::jsonb
        )
        INTO v_organizations
        FROM user_organizations uo
        INNER JOIN organizations org ON org.id = uo.organization_id
        WHERE uo.user_id = p_user_id
          AND uo.is_active = true
          AND org.is_active = true;

        -- 3. DETERMINE HAS_ORGANIZATION
        v_has_organization := jsonb_array_length(v_organizations) > 0;

        -- 4. BUILD AND RETURN RESPONSE
        RETURN jsonb_build_object(
            'success', true,
            'data', jsonb_build_object(
                'id', v_user_record.id,
                'email', v_user_record.email,
                'firstName', v_user_record.first_name,
                'lastName', v_user_record.last_name,
                'fullName', v_user_record.full_name,
                'avatarUrl', v_user_record.avatar_url,
                'phone', v_user_record.phone,
                'timezone', v_user_record.timezone,
                'language', v_user_record.language,
                'status', LOWER(v_user_record.status::TEXT),
                'isActive', v_user_record.is_active,
                'hasOrganization', v_has_organization,
                'createdAt', v_user_record.created_at,
                'updatedAt', v_user_record.updated_at,
                'activatedAt', v_user_record.activated_at,
                'lastLoginAt', v_user_record.last_login_at,
                'organizations', v_organizations
            )
        );

    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'Error in fn_get_user_auth_response: % | user_id: %',
            SQLERRM, p_user_id;

        RETURN jsonb_build_object(
            'success', false,
            'error', 'Internal server error',
            'details', SQLERRM
        );
    END;
    $$;
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS fn_get_user_auth_response(UUID)")
