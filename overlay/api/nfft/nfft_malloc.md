---
symbol: nfft_malloc
kind: function
source: header
---
Allocates `n` bytes aligned for use with the FFTW.

If the hook nfft_malloc_hook is set, the call is passed to the hook. A request for 0 bytes allocates 1 byte. If the allocation fails, the function calls nfft_die.

Parameters:

`n`
:   The number of bytes to allocate
