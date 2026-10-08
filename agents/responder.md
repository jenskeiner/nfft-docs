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
3. Run the verification commands. Commit with the message
   `Address review: <what changed>`. Push to the same branch. Never open a
   new PR, never force push.
4. Reply, always, even when you changed nothing: what changed in two
   sentences, or the answer. For a review comment reply in its thread with
   `gh api repos/jenskeiner/nfft-docs/pulls/<number>/comments/<id>/replies -f body=...`
   Write the repository path literally; a `$VARIABLE` in the command is denied.
   where `<id>` is the number at the end of the comment URL. For a review or
   a conversation comment use `gh pr comment <number> --body ...`.

## Stop conditions

One comment, one reply. 40 tool calls.
