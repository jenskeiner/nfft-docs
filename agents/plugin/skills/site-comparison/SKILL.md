---
name: site-comparison
description: Use when comparing the NFFT3 site with nfft.org, fftw.org, FINUFFT or another library's documentation, or when updating agents/coverage.md. Parity means topics are covered, never text copied. Triggers - "compare", "coverage matrix", "parity", "what do other sites cover".
---

# Comparing with other documentation sites

## Reference sites

| Site | Entry | What to look at |
|------|-------|-----------------|
| nfft.org | https://www-user.tu-chemnitz.de/~potts/nfft/ | Pages: Documentation, Download, Installation, FAQ, People, Links, Parallel NFFT; generalisations; inversion; applications. |
| fftw.org | https://www.fftw.org/fftw3_doc/ | Chapters 1 to 11. Tutorial, other important topics, reference, multi-threaded, distributed, Fortran, installation. |
| FINUFFT | https://finufft.readthedocs.io/en/latest/ | Sidebar: install, math, tutorials, C interface, options, error codes, troubleshooting, performance, interfaces, migration from NFFT, related, users, references. |

Fetch a page with `curl -sL <url>` and read its headings
(`grep -o '<h[1-3][^>]*>[^<]*'`). Do not read more than you need.

## Procedure

1. List the headings of the external section.
2. For each heading, decide the topic in library-neutral words. "Planner
   flags" and "Options" are one topic.
3. Find the topic on our site: the nav in `zensical.toml`, then
   `grep -ril "<term>" doc/`.
4. Record in `agents/coverage.md`: `yes` (a page or section covers it),
   `partial` (mentioned, not explained), `no`, `n/a` (does not apply to
   NFFT3, for example distributed memory).
5. For each `no` or `partial` that applies to NFFT3, file one issue of type
   `gap` or `new-section` with: the topic, why it applies to NFFT3, where it
   belongs in the nav, and acceptance criteria. Name the external site as a
   pointer for structure only.

## Rules

- Never copy sentences. Never paraphrase a paragraph. Take the topic list,
  write from `nfft/` sources.
- Topics that are FFTW-specific (wisdom, guru interface, distributed) may be
  `n/a`, but say why in the issue if someone could expect them.
- FINUFFT's "migration from NFFT" page is a source of what users find hard
  in NFFT3. Read it for the pain points, turn them into `clarity` issues.
