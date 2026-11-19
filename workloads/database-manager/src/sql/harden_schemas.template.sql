-- params:
-- identifiers: {api_user}, {orchestration_user}, {auth_user}, {auth_schema}
--
-- Post-bootstrap hardening: schema usage and function EXECUTE are invisible to
-- pg-schema-diff (it tracks tables only), so they cannot live in the schema
-- dir. Runs after the bootstrap, which is what creates the schemas.

-- Nobody gets implicit anything
REVOKE ALL ON SCHEMA public         FROM PUBLIC;
REVOKE ALL ON SCHEMA {auth_schema}  FROM PUBLIC;

-- Who may list objects in the schemas
GRANT USAGE ON SCHEMA public        TO {api_user}, {orchestration_user};
GRANT USAGE ON SCHEMA {auth_schema} TO {auth_user}, {api_user};

----------------------------------------------------------------------
-- Function-EXECUTE hardening
----------------------------------------------------------------------

REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC;
GRANT  EXECUTE                     ON ALL FUNCTIONS IN SCHEMA public TO {api_user};

REVOKE ALL ON ALL FUNCTIONS IN SCHEMA {auth_schema} FROM PUBLIC;
GRANT  EXECUTE                     ON ALL FUNCTIONS IN SCHEMA {auth_schema} TO {auth_user};

-- (only grant EXECUTE to {api_user} on auth functions if one truly needs it)
