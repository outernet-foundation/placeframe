Now I have the picture. Pulsar's sandbox app is `uv run sandbox` → COI launches an Incus container per `(project, branch)` slot → COI's `[tool]` block runs `claude` → a PATH shim at `/usr/local/sbin/claude` (`build.sh:93-113`) wraps Claude Code with Pulsar flags (`--add-dir /workspace --append-system-prompt-file /workspace/shared-conventions.md`).

COI hardcodes `claude` as the tool binary name (the comment at `build.sh:88-92` documents this — `ClaudeTool.BuildCommand` ignores the `[tool] binary` field). So integration has to go through that shim.

## Quick try-out (no Pulsar mods, 10 min)

In your current sandbox slot:

```bash
# Install opencode (npm or brew, whichever is available in-container)
curl -fsSL https://opencode.ai/install | bash
export MOONSHOT_API_KEY="sk-..."
mkdir -p ~/.config/opencode
```

Drop a minimal `~/.config/opencode/opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "moonshot": {
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "https://api.moonshot.ai/v1",
        "apiKey": "{env:MOONSHOT_API_KEY}"
      },
      "models": { "kimi-k2-0905-preview": {}, "kimi-k2-thinking": {} }
    }
  },
  "model": "moonshot/kimi-k2-0905-preview",
  "small_model": "moonshot/kimi-k2-0905-preview",
  "instructions": ["/workspace/shared-conventions.md"]
}
```

Then `cd /placeframe && opencode`. That's enough to evaluate the tool without touching any Pulsar code. The `instructions` field gives you Pulsar's shared conventions; Claude Code's `--append-system-prompt-file` becomes this. Throwaway — burn it down with `rm -rf ~/.config/opencode` when you're done.

## Pulsar integration — three options, ranked

### Option 1: Side-by-side (recommended starting point)

Add opencode to the image without touching the claude tool slot. Users opt in by running `opencode` instead of relying on COI's auto-launch.

Concrete changes:

1. **`.coi/profiles/pulsar/build.sh`** — add opencode install alongside the existing apt block, plus an `/usr/local/sbin/opencode` shim mirroring the claude shim shape (poll for project mount, cd in, exec real opencode):

   ```bash
   curl -fsSL https://opencode.ai/install | bash
   cat > /usr/local/sbin/opencode << 'SHIM'
   #!/bin/bash
   if [ -n "${PULSAR_PROJECT:-}" ]; then
     for _ in {1..60}; do
       [ -d "/$PULSAR_PROJECT" ] && break
       sleep 0.5
     done
     [ -d "/$PULSAR_PROJECT" ] && cd "/$PULSAR_PROJECT"
   fi
   exec /home/code/.local/bin/opencode "$@"
   SHIM
   chmod +x /usr/local/sbin/opencode
   ```

2. **`.coi/profiles/pulsar/config.toml`** — add API keys to `forward_env`:

   ```toml
   forward_env = [
     "GITHUB_TOKEN",
     # ...existing...
     "MOONSHOT_API_KEY",
     "DEEPSEEK_API_KEY",
     "OPENROUTER_API_KEY",
   ]
   ```

3. **`~/.config/placeframe/credentials`** (host side) — add `MOONSHOT_API_KEY`. Pulsar already forwards via `forward_env` once it's listed.

4. **A repo-side `opencode.json`** — drop one at `/workspace/opencode.json` (or per-project, e.g. `/placeframe/opencode.json`). Loads `shared-conventions.md` via `instructions`, configures the providers.

5. **Image rebuild**: `uv run sandbox setup --rebuild`. Then in any slot: `opencode` instead of (or alongside) the default claude tool.

This is the lowest-risk path. Claude Code keeps working unchanged; opencode is a peer.

### Option 2: Per-slot tool selection

Add a `--tool` flag to `uv run sandbox start` so you choose claude or opencode at slot creation. The shim at `/usr/local/sbin/claude` is hardcoded — COI calls it unconditionally — so this requires either:

- Forking the claude shim to check `$PULSAR_TOOL` and exec opencode if set, or
- Patching COI's `tool.go` (the comment at `build.sh:88-92` already names the function: `ClaudeTool.BuildCommand`)

The env-var approach is easier and stays within Pulsar:

```bash
# in /usr/local/sbin/claude
if [ "${PULSAR_TOOL:-}" = "opencode" ]; then
  exec /usr/local/sbin/opencode "$@"
fi
# ... existing claude logic ...
```

Then `uv run sandbox start -b my-branch` reads a `--tool opencode` flag, sets `PULSAR_TOOL=opencode` in `forward_env`, and the slot launches opencode through COI's normal flow. Skills, prompts, etc. resolve through the opencode shim.

### Option 3: Port Pulsar skills

The deepest integration. Pulsar has ~20 skills under `.claude/skills/` (commit, go, capture, audit, memorize, etc.). They're Claude Code-shaped. To run them in opencode they'd need translation to `.opencode/command/*.md` + `.opencode/agent/*.md`.

Many are simple enough (frontmatter + prompt body) to port directly with sed-style rewrites. A few — `tidy-commits`, `go`, `capture` — invoke Claude Code-specific tools (the Skill tool itself, TaskCreate, etc.) and would need rewiring. Worth doing only after Options 1-2 prove the workflow.

## Recommendation

Do **Option 1 first** — additive, ~30 lines of build.sh changes, one config.toml edit, one rebuild. Run opencode alongside Claude Code for a week on real tickets. If it sticks, escalate to Option 2 (single flag, single env-var-aware shim). Only port skills (Option 3) once you know which ones you'd actually use in opencode.

The whole Option-1 patch is small enough to put behind a feature branch and toss if you don't like it. Want me to draft the actual diff?
