---
symbol: fpt_trafo_direct
kind: function
source: header
---
Computes a single DPT transform directly, without the fast algorithm.

The routine evaluates the sum $f = \sum_{k=k_{\text{start}}}^{k_{\text{end}}} x_k P_k$ and returns its Chebyshev
coefficients, or with FPT_FUNCTION_VALUES its values at the Chebyshev nodes. It needs $O(k_{\text{end}}^2)$ operations.
The routine does nothing if the set was initialised with FPT_NO_DIRECT_ALGORITHM.

Parameters:

`set`
:   The set of DPT transform data

`m`
:   The transform index $m$, $0 \le m < M$

`x`
:   The polynomial coefficients $x_k$ for $k=k_{\text{start}},\ldots,k_{\text{end}}$, with `x[0]` $=x_{k_{\text{start}}}$

`y`
:   The result, $k_{\text{end}}+1$ entries: the Chebyshev coefficients $y_0,\ldots,y_{k_{\text{end}}}$, or with FPT_FUNCTION_VALUES the values at the Chebyshev nodes

`k_end`
:   The index $k_{\text{end}} \le N$ of the last coefficient

`flags`
:   FPT_FUNCTION_VALUES or 0
