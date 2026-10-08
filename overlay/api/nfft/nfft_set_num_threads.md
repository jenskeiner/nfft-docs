---
symbol: nfft_set_num_threads
kind: function
source: header
---
Sets the number of threads for subsequent OpenMP parallel regions.

The function has no effect if the library was built without OpenMP. Plans that exist already can keep the old number of threads in the FFT step.

Parameters:

`nthreads`
:   The number of threads
