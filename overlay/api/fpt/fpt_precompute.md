---
symbol: fpt_precompute
kind: function
source: header
---
Computes the data required for a single DPT transform.

The recurrence coefficients define the polynomials $P_k$ by $P_{-1}(x) = 0$,
$P_0(x) = \gamma_0$ and
$P_k(x) = (\alpha_k x+\beta_k) P_{k-1}(x) + \gamma_k P_{k-2}(x)$ for
$k \ge 1$.

Parameters:

`set`
:   The set of DPT transform data where the computed data will be stored.

`m`
:   The transform index $m \in \mathbb{N}_0, 0 \le m < M$.

`alpha`
:   The three-term recurrence coefficients $\alpha_k \in \mathbb{R}$ for $k=0,\ldots,N$ such that `alpha[k]` $=\alpha_k$.

`beta`
:   The three-term recurrence coefficients $\beta_k \in \mathbb{R}$ for $k=0,\ldots,N$ such that `beta[k]` $=\beta_k$.

`gam`
:   The three-term recurrence coefficients $\gamma_k \in \mathbb{R}$ for $k=0,\ldots,N$ such that `gam[k]` $=\gamma_k$.

`k_start`
:   The index $k_{\text{start}} \in \mathbb{N}_0, 0 \le k_{\text{start}} \le N$ of the first coefficient of the transform. The input of the transform holds the coefficients $x_k$ for $k=k_{\text{start}},\ldots,k_{\text{end}}$, starting at `x[0]`.

`threshold`
:   The threshold $\kappa \in \mathbb{R}, \kappa > 0$. It determines the number of stabilization steps and thereby the accuracy.
