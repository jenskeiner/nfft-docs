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

import datetime
import json
import os
import subprocess
import sys

SKIP = {"in-progress", "blocked", "needs-triage"}
AGENT = "claude[bot]"
MAX_STALE = 10
MAX_REASON = 300
MAX_BYTES = 65536


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
    if argv == ["sync"]:
        return cmd_sync()
    if len(argv) == 2 and argv[0] == "apply":
        return cmd_apply(argv[1])
    sys.exit("usage: backlog.py gate <worker|role> | sync | apply <backlog.json>")


if __name__ == "__main__":
    main(sys.argv[1:])
