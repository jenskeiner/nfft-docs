# Maintainer-controlled backlog order

Design spec, 2026-10-09.

## 1. Goal

The maintainer controls which issue the agents work next. A GitHub Project
board holds one total order of all open issues. The maintainer pushes issues
to the top. The product owner orders the rest, never changes the
maintainer's top items, and clears stale issues. Workers take the highest
item that nobody works on. Only the maintainer and the agents can add issues.

Non-goals: board-move webhooks, an `In progress` column, moving the repo to
an organization.

## 2. Decisions

| ID | Decision | Rejected |
|----|----------|----------|
| B1 | Order lives on a GitHub Project board owned by the organization `nfft-docs-agents`, which holds only this board. The repo stays under `jenskeiner`. | Priority labels: no total order. Rank number: manual renumbering. User-owned board: needs a classic token with access to all of the maintainer's boards. |
| B2 | Maintainer's top items are the `Next` status column. Product owner orders only `Backlog`. | `Pinned` field: less visible. Plain drag: API does not show who moved an item. |
| B3 | Issues in `Next` with `needs-triage` wait for the product owner. | Pick untriaged: no checked acceptance criteria. Trigger on move: needs a webhook. |
| B4 | Stale issues by the maintainer get only the label `stale-candidate`. Stale agent issues are closed. Issues labelled `keep` are never stale. | Close maintainer issues: maintainer decides. Repeat proposals every week: noise. |
| B5 | Model writes `backlog.json`. A separate job in a fresh checkout validates it against the live board and applies it with the token. The model never holds the token. | Model edits the board: model reads untrusted public text, and nothing enforces the `Next` rule. |
| B6 | Author lock in three layers: interaction limit `collaborators_only`, auto-close of other authors' issues, author filter in sync and gate. If the limit blocks the agent bots, the limit is removed and the other two layers stay. | Filter only: outsiders can still open issues. Private repo: Pages needs a paid plan. |
| B7 | Two fine-grained tokens, 1 year expiry, a monthly check warns 60 days before expiry. | Classic token: too broad. No expiry: risk without end. |
| B8 | The product owner is exempt from the cap of 3 open agent PRs. | Cap: no triage, order or stale review while the cap holds. |
| B9 | Board logic in one stdlib Python script with unit tests. | Bash and `jq`: rules too complex to test. |

## 3. Board and access

- Organization `nfft-docs-agents`, owner `jenskeiner`. Project `NFFT docs
  backlog`. The repo cannot list an organization board in its Projects tab;
  this has no effect on the design.
- Field `Status`, options `Next`, `Backlog`, `Done`.
- Built-in project workflows: item closed sets `Done`; auto-archive for
  `is:closed updated:<@today-14d`. Auto-add is off; the sync adds items.
- Every issue template has `projects: ["nfft-docs-agents/<number>"]`, so the
  maintainer's new issues are on the board at once, without a Status.
- A claim stays the `in-progress` label. A claimed `Next` item stays in
  `Next` until it is closed.
- Secret `BACKLOG_TOKEN`, environment `agents`: fine-grained token, resource
  owner `nfft-docs-agents`, organization permission Projects read and write,
  1 year expiry. Reads of the public repo need no extra permission.
- Secret `GUARD_TOKEN`, environment `agents`: fine-grained token, resource
  owner `jenskeiner`, repository `nfft-docs` only, permission Administration
  read and write, 1 year expiry. Only `repo-guard.yml` uses it.
- Only shell steps read the two tokens. Never the Claude Code step, never a
  step after it in the same job.
- Issue edits (comment, label, close) use `GITHUB_TOKEN`.
- Repo variables: `BACKLOG_OWNER` = `nfft-docs-agents`, `BACKLOG_PROJECT` =
  the project number, `BACKLOG_AUTHORS` =
  `jenskeiner claude[bot] github-actions[bot]`. If one is empty, every
  script fails. Never fall back to "all authors".
- Label `priority: high` is deleted. Label `from-maintainer` stays; it only
  orders triage. New labels `stale-candidate`, `keep`.

## 4. Gate

`.github/scripts/agent-gate.sh` replaces the label sort with the board order.

1. Read all board items with GraphQL, in board position. Keep `Next` items
   first, then `Backlog` items, each in board order. Items without a Status
   are skipped until the sync gives them `Backlog`.
2. Take the first item that matches all of:
   - an open issue in this repo,
   - author in `BACKLOG_AUTHORS`,
   - label `ready-for-agent`,
   - none of `in-progress`, `blocked`, `needs-triage`,
   - its type label maps to a role in `agents/roles.json`. For a dispatch
     with a named role: that role only.
3. Log each `Next` item skipped on the way, with the reason. No comments.
4. Write `role`, `model`, `max_turns`, `issue` as now.

If the board read fails, the gate writes `run=false` and exits non-zero. No
fallback to the label sort.

The cap of 3 open agent PRs applies to workers only. The product owner and
the analyst are exempt.

## 5. Product owner

### 5.1 Sync, before the model

`backlog.py sync`, token `BACKLOG_TOKEN`:

1. List open issues. Drop issues whose author is not in `BACKLOG_AUTHORS`.
2. Add each remaining issue that is not on the board, at the bottom. Give
   `Backlog` to every open board item without a Status.
3. Print the state, appended to the prompt under "## Backlog state":

   ```json
   {
     "next":    [{"n": 51, "title": "...", "author": "jenskeiner", "labels": ["gap"]}],
     "backlog": [{"n": 42, "title": "...", "author": "claude[bot]", "labels": ["new-section", "ready-for-agent"]}],
     "stale_review": true
   }
   ```

   `stale_review` is true on Mondays (UTC).

### 5.2 Model

Existing triage steps stay. `priority: high` is no longer set. New steps in
`agents/product-owner.md`:

- Order every `Backlog` item, also issues filed in this run. Criteria in
  order: targets in `CONTEXT.md`, dependencies between issues, small before
  large at equal value.
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

- Never list a `Next` item in `order`.

### 5.3 Apply, after the model

Job `apply` in `agents.yml`, after the product owner job, in a fresh
checkout. It gets only `backlog.json`, as an artifact. `backlog.py apply`
first runs the sync, so issues filed during the run are on the board. Then
it validates against the live board, never against the state file, because
the model can change files in its own job.

Errors, which mean no change and a failed job:

- not JSON, larger than 64 KiB, or wrong shape (`order` a list of issue
  numbers, `stale` a list of `{n, reason}` with a non-empty reason),
- a number twice,
- a number not on the board,
- more than 10 `stale` entries.

Not errors, because the maintainer can move items during the run:

- numbers whose live status is not `Backlog` are dropped from `order`,
- live `Backlog` items missing from `order` keep their relative order at
  the end,
- `stale` entries for closed issues, for issues with `keep` and for issues
  that already have `stale-candidate` are skipped.

Actions:

1. If the order changed, set it with `updateProjectV2ItemPosition`, each
   item after the previous one. Only live `Backlog` items move, so `Next`
   stays as the maintainer left it.
2. For each `stale` entry, reason cut to 300 characters on one line:
   - author `claude[bot]`: comment `Stale: <reason>`, close as not planned.
   - other author: add label `stale-candidate`, comment `Stale candidate:
     <reason>`. Never close. The maintainer closes the issue, or removes the
     label and adds `keep`.

### 5.4 Docs

Update `agents/product-owner.md`, `agents/skills/backlog.md` and
`agents/CONTEXT.md`: the pick order is the board order; remove the
`priority: high` rules and the label-based pick order; add `stale-candidate`
and `keep` to the label tables.

## 6. Author lock and token expiry

New workflow `.github/workflows/repo-guard.yml`:

- Monthly cron and dispatch:
  - `PUT /repos/{owner}/{repo}/interaction-limits` with
    `limit: collaborators_only`, `expiry: six_months`. Token `GUARD_TOKEN`.
    Runs only while the repo variable `INTERACTION_LIMIT` is `true`, so
    that the fallback of B6 needs no code change.
  - Read the response header `github-authentication-token-expiration` for
    `BACKLOG_TOKEN` and `GUARD_TOKEN`. If one expires in 60 days or less and
    no open issue has the title `Renew <secret name>`, open one with labels
    `meta` and `ready-for-human`. Token `GITHUB_TOKEN`.
- On `issues: opened`: if the author is not in `BACKLOG_AUTHORS`, comment
  that the repo accepts issues only from the maintainer and its agents,
  close as not planned, lock. Token `GITHUB_TOKEN`.
- Sync and gate filter by author, see sections 4 and 5.1.

Effect of the interaction limit: non-collaborators can also not comment or
open pull requests.

## 7. Setup by the maintainer

1. Create the organization, the project, field values, built-in workflows.
2. Create both tokens, store them in environment `agents`.
3. Set the repo variables of section 3.
4. Rollout as in section 8, step 5.

## 8. Testing

1. Spike before the build: confirm that the GraphQL `items` connection
   returns items in manual board order, that `updateProjectV2ItemPosition`
   changes it, and that the fine-grained token reads full issue content of
   the user repo. If the order is not readable, this design stops and goes
   back to review.
2. Unit tests for parse, rank, pick, sync plan, plan check, final order,
   moves and stale rules, with recorded GraphQL nodes. Run in PR checks.
3. Local runs of gate, sync and apply against the real board.
4. End to end: dispatch product owner, then worker, with `AGENTS_ENABLED`
   off. Check the order on the board and the issue picked.
5. Interaction limit, with crons off: set the limit, then check that
   `claude[bot]` can file and comment (product owner run), that Dependabot
   can open a PR, and that `github-actions[bot]` can comment. If one is
   blocked: delete the limit, set `INTERACTION_LIMIT` to `false`.
6. Issue form: file an issue from a template, check it is on the board.
7. Foreign author: with the limit active, a second account cannot open an
   issue. Without the limit, an issue from a second account is closed and
   locked.
