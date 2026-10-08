# NFFT docs repository with an unattended agent team

Design spec, 2026-10-08. Moves to `docs/specs/` of the new repository at M0.

## 1. Goal

A public repository `jenskeiner/nfft-docs` that holds the Zensical site from
`feature/docs-site`, builds it against `NFFT/nfft@develop`, publishes it on
GitHub Pages, and lets a team of Claude Code agents improve it unattended over
months through pull requests that the maintainer reviews.

Targets, in order:

1. Topic parity with nfft.org. Inventory in section 10.
2. API reference generated from `nfft3.h`, gaps filled by agents in an overlay.
3. Complete description of the mathematics and terminology.
4. Coverage parity with fftw.org and FINUFFT docs for installation, building,
   usage, options, performance, troubleshooting, interfaces, migration.
5. Docs follow upstream: each change on `NFFT/nfft@develop` is checked.

Non-goals: editing `NFFT/nfft`, auto-merge, copying external text.

## 2. Decisions

| ID | Decision | Rejected |
|----|----------|----------|
| D1 | GitHub Actions with `anthropics/claude-code-action@v1`. Prompts, skills and roles versioned in-tree. | claude.ai routines: outside git. |
| D2 | `NFFT/nfft` is a git submodule at `nfft/`, pinned SHA, bumped by a poll job. | Clone at build: no reproducible builds, no diff to watch. |
| D3 | C-side doc text lives in `overlay/api/<module>/<symbol>.md`. `apigen` merges overlay over header comments, overlay wins. Seeded once from this branch's `nfft3.h`. | Merge header docs upstream first: blocks on an upstream PR. Fork branch: agents would edit C. |
| D4 | Auth `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token`, subscription allowance. | API key: pay per token. WIF: needs a Console org. |
| D5 | Upstream detection by polling every 6 h from the docs repo. | `repository_dispatch` from `NFFT/nfft`: needs a workflow and token there. |
| D6 | Backlog is GitHub Issues with labels. | Markdown backlog: no locking, no UI for the maintainer. |
| D7 | One workflow `agents.yml`, one cron per role, role chosen from `github.event.schedule`. | Orchestrator plus matrix: not needed at 3 PRs. |
| D8 | Hard cap 3 open PRs with label `agent`, enforced by a shell step before any token is spent. | Agent-side check: costs tokens, can be skipped. |
| D9 | Maintainer comments on agent PRs trigger a revision run. Only login `jenskeiner`. | `@claude` mention: extra step. Anyone with write: nobody else has write, but be explicit. |
| D10 | Merge by the maintainer after 1 approving review and green checks. No auto-merge. | Auto-merge on approval: user may opt in later. |
| D11 | Models: Opus for product-owner, writer, analyst. Sonnet for editor, upstream-watcher, responder. | Opus everywhere: cost. |
| D12 | Snippet drift check stores first and last line text per `--8<--` range. | Markers in upstream files: not on develop. |

## 3. Repository layout

```
zensical.toml                   ported, snippets base_path = ["nfft", "."]
doc/                            Markdown sources, ported
nfft/                           submodule NFFT/nfft, develop, pinned
overlay/api/<module>/<symbol>.md
support/apigen/                 ported, reads nfft/include/nfft3.h + overlay/
support/apigen/seed_overlay.py  one-off: header docs -> overlay files
support/checks/snippets.py      drift check, D12
support/checks/site.py          ported docs-check-site.py
support/checks/overlay.py       every overlay file names a real symbol
support/docs-requirements.txt   ported, pinned
agents/CONTEXT.md               goals, style, parity targets, rules
agents/<role>.md                one prompt per role
agents/coverage.md              coverage matrix, owned by product-owner
.claude/skills/<name>/SKILL.md
.github/ISSUE_TEMPLATE/*.yml
.github/PULL_REQUEST_TEMPLATE.md
.github/CODEOWNERS              * @jenskeiner
.github/actions/agent-setup/action.yml
.github/workflows/docs.yml      build, deploy dev to gh-pages via mike
.github/workflows/pr-checks.yml
.github/workflows/agents.yml
.github/workflows/agent-respond.yml
.github/workflows/upstream.yml
.github/dependabot.yml          github-actions weekly
docs/adr/, docs/specs/
```

### Overlay format

One file per public symbol, path `overlay/api/nfft/nfft_trafo.md`. Content is
the Markdown doc body as `apigen` renders it today. Front matter:

```
---
symbol: nfft_trafo
kind: function | struct | flag | macro
source: header | agent
---
```

`source: header` marks text seeded from this branch, `agent` marks text written
by agents. `apigen` reads header comments first, then overlay; an overlay file
replaces the header text for that symbol. `coverage.json` gains per symbol
`"doc": "header" | "overlay" | "none"`. `none` entries are the api-gap backlog.

## 4. Publishing

`docs.yml`: on `pull_request` build with `--strict` plus checks, upload the
site artifact. On `push` to `develop` deploy `dev` with mike, concurrency group
`gh-pages`. Pages serves the `gh-pages` branch. `release` and manual deploy
jobs ported as they are.

`pr-checks.yml` on `pull_request`: `apigen` parser test, `checks/snippets.py`,
`checks/overlay.py`, `checks/site.py`, lychee on external links
(`continue-on-error`), Vale with a small STE rule set in `.vale/`.

Branch protection on `develop`: PR required, required checks `build`,
`pr-checks`, 1 approving review, CODEOWNERS review, no force push, admins
included.

## 5. Roles

| Role | Trigger | Model | Output | Skills |
|------|---------|-------|--------|--------|
| product-owner | daily 05:00 UTC | Opus | Issues: triage `needs-triage`, dedup, rank, write acceptance criteria, update `agents/coverage.md`, release stale `in-progress` claims older than 12 h, file retro issue every 14 days. No PR. | backlog, site-comparison |
| writer | every 4 h | Opus | One PR for one `ready-for-agent` issue of type `gap`, `new-section`, `api-gap`, `math`. | writing-docs, api-overlay, math-from-sources, snippets |
| editor | every 8 h | Sonnet | One PR for one issue of type `style`, `clarity`. | writing-docs |
| analyst | every 2 days | Opus | Reads one section, files issues with evidence. No PR. | backlog, site-comparison |
| upstream-watcher | on submodule bump | Sonnet | Reads `git diff` of the bump. Files issues per affected page, or a PR for mechanical fixes of snippet ranges and API signatures. | snippets, api-overlay, backlog |
| responder | maintainer comment on agent PR | Sonnet | Edits the PR branch, replies on the thread. | writing-docs, api-overlay |

Priority order for pickers: `from-maintainer` first, then `priority: high`,
then oldest. Pickers skip issues with `in-progress` or `blocked`.

### Labels

Type: `gap`, `new-section`, `api-gap`, `math`, `style`, `clarity`, `compare`,
`upstream`. State: `needs-triage`, `ready-for-agent`, `in-progress`, `blocked`,
`wontfix`. Origin: `from-maintainer`, `agent`. Priority: `priority: high`.

## 6. Workflow `agents.yml`

```
on:
  schedule: one cron per role
  workflow_dispatch: input role
permissions: contents: write, pull-requests: write, issues: write, id-token: write
concurrency: group agents-${role}, cancel-in-progress: false
environment: agents
```

Steps:

1. Map `github.event.schedule` or the dispatch input to `role`.
2. Gate, shell only: for PR-making roles, `gh pr list --label agent --state open
   --json number | jq length`, exit 0 if 3 or more. Also exit if no
   `ready-for-agent` issue exists for the role's types.
3. `agent-setup` composite: checkout with submodule, uv, build once to warm
   the cache.
4. `claude-code-action@v1` with `prompt` = `agents/CONTEXT.md` + `agents/<role>.md`,
   `claude_args: --model <per role> --max-turns 80 --allowedTools
   "Read,Edit,Write,Glob,Grep,Bash(uv run:*),Bash(git:*),Bash(gh issue:*),Bash(gh pr:*),Bash(gh label:*)"`,
   `branch_prefix: agent/`, `base_branch: develop`.

Agent contract, in `CONTEXT.md`:

- Claim: label `in-progress`, comment with the run URL. Release on failure.
- One issue, one PR, one run. Never more.
- Before `gh pr create`: `uv run python -m support.apigen`, `zensical build
  --strict`, `uv run python support/checks/snippets.py`, `overlay.py`, `site.py`.
  All green, or do not open the PR and comment the failure on the issue.
- PR body from the template: Goal, Changes, Verification, `Closes #n`. Labels
  `agent` plus the issue type.
- Never edit `nfft/`, never run binaries from `nfft/`, never add dependencies.
- No external text copied. External sites inform structure and topics only.
- Writing style: `agents/CONTEXT.md` section Style, STE, no symbols.

## 7. Workflow `agent-respond.yml`

```
on: issue_comment [created], pull_request_review_comment [created],
    pull_request_review [submitted]
if: actor login == 'jenskeiner' && PR has label 'agent' && not a fork
concurrency: group respond-${pr}, cancel-in-progress: false
```

Checkout the PR head branch, run `claude-code-action@v1` with the responder
prompt and the comment body. Agent edits, runs the checks, commits with message
`Address review: <summary>`, pushes, replies on the thread. Does not count
against the cap. An approving review without text triggers nothing.

## 8. Workflow `upstream.yml`

Every 6 h and on dispatch. Shell: `git ls-remote NFFT/nfft develop`, compare to
the pinned SHA. If equal, exit. If different and a PR labelled `upstream` is
open, or 3 agent PRs are open, exit and retry next poll. Otherwise: branch `upstream/<short sha>`, bump the submodule, run
`apigen` and all checks, open PR `Bump NFFT to <sha>` with labels `agent`,
`upstream`, and the check results in the body. Then run the upstream-watcher
agent in the same job on `git -C nfft diff <old> <new>`; it pushes mechanical
fixes to the bump branch and files issues for content work. The bump PR is one
of the 3.

## 9. Security

- `CLAUDE_CODE_OAUTH_TOKEN` in GitHub environment `agents`, deployment branch
  rule `develop` only, no other environment carries it.
- Secret reaches jobs only on `schedule`, `workflow_dispatch`, `push` to
  `develop`, and the comment events gated on login `jenskeiner`. Never
  `pull_request_target`, never `allowed_bots`, never `allowed_non_write_users`.
  Fork PRs run `docs.yml` build only, with no secrets.
- `permissions` explicit per job, default `GITHUB_TOKEN`, no PAT.
- Actions pinned by commit SHA, Dependabot weekly.
- Env scrub left on. No `--verbose`, no `--debug`: logs are public.
- Allowed tools deny `Bash` outside the listed prefixes. The submodule and the
  external sites are untrusted input; prompts say so.
- Rotation: new token every 90 days, calendar reminder. Revoke on any run the
  maintainer did not expect. Weekly look at the Claude usage page.
- Branch protection includes admins, so a compromised run cannot push to
  `develop`.

## 10. Coverage seed for `agents/coverage.md`

Rows are topics, columns are nfft.org, fftw.org, FINUFFT, ours. Values:
`yes`, `partial`, `no`, `n/a`.

nfft.org: Documentation, Download, Installation, FAQ, People, Links, Parallel
NFFT; generalisations NNFFT, NFCT/NFST, NSFFT, NFSFT, NFSOFT, FPT; inversion
intro, iNFFT 1D, least squares CGNR, interpolation CGNE; applications fastsum,
fast Gauss, fastsumS2, MRI, polar FFT, Radon/CT, ridgelet, quadrature on
manifolds, MTEX; tutorial paper, papers list, Matlab/Octave binaries, Julia
package.

FINUFFT: install, install GPU, directories, math, tutorial (series eval,
continuous FT, GRF, inverse 1D type 2, periodic Poisson 2D, real
interpolation 1D), C interface, C examples, options, error codes, troubleshoot,
performance, dev notes, implementation GPU, Fortran, MATLAB, Python, Julia,
migration from NFFT, related software, users, references, changelog,
acknowledgements.

FFTW: introduction, tutorial (complex 1-D, complex multi-D, real 1-D, real
multi-D, halfcomplex, real even/odd, DHT), other topics (SIMD alignment and
malloc, array format row/column major, fixed and dynamic arrays, wisdom,
caveats), reference (data types, complex numbers, precision, memory
allocation, plans, basic interface, planner flags, real-data array format,
real-to-real), advanced and guru interfaces, wisdom, thread safety,
multithreading, distributed, calling from Fortran, upgrading, installation and
customisation, acknowledgements, license, concept index.

Ours today: index, getting-started (install, first transform, build from
source, examples), guide (concepts, plans and flags, windows, precision,
OpenMP, accuracy), transforms (11 pages), API (11 generated), applications
(11), interfaces (Julia, MATLAB/Octave), reference (publications, FAQ, people,
changelog, license), development (contributing, build matrix, testing,
benchmarks, releasing).

Evident gaps the product owner starts from: error handling and return codes,
troubleshooting, performance guide, memory layout and array format, thread
safety, migration from other libraries, glossary of terms, options reference
per flag, Fortran/Python status, related software, users, acknowledgements,
ridgelet, MTEX, inversion pages per method.

## 11. Skills

| Skill | Content |
|-------|---------|
| writing-docs | STE rules, page structure, admonitions, math notation conventions, cross-link rules, snippet before prose. |
| api-overlay | Overlay format, how to read `coverage.json`, how to derive a doc from `kernel/*.c` and tests, what to say for flags. |
| math-from-sources | Where definitions live (`kernel/`, `tests/refgen`, papers list), how to state a transform, notation table, checking a formula against code. |
| snippets | `--8<--` with `nfft/` base, line ranges, the drift check, how to pick ranges that survive edits. |
| site-comparison | How to inventory an external site into coverage rows, parity means topics not text. |
| backlog | Issue template fields, labels, priority rules, acceptance criteria, how to claim and release. |

## 12. Cost

Per day worst case: 6 writer, 3 editor, 1 product-owner, 0.5 analyst, 4
upstream polls, responder runs. Gates stop most PR-making runs for free once
3 PRs are open. Expected: 2 to 4 agent runs per day. `--max-turns 80` caps
each. Retro after 14 days adjusts crons and models.

## 13. Rollout

| M | Scope | Done when |
|---|-------|-----------|
| M0 | Repo, submodule, overlay seed, apigen merge, checks, `docs.yml`, `pr-checks.yml`, Pages live, branch protection, environment and secret. | `dev` site on Pages equals this branch's site. |
| M1 | `agents/`, skills, issue templates, `agents.yml` with dispatch only, `agent-respond.yml`. One manual writer run opens a PR; one comment gets a revision. | Both observed. |
| M2 | Crons on, `upstream.yml` on, product-owner seeded `coverage.md`. | 7 days unattended, cap respected. |
| M3 | Retro: merge rate, PR quality, cost. Tune. | Issue closed with numbers. |

## 14. Risks

- OAuth token is long-lived. Mitigation: environment scoping, rotation, trigger
  allowlist.
- Zensical alpha and mike fork. Pinned, bump by hand.
- Overlay drifts from a future upstream header doc. `coverage.json` reports
  symbols with both; the upstream-watcher files an issue to reconcile.
- Line-range snippets break on upstream edits. Drift check fails the bump PR,
  the watcher fixes ranges.
- Agents produce plausible but wrong mathematics. `math-from-sources` requires
  a code or paper citation per formula; the maintainer reviews.
- Subscription rate limits stall runs. Runs fail loudly, gates retry next cron.
