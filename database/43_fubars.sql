CREATE TABLE fubars (
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
    label text
        NOT NULL,
    severity integer
        NOT NULL
        DEFAULT 0,
    resolved boolean
        NOT NULL
        DEFAULT false,
    notes text
        NULL,

    id uuid
        NOT NULL
        PRIMARY KEY
        DEFAULT gen_random_uuid()
);

ALTER TABLE fubars ENABLE ROW LEVEL SECURITY;

CREATE POLICY fubars_rls_policy ON fubars
  FOR ALL
    USING (tenant_id = current_tenant())
    WITH CHECK (tenant_id = current_tenant());

-- Allow orchestrator role to bypass RLS for all operations
CREATE POLICY fubars_orchestrator_rls_policy ON fubars
  FOR ALL
    TO placeframe_orchestration_user
    USING (true)
    WITH CHECK (true);

CREATE TRIGGER fubars_touch_updated_at_trigger
  BEFORE UPDATE ON fubars
  FOR EACH ROW
  EXECUTE FUNCTION touch_updated_at();
