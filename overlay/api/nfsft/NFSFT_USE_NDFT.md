---
symbol: NFSFT_USE_NDFT
kind: flag
source: header
---
If this flag is set, the fast NFSFT algorithms (see `nfsft_trafo`,
`nfsft_adjoint`) will use internally the exact but usually slower direct
NDFT algorithm in favor of fast but approximative NFFT algorithm.

See also: `nfsft_init`, `nfsft_init_advanced`, `nfsft_init_guru`.
