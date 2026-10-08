# NFFT docs repository with agent team: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up `jenskeiner/nfft-docs`: the Zensical site from `feature/docs-site` built against `NFFT/nfft@develop` as a submodule, published on Pages, with an unattended Claude Code agent team that opens reviewable PRs.

**Architecture:** Site sources plus `support/apigen` move as they are. `apigen` reads the header from the submodule and merges `overlay/api/` doc text over it. Snippets point into `nfft/` with a lock file that catches drift. Three workflows run the agents: `agents.yml` (cron per role), `agent-respond.yml` (maintainer comments), `upstream.yml` (poll, bump, watch).

**Tech Stack:** Zensical 0.0.57, mike fork, uv, Python 3.12 stdlib, GitHub Actions, `anthropics/claude-code-action@v1`, `gh`.

**Spec:** `docs/plans/2026-10-08-nfft-docs-agents-design.md`

## Global Constraints

- Public repo `jenskeiner/nfft-docs`, default branch `develop`.
- Submodule `nfft/` pinned to a SHA of `NFFT/nfft` `develop`. Never edited.
- Overlay wins over header text. Overlay seeded with `source: header`.
- Secret `CLAUDE_CODE_OAUTH_TOKEN` only in environment `agents`, branch rule `develop`.
- Agent triggers: `schedule`, `workflow_dispatch`, `push` to `develop`, comment events gated on login `jenskeiner`. Never `pull_request_target`.
- Hard cap 3 open PRs labelled `agent`, checked in shell before the action runs.
- Actions pinned by commit SHA.
- Zensical build must pass `--strict` plus `support/checks/site.py` before any deploy and before any agent PR.
- Prose: STE, no special symbols. Commit messages: imperative, no attribution lines.

## Review Focus

1. An overlay file whose `symbol` matches nothing in the header: `checks/overlay.py` must fail, not silently ignore. Test in Task 4.
2. Upstream edits a snippet file so the range now covers other code: `checks/snippets.py` must fail on the hash, and `--relocate` must find the old block or report it. Test in Task 5.
3. 3 agent PRs open and a cron fires: the gate exits 0 without running the action and without a token spent. Test by dispatch in Task 14.
4. A stranger comments on an agent PR: `agent-respond.yml` must skip. Verify the `if` expression in Task 13 with `act`-free review: the job condition names the login literally.
5. A revision run must push to the PR branch, not open a second PR. Prompt in Task 11 says so; Task 15 observes it.

---

## M0. Repository and publishing

### Task 1: Create the repository and copy the site

**Files:**
- Create in new repo: `doc/`, `zensical.toml`, `support/apigen/`, `support/docs-requirements.txt`, `support/overrides/`, `.github/scripts/docs-deploy.sh`, `.github/scripts/docs-version.sh`, `.gitignore`, `COPYING`, `README.md`, `docs/plans/` (spec and this plan).

- [ ] **Step 1:** `gh repo create jenskeiner/nfft-docs --public --description "Documentation site for the NFFT3 library" --clone` into `/workspaces/nfft-docs`. Set default branch: `git checkout -b develop`.
- [ ] **Step 2:** Copy from `/workspaces/nfft` (branch `feature/docs-site`): `doc/`, `zensical.toml`, `support/apigen/` without `__pycache__`, `support/docs-requirements.txt`, `support/overrides/`, `.github/scripts/docs-deploy.sh`, `.github/scripts/docs-version.sh`, `COPYING`, `docs/plans/2026-10-08-*.md`.
- [ ] **Step 3:** `.gitignore`: `site/`, `doc/api/`, `.venv/`, `__pycache__/`, `.cache/`.
- [ ] **Step 4:** `README.md`: what the repo is, how to build (`uv run python -m support.apigen && uv run --with-requirements support/docs-requirements.txt zensical build --strict`), that `nfft/` is a submodule, link to the spec.
- [ ] **Step 5:** Commit `Import the Zensical site from NFFT/nfft feature/docs-site.`

### Task 2: Add the NFFT submodule

- [ ] **Step 1:** `git submodule add -b develop https://github.com/NFFT/nfft.git nfft`. Record the SHA in the commit message.
- [ ] **Step 2:** `.gitmodules` gets `shallow = true`.
- [ ] **Step 3:** Commit `Add NFFT/nfft develop as submodule at <sha>.`

### Task 3: Point apigen at the submodule and merge the overlay

**Files:**
- Modify: `support/apigen/generate.py` (`HEADER`, `main`, new `apply_overlay`)
- Create: `support/apigen/overlay.py`
- Test: `support/apigen/test_overlay.py`

**Interfaces:**
- Produces: `overlay.load(root="overlay/api") -> dict[tuple[str,str], Overlay]` keyed by `(module_key, symbol)`; `overlay.apply(modules, entries) -> list[str]` returns unmatched keys; `overlay.key_of(section, item, prefixes) -> str` gives the DOUBLE mangled name for functions, typedefs, variables, the plain name for structs, flags, macros.

Overlay file format:

```
---
symbol: nfft_trafo
kind: function
source: header
---
Markdown body.
```

Struct files: body before the first `### member` heading is the struct doc; each `### name` section is that member's doc.

- [ ] **Step 1:** Write `test_overlay.py`:

```python
import os, tempfile
from support.apigen import overlay
from support.apigen.generate import parse, mangle_prefixes, HEADER

def test_roundtrip_function():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(f"{d}/nfft")
        open(f"{d}/nfft/nfft_trafo.md", "w").write(
            "---\nsymbol: nfft_trafo\nkind: function\nsource: agent\n---\nNew text.\n")
        mods = parse()
        prefixes = mangle_prefixes(open(HEADER).read())
        unmatched = overlay.apply(mods, overlay.load(d), prefixes)
        fn = next(f for f in mods[0].main.functions if f.name == "trafo")
        assert fn.doc == "New text."
        assert unmatched == []

def test_unmatched_symbol_reported():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(f"{d}/nfft")
        open(f"{d}/nfft/nfft_nope.md", "w").write(
            "---\nsymbol: nfft_nope\nkind: function\nsource: agent\n---\nx\n")
        mods = parse()
        prefixes = mangle_prefixes(open(HEADER).read())
        assert overlay.apply(mods, overlay.load(d), prefixes) == [("nfft", "nfft_nope")]
```

- [ ] **Step 2:** Run `uv run python -m support.apigen.test_overlay`, expect ImportError.
- [ ] **Step 3:** `HEADER = os.path.join("nfft", "include", "nfft3.h")`. Write `overlay.py` with `Overlay(symbol, kind, source, body, members)`, `load`, `key_of`, `apply`. `apply` sets `item.doc = body` and, for structs, `member.doc` per `### name` section. `main()` calls `apply` after `parse()` and records in `coverage.json` per symbol `"doc": "header" | "overlay" | "none"` and the list `unmatched_overlay`. `main` exits 1 if `unmatched_overlay` is non-empty.
- [ ] **Step 4:** Run the test, expect PASS. Run `uv run python -m support.apigen`, expect 149 functions.
- [ ] **Step 5:** Fix `test_apigen.py`: counts for develop (149 functions, exact per-module numbers from the run), drop the `.c.in` assertion. Run `uv run python -m support.apigen.test_apigen`, expect PASS.
- [ ] **Step 6:** Commit `Read the header from the submodule and merge the overlay.`

### Task 4: Seed the overlay from the branch header

**Files:**
- Create: `support/apigen/seed_overlay.py`, `overlay/api/<module>/*.md`, `support/checks/overlay.py`

- [ ] **Step 1:** `seed_overlay.py <header-path>`: parse that header with `generate.parse(path)`, for every function, typedef, variable, struct, flag, macro with a non-empty doc write `overlay/api/<module>/<key>.md` with `source: header`. Structs: write members with doc as `### name` sections. Skip symbols whose doc is identical to the submodule header's doc for the same key.
- [ ] **Step 2:** Run it with `/workspaces/nfft/include/nfft3.h`. Expect about 145 function files plus flags and macros.
- [ ] **Step 3:** `support/checks/overlay.py`: run `apigen` parse plus `overlay.apply`, exit 1 and list unmatched keys, exit 1 if any file lacks the three front-matter fields.
- [ ] **Step 4:** Run `uv run python -m support.apigen` and diff `doc/api/` against `/workspaces/nfft/doc/api/` (generate there first). Differences allowed: the 4 new develop functions, the `Declared in` line. Nothing else.
- [ ] **Step 5:** Commit `Seed the API overlay from the feature/docs-site header.`

### Task 5: Snippets into the submodule with a drift lock

**Files:**
- Modify: `zensical.toml` (`pymdownx.snippets.base_path = ["nfft", "."]`, `repo_url`, `repo_name`, `edit_uri = "edit/develop/doc/"`, `site_url = "https://jenskeiner.github.io/nfft-docs/"`), every `doc/**/*.md` with a `.c.in` snippet, `doc/getting-started/first-transform.md` prose about `.c.in`.
- Create: `support/checks/snippets.py`, `support/checks/snippets.lock`
- Test: `support/checks/test_snippets.py`

**Interfaces:**
- `snippets.py check` exits 1 on any changed block. `snippets.py update` rewrites the lock. `snippets.py relocate` searches each locked block in the current file and rewrites the range in the Markdown; prints `NOMATCH` lines for blocks it cannot find and exits 1.

Lock format, one line per snippet: `<doc file>\t<path>:<a>:<b>\t<sha256 of the block>`.

- [ ] **Step 1:** Rewrite the 15 `.c.in` ranges to the `.c` ranges found on 2026-10-08:
  `fastgauss.c.in:128:150 -> fastgauss.c:125:147`, `:203:226 -> :200:223`; `linogram_fft_test.c.in:47:76 -> :44:73`; `mpolar_fft_test.c.in:58:99 -> :55:96`; `polar_fft_test.c.in:176:209 -> :173:206`, `:73:92 -> :70:89`; `inverse_radon.c.in:178:224 -> :175:221`; `radon.c.in:167:193 -> :164:190`; `nfct/simple_test.c.in:28:77 -> :25:74`; `nfft/simple_test.c.in:27:76 -> :24:73`, `:87:119 -> :84:116`; `nfst/simple_test.c.in:28:77 -> :25:74`; `glacier.c.in:36:40 -> :33:37`, `:43:106 -> :40:103`; `solver/simple_test.c.in:86:150 -> :83:147`.
- [ ] **Step 2:** Write `test_snippets.py`: create a temp doc with a snippet into a temp file, `update`, assert the lock has one line; edit the file by inserting a line above the block, `check` returns 1, `relocate` rewrites the range by +1 and `check` returns 0.
- [ ] **Step 3:** Run, expect failure. Write `snippets.py` with `SNIP = re.compile(r'--8<--\s*"([^":]+):(\d+):(\d+)"')`, functions `scan(doc_dir) -> list[(docfile, path, a, b)]`, `block(path, a, b)`, `cmd_check`, `cmd_update`, `cmd_relocate`. Paths resolve against `nfft/` first, then `.`.
- [ ] **Step 4:** Run test, expect PASS. Run `uv run python support/checks/snippets.py update`, commit the lock. Run `check`, expect exit 0.
- [ ] **Step 5:** Edit `first-transform.md` to say `examples/nfft/simple_test.c`. Commit `Point snippets into the submodule and lock their ranges.`

### Task 6: Site check, local build, parity

**Files:**
- Create: `support/checks/site.py` (ported `docs-check-site.py`, `SITE = "site"`).

- [ ] **Step 1:** `uv run python -m support.apigen && uv run --with-requirements support/docs-requirements.txt zensical build --strict && uv run python support/checks/site.py`. Expect `No issues found` and the check silent.
- [ ] **Step 2:** Count pages: `find site -name index.html | wc -l` equals the same count in `/workspaces/nfft/site` after a build there, plus 0.
- [ ] **Step 3:** Commit `Port the site check.`

### Task 7: Workflows for build, deploy and PR checks

**Files:**
- Create: `.github/workflows/docs.yml`, `.github/workflows/pr-checks.yml`, `.github/dependabot.yml`, `.github/CODEOWNERS`, `.vale.ini`, `.vale/NFFT/Forbidden.yml`.

- [ ] **Step 1:** `docs.yml`: port the four jobs. Every checkout gets `submodules: true`. Drop the `release` job for now (no releases in the docs repo), keep `deploy-dev` and `deploy-manual`. `docs-deploy.sh` keeps calling `support/checks/site.py`.
- [ ] **Step 2:** `pr-checks.yml` on `pull_request`: steps `apigen.test_apigen`, `apigen.test_overlay`, `checks/snippets.py check`, `checks/overlay.py`, `checks/test_snippets.py`, lychee on `doc/` excluding `doc/api` with `fail: false`, Vale with `errata-ai/vale-action` on `doc/` with `fail_on_error: true`.
- [ ] **Step 3:** `.vale.ini`: `StylesPath = .vale`, `MinAlertLevel = error`, `[*.md] BasedOnStyles = NFFT`. `Forbidden.yml`: existence rule, level error, tokens `load-bearing`, `seam`, `byte-identical`, `odometer`, and a second rule for the emoji range.
- [ ] **Step 4:** `dependabot.yml`: `github-actions`, weekly. `CODEOWNERS`: `* @jenskeiner`.
- [ ] **Step 5:** Pin every action by SHA (`actions/checkout`, `astral-sh/setup-uv`, `actions/upload-artifact`, `lycheeverse/lychee-action`, `errata-ai/vale-action`). Resolve SHAs with `gh api repos/<owner>/<repo>/git/ref/tags/<tag>`.
- [ ] **Step 6:** Commit `Add build, deploy and PR check workflows.`

### Task 8: Push, Pages, first deploy

- [ ] **Step 1:** `git push -u origin develop`. `gh repo edit --default-branch develop`.
- [ ] **Step 2:** Wait for `docs.yml` run: `gh run watch`. Expect `build` and `deploy dev` green and a `gh-pages` branch.
- [ ] **Step 3:** `gh api -X POST repos/jenskeiner/nfft-docs/pages -f build_type=legacy -f source[branch]=gh-pages -f source[path]=/`.
- [ ] **Step 4:** `curl -sI https://jenskeiner.github.io/nfft-docs/dev/ | head -1` returns 200 within a few minutes. Open a transform page and an API page, confirm math and snippets render.

### Task 9: Repository settings

- [ ] **Step 1:** Labels via `gh label create`: types `gap`, `new-section`, `api-gap`, `math`, `style`, `clarity`, `compare`, `upstream`; states `needs-triage`, `ready-for-agent`, `in-progress`, `blocked`, `wontfix`; origin `from-maintainer`, `agent`; `priority: high`.
- [ ] **Step 2:** Environment: `gh api -X PUT repos/jenskeiner/nfft-docs/environments/agents -F deployment_branch_policy[protected_branches]=false -F deployment_branch_policy[custom_branch_policies]=true`, then `POST .../environments/agents/deployment-branch-policies -f name=develop -f type=branch`.
- [ ] **Step 3:** Branch protection on `develop`: `gh api -X PUT repos/.../branches/develop/protection` with required status checks `build`, `checks`, `required_pull_request_reviews.required_approving_review_count=1`, `require_code_owner_reviews=true`, `enforce_admins=true`, `allow_force_pushes=false`, `restrictions=null`.
- [ ] **Step 4:** `gh repo edit --enable-auto-merge=false --delete-branch-on-merge`. Allow Actions to create PRs: `gh api -X PUT repos/.../actions/permissions/workflow -f default_workflow_permissions=read -F can_approve_pull_request_reviews=false`.
- [ ] **Step 5:** Verify with `gh api repos/.../branches/develop/protection | jq .required_status_checks`.

## M1. Agents

### Task 10: Shared context and role prompts

**Files:**
- Create: `agents/CONTEXT.md`, `agents/product-owner.md`, `agents/writer.md`, `agents/editor.md`, `agents/analyst.md`, `agents/upstream-watcher.md`, `agents/responder.md`, `agents/coverage.md` (empty table with the spec's rows).

`CONTEXT.md` sections: Purpose and targets (spec section 1), Repository map, Rules (spec section 6 contract verbatim), Style (STE, no symbols, forbidden words, admonitions sparingly, math in `$...$`, cite code or paper for formulas), Labels, Verification commands, PR body template, What you must never do.

Each role file: Role, Inputs (`gh issue list` filters, `doc/api/coverage.json`, `agents/coverage.md`), Procedure numbered, Output, Skills to use, Stop conditions.

- [ ] **Step 1:** Write `CONTEXT.md`.
- [ ] **Step 2:** Write the six role files. Writer procedure: list `ready-for-agent` issues of its types, pick by priority rule, claim, read the issue and the pages it names, write, run the five verification commands, open PR with body template and `Closes #n`, label `agent` plus type, comment the PR link on the issue. If verification fails twice, release the claim, comment the failure, stop.
- [ ] **Step 3:** Commit `Add the agent context and role prompts.`

### Task 11: Skills

**Files:**
- Create: `.claude/skills/{writing-docs,api-overlay,math-from-sources,snippets,site-comparison,backlog}/SKILL.md`

- [ ] **Step 1:** Each `SKILL.md` has front matter `name`, `description` with trigger phrases, then: when to use, procedure, format examples, checks. Content per spec section 11. `snippets` includes the lock commands. `api-overlay` includes the file format and the `coverage.json` field names from Task 3.
- [ ] **Step 2:** `claude --print "List the skills you see" ` from the repo root lists all six.
- [ ] **Step 3:** Commit `Add the task skills.`

### Task 12: Issue and PR templates

**Files:**
- Create: `.github/ISSUE_TEMPLATE/{gap,new-section,style,math,api-gap,compare}.yml`, `.github/ISSUE_TEMPLATE/config.yml` (`blank_issues_enabled: false`), `.github/PULL_REQUEST_TEMPLATE.md`.

- [ ] **Step 1:** Each issue form: title prefix, labels `needs-triage` and the type, fields Pages affected, What is missing or wrong, Acceptance criteria, Sources.
- [ ] **Step 2:** PR template: `## Goal`, `## Changes`, `## Verification`, `Closes #`.
- [ ] **Step 3:** Commit `Add issue and PR templates.`

### Task 13: Agent workflows

**Files:**
- Create: `.github/actions/agent-setup/action.yml`, `.github/workflows/agents.yml`, `.github/workflows/agent-respond.yml`, `.github/workflows/upstream.yml`, `.github/scripts/agent-gate.sh`, `.github/scripts/upstream-poll.sh`.

- [ ] **Step 1:** `agent-setup/action.yml`: inputs `role`, `model`, `extra_prompt`; steps checkout (submodules, `fetch-depth: 0`), setup-uv, `uv run python -m support.apigen`, then `anthropics/claude-code-action@<sha>` with `claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}` passed as input, `prompt` built by `cat agents/CONTEXT.md agents/<role>.md` plus `extra_prompt`, `claude_args` with model, `--max-turns 80`, allowed tools from spec section 6, `branch_prefix: agent/`, `base_branch: develop`.
- [ ] **Step 2:** `agent-gate.sh <role>`: for `writer`, `editor`: `open=$(gh pr list --label agent --state open --json number --jq length)`; `[ "$open" -ge 3 ] && { echo "cap reached"; echo "run=false" >> "$GITHUB_OUTPUT"; exit 0; }`; also check `gh issue list --label ready-for-agent --label <type>` non-empty for the role's types. Else `run=true`.
- [ ] **Step 3:** `agents.yml`: `on.schedule` with the five crons, each mapped in a step: `case "${{ github.event.schedule }}"`, `workflow_dispatch` input `role` choice. Crons commented out until Task 16. `permissions` per spec, `environment: agents`, `concurrency: agents-${{ role }}`. Job: gate, then `agent-setup` if `run == true`.
- [ ] **Step 4:** `agent-respond.yml`: events per spec section 7. Job `if: github.event.sender.login == 'jenskeiner' && contains(github.event.issue.labels.*.name, 'agent') || ... pull_request.labels ...`, resolve PR number from the event, `gh pr checkout`, `agent-setup` with role `responder` and `extra_prompt` containing the comment body and the file path if a review comment. `concurrency: respond-<pr>`.
- [ ] **Step 5:** `upstream-poll.sh`: `new=$(git ls-remote https://github.com/NFFT/nfft.git refs/heads/develop | cut -f1)`, `old=$(git -C nfft rev-parse HEAD)`; exit if equal, if an `upstream` PR is open, or if the cap is reached. Else branch `upstream/${new:0:8}`, `git -C nfft fetch && git -C nfft checkout $new`, run apigen, `snippets.py check || snippets.py relocate`, `overlay.py`, build strict, commit, push, `gh pr create` with labels `agent`, `upstream`, body with check output. Print `old`, `new`, `pr` to `GITHUB_OUTPUT`.
- [ ] **Step 6:** `upstream.yml`: cron `17 */6 * * *` plus dispatch, run the poll script, then `agent-setup` with role `upstream-watcher` and `extra_prompt` with `old`, `new`, the PR number, when a PR was made.
- [ ] **Step 7:** `actionlint` on all workflow files (`uvx` not available: use `docker run rhysd/actionlint` or `gh extension install cschleiden/gh-actionlint`). Expect clean.
- [ ] **Step 8:** Commit `Add the agent, responder and upstream workflows.` Push.

### Task 14: STOP. Maintainer steps

- [ ] Install the Claude GitHub App on `jenskeiner/nfft-docs`: https://github.com/apps/claude.
- [ ] On the maintainer machine: `claude setup-token`, then `gh secret set CLAUDE_CODE_OAUTH_TOKEN --env agents --repo jenskeiner/nfft-docs`.
- [ ] Confirm: `gh secret list --env agents --repo jenskeiner/nfft-docs` shows the name.

### Task 15: First supervised runs

- [ ] **Step 1:** File one issue with the `gap` template, label it `ready-for-agent`, `from-maintainer`. Example: "Add a glossary page for the terms used across the guide".
- [ ] **Step 2:** `gh workflow run agents.yml -f role=writer`. Watch the run. Expect a PR labelled `agent`, `gap`, with the template body, checks green.
- [ ] **Step 3:** Maintainer leaves one review comment. Expect `agent-respond.yml` to push a commit to the same branch and reply. No new PR.
- [ ] **Step 4:** Dispatch `writer` twice more with cap-testing issues, then a fourth time: the fourth run logs `cap reached` and the action step is skipped.
- [ ] **Step 5:** `gh workflow run agents.yml -f role=product-owner`. Expect `agents/coverage.md` filled by a PR or issues filed with acceptance criteria.

## M2. Unattended

### Task 16: Enable the crons

- [ ] **Step 1:** Uncomment the crons: product-owner `0 5 * * *`, writer `0 */4 * * *`, editor `30 */8 * * *`, analyst `0 7 */2 * *`. Push to `develop` by PR.
- [ ] **Step 2:** After 7 days: `gh run list --workflow agents.yml --limit 50`, count runs, failures, PRs. File the retro issue with the numbers.
