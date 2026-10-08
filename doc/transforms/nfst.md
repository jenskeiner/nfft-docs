# NFST

Nonequispaced fast sine transform. The odd counterpart of the
[NFCT](nfct.md): same real-valued setting, sine kernel instead of cosine.

## Definition

The frequencies are the multi-indices of the set

$$
I_{\mathbf{N}}^{\mathrm{S}} := \left\{ \mathbf{k}=\left(k_t\right)_{t=0,\dots,d-1}
\in\mathbb{Z}^d : 1 \le k_t < N_t,\; t=0,\dots,d-1 \right\}.
$$

The index $k_t=0$ is missing, because the sine is zero for it. The nodes
$\mathbf{x}_j$, $j=0,\dots,M-1$, lie in $[0,\tfrac{1}{2})^d$. The
**nonequispaced discrete sine transform** (NDST) is

$$
f_j = \sum_{\mathbf{k}\in I_{\mathbf{N}}^{\mathrm{S}}} \hat f_{\mathbf{k}}
\prod_{t=0}^{d-1} \sin\!\left(2\pi\,k_t x_{j,t}\right),
\qquad j=0,\dots,M-1,
$$

and the adjoint NDST is

$$
\hat f_{\mathbf{k}} = \sum_{j=0}^{M-1} f_j
\prod_{t=0}^{d-1} \sin\!\left(2\pi\,k_t x_{j,t}\right),
\qquad \mathbf{k}\in I_{\mathbf{N}}^{\mathrm{S}}.
$$

Both $\hat f_{\mathbf{k}}$ and $f_j$ are real. The number of coefficients is
$(N_0-1)\cdots(N_{d-1}-1)$. The last dimension runs fastest in `f_hat`, and the
entry of the frequency $\mathbf{k}$ in dimension $t$ has the index $k_t-1$.

## Cost

`nfst_trafo_direct` and `nfst_adjoint_direct` evaluate the sums as written, in
${\cal O}(|I_{\mathbf{N}}^{\mathrm{S}}|M)$ operations. `nfst_trafo` and
`nfst_adjoint` need only
${\cal O}(|I_{\mathbf{N}}^{\mathrm{S}}|\log|I_{\mathbf{N}}^{\mathrm{S}}| + M)$
operations.

The fast algorithm has the same three steps as the [NFFT](nfft.md): a diagonal
deconvolution, an FFT and a sparse convolution with a window function. The FFT is
a real-to-real FFTW transform of type DST-I, `FFTW_RODFT00`, of length $n_t$ in
dimension $t$.

## Using a plan

The life cycle is the one of the [NFFT](nfft.md#using-a-plan), with the prefix
`nfst_`.

1. Declare `nfst_plan p;` and initialise it with `nfst_init_1d`, `nfst_init_2d`,
   `nfst_init_3d`, `nfst_init` or `nfst_init_guru`.
2. Write the nodes into `p.x`. Every component must lie in $[0,\tfrac{1}{2})$.
3. If `p.flags & PRE_ONE_PSI` is nonzero, call `nfst_precompute_one_psi`. The
   call must follow step 2.
4. Write the input into `p.f_hat` for the forward transform or into `p.f` for the
   adjoint. Both are arrays of real numbers. Call `nfst_check` to test the plan.
   It returns a message or a null pointer.
5. Call `nfst_trafo` or `nfst_adjoint`, read the other array, then call
   `nfst_finalize`.

`nfst_init` and the wrappers choose these defaults.

- $n_t = 2\,(2^{\lceil \log_2 N_t \rceil} - 1) + 1$ is the length of the DST-I.
- $m$ is the default cut-off of the window function that the library was
  compiled with. Query it with `nfft_get_default_window_cut_off`.
- `fftw_flags` is `FFTW_ESTIMATE | FFTW_DESTROY_INPUT`.
- `flags` is `PRE_PHI_HUT | PRE_PSI | MALLOC_X | MALLOC_F_HAT | MALLOC_F | FFTW_INIT`.
  For $d=1$ the plan also sets `FFT_OUT_OF_PLACE`.

`nfst_init_guru` sets `n`, `m`, `flags` and `fftw_flags` from its arguments.

## Flags

The plan accepts the flags of the [NFFT](nfft.md#flags): `PRE_PHI_HUT`,
`PRE_PSI`, `PRE_FULL_PSI`, `PRE_LIN_PSI`, `FG_PSI`, `PRE_FG_PSI`, `MALLOC_X`,
`MALLOC_F_HAT`, `MALLOC_F`, `FFTW_INIT` and `FFT_OUT_OF_PLACE`. They have the same
meaning. The flags `NFFT_SORT_NODES` and `NFFT_OMP_BLOCKWISE_ADJOINT` have no
effect. With `PRE_LIN_PSI` the table has $K=2^{10}(m+2)$ samples per dimension.

## Example

From `examples/nfst/simple_test.c`:

```c
--8<-- "examples/nfst/simple_test.c.in:28:77"
```

## References

Fenn, M. and Potts, D. Fast summation based on fast trigonometric transforms at
nonequispaced nodes. Numer. Linear Algebra Appl., 12:161--169, 2005.

## API

[NFST API reference](../api/nfst.md)
