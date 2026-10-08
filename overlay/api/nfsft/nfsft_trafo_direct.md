---
symbol: nfsft_trafo_direct
kind: function
source: header
---
Executes a direct NDSFT, i.e. computes for $m = 0,\ldots,M-1$
$$
  f(m) = \sum_{k=0}^N \sum_{n=-k}^k \hat{f}(k,n) Y_k^n\left(2\pi x_2(m),
  2\pi x_1(m)\right).
$$

Parameters:

`plan`
:   the plan
