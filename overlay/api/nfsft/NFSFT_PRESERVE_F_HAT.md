---
symbol: NFSFT_PRESERVE_F_HAT
kind: flag
source: header
---
If this flag is set, the transforms `nfsft_trafo_direct` and `nfsft_trafo`
leave the content of `f_hat` unchanged. Without the flag, `nfsft_trafo`
overwrites `f_hat`, and `nfsft_trafo_direct` overwrites it if
`NFSFT_NORMALIZED` is set.

See also: `nfsft_init`, `nfsft_init_advanced`, `nfsft_init_guru`.
