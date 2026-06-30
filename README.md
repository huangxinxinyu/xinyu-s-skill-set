# xinyu-s-skill-set

Personal Codex skill collection for syncing the same skills across machines.

## Skills Included

- `acceptance-before-completion`
- `atomic-step-commit`
- `brainstorming`
- `frontier-engineering-research`
- `grill-me`
- `grill-with-docs`
- `planning-with-files`
- `ponytail`
- `receiving-code-review`
- `systematic-debugging`
- `teach`
- `test-driven-development`
- `using-foodism-test-env`
- `using-git-worktrees`
- `writing-skills`

## Markdown Notes

- `md/loop-engineering/AGENTS.md`: compact loop engineering instructions for
  goal-driven coding-agent work with this skill set.
- `md/loop-engineering/BACKEND_ENGINEERING.md`: reusable backend engineering
  standards for API, storage, jobs, consistency, and production behavior.

## Install

Clone this repo on a new machine, then copy the skills you want into your local skill directory:

```sh
mkdir -p ~/.agents/skills ~/.codex/skills
cp -R skills/* ~/.agents/skills/
```

`teach` originally came from `~/.codex/skills/teach`; keeping everything under `skills/` makes the repo easier to sync. If a skill needs to live under `~/.codex/skills`, copy that folder there instead.

## Notes

- `job-search` was requested but was not found in the local skill directories at the time this repo was created.
- System skills from `~/.codex/skills/.system` are intentionally not included.
