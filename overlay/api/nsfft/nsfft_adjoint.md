---
symbol: nsfft_adjoint
kind: function
source: header
---
Executes an adjoint NSFFT, computes fast and approximate for
$k\in H_N^d$:
$$
  \hat f_k = \sum_{j=0,\dots,M-1} f_j {\rm e}^{+2\pi{\rm i}k x_j}
$$

Parameters:

`ths`
:   The pointer to a nsfft plan
