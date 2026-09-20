# Thread 4: internal tools on registries

## Scope

The fourth thread of the polyrepo initiative ([index](polyrepo.md)): every intra-org package reference resolves via a package registry, not a git URL. Threads 2 and 3 already convert the application-facing references (Unity `file:` → scoped registries, the zed repo's Python consumption → PyPI pins); this thread covers what remains — the internal tooling tier. Siblings: [prepo](polyrepo-workbench.md), [publishing](package-publishing-redesign.md), [repo boundaries](repo-extraction.md).

## Problem

Internal tool packages are consumed as git refs pinned to commit SHAs. That works — SHAs are immutable and declarative — but carries standing costs:

- **`tool.uv.sources` is not transitive**: every consumer must redeclare each tool's siblings alongside it (placeframe declares bashrun beside stack-lifecycle, unity-buildkit, openapi-clientgen, pubpkg; pubpkg declares bashrun beside stack-lifecycle, unity-buildkit; and so on down the graph). Registry dependencies would resolve transitively.
- **CI resolution cost**: git dependencies clone; registry wheels download faster and cache better.
- **Two consumption models**: application packages get registries, tools get git refs — two mental models, two update workflows, no uniform fresh-clone autonomy.

## Ground truth (census 2026-09-20)

Git-ref'd internal dependency edges in `[tool.uv.sources]` across the workspace:

| Package | Consumers |
|---|---|
| bashrun | openapi-clientgen, placeframe, prepo, pubpkg, pulsar, quarto-render, rubidium-build, stack-lifecycle, unity-buildkit (9) |
| logconf | placeframe, pulsar |
| stack-lifecycle | placeframe, pubpkg |
| unity-buildkit | placeframe, pubpkg |
| openapi-clientgen | placeframe |
| pubpkg | placeframe |

19 edges, 11 consuming repos. Make-it-Sing additionally pins two fork identities (`placeframe-bash`, `placeframe-unity`) — whether those fold into this thread or stay forked is an open parameter. None of the six packages has a release flow today: versions loaf at 0.1.0, no release tags, no publish config.

## Couplings

- **Gated on thread 2**: the feeds, pubpkg, and the dev channel must exist before tools can publish to them.
- **Gated on thread 3 in practice**: extraction settles the repo population and the final consumer set (zed and capture-tool repos become consumers); converting before extraction means re-touching their references again after.
- **Reopens a discarded alternative of the publishing design**: that doc rejected dev-channel discovery tooling ("exact-pin-by-hand suffices — CI prints the published version") explicitly *because* it was scoped to a one-or-two-consumer workflow. A tool like bashrun with nine consumers is a many-consumer world; hand-bumping nine pins per change may not survive contact, so the bump-tooling question (prepo `bump` resurrection, registry-query verb, Renovate-class bot) must be re-decided here on its own merits.

## Design

Not yet done. The design pass must at minimum resolve:

- **Update cadence and bump tooling** — hand-pinned exact versions versus discovery automation, decided against the many-consumer reality.
- **Bootstrap and circularity discipline** — pubpkg would publish itself and its own dependency tier; tool fixes reach consumers only after deliberate pin bumps. The rollout ordering and the "which pin does a release workflow itself consume" rules need writing down before anything converts.
- **Feed choice** — public PyPI claims names permanently and makes semver a public contract for tools that currently never release; a private index contradicts the no-standing-services preference. Public-CDN-for-internal-tools is the working assumption, not a decision.
- **Conversion scope** — which of the six packages (plus forks) convert and which stay git-ref'd; a single-consumer tool may never be worth a release flow.
- **The do-nothing check** — git-SHA pins cause redeclaration annoyance and CI latency, not correctness problems; the design pass should weigh whether that pain justifies permanent release discipline before converting anything.

## Change set

None yet — items appear here after the design pass. This thread does not open until threads 2 and 3 have landed.

## Discarded alternatives

None yet. Keeping git refs (doing nothing) remains the live default this thread must beat.
