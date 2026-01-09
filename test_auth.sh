#!/bin/bash
# Run Alembic migration and test authentication endpoints

set -e

echo "🚀 EvoTrack - Authentication Setup"
echo "==================================="
echo ""

# Check if containers are running
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Docker containers are not running"
    echo "Run: docker-compose up -d"
    exit 1
fi

echo "✓ Docker containers are running"
echo ""

# Run Alembic migration
echo "📊 Running database migration..."
docker-compose exec -T fastapi alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✓ Migration completed successfully"
else
    echo "❌ Migration failed"
    exit 1
fi

echo ""
echo "🧪 Testing authentication endpoints..."
echo ""

# Test 1: Register user
echo "1️⃣  Testing user registration..."
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@evotrack.com",
    "password": "SecurePass123",
    "first_name": "Test",
    "last_name": "User",
    "timezone": "America/New_York"
  }')

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    echo "✓ User registration successful"
    ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
else
    echo "❌ User registration failed"
    echo "$REGISTER_RESPONSE"
    exit 1
fi

echo ""

# Test 2: Login
echo "2️⃣  Testing user login..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@evotrack.com",
    "password": "SecurePass123"
  }')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✓ User login successful"
else
    echo "❌ User login failed"
    echo "$LOGIN_RESPONSE"
    exit 1
fi

echo ""

# Test 3: Get current user
echo "3️⃣  Testing get current user..."
ME_RESPONSE=$(curl -s -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$ME_RESPONSE" | grep -q "test@evotrack.com"; then
    echo "✓ Get current user successful"
else
    echo "❌ Get current user failed"
    echo "$ME_RESPONSE"
    exit 1
fi

echo ""

# Test 4: Health check
echo "4️⃣  Testing API health..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✓ API is healthy"
else
    echo "❌ API health check failed"
    exit 1
fi

echo ""
echo "=================================="
echo "✅ All authentication tests passed!"
echo ""
echo "Available endpoints:"
echo "  POST   /api/v1/auth/register"
echo "  POST   /api/v1/auth/login"
echo "  POST   /api/v1/auth/refresh"
echo "  GET    /api/v1/auth/me"
echo "  POST   /api/v1/auth/logout"
echo ""
echo "API Documentation:"
echo "  http://localhost:8000/api/docs"
echo ""
echo "Run pytest for complete test suite:"
echo "  docker-compose exec fastapi pytest tests/auth/ -v"
