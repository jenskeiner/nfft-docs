---
symbol: NFSFT_USE_DPT
kind: flag
source: header
---
If this flag is set, the fast NFSFT algorithms (see `nfsft_trafo`,
`nfsft_adjoint`) will use internally the usually slower direct
DPT algorithm in favor of the fast FPT algorithm.

See also: `nfsft_init`, `nfsft_init_advanced`, `nfsft_init_guru`.
