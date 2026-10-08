---
symbol: FPT_PERSISTENT_DATA
kind: flag
source: header
---
If this flag is set, the set keeps the pointers `alpha`, `beta` and `gam` that
are passed to `fpt_precompute` instead of copying the arrays. The arrays must
stay valid until `fpt_finalize`. Otherwise `fpt_precompute` copies the
arrays for the direct algorithm.
