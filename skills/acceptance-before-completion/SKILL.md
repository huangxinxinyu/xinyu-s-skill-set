---
name: acceptance-before-completion
description: Use when finishing non-trivial work, marking a goal complete, handing off code or documents, or when work may be drifting from the user's requested outcome and needs evidence-based acceptance before final response
---

# Acceptance Before Completion

## Overview

Do not call work done until the user's goal is mapped to concrete evidence.

**Core principle:** completion is a claim that needs proof, not a feeling that the loop has run long enough.

## The Gate

Before final response or marking a goal complete:

1. Restate the user's requested outcome and any known boundaries.
2. Convert it into acceptance criteria. Use the user's criteria when present; otherwise infer the smallest criteria that prove the requested outcome.
3. Map every criterion to evidence: tests, command output, screenshots, rendered artifacts, source links, diffs, or explicit manual inspection.
4. Check scope: note unrelated changes, skipped work, unresolved questions, and tradeoffs.
5. Decide `done: yes` only if all blocking criteria have evidence.

If a blocking criterion lacks evidence, do not say the work is complete. Say what is done and what evidence is missing.

## Evidence Rules

| Work type | Minimum useful evidence |
| --- | --- |
| Code change | Relevant tests, build/typecheck/lint when available, and changed files |
| Bug fix | Reproduction or failing test, root cause, passing verification |
| UI change | Screenshot or browser check for the affected viewport/state |
| Research | Sources used, date-sensitive caveats, and recommendation boundary |
| Document/artifact | Rendered or inspected final output, not only source text |

Use the smallest check that can actually fail if the work is wrong.

## Acceptance Report

Use this shape in the final response when the task is non-trivial:

```markdown
Acceptance:
- [pass] <criterion>: <evidence>
- [warn] <criterion>: <partial evidence or residual risk>
- [fail] <criterion>: <missing evidence or blocker>

Done: yes/no
```

For small tasks, compress it into one sentence: `Verified with <command/check>; residual risk: <none/item>.`

## Red Flags

- "Should be fine" without a check.
- Tests passed but do not cover the user's actual request.
- A plan is complete on paper while a blocking criterion remains unverified.
- The work solved a narrower problem than the user asked for.
- The implementation drifted into extra scope that was not accepted.

All of these mean: stop, run the gate, and report the gap instead of claiming completion.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Treating test pass as acceptance | Tie tests back to user-facing criteria |
| Hiding unverified work | Mark it `[warn]` or `[fail]` explicitly |
| Overbuilding the report | Use one short table or sentence |
| Marking a goal complete after partial progress | Say `Done: no` and name the missing criterion |
