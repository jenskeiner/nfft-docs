---
name: writing-docs
description: Use when writing or editing any page under doc/ of the NFFT3 documentation site. Covers STE style, page structure, math notation, cross-links and the forbidden words. Triggers - "write the page", "fill the gap", "improve clarity", "rewrite", "edit the section".
---

# Writing docs for the NFFT3 site

## Before writing

1. Read `doc/transforms/<module>.md` for the transform the page concerns. Use
   its notation and its terms. Do not invent synonyms.
2. Read one finished page of the same section, for example
   `doc/guide/windows.md`, and match its shape.
3. Find the facts in `nfft/`: the header `nfft/include/nfft3.h`, the kernel
   `nfft/kernel/<module>/`, the tests `nfft/tests/`, the examples
   `nfft/examples/`. A fact without a file and line does not go in.

## Page shape

- One `#` title, a noun phrase. Then one paragraph that says what the page
  answers and for whom.
- `##` sections in the order a reader needs them: what it is, when to use
  it, how to call it, parameters, pitfalls, further reading.
- Code before prose that explains it. Code comes from a locked snippet, see
  the `snippets` skill, or is at most five lines of illustrative C that the
  text says is not from the tree.
- Tables for parameters and flags: `| Name | Type | Meaning | Default |`.
- Links to API entries as `[nfft_trafo](../api/nfft.md#trafo)`. Anchors on
  API pages are the unmangled function name.
- Admonitions: `!!! warning` for data loss or wrong results, `!!! note` for
  version differences. Nothing else.

## Style, ASD-STE100

- One idea per sentence. Under 25 words. Active voice. Present tense.
- Commands as imperatives: "Call `nfft_precompute_one_psi` before the
  first transform."
- The same word for the same thing. "node" not "sample point", "plan" not
  "handle", "coefficient" not "Fourier coefficient" after the first use.
- No special symbols in prose, no emoji, no arrows, no `->` outside code.
- Forbidden words: load-bearing, seam, byte-identical, odometer.
- No marketing: no "powerful", "simply", "easily", "just".

## Math

- Inline `$...$`, display `$$...$$` on their own lines with a blank line
  before and after. MathJax, so `\mathbb`, `\mathbf`, amsmath work.
- Notation: $N$ bandwidth, $M$ nodes, $d$ dimension, $\mathbf{x}_j$ nodes in
  $\mathbb{T}^d$, $\hat f_{\mathbf{k}}$ coefficients, $I_N^d$ the index set,
  $n = \sigma N$ the oversampled length, $m$ the cut-off, $\varphi$ the
  window, $\hat\varphi$ its Fourier transform.
- Each displayed formula is followed by a sentence that says what it means
  and where it comes from: a path and line in `nfft/` or an entry on
  `doc/reference/publications.md`.

## Checks before you finish

```
uv run python -m support.apigen
uv run --with-requirements support/docs-requirements.txt zensical build --strict
uv run python -m support.checks.site
uv run python -m support.checks.snippets check
uv run python -m support.checks.overlay
```

Read your page in `site/<path>/index.html` once. Formula errors show only
there.
