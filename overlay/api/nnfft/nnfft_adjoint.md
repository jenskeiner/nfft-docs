---
symbol: nnfft_adjoint
kind: function
source: header
---
Executes a adjoint NNFFT, i.e. computes for $k=0,...,N_{total}-1$
$$
  \hat{f}(v_k) = \sum_{j = 0}^{M_{tota}l-1} f(x_j) {\rm e}^{2 \pi
                 {\rm i} v_k x_j \odot N}
$$

Parameters:

`ths_plan`
:   The plan
