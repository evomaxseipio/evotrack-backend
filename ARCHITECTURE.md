# 🏗️ EvoTrack Backend Architecture

## Overview

EvoTrack backend follows a **clean architecture** approach with clear separation of concerns, organized by domain (modules) rather than by technical layer.

## Core Principles

### 1. Domain-Driven Design
Each module represents a bounded context in the business domain:
- `auth` - Authentication and authorization
- `users` - User management
- `organizations` - Organization hierarchy
- `projects` - Projects and time tracking
- `reports` - Report generation
- `notifications` - Communication

### 2. Repository Pattern
Separates data access logic from business logic:

```python
# repository.py - Data access layer
class UserRepository(BaseRepository[User]):
    def get_by_email(self, email: str) -> Optional[User]:
        return self.get_by_field("email", email)

# service.py - Business logic layer
class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository
    
    def create_user(self, data: UserCreate) -> User:
        # Business validation
        if self.repository.get_by_email(data.email):
            raise AlreadyExistsException("User", "email", data.email)
        
        # Create user
        return self.repository.create(data.dict())
```

### 3. Dependency Injection
FastAPI's dependency injection system is used extensively:

```python
# dependencies.py
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(User, db)

def get_user_service(
    repository: UserRepository = Depends(get_user_repository)
) -> UserService:
    return UserService(repository)

# router.py
@router.post("/")
def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    return service.create_user(data)
```

### 4. Standardized Error Handling
Custom exceptions are caught by global handlers:

```python
# In service
if not user:
    raise NotFoundException("User", user_id)

# Automatically converted to:
# {"success": false, "error": "User with identifier '123' not found"}
# With appropriate HTTP status code (404)
```

## Directory Structure by Layer

### Core Layer (`app/core/`)
Infrastructure and cross-cutting concerns:
- **config.py**: Environment-based configuration
- **database.py**: SQLAlchemy engine and sessions
- **security.py**: JWT tokens, password hashing
- **logging.py**: Structured logging setup
- **dependencies.py**: Common FastAPI dependencies

### Module Layer (`app/modules/`)
Business logic organized by domain:

```
module/
├── router.py          # HTTP endpoints
├── schemas.py         # Pydantic request/response models
├── models.py          # SQLAlchemy ORM models
├── service.py         # Business logic
├── repository.py      # Database operations
└── dependencies.py    # Module-specific dependencies
```

**Responsibility Breakdown**:
- **router.py**: HTTP concerns only (parsing, validation, status codes)
- **service.py**: Business rules, orchestration, validation
- **repository.py**: Database queries, raw data access
- **models.py**: Database schema definition
- **schemas.py**: API contract definition

### Shared Layer (`app/shared/`)
Reusable utilities across all modules:
- **base_repository.py**: Generic CRUD operations
- **exceptions.py**: Custom exception hierarchy
- **responses.py**: Standardized API response formats
- **pagination.py**: Pagination utilities
- **utils.py**: Common helper functions

## Data Flow

### Request Flow
```
HTTP Request
    ↓
Router (validates request)
    ↓
Dependencies (inject services, auth)
    ↓
Service (business logic)
    ↓
Repository (database access)
    ↓
Database
```

### Response Flow
```
Database
    ↓
Repository (returns model)
    ↓
Service (transforms, applies business rules)
    ↓
Router (serializes to schema)
    ↓
HTTP Response
```

## Module Communication

Modules should be as independent as possible:

✅ **Good**: Service-to-service communication via dependency injection
```python
class ProjectService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        user_service: UserService  # Inject other service
    ):
        self.project_repo = project_repo
        self.user_service = user_service
```

❌ **Bad**: Direct repository access across modules
```python
# DON'T DO THIS
from app.modules.users.repository import UserRepository

class ProjectService:
    def __init__(self):
        self.user_repo = UserRepository(...)  # ❌ Wrong!
```

## Testing Strategy

### Unit Tests
Test services in isolation with mocked repositories:
```python
def test_create_user():
    mock_repo = Mock(spec=UserRepository)
    service = UserService(mock_repo)
    
    service.create_user(user_data)
    mock_repo.create.assert_called_once()
```

### Integration Tests
Test full request/response cycle:
```python
def test_create_user_endpoint(client):
    response = client.post("/api/v1/users", json=user_data)
    assert response.status_code == 201
```

## Error Handling

### Exception Hierarchy
```
EvoTrackException (base)
├── NotFoundException (404)
├── AlreadyExistsException (409)
├── UnauthorizedException (401)
├── ForbiddenException (403)
├── ValidationException (422)
├── DatabaseException (500)
└── BusinessLogicException (400)
```

### Usage
```python
# In service
if not entity:
    raise NotFoundException("Project", project_id)

# Automatically handled by exception handler in main.py
# Returns: 404 with standardized JSON error response
```

## API Response Format

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... }
}
```

### Error Response
```json
{
  "success": false,
  "error": "User with identifier '123' not found",
  "error_code": "NOT_FOUND",
  "details": { ... }
}
```

### Paginated Response
```json
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5,
    "has_next": true,
    "has_previous": false
  }
}
```

## Database Patterns

### Timestamps
All models inherit timestamp fields:
```python
class BaseModel:
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

### Soft Deletes (when needed)
```python
class User(Base):
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
```

## Security

### Authentication Flow
1. User sends credentials to `/auth/login`
2. Service validates credentials
3. JWT token generated with user ID
4. Token returned to client
5. Client includes token in `Authorization: Bearer <token>` header
6. Dependency extracts and validates token
7. User ID injected into endpoint

### Authorization
```python
@router.get("/admin-only")
def admin_endpoint(
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin_role)
):
    # Only admins can access
    pass
```

## Performance Considerations

### Database Queries
- Use `.all()` only when needed
- Prefer pagination for large datasets
- Use `.first()` for single records
- Eager load relationships with `joinedload()`

### Caching Strategy (Future)
- Redis for session storage
- Cache frequently accessed data
- Invalidate on updates

### Async Operations (Future)
- Celery for long-running tasks
- Report generation
- Email sending
- Data exports

## Deployment

### Environment-Based Configuration
```python
# Development
ENVIRONMENT=development
DEBUG=True

# Production
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<strong-secret>
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Best Practices

### DO ✅
- Keep routers thin (only HTTP concerns)
- Put business logic in services
- Use repository for all database access
- Validate in Pydantic schemas
- Use custom exceptions
- Write tests
- Document public APIs

### DON'T ❌
- Put business logic in routers
- Access database directly from routers
- Use generic `Exception` classes
- Skip validation
- Hardcode configuration
- Mix responsibilities

## Future Enhancements

1. **Event System**: Domain events for module communication
2. **CQRS**: Separate read/write models for complex queries
3. **GraphQL**: Alternative API for complex data requirements
4. **Microservices**: Split modules into separate services if needed
5. **Message Queue**: RabbitMQ for async communication

---

**Remember**: The goal is **maintainability** and **scalability**. This architecture allows us to:
- Add new modules easily
- Test components in isolation
- Scale specific modules independently
- Onboard new developers quickly
- Refactor without breaking everything
