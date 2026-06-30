# Loop Engineering Agent Instructions

This file is a compact `AGENTS.md` pattern for building goal-driven coding-agent
loops with the skills in this repository.

## Start With A Goal

For non-trivial work, create or restate a concrete goal before acting:

- objective: what must be true when the loop is done,
- boundary: what is out of scope,
- verification: how the result will be checked,
- commit policy: whether to commit each coherent unit.

Use goal tracking for long-running work: keep the active goal visible, update it
when the plan changes, and mark it complete only after implementation,
verification, and required commits are done.

## Skill Loop

Use the skills in this package to shape the loop:

- `brainstorming`: use first for new behavior, product choices, UX direction, or
  unclear requirements. Do not implement until the design is approved.
- `planning-with-files`: use after brainstorming for complex implementation.
  Keep `task_plan.md`, `findings.md`, and `progress.md` current while working.
- `test-driven-development`: use for feature work and bug fixes before writing
  implementation code.
- `systematic-debugging`: use when behavior is unexpected, tests fail, or root
  cause is unclear.
- `receiving-code-review`: use before applying review feedback, especially when
  the feedback is broad or technically questionable.
- `acceptance-before-completion`: use before final handoff or marking a goal
  complete, especially when the result may have drifted from the user's request.
- `atomic-step-commit`: use when splitting, staging, or creating commits.
- `using-git-worktrees`: use before larger isolated feature work or when the
  current workspace should stay untouched.
- `writing-skills`: use when creating or changing skills.

Default complex-task flow:

1. Set the goal.
2. Use `brainstorming` to clarify and approve the design.
3. Use `planning-with-files` to create the execution plan.
4. Implement in small increments, using TDD/debugging skills when applicable.
5. Verify, update progress, and commit each coherent unit.
6. Run `acceptance-before-completion`, then mark the goal complete only after
   final verification and required commits.

## Work Loop

At the start of each goal:

1. Read the repository `AGENTS.md`.
2. Read relevant standards, memory, scope notes, and ADRs.
3. Run `git status --short`.
4. Identify applicable skills before acting.

During work:

- state the next edit before making it,
- prefer existing patterns over new abstractions,
- keep changes scoped to the goal,
- run the smallest useful verification after each coherent change,
- update planning files or memory only when they carry future value.

## Git

Use `atomic-step-commit` when splitting, staging, or creating commits.

## Final Response

When the goal is done, report:

- what changed,
- acceptance result,
- commit hash or hashes,
- verification run,
- anything intentionally not run,
- memory or planning updates made.
