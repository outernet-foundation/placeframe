CREATE TABLE localization_evaluations (
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
  frame_timestamp bigint
    NOT NULL,
  retrieval_top_k integer
    NOT NULL,
  ransac_threshold double precision
    NOT NULL,
  pipeline_version text
    NOT NULL,

  succeeded boolean
    NOT NULL,

  num_correspondences integer
    NOT NULL,
  num_matches integer
    NOT NULL,
  num_inliers integer
    NOT NULL,
  inlier_ratio double precision
    NOT NULL,
  inlier_coverage double precision
    NOT NULL,
  reproj_error_median double precision
    NOT NULL,
  query_image_diagonal_px double precision
    NOT NULL,

  pnp_covariance double precision[]
    NULL,
  se3_residual double precision[]
    NULL,
  err_t_m double precision
    NULL,
  err_r_deg double precision
    NULL,

  id uuid
    PRIMARY KEY
    DEFAULT uuid_generate_v4(),

  UNIQUE (reconstruction_id, frame_timestamp, retrieval_top_k, ransac_threshold, pipeline_version),

  CONSTRAINT labels_present_iff_succeeded CHECK (
    succeeded = (err_t_m IS NOT NULL)
    AND succeeded = (err_r_deg IS NOT NULL)
    AND succeeded = (se3_residual IS NOT NULL)
    AND succeeded = (pnp_covariance IS NOT NULL)
  ),
  CONSTRAINT se3_residual_length CHECK (
    se3_residual IS NULL OR array_length(se3_residual, 1) = 6
  ),
  CONSTRAINT pnp_covariance_shape CHECK (
    pnp_covariance IS NULL OR (array_length(pnp_covariance, 1) = 6 AND array_length(pnp_covariance, 2) = 6)
  )
);

ALTER TABLE localization_evaluations ENABLE ROW LEVEL SECURITY;

CREATE POLICY localization_evaluations_rls_policy ON localization_evaluations
  FOR ALL
    USING (tenant_id = current_tenant())
    WITH CHECK (tenant_id = current_tenant());

CREATE TRIGGER localization_evaluations_touch_updated_at_trigger
  BEFORE UPDATE ON localization_evaluations
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
