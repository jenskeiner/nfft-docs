# Maintainer-controlled backlog order

Design spec, 2026-10-09.

## 1. Goal

The maintainer controls which issue the agents work next. A GitHub Project
board holds one total order of all open issues. The maintainer pushes issues
to the top. The product owner orders the rest, never changes the
maintainer's top items, and clears stale issues. Workers take the highest
item that nobody works on. Only the maintainer and the agents can add issues.

Non-goals: organization projects, board-move webhooks, an `In progress`
column.

## 2. Decisions

| ID | Decision | Rejected |
|----|----------|----------|
| B1 | Order lives on a user-owned GitHub Project board. | Priority labels: no total order. Rank number: manual renumbering. |
| B2 | Maintainer's top items are the `Next` status column. Product owner orders only `Backlog`. | `Pinned` field: less visible. Plain drag: API does not show who moved an item. |
| B3 | Issues in `Next` with `needs-triage` wait for the product owner. | Pick untriaged: no checked acceptance criteria. Trigger on move: no webhook for user projects. |
| B4 | Stale issues by the maintainer get only the label `stale-candidate`. Stale agent issues are closed. | Close maintainer issues: maintainer decides. |
| B5 | Model writes `backlog.json`. A shell step validates it and applies it with the token. The model never holds the token. | Model edits the board: model reads untrusted public text, and nothing enforces the `Next` rule. Organization move: too large. |
| B6 | Author lock in three layers: interaction limit `collaborators_only`, auto-close of other authors' issues, author filter in sync and gate. | Filter only: outsiders can still open issues. Private repo: Pages needs a paid plan. |

## 3. Board and access

- User project `NFFT docs backlog`, owner `jenskeiner`, linked to the repo.
- Field `Status`, options `Next`, `Backlog`, `Done`.
- Built-in project workflow: item closed sets `Done`. Auto-add is off; the
  sync script adds items.
- A claim stays the `in-progress` label. A claimed `Next` item stays in
  `Next` until it is closed.
- Secret `BACKLOG_TOKEN`: classic PAT of the maintainer, scopes `project` and
  `repo`. Repo admin rights are needed for the interaction limit. Only shell
  steps read it. It is never in the environment of the Claude Code step.
- Repo variable `BACKLOG_PROJECT`: the project number.
- Repo variable `BACKLOG_AUTHORS`: space-separated logins,
  `jenskeiner claude[bot]`.
- Label `priority: high` is deleted. Label `from-maintainer` stays; it only
  orders triage. New label `stale-candidate`.

## 4. Gate

`.github/scripts/agent-gate.sh` replaces the label sort with the board order.

1. Read all board items with GraphQL, in board position. Keep `Next` items
   first, then `Backlog` items, each in board order.
2. Take the first item that matches all of:
   - an open issue in this repo,
   - author in `BACKLOG_AUTHORS`,
   - label `ready-for-agent`,
   - none of `in-progress`, `blocked`, `needs-triage`,
   - its type label maps to a role in `agents/roles.json`. For a dispatch
     with a named role: that role only.
3. Write `role`, `model`, `max_turns`, `issue` as now.

If the board read fails, the gate writes `run=false` and exits non-zero. No
fallback to the label sort.

The cap of 3 open agent PRs stays. The gate step in `agents.yml` gets
`BACKLOG_TOKEN` in its environment.

## 5. Product owner

### 5.1 Sync, before the model

New `.github/scripts/backlog-sync.sh`, token `BACKLOG_TOKEN`:

1. List open issues. Drop issues whose author is not in `BACKLOG_AUTHORS`.
2. Add each remaining issue that is not on the board, with status `Backlog`,
   at the bottom.
3. Write `backlog-state.json`:

   ```json
   {
     "next":    [{"n": 51, "title": "...", "author": "jenskeiner", "labels": ["gap"]}],
     "backlog": [{"n": 42, "title": "...", "author": "claude[bot]", "labels": ["new-section", "ready-for-agent"]}],
     "stale_review": true
   }
   ```

   `stale_review` is true on Mondays (UTC).

The file content is appended to the prompt under "## Backlog state".

### 5.2 Model

Existing triage steps stay. `priority: high` is no longer set. New steps in
`agents/product-owner.md`:

- Order every `Backlog` item. Criteria in order: targets in `CONTEXT.md`,
  dependencies between issues, small before large at equal value. Issues
  that are not `ready-for-agent` may be anywhere in the order.
- If `stale_review` is true: review every open issue. Stale means one of:
  the pages already meet the acceptance criteria, duplicate of another open
  issue, conflicts with an active decision, refers to code removed upstream,
  outside the targets in `CONTEXT.md`. At most 10 per run.
- Write `backlog.json` at the repo root, not committed:

  ```json
  {
    "order": [42, 35, 34],
    "stale": [{"n": 17, "reason": "doc/guide/openmp.md already has the section"}]
  }
  ```

- Never list a `Next` item in `order`. Never move, label or close a `Next`
  item for order reasons.

### 5.3 Apply, after the model

New `.github/scripts/backlog-apply.sh`, token `BACKLOG_TOKEN`. Runs with
`if: always()` after the Claude Code step when `backlog.json` exists.

Validation against `backlog-state.json` and the live board. Any failure:
no board change, job fails with the reason.

- `order` holds each `Backlog` item number exactly once.
- `order` holds no `Next` item and no unknown number.
- Each `stale` number is an open issue on the board. Items in `Next` may
  appear in `stale`.

Actions:

1. Set the `Backlog` order with `updateProjectV2ItemPosition`, moving items
   from last to first, each after the previous one.
2. For each `stale` entry:
   - author `claude[bot]`: comment `Stale: <reason>`, close as not planned.
   - other author: add label `stale-candidate`, comment `Stale candidate:
     <reason>`. Never close.

### 5.4 Docs

Update `agents/product-owner.md`, `agents/skills/backlog.md` and
`agents/CONTEXT.md`: the pick order is the board order; remove the
`priority: high` rules and the label-based pick order; add the
`stale-candidate` label to the label tables.

## 6. Author lock

- New workflow `.github/workflows/repo-guard.yml`:
  - Monthly cron and dispatch: `PUT /repos/{owner}/{repo}/interaction-limits`
    with `limit: collaborators_only`, `expiry: six_months`. Token
    `BACKLOG_TOKEN`.
  - On `issues: opened`: if the author is not in `BACKLOG_AUTHORS`, comment
    that the repo accepts issues only from the maintainer, close as not
    planned, lock. Token `GITHUB_TOKEN`.
- Sync and gate filter by author, see sections 4 and 5.1.

Effect of the interaction limit: non-collaborators can also not comment or
open pull requests.

## 7. Setup by the maintainer

1. Create the project, field values, close workflow. Link the repo.
2. Create the PAT, store it as `BACKLOG_TOKEN`.
3. Set `BACKLOG_PROJECT` and `BACKLOG_AUTHORS`.
4. Dispatch `repo-guard.yml` once.
5. First product owner run adds all open issues to `Backlog`.

## 8. Testing

1. Spike before the build: confirm that the GraphQL `items` connection of a
   user project returns items in manual board order, and that the PAT can
   read and write it. If the order is not readable, this design stops and
   goes back to review.
2. `backlog-apply.sh` validation: offline tests with fixture files, bash and
   `jq`, one case per rule in 5.3.
3. Gate: offline test with a recorded GraphQL response, cases for `Next`
   first, skip rules, named role, board read failure.
4. End to end: dispatch product owner, then worker, on the real board with
   `AGENTS_ENABLED` off. Check the order on the board and the issue picked.
5. Author lock: with the limit active, a second account cannot open an
   issue. Then remove the limit, open an issue from the second account,
   check close and lock, and dispatch `repo-guard.yml` to restore the limit.
