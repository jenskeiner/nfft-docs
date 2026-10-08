---
symbol: nfft_init_lin
kind: function
source: header
---
Initialisation of a transform plan with a lookup table of the window function.

As nfft_init_guru, and in addition sets the number `K` of equispaced samples of the window function that the flag PRE_LIN_PSI uses.

Parameters:

`ths`
:   The pointer to a nfft plan

`d`
:   The dimension

`N`
:   The multi-bandwidth

`M`
:   The number of nodes

`n`
:   The oversampled multi-bandwidth, i.e. the lengths of the FFTW transforms

`m`
:   The cut-off parameter of the window function

`K`
:   The number of equispaced samples of the window function

`flags`
:   NFFT flags to use

`fftw_flags`
:   FFTW flags to use
