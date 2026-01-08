#!/bin/bash
# Database Diagnostic and Fix Script

echo "🔍 EvoTrack Database Diagnostic"
echo "================================"
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "📊 Current Configuration:"
echo "  POSTGRES_USER: $POSTGRES_USER"
echo "  POSTGRES_DB: $POSTGRES_DB"
echo "  POSTGRES_HOST: $POSTGRES_HOST"
echo "  DATABASE_URL: $DATABASE_URL"
echo ""

# Check if containers are running
echo "🐳 Checking Docker containers..."
if docker-compose ps | grep -q "evotrack-postgres.*Up"; then
    echo -e "${GREEN}✓${NC} PostgreSQL container is running"
else
    echo -e "${RED}✗${NC} PostgreSQL container is not running"
    echo "  Run: docker-compose up -d postgres"
    exit 1
fi

echo ""

# Check PostgreSQL connection
echo "🔌 Testing PostgreSQL connection..."
if docker-compose exec -T postgres pg_isready -U $POSTGRES_USER -h localhost 2>/dev/null; then
    echo -e "${GREEN}✓${NC} PostgreSQL is accepting connections"
else
    echo -e "${RED}✗${NC} PostgreSQL is not ready"
    echo "  Waiting for PostgreSQL to start..."
    sleep 5
fi

echo ""

# List existing databases
echo "📋 Existing databases:"
docker-compose exec -T postgres psql -U $POSTGRES_USER -c "\l" 2>/dev/null | grep -E "Name|$POSTGRES_USER|$POSTGRES_DB" || echo "  Could not list databases"

echo ""

# Check if our database exists
echo "🔍 Checking if '$POSTGRES_DB' database exists..."
DB_EXISTS=$(docker-compose exec -T postgres psql -U $POSTGRES_USER -tAc "SELECT 1 FROM pg_database WHERE datname='$POSTGRES_DB'" 2>/dev/null)

if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${GREEN}✓${NC} Database '$POSTGRES_DB' exists"
else
    echo -e "${YELLOW}!${NC} Database '$POSTGRES_DB' does not exist"
    echo ""
    echo "🛠️  Creating database..."
    docker-compose exec -T postgres psql -U $POSTGRES_USER -c "CREATE DATABASE $POSTGRES_DB;" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Database '$POSTGRES_DB' created successfully!"
    else
        echo -e "${RED}✗${NC} Failed to create database"
        exit 1
    fi
fi

echo ""

# Test database connection from FastAPI
echo "🔗 Testing database connection from FastAPI container..."
docker-compose exec -T fastapi python -c "
from app.core.database import engine
try:
    connection = engine.connect()
    connection.close()
    print('✓ Connection successful!')
except Exception as e:
    print(f'✗ Connection failed: {e}')
" 2>/dev/null || echo -e "${YELLOW}!${NC} FastAPI container not running or connection test failed"

echo ""
echo "================================"
echo "✅ Diagnostic complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Restart services: docker-compose restart"
echo "  2. View logs: docker-compose logs -f fastapi"
echo "  3. Run migrations: docker-compose exec fastapi alembic upgrade head"
