---
symbol: nfft_die
kind: function
source: header
---
Reports a fatal error and ends the program.

The function calls the hook nfft_die_hook with the message if the hook is set. Then it calls `exit(EXIT_FAILURE)`.

Parameters:

`s`
:   The error message
