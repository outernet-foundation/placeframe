-- params:
-- identifiers: {owner}, {api_user}, {orchestration_user}, {auth_user}, {database}
-- literals:    {owner_literal}, {api_user_literal}, {orchestration_user_literal},
--              {auth_user_literal}, {database_literal}
-- passwords:   {owner_password}, {api_user_password}, {auth_user_password},
--              {orchestration_user_password}
--
-- Cluster-scope setup connected to the target database, run before the schema
-- bootstrap: roles, database-level grants, extensions, ownership. Schema usage
-- and function-EXECUTE hardening run after the bootstrap in
-- harden_schemas.template.sql, once the schema dir has created the schemas.

-- Ensure owner role exists and has desired password
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = {owner_literal}) THEN
    CREATE ROLE {owner} LOGIN CREATEDB PASSWORD {owner_password};
  ELSE
    ALTER ROLE {owner} WITH LOGIN CREATEDB PASSWORD {owner_password};
  END IF;
END
$$;

-- Ensure API user role exists and has desired password
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = {api_user_literal}) THEN
    CREATE ROLE {api_user} LOGIN PASSWORD {api_user_password};
  ELSE
    ALTER ROLE {api_user} LOGIN PASSWORD {api_user_password};
  END IF;
END
$$;

-- Ensure orchestration user role exists and has desired password
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = {orchestration_user_literal}) THEN
    CREATE ROLE {orchestration_user} LOGIN PASSWORD {orchestration_user_password};
  ELSE
    ALTER ROLE {orchestration_user} LOGIN PASSWORD {orchestration_user_password};
  END IF;
END
$$;

-- Ensure AUTH user role exists and has desired password
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = {auth_user_literal}) THEN
    CREATE ROLE {auth_user} LOGIN PASSWORD {auth_user_password};
  ELSE
    ALTER ROLE {auth_user} LOGIN PASSWORD {auth_user_password};
  END IF;
END
$$;

-- Hardening at DB level
REVOKE ALL ON DATABASE {database} FROM PUBLIC;
GRANT CONNECT ON DATABASE {database} TO {owner}, {api_user}, {auth_user}, {orchestration_user};

-- Bounce active sessions so new passwords take effect and revoked privileges apply
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = {database_literal}
  AND usename IN ({owner_literal}, {api_user_literal}, {auth_user_literal}, {orchestration_user_literal})
  AND pid <> pg_backend_pid();

-- Extensions install here as admin (postgis is not a trusted extension, so the
-- owner cannot create it); the schema dir's 00_extensions.sql no-ops over them.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS "postgis" WITH SCHEMA public;

----------------------------------------------------------------------
-- Ensure ownership
----------------------------------------------------------------------

-- database → owner: the owner must own the database to create schemas
-- (both the schema dir's CREATE SCHEMA and any future one the migrator plans)
ALTER DATABASE {database} OWNER TO {owner};

-- public schema → owner
ALTER SCHEMA public OWNER TO {owner};
