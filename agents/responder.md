# Role: responder

The maintainer commented on a pull request an agent opened. You act on the
comment, on the same branch. Skills: `writing-docs`, `api-overlay`, `snippets`.
The prompt carries the PR number, the comment and, for a review comment, the
file and line.

## Procedure

1. Run the checkout command given in the inputs: `gh pr checkout <number>`
   and `git submodule update --init`. Then
   `gh pr view <number> --json title,body,headRefName,files` and read the
   comment.
2. Do what the comment asks. If the comment asks a question, answer it in a
   reply and change nothing unless the answer implies a change. If the
   comment asks for something that conflicts with `CONTEXT.md`, say so in the
   reply and do the part that does not conflict.
2b. If the comment rejects or forbids something in general terms ("do not",
   "never", "we do not want", "leave as is", "not in this project"), record
   it: append a row to `agents/DECISIONS.md` on this branch with the next id,
   today's date, the scope (pages or topics), the ruling in one sentence,
   the comment URL and `active`. Name the id in your reply. A comment that
   only asks for a different wording here is not a decision.
3. Run the verification commands. Commit with the message
   `Address review: <what changed>`. Push to the same branch. Never open a
   new PR, never force push.
4. Reply, always, even when you changed nothing: what changed in two
   sentences, or the answer. For a review comment reply in its thread with
   `gh api repos/jenskeiner/nfft-docs/pulls/<number>/comments/<id>/replies -f body=...`
   Write the repository path literally; a `$VARIABLE` in the command is denied.
   where `<id>` is the number at the end of the comment URL. For a review or
   a conversation comment use `gh pr comment <number> --body ...`.

## Closed without merge

When the inputs say the pull request was closed without merge, you are on
develop. Read the maintainer's last comment given in the inputs. If it
states a reason that applies beyond this PR, create branch
`agent/decision-<pr>` from develop, append the row to `agents/DECISIONS.md`,
and open a PR titled `Record decision Dn from PR #<pr>` with labels `agent`
and `decision`. Then label the issue the PR closed as `wontfix` with the id.
If the reason is specific to that PR, release the issue (`in-progress` off)
and comment that it is free to be reworked. No other change.

## Conflict with develop

`git fetch origin develop && git merge origin/develop`. Resolve every
conflict so that both the PR's change and develop's change survive; for
`zensical.toml` nav lists keep both entries in nav order; for
`support/checks/snippets.lock` and `doc/api/coverage.json` regenerate
(`python -m support.checks.snippets update`, `python -m support.apigen`)
instead of editing by hand. Run the verification commands. Commit with the
merge message git proposes, push, and comment on the PR which files
conflicted and how you resolved them. If a conflict needs a judgement call
on content, resolve it the way the PR's issue asks and say so.

## Update with develop

`git fetch origin develop && git merge origin/develop`, run the verification
commands, push. No comment unless something failed.

## Stop conditions

One comment, one reply. 40 tool calls. A conflict or update run makes no
reply beyond the comment its section names.
