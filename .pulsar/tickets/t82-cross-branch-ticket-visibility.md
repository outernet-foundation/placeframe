---
id: T82
title: Design cross-branch ticket visibility for the skill system
status: design-needed
depends_on: []
---

# T82: Design cross-branch ticket visibility for the skill system

## Goal

When work is parked on a feature branch and the user switches to another task, ticket state (status, branch location) should be visible from the base branch. Currently, ticket files are branch-local — switching branches loses visibility into parked work.

## Context

Discovered during T71 implementation. The workon skill assumes linear start-to-finish on one branch. When you need to park a ticket and switch tasks, there's no mechanism to record where the work lives or make the ticket's current status visible from other branches.

Three specific gaps:
1. No "park" concept in `/workon` — the skill has no step for saving state and switching
2. No `branch` field in ticket frontmatter — nowhere to record which branch holds the work
3. No cross-branch ticket sync — `/roadmap query`, the board app, and `/workon` all read from HEAD

Options explored (see conversation for full analysis):
- **Park convention**: Add `branch` field to frontmatter, add `/workon park` step that updates the base branch
- **Dedicated roadmap branch**: Move all tickets to a permanent branch, read via `git show`
- **External metadata file**: JSON map on base branch tracking ticket-to-branch mappings
- **Manual for now**: Use ad-hoc branch pointers in ticket frontmatter until a pattern emerges

## Next step

Decide on an approach after hitting this workflow a few more times. The manual `branch` field in frontmatter (used for T71) works as a stopgap.
