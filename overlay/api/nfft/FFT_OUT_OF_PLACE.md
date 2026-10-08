---
symbol: FFT_OUT_OF_PLACE
kind: flag
source: header
---
If this flag is set, FFTW uses disjoint input and output vectors. `nfft_init`
sets the flag for $d=1$ only.

See also: `nfft_init`, `nfft_init_guru`.
