---
symbol: nfsoft_init_guru_advanced
kind: function
source: header
---
Creates a  NFSOFT transform plan.

Parameters:

`plan`
:   a pointer to a nfsoft_plan structure

`N`
:   the bandwidth $N \in \mathbb{N}_0$

`M`
:   the number of nodes $M \in \mathbb{N}$

`nfsoft_flags`
:   the NFSOFT flags

`nfft_flags`
:   the NFFT flags

`nfft_cutoff`
:   the NFFT cutoff parameter

`fpt_kappa`
:   a parameter controlling the accuracy of the FPT

`nn_oversampled`
:   the size of the 3D FFTW transform inside the NFFT, `nn_oversampled` $= (2N+2)\,\sigma$, where $\sigma\ge1$ is the oversampling factor
