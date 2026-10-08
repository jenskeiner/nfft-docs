---
symbol: nfft_trafo_1d
kind: function
source: header
---
Computes an approximate NDFT for $d=1$ in $O(n\log n + M)$ operations.

nfft_trafo calls this function for $d=1$. The plan must satisfy $N > m$ and $n > 2m+2$, otherwise use nfft_trafo, which falls back to the direct algorithm.

Parameters:

`ths`
:   The pointer to a nfft plan
