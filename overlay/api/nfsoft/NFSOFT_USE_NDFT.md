---
symbol: NFSOFT_USE_NDFT
kind: flag
source: header
---
If this flag is set, the fast NFSOFT algorithms (see `nfsoft_trafo`,
`nfsoft_adjoint`) will use internally the exact but usually slower direct
NDFT algorithm in favor of fast but approximative NFFT algorithm.

See also: `nfsoft_init`, `nfsoft_init_advanced`, `nfsoft_init_guru`.
