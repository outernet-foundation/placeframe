CREATE TYPE membership_role AS ENUM(
  'owner',
  'admin',
  'member'
);

CREATE TABLE auth.memberships(
  user_id uuid 
    NOT NULL 
    REFERENCES auth.users(id) 
    ON DELETE CASCADE,
  tenant_id uuid 
    NOT NULL 
    REFERENCES auth.tenants(id) 
    ON DELETE CASCADE,
  role membership_role 
    NOT NULL 
    DEFAULT 'member',
  is_personal boolean 
    NOT NULL 
    DEFAULT FALSE,
  created_at timestamptz 
    NOT NULL 
    DEFAULT now(),
  updated_at timestamptz 
    NOT NULL 
    DEFAULT now(),

  PRIMARY KEY (user_id, tenant_id)
);

CREATE TRIGGER memberships_touch_updated_at
  BEFORE UPDATE ON auth.memberships
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
  
-- Exactly one personal membership per user
CREATE UNIQUE INDEX user_personal_tenant ON auth.memberships(user_id)
WHERE is_personal = TRUE;
