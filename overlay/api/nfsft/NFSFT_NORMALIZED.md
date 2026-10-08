---
symbol: NFSFT_NORMALIZED
kind: flag
source: header
---
By default, all computations are performed with respect to the
unnormalized basis functions
$$
  \tilde{Y}_k^n(\vartheta,\varphi) = P_k^{|n|}(\cos\vartheta)
  \mathrm{e}^{\mathrm{i} n \varphi}.
$$
If this flag is set, all computations are carried out using the $L_2$-
normalized basis functions
$$
  Y_k^n(\vartheta,\varphi) = \sqrt{\frac{2k+1}{4\pi}} P_k^{|n|}(\cos\vartheta)
  \mathrm{e}^{\mathrm{i} n \varphi}.
$$

See also: `nfsft_init`, `nfsft_init_advanced`, `nfsft_init_guru`.
