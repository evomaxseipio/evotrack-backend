# Sistema de Roles y Permisos (RBAC)

Este documento describe el sistema de control de acceso basado en roles (RBAC) implementado en EvoTrack.

## Tabla de Contenidos

- [Roles](#roles)
- [Permisos](#permisos)
- [Uso de Decorators](#uso-de-decorators)
- [Función has_permission](#función-has_permission)
- [Ejemplos](#ejemplos)

## Roles

El sistema define cuatro roles principales con diferentes niveles de acceso:

### Owner (Propietario)
- **Nivel**: 4 (más alto)
- **Permisos**: Todos los permisos (`*` - wildcard)
- **Descripción**: Tiene acceso completo a todas las funcionalidades de la organización

### Admin (Administrador)
- **Nivel**: 3
- **Permisos**: Gestión de usuarios, proyectos, timesheets, reportes, gastos
- **Descripción**: Puede gestionar la mayoría de aspectos de la organización, excepto eliminar la organización

### Manager (Gerente)
- **Nivel**: 2
- **Permisos**: Crear/editar proyectos, aprobar timesheets y gastos, ver reportes
- **Descripción**: Puede gestionar proyectos y aprobar trabajo, pero no puede gestionar usuarios

### Employee (Empleado)
- **Nivel**: 1 (más bajo)
- **Permisos**: Ver proyectos, crear/editar sus propios timesheets y gastos
- **Descripción**: Acceso limitado a sus propios datos y visualización de proyectos

## Permisos

### Permisos de Proyectos
- `CREATE_PROJECT`: Crear nuevos proyectos
- `EDIT_PROJECT`: Editar proyectos existentes
- `DELETE_PROJECT`: Eliminar proyectos
- `VIEW_PROJECT`: Ver proyectos

### Permisos de Timesheets
- `CREATE_TIMESHEET`: Crear timesheets
- `EDIT_TIMESHEET`: Editar timesheets
- `DELETE_TIMESHEET`: Eliminar timesheets
- `VIEW_TIMESHEET`: Ver timesheets
- `APPROVE_TIMESHEET`: Aprobar timesheets de otros usuarios

### Permisos de Gestión de Usuarios
- `MANAGE_USERS`: Gestionar usuarios (crear, editar, eliminar)
- `VIEW_USERS`: Ver lista de usuarios
- `EDIT_USER_ROLE`: Cambiar roles de usuarios
- `DEACTIVATE_USER`: Desactivar usuarios

### Permisos de Organización
- `MANAGE_ORGANIZATION`: Gestionar configuración de la organización
- `VIEW_ORGANIZATION`: Ver información de la organización
- `DELETE_ORGANIZATION`: Eliminar la organización (solo owner)

### Permisos de Reportes
- `VIEW_REPORTS`: Ver reportes
- `EXPORT_REPORTS`: Exportar reportes
- `MANAGE_REPORTS`: Gestionar reportes personalizados

### Permisos de Gastos
- `CREATE_EXPENSE`: Crear gastos
- `EDIT_EXPENSE`: Editar gastos
- `DELETE_EXPENSE`: Eliminar gastos
- `VIEW_EXPENSE`: Ver gastos
- `APPROVE_EXPENSE`: Aprobar gastos de otros usuarios

### Permisos Generales
- `VIEW_OWN_DATA`: Ver sus propios datos
- `EDIT_OWN_PROFILE`: Editar su propio perfil

### Permisos de Invitaciones
- `INVITE_USERS`: Invitar usuarios a la organización
- `MANAGE_INVITATIONS`: Gestionar invitaciones

## Uso de Decorators

### @require_permission

Protege un endpoint requiriendo un permiso específico.

**Sintaxis:**
```python
from app.core.constants import Permission
from app.modules.users.dependencies import require_permission
from fastapi import Depends

@router.post("/{org_id}/projects")
def create_project(
    org_id: UUID,
    current_user: CurrentUser,
    _: bool = Depends(require_permission(Permission.CREATE_PROJECT))
):
    # Endpoint logic
    pass
```

**Características:**
- Verifica que el usuario esté autenticado
- Verifica que el usuario sea miembro de la organización
- Verifica que el usuario tenga el permiso requerido en esa organización
- Lanza `ForbiddenException` si no cumple los requisitos

### @require_role

Protege un endpoint requiriendo un rol específico o superior.

**Sintaxis:**
```python
from app.modules.organizations.models import OrganizationRole
from app.modules.users.dependencies import require_role
from fastapi import Depends

@router.delete("/{org_id}")
def delete_organization(
    org_id: UUID,
    current_user: CurrentUser,
    _: bool = Depends(require_role(OrganizationRole.OWNER))
):
    # Endpoint logic
    pass
```

**Características:**
- Verifica que el usuario esté autenticado
- Verifica que el usuario sea miembro de la organización
- Verifica que el usuario tenga el rol requerido o superior
- Lanza `ForbiddenException` si no cumple los requisitos

**Jerarquía de roles:**
- Owner (4) > Admin (3) > Manager (2) > Employee (1)
- Un usuario con rol superior puede acceder a endpoints que requieren roles inferiores

## Función has_permission

La función `has_permission` en `UserService` permite verificar permisos en la lógica de negocio.

**Sintaxis:**
```python
from app.modules.users.service import UserService
from app.core.constants import Permission

# En un método del service
if not self.has_permission(user_id, org_id, Permission.CREATE_PROJECT):
    raise ForbiddenException("You don't have permission to create projects")
```

**Parámetros:**
- `user_id`: UUID del usuario
- `org_id`: UUID de la organización
- `permission`: String del permiso (de `Permission` enum)

**Retorna:**
- `True` si el usuario tiene el permiso
- `False` si el usuario no es miembro o no tiene el permiso

## Ejemplos

### Ejemplo 1: Endpoint con permiso requerido

```python
from fastapi import APIRouter, Depends
from uuid import UUID
from app.core.constants import Permission
from app.modules.auth.dependencies import CurrentUser
from app.modules.users.dependencies import require_permission, get_user_service
from app.modules.users.service import UserService

router = APIRouter()

@router.post("/{org_id}/projects")
def create_project(
    org_id: UUID,
    project_data: ProjectCreate,
    current_user: CurrentUser,
    user_service: UserService = Depends(get_user_service),
    _: bool = Depends(require_permission(Permission.CREATE_PROJECT))
):
    """Crear un nuevo proyecto."""
    # El decorator ya verificó el permiso
    return user_service.create_project(org_id, project_data, current_user.id)
```

### Ejemplo 2: Endpoint con rol requerido

```python
from app.modules.organizations.models import OrganizationRole
from app.modules.users.dependencies import require_role

@router.delete("/{org_id}")
def delete_organization(
    org_id: UUID,
    current_user: CurrentUser,
    org_service: OrganizationService = Depends(get_organization_service),
    _: bool = Depends(require_role(OrganizationRole.OWNER))
):
    """Eliminar organización (solo owner)."""
    return org_service.delete_organization(org_id, current_user.id)
```

### Ejemplo 3: Verificación de permiso en lógica de negocio

```python
class ProjectService:
    def create_project(self, org_id: UUID, project_data: ProjectCreate, user_id: UUID):
        # Verificar permiso en el service
        if not self.user_service.has_permission(user_id, org_id, Permission.CREATE_PROJECT):
            raise ForbiddenException("You don't have permission to create projects")
        
        # Lógica de creación del proyecto
        project = Project(
            organization_id=org_id,
            name=project_data.name,
            created_by=user_id
        )
        # ...
        return project
```

### Ejemplo 4: Verificación de múltiples permisos

```python
@router.post("/{org_id}/projects/{project_id}/timesheets/approve")
def approve_timesheet(
    org_id: UUID,
    project_id: UUID,
    timesheet_id: UUID,
    current_user: CurrentUser,
    user_service: UserService = Depends(get_user_service),
    _: bool = Depends(require_permission(Permission.APPROVE_TIMESHEET))
):
    """Aprobar timesheet (requiere permiso APPROVE_TIMESHEET)."""
    # Verificar permiso adicional si es necesario
    if not user_service.has_permission(current_user.id, org_id, Permission.VIEW_PROJECT):
        raise ForbiddenException("You don't have permission to view this project")
    
    return timesheet_service.approve_timesheet(timesheet_id, current_user.id)
```

## Mapeo de Roles a Permisos

### Owner
```
* (todos los permisos)
```

### Admin
- CREATE_PROJECT, EDIT_PROJECT, DELETE_PROJECT, VIEW_PROJECT
- CREATE_TIMESHEET, EDIT_TIMESHEET, DELETE_TIMESHEET, VIEW_TIMESHEET, APPROVE_TIMESHEET
- MANAGE_USERS, VIEW_USERS, EDIT_USER_ROLE, DEACTIVATE_USER
- MANAGE_ORGANIZATION, VIEW_ORGANIZATION
- VIEW_REPORTS, EXPORT_REPORTS, MANAGE_REPORTS
- CREATE_EXPENSE, EDIT_EXPENSE, DELETE_EXPENSE, VIEW_EXPENSE, APPROVE_EXPENSE
- VIEW_OWN_DATA, EDIT_OWN_PROFILE
- INVITE_USERS, MANAGE_INVITATIONS

### Manager
- CREATE_PROJECT, EDIT_PROJECT, VIEW_PROJECT
- CREATE_TIMESHEET, EDIT_TIMESHEET, VIEW_TIMESHEET, APPROVE_TIMESHEET
- VIEW_USERS
- VIEW_ORGANIZATION
- VIEW_REPORTS, EXPORT_REPORTS
- CREATE_EXPENSE, EDIT_EXPENSE, VIEW_EXPENSE, APPROVE_EXPENSE
- VIEW_OWN_DATA, EDIT_OWN_PROFILE

### Employee
- VIEW_PROJECT
- CREATE_TIMESHEET, EDIT_TIMESHEET, VIEW_TIMESHEET
- VIEW_ORGANIZATION
- CREATE_EXPENSE, EDIT_EXPENSE, VIEW_EXPENSE
- VIEW_OWN_DATA, EDIT_OWN_PROFILE

## Notas Importantes

1. **Wildcard para Owner**: El rol `owner` tiene el permiso especial `*` que otorga todos los permisos automáticamente.

2. **Verificación de Membresía**: Antes de verificar permisos, el sistema verifica que el usuario sea miembro activo de la organización.

3. **Jerarquía de Roles**: Los decorators `require_role` permiten que usuarios con roles superiores accedan a endpoints que requieren roles inferiores.

4. **Contexto de Organización**: Todos los permisos se verifican en el contexto de una organización específica. Un usuario puede tener diferentes permisos en diferentes organizaciones.

5. **Permisos en Service Layer**: Se recomienda usar `has_permission` en la capa de servicio para lógica de negocio compleja, además de usar decorators en los endpoints.

## Testing

Los tests del sistema de permisos se encuentran en:
- `tests/users/test_permissions.py`

Ejecutar tests:
```bash
pytest tests/users/test_permissions.py -v
```
