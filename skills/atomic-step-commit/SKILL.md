---
name: atomic-step-commit
description: Use when preparing, splitting, staging, or creating git commits for completed work, especially when changes span multiple concerns, tests, files, or behavioral units and each commit should be independently reviewable and verifiable
---

# Atomic Step Commit

## Overview

Commit work as atomic steps: each step is the smallest independently verifiable unit.

**Core principle:** one step equals one minimal unit that can be understood, checked, and reverted without depending on unrelated changes.

## Workflow

1. Inspect the full diff before staging anything.
2. Group changes by behavior, not by file.
3. For each group, ask: "Can this be verified on its own?"
4. Stage only that group.
5. Run the smallest check that can fail if the group is wrong.
6. Commit with a message that names the behavior changed.
7. Repeat until no intended changes remain.

Use `git add -p` when one file contains multiple steps. Do not stage a whole file just because it is convenient if it mixes unrelated changes.

## Atomic Step Test

A step is atomic only if all are true:

- It has one purpose.
- It can be verified with one focused check, test, build, lint, screenshot, or manual inspection.
- It can be reverted without removing unrelated work.
- It leaves the repository in a coherent state.
- Its commit message can be specific without using "and".

If the message needs "and", split the step unless the two parts cannot run independently.

## Rules

Prefer fewer commits when splitting would create fake steps.

Keep changes together when either side is invalid alone: test plus implementation, migration plus code, generated file plus source change.

Split formatting, mechanical renames, refactors, features, and independent bug fixes when each can be checked alone.

Verify each commit with the smallest real check: targeted test, build, typecheck, lint, screenshot, or staged diff review.

Use one concise imperative subject:

Good: `Fix stale token refresh`
Bad: `Fix auth and update tests`

Before final response, report each commit hash, subject, and verification command.
