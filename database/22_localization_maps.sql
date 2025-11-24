CREATE TABLE localization_maps (
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
    reconstruction_id uuid 
        NOT NULL
        REFERENCES reconstructions(id) 
        ON DELETE RESTRICT,
    position_x double precision
        NOT NULL,
    position_y double precision
        NOT NULL,
    position_z double precision
        NOT NULL,
    rotation_x double precision
        NOT NULL,
    rotation_y double precision
        NOT NULL,
    rotation_z double precision
        NOT NULL,
    rotation_w double precision
        NOT NULL,
    name text
        NULL,
    lighting integer
        NULL,
    active boolean
        NOT NULL
        DEFAULT true,
    color bigint
        NOT NULL,

    id uuid 
        NOT NULL 
        PRIMARY KEY 
        DEFAULT gen_random_uuid(),

    UNIQUE (reconstruction_id)
);

ALTER TABLE localization_maps ENABLE ROW LEVEL SECURITY;

CREATE POLICY localization_maps_rls_policy ON localization_maps
  FOR ALL
    USING (tenant_id = current_tenant())
    WITH CHECK (tenant_id = current_tenant());

CREATE TRIGGER localization_maps_touch_updated_at_trigger
  BEFORE UPDATE ON localization_maps
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();