# EvoTrack Backend

> Where Time Evolves - Sistema integral de seguimiento de tiempo y gestión de gastos.

## Stack Técnico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Runtime | Python | 3.11 |
| Framework | FastAPI | 0.109.0 |
| ORM | SQLAlchemy | 2.0.25 |
| Base de Datos | PostgreSQL | 15 |
| Migraciones | Alembic | 1.13.1 |
| Validación | Pydantic | 2.5.3 |
| Auth | python-jose + passlib | JWT |
| Server | Uvicorn | 0.27.0 |
| Containerización | Docker | - |

## Estructura del Proyecto

```
evotrack-backend/
├── app/
│   ├── main.py                 # Punto de entrada de la aplicación
│   ├── api.py                  # Router principal de la API
│   ├── core/                   # Configuración central
│   │   ├── config.py           # Settings (pydantic-settings)
│   │   ├── database.py         # Conexión a PostgreSQL
│   │   ├── security.py         # JWT, hashing de passwords
│   │   ├── logging.py          # Configuración de logs
│   │   ├── constants.py        # Constantes globales
│   │   ├── email.py            # Servicio de correo
│   │   └── dependencies.py     # Dependencias compartidas
│   ├── modules/                # Módulos de dominio
│   │   ├── auth/               # Autenticación
│   │   ├── users/              # Gestión de usuarios
│   │   ├── organizations/      # Organizaciones
│   │   ├── teams/              # Equipos
│   │   ├── departments/        # Departamentos
│   │   ├── projects/           # Proyectos
│   │   ├── reports/            # Reportes
│   │   └── notifications/      # Notificaciones
│   └── shared/                 # Utilidades compartidas
│       ├── base_repository.py  # Repository base pattern
│       ├── exceptions.py       # Excepciones personalizadas
│       ├── responses.py        # Formatos de respuesta
│       ├── pagination.py       # Utilidades de paginación
│       └── utils.py            # Helpers generales
├── alembic/                    # Migraciones de BD
├── tests/                      # Tests
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── pyproject.toml              # Configuración de herramientas
```

## Arquitectura de Módulos

Cada módulo sigue el patrón:

```
modules/{nombre}/
├── __init__.py
├── models.py           # Modelos SQLAlchemy
├── schemas.py          # Schemas Pydantic (request/response)
├── repository.py       # Acceso a datos
├── service.py          # Lógica de negocio
├── router.py           # Endpoints FastAPI
└── dependencies.py     # Inyección de dependencias
```

## Convenciones de Código

### Python
- Formateo: Black (line-length: 100)
- Imports: isort (profile: black)
- Type hints obligatorios en funciones públicas
- Docstrings en clases y funciones principales

### API REST
- Prefijo: `/api/v1`
- Responses en **camelCase** (usar `alias_generator=to_camel` en Pydantic)
- Requests aceptan **camelCase** y **snake_case** (`populate_by_name=True`)
- Endpoints de listado/búsqueda usan **POST** con JSON body
- Paginación cursor-based con estructura:
  ```json
  {
    "success": true,
    "data": [...],
    "meta": { "userRole": "...", "canSeeEmails": true, "organizationId": "..." },
    "pagination": { "count": 10, "limit": 20, "hasMore": true, "nextCursor": {...} }
  }
  ```

### Base de Datos
- UUIDs como primary keys
- Timestamps: `created_at`, `updated_at`
- Soft delete con `deleted_at` donde aplique
- Funciones PostgreSQL para queries complejas (prefijo: `fn_`)
- En SQLAlchemy `text()`: usar `CAST(:param AS jsonb)` en lugar de `:param::jsonb`

### Schemas Pydantic
```python
from pydantic import BaseModel, ConfigDict

def to_camel(string: str) -> str:
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

class MySchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )
```

## Comandos

### Desarrollo Local
```bash
# Iniciar con Docker
docker-compose up -d

# Reiniciar API (hot-reload automático, pero si es necesario)
docker restart evotrack-api

# Ver logs
docker logs -f evotrack-api

# Sin Docker
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Migraciones (Alembic)
```bash
# Crear migración
alembic revision --autogenerate -m "descripción"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1
```

### Testing
```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=app --cov-report=term-missing
```

### Linting
```bash
black app/
isort app/
mypy app/
```

## Configuración

### Variables de Entorno (.env)
```env
# Database
DATABASE_URL=postgresql://user:pass@host:port/db
POSTGRES_USER=evotrack_user
POSTGRES_PASSWORD=evotrack_password
POSTGRES_DB=evotrack_db

# Security
SECRET_KEY=your-secret-key-here

# Server
DEBUG=True
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Puertos
| Servicio | Puerto Interno | Puerto Externo |
|----------|---------------|----------------|
| FastAPI | 8000 | 8000 |
| PostgreSQL | 5432 | 5433 |

## Autenticación

- **Access Token**: JWT, expira en 30 minutos
- **Refresh Token**: JWT, expira en 7 días
- Header: `Authorization: Bearer {access_token}`
- Algoritmo: HS256

### Endpoints de Auth
```
POST /api/v1/auth/login          # Login
POST /api/v1/auth/refresh        # Refresh token
POST /api/v1/auth/logout         # Logout
```

## URLs Útiles

- API Docs (Swagger): http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI JSON: http://localhost:8000/api/openapi.json
- Health Check: http://localhost:8000/health

## Git

### Convención de Commits
```
feat: nueva funcionalidad
fix: corrección de bug
refactor: refactorización de código
docs: documentación
test: tests
chore: tareas de mantenimiento
```

### Branches
- `main`: producción
- `develop`: desarrollo
- `feature/*`: nuevas funcionalidades
- `fix/*`: correcciones
