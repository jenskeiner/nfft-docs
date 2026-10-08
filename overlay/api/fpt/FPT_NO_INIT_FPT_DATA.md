---
symbol: FPT_NO_INIT_FPT_DATA
kind: flag
source: header
---
If this flag is set, `fpt_init` does not allocate the data of the individual
transforms. The routines of the NFSFT and NFSOFT modules use the flag when
they fill a set themselves.
