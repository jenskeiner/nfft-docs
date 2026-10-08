---
symbol: PRE_LIN_PSI
kind: flag
source: header
---
If this flag is set, the convolution step (the multiplication with the
sparse matrix $\mathbf{B}$) uses linear interpolation from a lookup table of
equispaced samples of the window function instead of exact values of the
window function. The table has $K+1$ entries per dimension. `nfft_init` and
`nfft_init_guru` choose $K$ from the cut-off parameter $m$ and the window
function, and `nfft_init_lin` sets $K$ explicitly.

See also: `nfft_init`, `nfft_init_guru`, `nfft_init_lin`.
