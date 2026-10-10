---
name: self-improvement
description: Use when changing the agent system of the NFFT3 docs repository, roles, prompts, skills, checks, issue templates, or the site frame (nav, theme, CSS). Says where each piece lives, how roles are selected, and what the protected paths are. Triggers - "meta", "new role", "new agent", "change the prompt", "add a skill", "site structure", "UI polish".
---

# Self-improvement

## How the system fits together

| Piece | Where | Loaded by |
|-------|-------|-----------|
| Shared rules and style | `agents/CONTEXT.md` | Every run, first in the prompt |
| Maintainer decisions | `agents/DECISIONS.md` | Every run, after CONTEXT |
| Role prompt | `agents/<role>.md` | The run of that role |
| Worker roles and their issue types | `agents/roles.json` | `.github/scripts/agent-gate.sh` picks the role for the `worker` cron from the best ready issue |
| Skills | `agents/skills/<name>.md`, assembled into plugin `nfft-agents` by `.github/scripts/assemble-plugin.sh` at run start | Claude Code, by the description's triggers |
| Checks | `support/checks/*.py`, run as `python -m support.checks.<name>` | PR checks and every agent before a PR |
| Issue forms | `.github/ISSUE_TEMPLATE/*.yml` | Maintainer |
| Site frame | `zensical.toml`, `doc/stylesheets/extra.css`, `support/overrides/main.html`, `doc/assets/` | Zensical build |

Fixed crons: product-owner every six hours, analyst every two days, worker
every hour. `AGENTS_ENABLED` false pauses these crons and the upstream poll. The worker's role is data: add an entry to `roles.json` and a prompt
file, and the next worker run can pick it. No workflow edit is needed, and
none is allowed.

## Writing a skill file

A skill is `agents/skills/<name>.md` with front matter `name: <name>` and a
`description` that carries the trigger phrases. Write and Edit it like any
file. Claude Code refuses every write under its loaded plugin directory
(`agents/plugin/`, gitignored) and under `.claude/`; do not try. The next run
assembles your file into the plugin.

## Protected paths

`.github/workflows/`, `.github/actions/`, `.github/scripts/`,
`support/docs-requirements.txt`, `nfft/`. The `protected-paths` check fails
any agent PR touching them. If a change there is needed, file a `meta` issue
labelled `ready-for-human` that says exactly what to change and why.

## Evidence first

Read transcripts before changing a prompt: `gh run list --workflow agents.yml
--limit 10 --json databaseId,name,conclusion`, then `gh run download <id> -n
transcript-<role>-<id> -D /tmp/t`. The file `claude-execution-output.json`
lists every tool call and the final message. Count turns to the claim, denied
calls, and whether the verification commands ran. Quote the line in the PR.

## Writing a role prompt

Shape of `agents/editor.md`: title, one sentence of purpose, types handled,
skills, numbered procedure, quality bar, stop conditions. Under 60 lines.
State what the role must not do. Name the verification commands by
reference to `CONTEXT.md`, do not copy them.

## Site frame changes

Zensical is MkDocs Material compatible. Theme features and palette are in
`zensical.toml` `[project.theme]`. Custom CSS goes in
`doc/stylesheets/extra.css`, loaded by `extra_css`. Template overrides go
in `support/overrides/` with `{% extends "base.html" %}`. After a change
run the strict build and `python -m support.checks.site`, then read the
built HTML of one page and describe the difference in the PR.
