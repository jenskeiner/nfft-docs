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
if [ "$want" != analyst ] && [ "$open" -ge "$cap" ]; then
  say "cap reached: $open agent PRs open" false
fi
if [ "$want" = product-owner ] || [ "$want" = analyst ]; then
  say "go: $want" true
fi

# Worker, or a named worker role from a dispatch: pick the best ready issue
# whose type a role handles. Order: from-maintainer, priority: high, oldest.
if [ "$want" = worker ]; then
  candidates=$(jq -r 'to_entries[] | select(.key != "_comment") | .key' "$roles")
else
  jq -e --arg r "$want" '.[$r]' "$roles" >/dev/null || { echo "unknown role $want" >&2; exit 1; }
  candidates="$want"
fi

best=""
for role in $candidates; do
  for t in $(jq -r --arg r "$role" '.[$r].types[]' "$roles"); do
    gh issue list --label ready-for-agent --label "$t" --state open --limit 100 \
      --json number,createdAt,labels \
      --jq '.[] | select(all(.labels[].name; . != "in-progress" and . != "blocked"))
             | [ (if any(.labels[].name; . == "from-maintainer") then 0 else 1 end),
                 (if any(.labels[].name; . == "priority: high") then 0 else 1 end),
                 .createdAt, (.number|tostring), "'"$role"'" ] | @tsv'
  done
done | sort -t$'\t' -k1,1n -k2,2n -k3,3 | head -1 > /tmp/pick.tsv

if [ ! -s /tmp/pick.tsv ]; then say "no ready issue for $want" false; fi
issue=$(cut -f4 /tmp/pick.tsv); role=$(cut -f5 /tmp/pick.tsv)
{
  echo "role=$role"
  echo "model=$(jq -r --arg r "$role" '.[$r].model' "$roles")"
  echo "max_turns=$(jq -r --arg r "$role" '.[$r].max_turns' "$roles")"
  echo "issue=$issue"
} >> "$out"
say "go: $role on issue #$issue" true
