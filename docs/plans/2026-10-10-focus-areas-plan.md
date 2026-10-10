# Focus areas and pause: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agents work only on the maintainer's focus areas plus the fixed exceptions, and `AGENTS_ENABLED` pauses all scheduled agent work.

**Architecture:** Board items get their parent issue. `backlog.py` learns focus issues (open, label `focus`, author `BACKLOG_MAINTAINER`), a `Focus` column, an in-scope rule for the gate, an analyst focus choice and a `focus` list in the product owner state. The gate script, the workflows and the prompts use these.

**Tech Stack:** Python 3 stdlib, `gh` CLI, GitHub Projects v2 and sub-issues GraphQL API, GitHub Actions, bash.

**Spec:** `docs/plans/2026-10-10-focus-areas-design.md`

## Global Constraints

- Repo variable `BACKLOG_MAINTAINER` = `jenskeiner`. Empty: every `backlog.py` subcommand exits 1.
- Board Status options exactly `Next`, `Focus`, `Backlog`, `Done`.
- Focus issue: open, label `focus`, author `BACKLOG_MAINTAINER`. A `focus` label on any other issue has no effect.
- In scope for workers: status `Next`, author `BACKLOG_MAINTAINER`, type `upstream` or `meta`, or parent is an active focus.
- Tokens: only shell steps read `BACKLOG_TOKEN`; never the model step.
- Commit messages: one sentence, imperative, no prefixes, no attribution lines.
- Prose in `agents/`: ASD-STE100, no special symbols, forbidden words: load-bearing, seam, byte-identical, odometer.
- After every workflow change: `uvx zizmor==1.30.1 --no-progress --min-severity medium .github/` and `uvx --from actionlint-py==1.7.12.25 actionlint -no-color`, both without findings.

## Review Focus

1. The maintainer moves a focus issue into `Next`, or files it from a non-focus template and adds `focus` later: the sync moves it to `Focus`, the gate never picks it. Tests: Task 1 (`test_plan_sync_moves_focus_issues_into_focus`, `test_pick_never_takes_a_focus_issue`).
2. An agent sets `focus` on its own issue, or links work under a closed focus or under a non-focus parent: no effect. Tests: Task 1 (`test_pick_skips_sub_issue_of_inactive_focus`, `test_focus_list_puts_focus_column_first`).
3. No focus open: workers still take `Next`, the maintainer's issues, `upstream` and `meta`; the analyst does not run. Tests: Task 1 (`test_pick_exceptions_run_without_focus`, `test_analyst_focus_reasons`), Task 2 (gate shell check).
4. Apply with focus items on the board: never moves them. Test: Task 1 (`test_moves_never_touch_focus_items`).
5. `AGENTS_ENABLED=false`: the scheduled upstream poll does not run, a dispatch still does. Check: Task 4, Step 6.

## File structure

| File | Change |
|------|--------|
| `.github/scripts/backlog.py` | Parent per item, focus rules, `analyst` subcommand, `Focus` status in sync and state. |
| `.github/scripts/test_backlog.py` | Updated and new tests, 49 in total. |
| `.github/scripts/agent-gate.sh` | Analyst runs only on a focus, writes `focus`. |
| `.github/workflows/agents.yml` | `BACKLOG_MAINTAINER` env, analyst prompt input. |
| `.github/workflows/upstream.yml` | Pause by `AGENTS_ENABLED`. |
| `.github/ISSUE_TEMPLATE/focus.yml` | New template. |
| `agents/product-owner.md`, `agents/analyst.md`, `agents/skills/backlog.md`, `agents/CONTEXT.md`, `agents/skills/self-improvement.md` | Focus rules. |

---

### Task 1: Focus rules in the board model

**Files:**
- Modify: `.github/scripts/backlog.py`
- Modify: `.github/scripts/test_backlog.py`

**Interfaces:**
- Produces:
  - Item gets key `parent`: `None` or `{"n": int, "open": bool, "author": str, "labels": list[str]}`.
  - `env() -> (owner, project, authors, repo, maintainer)`.
  - `is_focus(item, maintainer) -> bool`, `in_scope(item, maintainer) -> bool`, `focus_list(items, maintainer) -> list[Item]` (column `Focus` first, then other focus issues, board order).
  - `pick(items, authors, roles, want, maintainer) -> (pick|None, skip lines)`; new skip reasons `focus issue`, `outside focus`.
  - `analyst_focus(items, maintainer) -> (int|None, str|None)`; reasons `no focus`, `every focus analysed`.
  - `plan_sync(items, issues, authors, maintainer) -> (add: list[(issue, status)], fix: list[(item, status)])`; `issues` rows now carry `labels`.
  - `assume_status(items, written: dict[int, str])` replaces `assume_backlog`.
  - `state(items, authors, today, maintainer)` adds `focus: [{"n", "title", "sub": [int], "ready": int}]`.
  - `sync() -> (project, authors, maintainer, items)`.
  - CLI `backlog.py analyst`: prints the focus number, or the reason on stderr and nothing on stdout.

- [ ] **Step 1: Write the failing tests**

Save this patch as `tests.patch` in the scratchpad and apply it with `git apply tests.patch` from the repository root:

```diff
--- a/.github/scripts/test_backlog.py	2026-10-10 14:16:33
+++ b/.github/scripts/test_backlog.py	2026-10-10 14:16:33
@@ -11,6 +11,7 @@
 
 REPO = "jenskeiner/nfft-docs"
 AUTHORS = {"jenskeiner", "claude[bot]"}
+M = "jenskeiner"
 ROLES = {
     "_comment": "x",
     "writer": {"types": ["gap", "new-section"]},
@@ -18,16 +19,22 @@
 }
 
 
+def par(n, state="OPEN", author=("User", "jenskeiner"), labels=("focus",)):
+    return {"number": n, "state": state, "author": {"__typename": author[0], "login": author[1]},
+            "labels": {"nodes": [{"name": x} for x in labels]}}
+
+
 def node(n, status="Backlog", labels=("gap", "ready-for-agent"), author=("User", "jenskeiner"),
-         state="OPEN", repo=REPO, kind="Issue"):
+         state="OPEN", repo=REPO, kind="Issue", parent=None, title=None):
     return {
         "id": f"I{n}",
         "fieldValueByName": {"name": status} if status else None,
         "content": {
-            "__typename": kind, "number": n, "title": f"t{n}", "state": state,
+            "__typename": kind, "number": n, "title": title or f"t{n}", "state": state,
             "repository": {"nameWithOwner": repo},
             "author": {"__typename": author[0], "login": author[1]},
             "labels": {"nodes": [{"name": x} for x in labels]},
+            "parent": parent,
         },
     }
 
@@ -37,7 +44,7 @@
 
 
 def pick(*args):
-    return backlog.pick(*args)[0]
+    return backlog.pick(*args, M)[0]
 
 
 def test_login_normalizes_bots():
@@ -102,14 +109,14 @@
         node(2, "Next", labels=("meta", "ready-for-agent")),
         node(3, "Next", labels=("gap", "ready-for-agent", "blocked")),
         node(4, "Backlog", labels=("gap",)),
-        node(5)), AUTHORS, ROLES, "worker")
+        node(5)), AUTHORS, ROLES, "worker", M)
     assert got == (5, "writer"), got
     assert skipped == ["skip #1: not ready-for-agent", "skip #2: no role for its type",
                        "skip #3: labelled blocked"], skipped
 
 
 def test_pick_accepts_bot_author():
-    got = pick(items(node(1, author=("Bot", "claude"))), AUTHORS, ROLES, "worker")
+    got = pick(items(node(1, author=("Bot", "claude"), parent=par(9))), AUTHORS, ROLES, "worker")
     assert got == (1, "writer"), got
 
 
@@ -117,7 +124,7 @@
     saved = dict(os.environ)
     try:
         os.environ.update(GITHUB_REPOSITORY=REPO, BACKLOG_OWNER="nfft-docs-agents",
-                          BACKLOG_PROJECT="3", BACKLOG_AUTHORS=" ")
+                          BACKLOG_PROJECT="3", BACKLOG_AUTHORS=" ", BACKLOG_MAINTAINER=M)
         try:
             backlog.env()
         except SystemExit as e:
@@ -125,7 +132,15 @@
         else:
             raise AssertionError("no exit")
         os.environ["BACKLOG_AUTHORS"] = "jenskeiner claude[bot]"
-        assert backlog.env() == ("nfft-docs-agents", 3, AUTHORS, REPO)
+        assert backlog.env() == ("nfft-docs-agents", 3, AUTHORS, REPO, M)
+        os.environ["BACKLOG_MAINTAINER"] = ""
+        try:
+            backlog.env()
+        except SystemExit as e:
+            assert "BACKLOG_MAINTAINER" in str(e.code), e.code
+        else:
+            raise AssertionError("no exit")
+        os.environ["BACKLOG_MAINTAINER"] = M
         os.environ["BACKLOG_OWNER"] = ""
         try:
             backlog.env()
@@ -225,22 +240,23 @@
 
 def test_plan_sync_adds_missing_and_fixes_empty_status():
     its = board((1, "Backlog", U), (2, None, U))
-    issues = [{"n": 1, "id": "N1", "author": "jenskeiner"},
-              {"n": 3, "id": "N3", "author": "claude[bot]"},
-              {"n": 4, "id": "N4", "author": "stranger"}]
-    add, unset = backlog.plan_sync(its, issues, AUTHORS)
-    assert [x["n"] for x in add] == [3] and [i["n"] for i in unset] == [2], (add, unset)
+    issues = [{"n": 1, "id": "N1", "author": "jenskeiner", "labels": []},
+              {"n": 3, "id": "N3", "author": "claude[bot]", "labels": []},
+              {"n": 4, "id": "N4", "author": "stranger", "labels": []}]
+    add, fix = backlog.plan_sync(its, issues, AUTHORS, M)
+    assert [(x["n"], w) for x, w in add] == [(3, "Backlog")], add
+    assert [(i["n"], w) for i, w in fix] == [(2, "Backlog")], fix
 
 
 def test_state_rows_and_stale_review():
     import datetime
     its = board((1, "Backlog", U), (2, "Next", B), (3, "Done", U))
-    got = backlog.state(its, AUTHORS, datetime.date(2026, 10, 12))
+    got = backlog.state(its, AUTHORS, datetime.date(2026, 10, 12), M)
     assert [r["n"] for r in got["next"]] == [2] and [r["n"] for r in got["backlog"]] == [1]
     assert got["next"][0] == {"n": 2, "title": "t2", "author": "claude[bot]",
                               "labels": ["gap", "ready-for-agent"]}, got
     assert got["stale_review"] is True
-    assert backlog.state(its, AUTHORS, datetime.date(2026, 10, 13))["stale_review"] is False
+    assert backlog.state(its, AUTHORS, datetime.date(2026, 10, 13), M)["stale_review"] is False
 
 
 def test_load_plan_rejects_large_and_broken_files():
@@ -287,14 +303,15 @@
 
 def test_plan_sync_resets_reopened_done_items():
     its = items(node(1, "Done"), node(2, "Done", state="CLOSED"))
-    add, unset = backlog.plan_sync(its, [{"n": 1, "id": "N1", "author": "jenskeiner"}], AUTHORS)
-    assert add == [] and [i["n"] for i in unset] == [1], (add, unset)
+    issues = [{"n": 1, "id": "N1", "author": "jenskeiner", "labels": ["gap"]}]
+    add, fix = backlog.plan_sync(its, issues, AUTHORS, M)
+    assert add == [] and [(i["n"], w) for i, w in fix] == [(1, "Backlog")], (add, fix)
 
 
-def test_assume_backlog_marks_items_the_sync_wrote():
+def test_assume_status_marks_items_the_sync_wrote():
     its = items(node(1, None), node(2, "Done"), node(3, "Next"), node(4, None))
-    got = backlog.assume_backlog(its, {1, 2})
-    assert [(i["n"], i["status"]) for i in got] == [(1, "Backlog"), (2, "Backlog"),
+    got = backlog.assume_status(its, {1: "Backlog", 2: "Focus"})
+    assert [(i["n"], i["status"]) for i in got] == [(1, "Backlog"), (2, "Focus"),
                                                     (3, "Next"), (4, None)], got
 
 
@@ -318,7 +335,8 @@
     saved = dict(os.environ)
     try:
         os.environ.update(GITHUB_REPOSITORY=REPO, BACKLOG_OWNER="nfft-docs-agents",
-                          BACKLOG_PROJECT="one", BACKLOG_AUTHORS="jenskeiner")
+                          BACKLOG_PROJECT="one", BACKLOG_AUTHORS="jenskeiner",
+                          BACKLOG_MAINTAINER=M)
         try:
             backlog.env()
         except SystemExit as e:
@@ -350,8 +368,102 @@
                 raise AssertionError("no exit")
     finally:
         backlog.json.load = saved
+
+
+FOCUS = ("focus", "from-maintainer")
+
+
+def test_parse_reads_parent():
+    got = items(node(1, parent=par(9)), node(2))
+    assert got[0]["parent"] == {"n": 9, "open": True, "author": "jenskeiner",
+                                "labels": ["focus"]}, got
+    assert got[1]["parent"] is None
+
+
+def test_pick_takes_sub_issue_of_active_focus():
+    got = pick(items(node(1, author=B), node(2, author=B, parent=par(9))),
+               AUTHORS, ROLES, "worker")
+    assert got == (2, "writer"), got
+
+
+def test_pick_skips_agent_issue_outside_focus_and_logs_it():
+    got, skipped = backlog.pick(items(node(1, author=B)), AUTHORS, ROLES, "worker", M)
+    assert got is None and skipped == ["skip #1: outside focus"], (got, skipped)
 
 
+def test_pick_skips_sub_issue_of_inactive_focus():
+    for parent in (par(9, state="CLOSED"), par(9, author=("Bot", "claude")),
+                   par(9, labels=("gap",))):
+        assert pick(items(node(1, author=B, parent=parent)), AUTHORS, ROLES, "worker") is None
+
+
+def test_pick_exceptions_run_without_focus():
+    roles = {"writer": {"types": ["gap"]}, "meta": {"types": ["meta"]},
+             "watcher": {"types": ["upstream"]}}
+    assert pick(items(node(1, "Next", author=B)), AUTHORS, roles, "worker") == (1, "writer")
+    assert pick(items(node(2, author=U)), AUTHORS, roles, "worker") == (2, "writer")
+    assert pick(items(node(3, author=B, labels=("meta", "ready-for-agent"))),
+                AUTHORS, roles, "worker") == (3, "meta")
+    assert pick(items(node(4, author=B, labels=("upstream", "gap", "ready-for-agent"))),
+                AUTHORS, roles, "worker") == (4, "writer")
+
+
+def test_pick_never_takes_a_focus_issue():
+    its = items(node(1, "Next", labels=FOCUS + ("gap", "ready-for-agent")))
+    got, skipped = backlog.pick(its, AUTHORS, ROLES, "worker", M)
+    assert got is None and skipped == ["skip #1: focus issue"], (got, skipped)
+
+
+def test_focus_list_puts_focus_column_first():
+    its = items(node(1, "Backlog", labels=FOCUS), node(2, "Focus", labels=FOCUS),
+                node(3, "Focus", labels=FOCUS, author=B), node(4, "Focus", labels=FOCUS),
+                node(5, "Focus", labels=FOCUS, state="CLOSED"))
+    assert [i["n"] for i in backlog.focus_list(its, M)] == [2, 4, 1]
+
+
+def test_analyst_focus_takes_first_focus_without_open_analysis():
+    its = items(node(2, "Focus", labels=FOCUS), node(4, "Focus", labels=FOCUS),
+                node(7, author=B, title="Analysis: #2"),
+                node(8, author=B, title="Analysis: #4", state="CLOSED"))
+    assert backlog.analyst_focus(its, M) == (4, None)
+
+
+def test_analyst_focus_reasons():
+    assert backlog.analyst_focus(items(node(1)), M) == (None, "no focus")
+    its = items(node(2, "Focus", labels=FOCUS), node(7, author=B, title="Analysis: #2"))
+    assert backlog.analyst_focus(its, M) == (None, "every focus analysed")
+
+
+def test_plan_sync_moves_focus_issues_into_focus():
+    its = items(node(1, "Backlog", labels=FOCUS), node(2, "Next", labels=FOCUS),
+                node(3, "Focus", labels=FOCUS), node(4, "Focus", labels=FOCUS, author=B),
+                node(5, "Focus"))
+    issues = [{"n": 6, "id": "N6", "author": "jenskeiner", "labels": ["focus"]},
+              {"n": 7, "id": "N7", "author": "claude[bot]", "labels": ["focus"]}]
+    add, fix = backlog.plan_sync(its, issues, AUTHORS, M)
+    assert [(x["n"], w) for x, w in add] == [(6, "Focus"), (7, "Backlog")], add
+    assert [(i["n"], w) for i, w in fix] == [(1, "Focus"), (2, "Focus"), (4, "Backlog"),
+                                             (5, "Backlog")], fix
+
+
+def test_state_lists_focus_with_sub_issues():
+    import datetime
+    its = items(node(9, "Focus", labels=FOCUS, title="[Focus] NFSFT API"),
+                node(1, author=B, parent=par(9)),
+                node(2, author=B, parent=par(9), labels=("gap", "needs-triage")),
+                node(3, author=B, parent=par(9), state="CLOSED"))
+    got = backlog.state(its, AUTHORS, datetime.date(2026, 10, 13), M)
+    assert got["focus"] == [{"n": 9, "title": "[Focus] NFSFT API", "sub": [1, 2],
+                             "ready": 1}], got["focus"]
+    assert [r["n"] for r in got["backlog"]] == [1, 2], got["backlog"]
+
+
+def test_moves_never_touch_focus_items():
+    its = items(node(1, "Focus", labels=FOCUS), node(2), node(3))
+    got = backlog.moves(its, AUTHORS, backlog.final_order([1, 3, 2], its, AUTHORS))
+    assert got == [("I3", None)], got
+
+
 if __name__ == "__main__":
     for name, fn in sorted(globals().items()):
         if name.startswith("test_"):
```

- [ ] **Step 2: Run, expect failure**

Run: `python3 .github/scripts/test_backlog.py`
Expected: a failure, the first one `AttributeError: module 'backlog' has no attribute 'analyst_focus'`.

- [ ] **Step 3: Change the module**

Save this patch as `module.patch` and apply it with `git apply module.patch`:

```diff
--- a/.github/scripts/backlog.py	2026-10-10 14:16:33
+++ b/.github/scripts/backlog.py	2026-10-10 14:16:33
@@ -2,23 +2,27 @@
 """Backlog board for the agents. Run from the repository root:
 
     python3 .github/scripts/backlog.py gate <worker|role>
+    python3 .github/scripts/backlog.py analyst
     python3 .github/scripts/backlog.py sync
     python3 .github/scripts/backlog.py apply <backlog.json>
 
-The board is an organization project with Status Next, Backlog, Done. Next
-belongs to the maintainer, Backlog to the product owner. Board calls use
-BOARD_TOKEN, issue edits use GH_TOKEN. Needs BACKLOG_OWNER, BACKLOG_PROJECT,
-BACKLOG_AUTHORS and GITHUB_REPOSITORY.
+The board is an organization project with Status Next, Focus, Backlog,
+Done. Next and Focus belong to the maintainer, Backlog to the product owner.
+Board calls use BOARD_TOKEN, issue edits use GH_TOKEN. Needs BACKLOG_OWNER,
+BACKLOG_PROJECT, BACKLOG_AUTHORS, BACKLOG_MAINTAINER and GITHUB_REPOSITORY.
 """
 
 import datetime
 import json
 import os
+import re
 import subprocess
 import sys
 import time
 
 SKIP = {"in-progress", "blocked", "needs-triage"}
+ALWAYS = {"upstream", "meta"}
+STATUSES = {"Next", "Focus", "Backlog", "Done"}
 AGENT = "claude[bot]"
 MAX_STALE = 10
 MAX_REASON = 300
@@ -30,13 +34,15 @@
     owner = os.environ.get("BACKLOG_OWNER", "").strip()
     project = os.environ.get("BACKLOG_PROJECT", "").strip()
     authors = set(os.environ.get("BACKLOG_AUTHORS", "").split())
+    maintainer = os.environ.get("BACKLOG_MAINTAINER", "").strip()
     for name, value in (("GITHUB_REPOSITORY", repo), ("BACKLOG_OWNER", owner),
-                        ("BACKLOG_PROJECT", project), ("BACKLOG_AUTHORS", authors)):
+                        ("BACKLOG_PROJECT", project), ("BACKLOG_AUTHORS", authors),
+                        ("BACKLOG_MAINTAINER", maintainer)):
         if not value:
             sys.exit(f"{name} is not set")
     if not project.isdigit():
         sys.exit(f"BACKLOG_PROJECT must be a project number, not {project!r}")
-    return owner, int(project), authors, repo
+    return owner, int(project), authors, repo, maintainer
 
 
 def login(author):
@@ -48,6 +54,13 @@
     return name
 
 
+def _parent(p):
+    if not p:
+        return None
+    return {"n": p["number"], "open": p["state"] == "OPEN", "author": login(p.get("author")),
+            "labels": [x["name"] for x in p["labels"]["nodes"]]}
+
+
 def parse_items(nodes, repo):
     out = []
     for node in nodes:
@@ -60,6 +73,7 @@
             "status": (node.get("fieldValueByName") or {}).get("name"),
             "author": login(c.get("author")),
             "labels": [x["name"] for x in c["labels"]["nodes"]],
+            "parent": _parent(c.get("parent")),
         })
     return out
 
@@ -69,8 +83,26 @@
     return [i for i in ok if i["status"] == "Next"] + [i for i in ok if i["status"] == "Backlog"]
 
 
+def is_focus(item, maintainer):
+    return item["open"] and "focus" in item["labels"] and item["author"] == maintainer
+
+
+def in_scope(item, maintainer):
+    parent = item["parent"]
+    return (item["status"] == "Next" or item["author"] == maintainer
+            or bool(ALWAYS & set(item["labels"]))
+            or bool(parent and is_focus(parent, maintainer)))
+
+
+def focus_list(items, maintainer):
+    focus = [i for i in items if is_focus(i, maintainer)]
+    return [i for i in focus if i["status"] == "Focus"] + [i for i in focus if i["status"] != "Focus"]
+
+
 def why_not(item, roles, names):
     labels = set(item["labels"])
+    if "focus" in labels:
+        return "focus issue"
     if "ready-for-agent" not in labels:
         return "not ready-for-agent"
     if labels & SKIP:
@@ -80,19 +112,33 @@
     return None
 
 
-def pick(items, authors, roles, want):
+def pick(items, authors, roles, want, maintainer):
     names = [r for r in roles if r != "_comment"] if want == "worker" else [want]
     skipped = []
     for item in ranked(items, authors):
         reason = why_not(item, roles, names)
+        if reason is None and not in_scope(item, maintainer):
+            reason = "outside focus"
         if reason is None:
             role = next(r for r in names if set(item["labels"]) & set(roles[r]["types"]))
             return (item["n"], role), skipped
-        if item["status"] == "Next":
+        if item["status"] == "Next" or reason == "outside focus":
             skipped.append(f"skip #{item['n']}: {reason}")
     return None, skipped
 
 
+def analyst_focus(items, maintainer):
+    analysed = {int(m.group(1)) for i in items if i["open"]
+                for m in [re.fullmatch(r"Analysis: #(\d+)", i["title"])] if m}
+    focus = focus_list(items, maintainer)
+    if not focus:
+        return None, "no focus"
+    for f in focus:
+        if f["n"] not in analysed:
+            return f["n"], None
+    return None, "every focus analysed"
+
+
 def _is_num(x):
     return type(x) is int
 
@@ -160,18 +206,32 @@
     return out
 
 
-def plan_sync(items, issues, authors):
+def plan_sync(items, issues, authors, maintainer):
     on_board = {i["n"] for i in items}
-    add = [x for x in issues if x["author"] in authors and x["n"] not in on_board]
-    # Done on an open item: reopened after the close workflow set Done.
-    unset = [i for i in items
-             if i["open"] and i["status"] in (None, "Done") and i["author"] in authors]
-    return add, unset
+    add = []
+    for x in issues:
+        if x["author"] in authors and x["n"] not in on_board:
+            focus = "focus" in x["labels"] and x["author"] == maintainer
+            add.append((x, "Focus" if focus else "Backlog"))
+    fix = []
+    for i in items:
+        if not i["open"] or i["author"] not in authors:
+            continue
+        if is_focus(i, maintainer):
+            want = "Focus"
+        # Done on an open item: reopened after the close workflow set Done.
+        elif i["status"] in (None, "Done", "Focus"):
+            want = "Backlog"
+        else:
+            continue
+        if i["status"] != want:
+            fix.append((i, want))
+    return add, fix
 
 
-def assume_backlog(items, written):
+def assume_status(items, written):
     # A read right after a write can still show the old Status.
-    return [{**i, "status": "Backlog"} if i["n"] in written else i for i in items]
+    return [{**i, "status": written[i["n"]]} if i["n"] in written else i for i in items]
 
 
 def read_until(read, written, tries=6, wait=2.0, sleep=time.sleep):
@@ -186,11 +246,17 @@
     sys.exit(f"board: items {sorted(missing)} not readable after the write")
 
 
-def state(items, authors, today):
+def state(items, authors, today, maintainer):
     def row(i):
         return {"n": i["n"], "title": i["title"], "author": i["author"], "labels": i["labels"]}
+    focus = []
+    for f in focus_list(items, maintainer):
+        sub = [i for i in items if i["open"] and i["parent"] and i["parent"]["n"] == f["n"]]
+        focus.append({"n": f["n"], "title": f["title"], "sub": [i["n"] for i in sub],
+                      "ready": sum("ready-for-agent" in i["labels"] for i in sub)})
     r = ranked(items, authors)
     return {"next": [row(i) for i in r if i["status"] == "Next"],
+            "focus": focus,
             "backlog": [row(i) for i in r if i["status"] == "Backlog"],
             "stale_review": today.isoweekday() == 1}
 
@@ -217,7 +283,8 @@
         fieldValueByName(name: "Status") { ... on ProjectV2ItemFieldSingleSelectValue { name } }
         content { __typename ... on Issue {
           number title state repository { nameWithOwner }
-          author { __typename login } labels(first: 50) { nodes { name } } } }
+          author { __typename login } labels(first: 50) { nodes { name } }
+          parent { number state author { __typename login } labels(first: 50) { nodes { name } } } } }
       }
     }
   } }
@@ -253,7 +320,7 @@
     if not field:
         sys.exit("board: field Status not found")
     options = {o["name"]: o["id"] for o in field["options"]}
-    missing = {"Next", "Backlog", "Done"} - set(options)
+    missing = STATUSES - set(options)
     if missing:
         sys.exit(f"board: Status lacks {sorted(missing)}")
     return project["id"], field["id"], options, parse_items(nodes, repo)
@@ -264,7 +331,7 @@
   repository(owner: $owner, name: $name) {
     issues(states: OPEN, first: 100, after: $cursor) {
       pageInfo { hasNextPage endCursor }
-      nodes { id number author { __typename login } }
+      nodes { id number author { __typename login } labels(first: 50) { nodes { name } } }
     }
   }
 }
@@ -307,29 +374,30 @@
     out, cursor = [], None
     while True:
         page = graphql(ISSUES, owner=owner, name=name, cursor=cursor)["repository"]["issues"]
-        out += [{"n": x["number"], "id": x["id"], "author": login(x["author"])}
-                for x in page["nodes"]]
+        out += [{"n": x["number"], "id": x["id"], "author": login(x["author"]),
+                 "labels": [y["name"] for y in x["labels"]["nodes"]]} for x in page["nodes"]]
         if not page["pageInfo"]["hasNextPage"]:
             return out
         cursor = page["pageInfo"]["endCursor"]
 
 
 def sync():
-    owner, number, authors, repo = env()
+    owner, number, authors, repo, maintainer = env()
     project, field, options, items = read_board(owner, number, repo)
-    add, unset = plan_sync(items, open_issues(repo), authors)
-    for x in add:
+    add, fix = plan_sync(items, open_issues(repo), authors, maintainer)
+    written = {}
+    for x, want in add:
         item = graphql(ADD, p=project, c=x["id"])["addProjectV2ItemById"]["item"]["id"]
-        graphql(SET_STATUS, p=project, i=item, f=field, o=options["Backlog"])
-    written = {x["n"] for x in add}
-    for i in unset:
-        if status_of(i["id"]) in (None, "Done"):
-            graphql(SET_STATUS, p=project, i=i["id"], f=field, o=options["Backlog"])
-            written.add(i["n"])
+        graphql(SET_STATUS, p=project, i=item, f=field, o=options[want])
+        written[x["n"]] = want
+    for i, want in fix:
+        if status_of(i["id"]) == i["status"]:
+            graphql(SET_STATUS, p=project, i=i["id"], f=field, o=options[want])
+            written[i["n"]] = want
     if written:
-        items = assume_backlog(
-            read_until(lambda: read_board(owner, number, repo)[3], written), written)
-    return project, authors, items
+        items = assume_status(
+            read_until(lambda: read_board(owner, number, repo)[3], set(written)), written)
+    return project, authors, maintainer, items
 
 
 def issue(*args):
@@ -339,14 +407,14 @@
 
 
 def cmd_sync():
-    _, authors, items = sync()
-    print(json.dumps(state(items, authors, datetime.datetime.now(datetime.timezone.utc).date()),
-                     indent=1))
+    _, authors, maintainer, items = sync()
+    today = datetime.datetime.now(datetime.timezone.utc).date()
+    print(json.dumps(state(items, authors, today, maintainer), indent=1))
 
 
 def cmd_apply(path):
     plan = load_plan(path)
-    project, authors, items = sync()
+    project, authors, _, items = sync()
     monday = datetime.datetime.now(datetime.timezone.utc).date().isoweekday() == 1
     errors = check(plan, items, monday)
     if errors:
@@ -370,24 +438,35 @@
 
 
 def cmd_gate(want):
-    owner, number, authors, repo = env()
+    owner, number, authors, repo, maintainer = env()
     with open("agents/roles.json") as fh:
         roles = json.load(fh)
-    got, skipped = pick(read_board(owner, number, repo)[3], authors, roles, want)
+    got, skipped = pick(read_board(owner, number, repo)[3], authors, roles, want, maintainer)
     for line in skipped:
         print(line, file=sys.stderr)
     if got:
         print(f"{got[0]}\t{got[1]}")
 
 
+def cmd_analyst():
+    owner, number, _, repo, maintainer = env()
+    focus, reason = analyst_focus(read_board(owner, number, repo)[3], maintainer)
+    if focus:
+        print(focus)
+    else:
+        print(reason, file=sys.stderr)
+
+
 def main(argv):
     if len(argv) == 2 and argv[0] == "gate":
         return cmd_gate(argv[1])
+    if argv == ["analyst"]:
+        return cmd_analyst()
     if argv == ["sync"]:
         return cmd_sync()
     if len(argv) == 2 and argv[0] == "apply":
         return cmd_apply(argv[1])
-    sys.exit("usage: backlog.py gate <worker|role> | sync | apply <backlog.json>")
+    sys.exit("usage: backlog.py gate <worker|role> | analyst | sync | apply <backlog.json>")
 
 
 if __name__ == "__main__":
```

- [ ] **Step 4: Run, expect pass**

Run: `python3 .github/scripts/test_backlog.py | grep -c '^ok'` and `uvx pyflakes .github/scripts/`
Expected: `49`, and no pyflakes output.

- [ ] **Step 5: Commit**

```bash
git add .github/scripts/backlog.py .github/scripts/test_backlog.py
git commit -m "Teach the board model focus areas and the focus scope of work."
```

---

### Task 2: Gate and workflows

**Files:**
- Modify: `.github/scripts/agent-gate.sh`
- Modify: `.github/workflows/agents.yml`
- Modify: `.github/workflows/upstream.yml`

**Interfaces:**
- Consumes: CLI `backlog.py analyst` (Task 1).
- Produces: gate output `focus=<n>` for the analyst.

- [ ] **Step 1: Analyst only on a focus**

In `.github/scripts/agent-gate.sh` replace

```bash
if [ "$want" = product-owner ] || [ "$want" = analyst ]; then
  say "go: $want" true
fi
```

with

```bash
if [ "$want" = product-owner ]; then
  say "go: $want" true
fi
# The analyst reviews one focus area; without a focus it does not run.
if [ "$want" = analyst ]; then
  if ! focus=$(python3 .github/scripts/backlog.py analyst); then
    echo "run=false" >> "$out"; echo "backlog.py analyst failed" >&2; exit 1
  fi
  [ -n "$focus" ] || say "analyst idle" false
  echo "focus=$focus" >> "$out"
  say "go: analyst on focus #$focus" true
fi
```

Run: `bash -n .github/scripts/agent-gate.sh`. Expected: no output.

- [ ] **Step 2: Maintainer variable and analyst input in `agents.yml`**

Under each of the three lines `BACKLOG_AUTHORS: ${{ vars.BACKLOG_AUTHORS }}` (steps Gate, Sync the board, Apply the plan) add, with the same indent:

```yaml
          BACKLOG_MAINTAINER: ${{ vars.BACKLOG_MAINTAINER }}
```

Replace the `extra_prompt` line of step "Run the role" with:

```yaml
          extra_prompt: "${{ steps.gate.outputs.issue && format('Work issue number {0}. It was chosen by the gate; skip the pick.', steps.gate.outputs.issue) || steps.gate.outputs.focus && format('Review focus issue number {0}. It was chosen by the gate.', steps.gate.outputs.focus) || steps.sync.outputs.prompt || '' }}"
```

- [ ] **Step 3: Pause for `upstream.yml`**

In `.github/workflows/upstream.yml`, job `poll`, after `name: poll and watch` add:

```yaml
    # AGENTS_ENABLED false pauses the team; a dispatch still runs.
    if: github.event_name == 'workflow_dispatch' || vars.AGENTS_ENABLED == 'true'
```

- [ ] **Step 4: Lint and check**

Run the two workflow linters. Expected: no findings.
Run: `grep -c BACKLOG_MAINTAINER .github/workflows/agents.yml`. Expected: `3`.

- [ ] **Step 5: Commit**

```bash
git add .github/scripts/agent-gate.sh .github/workflows/agents.yml .github/workflows/upstream.yml
git commit -m "Start the analyst on a focus area and pause the upstream poll with the team."
```

---

### Task 3: Template and prompts

**Files:**
- Create: `.github/ISSUE_TEMPLATE/focus.yml`
- Modify: `agents/product-owner.md`, `agents/analyst.md`, `agents/skills/backlog.md`, `agents/CONTEXT.md`, `agents/skills/self-improvement.md`

- [ ] **Step 1: Focus template**

`.github/ISSUE_TEMPLATE/focus.yml`:

```yaml
name: Focus
description: An area the agents work on until the maintainer closes this issue.
title: "[Focus] "
labels: ["focus", "from-maintainer"]
projects: ["nfft-docs-agents/1"]
body:
  - type: textarea
    id: goal
    attributes:
      label: Goal
      description: What the reader can do when this focus is done, and why it matters now.
    validations:
      required: true
  - type: textarea
    id: scope
    attributes:
      label: Scope
      description: Pages, nav sections, API modules. One per line.
      placeholder: "doc/install/\nAPI module nfsft"
    validations:
      required: true
  - type: textarea
    id: out
    attributes:
      label: Out of scope
  - type: textarea
    id: done
    attributes:
      label: Done when
      description: Checks a reader can verify.
      value: "- [ ] "
    validations:
      required: true
```

- [ ] **Step 2: Product owner**

In `agents/product-owner.md`:

1. Inputs, first bullet: replace `\`next\` (the maintainer's, in the maintainer's order) and \`backlog\` (yours\n  to order), and \`stale_review\`.` with `\`next\` (the maintainer's, in the maintainer's order), \`focus\` (the\n  maintainer's focus areas, most important first, each with its open\n  sub-issues \`sub\` and the number \`ready\` of them with \`ready-for-agent\`),\n  \`backlog\` (yours to order), and \`stale_review\`.`
2. Step 1, after the bullet `- Unclear: ...`, add:

```
   - A `focus` issue by the maintainer: remove `needs-triage`. Never add
     `ready-for-agent` or a type label to it.
```

3. Step 3b: replace the sentence `Criteria,\n   in order: the targets in \`CONTEXT.md\`, dependencies between issues (an\n   issue goes after the issues it needs), small before large at equal value.` with:

```
Order: the
   maintainer's issues, then `upstream` issues, then focus work in the order
   of `focus` (an issue is focus work if it is in the `sub` list of a
   focus), then `meta` issues, then the rest. Workers never take the rest.
   Inside each group: an issue goes after the issues it needs, small before
   large at equal value.
```

   and replace `Never list an item of\n   \`next\`: the maintainer owns that column` with `Never list an item of\n   \`next\` or \`focus\`: the maintainer owns these columns`.
4. Replace step 5 with:

```
5. File new issues only for the focus areas in `focus`, in their order. For
   each focus with `ready` below 5: first link open issues that match its
   scope as sub-issues (see the `backlog` skill), then file new issues as
   sub-issues until `ready` is 5, at most 5 new issues per focus per run.
   Sources inside the scope: the focus brief, `coverage.json` gaps, `no`
   rows of the coverage matrix, formulas without a source citation. Each
   issue uses the matching template fields and ends with acceptance
   criteria an agent can check. Label `ready-for-agent` directly. `focus`
   is empty: file no issues in this step.
5b. A focus with no open sub-issue and no further gap inside its scope:
   comment `This focus looks done: <reason>` on the focus issue, once. Read
   its comments first. Never close a focus issue.
```

- [ ] **Step 3: Analyst**

In `agents/analyst.md`, replace step 1 with:

```
1. The input of this run names a focus issue. Read it: goal, scope, out of
   scope, done when. Review the pages and API modules in its scope.
```

In step 5 replace `File one issue \`Analysis: <section>\`` with `File one issue \`Analysis: #<focus number>\`` and replace `with the type label and\n   acceptance criteria, label \`needs-triage\`.` with `with the type label and\n   acceptance criteria, label \`needs-triage\`. Link each of them as a\n   sub-issue of the focus (see the \`backlog\` skill).` Under `## Stop conditions` replace `One section.` with `One focus.`

- [ ] **Step 4: Backlog skill**

In `agents/skills/backlog.md`:

1. Label table, row `Maintainer input`: becomes `| Maintainer input | \`decision\` (a ruling to record in \`agents/DECISIONS.md\`), \`focus\` (an area to work on) |`.
2. Replace the paragraph that starts with `Pick order: the board` with:

```
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

    parent=$(gh issue view <focus> --json id --jq .id)
    child=$(gh issue view <n> --json id --jq .id)
    gh api graphql -f query='mutation($p: ID!, $c: ID!) { addSubIssue(input: {issueId: $p, subIssueId: $c}) { issue { number } } }' -f p="$parent" -f c="$child"

An issue has at most one parent.
```

- [ ] **Step 5: Shared context and self-improvement**

In `agents/CONTEXT.md`: replace `Origin: \`from-maintainer\`, \`agent\`. \`stale-candidate\`, \`keep\`.` with `Origin: \`from-maintainer\`, \`agent\`. \`stale-candidate\`, \`keep\`. Maintainer:\n\`focus\`, \`decision\`.` and replace the line pair `Pick order: the board, \`Next\` then \`Backlog\`. The gate picks; see the \`backlog\`\nskill.` with `Pick order: the board, \`Next\` then \`Backlog\`, only work in scope of the\nmaintainer's focus areas and the exceptions. The gate picks; see the \`backlog\`\nskill.`

In `agents/skills/self-improvement.md`, after `every hour.` add ` \`AGENTS_ENABLED\` false pauses these crons and the upstream poll.`

- [ ] **Step 6: Check**

```bash
grep -rniE "load-bearing|seam|byte-identical|odometer" agents/
grep -n "Analysis: <section>\|One section" agents/analyst.md
```

Expected: no output from either. Run the two workflow linters. Expected: no findings.

- [ ] **Step 7: Commit**

```bash
git add .github/ISSUE_TEMPLATE/focus.yml agents/
git commit -m "Tell the agents to work on the maintainer's focus areas."
```

---

### Task 4: Rollout and live checks

Every step changes GitHub state. Ask the maintainer before each one.

- [ ] **Step 1: Board option (maintainer)**

Project settings, field `Status`: add option `Focus`, order `Next`, `Focus`, `Backlog`, `Done`.

- [ ] **Step 2: Variable and label**

```bash
gh variable set BACKLOG_MAINTAINER --body jenskeiner
gh label create focus --color b60205 --description "An area the agents work on, set by the maintainer"
```

- [ ] **Step 3: Local checks against board 1 (before merge)**

```bash
export GITHUB_REPOSITORY=jenskeiner/nfft-docs BACKLOG_OWNER=nfft-docs-agents BACKLOG_PROJECT=1 \
  BACKLOG_AUTHORS="jenskeiner claude[bot] github-actions[bot]" BACKLOG_MAINTAINER=jenskeiner \
  BOARD_TOKEN=$(gh auth token)
python3 .github/scripts/backlog.py analyst; echo "exit=$?"
GITHUB_OUTPUT=/dev/null bash .github/scripts/agent-gate.sh worker
python3 .github/scripts/backlog.py gate worker
```

Expected with no focus open: `no focus` on stderr, exit 0; the gate logs `skip #<n>: outside focus` for agent issues and picks one of the maintainer's ready issues or none.

- [ ] **Step 4: First focus (maintainer)**

The maintainer files a real focus issue from the template. Then link one ready agent issue that matches it as a sub-issue (commands from the `backlog` skill, confirm the issue with the maintainer), run `backlog.py sync` and the commands of Step 3 again.

Expected: the focus issue is in `Focus`; `analyst` prints its number; the gate picks the sub-issue, or reports the cap.

- [ ] **Step 5: PR and merge**

Push the branch, open a PR to `develop`, checks green, the maintainer merges.

- [ ] **Step 6: Pause check**

`gh variable set AGENTS_ENABLED --body false`. After the next `upstream.yml` cron time (`17 */6 * * *`): `gh run list --workflow upstream.yml --limit 1` shows the run with job `poll` skipped. `gh variable set AGENTS_ENABLED --body true`.

- [ ] **Step 7: Product owner run**

`gh workflow run agents.yml --ref develop -f role=product-owner`. Expected: job `role` and job `apply` green; the state in the sync step log has a `focus` list; new issues of this run are sub-issues of the focus.
