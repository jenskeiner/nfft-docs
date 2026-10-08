---
symbol: nfft_free
kind: function
source: header
---
Frees memory that nfft_malloc returned.

A null pointer is ignored. If the hook nfft_free_hook is set, the call is passed to the hook.

Parameters:

`p`
:   The pointer to the memory region to free
