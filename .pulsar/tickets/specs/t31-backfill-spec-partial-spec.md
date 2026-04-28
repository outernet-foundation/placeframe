---
id: T31
title: Handle existing partial SPEC.md in backfill-spec
status: done
depends_on: []
---

# T31: Handle existing partial SPEC.md in backfill-spec

## Goal

Make backfill-spec handle the case where a SPEC.md already exists but is incomplete, instead of assuming no spec exists.

## Context

The skill currently assumes it's creating a new SPEC.md from scratch. If someone started a spec manually or a previous backfill was interrupted, the skill could overwrite partial work without warning.

## Key files

- `.claude/skills/backfill-spec/SKILL.md` — step 1 or new step 0

## Approach

Add a check before step 1: if SPEC.md exists, read it, assess completeness, and ask the user whether to augment the existing spec or start fresh.

## Done when

- backfill-spec detects existing SPEC.md files before starting
- User is asked how to proceed when a partial spec exists

## Log

Merged into T30 (backfill-spec edge case handling) per ticket sizing guidelines.
