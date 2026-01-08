#!/bin/bash
# Fix PostgreSQL Database Issue

echo "🔧 Fixing PostgreSQL Database Issue"
echo "===================================="
echo ""

echo "1️⃣ Stopping containers..."
docker-compose down

echo ""
echo "2️⃣ Removing volumes (this will delete all data)..."
docker-compose down -v

echo ""
echo "3️⃣ Starting fresh containers..."
docker-compose up -d

echo ""
echo "4️⃣ Waiting for PostgreSQL to be ready..."
sleep 10

echo ""
echo "5️⃣ Checking database..."
docker-compose exec postgres psql -U evotrack_user -d evotrack_db -c "SELECT version();"

echo ""
echo "✅ Database should be fixed!"
echo ""
echo "View logs:"
echo "  docker-compose logs -f fastapi"
echo ""
echo "Test API:"
echo "  curl http://localhost:8000/health"
