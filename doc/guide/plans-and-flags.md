# Plans and flags

Every transform in NFFT3 runs on a **plan**. A plan holds the problem size, the
node and coefficient arrays, the precomputed data and the FFTW plans. This page
describes the life of an [NFFT](../transforms/nfft.md) plan, the flags that
select what the plan precomputes and allocates, and what each flag costs in
memory. The other modules follow the same pattern. The
[API page](../api/nfft.md) lists every function and member.

## Life of a plan

A plan goes through six steps.

| Step | Call | What happens |
|------|------|--------------|
| 1 | `nfft_init`, `nfft_init_1d`, `nfft_init_2d`, `nfft_init_3d`, `nfft_init_guru` or `nfft_init_lin` | The plan allocates arrays as the flags say, computes the window parameters, fills the `PRE_PHI_HUT` table and creates the FFTW plans. |
| 2 | Write `x` | The nodes must lie in $[-\tfrac12,\tfrac12)^d$. |
| 3 | `nfft_precompute_one_psi` | Fills the node-dependent tables. Needed when `flags & PRE_ONE_PSI` is not zero. |
| 4 | `nfft_check` | Optional. Returns a message for a common parameter error, or a null pointer. |
| 5 | Write `f_hat` or `f`, then `nfft_trafo` or `nfft_adjoint` | The forward transform reads `f_hat` and writes `f`. The adjoint reads `f` and writes `f_hat`. |
| 6 | `nfft_finalize` | Frees what the flags allocated. |

Step 3 depends on the nodes. Call it again whenever `x` changes. Only the
`PRE_LIN_PSI` table does not depend on the nodes, so it can be filled before `x`
is set.

`nfft_trafo` and `nfft_adjoint` select `nfft_trafo_1d`, `nfft_trafo_2d` and
`nfft_trafo_3d`, or the adjoint versions, by the dimension `d`. Higher
dimensions use a generic path. You can call the specialised functions directly.

!!! note "Direct fallback"

    If `N[t] <= m` or `n[t] <= 2*m+2` in any dimension, `nfft_trafo` and
    `nfft_adjoint` call the direct transform `nfft_trafo_direct` or
    `nfft_adjoint_direct`. The window then has no room on the oversampled grid.

`nfft_trafo_direct` and `nfft_adjoint_direct` use only `x`, `f_hat` and `f`.
They need neither precomputation nor FFTW plans.

### Example

The example creates a two-dimensional plan with `nfft_init_guru`, fills the
tables, checks the plan and transforms in both directions. From
`examples/nfft/simple_test.c`:

```c
--8<-- "examples/nfft/simple_test.c:84:116"
```

## Creating a plan

| Function | Parameters | Result |
|----------|------------|--------|
| `nfft_init_1d`, `nfft_init_2d`, `nfft_init_3d` | Bandwidths `N1`, `N2`, `N3`, node count `M` | Calls `nfft_init` with `d = 1, 2, 3`. |
| `nfft_init` | Dimension `d`, bandwidths `N`, node count `M` | Default parameters, see below. |
| `nfft_init_guru` | `d`, `N`, `M`, oversampled lengths `n`, cut-off `m`, `flags`, `fftw_flags` | You choose every parameter. |
| `nfft_init_lin` | As `nfft_init_guru`, plus the table size `K` | For `PRE_LIN_PSI` with your own `K`. |

`nfft_init` sets these values.

| Member | Default |
|--------|---------|
| `n[t]` | $2\cdot 2^{\lceil\log_2 N_t\rceil}$. This gives an oversampling factor $2\le\sigma_t<4$. |
| `m` | The default cut-off of the window, see [Windows](windows.md). |
| `fftw_flags` | `FFTW_ESTIMATE` and `FFTW_DESTROY_INPUT` |
| `flags` | The flags of the list below. |

The default `flags` are `PRE_PHI_HUT`, `PRE_PSI`, `MALLOC_X`, `MALLOC_F_HAT`,
`MALLOC_F` and `FFTW_INIT`. In addition:

- For $d=1$, `FFT_OUT_OF_PLACE`.
- For $d>1$, `NFFT_SORT_NODES`. The OpenMP library also sets
  `NFFT_OMP_BLOCKWISE_ADJOINT`.

The plan needs these conditions. `nfft_check` tests them.

- Every $N_t$ is even.
- Every oversampling factor $\sigma_t=n_t/N_t$ is greater than 1.
- Every node coordinate lies in $[-\tfrac12,\tfrac12)$.
- `f`, `x` and `f_hat` are not null.

### Data layout

The plan stores the nodes node by node: `x[j*d + t]` is coordinate $t$ of node
$j$. The coefficient $\hat f_{\mathbf k}$ with $k_t\in\{-N_t/2,\dots,N_t/2-1\}$
is stored at the row-major position of $(k_0+\tfrac{N_0}{2},\dots,k_{d-1}+\tfrac{N_{d-1}}{2})$.
For $d=3$ this is

$$
\texttt{f\_hat}\big[\big((k_0+\tfrac{N_0}{2})N_1+(k_1+\tfrac{N_1}{2})\big)N_2
+(k_2+\tfrac{N_2}{2})\big].
$$

The last dimension runs fastest.

## Flags

`flags` is a bit mask. The flags fall into four groups. `R` in the memory column
is one real number of the plan precision. A complex number counts as two `R`.
`INT` is one index of type `NFFT_INT`.

### Precomputation

The forward transform multiplies by the sparse matrix $\mathbf{B}$ built from
the window $\varphi$. Each node touches $2m+2$ grid points per dimension. The
`PRE_*` flags decide how the library obtains the window values. The
`PRE_ONE_PSI` mask collects `PRE_LIN_PSI`, `PRE_FG_PSI`, `PRE_PSI` and
`PRE_FULL_PSI`.

| Flag | Meaning | Extra memory |
|------|---------|--------------|
| `PRE_PHI_HUT` | The deconvolution step uses a table of the Fourier transformed window. The plan fills the table at init. | $N_0+\dots+N_{d-1}$ `R` |
| `PRE_PSI` | The convolution step reads $(2m+2)dM$ stored window values, one run of $2m+2$ values per node and dimension. | $(2m+2)\,d\,M$ `R` |
| `PRE_FULL_PSI` | The convolution step reads $(2m+2)^dM$ stored products of window values. The plan also stores the source and target indices. | $(2m+2)^d M$ `R`, plus $(2m+2)^d M + M$ `INT` |
| `PRE_LIN_PSI` | The convolution step interpolates linearly in a table of $K+1$ equispaced window samples per dimension. The table does not depend on the nodes. | $(K+1)\,d$ `R` |
| `PRE_FG_PSI` | Gaussian window only. The plan stores the $2dM$ values that the fast Gaussian recurrence needs. | $2\,d\,M$ `R` |
| `FG_PSI` | Gaussian window only. The convolution step evaluates the run with a recurrence and $2dM$ calls of the exponential function. It stores nothing. | none |

Without any `PRE_*` flag the convolution step computes every window value in each
transform call. It needs no extra memory and no call of
`nfft_precompute_one_psi`.

Set at most one of `PRE_LIN_PSI`, `PRE_FG_PSI`, `PRE_PSI` and `PRE_FULL_PSI`.
Each of them allocates the same member `psi`. If several are set, the transform
uses the first of these in the order `PRE_FULL_PSI`, `PRE_PSI`, `PRE_FG_PSI`,
`FG_PSI`, `PRE_LIN_PSI`. `PRE_FG_PSI` and `FG_PSI` can be set together, as the
tests do.

!!! warning "The FG flags need the Gaussian window"

    The recurrence behind `FG_PSI` and `PRE_FG_PSI` uses the shape parameter of
    the Gaussian. Use these two flags only in a library built with
    `--with-window=gaussian`. The tests and the example `examples/nfft/flags.c`
    use them only there.

!!! note "The table size K for PRE_LIN_PSI"

    `nfft_init_guru` sets $K = 2^{e(m)}\,(m+2)$. The exponent $e(m)$ comes from
    a table in `kernel/util/window.c`. It is specific to the window and stops
    growing at the last entry of the table. For the Kaiser-Bessel window in
    double precision with $m=8$, $e=24$ and $K=167\,772\,160$. The table then
    holds $(K+1)\,d$ values, about 1.3 GB per dimension in double precision.
    `nfft_init_lin` sets $K$ directly. The test suite does not exercise
    `PRE_LIN_PSI` at present.

### Allocation

| Flag | Meaning | Memory |
|------|---------|--------|
| `MALLOC_X` | The plan allocates and frees the node array `x`. | $d\,M$ `R` |
| `MALLOC_F_HAT` | The plan allocates and frees the coefficient array `f_hat`. | $N_{\text{total}}$ complex |
| `MALLOC_F` | The plan allocates and frees the sample array `f`. | $M$ complex |

If a flag is not set, the pointer is yours. Assign a valid array before the
first transform. The plan never frees it. This lets several plans share one
array. `examples/nfft/flags.c` does this.

The plan allocates with `nfft_malloc`, which calls `fftw_malloc` unless you set
`nfft_malloc_hook`. It frees by its `flags`. Do not change
`flags` between init and `nfft_finalize`.

### FFTW

| Flag | Meaning | Memory |
|------|---------|--------|
| `FFTW_INIT` | The plan allocates the FFT buffer `g1` and creates the forward and backward FFTW plans, `my_fftw_plan1` and `my_fftw_plan2`. Without it the plan has no buffers and no FFTW plans, and the fast transforms cannot run unless you set `g1`, `g2`, `my_fftw_plan1` and `my_fftw_plan2` yourself. | $n_{\text{total}}$ complex |
| `FFT_OUT_OF_PLACE` | Needs `FFTW_INIT`. The FFT uses a second buffer `g2` for its output. Without the flag the FFT works in place and `g2` is the same array as `g1`. | $n_{\text{total}}$ complex more |

The argument `fftw_flags` goes to the FFTW planner unchanged. The default is
`FFTW_ESTIMATE | FFTW_DESTROY_INPUT`. `FFTW_MEASURE` makes planning slower and
can give a faster FFT. See the FFTW manual on
[planner flags](https://www.fftw.org/fftw3_doc/Planner-Flags.html). Here
$n_{\text{total}}=n_0\cdots n_{d-1}$.

### Ordering and threads

| Flag | Meaning | Memory |
|------|---------|--------|
| `NFFT_SORT_NODES` | The plan sorts the nodes by their position on the oversampled grid and processes them in that order. The nodes in `x` stay where they are. The plan computes the order in `nfft_precompute_one_psi`. Some transform paths compute it again. | $2M$ `INT` |
| `NFFT_OMP_BLOCKWISE_ADJOINT` | The OpenMP adjoint transform gives each thread its own block of the grid instead of using atomic additions. The flag implies `NFFT_SORT_NODES`. See [OpenMP](openmp.md). | as `NFFT_SORT_NODES` |

Sorting changes only the order in which the plan visits the nodes.

## Choosing flags

- **Default.** `nfft_init` is a good start. It precomputes the window values
  once and reuses them in every call.
- **One transform per node set.** The plan fills the table once and reads it
  once. If you do not need the table again, leave out `PRE_PSI`. The plan then
  needs no extra memory for it.
- **Many transforms with the same nodes.** Keep `PRE_PSI`. Solvers that apply
  the transform many times fall into this class.
- **High dimension.** The stencil holds $(2m+2)^d$ points. `PRE_FULL_PSI` grows
  with this number. For $d=2$, $M=10^6$ and $m=8$, `PRE_PSI` stores
  $3.6\cdot10^7$ reals, 288 MB in double precision. `PRE_FULL_PSI` stores
  $3.24\cdot10^8$ reals and as many indices, about 5.2 GB.
- **Gaussian window.** The FG flags remove most calls of the exponential
  function.

The report by Kunis and Potts, *Time and memory requirements of the
nonequispaced FFT*, Preprint 2006-1, Chemnitz University of Technology, Faculty
of Mathematics, compares the precomputation strategies. The program
`examples/nfft/flags.c` compares them on one data set. It prints the time of
each step for each strategy when the library is configured with
`--enable-measure-time`.

## API

[NFFT API reference](../api/nfft.md)
