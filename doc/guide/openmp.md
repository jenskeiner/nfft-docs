# OpenMP

The library can use OpenMP threads in the NFFT core and in the direct
transforms. An OpenMP build produces a second library next to the serial one.
The two libraries export the same names. A program links one of them. This page
describes the build, the thread functions, the parts that run in parallel and the
two ways to compute the parallel adjoint.

## Build

=== "Autotools"

    ```bash
    ./configure --enable-all --enable-openmp
    make -j
    ```

    The build makes the serial library `libnfft3` and the OpenMP library
    `libnfft3_omp`. The precision suffix goes before `_omp`: `libnfft3f_omp` for
    float and `libnfft3l_omp` for long double. The build also makes the second
    copy `libnfft3_threads` with the same content. `make check` runs
    `tests/checkall_threads` in addition to `tests/checkall`.

=== "CMake"

    ```bash
    cmake -S . -B build -DNFFT_ENABLE_OPENMP=ON
    cmake --build build -j
    ```

    `NFFT_ENABLE_OPENMP` is on by default. The OpenMP library is the target
    `nfft3_omp`. The install step copies it as a plain library file. It is not
    part of the exported CMake package, so `find_package` finds only the serial
    target `NFFT3::nfft3`.

A program that uses the OpenMP library compiles with the OpenMP flag of the
compiler and links `-lnfft3_omp`. The link also needs the FFTW library that the
build used, see below.

### Requirements

- A compiler with OpenMP. `configure` stops if `--enable-openmp` is set and the
  compiler has none.
- Working `#pragma omp atomic` on the real type of the selected precision. The
  configure script tests this and, if needed, adds `-latomic`. It stops with
  `OpenMP atomic operations do not work.` if neither variant links.
- A threaded FFTW for a threaded FFT step. The build looks for the OpenMP variant
  `libfftw3_omp` first. If it is missing, it uses `libfftw3_threads` and warns
  that this may be less efficient, because NFFT uses OpenMP threads and FFTW
  uses its own. If only the single-threaded FFTW exists, the build warns and the
  FFT step stays single-threaded. The other steps still use OpenMP. In the first
  two cases the build defines `HAVE_FFTW_THREADS`.

## Number of threads

NFFT3 does not manage threads itself. It uses the OpenMP team size. The public
functions read and set that size. Each has a `nfftf_` and a `nfftl_` form for
float and long double.

| Function | Result |
|----------|--------|
| `nfft_get_num_threads()` | The size of the OpenMP team that a parallel region gets now. |
| `nfft_set_num_threads(n)` | Calls `omp_set_num_threads(n)`. |
| `nfft_has_threads_enabled()` | 1 in the OpenMP library and 0 in the serial library. |

Without `nfft_set_num_threads`, the team size comes from the OpenMP defaults, for
example from the variable `OMP_NUM_THREADS`. In the serial library
`nfft_get_num_threads` returns 1 and `nfft_set_num_threads` does nothing.

NFFT3 has no functions like `fftw_init_threads` and `fftw_cleanup_threads`.

### FFTW threads

`nfft_init` and its variants ask FFTW for `nfft_get_num_threads()` threads when
they create the FFTW plans. This happens only if the library was built with
`HAVE_FFTW_THREADS`. The plan keeps that thread count. Changing the team size
later with `nfft_set_num_threads` changes the loops of NFFT, but not the FFT of
a plan that exists already. Set the number of threads before you create the
plan.

The library does not call `fftw_init_threads`. The FFTW manual asks for this call
before threaded planning. If you use a threaded FFTW, call it once before the
first plan, as `benchmarks/bench_nfft_fast.cpp` does. That benchmark calls
`fftw_cleanup_threads` at exit, after it has destroyed its last plan. The
function invalidates all existing plans.

```c
omp_set_num_threads(4);      /* or nfft_set_num_threads(4) */
fftw_init_threads();         /* threaded FFTW only */

nfft_plan p;
nfft_init_2d(&p, N1, N2, M); /* threaded FFTW: this plan's FFT uses 4 threads */
```

FFTW planning is not thread safe. The library therefore runs the creation of the
FFTW plans in a named critical section when it is built with `HAVE_FFTW_THREADS`,
and the destruction of the FFTW plans in an OpenMP build. Several threads can
create and destroy NFFT plans. They wait for each other. Other modules differ,
see [Thread safety](#thread-safety).

## What runs in parallel

| Step | In parallel |
|------|-------------|
| Deconvolution $\mathbf{D}$ | Yes, loops over the frequencies. |
| FFT | Only with a threaded FFTW. The plan fixes the thread count. |
| Convolution $\mathbf{B}$, forward | Yes, loop over the nodes. |
| Convolution $\mathbf{B}$, adjoint | Yes, see the next section. |
| Node sorting | Yes, the radix sort of `NFFT_SORT_NODES` uses the team. |
| `nfft_precompute_one_psi` | Yes for `PRE_PSI`, `PRE_FG_PSI` and `PRE_FULL_PSI`. The `PRE_LIN_PSI` table is filled serially. |
| `nfft_trafo_direct` | Yes, loop over the nodes. |
| `nfft_adjoint_direct` | Yes. Each thread gets a disjoint range of the frequencies. |

## The adjoint transform

The adjoint convolution adds the contribution of each node to $(2m+2)^d$ grid
values. Two nodes can write to the same grid value. The library has two
strategies to keep the sums right.

**Atomic additions.** The loop over the nodes runs in parallel. Each addition to
the grid is an atomic operation, one for the real and one for the imaginary
part. This is the strategy when `NFFT_OMP_BLOCKWISE_ADJOINT` is not set.

**Blockwise.** The flag `NFFT_OMP_BLOCKWISE_ADJOINT` selects it. The library
splits the oversampled grid along the first dimension into contiguous blocks, one
per thread. If $n_0$ is smaller than the team, only $n_0$ threads get a block.
Each thread scans the sorted node list for the nodes whose stencil overlaps its
block and writes only inside its block. No atomic operation is needed. A node
whose stencil crosses a block border is visited by more than one thread, and each
thread writes its own part. The flag implies `NFFT_SORT_NODES`, because the
threads find their nodes in the sorted index. That index takes $2M$ integers.

| Case | Adjoint strategy |
|------|------------------|
| `nfft_init`, $d=1$ | Atomic. |
| `nfft_init`, $d>1$, OpenMP library | Blockwise. |
| `nfft_init_guru` and `nfft_init_lin` | As set by `flags`. |

Both strategies work with every precomputation flag. In the serial library the
flag has no effect on the adjoint. It still turns on the node sorting.

The order of the atomic additions is not fixed. The atomic adjoint can therefore
return results that differ in the last digits from run to run. The
[accuracy tracking](accuracy.md) records serial and OpenMP runs as separate
metrics for this reason.

## Example

`examples/nfft/simple_test_threads.c` times a one-dimensional transform with
$N=M=10^6$. The example `examples/nfft/nfft_benchomp.c` runs benchmarks of the
OpenMP code and writes the results as pgfplots. It uses
`examples/nfft/nfft_benchomp_createdataset.c` and
`examples/nfft/nfft_benchomp_detail.c`.

## Thread safety

This section says which calls a program can make from several of its own
threads at the same time. It applies to the serial and to the OpenMP library.
The line numbers refer to `nfft/` at commit `49a0989d`.

### One plan per thread

A plan holds its own work arrays. `nfft_init_guru` allocates the oversampled
grids `g1` and `g2` in the plan (`kernel/nfft/nfft.c:6013-6018`). `nfft_trafo`
and `nfft_adjoint` write to these grids and to `f` or `f_hat`. The code has no
lock on a plan. Do not use one plan in two threads at the same time. This
includes `nfft_precompute_one_psi`, which writes the tables of the plan.

Two threads can run `nfft_trafo` or `nfft_adjoint` on two different plans at
the same time. Each call executes only the FFTW plans of its own plan
(`kernel/nfft/nfft.c:2947`, `kernel/nfft/nfft.c:2984`). The FFTW manual says
that `fftw_execute` is thread safe. The NFFT kernel has no other global state
that a transform writes. The same holds for `nfct_trafo`, `nfst_trafo` and
their adjoints. NFSFT and FPT are different, see below.

### Protection of FFTW planning

FFTW planning is not thread safe. The library puts the creation and the
destruction of FFTW plans in a named critical section,
`#pragma omp critical (nfft_omp_critical_fftw_plan)`. All modules use the same name, so their FFTW
calls wait for each other. The critical section exists only in the OpenMP
library. The serial library has none.

| Module | Plan creation | Plan destruction |
|--------|---------------|------------------|
| `nfft` | `nfft_init_guru` and the other init functions: `kernel/nfft/nfft.c:6020-6037`, only with `HAVE_FFTW_THREADS` | `nfft_finalize`: `kernel/nfft/nfft.c:6219-6226` |
| `nfct` | `nfct_init_guru`: not protected, `kernel/nfct/nfct.c:1181` | `nfct_finalize`: `kernel/nfct/nfct.c:1330-1333` |
| `nfst` | `nfst_init_guru`: not protected, `kernel/nfst/nfst.c:1180` | `nfst_finalize`: `kernel/nfst/nfst.c:1329-1332` |
| `nfsft` | Through `nfft_init_guru` (`kernel/nfsft/nfsft.c:351`). `nfsft_trafo` with `NFSFT_EQUISPACED`: `kernel/nfsft/nfsft.c:1274-1282`, only with `HAVE_FFTW_THREADS`. `nfsft_adjoint` with `NFSFT_EQUISPACED`: not protected, `kernel/nfsft/nfsft.c:1384` | Through `nfft_finalize`. `nfsft_trafo`: `kernel/nfsft/nfsft.c:1290-1293`. `nfsft_adjoint`: not protected, `kernel/nfsft/nfsft.c:1390` |
| `fpt` | `fpt_init`: `kernel/fpt/fpt.c:866-877` and `kernel/fpt/fpt.c:887-898`. `fpt_trafo` and `fpt_transposed` with `FPT_FUNCTION_VALUES`: `kernel/fpt/fpt.c:1433-1443`, `kernel/fpt/fpt.c:1797-1806`. All only with `HAVE_FFTW_THREADS` | `fpt_finalize`: `kernel/fpt/fpt.c:2076-2082`. `fpt_trafo`, `fpt_transposed`: `kernel/fpt/fpt.c:1672-1675`, `kernel/fpt/fpt.c:1808-1811` |

!!! warning
    Not every FFTW planner call is protected. `nfct_init_guru`,
    `nfst_init_guru` and the equispaced path of `nfsft_adjoint` call the
    planner outside the critical section. In an OpenMP library without
    `HAVE_FFTW_THREADS`, plan creation in `nfft`, `nfsft` and `fpt` is not
    protected either. The serial library protects nothing. In these cases,
    create and destroy plans in one thread, or put a lock of your own around
    the init and finalize calls.

### NFSFT and FPT

NFSFT keeps its precomputed data in one static variable `wisdom`
(`kernel/nfsft/nfsft.c:87-91`). `nfsft_precompute` fills it and
`nfsft_forget` frees it. Neither function has a lock. `nfsft_precompute`
reads `wisdom.initialized` and returns if it is set
(`kernel/nfsft/nfsft.c:381-384`). Call `nfsft_precompute` once in one thread
before the threads start, and call `nfsft_forget` after they end.

The fast `nfsft_trafo` and `nfsft_adjoint` use the FPT sets in `wisdom` for all
plans (`kernel/nfsft/nfsft.c:1202-1229`). An FPT set holds the work arrays
`work` and `result` (`kernel/fpt/fpt.c:857-858`). `fpt_trafo` writes to them
and to the scratch array `z` of the set (`kernel/fpt/fpt.c:214-216`). Two
threads that run the fast NFSFT at the same time therefore write to the same
arrays, even with two different plans. Do not do this. For the same reason,
do not use one FPT set in two threads at the same time.

### Hooks

`nfft_malloc_hook`, `nfft_free_hook` and `nfft_die_hook` are plain global
pointers without a lock (`kernel/util/malloc.c:23-25`). `nfft_malloc`,
`nfft_free` and `nfft_die` read them on each call
(`kernel/util/malloc.c:31-32`, `kernel/util/malloc.c:49-51`,
`kernel/util/malloc.c:60-61`). The library itself calls `nfft_malloc` from
several OpenMP threads at the same time, for example in `fpt_init` inside the
parallel region of `nfsft_precompute` (`kernel/nfsft/nfsft.c:441-456`). The
code and the header (`include/nfft3.h:73-82`) make no further statement. From
this code it follows:

- Set the hooks before the first call to the library, and do not change them
  while other threads use it.
- A malloc or free hook must be safe to call from several threads at the same
  time.
- A die hook that returns does not stop the exit: `nfft_die` calls `exit`
  after the hook (`kernel/util/malloc.c:63`).

## Limits

- The thread count of the FFT is fixed when the plan is created.
- The blockwise adjoint uses at most $n_0$ threads.
- A threaded FFT step needs a threaded FFTW at build time.
- Both libraries define the same symbols. Link only one of them.

## API

[NFFT API reference](../api/nfft.md), `get_num_threads`, `set_num_threads` and
`has_threads_enabled`.
