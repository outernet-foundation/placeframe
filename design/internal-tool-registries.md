# Internal tools on registries

## Scope

The tools thread of the polyrepo initiative ([index](polyrepo.md)), running third in the resequenced execution order — after publishing (its feeds and machinery are the prerequisite) and **before** repo boundaries, so the extracted repos are born registry-pinned rather than inheriting git refs that get converted again later. The CaptureTool manifest repoint to npmjs exact pins — the Unity-side registry-consumption proof — is this thread's closing bridge step into the boundaries thread. Siblings: [prepo](polyrepo-workbench.md), [publishing](package-publishing-redesign.md), [repo boundaries](repo-extraction.md).

## Problem

Internal tool packages are consumed as git refs pinned to commit SHAs. That works — SHAs are immutable and declarative — but carries standing costs:

- **`tool.uv.sources` is not transitive**: every consumer must redeclare each tool's siblings alongside it (placeframe declares bashrun beside stack-toolkit, unity-buildkit, openapi-client-codegen, release-kit; release-kit declares bashrun beside stack-toolkit, unity-buildkit; and so on down the graph). Registry dependencies would resolve transitively.
- **CI resolution cost**: git dependencies clone; registry wheels download faster and cache better.
- **Two consumption models**: application packages get registries, tools get git refs — two mental models, two update workflows, no uniform fresh-clone autonomy.

## Ground truth (census 2026-09-20; registry facts verified live the same day)

Git-ref'd internal dependency edges in `[tool.uv.sources]` across the workspace:

| Package | Consumers |
|---|---|
| bashrun | openapi-client-codegen, placeframe, prepo, release-kit, pulsar, quarto-render, rubidium-build, stack-toolkit, unity-buildkit (9) |
| logconf | placeframe, pulsar |
| stack-toolkit | placeframe, release-kit |
| unity-buildkit | placeframe, release-kit |
| openapi-client-codegen | placeframe |
| release-kit | placeframe |

19 edges, 11 consuming repos. Make-it-Sing additionally pins two fork identities (`placeframe-bash`, `placeframe-unity`) — whether those fold into this thread or stay forked is an open parameter. None of the six packages has a release flow today: versions loaf at 0.1.0, no release tags, no publish config.

Drift is already real: three bashrun revs are live across consumers (placeframe `0a9e9a46`, pulsar + rubidium-build `1a0add1e`, quarto-render `63419e0b`); prepo pins unity-buildkit at a fourth-era rev placeframe doesn't. CI exists only in bashrun, stack-toolkit, and openapi-client-codegen (`ci.yml`); logconf, unity-buildkit, and release-kit have no workflows at all.

Registry names (PyPI JSON API, anonymous): `bashrun`, `stack-toolkit`, `unity-buildkit`, `openapi-client-codegen`, `release-kit` unclaimed. **`logconf` is claimed** — an unrelated same-purpose package (Andreas Lutro, 0.2.1, "convenient python stdlib logging configuration", no extras).

**Live defect shipped by the dev channel**: `placeframe-common` `0.1.0.dev35547537192` (run `35547537192`) declares `Requires-Dist: logconf[otlp]` and imports `logconf` at module scope (`packages/python/common/src/placeframe_common/logging_config.py:5`); installing the wheel resolves the requirement to the *foreign* logconf with only a warning (verified in a scratch venv: foreign `logconf==0.2.1` installs, exit 0) — silent third-party substitution, `ImportError` at first use. The artifact is immutable; the fix is an owned `logger-conf` on PyPI plus common's next publish; yanking the broken artifact is the containment.

Where placeframe declares the tools: root `pyproject.toml` `[tool.uv.sources]` (six entries, workspace-wide), `build/pyproject.toml` `[project.dependencies]` (bashrun, stack-toolkit, unity-buildkit, openapi-client-codegen, release-kit — release-kit carrying a DEP002 deptry ignore and imported nowhere: invocation-only), `scripts/pyproject.toml` (bashrun, stack-toolkit — genuinely imported), and `packages/python/common/pyproject.toml` (`logconf[otlp]`, the wheel-shipped edge). release-kit mechanics that shape the design: Python version sentinel `0.0.0.dev0` patched ephemerally at publish, first release `0.1.0` then patch-auto from the tag ledger, `PyPIFeed` = `uv build` + `uv publish` under OIDC trusted publishing with `--check-url` idempotency; per-package `dependency_pins` for PyPI are refused upstream of a concrete in-repo consumer — irrelevant here, each tool is its own release unit and authored ranges suffice.

## Couplings

- **Gated on thread 2 only**: the feeds, release-kit, and the dev channel must exist before tools can publish to them — landed (dev channel live, dispatch-proven). The original extraction-first ordering was reversed: converting before extraction means the extracted capture repo inherits registry pins as-is, one conversion instead of two.
- **Deferral context**: placeframe's stable cutover (publishing items 11-13) is deferred behind this thread and boundaries — the tool repos publish from their own mains, so their release flows do not wait for placeframe's `main` to move.
- **Standing hold until item 1 completes**: no further `placeframe-common` publishes (dev dispatch or stable) — each would ship the broken `logconf[otlp]` metadata again until the consumer-half repoint lands (logger-conf on PyPI alone is not enough; common's requirement must say `logger-conf[otlp]`). The hold lifts when the repoint is committed; yanking the broken dev artifact is the containment step.
- **Reopens a discarded alternative of the publishing design**: that doc rejected dev-channel discovery tooling ("exact-pin-by-hand suffices — CI prints the published version") explicitly *because* it was scoped to a one-or-two-consumer workflow. Re-decided below on the many-consumer merits: the rejection survives in modified form — ranges + lockfiles make discovery tooling redundant for the stable tier, and prerelease consumption stays exact-pin-by-hand.

## Design

### Feed: public PyPI, nothing else

The tool tier is Python consumed via uv; npm/nuget feeds are irrelevant to it. A private index is a standing service (rejected org-wide); GitHub Packages serves Python over an authenticated API foreign to plain `pip`/`uv` consumers. Public PyPI is the working assumption made a ruling.

### Names: bare where verified free; logconf becomes logger-conf

The five names are claimed as-is (`bashrun`, `stack-toolkit`, `unity-buildkit`, `openapi-client-codegen`, `release-kit`) — all distinctive coinages, not generic words; the publishing thread's "no generic top-level names" ruling targeted generic *module* names (`common`, `core`), which these are not, and import-name == distribution-name holds for every one. Three are renames from the census spellings, all by operator ruling on 2026-09-20 before any first publish — no artifact carries any old name: `stack-toolkit` was `stack-lifecycle`, `openapi-client-codegen` was `openapi-clientgen` (console script renamed with it), and `release-kit` was `pubpkg`. Ground-truth correction the renames exposed: **a 404 on the PyPI JSON API proves a name unclaimed, not registrable** — the registrar rejects names merely *similar* to existing ones, and that similarity check is invisible until the registration attempt. Every name here is therefore provisional until its pending publisher accepts; long distinctive compounds are the defensive choice.

`logconf` renames at **both** levels to **`logger-conf`** / `logger_conf`, and the GitHub repo renames with it (`logconf` → `logger-conf`). Operator ruling, 2026-09-20: `logger-conf` chosen from the verified-free vicinity (`logging-conf`, `logger-conf`, `log-conf`, `logging-setup` free; `log-config`, `logging-config`, `logger-config`, `logger-setup` taken) — an initial same-day ruling of `log-conf` was superseded before anything published, so no artifact ever carried it. A distribution-only rename is refused: it breaks import==dist and plants a deptry `package_module_name_map` wart in every future consumer — the exact wart the publishing thread paid a rename to avoid. The import surface is exactly two sites outside the repo (placeframe-common's `logging_config.py`, pulsar's `sandbox/__init__.py`); PEP 503 normalization keeps `logger-conf` and the foreign `logconf` distinct projects.

### Pins: ranges in manifests, exacts in lockfiles

Consumers declare floors (`bashrun>=0.1.0`) in `[project.dependencies]`; the committed `uv.lock`/`pylock.toml` carry the exacts. Upgrades are the consumer's prerogative via `uv lock --upgrade-package <name>` — non-upgrade relocks preserve locked versions, so patch-auto tool releases enter a repo only when deliberately pulled (drift becomes chosen, not ambient). API-breaking tool changes ship with a manually bumped version and forward-fix culture; locks protect at-rest reproducibility. Prerelease consumption stays exact-pin-by-hand — the publishing thread's interface governs `-dev` versions, which ranges must never float onto.

Bump tooling stays dead in all forms: prepo's `bump` deletion stands (its dev-channel rationale never shipped), and a Renovate-class bot is refused — `uv lock --upgrade-package` is native, needs no network surface in consumer tooling, and generates no PR noise across eleven repos. Revisit only if tool release cadence makes hand-upgrades a measurable tax.

### Release flows: publish rides CI on main

Each tool repo gets a `publish-config.json` (one `pypi` package entry) and a publish job in its `ci.yml`, `needs: [check]`, gated on `push` to `main` — the operator's push is the deliberate release act; no release PRs, no `dev`/`main` split, no GitHub environment (one PyPI project per repo keeps the trusted-publisher tuple unique without one). Auth: `GITHUB_TOKEN` with `contents: write` (tag ledger) + `id-token: write` (PyPI OIDC) — no App-token machinery, which placeframe's release workflow needs only for its release-PR merge shape. Version discipline is release-kit's invariant set: committed `0.0.0.dev0` sentinel, first release `0.1.0`, patch-auto thereafter, `--check-url` idempotency for retries. Operator one-time step per repo: configure the PyPI pending publisher naming `ci.yml` (no environment) before the first run.

No dev channel for tool repos: six dispatch workflows and prerelease bookkeeping for a tier that changes rarely, while the pre-release test vehicle already exists — a consumer pins the tool repo at a git ref in a scratch branch (registry conversion removes nothing; git stays available), tests, and the deliberate release follows.

### Bootstrap and circularity: uvx-isolated release-kit, leaves-first ordering

release-kit is a project dependency of nothing after this thread. Four of the five converting tools sit inside release-kit's own dependency graph — a project-dep release-kit in their repos is a resolver cycle and a root-version conflict (the repo's `0.0.0.dev0` sentinel cannot satisfy release-kit's `bashrun>=0.1.0`). The cycle-proof boundary is uvx: every tool publish job invokes `uvx --from <source> publish-packages --config publish-config.json`, an ephemeral env disjoint from the repo's venv. placeframe's release-kit edge dissolves the same way — it is invocation-only (imported nowhere; the DEP002 ignore in `build/pyproject.toml` is the receipt) — so its release workflow's three release-kit commands convert to the same uvx form and the dependency entry dies.

Release order, leaves first:

1. **logger-conf and bashrun** (leaves; logger-conf first — the common-publish hold). Their workflows bootstrap with `uvx --from git+https://github.com/outernet-foundation/release-kit@<rev>`.
2. **stack-toolkit, unity-buildkit, openapi-client-codegen** — any order; each converts its own bashrun pin to a registry range in the same change.
3. **release-kit last**: converts its three dep pins to ranges (`[tool.uv.sources]` block deleted) and self-publishes from its own checkout (`uv run --no-sync publish-packages` — the repo *is* release-kit, no self-reference), so every dependency of its wheel exists on PyPI at publish moment. Never publish an uninstallable artifact: this ordering is why release-kit cannot go first despite everything else needing it.

After release-kit 0.1.0 exists, every workflow's uvx source converts to `release-kit==0.1.0` — an exact registry pin in reviewed YAML. Upgrading is a one-line edit in the consumer's own workflow, no relock, no venv, no cascade: release-kit's consumers move on their own initiative, and a stale release-kit pin blocks nothing.

### Conversion scope: all six tools; prepo never; forks stay

All six convert — the census's "a single-consumer tool may never be worth a release flow" calculus died on both ends: the logconf defect makes non-conversion unfixable, and release-kit collapsed the per-tool cost to a config file plus a workflow job. prepo never publishes (nothing depends on it; it is a per-machine workbench tool) but converts its two pins as a consumer. Make-it-Sing's `placeframe-bash`/`placeframe-unity` are subdirectory packages of the placeframe repo itself pinned at placeframe revs — a different animal from the tool tier, left forked (open parameter, non-blocking).

### Consumer repoints

placeframe: five root `[tool.uv.sources]` entries deleted (bashrun, stack-toolkit, unity-buildkit, openapi-client-codegen, release-kit; the logconf entry dies with the rename), `build`/`scripts` member deps flip to registry ranges, relock (`uv sync --all-packages`, `lock-python`, preflight). prepo, pulsar, quarto-render, rubidium-build: sources entries deleted, ranges in, pulsar additionally carries the `logger_conf` import rename. Every consumer collapses its drifted rev onto the published 0.1.0.

### The bridge: CaptureTool repoints to npmjs exact pins

CaptureTool's manifest swaps five `file:` refs for exact dev-channel pins from run `35547537192` (`org.outernet.placeframe.apiclient` `0.1.8-dev.35547537192`; `org.outernet.placeframe` and `-.arfoundation` `1.0.6-dev.35547537192`; `org.outernet.placeframe.auth` and `org.outernet.logging` `0.1.0-dev.35547537192`) — the Unity-side registry-consumption proof, exercising a real project rather than a scratch one. `org.outernet.placeframe.zedcaptureclient` stays `file:` until the capture repo's first publish (thread 4); `lock-unity` regenerates the lock; `compile-unity` is the sanity gate. MapRegistrationTool keeps its `file:` refs — the intra-repo consumption path stays exercised where it remains intra-repo.

## Change set

Each item flips to `[x]` when committed and verified; a fresh session resumes at the first unchecked item.

1. [x] **logger-conf**: in the logger-conf repo (renamed from `logconf`) — rename distribution + package + imports (`logconf` → `logger-conf` / `logger_conf`), version sentinel `0.0.0.dev0`, `publish-config.json`, author `ci.yml` (check + main-gated publish job, uvx `--from git+…release-kit@<rev>` bootstrap). Operator: PyPI pending publisher for `logger-conf`. Publish 0.1.0. Then the consumers: placeframe-common's dependency → `logger-conf[otlp]` and `logging_config.py` import rewrite, root sources entry deleted; pulsar repoints + `sandbox/__init__.py` import rename. Operator: yank `placeframe-common` `0.1.0.dev35547537192`; the publish hold lifts. — Landed: repo at `2eda33f` (pushed), `logger-conf` 0.1.0 live on PyPI with correct metadata (verified via the JSON API); consumer repoints committed (`173f1752` placeframe — common's dep, import, root sources entry, relock + per-service pylocks, checks green; `6fb27cb` pulsar — scripts dep range, import, relock; 3 pre-existing tidy-commits test failures and one pre-existing format drift reproduce at HEAD without the diff — unrelated, reported). The publish hold has lifted. Yank still outstanding as operator containment.
2. [x] **bashrun**: sentinel flip, `publish-config.json`, publish job in the existing `ci.yml` (uvx git-ref bootstrap). Operator pending publisher. Publish 0.1.0. — Landed: repo at `2d01762` (pushed), `bashrun` 0.1.0 live on PyPI, zero-dep wheel verified.
3. [x] **stack-toolkit, unity-buildkit, openapi-client-codegen**: same shape per repo — unity-buildkit gets `ci.yml` authored; each converts its own bashrun dep to the registry range and drops its sources entry. Publish each 0.1.0. — Landed: all three live on PyPI at 0.1.0 with `bashrun>=0.1.0` flowing transitively (verified via the JSON API). Renames rode the same window: stack-toolkit from `stack-lifecycle` (main `d86adce`), openapi-client-codegen from `openapi-clientgen` (main `4dc2fea`, console script renamed with it); unity-buildkit at `67d70c6`.
4. [ ] **release-kit**: three dep pins → registry ranges (sources block deleted), renaming the stack-lifecycle dep and its `stack_lifecycle` imports to `stack-toolkit`/`stack_toolkit` in the same change; `ci.yml` authored (check + main-gated publish running `uv run --no-sync publish-packages` from the checkout). Operator pending publisher. Self-publish 0.1.0. — Repo half committed, then renamed `pubpkg` → `release-kit` (PyPI similarity rejection made `pubpkg` unclaimable; nothing ever published under it): main `599d19b` — conversion `2f114c0` incl. both `stack_lifecycle` import sites, AGENTS uvx-consumption `d4aaab0`, README `a3454cc`, rename `f93ab86`+`599d19b` (ruff per-file-ignore paths fixed with it; lock resolves fully from the registry; checks green, 29 tests). Awaiting operator push + pending publisher for `release-kit` + the self-publish.
5. [x] **Pin conversion**: the tool workflows' uvx git ref → `release-kit==0.1.0`; placeframe's release workflow converts its release-kit invocations to uvx registry pins; `build/pyproject.toml` drops the release-kit dependency and its DEP002 ignore. — Landed: five tool workflows pinned (`ec24476` bashrun, `583b430` logger-conf, `1fdf3f4` openapi-client-codegen, `ff9057b` stack-toolkit, `7e7033f` unity-buildkit); placeframe `d3746b53` (six workflow invocations → uvx, dep + sources entry + DEP002 ignore dropped, relock).
6. [x] **Consumer repoints**: placeframe (sources entries, member ranges, relock + `lock-python` + checks), prepo, pulsar, quarto-render, rubidium-build. — Landed: placeframe `a90e3265` (four git pins deleted, `stack-toolkit`/`openapi-client-codegen` dep + import renames across build/scripts, relock; ruff + basedpyright + deptry + targeted pytest green) + `9bb4d365` (agent docs for registry consumption); prepo `c13858a` (bashrun + unity-buildkit), pulsar `ea20e67`, quarto-render `a7d2f22`, rubidium-build `6c9267c` (bashrun; every drifted rev collapsed onto 0.1.0).
7. [x] **CaptureTool manifest repoint** (the bridge): five exact dev pins, zedcaptureclient stays `file:`, `lock-unity`, `compile-unity` sanity check. — Landed: `3f8e51d7`; `lock-unity` resolved all five from the npmjs scoped registry, and `compile-unity --project CaptureTool --build android-mobile` produced the APK against them — the Unity-side registry-consumption proof.
8. [x] **Docs**: release-kit `AGENTS.md` uvx consumption class (`d4aaab0`); each tool repo's `AGENTS.md` release-discipline line (landed with each repo's conversion commit); placeframe agent docs (`9bb4d365`); `polyrepo.md` resume update (this commit).

## Discarded alternatives

- **Doing nothing (git refs forever)**: the live substitution defect is unfixable without an owned logconf on PyPI; pin drift is already three-revs-deep on bashrun alone; the extraction thread wants registry-born repos. The standing costs stop being annoyances the moment a registry artifact depends on a name we don't own.
- **Private index**: a standing service, contradicting the org-wide no-standing-services rule; GitHub Packages for Python is auth-walled off plain `pip`/`uv`.
- **Dev channel for tool repos**: six dispatch workflows and prerelease bookkeeping for a rarely-changing tier; the git-scratch-pin remains the pre-release vehicle.
- **Bump tooling** (prepo `bump` resurrection, registry-query verb, Renovate-class bot): ranges + `uv lock --upgrade-package` make it redundant for stables; exact-pin-by-hand governs prereleases; no consumer-side network surface.
- **release-kit as a project dependency in tool repos**: resolver cycle plus root-version conflict against the `0.0.0.dev0` sentinel; uvx isolation is the boundary. placeframe's edge dissolves too — invocation-only everywhere.
- **Distribution-only rename for logconf**: breaks import==dist, deptry map wart in every consumer.
- **Folding logconf into placeframe-common**: couples the pulsar meta-repo to a placeframe package or duplicates the helper; the package boundary survives as an org tool.

## Open parameters

- Make-it-Sing fork folding (`placeframe-bash` / `placeframe-unity`) — subdirectory packages of placeframe pinned at placeframe revs; non-blocking, left forked.
