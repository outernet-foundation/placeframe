-- params:
-- {owner}                -- identifier
-- {api_user}          -- identifier
-- {orchestration_user} -- identifier
-- {auth_user}         -- identifier

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;

----------------------------------------------------------------------
-- Ensure schema owners
----------------------------------------------------------------------

-- public schema → owner
ALTER SCHEMA public OWNER TO {owner};

-- create auth schema and set owner
CREATE SCHEMA IF NOT EXISTS {auth_schema} AUTHORIZATION {owner};

----------------------------------------------------------------------
-- Schema-level usage & hardening
----------------------------------------------------------------------

-- Nobody gets implicit anything
REVOKE ALL ON SCHEMA public     FROM PUBLIC;
REVOKE ALL ON SCHEMA {auth_schema} FROM PUBLIC;

-- Who may list objects in the schemas
GRANT USAGE ON SCHEMA public        TO {api_user}, {orchestration_user};
GRANT USAGE ON SCHEMA {auth_schema} TO {auth_user}, {api_user};

----------------------------------------------------------------------
-- Existing objects in public: API user full R/W
----------------------------------------------------------------------

REVOKE ALL ON ALL TABLES    IN SCHEMA public FROM PUBLIC;
GRANT  SELECT, INSERT, UPDATE, DELETE ON ALL TABLES    IN SCHEMA public TO {api_user};
GRANT  SELECT, UPDATE          ON ALL TABLES    IN SCHEMA public TO {orchestration_user};

REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;
GRANT  USAGE, SELECT                 ON ALL SEQUENCES IN SCHEMA public TO {api_user};

REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC;
GRANT  EXECUTE                       ON ALL FUNCTIONS IN SCHEMA public TO {api_user};

----------------------------------------------------------------------
-- Existing objects in auth:
--   AUTH user full R/W, API user read-only
----------------------------------------------------------------------

REVOKE ALL ON ALL TABLES    IN SCHEMA {auth_schema} FROM PUBLIC;
GRANT  SELECT, INSERT, UPDATE, DELETE ON ALL TABLES    IN SCHEMA {auth_schema} TO {auth_user};
GRANT  SELECT                         ON ALL TABLES    IN SCHEMA {auth_schema} TO {api_user};

REVOKE ALL ON ALL SEQUENCES IN SCHEMA {auth_schema} FROM PUBLIC;
GRANT  USAGE, SELECT                 ON ALL SEQUENCES IN SCHEMA {auth_schema} TO {auth_user};
GRANT  SELECT                        ON ALL SEQUENCES IN SCHEMA {auth_schema} TO {api_user};

REVOKE ALL ON ALL FUNCTIONS IN SCHEMA {auth_schema} FROM PUBLIC;
GRANT  EXECUTE                       ON ALL FUNCTIONS IN SCHEMA {auth_schema} TO {auth_user};
-- (only grant EXECUTE to {api_user} if a specific function truly needs it)

----------------------------------------------------------------------
-- Defaults for *future* objects (set by owner)
----------------------------------------------------------------------

SET ROLE {owner};

-- public → defaults for API user
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL                              ON TABLES    FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT  SELECT,INSERT,UPDATE,DELETE     ON TABLES    TO {api_user};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT  SELECT,UPDATE                     ON TABLES    TO {orchestration_user};

ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL                              ON SEQUENCES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT  USAGE,SELECT                     ON SEQUENCES TO {api_user};

ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE EXECUTE                          ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT  EXECUTE                          ON FUNCTIONS TO {api_user};

-- auth → defaults for AUTH user full; API user read-only
ALTER DEFAULT PRIVILEGES IN SCHEMA {auth_schema} REVOKE ALL                       ON TABLES    FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA {auth_schema} GRANT  SELECT,INSERT,UPDATE,DELETE ON TABLES    TO {auth_user};
ALTER DEFAULT PRIVILEGES IN SCHEMA {auth_schema} GRANT  SELECT                    ON TABLES    TO {api_user};

ALTER DEFAULT PRIVILEGES IN SCHEMA {auth_schema} REVOKE ALL                       ON SEQUENCES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA {auth_schema} GRANT  USAGE,SELECT              ON SEQUENCES TO {auth_user};
ALTER DEFAULT PRIVILEGES IN SCHEMA {auth_schema} GRANT  SELECT                    ON SEQUENCES TO {api_user};

ALTER DEFAULT PRIVILEGES IN SCHEMA {auth_schema} REVOKE EXECUTE                   ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA {auth_schema} GRANT  EXECUTE                   ON FUNCTIONS TO {auth_user};

RESET ROLE;
