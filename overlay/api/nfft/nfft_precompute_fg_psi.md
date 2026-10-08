---
symbol: nfft_precompute_fg_psi
kind: function
source: header
---
Precomputes the data for the flag PRE_FG_PSI, which stores two values per node and dimension for the fast Gaussian gridding.

Call nfft_precompute_one_psi instead. It calls this function when the flag is set.

Parameters:

`ths`
:   The pointer to a nfft plan
