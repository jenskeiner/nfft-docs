"""Lock the line ranges of `--8<--` snippets against the files they cut.

    python -m support.checks.snippets check      exit 1 if any block changed
    python -m support.checks.snippets update     rewrite the lock
    python -m support.checks.snippets relocate   find each locked block in the
                                                 current file, rewrite the range

Snippet paths resolve against nfft/ first, then the repository root, like
`pymdownx.snippets.base_path` in zensical.toml. The lock holds one line per
snippet: doc file, path:a:b, sha256 of the block.
"""

import glob
import hashlib
import os
import re
import sys

DOC = "doc"
LOCK = os.path.join("support", "checks", "snippets.lock")
BASES = ["nfft", "."]
SNIP = re.compile(r'--8<--\s*"([^":]+):(\d+):(\d+)"')


def resolve(path):
    for base in BASES:
        p = os.path.join(base, path)
        if os.path.isfile(p):
            return p
    sys.exit(f"snippet source not found: {path}")


def lines_of(path):
    return open(resolve(path)).read().split("\n")


def digest(block):
    return hashlib.sha256("\n".join(block).encode()).hexdigest()


def scan():
    out = []
    for page in sorted(glob.glob(os.path.join(DOC, "**", "*.md"), recursive=True)):
        for m in SNIP.finditer(open(page).read()):
            out.append((page, m.group(1), int(m.group(2)), int(m.group(3))))
    return out


def current():
    return {(page, f"{path}:{a}:{b}"): digest(lines_of(path)[a - 1:b])
            for page, path, a, b in scan()}


def read_lock():
    if not os.path.isfile(LOCK):
        return {}
    out = {}
    for ln in open(LOCK).read().splitlines():
        page, spec, sha = ln.split("\t")
        out[(page, spec)] = sha
    return out


def cmd_update():
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    with open(LOCK, "w") as fh:
        for (page, spec), sha in sorted(current().items()):
            fh.write(f"{page}\t{spec}\t{sha}\n")
    print(f"{len(current())} snippets locked")
    return 0


def cmd_check():
    lock, now = read_lock(), current()
    bad = [k for k in now if lock.get(k) != now[k]]
    for page, spec in bad:
        print(f"changed or unlocked: {page} {spec}")
    print(f"{len(now)} snippets, {len(bad)} drifted")
    return 1 if bad else 0


def cmd_relocate():
    lock = read_lock()
    failed = 0
    for page, path, a, b in scan():
        spec = f"{path}:{a}:{b}"
        sha = lock.get((page, spec))
        src = lines_of(path)
        if sha is None or digest(src[a - 1:b]) == sha:
            continue
        n = b - a + 1
        hits = [i + 1 for i in range(len(src) - n + 1) if digest(src[i:i + n]) == sha]
        if len(hits) != 1:
            print(f"NOMATCH {page} {spec} ({len(hits)} candidates)")
            failed += 1
            continue
        new = f"{path}:{hits[0]}:{hits[0] + n - 1}"
        text = open(page).read().replace(f'"{spec}"', f'"{new}"')
        open(page, "w").write(text)
        print(f"moved {page} {spec} -> {new}")
    if failed:
        return 1
    return cmd_update()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    sys.exit({"check": cmd_check, "update": cmd_update, "relocate": cmd_relocate}[cmd]())
