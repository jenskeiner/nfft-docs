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
| Maintainer input | `decision` (a ruling to record in `agents/DECISIONS.md`), `focus` (an area to work on) |
| State, exactly one | `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `in-progress`, `blocked`, `wontfix` |
| Origin | `from-maintainer`, `agent` |
| Backlog | `stale-candidate` (proposed for closing, the maintainer decides), `keep` (never stale) |
| Upstream | `upstream-defect`, always with `ready-for-human`, never `ready-for-agent` |

Pick order: the board `NFFT docs backlog` of the organization
`nfft-docs-agents`. Columns `Next`, `Focus`, `Backlog`, `Done`. The
maintainer owns `Next` and `Focus`; `Focus` holds the open focus issues,
most important first. The product owner orders `Backlog`. The gate picks
from `Next`, then `Backlog`, top down, the first item with
`ready-for-agent`, without `in-progress`, `blocked` or `needs-triage`, that
is in scope: in `Next`, filed by the maintainer, of type `upstream` or
`meta`, or a sub-issue of an open focus issue. Only issues by the
maintainer, by agents and by the workflows are on the board.

## Focus areas

A focus issue is an open issue with label `focus` filed by the maintainer.
Work for a focus is its sub-issue. Link an issue as a sub-issue:

```
parent=$(gh issue view <focus> --json id --jq .id)
child=$(gh issue view <n> --json id --jq .id)
gh api graphql -f query='mutation($p: ID!, $c: ID!) { addSubIssue(input: {issueId: $p, subIssueId: $c}) { issue { number } } }' -f p="$parent" -f c="$child"
```

An issue has at most one parent.

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
