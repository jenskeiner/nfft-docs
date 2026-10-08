---
symbol: nnfft_precompute_one_psi
kind: function
source: header
---
Precomputation for a transform plan.

The function calls the precomputation routines that match the flags PRE_PSI, PRE_FULL_PSI, PRE_LIN_PSI and PRE_PHI_HUT. If one of these flags is set, the application program has to call this routine after setting the nodes `x` and `v`.

Parameters:

`ths`
:   The plan for the transform
