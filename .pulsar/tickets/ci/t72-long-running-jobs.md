---
id: T72
title: Long-running jobs in Claude Code agent sessions
status: done
depends_on: []
---

# T72: Long-running jobs in Claude Code agent sessions

## Goal

Enable Claude Code to reliably run jobs that take longer than 10 minutes (e.g. native C++ builds with vcpkg) and receive completion notifications.

## Context

The Bash tool's `timeout` parameter has a maximum of 600,000ms (10 minutes). The `run_in_background` flag sends a completion notification, but it's unclear whether background tasks are also subject to this timeout. During T69, the Cesium native build (cmake + vcpkg, ~30-60 minutes) could not be run through normal Claude Code mechanisms:

- `run_in_background: true` with `timeout: 600000` — notified on early failures but untested for long-running success (the build never succeeded within a session)
- `nohup` — runs indefinitely but sends no notification; Claude only learns the result when the user asks

This affects any job that takes more than ~10 minutes: native builds, large Docker image builds, full test suites, etc.

## Resolution

No code change needed. `run_in_background: true` does **not** enforce the `timeout` parameter — background tasks run until the process exits naturally, regardless of duration. The perceived limitation during T69 was caused by explicitly passing `timeout: 600000` alongside `run_in_background: true`, which imposed an unnecessary cap.

Answers to open questions:

1. **Does `run_in_background` enforce timeout?** No. Background tasks run until the process exits. The timeout only governs foreground (blocking) calls.
2. **Wrapper script needed?** No. `run_in_background` already delivers a completion notification on exit (success or failure).
3. **`screen`/`tmux` in COI?** Not needed for this use case. The only caveat is that background tasks are killed if the Claude Code session itself exits — but that's a session lifecycle issue, not a timeout issue.

## Log

No implementation needed. The ticket's premise was based on a misunderstanding from the T69 session where a timeout was explicitly (and unnecessarily) set on a background command, making it appear that background tasks had a 10-minute limit.

## Observations

No pre-existing issues noticed.
