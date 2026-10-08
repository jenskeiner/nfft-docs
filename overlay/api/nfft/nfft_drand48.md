---
symbol: nfft_drand48
kind: function
source: header
---
Returns a pseudo-random number in $[0,1)$.

The function uses `drand48` of the C library when it is available and `rand()/RAND_MAX` otherwise.
