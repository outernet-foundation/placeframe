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
    ALTER ROLE {api_user} WITH LOGIN PASSWORD {api_user_password};
  END IF;
END
$$;

-- Ensure orchestration user role exists and has desired password
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = {orchestration_user_literal}) THEN
    CREATE ROLE {orchestration_user} LOGIN PASSWORD {orchestration_user_password};
  ELSE
    ALTER ROLE {orchestration_user} WITH LOGIN PASSWORD {orchestration_user_password};
  END IF;
END
$$;

-- Ensure AUTH user role exists and has desired password
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = {auth_user_literal}) THEN
    CREATE ROLE {auth_user} LOGIN PASSWORD {auth_user_password};
  ELSE
    ALTER ROLE {auth_user} WITH LOGIN PASSWORD {auth_user_password};
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
