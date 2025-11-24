CREATE TYPE device_type AS ENUM(
  'ARFoundation',
  'Zed'
);

CREATE TABLE capture_sessions(
  tenant_id uuid 
    NOT NULL 
    REFERENCES auth.tenants(id) 
    ON DELETE RESTRICT 
    DEFAULT current_tenant(),
  created_at timestamptz 
    NOT NULL 
    DEFAULT now(),
  updated_at timestamptz 
    NOT NULL 
    DEFAULT now(),
  name text 
    NOT NULL,
  device_type device_type 
    NOT NULL,

  id uuid 
    PRIMARY KEY 
    DEFAULT uuid_generate_v4()
);

ALTER TABLE capture_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY capture_sessions_rls_policy ON capture_sessions
  FOR ALL
    USING (tenant_id = current_tenant())
    WITH CHECK (tenant_id = current_tenant());

CREATE TRIGGER capture_sessions_touch_updated_at_trigger
  BEFORE UPDATE ON capture_sessions
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

