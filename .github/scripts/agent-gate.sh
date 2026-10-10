#!/usr/bin/env bash
# Usage: agent-gate.sh <role>
# Decides in shell, before any model call, whether a role may run now, and
# for `worker` which role from agents/roles.json runs on which issue.
# Writes run, role, model, max_turns, issue to GITHUB_OUTPUT.
set -euo pipefail
want="${1:?role}"
cap=3
out="${GITHUB_OUTPUT:-/dev/stdout}"
roles=agents/roles.json

say() { echo "$1"; echo "run=$2" >> "$out"; exit 0; }

case "$want" in
  product-owner) echo "role=product-owner" >> "$out"; echo "model=claude-opus-5-5" >> "$out"; echo "max_turns=80" >> "$out" ;;
  analyst)       echo "role=analyst" >> "$out";       echo "model=claude-opus-5-5" >> "$out"; echo "max_turns=60" >> "$out" ;;
  worker|*) ;;
esac

open=$(gh pr list --label agent --state open --json number --jq length)
# The product owner opens at most its housekeeping PR, under its own rule.
if [ "$want" != analyst ] && [ "$want" != product-owner ] && [ "$open" -ge "$cap" ]; then
  say "cap reached: $open agent PRs open" false
fi
if [ "$want" = product-owner ] || [ "$want" = analyst ]; then
  say "go: $want" true
fi

# Worker, or a named worker role from a dispatch: the first ready issue on the
# board, Next before Backlog, in board order, whose type a role handles.
if [ "$want" != worker ]; then
  jq -e --arg r "$want" '.[$r]' "$roles" >/dev/null || { echo "unknown role $want" >&2; exit 1; }
fi
if ! pick=$(python3 .github/scripts/backlog.py gate "$want"); then
  echo "run=false" >> "$out"; echo "backlog.py gate failed" >&2; exit 1
fi
[ -n "$pick" ] || say "no ready issue for $want" false
issue=$(cut -f1 <<<"$pick"); role=$(cut -f2 <<<"$pick")
{
  echo "role=$role"
  echo "model=$(jq -r --arg r "$role" '.[$r].model' "$roles")"
  echo "max_turns=$(jq -r --arg r "$role" '.[$r].max_turns' "$roles")"
  echo "issue=$issue"
} >> "$out"
say "go: $role on issue #$issue" true
