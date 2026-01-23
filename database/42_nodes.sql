CREATE TYPE link_type AS ENUM (
    'none',
    'address',
    'annotation',
    'image_list'
);

CREATE TYPE label_type AS ENUM (
    'automatic',
    'text',
    'image'
);

CREATE TABLE nodes (
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
    active boolean
        NOT NULL
        DEFAULT true,
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
    label_type label_type
        NOT NULL,
    label text
        NOT NULL,
    link_type link_type
        NOT NULL,
    link text
        NOT NULL,
    label_scale double precision
        NOT NULL,
    label_width double precision
        NOT NULL,
    label_height double precision
        NOT NULL,
    parent_id uuid
        NULL
        REFERENCES groups(id)
        ON DELETE RESTRICT,
    layer_id uuid
        NULL
        REFERENCES layers(id)
        ON DELETE RESTRICT,

    id uuid 
        NOT NULL 
        PRIMARY KEY 
        DEFAULT gen_random_uuid()
);

ALTER TABLE nodes ENABLE ROW LEVEL SECURITY;

CREATE POLICY nodes_rls_policy ON nodes
  FOR ALL
    USING (tenant_id = current_tenant())
    WITH CHECK (tenant_id = current_tenant());

CREATE TRIGGER nodes_touch_updated_at_trigger
  BEFORE UPDATE ON nodes
  FOR EACH ROW
  EXECUTE FUNCTION touch_updated_at();