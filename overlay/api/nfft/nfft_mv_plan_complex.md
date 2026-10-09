---
symbol: nfft_mv_plan_complex
kind: struct
source: agent
---
Base plan for a matrix-vector product with complex data. The solver module takes this type in `solver_init_complex` and `solver_init_advanced_complex` (`nfft/include/nfft3.h`, lines 782-783).

The members come from the macro `MACRO_MV_PLAN` (`nfft/include/nfft3.h`, lines 54-60). Every complex transform plan, for example `nfft_plan`, starts with the same macro (`nfft/include/nfft3.h`, line 111). Thus you cast a pointer to such a plan to `nfft_mv_plan_complex *`. You do not create this type yourself. Example: `nfft/examples/solver/simple_test.c`, line 101, casts an `nfft_plan`. `nfft/examples/nnfft/simple_test.c`, line 208, casts an `nnfft_plan`.

The init function of the transform sets `mv_trafo` and `mv_adjoint`, for example `nfft/kernel/nfft/nfft.c`, lines 6045-6046.

The solver reads all six members. It reads `N_total` and `M_total` to allocate its vectors (`nfft/kernel/solver/solver.c`, lines 46-73). In each step it writes `f_hat` or `f`, then calls `mv_trafo` or `mv_adjoint` (`nfft/kernel/solver/solver.c`, lines 83-108).

### N_total

Total number of Fourier coefficients. The length of `f_hat`.

### M_total

Total number of samples. The length of `f`.

### f_hat

The Fourier coefficients. The input of `mv_trafo` and the output of `mv_adjoint`. The solver swaps its own vectors into this pointer for a call and swaps them back after it (`nfft/kernel/solver/solver.c`, lines 106-108).

### f

The samples. The output of `mv_trafo` and the input of `mv_adjoint`. The solver swaps its own vectors into this pointer for a call and swaps them back after it (`nfft/kernel/solver/solver.c`, lines 85-87).

### mv_trafo

Computes `f` from `f_hat`. The argument is the plan itself.

### mv_adjoint

Computes `f_hat` from `f`. The argument is the plan itself.
