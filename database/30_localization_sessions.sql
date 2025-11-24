CREATE TABLE localization_sessions (
    tenant_id uuid 
        NOT NULL 
        REFERENCES auth.tenants(id) 
        ON DELETE RESTRICT 
        DEFAULT current_tenant(),
    created_at TIMESTAMPTZ 
        NOT NULL 
        DEFAULT NOW(),
    container_id text 
        NOT NULL,
    container_url text 
        NOT NULL,

    id UUID PRIMARY KEY DEFAULT gen_random_uuid()
);