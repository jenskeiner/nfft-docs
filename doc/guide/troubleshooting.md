# Troubleshooting

This page lists common problems when you build against NFFT3 and call the NFFT
module. Each section gives the symptom, the cause and the fix. For problems
with `configure` and with compilers, see the [FAQ](../reference/faq.md).

## Check a plan before the first transform

The transform functions do not test the plan. Only `nfft_check` does. No
function in `nfft/kernel/` calls it, so call it yourself. The example
`examples/nfft/simple_test.c` precomputes, then checks:

```c
--8<-- "examples/nfft/simple_test.c:39:53"
```

`nfft_check` returns `0` for a valid plan, else a message
(`nfft/kernel/nfft/nfft.c:6170-6208`). The sections below explain each
message. See [nfft_check](../api/nfft.md#check).

## Wrong results for an odd bandwidth

**Symptom.** The transform returns values that do not match `nfft_trafo_direct`.
`nfft_check` returns `polynomial degree N has to be even`.

**Cause.** Each $N_t$ must be even. The index set $I_N^d$ has
$-N_t/2 \le k_t < N_t/2$, see [Notation](index.md#notation). `nfft_check`
tests this at `nfft/kernel/nfft/nfft.c:6204-6205`. The init functions and the
transform functions do not test it.

**Fix.** Use an even $N_t$ in every dimension. To use an odd number of
coefficients, take the next even $N_t$ and set the extra coefficient to zero.

## Nodes outside the torus

**Symptom.** Wrong results. `nfft_check` returns
`ths->x out of range [-0.5,0.5)`.

**Cause.** Every coordinate of every node $\mathbf{x}_j$ must lie in
$[-1/2, 1/2)$. `nfft_check` tests all $dM$ coordinates at
`nfft/kernel/nfft/nfft.c:6186-6192`. The transform functions do not test them.

**Fix.** Map each coordinate into $[-1/2, 1/2)$ by adding or subtracting an
integer. The exponential $\mathrm{e}^{-2\pi\mathrm{i}\,\mathbf{k}\mathbf{x}}$
has period 1 in each coordinate of $\mathbf{x}$, because $\mathbf{k}$ is an
integer vector. So the shift does not change the sums of the
[definition](../transforms/nfft.md).

## No precomputation after the nodes are set

**Symptom.** `nfft_trafo` and `nfft_adjoint` return values that do not match
`nfft_trafo_direct` and `nfft_adjoint_direct`. `nfft_check` returns `0`.

**Cause.** A flag in `PRE_ONE_PSI` makes the init function allocate the member
`psi`, but not fill it (`nfft/kernel/nfft/nfft.c:5987-6001`). The default flags
of `nfft_init` and `nfft_init_1d` contain `PRE_PSI`
(`nfft/kernel/nfft/nfft.c:6069-6081`).
`nfft_precompute_one_psi` fills `psi` from the nodes
(`nfft/kernel/nfft/nfft.c:5939-5949`). `nfft_check` does not test this.

**Fix.** Set the nodes `x`. Then call
[nfft_precompute_one_psi](../api/nfft.md#precompute_one_psi) if
`flags & PRE_ONE_PSI` is not zero. Call it again each time the nodes change.
See [Plans and flags](plans-and-flags.md#precomputation).

## Other messages of nfft_check

The lines refer to `nfft/kernel/nfft/nfft.c`.

| Message | Cause | Fix |
|---------|-------|-----|
| `Member f not initialized.` | `f` is `NULL` (`nfft.c:6174-6175`). | Set `MALLOC_F` or assign an array. |
| `Member x not initialized.` | `x` is `NULL` (`nfft.c:6177-6178`). | Set `MALLOC_X` or assign an array. |
| `Member f_hat not initialized.` | `f_hat` is `NULL` (`nfft.c:6180-6181`). | Set `MALLOC_F_HAT` or assign an array. |
| `Number of nodes too small to use PRE_LIN_PSI.` | `PRE_LIN_PSI` is set and $K < M$ (`nfft.c:6183-6184`). | Use `PRE_PSI`, or a larger $K$. |
| `Oversampling factor too small` | $\sigma_t = n_t/N_t \le 1$ in a dimension (`nfft.c:5965`, `nfft.c:6194-6197`). | Choose $n_t > N_t$ in `nfft_init_guru`. |

## Linker errors

**Symptom.** The linker reports `cannot find -lnfft3`, or `undefined reference`
to a name that starts with `fftw_`.

**Cause.** The linker does not find the library, or the link line has no FFTW.
NFFT3 calls FFTW, so every program needs both. The `pkg-config` file names
both: `Requires: fftw3` and `Libs: -L${libdir} -lnfft3` (`nfft/nfft3.pc.in:9-10`).

**Fix.** Use `pkg-config --cflags --libs nfft3`. Without it, give the library
directory with `-L` and put `-lnfft3` before `-lfftw3` and `-lm`. See [Install](../getting-started/index.md#compile-against-it).

## Precision mismatch between header and library

**Symptom.** The program compiles. The linker reports `undefined reference` to
a name such as `nfftf_init_1d` or `nfftl_trafo`.

**Cause.** `nfft3.h` declares the functions of all three precisions
(`nfft/include/nfft3.h:190-192`). A library contains one precision only. The
macro `NFFT(name)` in `nfft3mp.h` adds the prefix of the precision macro that
you define (`nfft/include/nfft3mp.h:29-64`). If that precision is not the one
of the library, the names do not exist.

**Fix.** Link the library of the same precision: `-lnfft3f` and `-lfftw3f`
for `NFFT_PRECISION_SINGLE`, `-lnfft3l` and `-lfftw3l` for
`NFFT_PRECISION_LONG_DOUBLE`. See [Precision](precision.md).

## The program runs on one thread

**Symptom.** An OpenMP build does not run faster with more threads.
`nfft_has_threads_enabled()` returns 0.

**Cause.** The program links the serial library `libnfft3`. It has the same
names as the OpenMP library, so the link succeeds. In the serial library
`nfft_has_threads_enabled` returns 0 (`nfft/kernel/util/thread.c:51-58`).
The `pkg-config` file names the serial library only (`nfft/nfft3.pc.in:10`).

**Fix.** Link `-lnfft3_omp`, or `-lnfft3f_omp` or `-lnfft3l_omp`, and compile
with the OpenMP flag of the compiler. Call
[nfft_has_threads_enabled](../api/nfft.md#has_threads_enabled) to confirm.
See [OpenMP](openmp.md).
