---
id: T32
title: Note shared ticket numbering convention in backfill-spec
status: done
depends_on: []
---

# T32: Note shared ticket numbering convention in backfill-spec

## Goal

Add a note to backfill-spec step 6 clarifying that it uses the same ticket numbering convention as `/roadmap create`.

## Context

backfill-spec creates tickets for gaps (step 6) using the next available T-number. This is the same convention as `/roadmap create`, but the skill doesn't say so. A brief note prevents confusion about whether the two skills could collide on ticket numbers.

## Key files

- `.claude/skills/backfill-spec/SKILL.md` — step 6

## Done when

- Step 6 notes it uses the same numbering convention as `/roadmap create`

## Log

Merged into T30 (backfill-spec edge case handling) per ticket sizing guidelines.
