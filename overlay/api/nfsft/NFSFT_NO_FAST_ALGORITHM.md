---
symbol: NFSFT_NO_FAST_ALGORITHM
kind: flag
source: header
---
If this flag is set, `nfsft_precompute` does not compute the data for the fast
algorithm and the init functions do not create the internal NFFT plan. The
transforms `nfsft_trafo` and `nfsft_adjoint` are then not available and their
output is not valid. The flag saves memory for precomputed data.

See also: `nfsft_precompute`, `nfsft_trafo`, `nfsft_adjoint`.
