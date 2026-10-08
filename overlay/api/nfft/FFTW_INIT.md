---
symbol: FFTW_INIT
kind: flag
source: header
---
If this flag is set, the plan allocates the oversampled vectors and creates
the FFTW plans, and `nfft_finalize` destroys them. Without the flag, the
plan has no FFTW plans and the application must supply them.

See also: `nfft_init`, `nfft_init_guru`, `nfft_finalize`.
