-- ===========================
-- PostgreSQL + PostGIS init
-- ===========================
-- Runs once on first container start

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Spatial index on hotspots location for fast bbox queries
-- (Tables created by SQLAlchemy on startup; this adds extras)

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE sharksfromspace TO sharks;
