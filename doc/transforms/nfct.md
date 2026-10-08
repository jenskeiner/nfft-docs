# NFCT

Nonequispaced fast cosine transform. The real-valued counterpart of the
[NFFT](nfft.md): the exponential kernel is replaced by a cosine, so both the
coefficients and the samples are real.

## Definition

The frequencies are the multi-indices of the set

$$
I_{\mathbf{N}}^{\mathrm{C}} := \left\{ \mathbf{k}=\left(k_t\right)_{t=0,\dots,d-1}
\in\mathbb{Z}^d : 0 \le k_t < N_t,\; t=0,\dots,d-1 \right\}.
$$

The nodes $\mathbf{x}_j$, $j=0,\dots,M-1$, lie in $[0,\tfrac{1}{2})^d$, the half
period the cosine is even about. The **nonequispaced discrete cosine transform**
(NDCT) is

$$
f_j = \sum_{\mathbf{k}\in I_{\mathbf{N}}^{\mathrm{C}}} \hat f_{\mathbf{k}}
\prod_{t=0}^{d-1} \cos\!\left(2\pi\,k_t x_{j,t}\right),
\qquad j=0,\dots,M-1,
$$

and the adjoint NDCT is

$$
\hat f_{\mathbf{k}} = \sum_{j=0}^{M-1} f_j
\prod_{t=0}^{d-1} \cos\!\left(2\pi\,k_t x_{j,t}\right),
\qquad \mathbf{k}\in I_{\mathbf{N}}^{\mathrm{C}}.
$$

Both $\hat f_{\mathbf{k}}$ and $f_j$ are real. The number of coefficients is
$N_0\cdots N_{d-1}$. The last dimension runs fastest in `f_hat`.

## Cost

`nfct_trafo_direct` and `nfct_adjoint_direct` evaluate the sums as written, in
${\cal O}(|I_{\mathbf{N}}^{\mathrm{C}}|M)$ operations. `nfct_trafo` and
`nfct_adjoint` need only
${\cal O}(|I_{\mathbf{N}}^{\mathrm{C}}|\log|I_{\mathbf{N}}^{\mathrm{C}}| + M)$
operations.

The fast algorithm has the same three steps as the [NFFT](nfft.md): a diagonal
deconvolution, an FFT and a sparse convolution with a window function. The FFT is
a real-to-real FFTW transform of type DCT-I, `FFTW_REDFT00`, of length
$n_t$ in dimension $t$.

## Using a plan

The life cycle is the one of the [NFFT](nfft.md#using-a-plan), with the prefix
`nfct_`.

1. Declare `nfct_plan p;` and initialise it with `nfct_init_1d`, `nfct_init_2d`,
   `nfct_init_3d`, `nfct_init` or `nfct_init_guru`.
2. Write the nodes into `p.x`. Every component must lie in $[0,\tfrac{1}{2})$.
3. If `p.flags & PRE_ONE_PSI` is nonzero, call `nfct_precompute_one_psi`. The
   call must follow step 2.
4. Write the input into `p.f_hat` for the forward transform or into `p.f` for the
   adjoint. Both are arrays of real numbers. Call `nfct_check` to test the plan.
   It returns a message or a null pointer.
5. Call `nfct_trafo` or `nfct_adjoint`, read the other array, then call
   `nfct_finalize`.

`nfct_init` and the wrappers choose these defaults.

- $n_t = 2\,(2^{\lceil \log_2 N_t \rceil} - 1)$ is the length of the DCT-I.
- $m$ is the default cut-off of the window function that the library was
  compiled with. Query it with `nfft_get_default_window_cut_off`.
- `fftw_flags` is `FFTW_ESTIMATE | FFTW_DESTROY_INPUT`.
- `flags` is `PRE_PHI_HUT | PRE_PSI | MALLOC_X | MALLOC_F_HAT | MALLOC_F | FFTW_INIT`.
  For $d=1$ the plan also sets `FFT_OUT_OF_PLACE`.

`nfct_init_guru` sets `n`, `m`, `flags` and `fftw_flags` from its arguments.

## Flags

The plan accepts the flags of the [NFFT](nfft.md#flags): `PRE_PHI_HUT`,
`PRE_PSI`, `PRE_FULL_PSI`, `PRE_LIN_PSI`, `FG_PSI`, `PRE_FG_PSI`, `MALLOC_X`,
`MALLOC_F_HAT`, `MALLOC_F`, `FFTW_INIT` and `FFT_OUT_OF_PLACE`. They have the same
meaning. The flags `NFFT_SORT_NODES` and `NFFT_OMP_BLOCKWISE_ADJOINT` have no
effect. With `PRE_LIN_PSI` the table has $K=2^{10}(m+2)$ samples per dimension.

## Example

From `examples/nfct/simple_test.c`:

```c
--8<-- "examples/nfct/simple_test.c.in:28:77"
```

## References

Fenn, M. and Potts, D. Fast summation based on fast trigonometric transforms at
nonequispaced nodes. Numer. Linear Algebra Appl., 12:161--169, 2005.

## API

[NFCT API reference](../api/nfct.md)
