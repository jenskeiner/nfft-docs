---
symbol: PRE_FG_PSI
kind: flag
source: header
---
If this flag is set, the convolution step (the multiplication with the
sparse matrix $\mathbf{B}$) uses particular properties of the Gaussian
window function to trade multiplications for direct calls to exponential
function (the remaining $2dM$ direct calls are precomputed).

See also: `nfft_init`, `nfft_init_guru`.
