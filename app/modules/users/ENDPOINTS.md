# Users - Endpoints API

## Descripcion del modulo

El modulo **Users** es el modulo central del sistema EvoTrack. Gestiona todo el ciclo de vida del usuario: desde el registro y activacion de cuenta, pasando por la gestion del perfil personal, hasta la administracion de usuarios dentro de una organizacion (creacion, actualizacion, desactivacion y reactivacion).

Todos los endpoints relacionados con usuarios se dividen en dos grupos:
- **Perfil**: operaciones que el usuario realiza sobre su propia cuenta.
- **Gestion en organizacion**: operaciones administrativas sobre los usuarios de una organizacion.

---

## Relacion con otros modulos

| Modulo | Relacion |
|--------|----------|
| **Organizations** | Un usuario pertenece a una o mas organizaciones con un rol asignado (`owner`, `admin`, `manager`, `employee`, `member`) a traves de la tabla intermedia `UserOrganization`. |
| **Departments** | Un usuario puede estar asignado a un departamento (`departmentId`). Tambien puede ser designado como jefe de departamento (`departmentHeadId`). |
| **Teams** | Un usuario puede ser miembro de multiples equipos a traves de `TeamMember`, y puede ser lider de equipo (`teamLeadId`). |
| **Auth** | Maneja la autenticacion mediante tokens JWT (access token y refresh token), la activacion de cuentas por email y el cambio de contrasena. |
| **Projects** | *(Pendiente de implementacion)* |

---

## Informacion general

| Concepto | Valor |
|----------|-------|
| Base URL | `/api/v1` |
| Autenticacion | `Authorization: Bearer {accessToken}` |
| Formato de respuestas | **camelCase** |
| Formato de requests | Acepta **camelCase** y **snake_case** |
| Content-Type | `application/json` (excepto upload de avatar) |

### Roles de organizacion
`owner` · `admin` · `manager` · `employee` · `member`

### Estados de usuario
`active` · `pending_activation` · `inactive`

### Requisitos de contrasena
- Minimo 8 caracteres
- Al menos una letra
- Al menos un numero

---

## Perfil del usuario (self-service)

Estos endpoints permiten al usuario autenticado gestionar su propia cuenta. No requieren permisos de administrador.

---

### GET /users/me

Obtiene el perfil completo del usuario autenticado.

**Respuesta:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "fullName": "John Doe",
  "avatarUrl": "string | null",
  "phone": "string | null",
  "dateOfBirth": "2000-01-15 | null",
  "identification": "string | null",
  "nationality": "string | null",
  "departmentId": "uuid | null",
  "department": "string | null",
  "timezone": "UTC",
  "language": "en",
  "status": "active",
  "role": "admin | null",
  "isActive": true,
  "canLogin": true,
  "preferences": {},
  "lastLoginAt": "datetime | null",
  "organizations": [
    {
      "id": "uuid",
      "name": "Mi Empresa",
      "slug": "mi-empresa",
      "role": "admin"
    }
  ],
  "createdAt": "datetime",
  "updatedAt": "datetime | null",
  "activatedAt": "datetime | null"
}
```

---

### PUT /users/me

Actualiza la informacion del perfil del usuario autenticado.

**Body:**

| Campo | Tipo | Requerido | Notas |
|-------|------|-----------|-------|
| firstName | string | No | 1-100 caracteres |
| lastName | string | No | 1-100 caracteres |
| phone | string | No | Max 50 caracteres |
| dateOfBirth | date | No | Formato: `YYYY-MM-DD` |
| identification | string | No | Max 100 caracteres |
| nationality | string | No | Max 100 caracteres |
| timezone | string | No | Timezone IANA (ej: `America/Bogota`) |
| language | string | No | Codigo de idioma, max 10 chars (ej: `es`) |
| preferences | object | No | JSON libre para preferencias del usuario |

**Ejemplo:**
```json
{
  "firstName": "Juan",
  "phone": "+57 300 1234567",
  "timezone": "America/Bogota",
  "preferences": { "theme": "dark" }
}
```

**Respuesta:** Mismo formato que `GET /users/me`

---

### PUT /users/me/password

Cambia la contrasena del usuario autenticado.

**Body:**

| Campo | Tipo | Requerido | Notas |
|-------|------|-----------|-------|
| currentPassword | string | Si | Contrasena actual |
| newPassword | string | Si | Min 8 chars, debe contener letra + numero |

**Ejemplo:**
```json
{
  "currentPassword": "MiClaveActual1",
  "newPassword": "MiClaveNueva2"
}
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

**Errores:**
| Codigo | Descripcion |
|--------|-------------|
| 400 | Contrasena actual incorrecta |
| 422 | La nueva contrasena no cumple los requisitos |

---

### POST /users/me/avatar

Sube una imagen de avatar para el usuario autenticado.

**Content-Type:** `multipart/form-data`

| Campo | Tipo | Requerido | Notas |
|-------|------|-----------|-------|
| file | binary | Si | Formatos: jpg, jpeg, png, webp. Max: 2MB |

**Respuesta:** Mismo formato que `GET /users/me` (con `avatarUrl` actualizado)

**Errores:**
| Codigo | Descripcion |
|--------|-------------|
| 413 | Archivo excede 2MB |
| 422 | Formato de archivo no valido |

---

### DELETE /users/me/avatar

Elimina el avatar del usuario autenticado.

**Respuesta:**
```json
{
  "success": true,
  "message": "Avatar removed successfully"
}
```

---

## Gestion de usuarios en organizacion

Estos endpoints operan dentro del contexto de una organizacion. La mayoria requieren rol de **admin** u **owner**.

**Base:** `/api/v1/organizations/{orgId}/users`

| Parametro de ruta | Tipo | Descripcion |
|-------------------|------|-------------|
| orgId | UUID | ID de la organizacion |

---

### POST /organizations/{orgId}/users

Crea un nuevo usuario dentro de la organizacion. El usuario queda en estado `pending_activation` y recibe un email de activacion.

**Permiso:** Admin

**Body:**

| Campo | Tipo | Requerido | Default | Notas |
|-------|------|-----------|---------|-------|
| email | string | Si | - | Email valido, unico |
| firstName | string | Si | - | 1-100 caracteres |
| lastName | string | Si | - | 1-100 caracteres |
| phone | string | No | null | Max 50 caracteres |
| dateOfBirth | date | No | null | Formato: `YYYY-MM-DD` |
| identification | string | No | null | Max 100 caracteres |
| nationality | string | No | null | Max 100 caracteres |
| role | string | No | `"employee"` | Rol en la organizacion |
| departmentId | UUID | No | null | Debe existir en la organizacion |
| avatar | string | No | null | URL, max 500 caracteres |
| timezone | string | No | `"UTC"` | Timezone IANA |
| language | string | No | `"en"` | Codigo de idioma |
| sendActivationEmail | boolean | No | `true` | Enviar email de activacion |

**Ejemplo:**
```json
{
  "email": "nuevo@empresa.com",
  "firstName": "Maria",
  "lastName": "Garcia",
  "role": "employee",
  "departmentId": "550e8400-e29b-41d4-a716-446655440000",
  "sendActivationEmail": true
}
```

**Respuesta (201):**
```json
{
  "id": "uuid",
  "email": "nuevo@empresa.com",
  "firstName": "Maria",
  "lastName": "Garcia",
  "fullName": "Maria Garcia",
  "avatarUrl": null,
  "phone": null,
  "dateOfBirth": null,
  "identification": null,
  "nationality": null,
  "departmentId": "uuid | null",
  "department": "Ventas | null",
  "timezone": "UTC",
  "language": "en",
  "status": "pending_activation",
  "role": "employee",
  "isActive": true,
  "canLogin": false,
  "createdAt": "datetime",
  "updatedAt": null,
  "activatedAt": null
}
```

**Errores:**
| Codigo | Descripcion |
|--------|-------------|
| 403 | No tiene permisos de admin |
| 404 | Departamento no encontrado |
| 409 | Email ya existe |

---

### POST /organizations/{orgId}/users/bulk

Crea multiples usuarios en una sola operacion. Es una operacion de **exito parcial**: algunos pueden crearse y otros fallar.

**Permiso:** Admin

**Body:**

| Campo | Tipo | Requerido | Notas |
|-------|------|-----------|-------|
| users | array | Si | Min 1, max 50 elementos. Cada elemento igual al body de crear usuario individual |

**Ejemplo:**
```json
{
  "users": [
    {
      "email": "user1@empresa.com",
      "firstName": "Carlos",
      "lastName": "Lopez",
      "role": "employee"
    },
    {
      "email": "user2@empresa.com",
      "firstName": "Ana",
      "lastName": "Martinez",
      "role": "manager"
    }
  ]
}
```

**Respuesta (201):**
```json
{
  "created": [
    { "id": "uuid", "email": "user1@empresa.com", "..." : "..." }
  ],
  "failed": [
    { "email": "user2@empresa.com", "error": "Email already exists" }
  ],
  "totalCreated": 1,
  "totalFailed": 1
}
```

---

### POST /organizations/{orgId}/users/search

Lista los usuarios de la organizacion con filtros avanzados y paginacion basada en cursor.

**Permiso:** Miembro de la organizacion

**Body:**

| Campo | Tipo | Requerido | Default | Valores validos |
|-------|------|-----------|---------|-----------------|
| limit | integer | No | 20 | 1 - 100 |
| nextCursor | object | No | null | `{ "id": "uuid", "ts": "datetime" }` |
| search | string | No | null | Busqueda por nombre o email |
| status | string[] | No | null | `active`, `pending_activation`, `inactive` |
| role | string[] | No | null | `owner`, `admin`, `manager`, `employee`, `member` |
| isActive | boolean | No | null | `true` / `false` |
| createdFrom | datetime | No | null | Fecha ISO 8601 |
| createdTo | datetime | No | null | Fecha ISO 8601 (debe ser >= createdFrom) |

> Los filtros `status` y `role` aceptan multiples valores (logica OR). Entre filtros diferentes se aplica logica AND.

**Ejemplo:**
```json
{
  "search": "maria",
  "status": ["active", "pending_activation"],
  "role": ["employee", "manager"],
  "limit": 20
}
```

**Respuesta:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "email": "maria@empresa.com",
      "firstName": "Maria",
      "lastName": "Garcia",
      "avatarUrl": null,
      "status": "active",
      "role": "employee",
      "isActive": true,
      "createdAt": "datetime"
    }
  ],
  "meta": {
    "userRole": "admin",
    "canSeeEmails": true,
    "organizationId": "uuid"
  },
  "stats": {
    "totalUsers": 50,
    "activeUsers": 45,
    "pendingActivation": 3,
    "inactiveUsers": 2,
    "byRole": {
      "owner": 1,
      "admin": 2,
      "manager": 5,
      "employee": 35,
      "member": 7
    },
    "byStatus": {
      "active": 45,
      "pendingActivation": 3,
      "inactive": 2
    }
  },
  "pagination": {
    "count": 20,
    "limit": 20,
    "hasMore": true,
    "nextCursor": {
      "id": "uuid",
      "ts": "datetime"
    }
  }
}
```

**Paginacion:** Para obtener la siguiente pagina, enviar el objeto `nextCursor` de la respuesta anterior en el campo `nextCursor` del siguiente request. Continuar mientras `hasMore` sea `true`.

---

### GET /organizations/{orgId}/users/search

Busqueda rapida de usuarios por nombre o email. Util para campos de autocompletado.

**Permiso:** Miembro de la organizacion

**Query params:**

| Parametro | Tipo | Requerido | Default | Notas |
|-----------|------|-----------|---------|-------|
| q | string | Si | - | Termino de busqueda, min 2 caracteres |
| limit | integer | No | 10 | 1 - 50 |

**Ejemplo:** `GET /organizations/{orgId}/users/search?q=maria&limit=5`

**Respuesta:** Array de objetos de usuario (mismo formato que la respuesta de crear usuario).

---

### GET /organizations/{orgId}/users/{userId}

Obtiene el detalle completo de un usuario en la organizacion.

**Permiso:** Miembro de la organizacion

| Parametro de ruta | Tipo | Descripcion |
|-------------------|------|-------------|
| userId | UUID | ID del usuario |

**Respuesta:** Mismo formato que `GET /users/me` (incluye preferences, lastLoginAt y organizations).

**Errores:**
| Codigo | Descripcion |
|--------|-------------|
| 404 | Usuario no encontrado |

---

### PUT /organizations/{orgId}/users/{userId}

Actualiza la informacion de un usuario en la organizacion.

**Permiso:** Admin

| Parametro de ruta | Tipo | Descripcion |
|-------------------|------|-------------|
| userId | UUID | ID del usuario |

**Body:**

| Campo | Tipo | Requerido | Notas |
|-------|------|-----------|-------|
| firstName | string | No | 1-100 caracteres |
| lastName | string | No | 1-100 caracteres |
| phone | string | No | Max 50 caracteres |
| dateOfBirth | date | No | Formato: `YYYY-MM-DD` |
| identification | string | No | Max 100 caracteres |
| nationality | string | No | Max 100 caracteres |
| role | string | No | Rol en la organizacion |
| departmentId | UUID | No | Debe existir en la organizacion |
| avatar | string | No | URL, max 500 caracteres |
| timezone | string | No | Timezone IANA |
| language | string | No | Max 10 caracteres |
| isActive | boolean | No | Activar/desactivar usuario |
| status | string | No | `active`, `pending_activation`, `inactive` |

**Ejemplo:**
```json
{
  "role": "manager",
  "departmentId": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Respuesta:** Mismo formato que la respuesta de crear usuario.

**Errores:**
| Codigo | Descripcion |
|--------|-------------|
| 403 | No tiene permisos de admin |
| 404 | Usuario no encontrado |

---

### DELETE /organizations/{orgId}/users/{userId}

Desactiva un usuario (soft delete). El usuario no se elimina, su estado cambia a `inactive` y no puede iniciar sesion.

**Permiso:** Admin

| Parametro de ruta | Tipo | Descripcion |
|-------------------|------|-------------|
| userId | UUID | ID del usuario |

**Respuesta:**
```json
{
  "success": true,
  "message": "User deactivated successfully"
}
```

**Errores:**
| Codigo | Descripcion |
|--------|-------------|
| 400 | No puedes desactivarte a ti mismo |
| 403 | No tiene permisos de admin |
| 404 | Usuario no encontrado |

---

### POST /organizations/{orgId}/users/{userId}/reactivate

Reactiva un usuario previamente desactivado.

**Permiso:** Admin

| Parametro de ruta | Tipo | Descripcion |
|-------------------|------|-------------|
| userId | UUID | ID del usuario |

**Respuesta:** Mismo formato que la respuesta de crear usuario.

---

### GET /organizations/{orgId}/users/stats

Obtiene estadisticas de los usuarios de la organizacion.

**Permiso:** Admin

**Respuesta:**
```json
{
  "total": 50,
  "active": 45,
  "pending": 3,
  "inactive": 2
}
```

---

## Referencia rapida

| Metodo | Endpoint | Permiso | Descripcion |
|--------|----------|---------|-------------|
| GET | `/users/me` | Auth | Obtener mi perfil |
| PUT | `/users/me` | Auth | Actualizar mi perfil |
| PUT | `/users/me/password` | Auth | Cambiar mi contrasena |
| POST | `/users/me/avatar` | Auth | Subir avatar |
| DELETE | `/users/me/avatar` | Auth | Eliminar avatar |
| POST | `/organizations/{orgId}/users` | Admin | Crear usuario |
| POST | `/organizations/{orgId}/users/bulk` | Admin | Crear multiples usuarios |
| POST | `/organizations/{orgId}/users/search` | Miembro | Listar con filtros avanzados |
| GET | `/organizations/{orgId}/users/search` | Miembro | Busqueda rapida |
| GET | `/organizations/{orgId}/users/{userId}` | Miembro | Detalle de usuario |
| PUT | `/organizations/{orgId}/users/{userId}` | Admin | Actualizar usuario |
| DELETE | `/organizations/{orgId}/users/{userId}` | Admin | Desactivar usuario |
| POST | `/organizations/{orgId}/users/{userId}/reactivate` | Admin | Reactivar usuario |
| GET | `/organizations/{orgId}/users/stats` | Admin | Estadisticas |

> Todos los endpoints tienen prefijo `/api/v1`. Los marcados como **Auth** solo requieren estar autenticado. Los marcados como **Admin** requieren rol `admin` u `owner` en la organizacion. Los marcados como **Miembro** requieren pertenecer a la organizacion.
