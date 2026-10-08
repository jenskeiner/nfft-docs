---
symbol: solver_before_loop_double
kind: function
source: header
---
Initialises the iteration.

Set the samples `y`, the start vector `f_hat_iter`, and the weights `w` and `w_hat` if requested, then call this function once before the first step. It computes the first residual.

Parameters:

`ths`
:   The solver plan
