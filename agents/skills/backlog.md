---
name: backlog
description: Use when filing, triaging, claiming or releasing GitHub issues in the NFFT3 docs repository. Covers the issue format, labels, priority rules, acceptance criteria and the claim protocol. Triggers - "file an issue", "triage", "claim", "backlog", "ready-for-agent".
---

# Backlog

The backlog is GitHub Issues. Labels carry the state.

## Labels

| Group | Labels |
|-------|--------|
| Type, exactly one | `gap`, `new-section`, `api-gap`, `math`, `style`, `clarity`, `compare`, `upstream`, `meta`, `design` |
| Maintainer input | `decision` (a ruling to record in `agents/DECISIONS.md`) |
| State, exactly one | `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `in-progress`, `blocked`, `wontfix` |
| Origin | `from-maintainer`, `agent` |
| Backlog | `stale-candidate` (proposed for closing, the maintainer decides), `keep` (never stale) |
| Upstream | `upstream-defect`, always with `ready-for-human`, never `ready-for-agent` |

Pick order: the board `NFFT docs backlog` of the organization
`nfft-docs-agents`. Column `Next` first, then `Backlog`, each top down. The
maintainer owns `Next`. The product owner orders `Backlog`. The gate picks
the first item with `ready-for-agent` and without `in-progress`, `blocked`
or `needs-triage`. Only issues by the maintainer, by agents and by the
workflows are on the board.

## Filing an issue

```
gh issue create --title "<imperative, under 70 chars>" --label <type> --label <state> --body-file body.md
```

Body, in this order:

```
## Pages
doc/guide/accuracy.md, new section after "Choosing m"

## What is missing or wrong
Two sentences. Quote the current text if it is wrong.

## Acceptance criteria
- [ ] A check an agent can run or a reader can verify
- [ ] ...

## Sources
nfft/kernel/nfft/nfft.c lines 120-180; Keiner, Kunis, Potts 2009 section 3
```

Acceptance criteria are concrete: "the page states the default m for each
window and cites nfft_init", not "document m".

## Claiming

```
gh issue edit <n> --add-label in-progress
gh issue comment <n> --body "Claimed by run <run URL from the prompt>"
```

Release when you stop without a PR:

```
gh issue edit <n> --remove-label in-progress
gh issue comment <n> --body "Released: <reason>"
```

A claim older than 12 hours without an open PR is stale. The product owner
releases it.

## Decisions

Before claiming, read the active rows of `agents/DECISIONS.md` in your prompt.
An issue that asks for something a row forbids is not worked: comment
`Conflicts with Dn: <ruling>`, add label `blocked`, pick the next issue.

## Triage

`needs-triage` to `ready-for-agent` needs: one type label, acceptance
criteria, pages named. Else `needs-info` with one question. Duplicates are
closed with a comment that names the original.
