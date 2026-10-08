---
symbol: PRE_FULL_PSI
kind: flag
source: header
---
If this flag is set, the convolution step (the multiplication with the
sparse matrix $\mathbf{B}$) uses $(2m+2)^dM$ precomputed values of
the window function, in addition indices of source and target vectors are
stored.

See also: `nfft_init`, `nfft_init_guru`.
