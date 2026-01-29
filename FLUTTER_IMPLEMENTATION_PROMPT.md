# Prompt para Implementación Flutter - Nuevo Sistema de Autenticación

## Contexto del Backend

El backend FastAPI ha sido actualizado. Los endpoints de autenticación (`POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/login/form`, `GET /api/v1/auth/me`) ahora retornan una estructura de respuesta actualizada.

### Estructura de Respuesta Actual del Backend:

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "timezone": "UTC",
    "is_active": true,
    "has_organization": true,
    "organizations": [
      {
        "id": "org-uuid",
        "name": "Acme Corporation",
        "slug": "acme-corporation",
        "role": "owner"
      }
    ],
    "created_at": "2026-01-14T01:05:12.805136",
    "updated_at": "2026-01-14T01:05:12.805144"
  },
  "access_token": "jwt-token",
  "refresh_token": "jwt-token",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Campos Nuevos:
- `user.full_name`: String - Nombre completo del usuario (ya no necesitas concatenar first_name + last_name)
- `user.has_organization`: Boolean - Indica si el usuario pertenece a al menos una organización
- `user.organizations`: Array de objetos con:
  - `id`: String (UUID)
  - `name`: String
  - `slug`: String (identificador URL-friendly)
  - `role`: String - Puede ser: "owner", "admin", "manager", "employee"

### Comportamiento del Array `organizations`:
- Si el usuario NO tiene organizaciones: `organizations: []` (array vacío) y `has_organization: false`
- Si el usuario tiene organizaciones: `organizations` contiene objetos con la información de cada organización y el rol del usuario en cada una

---

## Tarea: Actualizar Frontend Flutter

Tengo una aplicación Flutter existente que usa el sistema de autenticación anterior. Necesito que actualices el código para:

1. **Actualizar los modelos de datos** para reflejar la nueva estructura de respuesta
2. **Implementar lógica de navegación post-login** según las siguientes reglas:
3. **Crear una pantalla de selección de organización** cuando sea necesario

---

## Reglas de Navegación Post-Login

Después de un login o registro exitoso, la aplicación debe navegar según estas reglas:

### Regla 1: Usuario SIN organizaciones
- **Condición**: `has_organization == false` O `organizations.length == 0`
- **Acción**: Navegar a pantalla de onboarding/crear organización (ruta: `/onboarding` o similar)

### Regla 2: Usuario con 1 organización
- **Condición**: `organizations.length == 1`
- **Acción**: Navegar directamente al dashboard (ruta: `/dashboard`) con esa organización

### Regla 3: Usuario con múltiples organizaciones Y es owner de 2 o más
- **Condición**: `organizations.length >= 2` Y el usuario tiene rol "owner" en 2 o más organizaciones
- **Acción**: Mostrar pantalla de selección de organización (ruta: `/select-organization`) donde el usuario debe elegir con cuál organización trabajar
- **Importante**: En la pantalla de selección, SOLO mostrar las organizaciones donde el usuario es "owner", no todas

### Regla 4: Usuario con múltiples organizaciones pero NO es owner de 2 o más
- **Condición**: `organizations.length >= 2` PERO el usuario NO es owner de 2 o más (puede ser owner de 1, o admin/manager/employee en varias)
- **Acción**: Navegar directamente al dashboard con la primera organización donde es "owner" (si existe), o si no tiene ninguna como owner, usar la primera organización del array

---

## Requisitos de Implementación

### 1. Modelos de Datos

Crea o actualiza los siguientes modelos:

**OrganizationBasic:**
```dart
class OrganizationBasic {
  final String id;
  final String name;
  final String slug;
  final String role; // "owner", "admin", "manager", "employee"
  
  // Métodos: fromJson, toJson
  // Getters: isOwner, isAdmin, isManager, isEmployee
}
```

**UserResponse:**
- Agregar campo `fullName` (String)
- Agregar campo `hasOrganization` (bool)
- Agregar campo `organizations` (List<OrganizationBasic>)
- Agregar métodos helper:
  - `ownerCount`: int - Cuenta cuántas organizaciones donde es owner
  - `hasMultipleOwnerOrgs`: bool - true si es owner de 2 o más
  - `firstOwnerOrg`: OrganizationBasic? - Primera organización donde es owner, o null

**AuthResponse:**
- Actualizar para usar el nuevo `UserResponse`

### 2. Servicio de Navegación

Crea un servicio o función que maneje la navegación post-login:

```dart
void handlePostLoginNavigation(BuildContext context, AuthResponse authResponse) {
  final user = authResponse.user;
  
  // Implementar las 4 reglas de navegación descritas arriba
  // Usar Navigator.pushReplacementNamed para navegar
  // Guardar la organización seleccionada en SharedPreferences
}
```

### 3. Pantalla de Selección de Organización

Crear una nueva pantalla `SelectOrganizationScreen`:

- **Props**: Recibe `List<OrganizationBasic> organizations`
- **Comportamiento**:
  - Filtrar y mostrar SOLO las organizaciones donde `role == "owner"`
  - Mostrar lista de tarjetas con: nombre de la organización, rol (aunque siempre será "owner")
  - Al seleccionar una organización:
    1. Guardar en SharedPreferences: `selected_org_id`, `selected_org_name`, `selected_org_slug`, `selected_org_role`
    2. Navegar a `/dashboard` pasando la organización seleccionada
- **UI**: Lista de tarjetas (Cards) con información de cada organización, botón/tap para seleccionar
- **Navegación**: No permitir volver atrás (automaticallyImplyLeading: false)

### 4. Actualizar Servicio de Autenticación

- Actualizar métodos `login()` y `register()` para parsear la nueva estructura
- Asegurar que `AuthResponse.fromJson()` funcione correctamente con los nuevos campos

### 5. Actualizar Pantalla de Login/Registro

- Después de login/registro exitoso, llamar a `handlePostLoginNavigation()` en lugar de navegar directamente al dashboard

### 6. Rutas

Agregar nueva ruta:
- `/select-organization` → `SelectOrganizationScreen`

---

## Detalles Técnicos

- **Persistencia**: Usar `SharedPreferences` para guardar la organización seleccionada
- **Navegación**: Usar `Navigator.pushReplacementNamed()` para reemplazar la pantalla actual
- **Filtrado**: Al contar organizaciones donde es owner, usar `organizations.where((org) => org.role == "owner")`
- **Fallback**: Si no hay organizaciones como owner, usar `organizations.first`

---

## Ejemplos de Casos

### Caso 1: Usuario nuevo
```json
{"has_organization": false, "organizations": []}
```
→ Navegar a `/onboarding`

### Caso 2: Usuario con 1 organización
```json
{
  "has_organization": true,
  "organizations": [{"id": "1", "name": "Mi Empresa", "role": "owner"}]
}
```
→ Navegar a `/dashboard` con esa organización

### Caso 3: Usuario owner de 2+ organizaciones
```json
{
  "has_organization": true,
  "organizations": [
    {"id": "1", "name": "Empresa A", "role": "owner"},
    {"id": "2", "name": "Empresa B", "role": "owner"},
    {"id": "3", "name": "Empresa C", "role": "admin"}
  ]
}
```
→ Mostrar pantalla de selección (solo Empresa A y B)

### Caso 4: Usuario con múltiples orgs pero solo 1 owner
```json
{
  "has_organization": true,
  "organizations": [
    {"id": "1", "name": "Empresa A", "role": "owner"},
    {"id": "2", "name": "Empresa B", "role": "admin"}
  ]
}
```
→ Navegar a `/dashboard` con Empresa A

---

## Instrucciones para la IA

1. Analiza el código Flutter existente relacionado con autenticación
2. Identifica los modelos actuales (`UserResponse`, `AuthResponse`, etc.)
3. Actualiza los modelos para incluir los nuevos campos
4. Crea el modelo `OrganizationBasic`
5. Implementa la función `handlePostLoginNavigation()` con las 4 reglas
6. Crea la pantalla `SelectOrganizationScreen`
7. Actualiza las pantallas de login/registro para usar la nueva lógica
8. Agrega la nueva ruta al router
9. Asegúrate de que la organización seleccionada se guarde en SharedPreferences
10. Prueba todos los casos de uso

**Importante**: Mantén la estructura y estilo de código existente. Solo actualiza lo necesario para soportar los nuevos campos y la lógica de navegación.

---

## Endpoints del Backend

- **Base URL**: `http://localhost:8000/api/v1`
- **Login**: `POST /api/v1/auth/login`
- **Register**: `POST /api/v1/auth/register`
- **Me**: `GET /api/v1/auth/me` (requiere header: `Authorization: Bearer <token>`)
- **Login OAuth2**: `POST /api/v1/auth/login/form` (compatible con OAuth2)

**URLs completas:**
- Login: `http://localhost:8000/api/v1/auth/login`
- Register: `http://localhost:8000/api/v1/auth/register`
- Me: `http://localhost:8000/api/v1/auth/me`

**Nota para producción**: Si el backend está desplegado en otro servidor, reemplaza `localhost:8000` con la URL correspondiente (ej: `https://api.tudominio.com`).

Todos los endpoints retornan la misma estructura de `AuthResponse` con los nuevos campos.
