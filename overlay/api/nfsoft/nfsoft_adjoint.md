---
symbol: nfsoft_adjoint
kind: function
source: header
---
Executes an adjoint NFSOFT, i.e. computes for $l=0,\ldots,B;
m,n=-l,\ldots,l$
$$
  \hat{f}^{mn}_l = \sum_{j = 0}^{M-1} f(g_j)
                   \overline{D_l^{mn}\left( \alpha_j,\beta_j,\gamma_j\right)}
$$

Parameters:

`plan_nfsoft`
:   the plan
