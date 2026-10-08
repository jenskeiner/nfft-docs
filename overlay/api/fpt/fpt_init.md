---
symbol: fpt_init
kind: function
source: header
---
Initializes a set of precomputed data for DPT transforms of equal length.

The set holds the data of $M$ transforms of length $N = 2^t$. Fill the
data of the transform with index $m$ with fpt_precompute.

Parameters:

`M`
:   The number $M \in \mathbb{N}$ of DPT transforms. The individual transforms are addressed by an index number $m \in \mathbb{N}_0$ with range $m = 0,\ldots,M-1$.

`t`
:   The exponent $t \in \mathbb{N}, t \ge 2$ of the transform length $N = 2^t \in \mathbb{N}, N \ge 4$

`flags`
:   A bitwise combination of the flags FPT_NO_STABILIZATION, FPT_NO_FAST_ALGORITHM, FPT_NO_DIRECT_ALGORITHM, FPT_PERSISTENT_DATA, FPT_NO_INIT_FPT_DATA and FPT_AL_SYMMETRY
