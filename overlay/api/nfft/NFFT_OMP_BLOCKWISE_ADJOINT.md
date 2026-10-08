---
symbol: NFFT_OMP_BLOCKWISE_ADJOINT
kind: flag
source: header
---
If this flag is set and the library was built with OpenMP, the adjoint
transform gives each thread a block of the oversampled grid instead of using
atomic updates. The flag implies `NFFT_SORT_NODES`. It has no effect in a
library built without OpenMP.

See also: `NFFT_SORT_NODES`.
