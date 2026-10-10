# Focus areas and pause

Design spec, 2026-10-10. Builds on `2026-10-09-backlog-priority-design.md`.

## 1. Goal

The maintainer acts as the business side and sets focus areas, for
example "installation and build" or "NFSFT API". The agents' own initiative
works only inside the active focus areas. Some work always runs: the
maintainer's own issues, `Next`, upstream sync and meta work. One switch
pauses the team.

Non-goals: focus areas that end by themselves, a second pause switch, focus
areas set by agents.

## 2. Decisions

| ID | Decision | Rejected |
|----|----------|----------|
| F1 | A focus is an open issue labelled `focus` whose author is the maintainer. Closing it ends the focus. Several can be active. | Milestones: short text, no discussion. `agents/FOCUS.md`: every change needs a PR. Repo variable: no room for a brief. |
| F2 | Strict focus with exceptions. Workers take an issue only if it is in `Next`, filed by the maintainer, of type `upstream` or `meta`, or a sub-issue of an active focus. | Soft focus: other work still runs. |
| F3 | With no focus open, only the exceptions run. The product owner files nothing, and the analyst does not run. | Fallback to coverage gaps: work the maintainer did not choose. |
| F4 | Focus order is the board column `Focus`, ordered by the maintainer. | Equal weight. Priority field: coarse. |
| F5 | Focus work is linked by GitHub sub-issues of the focus issue. | Labels per focus: no progress view, labels spread. |
| F6 | Pause stays `AGENTS_ENABLED`, extended to `upstream.yml`. The responder and the repo guard keep running while paused. | Pause issue, two switches. |

## 3. Focus issues and the board

- New template `.github/ISSUE_TEMPLATE/focus.yml`, title `[Focus] `,
  labels `focus`, `from-maintainer`, `projects: ["nfft-docs-agents/1"]`.
  Fields: Goal (required), Scope (required: pages, nav sections, API
  modules), Out of scope, Done when (required).
- Repo variable `BACKLOG_MAINTAINER` = `jenskeiner`. A `focus` issue by any
  other author is no focus. Scripts fail if the variable is empty.
- Board Status options, in this order: `Next`, `Focus`, `Backlog`, `Done`.
  The maintainer adds `Focus` in the project settings.
- Sync: every open focus issue of the maintainer gets `Focus`, also if it
  has another status. No other item gets `Focus`; a non-focus item found in
  `Focus` gets `Backlog`.
- Apply moves only `Backlog` items, as now, so `Next` and `Focus` keep the
  maintainer's order.
- The gate never picks an item in `Focus`. Triage never labels a focus issue
  `ready-for-agent`.

## 4. Gate

The existing rules stay (open, allowed author, `ready-for-agent`, none of
`in-progress`, `blocked`, `needs-triage`, a role for the type). New rule:
the issue is taken only if one of these holds:

- its status is `Next`,
- its author is `BACKLOG_MAINTAINER`,
- it has the type label `upstream` or `meta`,
- its parent issue is an active focus: open, label `focus`, author
  `BACKLOG_MAINTAINER`.

The board query reads `parent { number state author labels }` of each
issue. A `Backlog` item that fails only this rule is logged as
`skip #n: outside focus`.

Analyst: the gate starts the analyst only if at least one focus is active.
Otherwise `run=false`, log `no focus`. The analyst's input names the focus
issue to review: the highest focus in the `Focus` column without an open
issue titled `Analysis: #<focus number>`. If every focus has one, the gate
writes `run=false`, log `every focus analysed`.

## 5. Product owner

Sync adds a `focus` list to the state, in `Focus` column order:

```json
"focus": [{"n": 70, "title": "[Focus] NFSFT API", "sub": [71, 72], "ready": 1}]
```

`sub`: open sub-issues. `ready`: open sub-issues with `ready-for-agent`.

Prompt changes in `agents/product-owner.md`:

- Step 1: never label a `focus` issue `ready-for-agent`; remove
  `needs-triage` from it.
- Order of `Backlog`: the maintainer's issues, then `upstream`, then focus
  work by focus order, then `meta`, then the rest.
- Step 5 replaces the old sources: for each focus, in order, while it has
  fewer than 5 `ready` sub-issues, at most 5 new issues per focus per run.
  First adopt matching open issues as sub-issues, then file new ones as
  sub-issues. No focus: file nothing. The `Retro` issue and its `meta`
  proposals stay.
- New step: a focus whose sub-issues are all closed and whose scope has no
  further gap gets one comment `This focus looks done: <reason>`, once. The
  maintainer closes it.

Linking: `gh api graphql` with `addSubIssue(input: {issueId, subIssueId})`.

## 6. Analyst

Input from the gate: the focus issue number. The analyst reads the focus
brief and reviews the pages in its scope instead of the oldest section.
It files `Analysis: #<focus number>` and up to 5 finding issues, each a
sub-issue of the focus, labelled `needs-triage`.

## 7. Pause

`upstream.yml` job `poll` gets `if: github.event_name == 'workflow_dispatch'
|| vars.AGENTS_ENABLED == 'true'`. `agents.yml` keeps its condition. The
responder workflows and `repo-guard.yml` do not read `AGENTS_ENABLED`.

## 8. Docs

`agents/product-owner.md`, `agents/analyst.md`, `agents/skills/backlog.md`
(label `focus`, column `Focus`, pick rule), `agents/CONTEXT.md` (labels,
pick order), `agents/skills/self-improvement.md` (pause covers upstream).

## 9. Testing

1. Unit tests: each exception of section 4, a sub-issue of a closed focus,
   of a focus by another author, of a non-focus parent; `Focus` items never
   picked; sync status rules of section 3; apply never moves `Focus` items;
   state `focus` list; analyst focus choice.
2. Live: one test focus issue with one sub-issue on board 1; gate picks the
   sub-issue and skips an issue outside focus; the analyst choice names the
   focus.
3. Pause: with `AGENTS_ENABLED=false`, a scheduled upstream run is skipped;
   check after the next cron time.
