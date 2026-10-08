---
symbol: nfct_adjoint_direct
kind: function
source: header
---
executes a direct transposed NDCT (exact,slow), computes for $k \in I_0^{N,d}$
$h^C(k) = \sum_{j \in I_0^{(M\_total,1)}} f_j^C * cos(2 \pi k x_j)$

Parameters:

`ths_plan`
:   The plan for the transform
