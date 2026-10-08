---
symbol: NFSFT_NO_DIRECT_ALGORITHM
kind: flag
source: header
---
If this flag is set, `nfsft_precompute` does not compute the data for the
direct algorithm. The transforms `nfsft_trafo_direct` and
`nfsft_adjoint_direct` are then not available and their output is not valid.
The flag saves some memory for precomputed data.

See also: `nfsft_precompute`, `nfsft_trafo_direct`, `nfsft_adjoint_direct`.
