# 🚀 EvoTrack Backend API

**Where Time Evolves** - A comprehensive time tracking and expense management platform built with FastAPI, PostgreSQL, and modern Python practices.

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development](#development)
- [Database Migrations](#database-migrations)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)

## 🎯 Overview

EvoTrack is a B2B SaaS platform designed for professional services companies to manage:
- ⏱️ Time tracking and timesheets
- 💰 Expense management
- 📊 Project management
- 👥 Team collaboration
- 📈 Advanced analytics and reporting
- 💳 Multi-currency support
- 🌍 International compliance

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic 1.13
- **Authentication**: JWT (python-jose)
- **Password Hashing**: Bcrypt (passlib)
- **Containerization**: Docker + Docker Compose
- **Python**: 3.11+

## 📁 Project Structure

```
evotrack-backend/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── api.py                     # Centralized router registration
│   │
│   ├── core/                      # Cross-cutting infrastructure
│   │   ├── config.py              # Application settings
│   │   ├── database.py            # Database engine and session
│   │   ├── security.py            # JWT, password hashing
│   │   ├── logging.py             # Logging configuration
│   │   └── dependencies.py        # Common FastAPI dependencies
│   │
│   ├── modules/                   # Business logic by domain
│   │   ├── auth/                  # Authentication
│   │   │   ├── router.py          # API endpoints
│   │   │   ├── schemas.py         # Pydantic models
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   ├── service.py         # Business logic
│   │   │   ├── repository.py      # Database access layer
│   │   │   └── dependencies.py    # Module dependencies
│   │   │
│   │   ├── users/                 # User management
│   │   ├── organizations/         # Organization management
│   │   ├── projects/              # Project & time tracking
│   │   ├── reports/               # Report generation
│   │   └── notifications/         # Email & notifications
│   │
│   └── shared/                    # Reusable utilities
│       ├── base_repository.py     # Generic repository pattern
│       ├── pagination.py          # Pagination utilities
│       ├── exceptions.py          # Custom exceptions
│       ├── responses.py           # Standard API responses
│       └── utils.py               # Helper functions
│
├── alembic/                       # Database migrations
│   ├── versions/
│   └── env.py
│
├── tests/                         # Test suite
│   ├── conftest.py
│   ├── auth/
│   ├── users/
│   └── organizations/
│
├── scripts/                       # Administrative scripts
│
├── docker-compose.yml             # Docker services
├── Dockerfile                     # Container definition
├── requirements.txt               # Python dependencies
├── alembic.ini                   # Alembic configuration
└── README.md                     # This file
```

### Architecture Patterns

- **Repository Pattern**: Separates database access from business logic
- **Service Layer**: Business logic centralized in service files
- **Dependency Injection**: Module-specific dependencies per domain
- **Standardized Responses**: Consistent API response formats

## ✅ Prerequisites

- **Docker Desktop** (includes Docker Compose)
  - [Download for Mac](https://docs.docker.com/desktop/install/mac-install/)
  - [Download for Windows](https://docs.docker.com/desktop/install/windows-install/)
  - [Download for Linux](https://docs.docker.com/desktop/install/linux-install/)

**OR** for local development:

- Python 3.11+
- PostgreSQL 15+
- pip or poetry

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd evotrack-backend

# Copy environment variables
cp .env.example .env

# Edit .env with your settings (optional for local development)
nano .env
```

### 2. Start with Docker (Recommended)

```bash
# Build and start services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f fastapi
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### 3. Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","app":"EvoTrack","version":"1.0.0"}
```

## 🔄 CI/CD Pipeline

EvoTrack uses **GitHub Actions** for continuous integration and **Railway** for deployment.

### CI Workflow
- ✅ Runs on push to main/develop and pull requests
- ✅ Python 3.11 & 3.12 matrix testing
- ✅ PostgreSQL service container
- ✅ Linting with Ruff, Black, isort, mypy
- ✅ Security scanning with Safety and Bandit
- ✅ Code coverage with pytest-cov

### CD Workflow
- 🚀 Auto-deploy to Railway on push to main
- 🔄 Database migrations with Alembic
- 💚 Health check verification
- 📬 Slack notifications (optional)

See [docs/CI_CD.md](docs/CI_CD.md) for complete documentation.

### Setup CI/CD

1. **Configure GitHub Secrets**:
   - `RAILWAY_TOKEN` - Railway API token
   - `RAILWAY_APP_URL` - Deployed app URL

2. **Install Pre-commit Hooks** (optional):
```bash
pip install pre-commit
pre-commit install
```

3. **Run Tests Locally**:
```bash
pip install -r requirements-dev.txt
pytest --cov=app
```

## 💻 Development

### Local Development (Without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup PostgreSQL database
createdb evotrack_db

# Update DATABASE_URL in .env
# DATABASE_URL=postgresql://username:password@localhost:5432/evotrack_db

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Commands

```bash
# Stop services
docker-compose down

# Stop and remove volumes (clears database)
docker-compose down -v

# Rebuild after changes
docker-compose up --build

# Execute commands in container
docker-compose exec fastapi bash
docker-compose exec postgres psql -U evotrack_user -d evotrack_db

# View logs
docker-compose logs -f [service_name]
```

## 🗄️ Database Migrations

### Create Migration

```bash
# Auto-generate migration from models
docker-compose exec fastapi alembic revision --autogenerate -m "description"

# Or locally
alembic revision --autogenerate -m "Add users table"
```

### Apply Migrations

```bash
# Apply all pending migrations
docker-compose exec fastapi alembic upgrade head

# Or locally
alembic upgrade head
```

### Rollback Migrations

```bash
# Rollback one revision
docker-compose exec fastapi alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

### View Migration History

```bash
# Show current revision
alembic current

# Show migration history
alembic history
```

## 📚 API Documentation

Once the server is running, access interactive documentation:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

### Key Endpoints

```
GET  /                      # API information
GET  /health                # Health check
GET  /api/v1                # API version info

# Authentication (Coming in Sprint 2)
POST /api/v1/auth/login     # User login
POST /api/v1/auth/register  # User registration
POST /api/v1/auth/refresh   # Refresh token

# Organizations
GET    /api/v1/organizations      # List organizations
POST   /api/v1/organizations      # Create organization
GET    /api/v1/organizations/{id} # Get organization
PUT    /api/v1/organizations/{id} # Update organization
DELETE /api/v1/organizations/{id} # Delete organization
```

## 🧪 Testing

```bash
# Run tests (when implemented)
docker-compose exec fastapi pytest

# Run with coverage
docker-compose exec fastapi pytest --cov=app --cov-report=html

# Run specific test file
docker-compose exec fastapi pytest tests/test_auth.py
```

## 🚢 Deployment

### Environment Variables for Production

Update `.env` with production values:

```env
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<generate-strong-secret-key>
DATABASE_URL=<production-database-url>
ALLOWED_ORIGINS=https://yourdomain.com
```

### Generate Secret Key

```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Docker Production Build

```bash
# Build production image
docker build -t evotrack-api:latest .

# Run production container
docker run -d \
  --name evotrack-api \
  -p 8000:8000 \
  --env-file .env.production \
  evotrack-api:latest
```

## 📊 Project Status

**Sprint 1** (Current): Foundation & Organizations
- ✅ FastAPI project structure
- ✅ Docker Compose setup
- ✅ Alembic configuration
- ⏳ Organization models and API
- ⏳ Authentication system
- ⏳ User management

## 🔐 Security Notes

1. **Never commit `.env` files** to version control
2. **Change default SECRET_KEY** in production
3. **Use strong passwords** for database users
4. **Enable HTTPS** in production
5. **Regular security updates** for dependencies

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/amazing-feature`
2. Commit changes: `git commit -m 'Add amazing feature'`
3. Push to branch: `git push origin feature/amazing-feature`
4. Open Pull Request

## 📝 License

Copyright © 2026 Evolution Technology

## 🆘 Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Connect to database
docker-compose exec postgres psql -U evotrack_user -d evotrack_db
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill process or change PORT in .env
```

### Container Build Failures

```bash
# Clean rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

## 📞 Support

- **Documentation**: http://localhost:8000/api/docs
- **Issues**: Create issue in repository
- **Email**: support@evolutiontech.com

---

**Built with ❤️ by Evolution Technology**

*Where Time Evolves* ⚡
