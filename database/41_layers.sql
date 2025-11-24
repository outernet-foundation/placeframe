CREATE TABLE layers (
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

    id uuid
        PRIMARY KEY 
        DEFAULT gen_random_uuid()
);

ALTER TABLE layers ENABLE ROW LEVEL SECURITY;

CREATE POLICY layers_rls_policy ON layers
  FOR ALL
    USING (tenant_id = current_tenant())
    WITH CHECK (tenant_id = current_tenant());

CREATE TRIGGER layers_touch_updated_at_trigger
  BEFORE UPDATE ON layers
  FOR EACH ROW
  EXECUTE FUNCTION touch_updated_at();