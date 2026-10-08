---
symbol: FPT_AL_SYMMETRY
kind: flag
source: header
---
If this flag is set, the precomputed data uses the symmetry of associated
Legendre functions, $P(-x) = \pm P(x)$, and stores half of the entries in the
range where the symmetry holds. The NFSFT and NFSOFT modules set it. Do not
set it for other recurrence coefficients.
