---
updated: 2026-07-11
---

# opencode nested-doc auto-injection plugin

## Why this is needed

The agent-doc architecture puts one `AGENTS.md` per subsystem and relies on **auto-loading that doc when a file in its directory is touched** — so a subsystem's constraints land in context without anyone loading them by hand. Claude Code does this natively: it auto-pulls a directory's `CLAUDE.md` (our one-line `@AGENTS.md` import) on file-read. **opencode does not** — it loads only the root file at startup plus whatever `opencode.json` lists (which loads *always*, not per-directory), so nested subsystem docs never auto-inject. Without closing that gap, an opencode agent gets the root index and the cross-cutting rules but never a subsystem's own `AGENTS.md` automatically, and the architecture's core benefit is Claude-Code-only. A small opencode plugin restores parity.

## Mechanism

- **Observe the touched path.** `tool.execute.before` fires before `read`/`edit`/`grep`/`glob` with the authoritative file path. Observe here — do not mutate.
- **Inject via a chat hook.** Walk the touched directory up to the repo root, collect each `AGENTS.md`, and splice the ones not already in context this session in through `chat.message` / `experimental.chat.messages.transform` (synthetic text part) or `experimental.chat.system.transform` (append to the system-prompt array).
- **Dead route — do not use.** Mutating `output.output` in `tool.execute.after` does not reach the model (opencode #13574, closed not-planned).

## Prior art

Community plugins already implement this shape — lift from them rather than starting cold:

- `oh-my-opencode` (`code-yeongyu` / `dpshde`) ships a `directory-agents-injector` that walks touched-dir → root collecting every `AGENTS.md`.
- `frap129/opencode-rules` does path-aware injection with glob/keyword frontmatter.

## Caveats / open items

- The `experimental.chat.*` hooks are unstable (opencode #17100, #17637/#27401) — prefer the message-parts path over the system-prompt path.
- Needs per-session **dedup** so a doc injected once isn't re-injected on every touch.
- Point the walker at `AGENTS.md` (the canonical file), not `CLAUDE.md`.
- Verify against a current opencode build that injected content actually reaches the model — the hook surface has been in flux.
