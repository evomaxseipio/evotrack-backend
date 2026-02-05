"""update fn_get_organization_users_json with advanced filters and stats

Revision ID: 010_update_fn_org_users
Revises: 009_fn_user_auth
Create Date: 2026-01-31

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010_update_fn_org_users'
down_revision = '009_fn_user_auth'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing function first
    op.execute("DROP FUNCTION IF EXISTS fn_get_organization_users_json(UUID, UUID, INTEGER, JSONB, BOOLEAN, TEXT)")
    
    # Create updated function with advanced filters and stats
    op.execute("""
    CREATE OR REPLACE FUNCTION fn_get_organization_users_json(
        p_org_id UUID,
        p_current_user_id UUID,
        p_limit INTEGER DEFAULT 20,
        p_cursor JSONB DEFAULT NULL,
        p_include_inactive BOOLEAN DEFAULT false,
        p_search TEXT DEFAULT NULL,
        p_status_filter TEXT[] DEFAULT NULL,
        p_role_filter TEXT[] DEFAULT NULL,
        p_is_active_filter BOOLEAN DEFAULT NULL,
        p_created_from TIMESTAMPTZ DEFAULT NULL,
        p_created_to TIMESTAMPTZ DEFAULT NULL
    ) RETURNS JSONB
    LANGUAGE plpgsql
    STABLE
    AS $$
    DECLARE
        v_user_role TEXT;
        v_can_see_emails BOOLEAN;
        v_cursor_ts TIMESTAMPTZ;
        v_cursor_id UUID;
    BEGIN
        -- 1. PARAMETER VALIDATION
        IF p_limit NOT BETWEEN 1 AND 100 THEN
            RETURN jsonb_build_object(
                'success', false,
                'error', 'Invalid limit (1-100)',
                'code', 'INVALID_LIMIT'
            );
        END IF;
        
        -- 2. PERMISSION CHECK
        SELECT role INTO v_user_role
        FROM user_organizations
        WHERE organization_id = p_org_id
          AND user_id = p_current_user_id
          AND is_active = true;
        
        IF NOT FOUND THEN
            RETURN jsonb_build_object(
                'success', false,
                'error', 'Access denied',
                'code', 'NOT_MEMBER'
            );
        END IF;
        
        v_can_see_emails := (v_user_role IN ('admin', 'owner'));
        
        -- 3. PARSE CURSOR
        IF p_cursor IS NOT NULL THEN
            v_cursor_ts := NULLIF(p_cursor->>'ts', '')::TIMESTAMPTZ;
            v_cursor_id := NULLIF(p_cursor->>'id', '')::UUID;

            IF v_cursor_ts IS NULL OR v_cursor_id IS NULL THEN
                RETURN jsonb_build_object(
                    'success', false,
                    'error', 'Invalid cursor format',
                    'code', 'INVALID_CURSOR'
                );
            END IF;
        END IF;

        -- 4. MAIN QUERY WITH FILTERS AND STATS
        RETURN (
            WITH 
            -- CTE con TODOS los usuarios filtrados (para stats, sin paginación ni búsqueda de texto)
            filtered_users AS (
                SELECT 
                    u.id,
                    u.status,
                    uo.role,
                    uo.is_active
                FROM users u
                INNER JOIN user_organizations uo ON u.id = uo.user_id
                WHERE uo.organization_id = p_org_id
                  -- Aplicar filtros (pero NO búsqueda de texto ni cursor)
                  AND (
                      p_is_active_filter IS NULL 
                      OR uo.is_active = p_is_active_filter
                      OR (p_is_active_filter IS NULL AND p_include_inactive = true)
                  )
                  AND (p_status_filter IS NULL OR u.status = ANY(p_status_filter))
                  AND (p_role_filter IS NULL OR uo.role = ANY(p_role_filter))
                  AND (p_created_from IS NULL OR u.created_at >= p_created_from)
                  AND (p_created_to IS NULL OR u.created_at <= p_created_to)
            ),
            -- Calcular estadísticas sobre usuarios filtrados
            stats_data AS (
                SELECT
                    COUNT(*) as total_users,
                    COUNT(*) FILTER (WHERE status = 'active') as active_users,
                    COUNT(*) FILTER (WHERE status = 'pending_activation') as pending_activation,
                    COUNT(*) FILTER (WHERE status = 'inactive') as inactive_users,
                    
                    COUNT(*) FILTER (WHERE role = 'owner') as owners,
                    COUNT(*) FILTER (WHERE role = 'admin') as admins,
                    COUNT(*) FILTER (WHERE role = 'manager') as managers,
                    COUNT(*) FILTER (WHERE role = 'employee') as employees,
                    
                    COUNT(*) FILTER (WHERE status = 'active') as status_active,
                    COUNT(*) FILTER (WHERE status = 'pending_activation') as status_pending,
                    COUNT(*) FILTER (WHERE status = 'inactive') as status_inactive
                FROM filtered_users
            ),
            -- CTE para la página de usuarios (con búsqueda y cursor)
            user_page AS (
                SELECT 
                    u.id,
                    u.email,
                    u.first_name,
                    u.last_name,
                    u.avatar_url,
                    u.status,
                    u.created_at,
                    uo.role,
                    uo.is_active,
                    CASE 
                        WHEN v_can_see_emails THEN u.email
                        WHEN u.id = p_current_user_id THEN u.email
                        ELSE CONCAT(
                            LEFT(split_part(u.email, '@', 1), 2),
                            '***@',
                            split_part(u.email, '@', 2)
                        )
                    END as display_email
                FROM users u
                INNER JOIN user_organizations uo ON u.id = uo.user_id
                WHERE uo.organization_id = p_org_id
                  -- Todos los filtros (incluyendo búsqueda y cursor)
                  AND (
                      p_is_active_filter IS NULL 
                      OR uo.is_active = p_is_active_filter
                      OR (p_is_active_filter IS NULL AND p_include_inactive = true)
                  )
                  AND (p_status_filter IS NULL OR u.status = ANY(p_status_filter))
                  AND (p_role_filter IS NULL OR uo.role = ANY(p_role_filter))
                  AND (p_created_from IS NULL OR u.created_at >= p_created_from)
                  AND (p_created_to IS NULL OR u.created_at <= p_created_to)
                  AND (
                      p_cursor IS NULL 
                      OR (u.created_at, u.id) < (v_cursor_ts, v_cursor_id)
                  )
                  AND (
                      p_search IS NULL 
                      OR u.first_name ILIKE '%' || p_search || '%'
                      OR u.last_name ILIKE '%' || p_search || '%'
                      OR (v_can_see_emails AND u.email ILIKE '%' || p_search || '%')
                  )
                ORDER BY u.created_at DESC, u.id DESC
                LIMIT p_limit + 1
            ),
            numbered_users AS (
                SELECT 
                    *,
                    ROW_NUMBER() OVER (ORDER BY created_at DESC, id DESC) as row_num
                FROM user_page
            ),
            page_data AS (
                SELECT
                    COUNT(*) as total_fetched,
                    jsonb_agg(
                        CASE WHEN row_num <= p_limit THEN
                            jsonb_build_object(
                                'id', id,
                                'email', display_email,
                                'firstName', first_name,
                                'lastName', last_name,
                                'avatarUrl', avatar_url,
                                'status', status,
                                'role', role,
                                'isActive', is_active,
                                'createdAt', created_at
                            )
                        END
                    ) as users
                FROM numbered_users
            ),
            cursor_data AS (
                SELECT
                    created_at as last_ts,
                    id as last_id
                FROM numbered_users
                WHERE row_num = p_limit
                LIMIT 1
            )
            -- Construir respuesta final
            SELECT jsonb_build_object(
                'success', true,
                'data', COALESCE((SELECT users FROM page_data), '[]'::jsonb),
                'meta', jsonb_build_object(
                    'userRole', v_user_role,
                    'canSeeEmails', v_can_see_emails,
                    'organizationId', p_org_id
                ),
                'stats', COALESCE(
                    (
                        SELECT jsonb_build_object(
                            'totalUsers', total_users,
                            'activeUsers', active_users,
                            'pendingActivation', pending_activation,
                            'inactiveUsers', inactive_users,
                            'byRole', jsonb_build_object(
                                'owner', owners,
                                'admin', admins,
                                'manager', managers,
                                'employee', employees
                            ),
                            'byStatus', jsonb_build_object(
                                'active', status_active,
                                'pendingActivation', status_pending,
                                'inactive', status_inactive
                            )
                        )
                        FROM stats_data
                    ),
                    jsonb_build_object(
                        'totalUsers', 0,
                        'activeUsers', 0,
                        'pendingActivation', 0,
                        'inactiveUsers', 0,
                        'byRole', jsonb_build_object('owner', 0, 'admin', 0, 'manager', 0, 'employee', 0),
                        'byStatus', jsonb_build_object('active', 0, 'pendingActivation', 0, 'inactive', 0)
                    )
                ),
                'pagination', jsonb_build_object(
                    'count', COALESCE((SELECT COUNT(*) FILTER (WHERE row_num <= p_limit) FROM numbered_users), 0),
                    'limit', p_limit,
                    'hasMore', COALESCE((SELECT total_fetched > p_limit FROM page_data), false),
                    'nextCursor', CASE 
                        WHEN COALESCE((SELECT total_fetched > p_limit FROM page_data), false) THEN
                            (SELECT jsonb_build_object('ts', last_ts, 'id', last_id) FROM cursor_data)
                        ELSE NULL
                    END
                )
            )
        );
        
    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'Error in fn_get_organization_users_json: % | org_id: %, user_id: %',
            SQLERRM, p_org_id, p_current_user_id;

        RETURN jsonb_build_object(
            'success', false,
            'error', 'Internal server error',
            'details', SQLERRM
        );
    END;
    $$;
    """)


def downgrade() -> None:
    # Drop the updated function
    op.execute("DROP FUNCTION IF EXISTS fn_get_organization_users_json(UUID, UUID, INTEGER, JSONB, BOOLEAN, TEXT, TEXT[], TEXT[], BOOLEAN, TIMESTAMPTZ, TIMESTAMPTZ)")
    
    # Restore original function (without filters and stats)
    op.execute("""
    CREATE OR REPLACE FUNCTION fn_get_organization_users_json(
        p_org_id UUID,
        p_current_user_id UUID,
        p_limit INTEGER DEFAULT 20,
        p_cursor JSONB DEFAULT NULL,
        p_include_inactive BOOLEAN DEFAULT false,
        p_search TEXT DEFAULT NULL
    ) RETURNS JSONB
    LANGUAGE plpgsql
    STABLE
    AS $$
    DECLARE
        v_user_role TEXT;
        v_can_see_emails BOOLEAN;
        v_cursor_ts TIMESTAMPTZ;
        v_cursor_id UUID;
    BEGIN
        -- 1. PARAMETER VALIDATION
        IF p_limit NOT BETWEEN 1 AND 100 THEN
            RETURN jsonb_build_object(
                'success', false,
                'error', 'Invalid limit (1-100)',
                'code', 'INVALID_LIMIT'
            );
        END IF;
        
        -- 2. PERMISSION CHECK
        SELECT role INTO v_user_role
        FROM user_organizations
        WHERE organization_id = p_org_id
          AND user_id = p_current_user_id
          AND is_active = true;
        
        IF NOT FOUND THEN
            RETURN jsonb_build_object(
                'success', false,
                'error', 'Access denied',
                'code', 'NOT_MEMBER'
            );
        END IF;
        
        v_can_see_emails := (v_user_role IN ('admin', 'owner'));
        
        -- 3. PARSE CURSOR
        IF p_cursor IS NOT NULL THEN
            v_cursor_ts := NULLIF(p_cursor->>'ts', '')::TIMESTAMPTZ;
            v_cursor_id := NULLIF(p_cursor->>'id', '')::UUID;

            IF v_cursor_ts IS NULL OR v_cursor_id IS NULL THEN
                RETURN jsonb_build_object(
                    'success', false,
                    'error', 'Invalid cursor format',
                    'code', 'INVALID_CURSOR'
                );
            END IF;
        END IF;

        -- 4. MAIN QUERY (original version)
        RETURN (
            WITH user_page AS (
                SELECT 
                    u.id,
                    u.email,
                    u.first_name,
                    u.last_name,
                    u.avatar_url,
                    u.status,
                    u.created_at,
                    uo.role,
                    uo.is_active,
                    CASE 
                        WHEN v_can_see_emails THEN u.email
                        WHEN u.id = p_current_user_id THEN u.email
                        ELSE CONCAT(
                            LEFT(split_part(u.email, '@', 1), 2),
                            '***@',
                            split_part(u.email, '@', 2)
                        )
                    END as display_email
                FROM users u
                INNER JOIN user_organizations uo ON u.id = uo.user_id
                WHERE uo.organization_id = p_org_id
                  AND (p_include_inactive OR uo.is_active = true)
                  AND (
                      p_cursor IS NULL 
                      OR (u.created_at, u.id) < (v_cursor_ts, v_cursor_id)
                  )
                  AND (
                      p_search IS NULL 
                      OR u.first_name ILIKE '%' || p_search || '%'
                      OR u.last_name ILIKE '%' || p_search || '%'
                      OR (v_can_see_emails AND u.email ILIKE '%' || p_search || '%')
                  )
                ORDER BY u.created_at DESC, u.id DESC
                LIMIT p_limit + 1
            ),
            numbered_users AS (
                SELECT 
                    *,
                    ROW_NUMBER() OVER (ORDER BY created_at DESC, id DESC) as row_num
                FROM user_page
            ),
            page_data AS (
                SELECT
                    COUNT(*) as total_fetched,
                    jsonb_agg(
                        CASE WHEN row_num <= p_limit THEN
                            jsonb_build_object(
                                'id', id,
                                'email', display_email,
                                'firstName', first_name,
                                'lastName', last_name,
                                'avatarUrl', avatar_url,
                                'status', status,
                                'role', role,
                                'isActive', is_active,
                                'createdAt', created_at
                            )
                        END
                    ) as users
                FROM numbered_users
            ),
            cursor_data AS (
                SELECT
                    created_at as last_ts,
                    id as last_id
                FROM numbered_users
                WHERE row_num = p_limit
                LIMIT 1
            )
            SELECT jsonb_build_object(
                'success', true,
                'data', COALESCE((SELECT users FROM page_data), '[]'::jsonb),
                'meta', jsonb_build_object(
                    'userRole', v_user_role,
                    'canSeeEmails', v_can_see_emails,
                    'organizationId', p_org_id
                ),
                'pagination', jsonb_build_object(
                    'count', COALESCE((SELECT COUNT(*) FILTER (WHERE row_num <= p_limit) FROM numbered_users), 0),
                    'limit', p_limit,
                    'hasMore', COALESCE((SELECT total_fetched > p_limit FROM page_data), false),
                    'nextCursor', CASE 
                        WHEN COALESCE((SELECT total_fetched > p_limit FROM page_data), false) THEN
                            (SELECT jsonb_build_object('ts', last_ts, 'id', last_id) FROM cursor_data)
                        ELSE NULL
                    END
                )
            )
        );
    END;
    $$;
    """)
