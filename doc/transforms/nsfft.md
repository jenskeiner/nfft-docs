# NSFFT

Nonequispaced sparse fast Fourier transform. Same transform as the
[NFFT](nfft.md), but the frequencies live on a **hyperbolic cross** instead of a
full tensor-product grid.

!!! note "Window function"

    The NSFFT needs the Gaussian window. Configure the library with
    `--with-window=gaussian`. With any other window, `nsfft_init` prints an error
    message to the standard error stream and does nothing.

## Definition

Let $H_N^d$ be the hyperbolic cross index set of problem size $J$ in dimension
$d$. It is a subset of the frequency set $I_{\mathbf{N}}$ of the
[NFFT](nfft.md) with $N_t = N = 2^{J+2}$. The transform evaluates

$$
f_j = \sum_{\mathbf{k}\in H_N^d} \hat f_{\mathbf{k}}\,
\mathrm{e}^{-2\pi\mathrm{i}\,\mathbf{k}\mathbf{x}_j},
\qquad j=0,\dots,M-1,
$$

and the adjoint

$$
\hat f_{\mathbf{k}} = \sum_{j=0}^{M-1} f_j\,
\mathrm{e}^{+2\pi\mathrm{i}\,\mathbf{k}\mathbf{x}_j},
\qquad \mathbf{k}\in H_N^d.
$$

The nodes $\mathbf{x}_j$ lie in the torus $[-\tfrac{1}{2},\tfrac{1}{2})^d$.

## The hyperbolic cross

A full grid of bandwidth $N$ in $d$ dimensions holds $N^d$ coefficients. The
hyperbolic cross keeps only the frequencies whose product of moduli stays small,
which is where the coefficients of a smooth function are large. The number of
frequencies grows with the problem size $J$ as

$$
|H_N^2| = (J+4)\,2^{J+1}, \qquad
|H_N^3| = 2^J\,6\left(2^{\frac{J+1}{2}+1}-1\right) + 2^{3\left(\frac{J}{2}+1\right)},
$$

where the divisions in the exponents are integer divisions. This is far below
$N^d$. Only $d=2$ and $d=3$ are implemented.

For $d=2$ the set is the union of a central square and of dyadic rectangles. Let

$$
\langle a \rangle := \{ k\in\mathbb{Z} : -a/2 \le k < a/2 \}
\quad\text{for } a \ge 2, \qquad \langle 1 \rangle := \{0\},
$$

and let $a=2^r$ and $b=2^{J-r}$. Then

$$
H_N^2 = \left\langle 2^{\lfloor J/2\rfloor+1} \right\rangle^2
\;\cup \bigcup_{r=0}^{\lfloor (J+1)/2\rfloor}
\Big( \langle a\rangle \times \left([b,2b)\cup[-2b,-b)\right)
\;\cup\; \left([b,2b)\cup[-2b,-b)\right) \times \langle a\rangle \Big).
$$

Each rectangle has $2^J$ frequencies. The case $d=3$ follows the same dyadic
construction.

## How it works

The transform splits the cross into these blocks and runs a short
[NFFT](nfft.md) on each one. The plan holds the block plans in `act_nfft_plan`,
`center_nfft_plan` and the `set_nfft_plan_1d` and `set_nfft_plan_2d` arrays.
The oversampling factor of the block plans is $\sigma=2$, and the blocks use
the Gaussian window with the flag `FG_PSI`.

The array `f_hat` holds the $N_{\text{total}}$ coefficients block by block, not
in the order of a full grid. `nsfft_cp` copies them to the correct positions of
the coefficient vector of a full NFFT plan and copies the nodes, so that you can
compare the two transforms.

## Using a plan

1. Declare `nsfft_plan p;` and call `nsfft_init(&p, d, J, M, m, flags)`. The
   arguments are the dimension $d\in\{2,3\}$, the problem size $J$, the number
   of nodes $M$, the cut-off $m$ of the block NFFTs and the flags.
2. Set the flag `NSDFT` if you want to call `nsfft_trafo_direct`,
   `nsfft_adjoint_direct` or `nsfft_cp`. The flag allocates and initialises the
   member `index_sparse_to_full`, the map from the block layout of `f_hat` to the
   full grid. The map uses much memory. Leave the flag off if you use only the
   fast transforms.
3. Set the nodes and the coefficients. `nsfft_init_random_nodes_coeffs` fills
   both with pseudo random values. The plan keeps the nodes in
   `p.act_nfft_plan->x`, and the block plans use copies with exchanged
   coordinates. For $d=2$ this copy is `p.x_transposed`, for $d=3$ the copies are
   `p.x_102`, `p.x_201`, `p.x_120` and `p.x_021`. To use your own nodes, fill all
   of these arrays.
4. Call `nsfft_trafo` or `nsfft_adjoint`. The samples are in `p.f` and the
   coefficients in `p.f_hat`.
5. Call `nsfft_finalize`.

For $d=3$ and $J=9$ the index conversion in `index_sparse_to_full` overflows the
range of the integer type.

## Example

From `examples/nsfft/simple_test.c`:

```c
--8<-- "examples/nsfft/simple_test.c:27:56"
```

The program `examples/nsfft/nsfft_test.c` measures the error of the fast
transform against the direct transform and the run times of the NSFFT, the direct
NSDFT and the full NFFT.

## References

Fenn, M., Kunis, S. and Potts, D. Fast evaluation of trigonometric polynomials
from hyperbolic crosses.

## API

[NSFFT API reference](../api/nsfft.md)
