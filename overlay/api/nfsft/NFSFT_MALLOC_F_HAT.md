---
symbol: NFSFT_MALLOC_F_HAT
kind: flag
source: header
---
If this flag is set, the init methods (see `nfsft_init`, `nfsft_init_advanced`, and `nfsft_init_guru`) will allocate memory and the
method `nfsft_finalize` will free the array `f_hat` for you. Otherwise,
you have to assure by yourself that `f_hat` points to an array of
proper size before executing a transform and you are responsible for freeing
the corresponding memory before program termination.

See also: `nfsft_init`, `nfsft_init_advanced`, `nfsft_init_guru`.
