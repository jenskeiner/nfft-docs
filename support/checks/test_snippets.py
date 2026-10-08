"""Checks for the snippet drift lock. Run from the repository root:

    python support/checks/test_snippets.py
"""

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def run(cmd, cwd):
    return subprocess.run([sys.executable, "-m", "support.checks.snippets"] + cmd, cwd=cwd,
                          capture_output=True, text=True, env={**os.environ, "PYTHONPATH": ROOT})


def setup(d):
    os.makedirs(os.path.join(d, "doc"))
    os.makedirs(os.path.join(d, "nfft", "examples"))
    with open(os.path.join(d, "nfft", "examples", "a.c"), "w") as fh:
        fh.write("line1\nline2\nline3\nline4\n")
    with open(os.path.join(d, "doc", "page.md"), "w") as fh:
        fh.write('Text\n\n```c\n--8<-- "examples/a.c:2:3"\n```\n')


def test_update_writes_one_lock_line():
    with tempfile.TemporaryDirectory() as d:
        setup(d)
        r = run(["update"], d)
        assert r.returncode == 0, r.stderr
        lock = open(os.path.join(d, "support", "checks", "snippets.lock")).read().splitlines()
        assert len(lock) == 1 and lock[0].startswith("doc/page.md\texamples/a.c:2:3\t"), lock


def test_check_fails_after_drift_and_relocate_fixes_it():
    with tempfile.TemporaryDirectory() as d:
        setup(d)
        assert run(["update"], d).returncode == 0
        assert run(["check"], d).returncode == 0
        with open(os.path.join(d, "nfft", "examples", "a.c"), "w") as fh:
            fh.write("new0\nline1\nline2\nline3\nline4\n")
        r = run(["check"], d)
        assert r.returncode == 1 and "examples/a.c:2:3" in r.stdout, r.stdout
        r = run(["relocate"], d)
        assert r.returncode == 0, r.stdout + r.stderr
        page = open(os.path.join(d, "doc", "page.md")).read()
        assert '"examples/a.c:3:4"' in page, page
        assert run(["check"], d).returncode == 0


def test_relocate_reports_missing_block():
    with tempfile.TemporaryDirectory() as d:
        setup(d)
        assert run(["update"], d).returncode == 0
        with open(os.path.join(d, "nfft", "examples", "a.c"), "w") as fh:
            fh.write("gone\n")
        r = run(["relocate"], d)
        assert r.returncode == 1 and "NOMATCH" in r.stdout, r.stdout


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
