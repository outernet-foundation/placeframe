---
id: T30
title: Improve backfill-spec edge case handling
status: ready
depends_on: []
---

# T30: Improve backfill-spec edge case handling

## Goal

Improve backfill-spec with conflict resolution guidance, partial-spec handling, and a numbering convention note.

## Context

Three small gaps identified in the backfill-spec skill, merged into one ticket per sizing guidelines (each is too small alone, but they're coupled — all modify the same skill to handle edge cases):

1. **Conflict resolution** (was T30): Step 1 says "the code is the source of truth for behavior, and the user is the source of truth for intent." But there's no guidance for when the code contradicts a ticket, or when the user's stated intent contradicts what the code does.

2. **Partial spec handling** (was T31): The skill assumes it's creating a new SPEC.md from scratch. If someone started a spec manually or a previous backfill was interrupted, the skill could overwrite partial work without warning.

3. **Numbering convention note** (was T32): Step 6 creates tickets for gaps using the next available T-number — same convention as `/roadmap create`, but the skill doesn't say so.

## Key files

- `.claude/skills/backfill-spec/SKILL.md`

## Approach

Add conflict resolution guidance to step 1. Add a pre-check before step 1 for existing SPEC.md files. Add a brief note to step 6 about shared ticket numbering.

## Done when

- Step 1 has explicit conflict resolution guidance for code vs ticket and code vs user intent disagreements
- A pre-check detects existing SPEC.md files and asks the user how to proceed
- Step 6 notes it uses the same numbering convention as `/roadmap create`
