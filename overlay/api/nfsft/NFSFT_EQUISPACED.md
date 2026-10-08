---
symbol: NFSFT_EQUISPACED
kind: flag
source: header
---
If this flag is set, we use the equispaced FFT instead of the NFFT.
This implies that the nodes are fixed to
$$ \varphi_i = 2\pi \frac{i}{2N+2}, \qquad i=-N-1,\dots,N, $$
$$ \vartheta_j = 2\pi \frac{j}{2N+2}, \qquad j=0,\dots,N+1. $$
