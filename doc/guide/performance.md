# Performance

This page explains which settings of an [NFFT](../transforms/nfft.md) plan
change the run time and the memory of a transform. It is for readers who have a
working program and want it faster or smaller. The flags themselves are defined
on [Plans and flags](plans-and-flags.md). This page adds where the code uses
them and what each one costs. All line numbers refer to
`nfft/kernel/nfft/nfft.c` unless the text names another file.

## Where the time goes

A fast transform has three steps. `nfft_trafo` and `nfft_adjoint` time them
separately in the member `MEASURE_TIME_t` when the library is configured with
`--enable-measure-time` (`nfft/include/nfft3.h` line 139). The generic path
times the steps at lines 5683 to 5700. The paths for $d=1,2,3$ do the same,
for example at lines 2906 to 2950.

| Index | Step | Work depends on |
|-------|------|-----------------|
| 0 | Deconvolution $\mathbf{D}$ | The number of coefficients $N_0\cdots N_{d-1}$ and the flag `PRE_PHI_HUT`. |
| 1 | FFT of length $n_0\cdots n_{d-1}$ | The oversampling factor $\sigma$ and the FFTW planning flags. |
| 2 | Convolution $\mathbf{B}$ | The number of nodes $M$, the cut-off $m$, the dimension $d$ and the precomputation flag. |

The convolution visits $(2m+2)^d$ grid points for each node (line 1025). The choice of $m$ and
$\sigma$ trades accuracy against this work. See [Accuracy](accuracy.md) and
[Windows](windows.md) for that choice.

## Precomputation flags

The convolution needs, for each node and each dimension, $2m+2$ values of the
window $\varphi$. The precomputation flags decide whether the plan computes
these values in each transform or stores them once. `nfft_precompute_one_psi`
fills the stored values (lines 5939 to 5949). Call it again after every change
of `x`.

In the table, `R` is one real number of the plan precision and `INT` is one
index of type `NFFT_INT`. Memory and work are per plan.

| Flag | Memory that the flag allocates | Work per node and transform |
|------|--------------------------------|-----------------------------|
| no flag | none | Computes $d$ runs of $2m+2$ window values with `PHI_RUN` (lines 1130 to 1148). |
| `PRE_LIN_PSI` | $(K+1)\,d$ `R` (line 5987) | Saves the window evaluations. Computes $2m+2$ linear interpolations per dimension from a table that does not depend on the nodes (lines 1101 to 1128). |
| `PRE_FG_PSI` | $2\,d\,M$ `R` (line 5991) | Saves one window evaluation and one exponential per dimension compared with `FG_PSI` (lines 1084 to 1091). Generates the run of $2m+2$ values by a recurrence from the two stored values (lines 1057 to 1062). Gaussian window only. |
| `PRE_PSI` | $(2m+2)\,d\,M$ `R` (line 5994) | Saves all window evaluations. Reads $(2m+2)\,d$ stored values (line 848). Still forms the $(2m+2)^d$ products and grid indices (lines 1027 to 1040). |
| `PRE_FULL_PSI` | $(2m+2)^d M$ `R` and $(2m+2)^d M + M$ `INT` (lines 5996 to 6004) | Saves all window evaluations, products and index computations. Reads one stored value and one stored index per grid point (lines 1004 to 1020, macros at lines 824 to 832). |
| `PRE_ONE_PSI` | Not a flag of its own. It is the mask of the four flags above (`nfft/include/nfft3.h` line 208). | Tests if the plan needs `nfft_precompute_one_psi`. |

Each of the four flags allocates the same member `psi` (lines 5981 to 6004).
Set at most one of them. [Plans and flags](plans-and-flags.md#precomputation)
gives the order in which the transform tests them.

`nfft_precompute_psi` evaluates the same window runs that a transform without
a flag evaluates (lines 5823 to 5845). The stored values therefore pay back only
when the plan runs more than one transform with the same nodes. The report by Kunis and
Potts on time and memory requirements, listed on
[Publications](../reference/publications.md#nfft-and-its-generalisations),
compares the flags with measured times. To compare them on your machine, run
`examples/nfft/flags.c` in a library configured with `--enable-measure-time`
(`nfft/examples/nfft/flags.c` lines 283 to 290).

!!! warning "Memory of PRE_FULL_PSI and PRE_LIN_PSI"

    `PRE_FULL_PSI` grows with $(2m+2)^d$. The table of `PRE_LIN_PSI` has $K+1$
    entries per dimension, and the default $K$ can be very large.
    [Plans and flags](plans-and-flags.md#choosing-flags) gives values for
    typical parameters.

## Node sorting

`NFFT_SORT_NODES` makes the convolution visit the nodes in the order of their
position on the oversampled grid. The aim is better cache use in the
multiplication with $\mathbf{B}$ (comment at lines 111 to 118).

- The sort key of a node is the linear grid index of the first point of its
  stencil (lines 82 to 94). A radix sort orders the keys (lines 100 to 103).
- The plan allocates $2M$ `INT` for the keys and the order (lines 6040 to
  6041). The array `x` does not change.
- The function `sort` runs the sort when the flag is set (lines 119 to 123).
  The precompute functions call it, for example at line 5827, and each
  convolution calls it again before the node loop, for example at line 1029.
- The node loops read the order through `index_x[2*k+1]`, for example at
  line 1033.

`nfft_init` sets the flag for $d>1$ (lines 6070 to 6077). For $d=1$ it does not
set it (lines 6080 to 6082). Sorting does not change the result beyond the
order of the floating point additions in the adjoint.

## Blockwise adjoint

`NFFT_OMP_BLOCKWISE_ADJOINT` affects only the OpenMP library. It selects how
threads add node contributions into the shared grid in the adjoint
convolution.

- With the flag, each thread owns a block of the grid and writes only there.
  The code is in the `#ifdef _OPENMP` branches at line 1599 for
  `PRE_FULL_PSI` and at lines 1922, 2650 and 3604 for the general, 1d and 2d
  paths.
- Without the flag, threads loop over the nodes and use one atomic addition
  for the real part and one for the imaginary part (lines 1700 to 1704 for
  `PRE_FULL_PSI`).
- The flag implies `NFFT_SORT_NODES`. `init_help` sets the sort flag when the
  blockwise flag is set (lines 5956 to 5957). The threads find their nodes by
  a binary search in the sorted index (line 1614).

`nfft_init` sets the flag in the OpenMP library for $d>1$ (lines 6071 to 6074).
[OpenMP](openmp.md#the-adjoint-transform) describes both strategies and the
thread count.

## FFTW planning

`nfft_init` sets `fftw_flags` to `FFTW_ESTIMATE | FFTW_DESTROY_INPUT`
(line 6084). `nfft_init_1d`, `nfft_init_2d` and `nfft_init_3d` call
`nfft_init` and get the same value (lines 6142 to 6167). `nfft_init_guru` and
`nfft_init_lin` pass your `fftw_flags` unchanged (lines 6110 and 6136).
`init_help` gives the value to `fftw_plan_dft` for both FFTW plans (lines 6030
to 6031).

`FFTW_ESTIMATE` plans fast but does not measure. A flag such as
`FFTW_MEASURE` plans slower and can give a faster FFT. This pays when the plan
runs many transforms. `examples/nfft/flags.c` uses `FFTW_MEASURE`
(`nfft/examples/nfft/flags.c` line 100). See the FFTW manual on
[planner flags](https://www.fftw.org/fftw3_doc/Planner-Flags.html).

`FFT_OUT_OF_PLACE` costs a second grid of $n_0\cdots n_{d-1}$ complex numbers
(lines 6015 to 6018). `nfft_init` sets it only for $d=1$ (line 6082).

## Threads

The OpenMP library runs the deconvolution, the convolution and the
precomputation in parallel. The FFT runs in parallel only with a threaded
FFTW. [OpenMP](openmp.md) gives the build, the thread functions and the list
of parallel steps.

## Benchmarks in the source tree

`nfft/benchmarks/bench_nfft_fast.cpp` measures `nfft_precompute_psi`,
`nfft_trafo` and `nfft_adjoint` with `PRE_PSI` and without a precomputation
flag (lines 19 to 26). It uses `FFTW_ESTIMATE` (line 182). This site does not
publish its numbers.

## API

[NFFT API reference](../api/nfft.md)
