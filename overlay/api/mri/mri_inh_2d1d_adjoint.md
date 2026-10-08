---
symbol: mri_inh_2d1d_adjoint
kind: function
source: header
---
Executes an adjoint mri transformation considering the field inhomogeneity with the 2d1d method,
i.e. computes for $k \in I_N^2$
$$
  \hat{f}(k) = \sum_{j=0}^{M_{total}-1} f(x_j) {\rm e}^{2 \pi {\rm i} N_3 w_k t_j}
                     {\rm e}^{2 \pi {\rm i} k x_j}
$$

Parameters:

`ths`
:   The plan
