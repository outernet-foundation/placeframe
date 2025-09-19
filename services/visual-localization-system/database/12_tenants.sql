CREATE TABLE auth.tenants(
  created_at timestamptz 
    NOT NULL 
    DEFAULT now(),

  id uuid 
    PRIMARY KEY 
    DEFAULT gen_random_uuid()
);
