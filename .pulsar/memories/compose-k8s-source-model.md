---
updated: 2026-07-07
---

# Source-of-truth model for the Compose → Kubernetes deployment path

## Goal

The project is moving from local-development-only to a true SaaS deployment and must support Kubernetes. Working through the `my-transform` compose-bridge pipeline exposed that most of the system is built around a **Docker Compose mental model** — everything is a container on a flat network, brought up together — rather than a **Kubernetes mental model**, whose defining primitive is the *separation of a workload from its dependencies* (a workload declares what it needs; the platform decides how that need is satisfied — a container in dev, a managed service in prod). Decide the source-of-truth model that carries the system to SaaS without abandoning the properties the project requires.

Three hard constraints frame the decision:
1. **Must support Kubernetes** for the SaaS deployment.
2. **No drift** between different pieces of code (a core team principle).
3. **Docker Compose must remain usable by anyone** — this is a free, open-source project and Compose is what people know and contribute.

## State

- **Today:** `compose.yml` is the authored source of truth; `my-transform` + `uv run generate-k3s` generate the k8s Kustomize tree under `out/`. That pipeline now works end-to-end (validated on k3d: full boot chain, gateway → `api:8000` route, `{"status":"ok"}`).
- **The ceiling that motivates this initiative** is recorded as a constraint in `my-transform/SPEC.md` ("The transform inherits Compose's mental model"): a Compose-sourced transform structurally **cannot** express a platform-provisioned/external dependency. It always emits an in-cluster `postgres` Deployment/PVC; there is no way from `compose.yml` to say "in prod Postgres is a managed endpoint." Managed dependencies can only be handled downstream (a prod overlay swapping the `postgres` Service for an `ExternalName`) or by faking a resource model via `x-*` extensions.
- The init-job chain (`create-database → database-migrator → initialize-*`) is itself a Compose-era pattern, sequenced via generated init-container waits.

## Decisions

None committed. First-principles analysis (effort deliberately ignored), to be ratified or overturned:

- **Bridge convert is eliminated as the long-term model.** It is a function `compose → k8s`; its input is the Compose model, so it can never introduce a concept Compose lacks. It does not move the system toward the k8s mental model — it cements the Compose model as the permanent source and forces every k8s concept to be back-ported into `compose.yml` as `x-*` extensions (i.e. reimplementing a workload/dependency-separation model, badly, on top of Compose). It remains a working *bootstrap*, not a strategy.
- **Score is the leading candidate** because its core primitive *is* the missing separation: `containers` = what you run, `resources` = what you depend on, bound per-environment by provisioners. It is the only option that simultaneously satisfies all three constraints — one source (no drift) that generates both a runnable **compose** (OSS users) and production **k8s** (SaaS), with dependencies that **bind differently per environment** (container Postgres in dev, managed in prod — the ceiling above, solved by design). Platform-agnosticism is a genuine asset for a project meant to be self-hosted on heterogeneous infra.
- **Native Kubernetes (Kustomize/Helm + operators + external-secrets), with a separately-curated dev docker-compose, is the runner-up.** Maximum k8s fidelity, but it gives up single-source-generates-compose and platform portability, and "no drift" would have to be reinterpreted as binding the *contract* (images, env/secret names, declared resource needs) rather than the topology.
- **Bias check (recorded honestly):** the initial recommendation leaned against Score. On reflection that leaned on recency/sunk-cost (we had just built the bridge), asymmetric scrutiny (made Score prove weaknesses while giving the bridge a pass), and a reflexive `ExternalName` rebuttal to the managed-Postgres point instead of conceding it is Score's home turf. The de-biased read is that Score is the architecturally more correct target; the bridge's apparent advantage was mostly "it's what already exists."

## Open questions

Two hinges decide Score vs native-k8s; only the team can answer them:

- **Will managed/external dependencies be pervasive** in the SaaS (managed DB *and* cache, queue, object storage)? If yes, the bridge/overlay approach is per-dependency surgery and Score's resource model clearly earns its cost. If it is only Postgres, an `ExternalName` overlay is a contained fix.
- **Can Compose become a *generated* artifact** (produced by `score-compose`) rather than the hand-authored source? If yes, Score's biggest downside for this project evaporates. If Compose must stay the thing people author and contribute, that weighs against Score.

Secondary, real, not decisive:
- **Jobs / ordering:** Score has no Job/one-shot/CronJob and no `depends_on` — verified against the spec and score-k8s (which emit only Deployments/StatefulSets). The init-job chain would be authored as passthrough manifests in a provisioner, or the pattern itself rethought (managed-DB provisioning via IaC, migrations as a release-step Job). Score degrades gracefully to raw manifests where its model runs out.
- **Maturity:** Score is a CNCF *sandbox* project (accepted 2024) — younger than Kustomize/Helm.

## Key files

- `my-transform/SPEC.md` — the "transform inherits Compose's mental model" constraint that this initiative exists to resolve.
- `my-transform/` — the compose-bridge templates (base + overlays) that would be retired if the source model changes.
- `packages/python/placeframe-stack/src/placeframe_stack/generate_k3s.py` — the current generator/driver.
- `compose.yml` — today's source of truth; the `secrets:`/`volumes:` blocks and the `x-wait-images`/`expose` conventions show how much k8s intent is already being smuggled into Compose.
- `out/` — the generated Kustomize tree (base + `desktop` overlay); a `prod` overlay is where managed-dependency binding would live if the bridge model is kept.

## Pending threads

- **Proof-of-concept:** convert `api` + `lease-server` + `postgres` to Score workloads with `db`/`secret`/`volume` resources, run `score-k8s generate` and `score-compose generate`, and compare the output to the hand-built `out/`. This concretely tests the Jobs gap and the managed-Postgres win before committing.
- **Answer the two hinges** (pervasive managed deps? generated-compose acceptable?) — they select Score vs native-k8s.
- On close-out, fold the chosen direction back into `my-transform/SPEC.md` (or its successor) and delete this memory per the spec-style-guide lifecycle.
