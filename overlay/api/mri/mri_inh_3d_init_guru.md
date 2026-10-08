---
symbol: mri_inh_3d_init_guru
kind: function
source: header
---
Creates a transform plan for the 3d method.

The plan holds a 3d NFFT plan. Its first two dimensions are the image
dimensions. The third dimension resolves the scaled field values $w_k$.
`N[2]` is the integer $N_3$ of the transform and `sigma` the oversampling
factor of the window in the third dimension.

Parameters:

`ths`
:   The plan for the transform

`N`
:   The multi-bandwidth of the three dimensions

`M`
:   The number of nodes

`n`
:   The oversampled multi-bandwidth

`m`
:   The cut-off parameter

`sigma`
:   The oversampling factor of the third dimension

`nfft_flags`
:   The flags of the NFFT plan

`fftw_flags`
:   The flags of the FFTW
