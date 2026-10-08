---
symbol: nnfft_precompute_phi_hut
kind: function
source: header
---
Precomputation for a transform plan.

precomputes the values of the fourier transformed window function, i.e. phi_hut

if PRE_PHI_HUT is set the application program has to call this routine
after setting the nodes x

Parameters:

`ths_plan`
:   The pointer to a nfft plan
