---
symbol: nsfft_trafo
kind: function
source: header
---
Executes an NSFFT, computes fast and approximate for
$j=0,\dots,M-1$:
$$
  f_j = \sum_{k\in H_N^d}\hat f_k {\rm e}^{-2\pi{\rm i}k x_j}
$$

Parameters:

`ths`
:   The pointer to a nsfft plan
