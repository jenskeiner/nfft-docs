#!/usr/bin/env python3
"""Backlog board for the agents. Run from the repository root:

    python3 .github/scripts/backlog.py gate <worker|role>
    python3 .github/scripts/backlog.py analyst
    python3 .github/scripts/backlog.py sync
    python3 .github/scripts/backlog.py apply <backlog.json>

The board is an organization project with Status Next, Focus, Backlog,
Done. Next and Focus belong to the maintainer, Backlog to the product owner.
Board calls use BOARD_TOKEN, issue edits use GH_TOKEN. Needs BACKLOG_OWNER,
BACKLOG_PROJECT, BACKLOG_AUTHORS, BACKLOG_MAINTAINER and GITHUB_REPOSITORY.
"""

import datetime
import json
import os
import re
import subprocess
import sys
import time

SKIP = {"in-progress", "blocked", "needs-triage"}
ALWAYS = {"upstream", "meta"}
STATUSES = {"Next", "Focus", "Backlog", "Done"}
AGENT = "claude[bot]"
MAX_STALE = 10
MAX_REASON = 300
MAX_BYTES = 65536


def env():
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    owner = os.environ.get("BACKLOG_OWNER", "").strip()
    project = os.environ.get("BACKLOG_PROJECT", "").strip()
    authors = set(os.environ.get("BACKLOG_AUTHORS", "").split())
    maintainer = os.environ.get("BACKLOG_MAINTAINER", "").strip()
    for name, value in (("GITHUB_REPOSITORY", repo), ("BACKLOG_OWNER", owner),
                        ("BACKLOG_PROJECT", project), ("BACKLOG_AUTHORS", authors),
                        ("BACKLOG_MAINTAINER", maintainer)):
        if not value:
            sys.exit(f"{name} is not set")
    if not project.isdigit():
        sys.exit(f"BACKLOG_PROJECT must be a project number, not {project!r}")
    return owner, int(project), authors, repo, maintainer


def login(author):
    if not author:
        return ""
    name = author["login"]
    if author["__typename"] == "Bot" and not name.endswith("[bot]"):
        name += "[bot]"
    return name


def _parent(p):
    if not p:
        return None
    return {"n": p["number"], "open": p["state"] == "OPEN", "author": login(p.get("author")),
            "labels": [x["name"] for x in p["labels"]["nodes"]]}


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
            "parent": _parent(c.get("parent")),
        })
    return out


def ranked(items, authors):
    ok = [i for i in items if i["open"] and i["author"] in authors]
    return [i for i in ok if i["status"] == "Next"] + [i for i in ok if i["status"] == "Backlog"]


def is_focus(item, maintainer):
    return item["open"] and "focus" in item["labels"] and item["author"] == maintainer


def in_scope(item, maintainer):
    parent = item["parent"]
    return (item["status"] == "Next" or item["author"] == maintainer
            or bool(ALWAYS & set(item["labels"]))
            or bool(parent and is_focus(parent, maintainer)))


def focus_list(items, maintainer):
    focus = [i for i in items if is_focus(i, maintainer)]
    return [i for i in focus if i["status"] == "Focus"] + [i for i in focus if i["status"] != "Focus"]


def why_not(item, roles, names):
    labels = set(item["labels"])
    if "focus" in labels:
        return "focus issue"
    if "ready-for-agent" not in labels:
        return "not ready-for-agent"
    if labels & SKIP:
        return "labelled " + ", ".join(sorted(labels & SKIP))
    if not any(labels & set(roles[r]["types"]) for r in names):
        return "no role for its type"
    return None


def pick(items, authors, roles, want, maintainer):
    names = [r for r in roles if r != "_comment"] if want == "worker" else [want]
    skipped = []
    for item in ranked(items, authors):
        reason = why_not(item, roles, names)
        if reason is None and not in_scope(item, maintainer):
            reason = "outside focus"
        if reason is None:
            role = next(r for r in names if set(item["labels"]) & set(roles[r]["types"]))
            return (item["n"], role), skipped
        if item["status"] == "Next" or reason == "outside focus":
            skipped.append(f"skip #{item['n']}: {reason}")
    return None, skipped


def analyst_focus(items, maintainer):
    analysed = {int(m.group(1)) for i in items if i["open"]
                for m in [re.fullmatch(r"Analysis: #(\d+)", i["title"])] if m}
    focus = focus_list(items, maintainer)
    if not focus:
        return None, "no focus"
    for f in focus:
        if f["n"] not in analysed:
            return f["n"], None
    return None, "every focus analysed"


def _is_num(x):
    return type(x) is int


def check(plan, items, stale_day):
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
    if stale and not stale_day:
        errors.append("stale entries are allowed only on Mondays (UTC)")
    return errors


def final_order(order, items, authors):
    backlog = [i for i in ranked(items, authors) if i["status"] == "Backlog"]
    by_n = {i["n"]: i for i in backlog}
    head = [by_n[n] for n in order if n in by_n]
    listed = {i["n"] for i in head}
    return head + [i for i in backlog if i["n"] not in listed]


def moves(items, authors, final):
    cur = [i["id"] for i in ranked(items, authors) if i["status"] == "Backlog"]
    out, prev = [], None
    for item in final:
        k = cur.index(item["id"])
        if (cur[k - 1] if k else None) != prev:
            cur.pop(k)
            cur.insert(cur.index(prev) + 1 if prev else 0, item["id"])
            out.append((item["id"], prev))
        prev = item["id"]
    return out


def stale_actions(stale, items, authors):
    by_n = {i["n"]: i for i in items}
    out = []
    for s in stale:
        item = by_n[s["n"]]
        if (not item["open"] or item["author"] not in authors
                or {"stale-candidate", "keep"} & set(item["labels"])):
            continue
        reason = " ".join(s["reason"].split())[:MAX_REASON]
        # Closing moves an item out of Next, which only the maintainer changes.
        close = item["author"] == AGENT and item["status"] != "Next"
        out.append(("close" if close else "label", s["n"], reason))
    return out


def plan_sync(items, issues, authors, maintainer):
    on_board = {i["n"] for i in items}
    add = []
    for x in issues:
        if x["author"] in authors and x["n"] not in on_board:
            focus = "focus" in x["labels"] and x["author"] == maintainer
            add.append((x, "Focus" if focus else "Backlog"))
    fix = []
    for i in items:
        if not i["open"] or i["author"] not in authors:
            continue
        if is_focus(i, maintainer):
            want = "Focus"
        # Done on an open item: reopened after the close workflow set Done.
        elif i["status"] in (None, "Done", "Focus"):
            want = "Backlog"
        else:
            continue
        if i["status"] != want:
            fix.append((i, want))
    return add, fix


def assume_status(items, written):
    # A read right after a write can still show the old Status.
    return [{**i, "status": written[i["n"]]} if i["n"] in written else i for i in items]


def read_until(read, written, tries=6, wait=2.0, sleep=time.sleep):
    # A read right after a write can still miss new items.
    for k in range(tries):
        items = read()
        missing = written - {i["n"] for i in items}
        if not missing:
            return items
        if k + 1 < tries:
            sleep(wait * (k + 1))
    sys.exit(f"board: items {sorted(missing)} not readable after the write")


def state(items, authors, today, maintainer):
    def row(i):
        return {"n": i["n"], "title": i["title"], "author": i["author"], "labels": i["labels"]}
    focus = []
    for f in focus_list(items, maintainer):
        sub = [i for i in items if i["open"] and i["parent"] and i["parent"]["n"] == f["n"]]
        focus.append({"n": f["n"], "title": f["title"], "sub": [i["n"] for i in sub],
                      "ready": sum("ready-for-agent" in i["labels"] for i in sub)})
    r = ranked(items, authors)
    return {"next": [row(i) for i in r if i["status"] == "Next"],
            "focus": focus,
            "backlog": [row(i) for i in r if i["status"] == "Backlog"],
            "stale_review": today.isoweekday() == 1}


def load_plan(path):
    try:
        if os.path.getsize(path) > MAX_BYTES:
            sys.exit(f"invalid backlog.json: larger than {MAX_BYTES} bytes")
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError, RecursionError) as e:
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
          author { __typename login } labels(first: 50) { nodes { name } }
          parent { number state author { __typename login } labels(first: 50) { nodes { name } } } } }
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
    missing = STATUSES - set(options)
    if missing:
        sys.exit(f"board: Status lacks {sorted(missing)}")
    return project["id"], field["id"], options, parse_items(nodes, repo)


ISSUES = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    issues(states: OPEN, first: 100, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes { id number author { __typename login } labels(first: 50) { nodes { name } } }
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


STATUS = """
query($i: ID!) {
  node(id: $i) { ... on ProjectV2Item {
    fieldValueByName(name: "Status") { ... on ProjectV2ItemFieldSingleSelectValue { name } } } }
}
"""


def status_of(item_id):
    # Re-read right before a write: the maintainer may move items during a run.
    node = graphql(STATUS, i=item_id)["node"] or {}
    return (node.get("fieldValueByName") or {}).get("name")


def open_issues(repo):
    owner, name = repo.split("/")
    out, cursor = [], None
    while True:
        page = graphql(ISSUES, owner=owner, name=name, cursor=cursor)["repository"]["issues"]
        out += [{"n": x["number"], "id": x["id"], "author": login(x["author"]),
                 "labels": [y["name"] for y in x["labels"]["nodes"]]} for x in page["nodes"]]
        if not page["pageInfo"]["hasNextPage"]:
            return out
        cursor = page["pageInfo"]["endCursor"]


def sync():
    owner, number, authors, repo, maintainer = env()
    project, field, options, items = read_board(owner, number, repo)
    add, fix = plan_sync(items, open_issues(repo), authors, maintainer)
    written = {}
    for x, want in add:
        item = graphql(ADD, p=project, c=x["id"])["addProjectV2ItemById"]["item"]["id"]
        graphql(SET_STATUS, p=project, i=item, f=field, o=options[want])
        written[x["n"]] = want
    for i, want in fix:
        if status_of(i["id"]) == i["status"]:
            graphql(SET_STATUS, p=project, i=i["id"], f=field, o=options[want])
            written[i["n"]] = want
    if written:
        items = assume_status(
            read_until(lambda: read_board(owner, number, repo)[3], set(written)), written)
    return project, authors, maintainer, items


def issue(*args):
    r = subprocess.run(["gh", "issue", *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"gh issue {args[0]}: {r.stderr.strip()}")


def cmd_sync():
    _, authors, maintainer, items = sync()
    today = datetime.datetime.now(datetime.timezone.utc).date()
    print(json.dumps(state(items, authors, today, maintainer), indent=1))


def cmd_apply(path):
    plan = load_plan(path)
    project, authors, _, items = sync()
    monday = datetime.datetime.now(datetime.timezone.utc).date().isoweekday() == 1
    errors = check(plan, items, monday)
    if errors:
        sys.exit("invalid backlog.json: " + "; ".join(errors))
    steps = moves(items, authors, final_order(plan["order"], items, authors))
    moved = 0
    for item_id, after in steps:
        if status_of(item_id) != "Backlog":
            print(f"skip move of {item_id}: no longer in Backlog")
            continue
        graphql(MOVE, p=project, i=item_id, a=after)
        moved += 1
    print(f"moved {moved} items")
    for kind, n, reason in stale_actions(plan.get("stale", []), items, authors):
        if kind == "close":
            issue("close", str(n), "--reason", "not planned", "--comment", f"Stale: {reason}")
        else:
            issue("edit", str(n), "--add-label", "stale-candidate")
            issue("comment", str(n), "--body", f"Stale candidate: {reason}")
        print(f"{kind} #{n}: {reason}")


def cmd_gate(want):
    owner, number, authors, repo, maintainer = env()
    with open("agents/roles.json") as fh:
        roles = json.load(fh)
    got, skipped = pick(read_board(owner, number, repo)[3], authors, roles, want, maintainer)
    for line in skipped:
        print(line, file=sys.stderr)
    if got:
        print(f"{got[0]}\t{got[1]}")


def cmd_analyst():
    owner, number, _, repo, maintainer = env()
    focus, reason = analyst_focus(read_board(owner, number, repo)[3], maintainer)
    if focus:
        print(focus)
    else:
        print(reason, file=sys.stderr)


def main(argv):
    if len(argv) == 2 and argv[0] == "gate":
        return cmd_gate(argv[1])
    if argv == ["analyst"]:
        return cmd_analyst()
    if argv == ["sync"]:
        return cmd_sync()
    if len(argv) == 2 and argv[0] == "apply":
        return cmd_apply(argv[1])
    sys.exit("usage: backlog.py gate <worker|role> | analyst | sync | apply <backlog.json>")


if __name__ == "__main__":
    main(sys.argv[1:])
