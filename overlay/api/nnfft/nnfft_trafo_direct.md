---
symbol: nnfft_trafo_direct
kind: function
source: header
---
Executes a direct NNDFT, i.e. computes for $j=0,...,M_{total}-1$
$$
  f(x_j) = \sum_{k = 0}^{N_{total}-1} \hat{f}(v_k) {\rm e}^{-2 \pi
           {\rm i} v_k x_j \odot N}
$$

Parameters:

`ths_plan`
:   The plan
