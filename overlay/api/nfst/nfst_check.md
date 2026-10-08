---
symbol: nfst_check
kind: function
source: header
---
Checks a transform plan for frequently used bad parameters.

The function returns a null pointer if the plan is fine, and otherwise a message. It tests that `f`, `x` and `f_hat` are set, that all nodes lie in $[0,1/2)$, that the oversampling factor is larger than 1, and that $N_t-1 > m$.

Parameters:

`ths`
:   The plan for the transform
