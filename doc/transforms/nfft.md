# NFFT

Nonequispaced fast Fourier transform. The core module: every other module in the
library either generalises it or is built on it.

## Definition

Let the $d$-dimensional torus be

$$
\mathbb{T}^d := \left\{ \mathbf{x}=\left(x_t\right)_{t=0,\dots,d-1}
\in\mathbb{R}^{d} : \; -\frac{1}{2} \le x_t < \frac{1}{2},\;
t=0,\dots,d-1 \right\}.
$$

It is the domain the nonequispaced nodes are taken from. The sampling set is
${\cal X} := \{\mathbf{x}_j \in \mathbb{T}^d : j=0,\dots,M-1\}$. The
frequencies are collected in the multi-index set

$$
I_{\mathbf{N}} := \left\{ \mathbf{k}=\left(k_t\right)_{t=0,\dots,d-1}
\in\mathbb{Z}^d : -\frac{N_t}{2} \le k_t < \frac{N_t}{2},\;
t=0,\dots,d-1 \right\},
$$

where $\mathbf{N}=\left(N_t\right)_{t=0,\dots,d-1}$ is the multibandlimit, each
$N_t$ even.

The **nonequispaced discrete Fourier transform** (NDFT) is

$$
f_j = \sum_{\mathbf{k}\in I_{\mathbf{N}}} \hat f_{\mathbf{k}}\,
\mathrm{e}^{-2\pi\mathrm{i}\,\mathbf{k}\mathbf{x}_j},
\qquad j=0,\dots,M-1,
$$

and the adjoint NDFT is

$$
\hat f_{\mathbf{k}} = \sum_{j=0}^{M-1} f_j\,
\mathrm{e}^{+2\pi\mathrm{i}\,\mathbf{k}\mathbf{x}_j},
\qquad \mathbf{k}\in I_{\mathbf{N}}.
$$

The adjoint is **not** the inverse. Inverting a transform is the job of the
[solver](solver.md) module.

## Cost

`nfft_trafo_direct` and `nfft_adjoint_direct` evaluate the two sums as written,
in ${\cal O}(|I_{\mathbf{N}}|M)$ operations. `nfft_trafo` and `nfft_adjoint`
approximate them to a prescribed accuracy in only
${\cal O}(|I_{\mathbf{N}}|\log|I_{\mathbf{N}}| + M)$ operations.

## The fast algorithm

The fast transform factors the transform matrix into three cheap factors,
$\mathbf{A} \approx \mathbf{B}\,\mathbf{F}\,\mathbf{D}$.

| Factor | Name | Work |
|--------|------|------|
| $\mathbf{D}$ | Diagonal matrix. It divides each coefficient by the Fourier transform of the window function. | ${\cal O}(\lvert I_{\mathbf{N}}\rvert)$ |
| $\mathbf{F}$ | FFT of the oversampled length $n_0\cdots n_{d-1}$, done by FFTW. | ${\cal O}(n\log n)$ |
| $\mathbf{B}$ | Sparse matrix. It sums $2m+2$ window values per dimension and node. | ${\cal O}(M)$ |

The adjoint transform applies the transposed factors in the opposite order. Two
parameters set the accuracy: the cut-off $m$ and the oversampling factor
$\sigma_t = n_t/N_t$. The [guide](../guide/index.md) explains both. The flags
below control which of the entries of $\mathbf{D}$ and $\mathbf{B}$ the plan
stores and which it recomputes.

## Using a plan

The life cycle of a plan has six steps.

1. Declare the plan: `nfft_plan p;`
2. Initialise it. `nfft_init_1d`, `nfft_init_2d` and `nfft_init_3d` are wrappers
   for $d=1,2,3$, `nfft_init` takes any $d$, and `nfft_init_guru` sets the
   oversampled lengths, the cut-off and all flags. `nfft_init_lin` also sets the
   size of the lookup table for `PRE_LIN_PSI`.
3. Write the nodes into `p.x`. The plan stores node $j$ in
   `p.x[j*d]`, ..., `p.x[j*d+d-1]`. Each component must lie in $[-\tfrac{1}{2},\tfrac{1}{2})$.
4. If any of the flags in `PRE_ONE_PSI` is set, call `nfft_precompute_one_psi`.
   The call must follow step 3, because the precomputed values depend on the
   nodes. The routines `nfft_precompute_psi`, `nfft_precompute_full_psi` and
   `nfft_precompute_lin_psi` are superseded by `nfft_precompute_one_psi`.
5. Write the input into `p.f_hat` for the forward transform or into `p.f` for the
   adjoint. Call `nfft_check` to test the plan for frequent errors. It returns a
   message or a null pointer.
6. Call `nfft_trafo` or `nfft_adjoint`, read the result from `p.f` or `p.f_hat`,
   then call `nfft_finalize`.

The plan stores the coefficients in `f_hat` with the last dimension running
fastest. The entry of the frequency $\mathbf{k}$ has the index
$\sum_t (k_t + N_t/2)\prod_{s>t} N_s$.

For $d=1,2,3$, the routines `nfft_trafo_1d`, `nfft_trafo_2d`, `nfft_trafo_3d`
and `nfft_adjoint_1d`, `nfft_adjoint_2d`, `nfft_adjoint_3d` run the transform
with code specialised for that dimension.

## Plan parameters

`nfft_plan` carries the dimension in `d`, the multibandlimit in `N`, the
oversampled FFT length in `n`, the oversampling factor in `sigma`, the cut-off in
`m`, the window shape parameter in `b`, the flags in `flags` and `fftw_flags`,
the nodes in `x`, the coefficients in `f_hat` and the samples in `f`. The
[API page](../api/nfft.md) lists every member.

`nfft_init` and its wrappers choose the following defaults.

- $n_t = 2\cdot 2^{\lceil \log_2 N_t \rceil}$, that is $2 \le \sigma_t < 4$.
- $m$ is the default cut-off of the window function the library was compiled
  with. Query it with `nfft_get_default_window_cut_off`. The value depends on the
  window and on the precision.
- `fftw_flags` is `FFTW_ESTIMATE | FFTW_DESTROY_INPUT`.
- `flags` is `PRE_PHI_HUT | PRE_PSI | MALLOC_X | MALLOC_F_HAT | MALLOC_F | FFTW_INIT`.
  For $d=1$ the plan also sets `FFT_OUT_OF_PLACE`. For $d>1$ the plan sets
  `NFFT_SORT_NODES` instead, and `NFFT_OMP_BLOCKWISE_ADJOINT` in an OpenMP build.

`nfft_init_guru` uses exactly the values that the caller passes.

## Flags

The flags are bits of the member `flags`. Combine them with the bitwise or
operator.

### Precomputation for D

| Flag | Meaning |
|------|---------|
| `PRE_PHI_HUT` | The deconvolution step, the multiplication with $\mathbf{D}$, uses precomputed values of the Fourier transformed window function. |

### Precomputation for B

The convolution step is the multiplication with the sparse matrix $\mathbf{B}$.
The flags below select how it obtains the window values. Use at most one of them.

| Flag | Meaning |
|------|---------|
| none of them | The plan evaluates the window function exactly at each use. |
| `PRE_PSI` | The plan stores $(2m+2)dM$ precomputed window values. |
| `PRE_FULL_PSI` | The plan stores $(2m+2)^dM$ precomputed window values and, in addition, the indices of the source and target vectors. It needs much memory. |
| `PRE_LIN_PSI` | The plan interpolates linearly in a lookup table of equispaced window samples instead of using exact values. The table has $(K+1)d$ entries. `nfft_init_lin` sets $K$, otherwise the plan chooses $K$ from $m$. |
| `FG_PSI` | The plan uses properties of the Gaussian window to trade multiplications for calls to the exponential function. Use it with the Gaussian window only. |
| `PRE_FG_PSI` | As `FG_PSI`, and the plan stores the remaining $2dM$ values of the exponential function. Use it with the Gaussian window only. |
| `PRE_ONE_PSI` | Not a choice, but the bitwise union of `PRE_LIN_PSI`, `PRE_FG_PSI`, `PRE_PSI` and `PRE_FULL_PSI`. If `flags & PRE_ONE_PSI` is nonzero, the application must call `nfft_precompute_one_psi` after it sets the nodes. |

### Allocation

| Flag | Meaning |
|------|---------|
| `MALLOC_X` | The plan allocates the node vector `x` in `nfft_init_guru` and frees it in `nfft_finalize`. |
| `MALLOC_F_HAT` | The plan allocates the coefficient vector `f_hat` and frees it in `nfft_finalize`. |
| `MALLOC_F` | The plan allocates the sample vector `f` and frees it in `nfft_finalize`. |

Without one of these flags, the application sets the pointer `x`, `f_hat` or `f`
before the first transform and owns the memory.

### FFTW

| Flag | Meaning |
|------|---------|
| `FFTW_INIT` | The plan allocates the oversampled vectors and creates the FFTW plans. `nfft_finalize` destroys them. Without it, the plan has no FFTW plans and the application must supply them. |
| `FFT_OUT_OF_PLACE` | FFTW uses disjoint input and output vectors. |

### Node order and threads

| Flag | Meaning |
|------|---------|
| `NFFT_SORT_NODES` | The plan sorts the node indices to improve the cache use in the multiplication with $\mathbf{B}$. It keeps the sorted indices in `index_x` and does not change `x`. |
| `NFFT_OMP_BLOCKWISE_ADJOINT` | In an OpenMP build, each thread updates its own block of the oversampled grid in the adjoint transform, so that no atomic operations are needed. This flag implies `NFFT_SORT_NODES`. |

## Examples

The simple example from `examples/nfft/simple_test.c`:

```c
--8<-- "examples/nfft/simple_test.c:24:73"
```

The directory `examples/nfft` holds more programs.

| File | Purpose |
|------|---------|
| `simple_test.c` | Introductory example. |
| `flags.c` | Compares the precomputation strategies. Run it with the window function you want to test, because the window is fixed at compile time. |
| `flags.m` | Visualises the data files that `flags` writes. It also calls `taylor_nfft`. |
| `ndft_fast.c` | Compares the direct NDFT, a Horner-like NDFT and an NDFT with a fully precomputed matrix. |
| `ndft_fast.m` | Visualises the result of `ndft_fast`. |
| `taylor_nfft.c` | Compares the NFFT with a version based on a Taylor expansion. |
| `taylor_nfft.m` | Visualises the result of `taylor_nfft`. |
| `nfft_times.c` | Compares the times of NFFTs and FFTs in one, two and three dimensions and writes a LaTeX table. |
| `nfft_benchomp.c` | Runs benchmarks of the OpenMP code and writes PGFPlots data. It uses `nfft_benchomp_createdataset.c` and `nfft_benchomp_detail.c`. |

## References

Kunis, S. and Potts, D. Time and memory requirements of the nonequispaced FFT.
Preprint 2006-1, Chemnitz University of Technology, Faculty of Mathematics.

## API

[NFFT API reference](../api/nfft.md)
