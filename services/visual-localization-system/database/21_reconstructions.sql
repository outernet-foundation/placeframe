CREATE TYPE orchestration_status AS ENUM (
  'queued',
  'pending',
  'running',
  'succeeded',
  'cancelled',
  'failed'
);

CREATE TABLE reconstructions(
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
  capture_session_id uuid 
    NOT NULL 
    REFERENCES capture_sessions(id) 
    ON DELETE RESTRICT,
  orchestration_status orchestration_status
    NOT NULL 
    DEFAULT 'queued',

  id uuid 
    PRIMARY KEY 
    DEFAULT uuid_generate_v4()
);

ALTER TABLE reconstructions ENABLE ROW LEVEL SECURITY;

CREATE POLICY reconstructions_rls_policy ON reconstructions
  FOR ALL
    USING (tenant_id = current_tenant())
    WITH CHECK (tenant_id = current_tenant());

-- Allow orchestrator role to bypass RLS for all operations
CREATE POLICY reconstructions_orchestrator_rls_policy ON reconstructions
  FOR ALL
    TO plerion_orchestration_user
    USING (true)
    WITH CHECK (true);

CREATE TRIGGER reconstructions_touch_updated_at_trigger
  BEFORE UPDATE ON reconstructions
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

