# NFSFT

Nonequispaced fast spherical Fourier transform. The module evaluates
expansions in spherical harmonics on the two-dimensional unit sphere
$\mathbb{S}^2$ at arbitrary nodes, and computes the adjoint transform. The
abbreviation NFSFT stands for "nonuniform fast spherical Fourier transform".

The [background page](nfsft-background.md) defines spherical coordinates,
Legendre polynomials, associated Legendre functions and spherical harmonics.
This page defines the transforms, the data layout of the plan and the
precomputation. It also explains how the fast algorithm works.

## Definition

By default the module works with the unnormalised spherical harmonics
$\tilde{Y}_k^n$. With the flag `NFSFT_NORMALIZED` it works with the
$\mathrm{L}^2$-normalised harmonics $Y_k^n$. In the formulas below $Y_k^n$
stands for the basis in use. The node
$\mathbf{x}(m) = (x_1(m),x_2(m))$ has the polar angle
$\vartheta = 2\pi x_2(m)$ and the azimuth $\varphi = 2\pi x_1(m)$, so
$Y_k^n(\mathbf{x}(m))$ means $Y_k^n\!\left(2\pi x_2(m),2\pi x_1(m)\right)$.

### NDSFT

The **nonuniform discrete spherical Fourier transform** (NDSFT) is defined as
follows.

**Input.** Coefficients $\hat f(k,n) \in \mathbb{C}$ for $k=0,\dots,N$ and
$n=-k,\dots,k$ with $N \in \mathbb{N}_0$. Arbitrary nodes
$\mathbf{x}(m) \in [-\tfrac{1}{2},\tfrac{1}{2}] \times [0,\tfrac{1}{2}]$ for
$m=0,\dots,M-1$ with $M \in \mathbb{N}$.

**Task.** Evaluate

$$
f(m) := f\!\left(\mathbf{x}(m)\right)
= \sum_{k=0}^{N} \sum_{n=-k}^{k} \hat f(k,n)\,
Y_k^n\!\left(\mathbf{x}(m)\right),
\qquad m=0,\dots,M-1.
$$

**Output.** Values $f(m) \in \mathbb{C}$ for $m=0,\dots,M-1$.

The functions `nfsft_trafo_direct` and `nfsft_trafo` compute this sum. The
first function evaluates it directly. The second function uses the fast
algorithm.

### Adjoint NDSFT

The **adjoint nonuniform discrete spherical Fourier transform** is defined as
follows.

**Input.** Values $f(m) \in \mathbb{C}$ for $m=0,\dots,M-1$ with
$M \in \mathbb{N}$. Arbitrary nodes
$\mathbf{x}(m) \in [-\tfrac{1}{2},\tfrac{1}{2}] \times [0,\tfrac{1}{2}]$ for
$m=0,\dots,M-1$. The bandwidth $N \in \mathbb{N}_0$.

**Task.** Evaluate

$$
\hat f(k,n) := \sum_{m=0}^{M-1} f(m)\,
\overline{Y_k^n\!\left(\mathbf{x}(m)\right)},
\qquad k=0,\dots,N,\; n=-k,\dots,k.
$$

**Output.** Coefficients $\hat f(k,n) \in \mathbb{C}$ for $k=0,\dots,N$ and
$n=-k,\dots,k$.

The functions `nfsft_adjoint_direct` and `nfsft_adjoint` compute this sum.
The first function evaluates it directly. The second function uses the fast
algorithm.

## Workflow

1. Call `nfsft_precompute(N, kappa, nfsft_flags, fpt_flags)` once for the
   largest bandwidth in use.
2. Create a plan with `nfsft_init`, `nfsft_init_advanced` or `nfsft_init_guru`.
3. Set the nodes in `plan.x`.
4. Call `nfsft_precompute_x(&plan)`.
5. Set `plan.f_hat` for a transform or `plan.f` for an adjoint transform.
6. Call `nfsft_trafo`, `nfsft_adjoint`, `nfsft_trafo_direct` or
   `nfsft_adjoint_direct`.
7. Call `nfsft_finalize` for each plan and `nfsft_forget` when no plan is left.

The names above are the double precision names. The prefixes `nfsftf_` and
`nfsftl_` select single and long double precision. See
[precision](../guide/precision.md).

## Plan and data layout

The `nfsft_plan` structure holds all data of the transforms. The members below
are public. The plan has further members for internal use, among them the
internal NFFT plan `plan_nfft`. The
[API page](../api/nfsft.md) lists all members.

| Member | Access | Meaning |
|--------|--------|---------|
| `N_total` | read | Number of entries of `f_hat`. For bandwidth $N$ it is $(2N+2)^2$. |
| `M_total` | read | Number of nodes $M$. |
| `f_hat` | read and write | Spherical Fourier coefficients in the layout below. |
| `f` | read and write | Function values. `f[m]` is $f(m)$ for $m=0,\dots,M-1$. |
| `N` | read | Bandwidth $N \in \mathbb{N}_0$. |
| `x` | read and write | Nodes. `x[2*m]` is $x_1(m)$ and `x[2*m+1]` is $x_2(m)$. |
| `mv_trafo`, `mv_adjoint` | read | Function pointers to `nfsft_trafo` and `nfsft_adjoint`. The [solver](solver.md) module uses them. |

### Layout of `f_hat`

`f_hat` is a flat array of $(2N+2)^2$ complex numbers. Read it as a row-major
matrix with $2N+2$ rows and $2N+2$ columns. The coefficient
$\hat f(k,n)$ with $0 \le k \le N$ and $-k \le n \le k$ has the row
$N-n+1$ and the column $N+k+1$. Its index is

$$
i = (2N+2)(N-n+1) + N + k + 1.
$$

The macro `NFSFT_INDEX(k,n,plan)` computes this index, so that
`f_hat[NFSFT_INDEX(k,n,&plan)]` is the component of $\hat f(k,n)$. The macro
`NFSFT_F_HAT_SIZE(N)` gives the array length $(2N+2)^2$.

Only the entries that belong to a coefficient $\hat f(k,n)$ carry data. The
other entries serve as work space of the fast algorithm. The layout follows
from the implementation.

!!! warning "Macro arguments"

    `NFSFT_INDEX` and `NFSFT_F_HAT_SIZE` do not put their arguments in
    parentheses. Pass a plain variable or write the parentheses yourself, for
    example `NFSFT_INDEX(k,(-n),&plan)`.

### Nodes

Each node is a pair $(x_1,x_2) \in [-\tfrac{1}{2},\tfrac{1}{2}) \times
[0,\tfrac{1}{2}]$. The value $x_1 = \varphi/2\pi$ is the scaled azimuth and
$x_2 = \vartheta/2\pi$ is the scaled polar angle. Call `nfsft_precompute_x`
after you change the nodes. The internal NFFT plan needs this step for its
node-dependent precomputation.

## Precomputation

The function `nfsft_precompute(N, kappa, nfsft_flags, fpt_flags)` fills a global
store of precomputed data. The code calls this store wisdom. It holds

- the coefficients $v_k^n$, $w_k^n$ of the three-term recurrence of the
  associated Legendre functions, in the form $\alpha_k^n$, $\beta_k^n$,
  $\gamma_k^n$ used by the [FPT](fpt.md), for the direct transforms, and
- the FPT data for all orders $n$, for the fast transforms.

Rules for the precomputation:

- The bandwidth $N_{\max}$ up to which the function precomputes is the next
  power of two with respect to the argument `N`. A plan needs
  $N \le N_{\max}$. If $N > N_{\max}$, the fast transforms write `NaN` to
  their result and the direct transforms read outside the stored data.
- The parameter `kappa` is the threshold $\kappa \in \mathbb{R}^{+}$ of the
  FPT. It sets the number of stabilisation steps of the discrete polynomial
  transform and so its accuracy. The examples use $\kappa = 1000$.
- The parameter `fpt_flags` goes to the [FPT](fpt.md) module.
- The store exists once per precision. The function returns at once if the
  store exists. Call `nfsft_forget` first to precompute for other parameters.
- `nfsft_forget` frees the store. Transforms need the store, so call it after
  the last transform.
- A plan with $N < 5$ always runs the direct algorithm, also in `nfsft_trafo`
  and `nfsft_adjoint`. The break-even bandwidth is 5.

The following flags for `nfsft_precompute` save memory.

| Flag | Effect |
|------|--------|
| `NFSFT_NO_DIRECT_ALGORITHM` | The function does not precompute the recurrence coefficients. `nfsft_trafo_direct` and `nfsft_adjoint_direct` write `NaN` to their result. A plan with $N < 5$ has no working transform. |
| `NFSFT_NO_FAST_ALGORITHM` | The function does not precompute the FPT data. `nfsft_trafo` and `nfsft_adjoint` write `NaN` to their result. |

## Creating a plan

| Function | Meaning |
|----------|---------|
| `nfsft_init(&plan, N, M)` | Plan with the flags `NFSFT_MALLOC_X`, `NFSFT_MALLOC_F` and `NFSFT_MALLOC_F_HAT`. |
| `nfsft_init_advanced(&plan, N, M, nfsft_flags)` | Plan with the given NFSFT flags. The NFFT uses the flags `PRE_PHI_HUT`, `PRE_PSI`, `FFTW_INIT` and `NFFT_OMP_BLOCKWISE_ADJOINT` and the cut-off 6. |
| `nfsft_init_guru(&plan, N, M, nfsft_flags, nfft_flags, nfft_cutoff)` | Plan with the given NFSFT flags, NFFT flags and NFFT cut-off. See [NFFT](nfft.md). |

The internal NFFT plan has the bandwidth $2N+2$ in both dimensions and the FFT
size $4N$.

## Flags

The flags for `nfsft_init_advanced` and `nfsft_init_guru` are bit flags. Combine
them with `|`.

### Basis and algorithms

| Flag | Effect |
|------|--------|
| `NFSFT_NORMALIZED` | By default the computation uses the unnormalised functions $\tilde{Y}_k^n(\vartheta,\varphi) = P_k^{\lvert n\rvert}(\cos\vartheta)\,\mathrm{e}^{\mathrm{i} n \varphi}$. With this flag it uses the $\mathrm{L}^2$-normalised functions $Y_k^n(\vartheta,\varphi) = \sqrt{\tfrac{2k+1}{4\pi}}\,P_k^{\lvert n\rvert}(\cos\vartheta)\,\mathrm{e}^{\mathrm{i} n \varphi}$. Each transform multiplies the coefficients by $\sqrt{(2k+1)/4\pi}$. |
| `NFSFT_USE_NDFT` | The fast transforms use the exact direct NDFT in place of the fast but approximate NFFT. |
| `NFSFT_USE_DPT` | The fast transforms use the direct discrete polynomial transform (DPT) in place of the FPT. |
| `NFSFT_EQUISPACED` | The plan uses an equispaced FFT in place of the NFFT. See [Equispaced nodes](#equispaced-nodes). |
| `NFSFT_NO_FAST_ALGORITHM` | The plan has no internal NFFT plan. The fast transforms write `NaN`. |
| `NFSFT_ZERO_F_HAT` | The adjoint transforms set all entries of `f_hat` that do not belong to a coefficient to zero. `nfsft_adjoint_direct` always does this. Without the flag, `nfsft_adjoint` leaves undefined values in these entries. |

### Memory

| Flag | Effect |
|------|--------|
| `NFSFT_MALLOC_X` | The init function allocates the node array `x`, of $2M$ real numbers, and `nfsft_finalize` frees it. Without the flag, `x` must point to an array of the right size before a transform, and you free it. |
| `NFSFT_MALLOC_F_HAT` | The same for the array `f_hat`, of $(2N+2)^2$ complex numbers. |
| `NFSFT_MALLOC_F` | The same for the array `f`, of $M$ complex numbers. |

### Input preservation

The transforms treat the input arrays as follows.

- `nfsft_trafo` and `nfsft_trafo_direct` do not change `x`. By default the fast
  transform overwrites `f_hat`. The direct transform overwrites `f_hat` only
  together with `NFSFT_NORMALIZED`.
- The adjoint transforms `nfsft_adjoint` and `nfsft_adjoint_direct` do not
  change `x` and `f`.

The flag `NFSFT_PRESERVE_F_HAT` makes the transforms work on an internal copy
of `f_hat`. It costs memory for one more coefficient array. Then `f_hat`
stays unchanged. The flags below are part of the interface. They have no
further effect in the current implementation.

| Flag | Meaning |
|------|---------|
| `NFSFT_PRESERVE_F_HAT` | `f_hat` stays unchanged in `nfsft_trafo_direct` and `nfsft_trafo`. |
| `NFSFT_PRESERVE_X` | `x` stays unchanged in all four transforms. This is always true. |
| `NFSFT_PRESERVE_F` | `f` stays unchanged in `nfsft_adjoint_direct` and `nfsft_adjoint`. This is always true. |
| `NFSFT_DESTROY_F_HAT` | The transforms may change `f_hat` in `nfsft_trafo_direct` and `nfsft_trafo`. This is the default. |
| `NFSFT_DESTROY_X` | The transforms may change `x`. |
| `NFSFT_DESTROY_F` | The adjoint transforms may change `f`. |

## How the fast algorithm works

The direct algorithm evaluates for each order $n$ the sum over $k$ with the
Clenshaw algorithm and the stored recurrence coefficients. It runs in long
double arithmetic for $N > 1024$.

The fast algorithm `nfsft_trafo` has these stages.

1. **Weights.** With `NFSFT_NORMALIZED` the algorithm multiplies
   $\hat f(k,n)$ by $\sqrt{(2k+1)/4\pi}$.
2. **FPT.** For each order $n$ the [FPT](fpt.md) turns the coefficients of
   the functions $P_k^{\lvert n\rvert}$ into coefficients of Chebyshev
   polynomials. The result is a function
   $f_n(\cos\vartheta) = \sum_{k=0}^{N} a_k^n\,(\sin\vartheta)^{n \bmod 2}\,
   T_k(\cos\vartheta)$. With `NFSFT_USE_DPT` the direct DPT does this step.
3. **Conversion.** The internal function `c2e` changes these coefficients in
   place into the coefficients $c_k^n$ of the representation by complex
   exponentials
   $f_n(\cos\vartheta) = \sum_{k=-N}^{N} c_k^n\,\mathrm{e}^{\mathrm{i} k \vartheta}$.
4. **NFFT.** A two-dimensional [NFFT](nfft.md) evaluates the trigonometric
   sum in $\varphi$ and $\vartheta$ with the coefficients $c_k^n$ at the
   nodes. With `NFSFT_USE_NDFT` the direct NDFT does this step.

The adjoint algorithm `nfsft_adjoint` runs the transposed stages in reverse
order: adjoint NFFT, transposed conversion, transposed FPT and the weights.

The `f_hat` array is also the coefficient array of the NFFT, of bandwidth
$2N+2$ in both dimensions. For this reason the layout has $2N+2$ rows and
columns. The row of $\hat f(k,n)$ is the NFFT frequency $-n$ and the column is
the NFFT frequency $k$, each shifted by $N+1$.

## Equispaced nodes

With `NFSFT_EQUISPACED` the transform evaluates on a fixed grid with an FFT
of size $2N+2$ in place of the NFFT. The plan creates no NFFT plan. The nodes
are

$$
\varphi_i = 2\pi \frac{i}{2N+2}, \qquad i=-N-1,\dots,N,
$$

$$
\vartheta_j = 2\pi \frac{j}{2N+2}, \qquad j=0,\dots,N+1.
$$

The number of nodes is fixed to $M = (2N+2)(N+2)$, whatever `M` is in the init
call. `plan.M_total` holds the value. The entry `f[i*(N+2)+j]` belongs to the
node with the angle $\varphi$ of the index $i-N-1$ and the angle $\vartheta$ of
the index $j$, for $i=0,\dots,2N+1$ and $j=0,\dots,N+1$. The value of the flag
is `1U << 17`.

## Example

The example `examples/nfsft/simple_test.c` uses the guru interface with
normalised harmonics and preserved `f_hat`. It computes a direct and a fast
transform and a direct and a fast adjoint transform.

```c
--8<-- "examples/nfsft/simple_test.c:32:115"
```

The example uses the bandwidth $N=4$. Because of $N < 5$, `nfsft_trafo` and
`nfsft_adjoint` call the direct algorithm there. Use $N \ge 5$ to run the fast
algorithm.

## API

[NFSFT API reference](../api/nfsft.md)
