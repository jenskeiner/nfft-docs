---
symbol: nnfft_precompute_psi
kind: function
source: header
---
Precomputation for a transform plan.

precomputes the values of the window function psi in a tensor product form

if PRE_PSI is set the application program has to call this routine after
setting the nodes x and v

Parameters:

`ths_plan`
:   The pointer to a nfft plan
