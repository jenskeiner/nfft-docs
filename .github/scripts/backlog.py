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
