---
symbol: nfft_trafo_3d
kind: function
source: header
---
Computes an approximate NDFT for $d=3$ in $O(n\log n + M)$ operations.

nfft_trafo calls this function for $d=3$. The plan must satisfy $N_t > m$ and $n_t > 2m+2$ for each dimension $t$, otherwise use nfft_trafo, which falls back to the direct algorithm.

Parameters:

`ths`
:   The pointer to a nfft plan
