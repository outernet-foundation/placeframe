-- pg-schema-diff doesn't support domains types yet :-(
-- CREATE DOMAIN vector3 AS double precision[]
--   CHECK (array_length(VALUE, 1) = 3);

-- CREATE DOMAIN quaternion AS double precision[]
--   CHECK (
--     array_length(VALUE,1) = 4
--     AND abs((VALUE[1]^2 + VALUE[2]^2 + VALUE[3]^2 + VALUE[4]^2) - 1.0) < 1e-6
--   );
