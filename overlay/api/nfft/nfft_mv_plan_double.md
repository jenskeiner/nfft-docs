---
symbol: nfft_mv_plan_double
kind: struct
source: agent
---
Base plan for a matrix-vector product with real data. The solver module takes this type in `solver_init_double` and `solver_init_advanced_double` (`nfft/include/nfft3.h`, lines 811-812).

The members come from the macro `MACRO_MV_PLAN` (`nfft/include/nfft3.h`, lines 54-60). The real transform plans `nfct_plan` and `nfst_plan` start with the same macro (`nfft/include/nfft3.h`, lines 229 and 309). Thus you cast a pointer to such a plan to `nfft_mv_plan_double *`. You do not create this type yourself. No program in `nfft/examples/` does this cast for the real type. The complex form of the same cast is in `nfft/examples/solver/simple_test.c`, line 101.

The init function of the transform sets `mv_trafo` and `mv_adjoint`, for example `nfft/kernel/nfct/nfct.c`, lines 1191-1192.

The solver reads all six members. It reads `N_total` and `M_total` to allocate its vectors (`nfft/kernel/solver/solver.c`, lines 396-425). In each step it writes `f_hat` or `f`, then calls `mv_trafo` or `mv_adjoint` (`nfft/kernel/solver/solver.c`, lines 434-458).

### N_total

Total number of Fourier coefficients. The length of `f_hat`.

### M_total

Total number of samples. The length of `f`.

### f_hat

The real Fourier coefficients. The input of `mv_trafo` and the output of `mv_adjoint`. The solver swaps its own vectors into this pointer for a call and swaps them back after it.

### f

The real samples. The output of `mv_trafo` and the input of `mv_adjoint`. The solver swaps its own vectors into this pointer for a call and swaps them back after it (`nfft/kernel/solver/solver.c`, lines 436-438).

### mv_trafo

Computes `f` from `f_hat`. The argument is the plan itself.

### mv_adjoint

Computes `f_hat` from `f`. The argument is the plan itself.
