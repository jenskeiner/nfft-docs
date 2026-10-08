# NFFT3 documentation site

Sources of the documentation site for the [NFFT3](https://github.com/NFFT/nfft)
library, built with [Zensical](https://zensical.org) and published at
https://jenskeiner.github.io/nfft-docs/.

The C sources are not here. `nfft/` is a git submodule pinned to a commit of
`NFFT/nfft` `develop`. The API reference is generated from
`nfft/include/nfft3.h`; doc text that the header lacks lives in `overlay/api/`.

## Build

```bash
git submodule update --init
uv run python -m support.apigen
uv run --with-requirements support/docs-requirements.txt zensical build --strict
uv run python -m support.checks.site
```

Preview with `zensical serve` in place of `build --strict`.

## Checks

```bash
uv run python -m support.apigen.test_apigen
uv run python -m support.apigen.test_overlay
uv run python -m support.checks.snippets check
uv run python -m support.checks.overlay
```

## Agents

A team of Claude Code agents improves the site unattended and opens pull
requests. Roles, rules, skills (`agents/plugin/skills/`) and the backlog policy are in `agents/`. Design and
plan: `docs/plans/`.
