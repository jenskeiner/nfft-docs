#!/usr/bin/env bash
# Usage: agent-gate.sh <role>
# Decides in shell, before any model call, whether a role may run now.
# Writes run=true|false to GITHUB_OUTPUT.
set -euo pipefail
role="${1:?role}"
cap=3

say() { echo "$1"; echo "run=$2" >> "${GITHUB_OUTPUT:-/dev/stdout}"; exit 0; }

case "$role" in
  writer)  types="gap new-section api-gap math" ;;
  editor)  types="style clarity" ;;
  product-owner|analyst|upstream-watcher|responder) types="" ;;
  *) echo "unknown role $role" >&2; exit 1 ;;
esac

if [ "$role" = writer ] || [ "$role" = editor ] || [ "$role" = product-owner ]; then
  open=$(gh pr list --label agent --state open --json number --jq length)
  [ "$open" -ge "$cap" ] && say "cap reached: $open agent PRs open" false
fi

if [ -n "$types" ]; then
  ready=0
  for t in $types; do
    n=$(gh issue list --label ready-for-agent --label "$t" --state open --json number,labels \
        --jq '[.[] | select(all(.labels[].name; . != "in-progress" and . != "blocked"))] | length')
    ready=$((ready + n))
  done
  [ "$ready" -eq 0 ] && say "no ready issue for $role" false
fi

say "go: $role" true
