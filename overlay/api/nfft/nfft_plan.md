---
symbol: nfft_plan
kind: struct
source: header
---

### m

Cut-off parameter for window function. The default depends
on the window the library was compiled with and on the precision.
Query it with X(get_default_window_cut_off)() rather than
assuming a value. In double precision it is

-  8 (KAISER_BESSEL),
- 11 (SINC_POWER),
- 11 (B_SPLINE),
- 13 (GAUSSIAN)
