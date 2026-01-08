#!/bin/bash
# EvoTrack Backend - Setup Validation Script

echo "🚀 EvoTrack Backend - Setup Validation"
echo "========================================"
echo ""

# Check Python version
echo "✓ Checking Python version..."
python3 --version

# Check if requirements.txt exists
echo "✓ Checking requirements.txt..."
if [ -f "requirements.txt" ]; then
    echo "  Found requirements.txt with $(wc -l < requirements.txt) dependencies"
else
    echo "  ❌ requirements.txt not found"
fi

# Check if .env exists
echo "✓ Checking .env file..."
if [ -f ".env" ]; then
    echo "  Found .env file"
else
    echo "  ❌ .env file not found"
fi

# Check if docker-compose.yml exists
echo "✓ Checking docker-compose.yml..."
if [ -f "docker-compose.yml" ]; then
    echo "  Found docker-compose.yml"
else
    echo "  ❌ docker-compose.yml not found"
fi

# Check if alembic.ini exists
echo "✓ Checking alembic.ini..."
if [ -f "alembic.ini" ]; then
    echo "  Found alembic.ini"
else
    echo "  ❌ alembic.ini not found"
fi

# Check directory structure
echo "✓ Checking directory structure..."
directories=("app/core" "app/shared" "app/modules/auth" "app/modules/organizations" "app/modules/users" "app/modules/projects" "alembic/versions" "uploads")

for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir"
    else
        echo "  ❌ $dir not found"
    fi
done

echo ""
echo "========================================"
echo "Setup validation complete!"
echo ""
echo "Next steps:"
echo "1. Run: docker-compose up --build"
echo "2. Visit: http://localhost:8000"
echo "3. API Docs: http://localhost:8000/api/docs"
echo ""
