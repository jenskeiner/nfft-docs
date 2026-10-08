---
symbol: NFSFT_ZERO_F_HAT
kind: flag
source: header
---
If this flag is set, the fast adjoint transform `nfsft_adjoint` sets all
unused entries of `f_hat`, those that do not correspond to a spherical Fourier
coefficient, to zero. The direct adjoint transform `nfsft_adjoint_direct`
always does so.
