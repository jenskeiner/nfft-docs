#!/usr/bin/env bash
# Builds the skills plugin agents/plugin/ from agents/skills/<name>.md.
# Claude Code treats everything under a --plugin-dir as sensitive and refuses
# every write there, by any tool. So the plugin is a gitignored build product
# and the sources are plain Markdown files that agents may edit.
set -euo pipefail
src=agents/skills
out=agents/plugin
rm -rf "$out"
mkdir -p "$out/.claude-plugin" "$out/skills"
cat > "$out/.claude-plugin/plugin.json" <<'JSON'
{
  "name": "nfft-agents",
  "version": "0.1.0",
  "description": "Skills of the NFFT3 documentation agents, assembled from agents/skills/ by .github/scripts/assemble-plugin.sh."
}
JSON
n=0
for f in "$src"/*.md; do
  name=$(basename "$f" .md)
  grep -q "^name: $name$" "$f" || { echo "$f: front matter name must be $name" >&2; exit 1; }
  mkdir -p "$out/skills/$name"
  cp "$f" "$out/skills/$name/SKILL.md"
  n=$((n + 1))
done
echo "$n skills assembled into $out"
