---
symbol: nnfft_init_1d
kind: function
source: header
---
Initialisation of a transform plan, wrapper $d=1$.

The function calls nnfft_init with $d=1$ and $N_{total} = N$.

Parameters:

`ths_plan`
:   The plan for the transform

`N`
:   The number of frequency nodes and the bandwidth

`M_total`
:   The number of spatial nodes
