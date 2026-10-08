---
symbol: nfft_clock_gettime_seconds
kind: function
source: header
---
Returns the wall clock time in seconds.

The time comes from `clock_gettime` with `CLOCK_REALTIME`. The function returns 0 if `clock_gettime` is not available.
