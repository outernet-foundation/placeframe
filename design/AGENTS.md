# design/

## What this is

`design/` holds **in-flux design and research**: the worked-out plans, math, thresholds, literature, and discarded alternatives for work that will be built but does not exist yet — or that cross-cuts several subsystems and so has no single code directory to sit beside. It is plain, git-tracked Markdown, so the design is durable (it survives a sandbox teardown), reviewable, and linkable from a Linear ticket by a GitHub blob URL.

It is a distinct tier from the other three, and the distinctions are the whole point:

- **vs a subsystem `AGENTS.md`** — an `AGENTS.md` is *present truth* about code that exists, auto-loaded on directory touch. A design doc here is *pre-implementation and in flux*: allowed to be incomplete, speculative, and — as the code moves under it — wrong. It is never auto-loaded and must not be read as an authority on the current codebase.
- **vs `.pulsar/memories/`** — a memory is a free-form bookmark of one working session, distilled-and-deleted. A design doc is durable working design that outlives any single session.
- **vs a Linear ticket** — a ticket is a declarative outcome; the mechanism, derivation, and alternatives it references live here.

## Conventions

- **Plain Markdown, cross-linked, no enforced hierarchy.** Notes reference each other with relative Markdown links and reference code by `path:line`. Design is inherently a cross-cutting web, not a tree — don't impose a directory taxonomy on it.
- **Staleness is expected, not a defect.** These describe in-progress thinking, and shipping code will routinely outdate a shelved design. Do not build tooling to keep them current, and do not trust one as a description of the code as it stands. When you need present truth, read the code or its `AGENTS.md`.
- **Link from Linear by blob URL.** A ticket needing design context links the note by a full `github.com/.../blob/dev/design/...` URL — clickable, and accepted by the ticket-body linter, which rejects only `.pulsar/memories` pointers.
- **Promotion is opportunistic, not required.** When a design is implemented, fold whatever has hardened into the built subsystem's co-located `AGENTS.md`. The design note can then be deleted or left to rot — it is no longer load-bearing once the truth lives beside the code.

## Scope

This tier is org-level and cross-repo: the same localization and spatial-mapping design informs placeframe, make-it-sing, and infra. It is homed in the placeframe repo, but treat it as shared — a design about another repo is welcome here.
