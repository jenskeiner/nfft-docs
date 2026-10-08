---
symbol: nfft_precompute_one_psi
kind: function
source: header
---
Precomputation for a transform plan.

wrapper for precompute*_psi

if PRE_*_PSI is set the application program has to call this routine
(after) setting the nodes x

Parameters:

`ths`
:   The pointer to a nfft plan
