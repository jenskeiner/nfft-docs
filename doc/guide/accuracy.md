# Accuracy

The fast transforms approximate the direct sums. This page explains what limits
the error, shows how to measure it for your own parameters, and points to the
test suite and to the published accuracy report. The error bounds below are the
ones the test suite asserts. They are not guarantees for other inputs.

## What limits the accuracy

Two sources of error act on the NFFT.

**Truncation of the window.** The [window](windows.md) is cut to $2m+2$ grid
points per dimension. This error depends on the window, on the cut-off $m$ and
on the oversampling factor $\sigma$. It falls as $m$ or $\sigma$ grows. A larger
$m$ costs $(2m+2)^d$ work per node. A larger $\sigma$ costs a longer FFT. See
[Plans and flags](plans-and-flags.md).

**Round-off.** Every step works in the precision of the build, and the error
cannot fall below it. The [precision](precision.md) sets the machine epsilon
$\varepsilon$. The direct transform has round-off only. It is the reference for
the fast transform.

`nfft_init` uses a default cut-off for each window and precision, see
[Windows](windows.md). With a smaller $m$ the truncation error shows. No choice
of $m$ or $\sigma$ brings the error below the round-off level.

The order of operations matters at the level of round-off. The OpenMP adjoint
with atomic additions can differ in the last digits from run to run. See
[OpenMP](openmp.md).

## Measuring the error

Compute the same transform with the direct and the fast function and compare.
The direct transform costs $\mathcal{O}(|I_{\mathbf N}|M)$ operations, so use
moderate sizes.

The public utility functions compute two error norms of complex vectors. In both,
`x` is the reference.

| Function | Value |
|----------|-------|
| `nfft_error_l_infty_complex(x, y, n)` | $\displaystyle\frac{\max_j\lvert x_j-y_j\rvert}{\max_j\lvert x_j\rvert}$ |
| `nfft_error_l_infty_1_complex(x, y, n, z, m)` | $\displaystyle\frac{\max_j\lvert x_j-y_j\rvert}{\sum_{k}\lvert z_k\rvert}$ with $k=0,\dots,m-1$ |

Each function has a `nfftf_` and a `nfftl_` form. The test suite uses the second
norm. For the forward transform `z` is `f_hat`. For the adjoint transform `z` is
`f`. The tests bound this measure by a value that does not contain $N$ or $M$.

```c
#define NFFT_PRECISION_DOUBLE
#include "nfft3mp.h"

NFFT(plan) p;
NFFT_C *f_direct = NFFT(malloc)((size_t)M * sizeof(NFFT_C));

NFFT(init_1d)(&p, N, M);
/* set p.x and p.f_hat, then call precompute_one_psi if flags & PRE_ONE_PSI */

NFFT(trafo_direct)(&p);
memcpy(f_direct, p.f, (size_t)M * sizeof(NFFT_C));

NFFT(trafo)(&p);
err = NFFT(error_l_infty_1_complex)(f_direct, p.f, M, p.f_hat, p.N_total);
```

The programs `examples/nnfft/accuracy.c`, `examples/nfsoft/simple_test.c` and
`examples/nsfft/nsfft_test.c` use the same functions for other modules.

## The bounds in the test suite

The CUnit suites for the NFFT, NFCT and NFST compute the error measure above for
each case and compare it with a bound. A case passes when the error is smaller
than the bound.

| Transform | Bound |
|-----------|-------|
| Direct | $C\,\varepsilon$ with $C=56$ for the NFFT, 120 for the NFCT and 130 for the NFST. |
| Fast, NFFT | $\max\bigl(a\,E,\; b\,\varepsilon,\; 56\,\varepsilon\bigr)$ |

$\varepsilon$ is the machine epsilon of the build precision. The constants $a$
and $b$ are set in `tests/nfft.c` for each window and each mantissa length: 24
bits for float, 53 for double, 64 for Intel long double and 113 for quadruple
precision. The constants for 113 bits are not tuned. $E$ is the analytic
truncation estimate of the window. With $s$ the smallest oversampling factor of
the plan, the test code uses these estimates:

| Window | Estimate $E$ |
|--------|--------------|
| Kaiser-Bessel | $\pi\,(\sqrt m+m)\,2^{-1/4}\,\mathrm{e}^{-\pi\sqrt2\,m}$ |
| Gaussian | $\mathrm{e}^{-2\pi m/3}$ |
| B-spline | $12000\,(2s-1)^{-2m}$ |
| Sinc power | $\dfrac{1}{m-1}\left(\dfrac{2}{s^{2m}}+\left(\dfrac{s}{2s-1}\right)^{2m}\right)$ |

The Kaiser-Bessel and Gaussian estimates fix $\sigma=2$. The suite also runs
the Gaussian window with small fixed $m$, where the truncation error shows above
the round-off level. There it asserts the larger of the bound above and
$4\,\mathrm{e}^{-\pi m(1-1/(2\sigma-1))}$ at $\sigma=2$.

The bound does not contain $N$ or $M$. Two kinds of check give the reference:

- **File-based.** A stored high-precision result. It validates the direct
  transform and the fast transform on small sizes.
- **Online.** A random input, with the direct transform as the reference. It
  validates the fast transform on larger sizes.

[Testing](../development/testing.md) describes both, and how to run the suite.

## The accuracy report

The test run records every error and bound. CI turns them into an HTML report
with one table per module. A cell shows the correct digits beyond the bound of
its case. Red means an error above the bound. The report does not decide whether
a build passes. The C test decides.

The report for the `develop` branch is at
`https://nfft.github.io/nfft/accuracy/`. Pull requests from the repository get their
own report and a comment with the changes against `develop`. The
[Testing](../development/testing.md) page explains how to produce the report
locally.
