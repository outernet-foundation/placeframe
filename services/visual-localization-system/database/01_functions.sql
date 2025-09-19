CREATE FUNCTION touch_updated_at()
  RETURNS TRIGGER
  LANGUAGE plpgsql
  AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END
$$;

CREATE FUNCTION current_tenant()
  RETURNS uuid
  LANGUAGE plpgsql
  STABLE
  AS $$
DECLARE
  tenant_id uuid;
BEGIN
  tenant_id := COALESCE(
    NULLIF(current_setting('app.tenant_id', TRUE), '')::uuid,
    (
      SELECT m.tenant_id
      FROM auth.memberships AS m
      WHERE
        m.user_id = NULLIF(current_setting('app.user_id', TRUE), '')::uuid
        AND m.is_personal LIMIT 1
    )
  );
  
  IF tenant_id IS NULL THEN
    RAISE EXCEPTION 'No current tenant set'
    USING ERRCODE = 'invalid_parameter_value';
  END IF;
    
  RETURN tenant_id;
END;
$$;

