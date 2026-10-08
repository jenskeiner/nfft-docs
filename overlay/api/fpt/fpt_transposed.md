---
symbol: fpt_transposed
kind: function
source: header
---
Computes a single transposed DPT transform with the fast algorithm.

The arguments are those of fpt_transposed_direct. The routine does nothing if
the set was initialised with FPT_NO_FAST_ALGORITHM.

Parameters:

`set`
:   The set of DPT transform data

`m`
:   The transform index $m$, $0 \le m < M$

`x`
:   The result, the coefficients for $k=k_{\text{start}},\ldots,k_{\text{end}}$, with `x[0]` for $k_{\text{start}}$

`y`
:   The input, $k_{\text{end}}+1$ entries

`k_end`
:   The index $k_{\text{end}} \le N$ of the last coefficient

`flags`
:   FPT_FUNCTION_VALUES or 0
