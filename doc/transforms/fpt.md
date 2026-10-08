# FPT

Fast polynomial transform. It changes the basis of a polynomial from an
arbitrary system defined by a three-term recurrence to the Chebyshev system.
The [NFSFT](nfsft.md) and the [NFSOFT](nfsoft.md) both use it as their first
stage.

## Definition

Let $\alpha_n, \beta_n, \gamma_n$, $n=0,\dots,N$, be the recurrence
coefficients of a polynomial system $P_n$ defined by $P_{-1}(x) = 0$,
$P_{0}(x) = \gamma_0$ and

$$
P_n(x) = (\alpha_n x + \beta_n)\,P_{n-1}(x) + \gamma_n\,P_{n-2}(x),
\qquad n=1,2,\dots
$$

for $x \in [-1,1]$. The coefficients $\alpha_0$ and $\beta_0$ do not occur. The
constant $\gamma_0$ is the value of $P_0$. For the Legendre polynomials,
$\gamma_0=1$, $\alpha_n=\frac{2n-1}{n}$, $\beta_n=0$ and $\gamma_n=-\frac{n-1}{n}$.

The Chebyshev polynomials of the first kind are

$$
T_n(x) = \cos\!\left(n \arccos x\right).
$$

Let $f\colon [-1,1] \to \mathbb{R}$ be a polynomial of degree $N$. The FPT maps
the coefficients $[x_n]_{n=0..N}$ of

$$
f = \sum_{n=0}^{N} x_n P_n
$$

to the Chebyshev coefficients $[y_n]_{n=0..N}$ of

$$
f = \sum_{n=0}^{N} y_n T_n.
$$

The transform is linear. Its transposed matrix maps Chebyshev coefficients to
coefficients in the system $P_n$. The transposed is not the inverse.

A transform can start at an index $k_{\text{start}}$ and end at an index
$k_{\text{end}}$. Then only the coefficients $x_n$ with
$k_{\text{start}} \le n \le k_{\text{end}}$ are nonzero. The routines take these
$k_{\text{end}}-k_{\text{start}}+1$ coefficients in an array in which `x[0]` is
the coefficient of $P_{k_{\text{start}}}$, and they return the Chebyshev
coefficients $y_0,\dots,y_{k_{\text{end}}}$.

With the flag `FPT_FUNCTION_VALUES` the routines return the function values

$$
f(\xi_j),\qquad \xi_j = \cos\frac{\pi\,(j+\tfrac{1}{2})}{k_{\text{end}}+1},
\qquad j=0,\dots,k_{\text{end}},
$$

at the Chebyshev nodes instead of the Chebyshev coefficients.

## Algorithms

The direct algorithms `fpt_trafo_direct` and `fpt_transposed_direct` evaluate
the sum with the Clenshaw algorithm and cost ${\cal O}(N^2)$ operations. The fast
algorithms `fpt_trafo` and `fpt_transposed` use a cascade of $t=\log_2 N$ levels
of small matrix products and the FFTW cosine transforms. They stabilise the
three-term recurrence where it loses accuracy. If $k_{\text{end}}<4$, the fast
routines call the direct routines.

## Using it

The module works on a **set** of transforms of equal maximum length $N=2^t$.
The `fpt_set` handle is opaque.

1. `fpt_init(M, t, flags)` creates a set for $M$ transforms of length $2^t$,
   $t\ge 2$. The transforms have the numbers $m=0,\dots,M-1$. The flags select
   the algorithms and the data the set keeps, see the table below.
2. `fpt_precompute(set, m, alpha, beta, gam, k_start, threshold)` registers the
   recurrence coefficients of transform number `m`. The arrays `alpha`, `beta`
   and `gam` hold the coefficients $\alpha_n$, $\beta_n$ and $\gamma_n$ for
   $n=0,\dots,N$, and `gam[0]` holds $\gamma_0=P_0$. The argument `k_start` is
   $k_{\text{start}}$, with $0\le k_{\text{start}}\le N$.
3. `fpt_trafo(set, m, x, y, k_end, flags)` runs the transform and
   `fpt_trafo_direct` runs the slow reference version. The arrays `x` and `y`
   hold complex numbers. `y` has $k_{\text{end}}+1$ entries, and $k_{\text{end}}\le N$.
   Only the flag `FPT_FUNCTION_VALUES` is meaningful for the argument `flags`.
4. `fpt_transposed(set, m, x, y, k_end, flags)` and `fpt_transposed_direct` run
   the transposed transform. They read the $k_{\text{end}}+1$ Chebyshev
   coefficients, or function values, from `y` and write the
   $k_{\text{end}}-k_{\text{start}}+1$ coefficients into `x`. They overwrite `y`.
5. `fpt_finalize(set)` releases the set.

The argument `threshold` is the stabilisation threshold $\kappa>0$. During the
precomputation, the algorithm evaluates the polynomials at the Chebyshev nodes.
If a value exceeds $\kappa$ in magnitude, the algorithm uses a stabilised step
for that block. The example below uses $\kappa=1000$, a usual choice.

## Flags

The flags for `fpt_init` are bits that you combine with the bitwise or operator.

| Flag | Meaning |
|------|---------|
| `FPT_NO_STABILIZATION` | The precomputation applies no stabilisation. `threshold` has no effect. |
| `FPT_NO_FAST_ALGORITHM` | The set holds no data for the fast algorithm. `fpt_trafo` and `fpt_transposed` compute nothing unless $k_{\text{end}}<4$. |
| `FPT_NO_DIRECT_ALGORITHM` | The set holds no data for the direct algorithm. `fpt_trafo_direct` and `fpt_transposed_direct` compute nothing. This includes the calls from the fast routines for $k_{\text{end}}<4$. |
| `FPT_PERSISTENT_DATA` | `fpt_precompute` keeps the pointers to `alpha`, `beta` and `gam` instead of copying the arrays. The arrays must stay valid until `fpt_finalize`. The direct algorithm needs the arrays. |
| `FPT_AL_SYMMETRY` | The set uses the parity symmetry of the associated Legendre functions to reduce the stored data. Use it only for the recurrence coefficients of the associated Legendre functions, with the transform number $m$ equal to the order. The NFSFT sets it. |
| `FPT_NO_INIT_FPT_DATA` | `fpt_init` does not allocate the data of the single transforms. The NFSFT and the NFSOFT set this flag and set up the data themselves. Do not set it if you call `fpt_precompute`. |

The flag `FPT_FUNCTION_VALUES` is an argument of the transform routines. If it is
set, the output of `fpt_trafo` is function values at the Chebyshev nodes, and the
input of `fpt_transposed` is function values.

## Example

From `examples/fpt/simple_test.c`. The program evaluates a finite expansion in
Legendre polynomials at the Chebyshev nodes. It computes the Chebyshev
coefficients with the FPT and evaluates the cosine sum with a DCT-I of FFTW.

```c
--8<-- "examples/fpt/simple_test.c:32:153"
```

## API

[FPT API reference](../api/fpt.md)
