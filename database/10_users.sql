CREATE TABLE auth.users(
  created_at timestamptz NOT NULL 
    DEFAULT now(),

  id uuid 
    PRIMARY KEY
);

-- Ensure that each user has an associated personal tenant and is owner of that tenant
CREATE FUNCTION auth.create_personal_tenant()
  RETURNS trigger 
  LANGUAGE plpgsql
  AS $$
BEGIN
  WITH new_t AS (
    INSERT INTO auth.tenants DEFAULT VALUES
    RETURNING id
  )
  INSERT INTO auth.memberships (tenant_id, user_id, role, is_personal)
  SELECT id, NEW.id, 'owner', true
  FROM new_t;

  RETURN NEW;
END;
$$;

CREATE TRIGGER after_insert_create_personal_tenant
AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION auth.create_personal_tenant();
