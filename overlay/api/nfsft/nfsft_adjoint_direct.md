---
symbol: nfsft_adjoint_direct
kind: function
source: header
---
Executes a direct adjoint NDSFT, i.e. computes for $k=0,\ldots,N;
n=-k,\ldots,k$
$$
  \hat{f}(k,n) = \sum_{m = 0}^{M-1} f(m)
  \overline{Y_k^n\left(2\pi x_2(m), 2\pi x_1(m)\right)}.
$$

Parameters:

`plan`
:   the plan
