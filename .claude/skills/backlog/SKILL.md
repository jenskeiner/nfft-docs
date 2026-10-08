---
name: backlog
description: Use when filing, triaging, claiming or releasing GitHub issues in the NFFT3 docs repository. Covers the issue format, labels, priority rules, acceptance criteria and the claim protocol. Triggers - "file an issue", "triage", "claim", "backlog", "ready-for-agent".
---

# Backlog

The backlog is GitHub Issues. Labels carry the state.

## Labels

| Group | Labels |
|-------|--------|
| Type, exactly one | `gap`, `new-section`, `api-gap`, `math`, `style`, `clarity`, `compare`, `upstream` |
| State, exactly one | `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `in-progress`, `blocked`, `wontfix` |
| Origin | `from-maintainer`, `agent` |
| Priority | `priority: high` |
| Upstream | `upstream-defect`, always with `ready-for-human`, never `ready-for-agent` |

Pick order for workers: `from-maintainer`, then `priority: high`, then the
oldest `createdAt`.

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

## Triage

`needs-triage` to `ready-for-agent` needs: one type label, acceptance
criteria, pages named. Else `needs-info` with one question. Duplicates are
closed with a comment that names the original.
