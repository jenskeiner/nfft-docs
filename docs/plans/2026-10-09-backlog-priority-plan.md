# Maintainer-controlled backlog order: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Workers pick issues in the order of a GitHub Project board; the maintainer owns the `Next` column, the product owner orders `Backlog` and clears stale issues; only the maintainer and the agents add issues.

**Architecture:** One stdlib Python script, `.github/scripts/backlog.py`, holds the board logic as pure functions plus three subcommands: `gate`, `sync`, `apply`. Shell and workflows call it with a fine-grained token for the board, which belongs to the organization `nfft-docs-agents`. The model never holds a token: it writes `backlog.json`, and a separate job in a fresh checkout validates and applies it. A new workflow keeps non-collaborators out and warns before tokens expire.

**Tech Stack:** Python 3 stdlib, `gh` CLI (`gh api graphql`), GitHub Projects v2 GraphQL API, GitHub Actions, bash, `jq`.

**Spec:** `docs/plans/2026-10-09-backlog-priority-design.md`

## Global Constraints

- Only shell steps read `secrets.BACKLOG_TOKEN` and `secrets.GUARD_TOKEN`. Never pass them to `./.github/actions/agent-setup` or to any step after the model step in the same job.
- Board GraphQL calls use env `BOARD_TOKEN`. Issue edits (comment, label, close) use env `GH_TOKEN` = `github.token`, so they appear as `github-actions[bot]`, not as the maintainer.
- Repo variables: `BACKLOG_OWNER` (`nfft-docs-agents`), `BACKLOG_PROJECT` (project number), `BACKLOG_AUTHORS` (`jenskeiner claude[bot] github-actions[bot]`), `INTERACTION_LIMIT` (`true` or `false`). If one of the first three is empty, every subcommand exits 1. Never fall back to "all authors".
- Board queries use `organization(login: $owner)`, never `user(login:)`.
- Status values exactly `Next`, `Backlog`, `Done`.
- Agent author login: `claude[bot]`. GraphQL returns bots as `__typename: Bot`, `login: claude`; normalize to `claude[bot]`.
- Stale: at most 10 entries per run, reason at most 300 characters, whitespace collapsed. Issues labelled `keep` are never stale.
- Actions pinned by commit SHA with a version comment, as in the existing workflows.
- Commit messages: one sentence, imperative, no prefixes, no attribution lines.
- Prose in `agents/`: ASD-STE100, no special symbols, forbidden words: load-bearing, seam, byte-identical, odometer.
- Run `uvx zizmor==1.30.1 --no-progress --min-severity medium .github/` and `uvx --from actionlint-py==1.7.12.25 actionlint -no-color` after every workflow change. Both must pass.
- `P` below is the project number from Task 1.

## Review Focus

1. `BACKLOG_AUTHORS` unset or empty: the guard must not close the maintainer's issues, and the gate must not pick anything. Expect a failed job with a clear message. Tests: Task 2 (`test_env_requires_authors`), Task 6 (guard shell check).
2. The maintainer moves an issue from `Backlog` to `Next`, or closes it, while the product owner runs: `apply` must not fail and must not move it. Test: Task 4 (`test_final_order_drops_items_no_longer_in_backlog`).
3. Malformed `backlog.json` (not JSON, strings instead of numbers, duplicates, unknown numbers, 11 stale entries, empty reason, file over 64 KiB): no board change, job fails, message names the rule. Tests: Task 4 (`test_check_*`), Task 5 (`test_load_plan_rejects_large_and_broken_files`).
4. Weekly stale review reports the same maintainer issue again, or an issue labelled `keep`: no label, no comment. Test: Task 4 (`test_stale_skips_candidate_keep_and_closed`).
5. Board items that are pull requests, draft issues, issues of other repos, or issues by other authors: never picked, never moved. Tests: Task 2 (`test_parse_skips_non_issues`, `test_pick_skips_foreign_authors`).

## File structure

| File | Responsibility |
|------|----------------|
| `.github/scripts/backlog.py` | Create. Pure functions: parse, rank, pick, plan sync, check plan, final order, moves, stale actions. I/O: GraphQL and `gh issue`. CLI: `gate`, `sync`, `apply`. |
| `.github/scripts/test_backlog.py` | Create. Unit tests for the pure functions, run with `python3`. |
| `.github/scripts/agent-gate.sh` | Modify. Worker pick calls `backlog.py gate`. Product owner exempt from the PR cap. |
| `.github/workflows/agents.yml` | Modify. Gate env, sync step, upload step, `apply` job. |
| `.github/workflows/repo-guard.yml` | Create. Interaction limit, token expiry check, auto-close. |
| `.github/workflows/pr-checks.yml` | Modify. Run `test_backlog.py`. |
| `.github/ISSUE_TEMPLATE/*.yml` | Modify. `projects:` key. |
| `.gitignore` | Modify. Add `backlog.json`. |
| `agents/product-owner.md`, `agents/skills/backlog.md`, `agents/CONTEXT.md` | Modify. Board order, stale review, no `priority: high`. |

---

### Task 1: Board setup and spike

Throwaway probe. Nothing from this task is committed except the result line below.

**Files:** scratchpad only.

- [ ] **Step 1: Organization and board (maintainer, web UI)**

1. Create the free organization `nfft-docs-agents` (github.com/organizations/plan).
2. In the organization, create the project `NFFT docs backlog`. Note its number as `P`.
3. Project settings, field `Status`: options exactly `Next`, `Backlog`, `Done`, in this order. Delete the rest.
4. Project workflows: "Item closed" sets `Done`, on. "Auto-archive items" with filter `is:closed updated:<@today-14d`, on. "Auto-add to project", off. "Item added to project", off.
5. Add a board view grouped by `Status`, sorted manually.

- [ ] **Step 2: Board token (maintainer)**

Fine-grained token, resource owner `nfft-docs-agents`, expiry 1 year, repository access "Public repositories", organization permission Projects: read and write. Owner tokens are approved automatically. Keep it in the shell as `BOARD_TOKEN` for Tasks 1, 3 and 5.

- [ ] **Step 3: Probe the order**

Add three open issues of `jenskeiner/nfft-docs` in the web UI, one of them by `claude[bot]`, put them in `Backlog`, drag them to the order B, C, A. Then:

```bash
GH_TOKEN=$BOARD_TOKEN gh api graphql -F number=P -f query='
query($number:Int!){ organization(login:"nfft-docs-agents"){ projectV2(number:$number){ id
  items(first:100){ nodes{ id
    fieldValueByName(name:"Status"){ ... on ProjectV2ItemFieldSingleSelectValue{ name } }
    content{ __typename ... on Issue{ number title state repository{ nameWithOwner }
      author{ __typename login } labels(first:5){ nodes{ name } } } } } } } } }'
```

Expected: nodes in the order B, C, A, with full number, title, labels and author. Agent author: `{"__typename":"Bot","login":"claude"}`.

- [ ] **Step 4: Probe a move**

```bash
GH_TOKEN=$BOARD_TOKEN gh api graphql -f query='mutation($p:ID!,$i:ID!){ updateProjectV2ItemPosition(input:{projectId:$p,itemId:$i}){ clientMutationId } }' -f p=PROJECT_ID -f i=ITEM_ID_OF_A
```

Expected: A is first within `Backlog`, in the web UI and in the Step 3 query.

- [ ] **Step 5: Record the result**

If all probes pass, write one line under this task: `Spike result: order readable and writable, content complete, bot login claude.` If the order is not readable or content is redacted, stop and return to the maintainer: the design does not hold.

---

### Task 2: Board model and pick

**Files:**
- Create: `.github/scripts/backlog.py`
- Create: `.github/scripts/test_backlog.py`
- Modify: `.github/workflows/pr-checks.yml` (step after "Snippet lock")

**Interfaces:**
- Produces: `login(author: dict|None) -> str`, `parse_items(nodes: list, repo: str) -> list[Item]` where `Item = {"id": str, "n": int, "title": str, "open": bool, "status": str|None, "author": str, "labels": list[str]}`, `ranked(items, authors: set) -> list[Item]`, `why_not(item, roles, names: list[str]) -> str|None`, `pick(items, authors, roles: dict, want: str) -> tuple[tuple[int, str]|None, list[str]]` returning `(pick or None, skip lines for Next items)`, `env() -> tuple[str, int, set, str]` returning `(owner, project_number, authors, repo)`, owner from `BACKLOG_OWNER`.

- [ ] **Step 1: Write the failing tests**

`.github/scripts/test_backlog.py`:

```python
"""Checks for the backlog board logic. Run from the repository root:

    python3 .github/scripts/test_backlog.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backlog  # noqa: E402

REPO = "jenskeiner/nfft-docs"
AUTHORS = {"jenskeiner", "claude[bot]"}
ROLES = {
    "_comment": "x",
    "writer": {"types": ["gap", "new-section"]},
    "editor": {"types": ["style"]},
}


def node(n, status="Backlog", labels=("gap", "ready-for-agent"), author=("User", "jenskeiner"),
         state="OPEN", repo=REPO, kind="Issue"):
    return {
        "id": f"I{n}",
        "fieldValueByName": {"name": status} if status else None,
        "content": {
            "__typename": kind, "number": n, "title": f"t{n}", "state": state,
            "repository": {"nameWithOwner": repo},
            "author": {"__typename": author[0], "login": author[1]},
            "labels": {"nodes": [{"name": x} for x in labels]},
        },
    }


def items(*nodes):
    return backlog.parse_items(list(nodes), REPO)


def pick(*args):
    return backlog.pick(*args)[0]


def test_login_normalizes_bots():
    assert backlog.login({"__typename": "Bot", "login": "claude"}) == "claude[bot]"
    assert backlog.login({"__typename": "User", "login": "jenskeiner"}) == "jenskeiner"
    assert backlog.login(None) == ""


def test_parse_skips_non_issues():
    got = items(node(1), node(2, kind="PullRequest"), node(3, repo="other/repo"),
                {"id": "D", "fieldValueByName": None, "content": {"__typename": "DraftIssue"}})
    assert [i["n"] for i in got] == [1], got


def test_ranked_puts_next_first_in_board_order():
    got = backlog.ranked(items(node(1), node(2, "Next"), node(3), node(4, "Next"),
                               node(5, "Done"), node(6, None)), AUTHORS)
    assert [i["n"] for i in got] == [2, 4, 1, 3], got


def test_pick_takes_next_before_backlog():
    assert pick(items(node(1), node(2, "Next")), AUTHORS, ROLES, "worker") == (2, "writer")


def test_pick_skips_unready_claimed_blocked_untriaged():
    got = pick(items(
        node(1, "Next", labels=("gap",)),
        node(2, "Next", labels=("gap", "ready-for-agent", "in-progress")),
        node(3, "Next", labels=("gap", "ready-for-agent", "blocked")),
        node(4, "Next", labels=("gap", "ready-for-agent", "needs-triage")),
        node(5, "Next", state="CLOSED"),
        node(6, "Backlog", labels=("style", "ready-for-agent")),
    ), AUTHORS, ROLES, "worker")
    assert got == (6, "editor"), got


def test_pick_skips_foreign_authors():
    got = pick(items(node(1, "Next", author=("User", "stranger")), node(2)),
                       AUTHORS, ROLES, "worker")
    assert got == (2, "writer"), got


def test_pick_skips_types_without_role():
    got = pick(items(node(1, "Next", labels=("meta", "ready-for-agent")), node(2)),
                       AUTHORS, ROLES, "worker")
    assert got == (2, "writer"), got


def test_pick_named_role():
    got = pick(items(node(1, "Next"), node(2, labels=("style", "ready-for-agent"))),
                       AUTHORS, ROLES, "editor")
    assert got == (2, "editor"), got


def test_pick_none():
    assert pick(items(node(1, labels=("gap",))), AUTHORS, ROLES, "worker") is None


def test_pick_logs_skipped_next_items():
    got, skipped = backlog.pick(items(
        node(1, "Next", labels=("gap",)),
        node(2, "Next", labels=("meta", "ready-for-agent")),
        node(3, "Next", labels=("gap", "ready-for-agent", "blocked")),
        node(4, "Backlog", labels=("gap",)),
        node(5)), AUTHORS, ROLES, "worker")
    assert got == (5, "writer"), got
    assert skipped == ["skip #1: not ready-for-agent", "skip #2: no role for its type",
                       "skip #3: labelled blocked"], skipped


def test_pick_accepts_bot_author():
    got = pick(items(node(1, author=("Bot", "claude"))), AUTHORS, ROLES, "worker")
    assert got == (1, "writer"), got


def test_env_requires_authors():
    saved = dict(os.environ)
    try:
        os.environ.update(GITHUB_REPOSITORY=REPO, BACKLOG_OWNER="nfft-docs-agents",
                          BACKLOG_PROJECT="3", BACKLOG_AUTHORS=" ")
        try:
            backlog.env()
        except SystemExit as e:
            assert "BACKLOG_AUTHORS" in str(e.code), e.code
        else:
            raise AssertionError("no exit")
        os.environ["BACKLOG_AUTHORS"] = "jenskeiner claude[bot]"
        assert backlog.env() == ("nfft-docs-agents", 3, AUTHORS, REPO)
        os.environ["BACKLOG_OWNER"] = ""
        try:
            backlog.env()
        except SystemExit as e:
            assert "BACKLOG_OWNER" in str(e.code), e.code
        else:
            raise AssertionError("no exit")
    finally:
        os.environ.clear()
        os.environ.update(saved)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
```

- [ ] **Step 2: Run the tests, expect failure**

Run: `python3 .github/scripts/test_backlog.py`
Expected: `ModuleNotFoundError: No module named 'backlog'`

- [ ] **Step 3: Write the module**

`.github/scripts/backlog.py`:

```python
#!/usr/bin/env python3
"""Backlog board for the agents. Run from the repository root:

    python3 .github/scripts/backlog.py gate <worker|role>
    python3 .github/scripts/backlog.py sync
    python3 .github/scripts/backlog.py apply <backlog.json>

The board is an organization project with Status Next, Backlog, Done. Next
belongs to the maintainer, Backlog to the product owner. Board calls use
BOARD_TOKEN, issue edits use GH_TOKEN. Needs BACKLOG_OWNER, BACKLOG_PROJECT,
BACKLOG_AUTHORS and GITHUB_REPOSITORY.
"""

import json
import os
import subprocess
import sys

SKIP = {"in-progress", "blocked", "needs-triage"}


def env():
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    owner = os.environ.get("BACKLOG_OWNER", "").strip()
    project = os.environ.get("BACKLOG_PROJECT", "").strip()
    authors = set(os.environ.get("BACKLOG_AUTHORS", "").split())
    for name, value in (("GITHUB_REPOSITORY", repo), ("BACKLOG_OWNER", owner),
                        ("BACKLOG_PROJECT", project), ("BACKLOG_AUTHORS", authors)):
        if not value:
            sys.exit(f"{name} is not set")
    return owner, int(project), authors, repo


def login(author):
    if not author:
        return ""
    name = author["login"]
    if author["__typename"] == "Bot" and not name.endswith("[bot]"):
        name += "[bot]"
    return name


def parse_items(nodes, repo):
    out = []
    for node in nodes:
        c = node.get("content") or {}
        if c.get("__typename") != "Issue" or c["repository"]["nameWithOwner"] != repo:
            continue
        out.append({
            "id": node["id"], "n": c["number"], "title": c["title"],
            "open": c["state"] == "OPEN",
            "status": (node.get("fieldValueByName") or {}).get("name"),
            "author": login(c.get("author")),
            "labels": [x["name"] for x in c["labels"]["nodes"]],
        })
    return out


def ranked(items, authors):
    ok = [i for i in items if i["open"] and i["author"] in authors]
    return [i for i in ok if i["status"] == "Next"] + [i for i in ok if i["status"] == "Backlog"]


def why_not(item, roles, names):
    labels = set(item["labels"])
    if "ready-for-agent" not in labels:
        return "not ready-for-agent"
    if labels & SKIP:
        return "labelled " + ", ".join(sorted(labels & SKIP))
    if not any(labels & set(roles[r]["types"]) for r in names):
        return "no role for its type"
    return None


def pick(items, authors, roles, want):
    names = [r for r in roles if r != "_comment"] if want == "worker" else [want]
    skipped = []
    for item in ranked(items, authors):
        reason = why_not(item, roles, names)
        if reason is None:
            role = next(r for r in names if set(item["labels"]) & set(roles[r]["types"]))
            return (item["n"], role), skipped
        if item["status"] == "Next":
            skipped.append(f"skip #{item['n']}: {reason}")
    return None, skipped
```

- [ ] **Step 4: Run the tests, expect pass**

Run: `python3 .github/scripts/test_backlog.py`
Expected: one `ok test_...` line per test, exit 0.

- [ ] **Step 5: Run the tests in PR checks**

In `.github/workflows/pr-checks.yml`, after the step "Snippet lock", add:

```yaml
      - name: Backlog board logic
        run: python3 .github/scripts/test_backlog.py
```

Run the two workflow linters from Global Constraints. Expected: no findings.

- [ ] **Step 6: Commit**

```bash
git add .github/scripts/backlog.py .github/scripts/test_backlog.py .github/workflows/pr-checks.yml
git commit -m "Add the board model and pick order for the backlog."
```

---

### Task 3: Board I/O, gate subcommand, gate wiring

**Files:**
- Modify: `.github/scripts/backlog.py` (append)
- Modify: `.github/scripts/agent-gate.sh:28-57`
- Modify: `.github/workflows/agents.yml` (step "Gate")

**Interfaces:**
- Consumes: `env`, `parse_items`, `pick` from Task 2.
- Produces: `graphql(query: str, **variables) -> dict` (the `data` object; exits 1 on error), `read_board(owner, number, repo) -> tuple[str, str, dict[str, str], list[Item]]` returning `(project_id, status_field_id, {option name: option id}, items)`, `main(argv)` dispatching subcommands. CLI `gate <want>` prints `<n>\t<role>` or nothing to stdout and the skip lines to stderr, exit 0; exit 1 on board error.

- [ ] **Step 1: Write the failing test**

Append to `test_backlog.py` before the `__main__` block:

```python
def test_main_rejects_unknown_command():
    try:
        backlog.main(["nope"])
    except SystemExit as e:
        assert "usage" in str(e.code), e.code
    else:
        raise AssertionError("no exit")
```

- [ ] **Step 2: Run, expect failure**

Run: `python3 .github/scripts/test_backlog.py`
Expected: `AttributeError: module 'backlog' has no attribute 'main'`

- [ ] **Step 3: Write the I/O and CLI**

Append to `backlog.py`:

```python
BOARD = """
query($owner: String!, $number: Int!, $cursor: String) {
  organization(login: $owner) { projectV2(number: $number) {
    id
    field(name: "Status") { ... on ProjectV2SingleSelectField { id options { id name } } }
    items(first: 100, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        fieldValueByName(name: "Status") { ... on ProjectV2ItemFieldSingleSelectValue { name } }
        content { __typename ... on Issue {
          number title state repository { nameWithOwner }
          author { __typename login } labels(first: 50) { nodes { name } } } }
      }
    }
  } }
}
"""


def graphql(query, **variables):
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        if value is not None:
            cmd += ["-F" if isinstance(value, int) else "-f", f"{key}={value}"]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       env={**os.environ, "GH_TOKEN": os.environ.get("BOARD_TOKEN", "")})
    if r.returncode:
        sys.exit(f"board: {r.stderr.strip() or r.stdout.strip()}")
    return json.loads(r.stdout)["data"]


def read_board(owner, number, repo):
    nodes, cursor = [], None
    while True:
        org = graphql(BOARD, owner=owner, number=number, cursor=cursor)["organization"]
        project = org and org["projectV2"]
        if not project:
            sys.exit(f"board: project {number} of {owner} not found")
        nodes += project["items"]["nodes"]
        page = project["items"]["pageInfo"]
        if not page["hasNextPage"]:
            break
        cursor = page["endCursor"]
    field = project["field"]
    if not field:
        sys.exit("board: field Status not found")
    options = {o["name"]: o["id"] for o in field["options"]}
    missing = {"Next", "Backlog", "Done"} - set(options)
    if missing:
        sys.exit(f"board: Status lacks {sorted(missing)}")
    return project["id"], field["id"], options, parse_items(nodes, repo)


def cmd_gate(want):
    owner, number, authors, repo = env()
    with open("agents/roles.json") as fh:
        roles = json.load(fh)
    got, skipped = pick(read_board(owner, number, repo)[3], authors, roles, want)
    for line in skipped:
        print(line, file=sys.stderr)
    if got:
        print(f"{got[0]}\t{got[1]}")


def main(argv):
    if len(argv) == 2 and argv[0] == "gate":
        return cmd_gate(argv[1])
    sys.exit("usage: backlog.py gate <worker|role> | sync | apply <backlog.json>")


if __name__ == "__main__":
    main(sys.argv[1:])
```

- [ ] **Step 4: Run, expect pass**

Run: `python3 .github/scripts/test_backlog.py`
Expected: all `ok`, exit 0.

- [ ] **Step 5: Replace the label sort in the gate**

In `.github/scripts/agent-gate.sh`, replace everything from the comment `# Worker, or a named worker role from a dispatch:` to the end of the file with:

```bash
# Worker, or a named worker role from a dispatch: the first ready issue on the
# board, Next before Backlog, in board order, whose type a role handles.
if [ "$want" != worker ]; then
  jq -e --arg r "$want" '.[$r]' "$roles" >/dev/null || { echo "unknown role $want" >&2; exit 1; }
fi
if ! pick=$(python3 .github/scripts/backlog.py gate "$want"); then
  echo "run=false" >> "$out"; echo "board read failed" >&2; exit 1
fi
[ -n "$pick" ] || say "no ready issue for $want" false
issue=$(cut -f1 <<<"$pick"); role=$(cut -f2 <<<"$pick")
{
  echo "role=$role"
  echo "model=$(jq -r --arg r "$role" '.[$r].model' "$roles")"
  echo "max_turns=$(jq -r --arg r "$role" '.[$r].max_turns' "$roles")"
  echo "issue=$issue"
} >> "$out"
say "go: $role on issue #$issue" true
```

- [ ] **Step 6: Exempt the product owner from the cap**

In `.github/scripts/agent-gate.sh`, replace

```bash
if [ "$want" != analyst ] && [ "$open" -ge "$cap" ]; then
```

with

```bash
# The product owner opens at most its housekeeping PR, under its own rule.
if [ "$want" != analyst ] && [ "$want" != product-owner ] && [ "$open" -ge "$cap" ]; then
```

- [ ] **Step 7: Give the gate the board**

In `.github/workflows/agents.yml`, step `Gate`:

```yaml
      - name: Gate
        id: gate
        env:
          BOARD_TOKEN: ${{ secrets.BACKLOG_TOKEN }}
          BACKLOG_OWNER: ${{ vars.BACKLOG_OWNER }}
          BACKLOG_PROJECT: ${{ vars.BACKLOG_PROJECT }}
          BACKLOG_AUTHORS: ${{ vars.BACKLOG_AUTHORS }}
        run: bash .github/scripts/agent-gate.sh "${{ steps.want.outputs.want }}"
```

Run the two workflow linters. Expected: no findings.

- [ ] **Step 8: Local check against the real board**

```bash
GITHUB_REPOSITORY=jenskeiner/nfft-docs BACKLOG_OWNER=nfft-docs-agents BACKLOG_PROJECT=P \
BACKLOG_AUTHORS="jenskeiner claude[bot] github-actions[bot]" BOARD_TOKEN=$BOARD_TOKEN GITHUB_OUTPUT=/dev/stdout bash .github/scripts/agent-gate.sh worker
```

Expected: the cap line, or `go: <role> on issue #<n>` for the first ready item from Task 1, or `no ready issue for worker`, with a `skip #<n>: <reason>` line for each `Next` item passed over. Then with `BACKLOG_PROJECT=999`: `run=false`, `board read failed`, exit 1.

- [ ] **Step 9: Commit**

```bash
git add .github/scripts/backlog.py .github/scripts/test_backlog.py .github/scripts/agent-gate.sh .github/workflows/agents.yml
git commit -m "Pick the next issue from the backlog board in the gate."
```

---

### Task 4: Plan check, final order, stale actions

**Files:**
- Modify: `.github/scripts/backlog.py` (insert pure functions after `pick`)
- Modify: `.github/scripts/test_backlog.py`

**Interfaces:**
- Consumes: `Item`, `ranked` from Task 2.
- Produces: `AGENT = "claude[bot]"`, `MAX_STALE = 10`, `MAX_REASON = 300`, `MAX_BYTES = 65536`, `check(plan, items) -> list[str]` (errors, empty when valid), `final_order(order: list[int], items, authors) -> list[Item]`, `moves(items, authors, final: list[Item]) -> list[tuple[str, str|None]]` (`(item_id, after_id)`), `stale_actions(stale: list[dict], items) -> list[tuple[str, int, str]]` with kinds `"close"` and `"label"`, `plan_sync(items, issues: list[dict], authors) -> tuple[list[dict], list[Item]]` where `issues` are `{"n": int, "id": str, "author": str}` (node id of the issue).

- [ ] **Step 1: Write the failing tests**

Append to `test_backlog.py` before the `__main__` block:

```python
def board(*specs):
    return items(*[node(n, s, author=a) for n, s, a in specs])


U, B = ("User", "jenskeiner"), ("Bot", "claude")


def test_check_accepts_valid_plan():
    its = board((1, "Backlog", U), (2, "Next", U))
    assert backlog.check({"order": [1], "stale": [{"n": 2, "reason": "done"}]}, its) == []


def test_check_rejects_bad_shapes():
    its = board((1, "Backlog", U))
    for plan in ([1], {"order": "1"}, {"order": ["1"]}, {"order": [True]},
                 {"order": [1], "extra": 1}, {"order": [1], "stale": [{"n": 1}]},
                 {"order": [1], "stale": [{"n": 1, "reason": " "}]}):
        assert backlog.check(plan, its), plan


def test_check_rejects_duplicates_and_unknown():
    its = board((1, "Backlog", U), (2, "Backlog", U))
    assert any("duplicate" in e for e in backlog.check({"order": [1, 1, 2]}, its))
    assert any("not on the board" in e for e in backlog.check({"order": [1, 2, 9]}, its))
    assert any("not on the board" in e for e in
               backlog.check({"order": [1, 2], "stale": [{"n": 9, "reason": "x"}]}, its))


def test_check_limits_stale():
    its = board(*[(n, "Backlog", B) for n in range(1, 13)])
    plan = {"order": list(range(1, 13)), "stale": [{"n": n, "reason": "x"} for n in range(1, 12)]}
    assert any("at most 10" in e for e in backlog.check(plan, its))


def test_final_order_follows_plan_and_appends_missing():
    its = board((1, "Backlog", U), (2, "Backlog", U), (3, "Backlog", U), (4, "Backlog", U))
    got = backlog.final_order([3, 1], its, AUTHORS)
    assert [i["n"] for i in got] == [3, 1, 2, 4], got


def test_final_order_drops_items_no_longer_in_backlog():
    its = board((1, "Next", U), (2, "Backlog", U), (3, "Done", U))
    got = backlog.final_order([1, 3, 2], its, AUTHORS)
    assert [i["n"] for i in got] == [2], got


def test_moves_empty_when_order_unchanged():
    its = board((1, "Next", U), (2, "Backlog", U), (3, "Backlog", U))
    assert backlog.moves(its, AUTHORS, backlog.final_order([2, 3], its, AUTHORS)) == []


def test_moves_chain_backlog_only():
    its = board((1, "Next", U), (2, "Backlog", U), (3, "Backlog", U))
    got = backlog.moves(its, AUTHORS, backlog.final_order([3, 2], its, AUTHORS))
    assert got == [("I3", None), ("I2", "I3")], got


def test_stale_closes_agent_issues_and_labels_others():
    its = board((1, "Backlog", B), (2, "Next", U))
    got = backlog.stale_actions([{"n": 1, "reason": "a\n  b"}, {"n": 2, "reason": "c"}], its)
    assert got == [("close", 1, "a b"), ("label", 2, "c")], got


def test_stale_skips_candidate_keep_and_closed():
    its = items(node(1, labels=("gap", "stale-candidate")), node(2, state="CLOSED", author=B),
                node(3, labels=("gap", "keep"), author=B))
    stale = [{"n": n, "reason": "x"} for n in (1, 2, 3)]
    assert backlog.stale_actions(stale, its) == []


def test_stale_truncates_reason():
    its = board((1, "Backlog", B))
    got = backlog.stale_actions([{"n": 1, "reason": "x" * 400}], its)
    assert len(got[0][2]) == 300, got


def test_plan_sync_adds_missing_and_fixes_empty_status():
    its = board((1, "Backlog", U), (2, None, U))
    issues = [{"n": 1, "id": "N1", "author": "jenskeiner"},
              {"n": 3, "id": "N3", "author": "claude[bot]"},
              {"n": 4, "id": "N4", "author": "stranger"}]
    add, unset = backlog.plan_sync(its, issues, AUTHORS)
    assert [x["n"] for x in add] == [3] and [i["n"] for i in unset] == [2], (add, unset)
```

- [ ] **Step 2: Run, expect failure**

Run: `python3 .github/scripts/test_backlog.py`
Expected: `AttributeError: module 'backlog' has no attribute 'check'`

- [ ] **Step 3: Write the functions**

Insert into `backlog.py` after `pick`; add the constants below `SKIP`:

```python
AGENT = "claude[bot]"
MAX_STALE = 10
MAX_REASON = 300
MAX_BYTES = 65536
```

```python
def _is_num(x):
    return type(x) is int


def check(plan, items):
    if not isinstance(plan, dict) or set(plan) - {"order", "stale"} or "order" not in plan:
        return ["backlog.json must be an object with keys order and stale"]
    order, stale = plan["order"], plan.get("stale", [])
    if not isinstance(order, list) or not all(_is_num(n) for n in order):
        return ["order must be a list of issue numbers"]
    if not isinstance(stale, list) or not all(
            isinstance(s, dict) and set(s) == {"n", "reason"} and _is_num(s["n"])
            and isinstance(s["reason"], str) and s["reason"].strip() for s in stale):
        return ["stale must be a list of {n, reason} with a non-empty reason"]
    errors = []
    known = {i["n"] for i in items}
    nums = order + [s["n"] for s in stale]
    dups = sorted({n for n in order if order.count(n) > 1}
                  | {s["n"] for s in stale if [t["n"] for t in stale].count(s["n"]) > 1})
    if dups:
        errors.append(f"duplicate numbers: {dups}")
    unknown = sorted(set(nums) - known)
    if unknown:
        errors.append(f"not on the board: {unknown}")
    if len(stale) > MAX_STALE:
        errors.append(f"stale has {len(stale)} entries, at most {MAX_STALE}")
    return errors


def final_order(order, items, authors):
    backlog = [i for i in ranked(items, authors) if i["status"] == "Backlog"]
    by_n = {i["n"]: i for i in backlog}
    head = [by_n[n] for n in order if n in by_n]
    listed = {i["n"] for i in head}
    return head + [i for i in backlog if i["n"] not in listed]


def moves(items, authors, final):
    current = [i["id"] for i in ranked(items, authors) if i["status"] == "Backlog"]
    wanted = [i["id"] for i in final]
    if current == wanted:
        return []
    out, prev = [], None
    for item_id in wanted:
        out.append((item_id, prev))
        prev = item_id
    return out


def stale_actions(stale, items):
    by_n = {i["n"]: i for i in items}
    out = []
    for s in stale:
        item = by_n[s["n"]]
        if not item["open"] or {"stale-candidate", "keep"} & set(item["labels"]):
            continue
        reason = " ".join(s["reason"].split())[:MAX_REASON]
        out.append(("close" if item["author"] == AGENT else "label", s["n"], reason))
    return out


def plan_sync(items, issues, authors):
    on_board = {i["n"] for i in items}
    add = [x for x in issues if x["author"] in authors and x["n"] not in on_board]
    unset = [i for i in items if i["open"] and i["status"] is None and i["author"] in authors]
    return add, unset
```

- [ ] **Step 4: Run, expect pass**

Run: `python3 .github/scripts/test_backlog.py`
Expected: all `ok`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add .github/scripts/backlog.py .github/scripts/test_backlog.py
git commit -m "Add plan validation, final order and stale rules for the backlog."
```

---

### Task 5: Sync and apply subcommands, workflow wiring

**Files:**
- Modify: `.github/scripts/backlog.py` (I/O and CLI)
- Modify: `.github/workflows/agents.yml`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `read_board`, `graphql`, `env` (Task 3); `plan_sync`, `check`, `final_order`, `moves`, `stale_actions`, `ranked`, `MAX_BYTES` (Task 4).
- Produces: CLI `sync` prints the state JSON `{"next": [...], "backlog": [...], "stale_review": bool}` (rows `{"n", "title", "author", "labels"}`) to stdout. CLI `apply <path>` exits 0 after applying, 1 with `invalid backlog.json: ...` or a board error. Artifact name `backlog-plan` holding `backlog.json`. Job output `role.outputs.po` (`"true"`/`"false"`).

- [ ] **Step 1: Write the failing test**

Append to `test_backlog.py` before the `__main__` block:

```python
def test_state_rows_and_stale_review():
    import datetime
    its = board((1, "Backlog", U), (2, "Next", B), (3, "Done", U))
    got = backlog.state(its, AUTHORS, datetime.date(2026, 10, 12))
    assert [r["n"] for r in got["next"]] == [2] and [r["n"] for r in got["backlog"]] == [1]
    assert got["next"][0] == {"n": 2, "title": "t2", "author": "claude[bot]",
                              "labels": ["gap", "ready-for-agent"]}, got
    assert got["stale_review"] is True
    assert backlog.state(its, AUTHORS, datetime.date(2026, 10, 13))["stale_review"] is False


def test_load_plan_rejects_large_and_broken_files():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "backlog.json")
        for content in ("{", " " * (backlog.MAX_BYTES + 1)):
            with open(p, "w") as fh:
                fh.write(content)
            try:
                backlog.load_plan(p)
            except SystemExit as e:
                assert "invalid backlog.json" in str(e.code), e.code
            else:
                raise AssertionError(content[:5])
        try:
            backlog.load_plan(os.path.join(d, "missing.json"))
        except SystemExit as e:
            assert "invalid backlog.json" in str(e.code), e.code
```

- [ ] **Step 2: Run, expect failure**

Run: `python3 .github/scripts/test_backlog.py`
Expected: `AttributeError: module 'backlog' has no attribute 'state'`

- [ ] **Step 3: Write state, load_plan, sync, apply**

Add `import datetime` to the imports of `backlog.py`. Insert after `plan_sync`:

```python
def state(items, authors, today):
    def row(i):
        return {"n": i["n"], "title": i["title"], "author": i["author"], "labels": i["labels"]}
    r = ranked(items, authors)
    return {"next": [row(i) for i in r if i["status"] == "Next"],
            "backlog": [row(i) for i in r if i["status"] == "Backlog"],
            "stale_review": today.isoweekday() == 1}


def load_plan(path):
    try:
        if os.path.getsize(path) > MAX_BYTES:
            sys.exit(f"invalid backlog.json: larger than {MAX_BYTES} bytes")
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError) as e:
        sys.exit(f"invalid backlog.json: {e}")
```

Insert after `read_board`:

```python
ISSUES = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    issues(states: OPEN, first: 100, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes { id number author { __typename login } }
    }
  }
}
"""

ADD = """
mutation($p: ID!, $c: ID!) { addProjectV2ItemById(input: {projectId: $p, contentId: $c}) { item { id } } }
"""

SET_STATUS = """
mutation($p: ID!, $i: ID!, $f: ID!, $o: String!) {
  updateProjectV2ItemFieldValue(input: {projectId: $p, itemId: $i, fieldId: $f,
    value: {singleSelectOptionId: $o}}) { projectV2Item { id } }
}
"""

MOVE = """
mutation($p: ID!, $i: ID!, $a: ID) {
  updateProjectV2ItemPosition(input: {projectId: $p, itemId: $i, afterId: $a}) { clientMutationId }
}
"""


def open_issues(repo):
    owner, name = repo.split("/")
    out, cursor = [], None
    while True:
        page = graphql(ISSUES, owner=owner, name=name, cursor=cursor)["repository"]["issues"]
        out += [{"n": x["number"], "id": x["id"], "author": login(x["author"])}
                for x in page["nodes"]]
        if not page["pageInfo"]["hasNextPage"]:
            return out
        cursor = page["pageInfo"]["endCursor"]


def sync():
    owner, number, authors, repo = env()
    project, field, options, items = read_board(owner, number, repo)
    add, unset = plan_sync(items, open_issues(repo), authors)
    for x in add:
        item = graphql(ADD, p=project, c=x["id"])["addProjectV2ItemById"]["item"]["id"]
        graphql(SET_STATUS, p=project, i=item, f=field, o=options["Backlog"])
    for i in unset:
        graphql(SET_STATUS, p=project, i=i["id"], f=field, o=options["Backlog"])
    if add or unset:
        items = read_board(owner, number, repo)[3]
    return project, authors, items


def issue(*args):
    r = subprocess.run(["gh", "issue", *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"gh issue {args[0]}: {r.stderr.strip()}")


def cmd_sync():
    _, authors, items = sync()
    print(json.dumps(state(items, authors, datetime.datetime.now(datetime.timezone.utc).date()),
                     indent=1))


def cmd_apply(path):
    plan = load_plan(path)
    project, authors, items = sync()
    errors = check(plan, items)
    if errors:
        sys.exit("invalid backlog.json: " + "; ".join(errors))
    steps = moves(items, authors, final_order(plan["order"], items, authors))
    for item_id, after in steps:
        graphql(MOVE, p=project, i=item_id, a=after)
    print(f"moved {len(steps)} items")
    for kind, n, reason in stale_actions(plan.get("stale", []), items):
        if kind == "close":
            issue("close", str(n), "--reason", "not planned", "--comment", f"Stale: {reason}")
        else:
            issue("edit", str(n), "--add-label", "stale-candidate")
            issue("comment", str(n), "--body", f"Stale candidate: {reason}")
        print(f"{kind} #{n}: {reason}")
```

Replace `main`:

```python
def main(argv):
    if len(argv) == 2 and argv[0] == "gate":
        return cmd_gate(argv[1])
    if argv == ["sync"]:
        return cmd_sync()
    if len(argv) == 2 and argv[0] == "apply":
        return cmd_apply(argv[1])
    sys.exit("usage: backlog.py gate <worker|role> | sync | apply <backlog.json>")
```

- [ ] **Step 4: Run, expect pass**

Run: `python3 .github/scripts/test_backlog.py`
Expected: all `ok`, exit 0.

- [ ] **Step 5: Wire the workflow**

`.gitignore`: add a line `backlog.json`.

`.github/workflows/agents.yml`:

1. Under `jobs.role`, after `runs-on`, add:

```yaml
    outputs:
      po: ${{ steps.gate.outputs.run == 'true' && steps.gate.outputs.role == 'product-owner' }}
```

2. Between `Gate` and `Run the role`, add:

```yaml
      # Runs before the model, which never sees BACKLOG_TOKEN.
      - name: Sync the board
        id: sync
        if: steps.gate.outputs.run == 'true' && steps.gate.outputs.role == 'product-owner'
        env:
          BOARD_TOKEN: ${{ secrets.BACKLOG_TOKEN }}
          BACKLOG_OWNER: ${{ vars.BACKLOG_OWNER }}
          BACKLOG_PROJECT: ${{ vars.BACKLOG_PROJECT }}
          BACKLOG_AUTHORS: ${{ vars.BACKLOG_AUTHORS }}
        run: |
          python3 .github/scripts/backlog.py sync > "$RUNNER_TEMP/state.json"
          # Issue titles are in the state; a random delimiter cannot occur there.
          eof="STATE_$(openssl rand -hex 16)"
          {
            echo "prompt<<$eof"
            echo "## Backlog state"
            echo
            cat "$RUNNER_TEMP/state.json"
            echo "$eof"
          } >> "$GITHUB_OUTPUT"
```

3. In `Run the role`, set:

```yaml
          extra_prompt: "${{ steps.gate.outputs.issue && format('Work issue number {0}. It was chosen by the gate; skip the pick.', steps.gate.outputs.issue) || steps.sync.outputs.prompt || '' }}"
```

4. After `Run the role`, add:

```yaml
      - name: Keep the backlog plan
        if: always() && steps.sync.outcome == 'success'
        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: backlog-plan
          path: backlog.json
          if-no-files-found: ignore
          retention-days: 14
```

5. New job after `role`:

```yaml
  # A fresh checkout: nothing the model wrote runs here except backlog.json,
  # which is data and is validated against the live board.
  apply:
    name: apply backlog plan
    needs: role
    if: always() && needs.role.outputs.po == 'true'
    runs-on: ubuntu-latest
    environment: agents
    permissions:
      contents: read
      issues: write
    env:
      GH_TOKEN: ${{ github.token }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v6
        with:
          persist-credentials: false

      - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
        with:
          name: backlog-plan
          path: ${{ runner.temp }}/plan

      - name: Apply the plan
        env:
          BOARD_TOKEN: ${{ secrets.BACKLOG_TOKEN }}
          BACKLOG_OWNER: ${{ vars.BACKLOG_OWNER }}
          BACKLOG_PROJECT: ${{ vars.BACKLOG_PROJECT }}
          BACKLOG_AUTHORS: ${{ vars.BACKLOG_AUTHORS }}
        run: python3 .github/scripts/backlog.py apply "$RUNNER_TEMP/plan/backlog.json"
```

A missing artifact fails the download step. That is wanted: the product owner ran and wrote no plan.

Run the two workflow linters. Expected: no findings.

- [ ] **Step 6: Local check of sync against the real board**

```bash
GITHUB_REPOSITORY=jenskeiner/nfft-docs BACKLOG_OWNER=nfft-docs-agents BACKLOG_PROJECT=P \
BACKLOG_AUTHORS="jenskeiner claude[bot] github-actions[bot]" BOARD_TOKEN=$BOARD_TOKEN python3 .github/scripts/backlog.py sync
```

Expected: every open issue by the three authors now on the board, JSON with `next`, `backlog`, `stale_review`. This is an outward action on the board; confirm with the maintainer first.

- [ ] **Step 7: Local check of apply**

Write a scratchpad `backlog.json` with the current backlog order reversed and `"stale": []`, run `backlog.py apply <path>`. Expected: `moved N items`, board shows the reversed `Backlog`, `Next` unchanged. Run again with `{"order": [99999]}`. Expected: exit 1, `invalid backlog.json: not on the board: [99999]`, no board change.

- [ ] **Step 8: Commit**

```bash
git add .github/scripts/backlog.py .github/scripts/test_backlog.py .github/workflows/agents.yml .gitignore
git commit -m "Sync the board before the product owner and apply its plan after."
```

---

### Task 6: Repo guard

**Files:**
- Create: `.github/workflows/repo-guard.yml`

- [ ] **Step 1: Write the workflow**

```yaml
name: Repo guard

# Only the maintainer and the agents add issues. The interaction limit keeps
# non-collaborators out; it expires after six months, so a monthly run renews
# it. The same run warns before a token expires. An issue by any other author
# is closed and locked when it opens.
on:
  schedule:
    - cron: "0 4 1 * *"
  workflow_dispatch:
  issues:
    types: [opened]

permissions: {}

jobs:
  monthly:
    name: interaction limit and token expiry
    if: github.event_name != 'issues'
    runs-on: ubuntu-latest
    environment: agents
    permissions:
      issues: write
    steps:
      # INTERACTION_LIMIT is false if the limit blocks the agent bots.
      - name: Collaborators only, six months
        if: vars.INTERACTION_LIMIT == 'true'
        env:
          GH_TOKEN: ${{ secrets.GUARD_TOKEN }}
        run: |
          gh api -X PUT "repos/$GITHUB_REPOSITORY/interaction-limits" \
            -f limit=collaborators_only -f expiry=six_months

      - name: Warn 60 days before a token expires
        env:
          GH_TOKEN: ${{ github.token }}
          BACKLOG_TOKEN: ${{ secrets.BACKLOG_TOKEN }}
          GUARD_TOKEN: ${{ secrets.GUARD_TOKEN }}
        run: |
          warn() {
            title="Renew $1"
            if [ "$(gh issue list --repo "$GITHUB_REPOSITORY" --state open \
                  --search "in:title \"$title\"" --json title \
                  --jq "[.[] | select(.title == \"$title\")] | length")" -gt 0 ]; then
              echo "$title: issue already open"; return
            fi
            gh issue create --repo "$GITHUB_REPOSITORY" --title "$title" \
              --label meta --label ready-for-human \
              --body "Secret \`$1\` in environment \`agents\`: $2. Create a new fine-grained token with the same resource owner, repository access and permissions, 1 year expiry, and store it under the same name."
          }
          for name in BACKLOG_TOKEN GUARD_TOKEN; do
            token=${!name}
            if ! head=$(GH_TOKEN=$token gh api -i /rate_limit 2>&1); then
              warn "$name" "the API rejects it"; continue
            fi
            exp=$(printf '%s\n' "$head" | tr -d '\r' \
              | awk -F': ' 'tolower($1) == "github-authentication-token-expiration" { print $2 }')
            if [ -z "$exp" ]; then echo "$name: no expiry"; continue; fi
            days=$(( ($(date -u -d "$exp" +%s) - $(date -u +%s)) / 86400 ))
            echo "$name: expires $exp, in $days days"
            if [ "$days" -le 60 ]; then warn "$name" "expires $exp"; fi
          done

  close:
    name: close foreign issue
    if: github.event_name == 'issues'
    runs-on: ubuntu-latest
    permissions:
      issues: write
    steps:
      - name: Close issues by other authors
        env:
          GH_TOKEN: ${{ github.token }}
          AUTHOR: ${{ github.event.issue.user.login }}
          AUTHORS: ${{ vars.BACKLOG_AUTHORS }}
          N: ${{ github.event.issue.number }}
        run: |
          if [ -z "${AUTHORS// /}" ]; then echo "BACKLOG_AUTHORS is not set" >&2; exit 1; fi
          for a in $AUTHORS; do
            if [ "$a" = "$AUTHOR" ]; then echo "allowed: $AUTHOR"; exit 0; fi
          done
          gh issue comment "$N" --repo "$GITHUB_REPOSITORY" \
            --body "This repository accepts issues only from the maintainer and its agents."
          gh issue close "$N" --repo "$GITHUB_REPOSITORY" --reason "not planned"
          gh issue lock "$N" --repo "$GITHUB_REPOSITORY"
```

- [ ] **Step 2: Check the author test in shell**

```bash
for case in "jenskeiner|jenskeiner claude[bot] github-actions[bot]" \
            "github-actions[bot]|jenskeiner claude[bot] github-actions[bot]" \
            "stranger|jenskeiner claude[bot] github-actions[bot]" "jenskeiner| "; do
  AUTHOR=${case%%|*} AUTHORS=${case#*|} bash -c '
    if [ -z "${AUTHORS// /}" ]; then echo "$AUTHOR: unset"; exit 0; fi
    for a in $AUTHORS; do [ "$a" = "$AUTHOR" ] && { echo "$AUTHOR: allowed"; exit 0; }; done
    echo "$AUTHOR: close"'
done
```

Expected: `jenskeiner: allowed`, `github-actions[bot]: allowed`, `stranger: close`, `jenskeiner: unset`.

- [ ] **Step 3: Check the expiry parse locally**

```bash
head=$(gh api -i /rate_limit); printf '%s\n' "$head" | tr -d '\r' \
  | awk -F': ' 'tolower($1) == "github-authentication-token-expiration" { print $2 }'
GH_TOKEN=$BOARD_TOKEN gh api -i /rate_limit | tr -d '\r' \
  | awk -F': ' 'tolower($1) == "github-authentication-token-expiration" { print $2 }'
```

Expected: the first prints nothing or the expiry of the local `gh` token. The second prints a date about one year ahead, e.g. `2027-10-09 12:00:00 UTC`. On macOS, `date -d` does not exist; check the day count on Linux or trust the workflow run in Task 8.

- [ ] **Step 4: Lint**

Run the two workflow linters. Expected: no findings.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/repo-guard.yml
git commit -m "Limit issues to the maintainer and the agents and warn before tokens expire."
```

---

### Task 7: Agent prompts, skill, issue templates

**Files:**
- Modify: `agents/product-owner.md`
- Modify: `agents/skills/backlog.md`
- Modify: `agents/CONTEXT.md`
- Modify: `.github/ISSUE_TEMPLATE/*.yml` except `config.yml`

- [ ] **Step 1: Product owner**

In `agents/product-owner.md`:

Under `## Inputs`, add as the first bullet:

```
- The section "Backlog state" at the end of your prompt: the board items in
  `next` (the maintainer's, in the maintainer's order) and `backlog` (yours
  to order), and `stale_review`.
```

In step 1, replace `add \`ready-for-agent\`. Issues from the maintainer also get \`priority: high\`.` with `add \`ready-for-agent\`.`

Step 4 keeps its rule "only if fewer than 3 agent PRs are open". Do not change it: the gate no longer stops the product owner at the cap, so this rule now does the work.

After step 3, add:

~~~
3b. Order the backlog. Rank every item of `backlog` in the state. Criteria,
   in order: the targets in `CONTEXT.md`, dependencies between issues (an
   issue goes after the issues it needs), small before large at equal value.
   Issues you file in this run go into the order too. Never list an item of
   `next`: the maintainer owns that column, and a script drops such numbers.
3c. If `stale_review` is true, review every open issue, also those in `next`.
   An issue is stale if: the pages already meet its acceptance criteria, it
   duplicates another open issue, it conflicts with an active decision, it
   refers to code removed upstream, or it is outside the targets in
   `CONTEXT.md`. Never propose an issue labelled `keep` or
   `stale-candidate`. At most 10 per run. Give each a reason of one sentence
   that names the page, issue, decision or path. A script closes stale
   issues filed by agents and labels the other issues `stale-candidate`. Do
   not close or label them yourself.
3d. Write `backlog.json` at the repository root. Do not commit it.

   ```json
   {"order": [42, 35, 34], "stale": [{"n": 17, "reason": "doc/guide/openmp.md has the section"}]}
   ```

   `order` lists every `backlog` number once, best first. `stale` may be
   empty. An invalid file changes nothing and fails the run.
~~~

Under `## Stop conditions`, replace `Stop after step 7` with `Stop after step 7, with \`backlog.json\` written,`.

- [ ] **Step 2: Backlog skill**

In `agents/skills/backlog.md`:

- Label table: the Priority row becomes `| Backlog | \`stale-candidate\` (proposed for closing, the maintainer decides), \`keep\` (never stale) |`.
- Replace the paragraph `Pick order for workers: ...` with:

```
Pick order: the board `NFFT docs backlog` of the organization
`nfft-docs-agents`. Column `Next` first, then `Backlog`, each top down. The
maintainer owns `Next`. The product owner orders `Backlog`. The gate picks
the first item with `ready-for-agent` and without `in-progress`, `blocked`
or `needs-triage`. Only issues by the maintainer, by agents and by the
workflows are on the board.
```

- [ ] **Step 3: Shared context**

In `agents/CONTEXT.md`, section `## Labels`: replace `\`from-maintainer\`, \`agent\`. \`priority: high\`.` with `\`from-maintainer\`, \`agent\`. \`stale-candidate\`, \`keep\`.` and replace the line `Pick order: \`from-maintainer\` first, then \`priority: high\`, then oldest.` with `Pick order: the board, \`Next\` then \`Backlog\`. The gate picks; see the \`backlog\` skill.`

- [ ] **Step 4: Issue templates**

In every `.github/ISSUE_TEMPLATE/*.yml` except `config.yml`, add after the `labels:` line:

```yaml
projects: ["nfft-docs-agents/P"]
```

```bash
for f in .github/ISSUE_TEMPLATE/*.yml; do
  [ "$(basename "$f")" = config.yml ] && continue
  grep -q '^projects:' "$f" || sed -i '' '/^labels:/a\
projects: ["nfft-docs-agents/P"]
' "$f"
done
grep -c '^projects:' .github/ISSUE_TEMPLATE/*.yml
```

Expected: `1` for every template, `0` for `config.yml`.

- [ ] **Step 5: Check**

```bash
grep -rn "priority: high" agents/ .github/ ; grep -rniE "load-bearing|seam|byte-identical|odometer" agents/
```

Expected: no output. Run the two workflow linters. Expected: no findings.

- [ ] **Step 6: Commit**

```bash
git add agents/product-owner.md agents/skills/backlog.md agents/CONTEXT.md .github/ISSUE_TEMPLATE/
git commit -m "Tell the agents to order the backlog board and put new issues on it."
```

---

### Task 8: Rollout and end-to-end check

Every step is an outward action. Ask the maintainer before each one. Note the current value of `AGENTS_ENABLED` (`gh variable get AGENTS_ENABLED`); it stays off until Step 9.

- [ ] **Step 1: Guard token (maintainer)**

Fine-grained token, resource owner `jenskeiner`, repository `nfft-docs` only, permission Administration: read and write, expiry 1 year.

- [ ] **Step 2: Secrets and variables**

```bash
gh variable set AGENTS_ENABLED --body false
gh secret set BACKLOG_TOKEN --env agents
gh secret set GUARD_TOKEN --env agents
gh variable set BACKLOG_OWNER --body nfft-docs-agents
gh variable set BACKLOG_PROJECT --body P
gh variable set BACKLOG_AUTHORS --body "jenskeiner claude[bot] github-actions[bot]"
gh variable set INTERACTION_LIMIT --body true
```

Restrict environment `agents` to the branch `develop` (Settings, Environments, agents, Deployment branches, Selected branches, `develop`). A workflow on an agent branch then cannot read `BACKLOG_TOKEN`, `GUARD_TOKEN` or `CLAUDE_CODE_OAUTH_TOKEN`. Check that dispatches with `--ref develop` still run.

- [ ] **Step 3: Labels**

```bash
gh label create stale-candidate --color fbca04 --description "Proposed for closing, the maintainer decides"
gh label create keep --color 0e8a16 --description "Never proposed as stale"
gh label delete "priority: high" --yes
```

- [ ] **Step 4: Merge**

Push the branch, open a PR to `develop`. PR checks, zizmor and actionlint must pass. The maintainer merges.

- [ ] **Step 5: Interaction limit and bots**

`gh workflow run repo-guard.yml`. Then `gh api repos/jenskeiner/nfft-docs/interaction-limits`. Expected: `"limit": "collaborators_only"`, and the run log shows the expiry of both tokens.

Check the bots under the limit:
- `gh workflow run agents.yml -f role=product-owner`. Expected: the run can comment on and label issues as `claude[bot]`. Check the transcript for refused `gh issue` calls.
- Dependabot: in the web UI, Insights, Dependency graph, Dependabot, click "Check for updates" on one ecosystem. Expected: no error in its log about interaction limits.
- `github-actions[bot]`: the `apply` job of this run comments if `backlog.json` has stale entries. If it has none, check the `apply` log of the first Monday run.

If a bot is blocked: `gh api -X DELETE repos/jenskeiner/nfft-docs/interaction-limits` and `gh variable set INTERACTION_LIMIT --body false`.

- [ ] **Step 6: Product owner end to end**

From the Step 5 run: job `role` green, job `apply` green with `moved N items`, board `Backlog` in the new order, `Next` unchanged, every open issue by the three authors on the board.

- [ ] **Step 7: Worker end to end**

Move one `ready-for-agent` issue to `Next`. `gh workflow run agents.yml -f role=worker`. Expected: gate log `go: <role> on issue #<that issue>`. Put an issue without `ready-for-agent` above it in `Next`. Expected: gate log line `skip #<n>: not ready-for-agent`.

- [ ] **Step 8: Issue form and foreign author**

File an issue from a template in the web UI. Expected: on the board at once, without a Status. From a second account: opening an issue is refused while the limit is on. With `INTERACTION_LIMIT` false only: an issue from a second account is closed, commented and locked.

- [ ] **Step 9: Turn the crons on**

`gh variable set AGENTS_ENABLED --body true`.
