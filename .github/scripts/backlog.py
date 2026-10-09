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
