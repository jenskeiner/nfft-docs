---
symbol: NFSFT_INDEX
kind: macro
source: header
---
This helper macro expands to the index $i$ that corresponds to the
spherical Fourier coefficient $\mathtt{f\_hat}(k,n)$ for $0 \le k \le N$,
$-k \le n \le k$, with

$$
  i = (2N+2)(N-n+1)+N+k+1.
$$
