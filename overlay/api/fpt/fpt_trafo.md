---
symbol: fpt_trafo
kind: function
source: header
---
Computes a single DPT transform with the fast algorithm.

The arguments and the result are those of fpt_trafo_direct. For
$k_{\text{end}} < 4$ it calls fpt_trafo_direct.
The routine does nothing if the set was initialised with FPT_NO_FAST_ALGORITHM.

Parameters:

`set`
:   The set of DPT transform data

`m`
:   The transform index $m$, $0 \le m < M$

`x`
:   The polynomial coefficients $x_k$ for $k=k_{\text{start}},\ldots,k_{\text{end}}$, with `x[0]` $=x_{k_{\text{start}}}$

`y`
:   The result, $k_{\text{end}}+1$ entries

`k_end`
:   The index $k_{\text{end}} \le N$ of the last coefficient

`flags`
:   FPT_FUNCTION_VALUES or 0
