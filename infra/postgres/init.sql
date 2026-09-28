-- Extensions
CREATE EXTENSION IF NOT EXISTS pgvector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Application setting for RLS tenant isolation
-- Usage: SET LOCAL app.tenant_id = '<uuid>' per transaction
ALTER DATABASE nudgeline SET app.tenant_id TO '';

-- Grant permissions for the RLS session variable
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app'
    ) THEN
        CREATE ROLE app NOLOGIN;
    END IF;
END
$$;
