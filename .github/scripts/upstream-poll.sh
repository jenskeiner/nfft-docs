#!/usr/bin/env bash
# Compares the pinned submodule with NFFT/nfft develop. On a change, bumps the
# submodule on a branch, runs the checks, opens a PR. Writes old, new and pr to
# GITHUB_OUTPUT. Shell only, no model call.
set -euo pipefail
out="${GITHUB_OUTPUT:-/dev/stdout}"
old=$(git -C nfft rev-parse HEAD)
new=$(git ls-remote https://github.com/NFFT/nfft.git refs/heads/develop | cut -f1)
echo "old=$old" >> "$out"; echo "new=$new" >> "$out"

if [ "$old" = "$new" ]; then echo "up to date at ${old:0:12}"; echo "pr=" >> "$out"; exit 0; fi
if [ "$(gh pr list --label upstream --state open --json number --jq length)" -gt 0 ]; then
  echo "an upstream PR is already open"; echo "pr=" >> "$out"; exit 0
fi
if [ "$(gh pr list --label agent --state open --json number --jq length)" -ge 3 ]; then
  echo "cap reached"; echo "pr=" >> "$out"; exit 0
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
git push -q -u origin "$branch"

body=$(mktemp)
{
  echo "## Goal"; echo; echo "Follow NFFT/nfft develop from \`${old:0:12}\` to \`${new:0:12}\`."; echo
  echo "## Changes"; echo; echo "- Submodule bump."; echo "- Mechanical fixes by the checks, if any, are in the commits that follow."; echo
  echo "Upstream log:"; echo; echo '```'; git -C nfft log --oneline "$old..$new" | head -50; echo '```'; echo
  echo "## Verification"; echo; echo "Checks on the bump, status $status:"; echo; cat "$log"
} > "$body"
pr=$(gh pr create --base develop --head "$branch" --title "Bump NFFT to ${new:0:12}" \
     --label agent --label upstream --body-file "$body" --json number --jq .number 2>/dev/null \
     || gh pr list --head "$branch" --json number --jq '.[0].number')
echo "pr=$pr" >> "$out"
echo "opened PR #$pr, checks status $status"
