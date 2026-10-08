---
symbol: PRE_PSI
kind: flag
source: header
---
If this flag is set, the convolution step (the multiplication with the
sparse matrix $\mathbf{B}$) uses $(2m+2)dM$ precomputed values of
the window function.

See also: `nfft_init`, `nfft_init_guru`.
