First: rewrite T1/T2/T3 into the constraint-violation format. This means:

1. Write CI constraints as directory-local `CLAUDE.md` files (the decisions are currently buried in ticket prose and plans)
2. Rewrite T1/T2/T3 tickets with `constraint:` and `violators:` frontmatter — they may decompose into more tickets once constraints are explicit

The current tickets and plans have the right content but the wrong shape. Read them, extract the constraints, distribute into directory-local CLAUDE.md files, then rewrite the tickets as violations of those constraints.

Current tickets: `.pulsar/tickets/ci/t1-*`, `.pulsar/tickets/ci/t2-*`, `.pulsar/tickets/ci/t3-*`
Plans: `.pulsar/plans/t1-plan.md`, `.pulsar/plans/t2-plan.md`, `.pulsar/plans/t3-plan.md`
Research: `.pulsar/research/docker-build-reproducibility.md`
