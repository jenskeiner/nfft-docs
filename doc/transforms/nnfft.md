# NNFFT

Nonequispaced fast Fourier transform in time **and** frequency. The
[NFFT](nfft.md) allows arbitrary nodes $\mathbf{x}_j$ but keeps the frequencies
on a grid. The NNFFT drops that restriction too.

## Definition

Given $N_{\text{total}}$ arbitrary frequency nodes $v_k$ and
$M_{\text{total}}$ arbitrary spatial nodes $x_j$, the transform evaluates

$$
f(x_j) = \sum_{k=0}^{N_{\text{total}}-1} \hat f(v_k)\,
\mathrm{e}^{-2\pi\mathrm{i}\, v_k x_j \odot N},
\qquad j=0,\dots,M_{\text{total}}-1,
$$

and the adjoint

$$
\hat f(v_k) = \sum_{j=0}^{M_{\text{total}}-1} f(x_j)\,
\mathrm{e}^{+2\pi\mathrm{i}\, v_k x_j \odot N},
\qquad k=0,\dots,N_{\text{total}}-1.
$$

Here $\odot$ is the componentwise product and $N$ the bandwidth, so
$v_k x_j \odot N = \sum_{t=0}^{d-1} v_{k,t}\,x_{j,t}\,N_t$. The frequency nodes
are scaled by $N$ before they enter the exponent. Both node sets lie in
$[-\tfrac{1}{2},\tfrac{1}{2})^d$. The plan does not check this.

The number of coefficients is $N_{\text{total}}$, the number of frequency nodes.
It is not the product of the bandwidths.

## Cost

`nnfft_trafo_direct` and `nnfft_adjoint_direct` evaluate the sums as written, in
${\cal O}(N_{\text{total}}M_{\text{total}})$ operations. `nnfft_trafo` and
`nnfft_adjoint` approximate them fast.

## How it works

The NNFFT applies the NFFT idea twice: once to the frequency nodes and once to
the spatial nodes. The forward transform has three steps.

1. A sparse matrix spreads each coefficient $\hat f(v_k)$ onto a regular grid
   with a window function. The frequency nodes $v_k$ take the role that the
   spatial nodes have in the NFFT. The window has $2m+2$ values per dimension.
2. An [NFFT](nfft.md) of bandwidth $aN_1$ evaluates the grid values at the
   nodes $x_j/\sigma$. The plan owns this inner `nfft_plan`. It is reachable as
   `direct_plan`.
3. A diagonal matrix divides each sample by the Fourier transform of the window
   function at $x_j \odot N$.

The adjoint transform applies the transposed steps in the opposite order.

The plan uses these quantities. $N_1 = \sigma N$ is the oversampled bandwidth,
$a = 1 + 2m/N_1$ enlarges the grid so that the window fits, and $aN_1$ is the
grid length, made even. The member `sigma` holds the
oversampling factor.

## Using a plan

1. Declare `nnfft_plan p;` and initialise it. `nnfft_init(&p, d, N_total, M_total, N)`
   sets the numbers of frequency nodes and spatial nodes and the bandwidth
   vector `N`. `nnfft_init_1d(&p, N, M_total)` is the wrapper for $d=1$ with
   $N_{\text{total}}=N$. `nnfft_init_guru` also sets the oversampled bandwidth
   `N1`, the cut-off `m` and the flags.
2. Write the spatial nodes into `p.x` and the frequency nodes into `p.v`. Node
   $j$ occupies `p.x[j*d]`, ..., `p.x[j*d+d-1]`. The layout of `p.v` is the same.
3. Call `nnfft_precompute_one_psi`. It runs the precomputation that the flags
   select.
4. Write the coefficients into `p.f_hat` for the forward transform or the
   samples into `p.f` for the adjoint.
5. Call `nnfft_trafo` or `nnfft_adjoint`, read the other array, then call
   `nnfft_finalize`.

`nnfft_init` and `nnfft_init_1d` choose these defaults.

- $N_{1,t} = \lceil 1.5\,N_t \rceil$, rounded up to an even number. The
  oversampling factor is about $1.5$.
- $m$ is the default cut-off of the window function that the library was
  compiled with. Query it with `nfft_get_default_window_cut_off`.
- `nnfft_flags` is `PRE_PSI | PRE_PHI_HUT | MALLOC_X | MALLOC_V | MALLOC_F_HAT | MALLOC_F`.

## Flags

The member `nnfft_flags` holds the flags of the plan. The flags for the inner
NFFT follow from them.

| Flag | Meaning |
|------|---------|
| `PRE_PHI_HUT` | The plan stores the values of the Fourier transformed window function for the diagonal step, one value per spatial node. `nnfft_precompute_phi_hut` computes them from `x`. |
| `PRE_PSI` | The plan stores $(2m+2)dN_{\text{total}}$ window values for the spreading step. `nnfft_precompute_psi` computes them from `v` and `x`. |
| `PRE_FULL_PSI` | The plan stores $(2m+2)^dN_{\text{total}}$ window values and their indices. `nnfft_precompute_full_psi` computes them from `v` and `x`. |
| `PRE_LIN_PSI` | The plan interpolates linearly in a lookup table of equispaced window samples. `nnfft_precompute_lin_psi` computes the table. It does not depend on the nodes. |
| `MALLOC_X` | The plan allocates the spatial nodes `x` and frees them in `nnfft_finalize`. |
| `MALLOC_V` | The plan allocates the frequency nodes `v` and frees them in `nnfft_finalize`. |
| `MALLOC_F_HAT` | The plan allocates the coefficient vector `f_hat` and frees it in `nnfft_finalize`. |
| `MALLOC_F` | The plan allocates the sample vector `f` and frees it in `nnfft_finalize`. |

`PRE_PSI`, `PRE_FULL_PSI` and `PRE_LIN_PSI` are alternatives. Use at most one of
them. `nnfft_precompute_one_psi` calls the routines that belong to the flags in
`nnfft_flags`. Call it once after you set both node sets. The single
precomputation routines exist for the case that only one node set changes.

## Example

From `examples/nnfft/simple_test.c`:

```c
--8<-- "examples/nnfft/simple_test.c:29:83"
```

## References

Potts, D., Steidl, G. and Tasche, M. Fast Fourier transforms for nonequispaced
data: A tutorial. In: Modern Sampling Theory: Mathematics and Applications,
J. J. Benedetto and P. Ferreira (Eds.), Chapter 12, pages 249-274. 1998.

Tobias Knopp wrote the NNFFT module based on this paper.

## API

[NNFFT API reference](../api/nnfft.md)
