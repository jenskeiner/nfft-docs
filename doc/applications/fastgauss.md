# Fast Gauss transform

Fast Gauss transform with complex parameter. The program computes the
one-dimensional Gauss transform

$$
g(y_j) = \sum_{k=1}^{N} \alpha_k\, \mathrm{e}^{-\sigma (y_j - x_k)^2},
\qquad j = 1,\dots,M,
$$

for real nodes $x_k, y_j \in [-\tfrac14, \tfrac14]$, complex coefficients
$\alpha_k$ and a complex parameter $\sigma$ with $\operatorname{Re}\sigma > 0$.
The fast algorithm is based on the [NFFT](../transforms/nfft.md). The Gaussian
is a kernel with an explicit Fourier transform, so the NFFT method of
[fast summation](fastsum.md) needs no regularisation here.

## Method

Let $p \ge 1$ be a period. The differences $y_j - x_k$ lie in
$[-\tfrac12, \tfrac12]$. On this interval the Gaussian equals the restriction of
its $p$-periodisation up to a small error. The periodised function has the
Fourier series

$$
\mathrm{e}^{-\sigma t^2} \approx \sum_{l=-n/2}^{n/2-1} b_l\,
\mathrm{e}^{-2\pi\mathrm{i}\, l\, t/p},
\qquad
b_l = \frac{1}{p}\sqrt{\frac{\pi}{\sigma}}\;
\mathrm{e}^{-\pi^2 l^2/(p^2\sigma)}.
$$

The coefficient $b_l$ is $1/p$ times the value of the continuous Fourier
transform of the Gaussian at $l/p$. Insert the series into the sum. The transform becomes

$$
g(y_j) \approx \sum_{l=-n/2}^{n/2-1} b_l
\Bigl(\sum_{k=1}^{N} \alpha_k\, \mathrm{e}^{2\pi\mathrm{i}\, l\, x_k/p}\Bigr)
\mathrm{e}^{-2\pi\mathrm{i}\, l\, y_j/p}.
$$

The algorithm has three steps.

1. Adjoint NFFT of the coefficients $\alpha_k$ at the scaled nodes $x_k/p$.
2. Multiplication by $b_l$.
3. NFFT at the scaled nodes $y_j/p$.

Three parameters control the error.

* The period $p$ controls the periodisation error. The wrap-around distance of
  the periodised Gaussian is at least $p - \tfrac12$.
* The expansion degree $n$ controls the truncation error of the Fourier
  series.
* The cut-off parameter $m$ of the NFFT controls the error of the NFFT.

The program supports two variants for the coefficients $b_l$. By default it
uses the values of the continuous Fourier transform as above. With the flag
`FGT_APPROX_B` it samples the Gaussian on a uniform grid with $n$ points and
takes the discrete Fourier coefficients of the samples.

### Parameters for a target accuracy

The function `fgt_init` chooses the parameters for a given accuracy
$\varepsilon$. It sets

$$
p = \max\Bigl\{1,\; \tfrac12 + \sqrt{-\ln\varepsilon / \operatorname{Re}\sigma}\Bigr\},
\qquad
n = 2 \Bigl\lceil \frac{p\,|\sigma|}{\pi}
\sqrt{-\ln\varepsilon / \operatorname{Re}\sigma} \Bigr\rceil,
$$

and $m = 7$. With this $p$, the absolute value of the Gaussian at the
wrap-around distance $p - \tfrac12$ is at most $\varepsilon$. With this $n$,
the exponential factor of $b_l$ at $|l| = n/2$ is at most $\varepsilon$.

## Flags

`DGT_PRE_CEXP`
:   The discrete Gauss transform precomputes and stores the whole matrix of
    exponentials. `fgt_init` sets this flag for $NM \le 2^{20}$.

`FGT_NDFT`
:   The fast transform uses the direct NFFT routines instead of the fast
    ones. This tests the fast transform against the definition of the NFFT.

`FGT_APPROX_B`
:   Use the discrete Fourier coefficients of the sampled Gaussian for $b_l$.

## Program

The program is `applications/fastgauss/fastgauss.c`. The build system
sets the precision macro of the configured precision on the compiler command
line. The code uses only the public header `nfft3mp.h`
and the [NFFT API](../api/nfft.md). All functions of the Gauss transform
(`fgt_init`, `fgt_init_guru`, `fgt_trafo`, `dgt_trafo` and others) are
`static` functions in the program and not a library.

The plan `fgt_plan` holds the numbers $N$ and $M$, the nodes `x` and `y`, the
coefficients `alpha`, the result `f`, the parameter `sigma`, the expansion
degree `n`, the period `p`, the coefficients `b` and two NFFT plans. The
program has these steps.

1. `fgt_init_guru` takes $N$, $M$, $\sigma$, $n$, $p$, $m$ and the flags. It
   allocates the arrays, creates the two NFFT plans with the oversampled
   bandwidth equal to the next power of two of $2n$, and computes $b_l$.
   `fgt_init` takes $N$, $M$, $\sigma$ and $\varepsilon$ instead and chooses
   $p$, $n$ and $m$ as above.
2. The program writes the nodes and the coefficients. Then
   `fgt_init_node_dependent` scales the nodes by $1/p$, hands them to the NFFT
   plans, precomputes the window values and, with `DGT_PRE_CEXP`, the matrix of
   exponentials.
3. `fgt_trafo` runs the fast transform. `dgt_trafo` runs the direct
   transform.
4. `fgt_finalize` frees the plan.

The coefficients $b_l$ for the default variant:

```c
--8<-- "applications/fastgauss/fastgauss.c:200:223"
```

The fast transform:

```c
--8<-- "applications/fastgauss/fastgauss.c:125:147"
```

### Build

The program is built with the other applications. The applications are on by
default, and `--enable-all` selects every module.

```bash
./configure --enable-all
make -j
cd applications/fastgauss
```

The CMake build has the option `NFFT_ENABLE_APPLICATIONS`, on by default, and
places the program in `build/applications/fastgauss/`. The program builds in
all precisions.

### Run

```bash
./fastgauss type
```

The argument `type` selects one of four tests. Without an argument the program
prints this list.

| `type` | Test |
|--------|------|
| 0 | Simple test. $N = M = 10$, $\sigma = 5 + 3\mathrm{i}$, accuracy $\varepsilon = 10^{-3}$. The program prints the discrete and the fast result and the relative error. |
| 1 | Accuracy and timing, similar to the test in Andersson and Beylkin. $\sigma = 4(138 + 100\mathrm{i})$, $n = 128$, $p = 1$, $N = M = 2^6, 2^7, \dots, 2^{21}$. The program prints one table row in LaTeX form for every $N$: the time of the direct transform, the time of the direct transform with precomputed exponentials for small $N$, the time of the fast transform with the direct NFFT, the time of the fast transform and the error. |
| 2 | Accuracy against the expansion degree. $N = M = 1000$, $\sigma = 4(138+100\mathrm{i})$, $p = 1$, $n = 8, 12, \dots, 128$, with $m = 7$ and $m = 3$. The program prints a MATLAB matrix `error` with the columns $n$, error for $m=7$, error for $m=3$. |
| 3 | Accuracy against the expansion degree and the period. $N = M = 1000$, $\sigma = 20 + 40\mathrm{i}$, $m = 7$, $n = 8, 12, \dots, 128$, $p \in \{1, 1.5, 2\}$. The program prints a MATLAB matrix `error` with the columns $n$ and the errors for the three periods. |

The error is $\|g_{\text{direct}} - g\|_\infty / \|\alpha\|_1$. The nodes are
uniformly random in $[-\tfrac14, \tfrac14]$ and the coefficients have random real
and imaginary parts in $[-\tfrac12, \tfrac12)$.

### MATLAB and Octave scripts

The output of types 2 and 3 is MATLAB code. Redirect it to
`output_error.m` for type 2 and to `output_error_p.m` for type 3. The
directory holds stored results with these names.

`show_results.m`
:   Runs `output_error` and `output_error_p` and plots the error curves
    together with theoretical error bounds. It prints the figures to
    `gauss1.eps`, `gauss2.eps` and `gauss6.eps`.

`levelplots.m`
:   Draws level lines of two error estimates over the complex plane of
    $\sigma$, with $\operatorname{Re}\sigma$ from 1 to 1500 and
    $\operatorname{Im}\sigma$ from $-1500$ to 1500. The estimates use
    $n = 128$ and $p = 1$.

The stored `output_error.m` and `output_error_p.m` come from an earlier version
of the tests. `output_error.m` has six error columns and the variable `delta`
for $\sigma$. A fresh output of type 2 has two error columns and the variable
`sigma`. `show_results.m` expects the stored format.

## References

* S. Kunis, D. Potts and G. Steidl. Fast Gauss transforms with complex
  parameters using NFFTs. J. Numer. Math., to appear, 2006.
* F. Andersson and G. Beylkin. The fast Gauss transform with complex
  parameters. J. Comput. Physics 203 (2005) 274-286.
