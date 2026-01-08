#!/bin/bash
# Database initialization script
# This ensures the database is created correctly

set -e

echo "🗄️  Initializing PostgreSQL database..."

# Wait for PostgreSQL to be ready
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -c '\q' 2>/dev/null; do
  echo "⏳ Waiting for PostgreSQL to be ready..."
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Create database if it doesn't exist
PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -tc "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DB'" | grep -q 1 || \
PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -c "CREATE DATABASE $POSTGRES_DB"

echo "✅ Database '$POSTGRES_DB' is ready!"

# Run Alembic migrations
echo "🔄 Running database migrations..."
alembic upgrade head

echo "✅ Database initialization complete!"
