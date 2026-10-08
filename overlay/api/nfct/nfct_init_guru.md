---
symbol: nfct_init_guru
kind: function
source: header
---
Initialisation of a transform plan.

As nfct_init, with control over the oversampled bandwidth `n`, the cut-off `m` and the flags.

Parameters:

`ths_plan`
:   The plan for the transform

`d`
:   The dimension

`N`
:   The multi-bandwidth

`M_total`
:   The number of nodes

`n`
:   The oversampled multi-bandwidth

`m`
:   The cut-off parameter of the window function

`flags`
:   NFCT flags to use

`fftw_flags`
:   FFTW flags to use
