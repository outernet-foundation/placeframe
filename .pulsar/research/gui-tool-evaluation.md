# GUI Tool Evaluation for Roadmap Board

Research conducted 2026-03-01. Context: choosing a web UI for the markdown-based ticket system.

## Constraint

FOSS only, no VC-backed projects at acquisition risk. Evaluate not just current license but governance structure and funding model.

## Tools Evaluated

### Rejected

| Tool | License | Reason |
|------|---------|--------|
| **Streamlit** | Apache 2.0 | Acquired by Snowflake (2022). Core team are Snowflake employees. License protects existing code but not development trajectory or ecosystem. Classic rug-pull profile. |
| **GitHub Projects** | Proprietary | Microsoft-owned. Polished kanban board but vendor lock-in for a core workflow. |
| **Obsidian** | Proprietary | Kanban + Dataview plugins work great with frontmatter files, but proprietary, desktop-only, not self-hostable. |
| **Marimo** | Apache 2.0 | VC-backed. Same rug-pull risk as Streamlit. |
| **Linear/Notion/Jira** | Proprietary | Fighting two systems (sync glue between markdown files and the tool). More work than building bespoke. |

### Approved (used in T16)

| Tool | License | Governance | Role |
|------|---------|------------|------|
| **Litestar** | MIT | Community fork, independent | Backend (already in project) |
| **htmx** | 0-clause BSD | Independent (Carson Gross) | Interactivity without JS framework |
| **Sortable.js** | MIT | Independent | Drag-and-drop for kanban columns |
| **python-frontmatter** | MIT | Independent | Read/write ticket YAML frontmatter |
| **mistune** | BSD | Independent (Hsiaoming Yang) | Render ticket markdown as HTML |

### Considered but deferred

| Tool | License | Notes |
|------|---------|-------|
| **Datasette** | BSD | Simon Willison, independent. Great for querying (faceted search, JSON API) but less interactive than a kanban board. Could complement the board for ad-hoc queries. |
| **Vikunja** | GPL | Go-based, self-hosted task management with kanban. Genuinely independent FOSS. But running another service + sync glue is more work than bespoke for ~15-500 tickets. |
| **Kanboard** | GPL | PHP, minimal, JSON-RPC API. Same tradeoff as Vikunja. |

## Decision

Bespoke Litestar + htmx app. The FOSS constraint makes "adopt an existing tool" harder (vetting overhead, migration path maintenance) while making "build a small thing" easier (every dependency is trivially replaceable, total code ~300-500 lines fully owned). The board runs as `uv run board`, reads frontmatter files directly, and requires no external services.
