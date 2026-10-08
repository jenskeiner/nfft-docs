---
symbol: nfsft_precompute
kind: function
source: header
---
Performes precomputation up to the next power of two with respect to a given
bandwidth $N \in \mathbb{N}_2$. The threshold parameter $\kappa \in
\mathbb{R}^{+}$ determines the number of stabilization steps computed in
the discrete polynomial transform and thereby its accuracy.

Parameters:

`N`
:   the bandwidth $N \in \mathbb{N}_0$

`kappa`
:   the threshold $\kappa \in \mathbb{R}^{+}$

`nfsft_flags`
:   the NFSFT precomputation flags

`fpt_flags`
:   the FPT precomputation flags
