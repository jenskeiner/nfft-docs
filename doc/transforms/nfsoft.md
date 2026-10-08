# NFSOFT

Nonequispaced fast $\mathrm{SO}(3)$ Fourier transform. The module evaluates
expansions in Wigner-D functions on the rotation group $\mathrm{SO}(3)$ at
arbitrary rotations, and computes the adjoint transform. The abbreviation
NFSOFT stands for "nonuniform fast SO(3) Fourier transform".

The module builds on the [NFSFT](nfsft.md). Read the
[NFSFT background](nfsft-background.md) for the spherical harmonics and the
associated Legendre functions.

## Basis

A rotation is given by its three Euler angles $(\alpha,\beta,\gamma)$ with
$\alpha,\gamma \in [-\pi,\pi)$ and $\beta \in [0,\pi]$. The Wigner-D functions
are

$$
D_{mn}^l(\alpha,\beta,\gamma) = d^{mn}_{l}(\cos\beta)\,
\mathrm{e}^{-\mathrm{i} m \alpha}\,\mathrm{e}^{-\mathrm{i} n \gamma},
\qquad l \in \mathbb{N}_0,\; m,n=-l,\dots,l.
$$

Here $d^{mn}_{l}(\cos\beta)$ is the Wigner small-d function
$d^{l}_{mn}(\beta) = \langle l,m|\,\mathrm{e}^{-\mathrm{i}\beta J_y}\,|l,n\rangle$.
Like the associated Legendre functions of the [NFSFT](nfsft.md), these
functions satisfy a three-term recurrence in $l$. The [FPT](fpt.md) module
turns this recurrence into a fast algorithm.

The functions $D_{mn}^l$ are orthogonal in $\mathrm{L}^2(\mathrm{SO}(3))$ with
the inner product

$$
\left< f,g \right> = \int_{-\pi}^{\pi} \int_{0}^{\pi} \int_{-\pi}^{\pi}
f(\alpha,\beta,\gamma)\,\overline{g(\alpha,\beta,\gamma)}\,\sin\beta\,
\mathrm{d}\gamma\,\mathrm{d}\beta\,\mathrm{d}\alpha.
$$

By default the module computes with these functions. With the flag
`NFSOFT_NORMALIZED` it uses the $\mathrm{L}^2$-normalised functions

$$
\tilde D_{mn}^l(\alpha,\beta,\gamma) = \sqrt{\frac{2l+1}{8\pi^2}}\,
d^{mn}_{l}(\cos\beta)\,
\mathrm{e}^{-\mathrm{i} m \alpha}\,\mathrm{e}^{-\mathrm{i} n \gamma}.
$$

In the formulas below $D_{mn}^l$ stands for the basis in use.

## Definition

Given the bandwidth $B \in \mathbb{N}_0$, coefficients
$\hat f^{mn}_l \in \mathbb{C}$ for $l=0,\dots,B$ and $m,n=-l,\dots,l$, and
arbitrary rotations $g_j = (\alpha_j,\beta_j,\gamma_j)$ for $j=0,\dots,M-1$,
the transform evaluates

$$
f(g_j) = \sum_{l=0}^{B} \sum_{m=-l}^{l} \sum_{n=-l}^{l} \hat f^{mn}_l\,
D_{mn}^l\!\left(\alpha_j,\beta_j,\gamma_j\right),
\qquad j=0,\dots,M-1,
$$

and the adjoint transform evaluates

$$
\hat f^{mn}_l = \sum_{j=0}^{M-1} f(g_j)\,
\overline{D_{mn}^l\!\left(\alpha_j,\beta_j,\gamma_j\right)},
\qquad l=0,\dots,B,\; m,n=-l,\dots,l.
$$

The functions `nfsoft_trafo` and `nfsoft_adjoint` compute these sums with the
fast algorithm. With the flags `NFSOFT_USE_NDFT` and `NFSOFT_USE_DPT` the same
functions compute the exact direct transform, the NDSOFT. It has no separate
function.

## Workflow

1. Create a plan with `nfsoft_init`, `nfsoft_init_advanced`, `nfsoft_init_guru`
   or `nfsoft_init_guru_advanced`. The init function does the FPT precomputation.
2. Set the nodes in `plan.x`.
3. Call `nfsoft_precompute(&plan)`.
4. Set `plan.f_hat` for a transform or `plan.f` for an adjoint transform.
5. Call `nfsoft_trafo` or `nfsoft_adjoint`.
6. Call `nfsoft_finalize`.

Call `nfsoft_precompute` after you set the nodes and before the first
transform. It copies the nodes into the internal NFFT plan and does the
node-dependent precomputation. The names above are the double precision names.
The prefixes `nfsoftf_` and `nfsoftl_` select single and long double precision.
See [precision](../guide/precision.md).

## Plan and data layout

The plan has these public members. The [API page](../api/nfsoft.md) lists all
members. The plan has further members for internal use, among them the internal
NFFT plan `p_nfft` and the FPT sets `internal_fpt_set`.

| Member | Meaning |
|--------|---------|
| `N_total` | The bandwidth $B$. In this module the member does not hold the number of coefficients. |
| `M_total` | Number of nodes $M$. |
| `f_hat` | The coefficients $\hat f^{mn}_l$ in the layout below. |
| `f` | Function values. `f[j]` is $f(g_j)$ for $j=0,\dots,M-1$. |
| `x` | Nodes. Three angles in radians for each rotation. |
| `mv_trafo`, `mv_adjoint` | Function pointers to `nfsoft_trafo` and `nfsoft_adjoint`. |

### Nodes

The array `x` has $3M$ entries. For the rotation $g_j$ the entries are
`x[3*j]` $=\alpha_j$, `x[3*j+1]` $=\beta_j$ and `x[3*j+2]` $=\gamma_j$. The
angles are in radians, with $\alpha_j,\gamma_j \in [-\pi,\pi)$ and
$\beta_j \in [0,\pi]$. Unlike the nodes of the [NFSFT](nfsft.md), these nodes are not
scaled by $2\pi$. `nfsoft_precompute` scales them for the internal NFFT.

### Layout of `f_hat`

`f_hat` is a packed array of

$$
\sum_{l=0}^{B} (2l+1)^2 = \frac{(B+1)\left(4(B+1)^2-1\right)}{3}
$$

complex numbers. The macro `NFSOFT_F_HAT_SIZE(B)` gives this number. The order
of the coefficients is the order of these loops:

```c
int i = 0;
for (int n = -B; n <= B; n++)
  for (int m = -B; m <= B; m++)
    for (int l = MAX(abs(m), abs(n)); l <= B; l++)
      /* f_hat[i++] holds the coefficient of degree l, order m and n. */
```

The index $n$ of $\mathrm{e}^{-\mathrm{i} n \gamma}$ runs slowest. The index $m$ of
$\mathrm{e}^{-\mathrm{i} m \alpha}$ comes next. The degree $l$ runs fastest, from
$\max(|m|,|n|)$ to $B$.

!!! warning "NFSOFT_INDEX"

    The macro `NFSOFT_INDEX(m,n,l,B)` does not compute an index into
    `plan.f_hat`. It is the index of the coefficient array of the internal NFFT
    plan, with $(2B+2)^3$ entries. Use the loop above to address `f_hat`.

## Creating a plan

| Function | Meaning |
|----------|---------|
| `nfsoft_init(&plan, N, M)` | Plan with the flags `NFSOFT_MALLOC_X`, `NFSOFT_MALLOC_F` and `NFSOFT_MALLOC_F_HAT`. |
| `nfsoft_init_advanced(&plan, N, M, nfsoft_flags)` | Plan with the given NFSOFT flags. |
| `nfsoft_init_guru(&plan, N, M, nfsoft_flags, nfft_flags, nfft_cutoff, fpt_kappa)` | Plan with the given NFFT flags, NFFT cut-off and FPT threshold. |
| `nfsoft_init_guru_advanced(&plan, N, M, nfsoft_flags, nfft_flags, nfft_cutoff, fpt_kappa, fftw_size)` | The same with the size of the oversampled FFT. |

The parameter `N` is the bandwidth $B$. The parameters have these meanings.

- `nfsoft_flags` are the NFSOFT flags.
- `nfft_flags` are the flags of the internal three-dimensional
  [NFFT](nfft.md). They must contain `MALLOC_X`, `MALLOC_F_HAT` and `MALLOC_F`,
  because the internal plan owns arrays for the nodes, the values and the
  coefficients. The example below shows a working set.
- `nfft_cutoff` is the NFFT cut-off parameter.
- `fpt_kappa` is a threshold that controls the accuracy of the FPT. The
  examples use 1000.
- `fftw_size` is the size of the three-dimensional FFTW transform inside the
  NFFT in each dimension. Write it as $(2B+2)\,\sigma$ with the oversampling
  factor $\sigma \ge 1$.

`nfsoft_init_advanced` uses the NFFT flags `PRE_PHI_HUT`, `PRE_PSI`,
`MALLOC_X`, `MALLOC_F_HAT`, `MALLOC_F`, `FFTW_INIT` and
`NFFT_OMP_BLOCKWISE_ADJOINT`, the cut-off 6 and $\kappa = 1000$.
`nfsoft_init_guru` uses the FFT size $8B$.

## Flags

The flags for the init functions are bit flags. Combine them with `|`.

### Basis and algorithms

| Flag | Effect |
|------|--------|
| `NFSOFT_NORMALIZED` | The computation uses the $\mathrm{L}^2$-normalised functions $\tilde D_{mn}^l$ in place of $D_{mn}^l$. Each coefficient carries the factor $\sqrt{(2l+1)/8\pi^2}$. |
| `NFSOFT_REPRESENT` | The Wigner-D functions get signs so that they satisfy the representation property of the spherical harmonics as defined in the NFFT software package. For every rotation matrix $A$ with the Euler angles $\alpha,\beta,\gamma$ and every unit vector $\mathbf{x}$ the relation $\sum_{m=-l}^{l} D_{mn}^l(\alpha,\beta,\gamma)\,Y_l^m(\mathbf{x}) = Y_l^n(A^{-1}\mathbf{x})$ holds. In the implementation this multiplies each coefficient by $(-1)^{\max(m,0)+\max(n,0)}$. |
| `NFSOFT_USE_NDFT` | The transforms use the exact direct NDFT in place of the fast but approximate NFFT. |
| `NFSOFT_USE_DPT` | The transforms use the direct discrete polynomial transform (DPT) in place of the FPT. |
| `NFSOFT_NO_STABILIZATION` | The FPT runs without the stabilisation scheme. The errors grow for higher bandwidths, but the transform is much faster. |
| `NFSOFT_CHOOSE_DPT` | Reserved. The flag is meant to select the DPT or the FPT by speed for the chosen orders. The current implementation has no effect. |
| `NFSOFT_SOFT` | Reserved. The flag is meant to turn the transform into the SOFT with equispaced nodes and the FFTW in place of the NFFT. The current implementation has no effect. |
| `NFSOFT_ZERO_F_HAT` | Reserved. The flag is meant to set unused entries of `f_hat` to zero. The packed layout has no unused entries. |

### Memory

| Flag | Effect |
|------|--------|
| `NFSOFT_MALLOC_X` | The init function allocates the node array `x`, of $3M$ real numbers, and `nfsoft_finalize` frees it. Without the flag, `x` must point to an array of the right size before a transform, and you free it. |
| `NFSOFT_MALLOC_F_HAT` | The same for the array `f_hat`. |
| `NFSOFT_MALLOC_F` | The same for the array `f`, of $M$ complex numbers. |

### Input preservation

The transforms `nfsoft_trafo` and `nfsoft_adjoint` never change their input
arrays `f_hat`, `x` and `f`. The flags `NFSOFT_PRESERVE_F_HAT`,
`NFSOFT_PRESERVE_X`, `NFSOFT_PRESERVE_F`, `NFSOFT_DESTROY_F_HAT`,
`NFSOFT_DESTROY_X` and `NFSOFT_DESTROY_F` are part of the interface. They have
no effect in the current implementation. The preserve flags state a guarantee
that always holds. The destroy flags allow a change that the transforms do not
make.

## How the fast algorithm works

For each pair of orders $(m,n)$ the transform `nfsoft_trafo` does these steps.

1. **Weights.** The algorithm copies the coefficients of the degrees
   $l=\max(|m|,|n|),\dots,B$ and applies the normalisation and the signs of
   `NFSOFT_NORMALIZED` and `NFSOFT_REPRESENT`.
2. **FPT.** The [FPT](fpt.md) turns these coefficients into Chebyshev
   coefficients in $\cos\beta$. It uses a set of transforms, one for each pair
   $(m,n)$, of length the next power of two with respect to $B$. With
   `NFSOFT_USE_DPT` the direct DPT does this step.
3. **Conversion.** The algorithm converts the Chebyshev coefficients into
   coefficients of complex exponentials in $\beta$. It writes them into the
   coefficient array of the internal NFFT.

Then a three-dimensional [NFFT](nfft.md) of bandwidth $2B+2$ in each dimension
evaluates the trigonometric sum in $\gamma$, $\alpha$ and $\beta$ at the nodes.
With `NFSOFT_USE_NDFT` the direct NDFT does this step. For $B=0$ the function
copies the single coefficient to all values.

`nfsoft_adjoint` runs the transposed stages in reverse order: adjoint NFFT,
transposed conversion, transposed FPT and the weights.

The FPT set is built in the init function. Its accuracy depends on
`fpt_kappa`. The transforms run in parallel over the orders when the library
uses OpenMP.

## Example

The example `examples/nfsoft/simple_test.c` creates two plans with the guru
interface, one for the fast transform and one for the direct transform with
`NFSOFT_USE_NDFT | NFSOFT_USE_DPT`. It sets random rotations and coefficients,
runs both transforms and prints the difference. Then it does the same for the
adjoint transform. The program takes the bandwidth and the number of nodes on
the command line.

```c
--8<-- "examples/nfsoft/simple_test.c:29:160"
```

## Literature

The algorithms are the work of Antje Vollrath. They are based on the following
paper. The [publications](../reference/publications.md) page lists further
references.

- D. Potts, J. Prestin and A. Vollrath. A fast algorithm for nonequispaced
  Fourier transforms on the rotation group. To appear in Num. Alg.

## API

[NFSOFT API reference](../api/nfsoft.md)
