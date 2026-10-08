---
symbol: NFSOFT_MALLOC_X
kind: flag
source: header
---
If this flag is set, the init methods (see `nfsoft_init`,
`nfsoft_init_advanced`, and `nfsoft_init_guru`) will allocate memory and the
method `nfsoft_finalize` will free the array `x` for you. Otherwise,
you have to assure by yourself that `x` points to an array of
proper size before executing a transform and you are responsible for freeing
the corresponding memory before program termination.

See also: `nfsoft_init`, `nfsoft_init_advanced`, `nfsoft_init_guru`.
