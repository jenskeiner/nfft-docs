---
name: snippets
description: Use when including C, Julia or MATLAB code from the NFFT source tree in a docs page, or when the snippet lock check fails. Covers the --8<-- syntax, the nfft/ base path, choosing ranges, and the lock commands check, update, relocate. Triggers - "snippet", "include the example", "code from examples/", "snippets.lock", "drift".
---

# Snippets from the source tree

Code on the site is cut from files in `nfft/` at build time. Nothing is
pasted. The lock file `support/checks/snippets.lock` records a hash of every
cut block, so an upstream edit cannot silently change what a page shows.

## Syntax

````
```c
--8<-- "examples/nfft/simple_test.c:24:73"
```
````

The path is relative to `nfft/` (`pymdownx.snippets.base_path = ["nfft", "."]`).
Lines are 1-based and inclusive. Use the language of the file: `c`,
`julia`, `matlab`.

## Choosing a range

- Cut a whole function or a whole logical block, from the comment above it
  to the closing brace. Partial statements confuse readers.
- Prefer `nfft/examples/` and `nfft/applications/` files. They are compiled
  by the upstream build, so they cannot rot.
- Keep ranges under 60 lines. Split with prose between two snippets.
- Never cut from `nfft/kernel/` to show usage. Kernel code is for citing
  facts, not for examples.

## Commands

```
uv run python -m support.checks.snippets check      # CI runs this
uv run python -m support.checks.snippets update     # after you add or change a snippet
uv run python -m support.checks.snippets relocate   # after an upstream bump moved lines
```

After adding a snippet: run `update`, then `check`, commit the lock with the
page. `relocate` finds each locked block in the current file and rewrites the
range; a `NOMATCH` line means the code changed and someone must look at the
page.
