---
symbol: nnfft_precompute_full_psi
kind: function
source: header
---
Precomputation for a transform plan.

precomputes the values of the window function psi and their indices in
non tensor product form

if PRE_FULL_PSI is set the application program has to call this routine
after setting the nodes x and v

Parameters:

`ths_plan`
:   The pointer to a nfft plan
