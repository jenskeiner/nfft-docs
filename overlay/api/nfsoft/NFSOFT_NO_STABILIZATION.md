---
symbol: NFSOFT_NO_STABILIZATION
kind: flag
source: header
---
If this flag is set, the fast NFSOFT algorithms (see `nfsoft_trafo`,
`nfsoft_adjoint`) will use internally the FPT algorithm without the
stabilization scheme and thus making bigger errors for higher
bandwidth but becoming significantly faster
