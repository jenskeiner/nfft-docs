---
symbol: NFSOFT_NORMALIZED
kind: flag
source: header
---
By default, all computations are performed with respect to the
unnormalized basis functions
$$
  D_{mn}^l(\alpha,\beta,\gamma) = d^{mn}_{l}(\cos\beta)
  \mathrm{e}^{-\mathrm{i} m \alpha}\mathrm{e}^{-\mathrm{i} n \gamma}.
$$
If this flag is set, all computations are carried out using the $L_2$-
normalized basis functions
$$
 \tilde D_{mn}^l(\alpha,\beta,\gamma) = \sqrt{\frac{2l+1}{8\pi^2}}d^{mn}_{l}(\cos\beta)
  \mathrm{e}^{-\mathrm{i} m \alpha}\mathrm{e}^{-\mathrm{i} n \gamma}
$$

See also: `nfsoft_init`, `nfsoft_init_advanced`, `nfsoft_init_guru`.
