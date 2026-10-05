# xinyu-s-skill-set

Personal Codex skill collection for syncing the same skills across machines. The maintained catalog is in [SKILLS_CATALOG.md](SKILLS_CATALOG.md).

## Skills Included

- `alipay-authenticate-wallet`
- `alipay-payment-skill`
- `animate`
- `animate-expo`
- `animation-vocabulary`
- `apple-design`
- `ask-sonner`
- `atomic-step-commit`
- `blindbox-ip-skill-4styles`
- `boji`
- `brainstorm-experiments-new`
- `brainstorm-ideas-new`
- `build-personal-profile`
- `creating-xiaohongshu-posts`
- `emil-design-eng`
- `find-animation-opportunities`
- `frontier-engineering-research`
- `grill-me`
- `grill-with-docs`
- `how`
- `identify-assumptions-new`
- `improve-animations`
- `lark-approval`
- `lark-apps`
- `lark-attendance`
- `lark-base`
- `lark-calendar`
- `lark-contact`
- `lark-doc`
- `lark-drive`
- `lark-event`
- `lark-im`
- `lark-mail`
- `lark-markdown`
- `lark-minutes`
- `lark-note`
- `lark-okr`
- `lark-openapi-explorer`
- `lark-shared`
- `lark-sheets`
- `lark-skill-maker`
- `lark-slides`
- `lark-task`
- `lark-vc`
- `lark-vc-agent`
- `lark-whiteboard`
- `lark-wiki`
- `lark-workflow-meeting-summary`
- `lark-workflow-standup-report`
- `lieflat-less-ai-tone`
- `monetization-strategy`
- `pick-ui-library`
- `planning-with-files`
- `prototype`
- `receiving-code-review`
- `review-animations`
- `show-me`
- `skillpay-onboarding`
- `systematic-debugging`
- `teach`
- `test-driven-development`
- `using-git-worktrees`
- `write-swift`
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
