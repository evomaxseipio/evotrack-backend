# 🚀 CI/CD Pipeline Documentation

## Overview

EvoTrack uses **GitHub Actions** for continuous integration and deployment, with automated testing, linting, and deployment to **Railway**.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Git Push / Pull Request                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │    CI Pipeline (Parallel)   │
        └────────────┬────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐      ┌──────────────────┐
│  Test Suite   │      │  Code Quality    │
│  - Unit       │      │  - Ruff          │
│  - Integration│      │  - Black         │
│  - Coverage   │      │  - isort         │
└───────┬───────┘      │  - mypy          │
        │              │  - Security      │
        │              └────────┬─────────┘
        │                       │
        └───────────┬───────────┘
                    │
                    ▼
            ┌───────────────┐
            │  All Checks   │
            │    Pass?      │
            └───────┬───────┘
                    │
                    ▼ (main branch only)
            ┌───────────────┐
            │   Deploy to   │
            │    Railway    │
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │  Post-Deploy  │
            │  - Migrations │
            │  - Health     │
            └───────────────┘
```

---

## GitHub Actions Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)

Runs on: **Push to main/develop** and **Pull Requests**

#### Jobs

**Test Job**:
- Matrix testing on Python 3.11 and 3.12
- PostgreSQL service container
- Run pytest with coverage
- Upload coverage to Codecov

**Lint Job**:
- Ruff linting
- Black formatting check
- isort import sorting check
- mypy type checking

**Security Job**:
- Safety dependency scanning
- Bandit security linting

#### Test Database

Uses PostgreSQL 15 in GitHub Actions service container:
```yaml
services:
  postgres:
    image: postgres:15-alpine
    env:
      POSTGRES_USER: evotrack_test
      POSTGRES_PASSWORD: test_password
      POSTGRES_DB: evotrack_test_db
```

### 2. CD Workflow (`.github/workflows/cd.yml`)

Runs on: **Push to main** (manual trigger also available)

#### Jobs

**Deploy Job**:
- Install Railway CLI
- Deploy to Railway
- Notifications on success/failure

**Post-Deploy Job**:
- Run Alembic migrations
- Health check verification
- Slack notifications (optional)

---

## Setup Instructions

### 1. GitHub Repository Setup

```bash
# Initialize git repository
git init
git add .
git commit -m "Initial commit with CI/CD"

# Create GitHub repository and push
git remote add origin https://github.com/yourusername/evotrack-backend.git
git branch -M main
git push -u origin main
```

### 2. GitHub Secrets Configuration

Go to: `Settings → Secrets and variables → Actions → New repository secret`

**Required Secrets**:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `RAILWAY_TOKEN` | Railway API token | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `RAILWAY_APP_URL` | Deployed app URL | `https://evotrack-backend-production.up.railway.app` |
| `CODECOV_TOKEN` | Codecov upload token | Optional for coverage |
| `SLACK_WEBHOOK` | Slack webhook for notifications | Optional |

### 3. Railway Setup

#### Step 1: Create Railway Account
1. Go to [Railway.app](https://railway.app)
2. Sign up with GitHub
3. Create new project

#### Step 2: Add PostgreSQL Database
1. Click "New" → "Database" → "PostgreSQL"
2. Railway will automatically provision database
3. Database URL available as `DATABASE_URL` variable

#### Step 3: Deploy Backend Service
1. Click "New" → "GitHub Repo"
2. Select your `evotrack-backend` repository
3. Railway auto-detects Dockerfile

#### Step 4: Configure Environment Variables

In Railway dashboard, add these variables:

```bash
# Application
ENVIRONMENT=production
DEBUG=False
APP_NAME=EvoTrack
APP_VERSION=1.0.0

# Database (auto-configured by Railway)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Security
SECRET_KEY=<generate-strong-secret-key-here>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Logging
LOG_LEVEL=INFO
```

#### Step 5: Get Railway Token

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Get token (for GitHub Actions)
railway whoami
```

Copy the token and add it to GitHub Secrets as `RAILWAY_TOKEN`.

### 4. Local Development Setup

#### Install Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

#### Run Tests Locally

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_main.py -v

# Run with markers
pytest -m "unit"  # Only unit tests
pytest -m "integration"  # Only integration tests
```

#### Run Linting

```bash
# Ruff (fast linter)
ruff check app/ tests/

# Fix issues automatically
ruff check app/ tests/ --fix

# Black (formatter)
black app/ tests/ --check
black app/ tests/  # Format files

# isort (import sorting)
isort app/ tests/ --check-only
isort app/ tests/  # Sort imports

# mypy (type checking)
mypy app/ --ignore-missing-imports
```

---

## Workflow Triggers

### CI Workflow Triggers

```yaml
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
```

**Runs when**:
- Push to `main` or `develop`
- Pull request to `main` or `develop`
- Manual workflow dispatch

### CD Workflow Triggers

```yaml
on:
  push:
    branches: [ main ]
  workflow_dispatch:
```

**Runs when**:
- Push to `main` (after CI passes)
- Manual trigger from Actions tab

---

## Testing Strategy

### Test Categories

```python
# Unit tests
@pytest.mark.unit
def test_password_hashing():
    ...

# Integration tests
@pytest.mark.integration
def test_user_registration_flow():
    ...

# Database tests
@pytest.mark.db
def test_user_repository():
    ...

# Slow tests
@pytest.mark.slow
def test_report_generation():
    ...
```

### Coverage Requirements

- **Minimum**: 80% overall coverage
- **Exclude**: Tests, migrations, `__init__.py` files
- Reports generated in `htmlcov/` directory

### Running Specific Tests

```bash
# By marker
pytest -m unit
pytest -m "not slow"

# By file
pytest tests/test_main.py

# By function name
pytest tests/test_main.py::test_health_check

# With output
pytest -v -s  # Verbose with stdout

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf
```

---

## Code Quality Standards

### Ruff Configuration

- Line length: 100 characters
- Python 3.11 target
- Enabled rules: pycodestyle, pyflakes, isort, bugbear
- Auto-fix available

### Black Configuration

- Line length: 100 characters
- Python 3.11 target
- Double quotes for strings

### Import Sorting (isort)

- Profile: black
- Known first party: `app`
- Multi-line: trailing comma

---

## Deployment Process

### Automatic Deployment

1. **Developer pushes to `main`**
   ```bash
   git push origin main
   ```

2. **CI runs** (5-10 minutes)
   - Tests execute
   - Linting checks
   - Security scan

3. **CD triggers** (if CI passes)
   - Railway deployment starts
   - Docker image builds
   - App deploys

4. **Post-deployment**
   - Database migrations run
   - Health check verifies
   - Notifications sent

### Manual Deployment

```bash
# Using Railway CLI
railway up

# Or trigger GitHub Action manually
# Go to: Actions → CD - Deploy to Railway → Run workflow
```

### Rollback

```bash
# Using Railway CLI
railway rollback

# Or redeploy previous commit
git revert HEAD
git push origin main
```

---

## Monitoring & Debugging

### View Deployment Logs

**GitHub Actions**:
```
Repository → Actions → Select workflow run → View logs
```

**Railway**:
```
Railway Dashboard → Project → Service → Deployments → View logs
```

### Health Check Endpoints

```bash
# Health check
curl https://your-app.railway.app/health

# API info
curl https://your-app.railway.app/

# API documentation
open https://your-app.railway.app/api/docs
```

### Check CI Status

GitHub provides status badges you can add to README:

```markdown
![CI Status](https://github.com/yourusername/evotrack-backend/workflows/CI/badge.svg)
![Deploy Status](https://github.com/yourusername/evotrack-backend/workflows/CD/badge.svg)
```

---

## Troubleshooting

### CI Failures

**Tests failing**:
```bash
# Run tests locally first
pytest -v

# Check test database connection
docker-compose up -d postgres
pytest
```

**Linting errors**:
```bash
# Fix automatically
ruff check app/ tests/ --fix
black app/ tests/
isort app/ tests/
```

**Type errors**:
```bash
# Run mypy locally
mypy app/ --ignore-missing-imports
```

### Deployment Failures

**Database connection**:
- Check `DATABASE_URL` in Railway env vars
- Verify PostgreSQL service is running
- Check migrations are up to date

**Build failures**:
- Check Dockerfile syntax
- Verify all dependencies in requirements.txt
- Check Railway build logs

**Runtime errors**:
- Check Railway logs for error details
- Verify all env vars are set
- Check SECRET_KEY is configured

---

## Best Practices

### Branch Strategy

```
main (production)
  ↑
develop (staging)
  ↑
feature/xyz (development)
```

### Commit Messages

```bash
# Good
git commit -m "feat: add user authentication endpoint"
git commit -m "fix: resolve database connection timeout"
git commit -m "test: add tests for organization CRUD"

# Bad
git commit -m "update"
git commit -m "fixes"
```

### Pull Request Checklist

- [ ] Tests pass locally
- [ ] Linting passes
- [ ] Coverage maintained or improved
- [ ] Documentation updated
- [ ] Migrations created (if needed)
- [ ] Environment variables documented

---

## Performance Optimization

### GitHub Actions Caching

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.11"
    cache: 'pip'  # Cache pip dependencies
```

### Docker Layer Caching

Multi-stage build reduces image size:
- Builder stage: ~500MB
- Production stage: ~200MB

### Test Optimization

```bash
# Parallel test execution
pytest -n auto  # Requires pytest-xdist

# Run fast tests first
pytest -m "not slow"
```

---

## Security Considerations

### Secret Management

- ✅ Never commit secrets to repository
- ✅ Use GitHub Secrets for sensitive data
- ✅ Rotate secrets regularly
- ✅ Use different secrets for dev/staging/prod

### Dependency Scanning

- `safety check` runs on every CI build
- Alerts on known vulnerabilities
- Auto-update dependencies with Dependabot

### Code Scanning

- `bandit` scans for security issues
- Ruff includes security rules
- Pre-commit hooks prevent commits with issues

---

## Cost Optimization

### Railway Pricing

- **Free Tier**: $5/month credit
- **Usage-based**: $0.000463/GB-hour RAM
- **PostgreSQL**: Included in usage

### Optimization Tips

1. **Use sleep policy** for non-production
2. **Optimize Docker image** (multi-stage build)
3. **Database connection pooling**
4. **Efficient queries** (avoid N+1)

---

## Future Enhancements

- [ ] Add staging environment
- [ ] Implement blue-green deployments
- [ ] Add performance testing
- [ ] Integrate SonarQube for code quality
- [ ] Add smoke tests post-deployment
- [ ] Implement feature flags
- [ ] Add A/B testing capabilities

---

## Support & Resources

- **GitHub Actions Docs**: https://docs.github.com/actions
- **Railway Docs**: https://docs.railway.app
- **Pytest Docs**: https://docs.pytest.org
- **Ruff Docs**: https://docs.astral.sh/ruff

---

**Last Updated**: January 2026  
**Maintained by**: Evolution Technology Team
