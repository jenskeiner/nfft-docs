---
symbol: nfct_precompute_one_psi
kind: function
source: header
---
Precomputation for a transform plan.

The function calls the precomputation routines that match the flags PRE_PSI, PRE_FULL_PSI, PRE_FG_PSI and PRE_LIN_PSI. If one of these flags is set, the application program has to call this routine after setting the nodes `x`.

Parameters:

`ths`
:   The plan for the transform
