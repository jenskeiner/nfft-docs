---
symbol: NFSOFT_INDEX
kind: macro
source: header
---
This helper macro expands to the index $i$ that corresponds to the SO(3)
Fourier coefficient $\hat f^{mn}_l$ for $l=0,\ldots,B$, $m,n=-l,\ldots,l$,
with

$$
  i = (l+B+1) + (2B+2)\bigl((n+B+1) + (2B+2)(m+B+1)\bigr).
$$
