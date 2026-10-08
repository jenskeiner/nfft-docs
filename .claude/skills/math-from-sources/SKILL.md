---
name: math-from-sources
description: Use when adding or checking a formula, a definition, a transform statement or an error bound in the NFFT3 docs. Says where definitions live in the source tree, how to state a transform, and how to check a formula against the code. Triggers - "math", "formula", "definition", "derive", "notation", "error bound".
---

# Mathematics from sources

Every formula on the site has a source. Either the code computes it, or a
paper on `doc/reference/publications.md` states it. Write nothing from memory.

## Where definitions live

| What | Where |
|------|-------|
| Transform definitions, index sets | `doc/transforms/<module>.md`, already reviewed. Reuse. |
| What the code computes | `nfft/kernel/<module>/<module>.c`, the `*_trafo_direct` functions are the plain sums. |
| Window functions and their Fourier transforms | `nfft/kernel/nfft/nfft.c` `PHI`, `PHI_HUT` macros per window; `nfft/include/nfft3.h` flags `KAISER_BESSEL`, `GAUSSIAN`, `B_SPLINE`, `SINC_POWER`. |
| Default parameters | `nfft_init` and `nfft_init_guru` in `nfft/kernel/nfft/nfft.c`: $m$, $\sigma$, flags. |
| Reference values the tests check against | `nfft/tests/`, `nfft/tests/refgen/`. |
| Error estimates | Papers: Keiner, Kunis, Potts 2009 "Using NFFT 3"; Potts, Steidl, Tasche 2001; Plonka, Potts, Steidl, Tasche 2018 textbook. |
| Spherical harmonics, Wigner functions | `doc/transforms/nfsft-background.md`, `nfft/kernel/nfsft/`, `nfft/kernel/nfsoft/`. |
| Polynomial transform | `nfft/kernel/fpt/`, Potts, Steidl, Tasche 1998. |

## How to state a transform

1. The index set first, for example $I_N^d = \{-N/2, \dots, N/2-1\}^d$.
2. The sum, with the sign convention of the code. NFFT3 uses
   $\mathrm{e}^{-2\pi\mathrm{i}\mathbf{k}\mathbf{x}_j}$ in the forward
   transform. Check `nfft_trafo_direct` before you write a sign.
3. The adjoint, not the inverse. Say so.
4. The cost, with the parameters: $\mathcal{O}(N^d \log N + m^d M)$.

## Checking a formula against the code

- Find the direct function. Map every symbol in your formula to a variable.
- Run nothing from `nfft/`. Read the loop and the exponent.
- For a window, compare your $\varphi$ with the `PHI` macro and your
  $\hat\varphi$ with `PHI_HUT`. Note the normalisation of $n$.
- If the code and a paper differ, the code wins on the site, and you say
  that the paper uses another convention.

## Writing it

See the `writing-docs` skill for notation and layout. After each display
formula: one sentence, what it means, and the source in the form
`nfft/kernel/nfft/nfft.c`, function `nfft_trafo_direct`, or the paper.
