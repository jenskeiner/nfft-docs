# Fast summation

Direct and fast summation of kernel sums. The program computes

$$
f(y_j) = \sum_{k=1}^{N} \alpha_k\, K(y_j - x_k),
\qquad j = 1,\dots,M,
$$

for $N$ source nodes $x_k$, $M$ target nodes $y_j$, complex coefficients
$\alpha_k$ and a kernel $K : \mathbb{R}^d \to \mathbb{C}$. A direct evaluation
needs $\mathcal{O}(NM)$ operations. The fast algorithm uses the
[NFFT](../transforms/nfft.md) to approximate all $M$ sums with far fewer
operations.

!!! note "Application code"

    The code is in `applications/fastsum/`. The library `libfastsum` and the
    kernel library `libkernels` are built next to the programs. They are
    not installed and have no page in the [API reference](../api/index.md).
    Only the [NFFT API](../api/nfft.md) is public.

## Kernels and nodes

The kernel $K$ is $C^\infty$ except at the origin. In $d > 1$ dimensions $K$
is a radial function, that is $K(x)$ depends on $\|x\|_2$ only. Typical kernels
are $\log|x|$, $|x|^{-b}$ with $b \in \mathbb{N}$, Hardy's multiquadric
$(x^2+c^2)^{1/2}$ and the generalised multiquadrics $(x^2+c^2)^{-b/2}$.
[The table below](#kernel-list) lists all kernels of the program.

All nodes lie in the ball of radius $\tfrac14 - \tfrac{\varepsilon_B}{2}$
around the origin. For $d = 1$ this is the interval
$[-\tfrac14 + \tfrac{\varepsilon_B}{2},\, \tfrac14 - \tfrac{\varepsilon_B}{2}]$.
Then all differences $y_j - x_k$ have norm at most
$\tfrac12 - \varepsilon_B$. The parameter $\varepsilon_B$ is the width of the
outer boundary strip of the regularisation.

## Method

The algorithm splits the kernel into a smooth part and a part that is nonzero
only near the origin.

### Regularisation

The kernel $K$ has a singularity at the origin, and $K$ is not periodic. The
algorithm first replaces $K$ on $[-\tfrac12,\tfrac12]^d$ by a regularised
kernel $K_R$ that is smooth and periodic:

$$
K_R(t) =
\begin{cases}
T_I(t), & \|t\| < \varepsilon_I,\\
K(t), & \varepsilon_I \le \|t\| \le \tfrac12 - \varepsilon_B,\\
T_B(t), & \tfrac12 - \varepsilon_B < \|t\| \le \tfrac12.
\end{cases}
$$

Here $\varepsilon_I$ is the inner boundary. The functions $T_I$ and $T_B$ are
polynomials of degree $2p-1$ in $\|t\|$, built as two-point Taylor
interpolation. They match the derivatives of $K$ up to order $p-1$ at
$\|t\| = \varepsilon_I$ and at $\|t\| = \tfrac12 - \varepsilon_B$. The
parameter $p$ is the degree of smoothness of the regularisation.

The boundary polynomial $T_B$ depends on $d$.

* For $d = 1$ the kernel $K_R$ is the periodic continuation of the
  regularised kernel. On the boundary strip $T_B$ joins the derivatives of $K$
  at $\tfrac12 - \varepsilon_B$ to the derivatives at $-\tfrac12 + \varepsilon_B$.
  Odd kernels such as $1/x$ are allowed.
* For $d > 1$ the kernel is treated as an even radial function. On the strip
  $T_B$ goes smoothly to the constant value $K(\tfrac12)$.

The derivatives of $K$ come from the kernel function itself. Every kernel
function takes the derivative order as its second argument. The predefined
kernels implement the orders 0 to 12, so $p \le 13$.

### Far field

The smooth kernel $K_R$ has a rapidly converging Fourier series. The algorithm
truncates it to the index set
$I_n^d = \{-\tfrac{n}{2},\dots,\tfrac{n}{2}-1\}^d$:

$$
K_R(t) \approx \sum_{l \in I_n^d} b_l\, \mathrm{e}^{-2\pi\mathrm{i}\, l\cdot t}.
$$

The coefficients $b_l$ follow from one $d$-dimensional FFT of samples of $K_R$
on a regular grid with $n$ points per dimension. Insert the series into the sum:

$$
f_{\text{far}}(y_j) = \sum_{l \in I_n^d} b_l
\Bigl(\sum_{k=1}^{N} \alpha_k\, \mathrm{e}^{2\pi\mathrm{i}\, l\cdot x_k}\Bigr)
\mathrm{e}^{-2\pi\mathrm{i}\, l\cdot y_j}.
$$

The inner sum is an adjoint NFFT at the source nodes. The outer sum is an NFFT
at the target nodes. So the far field takes three steps:

1. Adjoint NFFT of the coefficients $\alpha_k$ at the nodes $x_k$.
2. Multiplication of the result by the coefficients $b_l$.
3. NFFT at the nodes $y_j$.

Both NFFT plans have bandwidth $n$ in every dimension, oversampled
bandwidth $2n$ and cut-off parameter $m$.

### Near field

The far field approximates $K_R$ instead of $K$. The two differ only for
$\|t\| < \varepsilon_I$. The near field correction adds the difference

$$
K_{NE}(t) = K(t) - K_R(t) \quad\text{for } \|t\| < \varepsilon_I,
\qquad K_{NE}(t) = 0 \quad\text{otherwise},
$$

for every pair of nodes with $\|y_j - x_k\| < \varepsilon_I$. The result is

$$
f(y_j) \approx f_{\text{far}}(y_j)
+ \sum_{\|y_j - x_k\| < \varepsilon_I} \alpha_k\, K_{NE}(y_j - x_k).
$$

The program must find the sources near each target. It has two methods.

* Search tree (default). The plan sorts the sources into a
  $k$-d tree. The search for a target visits only the tree parts that meet the
  cube of side $2\varepsilon_I$ around the target. The sort changes the order
  of `x` and `alpha` in the plan.
* Boxes (flag `NEARFIELD_BOXES`). The plan distributes the sources into boxes
  of side $\varepsilon_I$ and searches the neighbouring boxes.
  It stores sorted copies of `x` and `alpha` and leaves the plan arrays
  unchanged. This method supports $d \le 3$.

Evaluating $K_{NE}$ needs $K_R$ near the origin. By default the plan tabulates
$K_R$ for $\|t\| \le \varepsilon_I$ at $A_d$ knots and interpolates with
piecewise cubic Lagrange polynomials. The number of knots is
$A_d = 4p^2$ for $d = 1$ and $A_d = 2p^2$ for $d > 1$. The kernel
$1/x$ in $d > 1$ is an exception: the plan uses more knots, depending on $p$.
The flag `EXACT_NEARFIELD` evaluates $K_R$ directly instead of
interpolating.

If $\varepsilon_I = 0$ the plan has no near field. Use this only for
kernels that are smooth at the origin.

## Kernel list

Every kernel is a C function `C name(R x, int der, const R *param)`. The
argument `x` is the distance, `der` the derivative order and `param[0]` the
kernel parameter $c$. The program selects a kernel by its name on the command
line.

| Name | $K(x)$ | Uses $c$ |
|------|--------|----------|
| `gaussian` | $\mathrm{e}^{-x^2/c^2}$ | yes |
| `multiquadric` | $\sqrt{x^2+c^2}$ | yes |
| `inverse_multiquadric` | $1/\sqrt{x^2+c^2}$ | yes |
| `inverse_multiquadric3` | $1/\sqrt{x^2+c^2}^{\,3}$ | yes |
| `logarithm` | $\log\lvert x\rvert$ | no |
| `thinplate_spline` | $x^2 \log\lvert x\rvert$ | no |
| `one_over_square` | $1/x^2$ | no |
| `one_over_modulus` | $1/\lvert x\rvert$ | no |
| `one_over_x` | $1/x$ | no |
| `one_over_cube` | $1/x^3$ | no |
| `sinc_kernel` | $\sin(cx)/x$ | yes |
| `cosc` | $\cos(cx)/x$ | yes |
| `cot` | $\cot(cx)$ | yes |
| `log_sin` | $\log\lvert\sin(cx)\rvert$ | yes |
| `laplacian_rbf` | $\mathrm{e}^{-\lvert x\rvert/c}$ | yes |
| `der_laplacian_rbf` | $\lvert x\rvert/c\;\mathrm{e}^{-\lvert x\rvert/c}$ | yes |
| `xx_gaussian` | $(x^2/c^2)\,\mathrm{e}^{-x^2/c^2}$ | yes |
| `absx` | $\lvert x\rvert$ | no |

The kernel `cot` is the C function `kcot`. To add a kernel, write a function
with this signature that returns the derivatives of order 0 up to $p-1$, and
add it to the name lookup in the program. `applications/fastsum/kernels.c`
holds all predefined kernels as examples.

## Parameters

| Parameter | Meaning |
|-----------|---------|
| $d$ | Dimension. |
| $N$, $M$ | Number of source nodes and of target nodes. |
| $n$ | Expansion degree. The far field uses $n^d$ Fourier coefficients. $n$ must be even. |
| $m$ | Cut-off parameter of the NFFT. |
| $p$ | Degree of smoothness of the regularisation. |
| kernel, $c$ | The kernel function and its parameter. |
| $\varepsilon_I$ | Inner boundary, the radius of the near field. The test programs and `fastsum_test.m` use $\varepsilon_I = p/n$. |
| $\varepsilon_B$ | Outer boundary. The test programs and `fastsum_test.m` use $\varepsilon_B = 1/16$. |
| flags | `EXACT_NEARFIELD`, `NEARFIELD_BOXES`, `STORE_PERMUTATION_X_ALPHA`. |

The flag `STORE_PERMUTATION_X_ALPHA` applies to the search tree with
$\varepsilon_I > 0$. It makes the plan store the permutation of the source
nodes in `permutation_x_alpha`.

## Plan lifecycle

The plan `fastsum_plan` in `applications/fastsum/fastsum.h` has these members
that a caller uses.

`d`, `N_total`, `M_total`
:   Dimension and numbers of source and target nodes.

`x`, `y`
:   Source nodes, $d$ values per node, and target nodes.
    The nodes lie in the ball of radius $\tfrac14 - \tfrac{\varepsilon_B}{2}$.

`alpha`, `f`
:   Source coefficients and target values, both complex.

`k`, `kernel_param`, `flags`
:   Kernel function, pointer to its parameters and the flags.

`n`, `p`, `eps_I`, `eps_B`
:   Expansion degree, smoothness, inner boundary and outer boundary.

The plan is used in five steps.

1. **Initialise.** `fastsum_init_guru` takes $d$, $N$, $M$, the kernel, the
   parameters, the flags, $n$, $m$, $p$, $\varepsilon_I$ and $\varepsilon_B$. It
   allocates the node and coefficient arrays. The call has three parts that a
   program can also call alone: the kernel part
   (`fastsum_init_guru_kernel`), the source part
   (`fastsum_init_guru_source_nodes`) and the target part
   (`fastsum_init_guru_target_nodes`). The kernel part builds the near field
   table and computes the coefficients $b_l$ with one FFT. The two other parts
   create the NFFT plans. `fastsum_init_guru` uses the oversampled bandwidth
   $2n$ for both.
2. **Fill.** The program writes the source nodes to `x`, the target nodes to
   `y` and the coefficients to `alpha`.
3. **Precompute.** `fastsum_precompute` builds the search tree or the boxes
   and precomputes the NFFT window values. The source part and the target part
   also exist alone, as `fastsum_precompute_source_nodes` and
   `fastsum_precompute_target_nodes`. In tree mode the call sorts `x` and
   `alpha` in place. A caller that provides new coefficients later must use
   this order or the stored permutation.
4. **Evaluate.** `fastsum_trafo` runs the fast algorithm and writes the
   result to `f`. `fastsum_exact` computes the direct sum into `f` for a
   comparison.
5. **Finalise.** `fastsum_finalize` frees the plan. The parts
   `fastsum_finalize_kernel`, `fastsum_finalize_source_nodes` and
   `fastsum_finalize_target_nodes` free the corresponding parts.

With `MEASURE_TIME` defined at configure time (`--enable-measure-time`) the
plan stores the time of each step in `MEASURE_TIME_t`.

## Programs

The directory `applications/fastsum/` builds these programs. The Makefile
lists them as `noinst_PROGRAMS`, so `make install` does not install them.

`fastsum_test`
:   Random test. It creates random nodes and coefficients, computes the sums
    directly and with the fast algorithm, and prints the times and the maximum
    relative error.

`fastsum_matlab`
:   The same computation on data from files. The MATLAB and Octave function
    `fastsum.m` calls it.

`fastsum_test_threads`
:   The source of `fastsum_test` linked to the OpenMP libraries. It prints the
    number of threads. It exists only with `--enable-openmp`.

`fastsum_benchomp`, `fastsum_benchomp_createdataset`, `fastsum_benchomp_detail_single`, `fastsum_benchomp_detail_threads`
:   Benchmark programs for the OpenMP version. They exist only with
    `--enable-openmp`.

### Build

The application programs are built by default. The option
`--enable-applications` switches them on explicitly, and `--enable-all`
builds every module together with the applications.

```bash
./configure --enable-all --enable-openmp
make -j
cd applications/fastsum
```

The CMake build has the option `NFFT_ENABLE_APPLICATIONS`, on by default. It
places the programs in `build/applications/fastsum/`.

### fastsum_test

```bash
./fastsum_test d N M n m p kernel c eps_I eps_B
```

All ten arguments are required. `kernel` is a name from the
[kernel list](#kernel-list). An unknown name selects `multiquadric`.
The program draws the nodes uniformly in the ball of radius
$\tfrac14 - \tfrac{\varepsilon_B}{2}$. It draws the real and imaginary parts of
the coefficients uniformly in $[0,1)$. A call with the settings of
`fastsum_test.m` in two dimensions is

```bash
./fastsum_test 2 2000 2000 156 4 3 multiquadric 0.0223607 0.0192308 0.0625
```

The program prints the parameters and the near field method, then the times of
the direct computation, the precomputation and the fast computation, and

```text
max relative error: ...
```

The error is $\max_j |f_{\text{direct}}(y_j) - f(y_j)| / |f_{\text{direct}}(y_j)|$.
The program uses the search tree. To try the boxes, change the flags argument
of `fastsum_init_guru` in the source from `0` to `NEARFIELD_BOXES`.

### fastsum_matlab and fastsum.m

`fastsum_matlab` takes the same ten arguments as `fastsum_test`, but an
unknown kernel name stops the program. It reads the nodes and coefficients from
the current directory:

| File | Content |
|------|---------|
| `x.dat` | $N$ lines with the $d$ coordinates of a source node. |
| `alpha.dat` | $N$ lines with real part and imaginary part of a coefficient. |
| `y.dat` | $M$ lines with the $d$ coordinates of a target node. |

It writes `f.dat` and `f_direct.dat`, each with $M$ lines of real part and
imaginary part, for the fast and the direct result.

The function `fastsum.m` writes these files, calls `fastsum_matlab` and reads
the results:

```matlab
[f, f_direct] = fastsum(x, alpha, y, kernel, c, m, n, p, eps_I, eps_B);
```

Here `x` is an $N \times d$ matrix, `alpha` an $N \times 1$ complex vector and
`y` an $M \times d$ matrix. The program `fastsum_matlab` must be in the current
directory. The script `fastsum_test.m` shows the use. It sets
$N = M = 2000$, the multiquadric kernel with $c = 1/\sqrt{N}$, $m = 4$,
$p = 3$, $n = 156$, $\varepsilon_I = p/n$ and $\varepsilon_B = 1/16$. It draws
random nodes in the disc of radius $\tfrac14 - \tfrac{\varepsilon_B}{2}$ and
calls `fastsum`.

## Example

The main steps of `fastsum_test.c` are the plan initialisation, the direct
computation, the precomputation, the fast computation and the error.

```c
--8<-- "applications/fastsum/fastsum_test.c:164:166"
```

The program then fills `x`, `y` and `alpha` with random values and runs the
computation.

```c
--8<-- "applications/fastsum/fastsum_test.c:246:288"
```

## Accuracy

The error of the fast algorithm depends on $n$, $m$, $p$, $\varepsilon_I$ and
$\varepsilon_B$. A larger $n$, $m$ and $p$ give a smaller error and a higher
cost. The error is the sum of the truncation error of the Fourier series of
$K_R$, the error of the NFFT and the error of the near field interpolation.
The papers [1] and [3] analyse this error.

## Julia interface

A Julia module `fastsum` in `julia/fastsum/` wraps the same library. It is
built with `--enable-julia`. See [Julia](../interfaces/julia.md).

## References

1. D. Potts and G. Steidl. Fast summation at nonequispaced knots by NFFTs.
   SIAM J. Sci. Comput., 24:2013-2037, 2003.
2. D. Potts, G. Steidl and A. Nieslony. Fast convolution with radial kernels at
   nonequispaced knots. Numer. Math., 98:329-351, 2004.
3. M. Fenn and G. Steidl. Fast NFFT-based summation of radial functions. Sampl.
   Theory Signal Image Process., 3:1-28, 2004.
4. M. Fenn and D. Potts. Fast summation based on fast trigonometric transforms
   at non-equispaced nodes. Numer. Linear Algebra Appl., 12:161-169, 2005.
