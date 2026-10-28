# TODO — k8s deployment handoff

Follow-ups required when deploying from the generated manifests. Audience: the SaaS
engineer owning the Pulumi/infra layer and the Argo application. The repo generates both
renderings from one source (`stack/score/`): local Docker compose and
`stack/generated/k8s/manifests.yaml` for the cluster. The manifests carry no secret
values — every credential and environment value is looked up at runtime from the
`placeframe-secrets` Secret, which this repo never creates. The generated mint list
`stack/generated/secrets.txt` is the authoritative contract for the keys that Secret
must contain (regenerate with `uv run generate-score --target k8s` from the repo root).

## Required before the next apply

1. **Mint `POSTGRES_ADMIN_USER` into `placeframe-secrets`.** New as of the bucket-contract
   commit: the postgres container and the create Job now read the superuser name from the
   Secret via `secretKeyRef` instead of baking the literal `postgres`. Value: `postgres` —
   the superuser name is fixed at first `initdb`, and existing data volumes were
   initialized with it. A missing key fails both pods with `CreateContainerConfigError`.
2. **Mint the three `KEYCLOAK_*` lifespan keys** (`KEYCLOAK_ACCESS_TOKEN_LIFESPAN`,
   `KEYCLOAK_SSO_SESSION_IDLE_TIMEOUT`, `KEYCLOAK_SSO_SESSION_MAX_LIFESPAN`; dev values
   `3600`/`2592000`/`2592000`) — the realm configurator Job reads them via `secretKeyRef`.
3. **Prepare the cluster for the keycloak-operator manifests.** The next k8s artifact
   (after the mirror job copies the operator chart + 26.8.1 images) carries cluster-scoped
   CRDs and ClusterRole/Bindings plus the operator Deployment; keycloak itself becomes an
   operator-managed StatefulSet behind Service `keycloak-service` (an ExternalName alias
   keeps `keycloak` resolving for the gateway snippets). H2-ephemeral storage — no data
   PVC, the old fsGroup concern is gone. Point the minted `AUTH_JWKS_URL` at
   `http://keycloak-service:8080/realms/placeframe-dev/protocol/openid-connect/certs`.
4. **Conform the whole Secret to the current mint list** (the deployed key set predates
   the SeaweedFS migration): drop `AUTH_MODE`, `AUTH_URL`/`AUTH_TOKEN_URL`,
   `MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY`; ensure every key in `secrets.txt` exists
   (`S3_*`, `KEYCLOAK_*`, `GRAFANA_ADMIN_*`, `DEPLOYMENT_ENVIRONMENT`, the `DATABASE_*`
   and `AUTH_*` blocks, `PUBLIC_URL`).
5. **Reconcile the Argo Application source path.** Last seen pointing at `score/deploy`
   on placeframe `main` — a path that exists nowhere. Point it at
   `stack/generated/k8s/manifests.yaml` on the branch that carries it, at merge.
6. **Drop MinIO from the infra layer.** The manifests run SeaweedFS (StatefulSet +
   `seaweedfs-audit` relay + bucket Job) with unprefixed bucket names
   `captures`/`reconstructions`/`loki`; any Pulumi-side MinIO resources are dead.
7. **Rename the Pulumi config keys feeding `pf-secrets`** (`placeframe:minioSecretKey` →
   `s3*` spellings) so the camelCase→SNAKE mapping in `secrets_exec.py` yields the `S3_*`
   env names the stack reads.

## When the artifact carries the reconstructor (Slice D regen, post-mirror)

8. **Delete the Pulumi reconstructor workload path — keep `install_keda`.** In
   `program/reconstructor.py`: `deploy_reconstructor` goes (the stale Deployment —
   `MINIO_*` envs, `dev-captures` bucket, tree-pinned image — plus the
   `keda-reconstructor-pg` connection Secret and the Pulumi-built
   TriggerAuthentication/ScaledObject), along with `reconstructor-probe.yaml`,
   `EnableLocalNode.py`, and the `cluster.py` call site. `install_keda` is the KEDA
   operator's permanent home: the operator is cluster tier — a cluster-wide reconciler,
   peer of the NVIDIA device plugin — and the artifact now carries only the
   ScaledObject/TriggerAuthentication CRs that assume it (industry line: app manifests
   declare CRs; the platform installs the reconciler). Once the artifact's Argo sync
   (prune + selfHeal) carries the `reconstructor` Deployment, Pulumi ownership of the
   same name in the same namespace is a standing fight, not a migration window.
9. **Add `ignoreDifferences` for the reconstructor Deployment `/spec/replicas` to the
    Argo Application spec** (`program/argocd.py`). KEDA owns the replica count once the
    artifact's ScaledObject is live; without the ignore, every Argo sync reverts KEDA's
    scaling. No new Secret keys: the artifact's TriggerAuthentication reads
    `DATABASE_ORCHESTRATION_USER_PASSWORD` (already on the mint list) via
    `secretTargetRef`; the Pulumi-built `keda-reconstructor-pg` connection Secret dies
    with item 8. Keep the operator at 2.20.2 (the artifact's CRs are written against
    it). The operator no longer rides the artifact, so the Argo target needs no KEDA
    CRD/RBAC permissions — the cluster-scoped-permissions caveat now applies only to
    the keycloak-operator chart (item 3).

## Notes

- The Job annotations (`argocd.argoproj.io/hook-weight`) only take effect under Argo CD;
  a bare `kubectl apply` path (score-up wrappers) still relies on job retry-idempotency,
  which is the designed behavior.
- The mint list grew with the realm-configurator slice (the three `KEYCLOAK_*` lifespan
  keys), and again with `SEED_TEST_USERS` (optional — mint an empty string to disable
  test-user seeding) — resync against `secrets.txt` at each pull rather than tracking
  keys by hand.
- `stack/score/k8s/postgres.yaml` changed shape recently (readiness probe, admin-user via
  Secret, hook weights) — expect rebase conflicts in the deploy branches that register
  provisioners (`placeframe-deploy`, `cnpg-dev`).
- Local k3d bring-up recipe (hand-minting the Secret, storage class, image preloading)
  lives in `stack/AGENTS.md` under "Deploy: Kubernetes".
