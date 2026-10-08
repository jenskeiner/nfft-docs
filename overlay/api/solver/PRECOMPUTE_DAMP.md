---
symbol: PRECOMPUTE_DAMP
kind: flag
source: header
---
If this flag is set, the Fourier coefficients are damped, for example to
favour fast decaying coefficients. The plan allocates the array `w_hat` of
damping factors.
