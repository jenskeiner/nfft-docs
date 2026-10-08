---
symbol: solver_loop_one_step_double
kind: function
source: header
---
Executes one step of the iteration that the flags of the plan select.

Call the function repeatedly after solver_before_loop. Read the iterate from `f_hat_iter`. The member `dot_r_iter` holds the weighted squared norm of the residual, except for the Landweber iteration without the flag NORMS_FOR_LANDWEBER.

Parameters:

`ths`
:   The solver plan
