---
symbol: NFSOFT_REPRESENT
kind: flag
source: header
---
If this flag is set, the Wigner-D functions will be normed
such that they satisfy the representation property of
the spherical harmonics as defined in the NFFT software package, i.e.
for every rotation matrix `A` with Euler angles $\alpha, \beta, \gamma$
and every unit vector `x` the Wigner-D functions will be normed such that

$$
 \sum_{m=-l}^l D_{mn}^l(\alpha,\beta,\gamma) Y_m^l(x) = Y_n^l(A^{-1} x)
$$
