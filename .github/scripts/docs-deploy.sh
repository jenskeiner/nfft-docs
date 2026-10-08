#!/usr/bin/env bash
# Usage: docs-deploy.sh <version> [<alias>]
#
# Deploys the documentation site to the gh-pages branch with mike.
#
# mike runs `zensical build --clean` itself, without --strict and without the
# API generator, so it would happily publish a site with every api/ page
# missing. Generate and gate first, then let mike rebuild.
set -euo pipefail
version="${1:?usage: docs-deploy.sh <version> [<alias>]}"
alias="${2:-}"

uv run python -m support.apigen
uv run --with-requirements support/docs-requirements.txt zensical build --strict
uv run python -m support.checks.site

git config user.name ci
git config user.email ci@nfft

run_mike() {
  uv run --with-requirements support/docs-requirements.txt mike "$@"
}

if [ -n "$alias" ]; then
  run_mike deploy --push --update-aliases "$version" "$alias"
  # Only a named alias becomes the default landing page; `dev` must not.
  if [ "$alias" = "latest" ]; then
    run_mike set-default --push latest
  fi
else
  run_mike deploy --push "$version"
fi
