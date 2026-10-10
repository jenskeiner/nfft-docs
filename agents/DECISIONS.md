# Decisions

Rulings by the maintainer that every agent must respect. One row per decision,
append only. A changed mind adds a new row and sets the old one to
`superseded by Dn`. Never delete a row. Agents read this file in every run:
before claiming an issue, check it against the active rows; on conflict,
comment the id on the issue, label it `blocked`, and do not work it.

Who writes rows: the responder when a review comment rejects or forbids
something, on the PR branch; the product owner from `decision` issues filed by
the maintainer; the maintainer directly.

| Id | Date | Scope | Decision | Source | Status |
|----|------|-------|----------|--------|--------|
| D1 | 2026-10-10 | All pages | Do not point readers to source locations (file and line in `nfft/`, `configure.ac` and similar) unless readers need to open that source themselves. State the fact only. | https://github.com/jenskeiner/nfft-docs/pull/70#issuecomment-6098681357 | active |

## Standing rules

Settled decisions folded in by the product owner when the table passes 80
rows. Ids stay.
