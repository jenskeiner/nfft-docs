---
symbol: mri_inh_3d_trafo
kind: function
source: header
---
Executes a mri transformation considering the field inhomogeneity with the 3d method,
i.e. computes for $j=0,...,M_{total}-1$
$$
  f(x_j) = \sum_{k \in I_N^2} \hat{f}(k) {\rm e}^{-2 \pi {\rm i} N_3 w_k t_j}
                     {\rm e}^{-2 \pi {\rm i} k x_j}
$$

Parameters:

`ths`
:   The plan
