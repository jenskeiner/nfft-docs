#!/usr/bin/env bash
# Compares the pinned submodule with NFFT/nfft develop. On a change, bumps the
# submodule on a local branch, runs the checks and writes a PR body. The model
# step pushes and opens the PR with the app token, so the PR checks run. Writes
# old, new, bump, branch, body and status to GITHUB_OUTPUT.
set -euo pipefail
out="${GITHUB_OUTPUT:-/dev/stdout}"
old=$(git -C nfft rev-parse HEAD)
new=$(git ls-remote https://github.com/NFFT/nfft.git refs/heads/develop | cut -f1)
echo "old=$old" >> "$out"; echo "new=$new" >> "$out"

if [ "$old" = "$new" ]; then echo "up to date at ${old:0:12}"; echo "bump=false" >> "$out"; exit 0; fi
if [ "$(gh pr list --label upstream --state open --json number --jq length)" -gt 0 ]; then
  echo "an upstream PR is already open"; echo "bump=false" >> "$out"; exit 0
fi
if [ "$(gh pr list --label agent --state open --json number --jq length)" -ge 3 ]; then
  echo "cap reached"; echo "bump=false" >> "$out"; exit 0
fi

branch="upstream/${new:0:8}"
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git checkout -b "$branch"
git -C nfft fetch --depth 1 origin "$new"
git -C nfft checkout -q "$new"
git add nfft

log=$(mktemp)
status=0
{
  echo '```'
  uv run python -m support.apigen || status=1
  uv run python -m support.checks.overlay || status=1
  uv run python -m support.checks.snippets check || uv run python -m support.checks.snippets relocate || status=1
  uv run --with-requirements support/docs-requirements.txt zensical build --strict || status=1
  uv run python -m support.checks.site || status=1
  echo '```'
} > "$log" 2>&1 || true

git add -A
git commit -q -m "Bump NFFT to ${new:0:12}."

body=$(mktemp)
{
  echo "## Goal"; echo; echo "Follow NFFT/nfft develop from \`${old:0:12}\` to \`${new:0:12}\`."; echo
  echo "## Changes"; echo; echo "- Submodule bump."; echo "- Mechanical fixes by the checks, if any, are in the commits that follow."; echo
  echo "Upstream log:"; echo; echo '```'; git -C nfft log --oneline "$old..$new" | head -50; echo '```'; echo
  echo "## Verification"; echo; echo "Checks on the bump, status $status:"; echo; cat "$log"
} > "$body"
{ echo "bump=true"; echo "branch=$branch"; echo "body=$body"; echo "status=$status"; } >> "$out"
echo "bump prepared on $branch, checks status $status"
