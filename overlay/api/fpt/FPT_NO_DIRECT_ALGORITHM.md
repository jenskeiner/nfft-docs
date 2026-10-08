---
symbol: FPT_NO_DIRECT_ALGORITHM
kind: flag
source: header
---
If this flag is set, `fpt_precompute` does not keep the data for the direct
algorithm. `fpt_trafo_direct` and `fpt_transposed_direct` do not work. This
saves memory.
