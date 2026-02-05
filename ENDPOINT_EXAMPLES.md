# Ejemplos de Uso del Endpoint de Búsqueda de Usuarios

## Endpoint
```
POST /api/v1/organizations/{org_id}/users/search
```

---

## Ejemplo 1: Búsqueda Básica (Sin Filtros)

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/organizations/2b76e903-3158-466c-ac14-63153c85aa77/users/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "limit": 20
  }'
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "8f117a36-3658-4ec5-9aae-9cf0578869d2",
      "email": "epena@deco.com",
      "firstName": "Eduardo",
      "lastName": "Peña",
      "avatarUrl": null,
      "status": "active",
      "role": "owner",
      "isActive": true,
      "createdAt": "2026-01-14T03:24:36.361975"
    },
    {
      "id": "5d5ff144-58e6-456d-a69c-c998b700bf79",
      "email": "ma***@hotmail.com",
      "firstName": "Max",
      "lastName": "Seipio",
      "avatarUrl": null,
      "status": "pending_activation",
      "role": "member",
      "isActive": true,
      "createdAt": "2026-01-20T10:15:00.000000"
    }
  ],
  "meta": {
    "userRole": "admin",
    "canSeeEmails": true,
    "organizationId": "2b76e903-3158-466c-ac14-63153c85aa77"
  },
  "stats": {
    "totalUsers": 5,
    "activeUsers": 4,
    "pendingActivation": 1,
    "inactiveUsers": 0,
    "byRole": {
      "owner": 1,
      "admin": 0,
      "manager": 0,
      "employee": 4
    },
    "byStatus": {
      "active": 4,
      "pendingActivation": 1,
      "inactive": 0
    }
  },
  "pagination": {
    "count": 5,
    "limit": 20,
    "hasMore": false,
    "nextCursor": null
  }
}
```

---

## Ejemplo 2: Filtrar por Status "ACTIVE"

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/organizations/2b76e903-3158-466c-ac14-63153c85aa77/users/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "limit": 20,
    "status": ["active"]
  }'
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "8f117a36-3658-4ec5-9aae-9cf0578869d2",
      "email": "epena@deco.com",
      "firstName": "Eduardo",
      "lastName": "Peña",
      "status": "active",
      "role": "owner",
      "isActive": true,
      "createdAt": "2026-01-14T03:24:36.361975"
    }
  ],
  "meta": {
    "userRole": "admin",
    "canSeeEmails": true,
    "organizationId": "2b76e903-3158-466c-ac14-63153c85aa77"
  },
  "stats": {
    "totalUsers": 4,
    "activeUsers": 4,
    "pendingActivation": 0,
    "inactiveUsers": 0,
    "byRole": {
      "owner": 1,
      "admin": 0,
      "manager": 0,
      "employee": 3
    },
    "byStatus": {
      "active": 4,
      "pendingActivation": 0,
      "inactive": 0
    }
  },
  "pagination": {
    "count": 4,
    "limit": 20,
    "hasMore": false,
    "nextCursor": null
  }
}
```

---

## Ejemplo 3: Filtrar por Rol "owner"

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/organizations/2b76e903-3158-466c-ac14-63153c85aa77/users/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "limit": 20,
    "role": ["owner"]
  }'
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "8f117a36-3658-4ec5-9aae-9cf0578869d2",
      "email": "epena@deco.com",
      "firstName": "Eduardo",
      "lastName": "Peña",
      "status": "active",
      "role": "owner",
      "isActive": true,
      "createdAt": "2026-01-14T03:24:36.361975"
    }
  ],
  "meta": {
    "userRole": "admin",
    "canSeeEmails": true,
    "organizationId": "2b76e903-3158-466c-ac14-63153c85aa77"
  },
  "stats": {
    "totalUsers": 1,
    "activeUsers": 1,
    "pendingActivation": 0,
    "inactiveUsers": 0,
    "byRole": {
      "owner": 1,
      "admin": 0,
      "manager": 0,
      "employee": 0
    },
    "byStatus": {
      "active": 1,
      "pendingActivation": 0,
      "inactive": 0
    }
  },
  "pagination": {
    "count": 1,
    "limit": 20,
    "hasMore": false,
    "nextCursor": null
  }
}
```

---

## Ejemplo 4: Filtrar por Múltiples Status

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/organizations/2b76e903-3158-466c-ac14-63153c85aa77/users/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "limit": 20,
    "status": ["active", "pending_activation"]
  }'
```

---

## Ejemplo 5: Filtrar por Rango de Fechas

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/organizations/2b76e903-3158-466c-ac14-63153c85aa77/users/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "limit": 20,
    "createdFrom": "2026-01-14T00:00:00",
    "createdTo": "2026-01-20T23:59:59"
  }'
```

---

## Ejemplo 6: Combinar Múltiples Filtros

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/organizations/2b76e903-3158-466c-ac14-63153c85aa77/users/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "limit": 20,
    "status": ["active"],
    "role": ["owner", "admin"],
    "isActive": true,
    "createdFrom": "2026-01-01T00:00:00",
    "search": "eduardo"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "8f117a36-3658-4ec5-9aae-9cf0578869d2",
      "email": "epena@deco.com",
      "firstName": "Eduardo",
      "lastName": "Peña",
      "status": "active",
      "role": "owner",
      "isActive": true,
      "createdAt": "2026-01-14T03:24:36.361975"
    }
  ],
  "meta": {
    "userRole": "admin",
    "canSeeEmails": true,
    "organizationId": "2b76e903-3158-466c-ac14-63153c85aa77"
  },
  "stats": {
    "totalUsers": 1,
    "activeUsers": 1,
    "pendingActivation": 0,
    "inactiveUsers": 0,
    "byRole": {
      "owner": 1,
      "admin": 0,
      "manager": 0,
      "employee": 0
    },
    "byStatus": {
      "active": 1,
      "pendingActivation": 0,
      "inactive": 0
    }
  },
  "pagination": {
    "count": 1,
    "limit": 20,
    "hasMore": false,
    "nextCursor": null
  }
}
```

---

## Ejemplo 7: Búsqueda de Texto

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/organizations/2b76e903-3158-466c-ac14-63153c85aa77/users/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "limit": 20,
    "search": "max"
  }'
```

---

## Ejemplo 8: Paginación con Cursor

**Request (Primera página):**
```bash
curl -X POST "http://localhost:8000/api/v1/organizations/2b76e903-3158-466c-ac14-63153c85aa77/users/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "limit": 2
  }'
```

**Response (Primera página):**
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "count": 2,
    "limit": 2,
    "hasMore": true,
    "nextCursor": {
      "id": "5d5ff144-58e6-456d-a69c-c998b700bf79",
      "ts": "2026-01-20T10:15:00.000000"
    }
  }
}
```

**Request (Segunda página con cursor):**
```bash
curl -X POST "http://localhost:8000/api/v1/organizations/2b76e903-3158-466c-ac14-63153c85aa77/users/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "limit": 2,
    "nextCursor": {
      "id": "5d5ff144-58e6-456d-a69c-c998b700bf79",
      "ts": "2026-01-20T10:15:00.000000"
    }
  }'
```

---

## Filtros Disponibles

| Filtro | Tipo | Valores Posibles | Descripción |
|--------|------|------------------|-------------|
| `status` | `array[string]` | `active`, `pending_activation`, `inactive` | Filtra por status del usuario |
| `role` | `array[string]` | `owner`, `admin`, `manager`, `employee` | Filtra por rol en la organización |
| `isActive` | `boolean` | `true`, `false` | Filtra por estado activo/inactivo |
| `createdFrom` | `datetime` | ISO 8601 | Usuarios creados desde esta fecha |
| `createdTo` | `datetime` | ISO 8601 | Usuarios creados hasta esta fecha |
| `search` | `string` | Texto libre | Búsqueda por nombre o email |
| `limit` | `integer` | 1-100 | Máximo de resultados (default: 20) |
| `nextCursor` | `object` | `{id, ts}` | Cursor para paginación |

---

## Objeto Stats en la Respuesta

El objeto `stats` siempre se incluye en la respuesta y contiene:

```json
{
  "totalUsers": 25,           // Total de usuarios que cumplen los filtros
  "activeUsers": 20,          // Usuarios con status "active"
  "pendingActivation": 3,     // Usuarios con status "pending_activation"
  "inactiveUsers": 2,         // Usuarios con status "inactive"
  "byRole": {
    "owner": 1,               // Número de owners
    "admin": 2,               // Número de admins
    "manager": 5,             // Número de managers
    "employee": 17            // Número de employees
  },
  "byStatus": {
    "active": 20,             // Usuarios activos
    "pendingActivation": 3,   // Usuarios pendientes
    "inactive": 2             // Usuarios inactivos
  }
}
```

**Nota:** Las estadísticas reflejan **solo los usuarios que cumplen con los filtros aplicados**, no el total de la organización.

---

## Errores Comunes

### Error 400: Valor de status inválido
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "status"],
      "msg": "Invalid status 'ACTIVE'. Must be one of: active, pending_activation, inactive"
    }
  ]
}
```
**Solución:** Usar valores en minúsculas: `active`, `pending_activation`, `inactive`

### Error 400: Valor de role inválido
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "role"],
      "msg": "Invalid role 'OWNER'. Must be one of: owner, admin, manager, employee"
    }
  ]
}
```
**Solución:** Usar valores en minúsculas: `owner`, `admin`, `manager`, `employee`

### Error 400: Rango de fechas inválido
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "createdTo"],
      "msg": "createdTo must be greater than or equal to createdFrom"
    }
  ]
}
```
**Solución:** Asegurar que `createdTo` >= `createdFrom`

---

## Notas Importantes

1. **Valores de enum en minúsculas:** Los valores de `status` y `role` deben estar en minúsculas (`active`, no `ACTIVE`)
2. **Estadísticas filtradas:** El objeto `stats` refleja solo los usuarios que cumplen con los filtros aplicados
3. **Email ofuscado:** Los emails se ofuscan para usuarios que no son admin/owner (excepto el email del usuario actual)
4. **Paginación cursor-based:** Usar `nextCursor` de la respuesta para obtener la siguiente página
5. **Compatibilidad:** El parámetro `includeInactive` está deprecado, usar `isActive` en su lugar
