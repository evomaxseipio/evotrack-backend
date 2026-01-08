-- Initialization script for EvoTrack PostgreSQL database
-- This ensures the database exists on container startup

SELECT 'CREATE DATABASE evotrack_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'evotrack_db')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE evotrack_db TO evotrack_user;
