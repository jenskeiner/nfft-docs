---
symbol: nfsft_precompute_x
kind: function
source: header
---
Precomputes the data that depends on the nodes.

Call this function after setting the nodes `x` of the plan and before the first transform. It passes the nodes to the internal NFFT plan and runs its precomputation when a PRE_* flag is set. The function does nothing if the plan uses the flags NFSFT_NO_FAST_ALGORITHM or NFSFT_EQUISPACED.

Parameters:

`plan`
:   The plan
