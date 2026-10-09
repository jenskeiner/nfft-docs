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


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
