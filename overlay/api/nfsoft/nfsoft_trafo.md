---
symbol: nfsoft_trafo
kind: function
source: header
---
Executes a NFSOFT, i.e. computes for $j = 0,\ldots,M-1$
$$
  f(g_j) = \sum_{l=0}^B \sum_{m=-l}^l \sum_{n=-l}^l \hat{f}^{mn}_l
           D_l^{mn}\left( \alpha_j,\beta_j,\gamma_j\right).
$$

Parameters:

`plan_nfsoft`
:   the plan
