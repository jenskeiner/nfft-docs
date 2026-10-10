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


def test_main_rejects_unknown_command():
    try:
        backlog.main(["nope"])
    except SystemExit as e:
        assert "usage" in str(e.code), e.code
    else:
        raise AssertionError("no exit")


def board(*specs):
    return items(*[node(n, s, author=a) for n, s, a in specs])


U, B = ("User", "jenskeiner"), ("Bot", "claude")


def test_check_accepts_valid_plan():
    its = board((1, "Backlog", U), (2, "Next", U))
    assert backlog.check({"order": [1], "stale": [{"n": 2, "reason": "done"}]}, its, True) == []


def test_check_rejects_bad_shapes():
    its = board((1, "Backlog", U))
    for plan in ([1], {"order": "1"}, {"order": ["1"]}, {"order": [True]},
                 {"order": [1], "extra": 1}, {"order": [1], "stale": [{"n": 1}]},
                 {"order": [1], "stale": [{"n": 1, "reason": " "}]}):
        assert backlog.check(plan, its, True), plan


def test_check_rejects_duplicates_and_unknown():
    its = board((1, "Backlog", U), (2, "Backlog", U))
    assert any("duplicate" in e for e in backlog.check({"order": [1, 1, 2]}, its, True))
    assert any("not on the board" in e for e in backlog.check({"order": [1, 2, 9]}, its, True))
    assert any("not on the board" in e for e in
               backlog.check({"order": [1, 2], "stale": [{"n": 9, "reason": "x"}]}, its, True))


def test_check_limits_stale():
    its = board(*[(n, "Backlog", B) for n in range(1, 13)])
    plan = {"order": list(range(1, 13)), "stale": [{"n": n, "reason": "x"} for n in range(1, 12)]}
    assert any("at most 10" in e for e in backlog.check(plan, its, True))


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
    assert got == [("I3", None)], got


def test_stale_closes_agent_issues_and_labels_others():
    its = board((1, "Backlog", B), (2, "Next", U))
    got = backlog.stale_actions([{"n": 1, "reason": "a\n  b"}, {"n": 2, "reason": "c"}], its, AUTHORS)
    assert got == [("close", 1, "a b"), ("label", 2, "c")], got


def test_stale_skips_candidate_keep_and_closed():
    its = items(node(1, labels=("gap", "stale-candidate")), node(2, state="CLOSED", author=B),
                node(3, labels=("gap", "keep"), author=B))
    stale = [{"n": n, "reason": "x"} for n in (1, 2, 3)]
    assert backlog.stale_actions(stale, its, AUTHORS) == []


def test_stale_truncates_reason():
    its = board((1, "Backlog", B))
    got = backlog.stale_actions([{"n": 1, "reason": "x" * 400}], its, AUTHORS)
    assert len(got[0][2]) == 300, got


def test_plan_sync_adds_missing_and_fixes_empty_status():
    its = board((1, "Backlog", U), (2, None, U))
    issues = [{"n": 1, "id": "N1", "author": "jenskeiner"},
              {"n": 3, "id": "N3", "author": "claude[bot]"},
              {"n": 4, "id": "N4", "author": "stranger"}]
    add, unset = backlog.plan_sync(its, issues, AUTHORS)
    assert [x["n"] for x in add] == [3] and [i["n"] for i in unset] == [2], (add, unset)


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


def test_moves_only_items_whose_predecessor_changed():
    its = board(*[(n, "Backlog", U) for n in range(1, 6)])
    got = backlog.moves(its, AUTHORS, backlog.final_order([1, 2, 3, 5, 4], its, AUTHORS))
    assert got == [("I5", "I3")], got


def test_check_rejects_stale_outside_monday():
    its = board((1, "Backlog", B))
    plan = {"order": [1], "stale": [{"n": 1, "reason": "x"}]}
    assert any("Monday" in e for e in backlog.check(plan, its, False))
    assert backlog.check({"order": [1], "stale": []}, its, False) == []


def test_stale_labels_agent_issue_in_next():
    its = board((1, "Next", B))
    assert backlog.stale_actions([{"n": 1, "reason": "x"}], its, AUTHORS) == [("label", 1, "x")]


def test_stale_skips_foreign_authors():
    its = items(node(1, author=("User", "stranger")))
    assert backlog.stale_actions([{"n": 1, "reason": "x"}], its, AUTHORS) == []


def test_plan_sync_resets_reopened_done_items():
    its = items(node(1, "Done"), node(2, "Done", state="CLOSED"))
    add, unset = backlog.plan_sync(its, [{"n": 1, "id": "N1", "author": "jenskeiner"}], AUTHORS)
    assert add == [] and [i["n"] for i in unset] == [1], (add, unset)


def test_assume_backlog_marks_items_the_sync_wrote():
    its = items(node(1, None), node(2, "Done"), node(3, "Next"), node(4, None))
    got = backlog.assume_backlog(its, {1, 2})
    assert [(i["n"], i["status"]) for i in got] == [(1, "Backlog"), (2, "Backlog"),
                                                    (3, "Next"), (4, None)], got


def test_read_until_waits_for_written_items():
    reads = iter([items(node(1)), items(node(1)), items(node(1), node(2))])
    slept = []
    got = backlog.read_until(lambda: next(reads), {1, 2}, sleep=slept.append)
    assert [i["n"] for i in got] == [1, 2] and slept == [2.0, 4.0], (got, slept)


def test_read_until_gives_up_with_a_message():
    try:
        backlog.read_until(lambda: items(node(1)), {1, 2}, sleep=lambda s: None)
    except SystemExit as e:
        assert "[2] not readable" in str(e.code), e.code
    else:
        raise AssertionError("no exit")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
