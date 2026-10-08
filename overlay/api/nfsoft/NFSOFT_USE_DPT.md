---
symbol: NFSOFT_USE_DPT
kind: flag
source: header
---
If this flag is set, the fast NFSOFT algorithms (see `nfsoft_trafo`,
`nfsoft_adjoint`) will use internally the usually slower direct
DPT algorithm in favor of the fast FPT algorithm.

See also: `nfsoft_init`, `nfsoft_init_advanced`, `nfsoft_init_guru`.
