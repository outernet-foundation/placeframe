CREATE TABLE groups (
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
    parent_id uuid
        REFERENCES groups(id)
        ON DELETE RESTRICT,

    id uuid 
        PRIMARY KEY 
        DEFAULT gen_random_uuid()
);

ALTER TABLE groups ENABLE ROW LEVEL SECURITY;

CREATE POLICY groups_rls_policy ON groups
  FOR ALL
    USING (tenant_id = current_tenant())
    WITH CHECK (tenant_id = current_tenant());

CREATE TRIGGER groups_touch_updated_at_trigger
  BEFORE UPDATE ON groups
  FOR EACH ROW
  EXECUTE FUNCTION touch_updated_at();