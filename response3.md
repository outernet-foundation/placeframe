Good news: opencode is well-suited to exactly what you're describing. Here's the control surface and the concrete recipe.

## What you can configure per agent

Each agent is a markdown file with YAML frontmatter — `.opencode/agent/<name>.md` (per-project) or `~/.config/opencode/agent/<name>.md` (global). Fields:

```yaml
---
name: explorer
description: Read-only exploration of the codebase
mode: subagent          # primary | subagent | all
model: moonshot/kimi-k2-0905-preview
temperature: 0.3
tools:
  read: true
  grep: true
  glob: true
  bash: false           # deny dangerous tools per-agent
  write: false
  edit: false
permissions:
  bash: deny
---
You are an exploration agent. Search the repo and report findings...
```

The frontmatter gives you per-agent **model**, **tool allowlist**, and **permission policy**. The markdown body becomes the system prompt. Three modes:
- `primary` — switchable target you can talk to directly
- `subagent` — only invoked via `task` tool or `@mention`
- `all` — both

## How commands map to agent invocations

Commands live in `.opencode/command/<name>.md`. Two frontmatter fields are key to your question:

```yaml
---
agent: explorer
subtask: true           # critical
---
Find every place in the repo that touches $ARGUMENTS.
```

When `subtask: true` is set and `agent:` names a subagent, **`/explore foo` directly dispatches a subtask to that agent**. The primary model isn't asked "should I invoke the task tool?" — the slash command itself is the invocation. From the primary agent's perspective, the result comes back as if it had called the task tool, but the *decision* to dispatch was deterministic and synchronous from your keypress.

So: `/explore foo` → opencode looks up `explorer.md` → spawns it with the rendered prompt → it runs in a child session → returns when done. No inference round-trip on the primary side for the dispatch.

## Child sessions are visible and selectable

This is the 2026-added feature you want: **background subagents create child sessions that appear in the parent session's TUI**. Default keybinding `<Leader>+Down` enters the first child; you can navigate them like a list. So while the explorer is grinding through the repo on Kimi, you can:
- Stay in the parent session and keep working
- Pop into the child to watch progress
- Pop back out and let it finish
- See the result land in the parent when it completes

That matches your spec exactly: type a command, instantly spawn a background agent (no main-model inference for the decision), have it appear as a selectable session in your current view.

## The fully-independent variant

If you want a spawned agent that's **not** tied to the current session at all — runs as a peer, never reports back, just shows up in the global session list — use opencode's HTTP API directly. The server exposes session creation; a tiny shell hook in a command can POST to it:

```yaml
---
shell: true
---
curl -X POST http://localhost:4096/session \
  -H "Content-Type: application/json" \
  -d '{"agent":"explorer","message":"$ARGUMENTS"}'
```

That spawns an independent session, returns immediately, doesn't block your current session, and the new session appears in the session list (Ctrl+L or similar). Useful when you want to fire-and-forget multiple parallel explorers.

## Practical pattern for your use case

A reasonable setup for your stated workflow:

1. **`scout` agent** (subagent, Kimi K2 base, read-only tools) — fast exploration
2. **`investigator` agent** (subagent, Kimi K2 Thinking, read-only + run-tests) — deeper analysis
3. **`refactor` agent** (subagent, Claude Sonnet via API, full tools) — when you want the strong model for a specific edit
4. Commands `/scout`, `/dig`, `/refactor` each with `subtask: true` and the right `agent:` field

Then your driving session is the primary agent you talk to normally, and you fire off these specialists in parallel as needed. Each appears as a child session you can attach to. Cost stays low because the specialists run on Kimi; only `/refactor` hits the Claude API.

One real wrinkle: **command-as-passthrough still consumes a small amount of primary-agent context** when the result returns (the subtask result is appended to the parent's history). If you want zero context impact on the primary, the HTTP-API spawn is the cleaner path. For most workflows the context cost is small enough not to matter.

Sources:
- [opencode Agents docs](https://opencode.ai/docs/agents/)
- [opencode Commands docs](https://opencode.ai/docs/commands/)
- [opencode Agent System — DeepWiki](https://deepwiki.com/sst/opencode/3.2-agent-system)
- [Custom Agents in OpenCode CLI — BSWEN](https://docs.bswen.com/blog/2026-03-30-opencode-custom-agents/)
