---
symbol: PRE_ONE_PSI
kind: flag
source: header
---
Summarises if precomputation is used within the convolution step (the
multiplication with the sparse matrix $\mathbf{B}$).
If testing against this flag is positive, `nfft_precompute_one_psi` has
to be called.

See also: `nfft_init`, `nfft_init_guru`, `nfft_precompute_one_psi`, `nfft_finalize`.
