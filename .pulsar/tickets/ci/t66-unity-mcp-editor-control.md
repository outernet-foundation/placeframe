---
id: T66
title: Unity MCP — direct editor control from Claude Code
status: design-needed
depends_on: [T62]
---

# T66: Unity MCP — direct editor control from Claude Code

## Goal

Investigate running Unity Editor (full GUI, not batch mode) inside the COI Incus container with GPU passthrough, and connecting it to Claude Code via a Unity MCP server — enabling direct scene manipulation, asset management, build triggering, and project automation through natural language.

## Context

T62 gives Claude batch-mode compilation checking (can the C# compile?). This ticket explores a much richer capability: Claude directly controlling a running Unity Editor instance. Several community MCP server implementations exist:

- [mcp-unity](https://github.com/CoderGamester/mcp-unity) — MCP plugin for Unity Editor, designed for Cursor/Claude Code/Codex
- [unity-mcp](https://github.com/CoplayDev/unity-mcp) — bridge for AI assistants to interact with Unity Editor via WebSocket + MCP
- [Unity-MCP](https://github.com/IvanMurzak/Unity-MCP) — AI-powered bridge connecting LLMs to the Unity Editor

These run a WebSocket server inside Unity and a Node.js MCP bridge that Claude Code can connect to natively. Capabilities include executing menu items, managing assets, controlling scenes, editing scripts, and automating tasks.

Infrastructure already partially exists: `setup_agent_sandbox.py` configures full GPU passthrough on the Incus default profile (`incus profile device add default gpu gpu`). The host has NVIDIA drivers.

## Open questions

1. **Display server**: Unity Editor needs a display. Options: Xvfb (virtual framebuffer — works in full COI containers, only failed in restricted build containers), VNC server, or X11 forwarding. Which is simplest and most reliable?
2. **Resource budget**: A running Unity Editor uses ~2-4GB RAM. Is this acceptable alongside Docker services? Should we only open one project at a time?
3. **MCP server choice**: Three community implementations exist. Which is most mature, best maintained, and compatible with Claude Code's MCP support?
4. **License mode**: Does a Personal `.ulf` license work for GUI mode in a container, or only batch mode?
5. **Per-project setup**: MCP servers need to be installed as Unity packages in each project. Is this acceptable, or is there a project-agnostic approach?
6. **Scope boundary**: What operations should Claude be able to perform? Just builds and scene queries? Or full scene editing, asset creation, prefab manipulation?

## Done when

- [ ] Research report in `.pulsar/research/` evaluating feasibility and recommending an approach
- [ ] Design decisions made on all open questions above
- [ ] Ticket updated with approach and moved to `plan-needed`
