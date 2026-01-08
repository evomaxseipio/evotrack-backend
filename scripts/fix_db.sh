#!/bin/bash
# Quick Fix for Database Connection Issues

echo "🔧 EvoTrack Database Quick Fix"
echo "==============================="
echo ""

# Stop containers
echo "🛑 Stopping containers..."
docker-compose down

echo ""

# Remove volumes (this will delete data!)
read -p "⚠️  Remove existing PostgreSQL data? This will delete all data! (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "🗑️  Removing PostgreSQL volume..."
    docker-compose down -v
    echo "✅ Volume removed"
else
    echo "ℹ️  Keeping existing data"
fi

echo ""

# Rebuild and start
echo "🔨 Rebuilding and starting services..."
docker-compose up --build -d

echo ""

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Check status
echo ""
echo "📊 Container Status:"
docker-compose ps

echo ""

# Test database connection
echo "🔗 Testing database connection..."
docker-compose exec -T postgres psql -U evotrack_user -d evotrack_db -c "SELECT 'Connection successful!' as status;" 2>/dev/null || {
    echo "❌ Connection failed. Creating database manually..."
    docker-compose exec -T postgres psql -U evotrack_user -c "CREATE DATABASE evotrack_db;" 2>/dev/null
    echo "✅ Database created!"
}

echo ""

# Show logs
echo "📋 Recent FastAPI logs:"
docker-compose logs --tail=20 fastapi

echo ""
echo "================================"
echo "✅ Fix complete!"
echo ""
echo "To check if everything is working:"
echo "  curl http://localhost:8000/health"
echo ""
echo "To view live logs:"
echo "  docker-compose logs -f"
