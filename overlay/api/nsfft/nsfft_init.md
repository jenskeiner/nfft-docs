---
symbol: nsfft_init
kind: function
source: header
---
Initialisation of a transform plan.

The function needs a library that was built with the Gaussian window
function. Otherwise it prints an error message and does not initialise the
plan.

Parameters:

`ths`
:   The pointer to a nsfft plan

`d`
:   The dimension

`J`
:   The problem size

`M`
:   The number of nodes

`m`
:   nfft cut-off parameter

`flags`
:   NSFFT flags to use, for example NSDFT
