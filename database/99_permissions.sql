-- ON ALL TABLES, never ALTER DEFAULT PRIVILEGES: pg-schema-diff ignores default
-- ACLs, so they would never leave its shadow database. The 99_ prefix sorts after
-- every table file, covering future tables. Roles come from database-manager,
-- which runs first.

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO placeframe_api_user;
GRANT SELECT, UPDATE ON ALL TABLES IN SCHEMA public TO placeframe_orchestration_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA auth TO placeframe_auth_user;
GRANT SELECT ON ALL TABLES IN SCHEMA auth TO placeframe_api_user;
