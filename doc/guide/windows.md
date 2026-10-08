# Windows

The [NFFT](../transforms/nfft.md) approximates the transform matrix by
$\mathbf{B}\,\mathbf{F}\,\mathbf{D}$. The window function $\varphi$ defines both
outer factors: $\mathbf{D}$ divides by its Fourier transform $\hat\varphi$, and
$\mathbf{B}$ weights the grid values with $\varphi$. NFFT3 offers five windows.
The build selects one. This page lists them, gives the formulas as the code
evaluates them, and shows the default cut-off and the shape parameter of each.

## Selecting the window

The window is fixed when the library is built. There is no run-time switch.

=== "Autotools"

    ```bash
    ./configure --with-window=kaiserbessel
    ```

=== "CMake"

    ```bash
    cmake -S . -B build -DNFFT_WINDOW=kaiserbessel
    ```

| Window | Autotools `--with-window=` | CMake `-DNFFT_WINDOW=` |
|--------|----------------------------|------------------------|
| Kaiser-Bessel, the default | `kaiserbessel` | `kaiserbessel` |
| Gaussian | `gaussian` | `gaussian` |
| B-spline | `bspline` | `bspline` |
| Sinc power | `sinc` | `sinc` |
| Dirac delta | `delta` | `dirac` |

!!! warning "The Dirac name differs between the build systems"

    The help text of `./configure` says `dirac`, but the `configure` script
    accepts only `delta`. `--with-window=dirac` stops with the message
    `Unknown window function`. CMake accepts `dirac`.

A second window needs a second configured tree, as a second precision does. See
[Build from source](../getting-started/build-from-source.md). The library reports
its window and default cut-off at run time:

```c
printf("%s, m = %ld\n", nfft_get_window_name(),
       (long) nfft_get_default_window_cut_off());
```

The string that `nfft_get_window_name` returns is the value the build system
put in `config.h`. Autotools gives `kaiserbessel`, `gaussian`, `bspline`, `sinc`
or `delta`. CMake gives a spelled-out name such as `Kaiser Bessel`.

## Parameters

Each window depends on the cut-off $m$ and on the oversampling factor
$\sigma_t=n_t/N_t$. The plan member `m` holds the cut-off. The plan member `b`
holds the shape parameters and the per-dimension constants of the window. The
plan init sets `b` from $m$ and $\sigma_t$.

The sparse matrix $\mathbf{B}$ has $(2m+2)^d$ entries per node. A larger $m$
lowers the truncation error and raises this work.

### Default cut-off

`nfft_init` sets `m` to the default of the window and the precision. The
default is a compile-time constant in `include/infft.h`.

| Window | Float | Double | Long double |
|--------|-------|--------|-------------|
| Kaiser-Bessel | 4 | 8 | 9 |
| Gaussian | 5 | 13 | 17 |
| B-spline | 11 | 11 | 11 |
| Sinc power | 11 | 11 | 13 |
| Dirac delta | 0 | 0 | 0 |

The stencil of one node holds $2m+2$ points per dimension. In double precision
this is 18 points for Kaiser-Bessel, 24 for B-spline and sinc power, and 28 for
the Gaussian. For $d=3$ these are 5832, 13 824 and 21 952 points per node.

### Shape parameter

The shape parameters below are what `init` computes. The symbols are the plan
members $\sigma_t$ and $m$.

| Window | Shape parameter for dimension $t$ |
|--------|-----------------------------------|
| Kaiser-Bessel | $b_t=\pi\bigl(2-\tfrac{1}{\sigma_t}\bigr)$ |
| Gaussian | $b_t=\dfrac{2\sigma_t}{2\sigma_t-1}\cdot\dfrac{m+1}{\pi}$ |
| B-spline | none |
| Sinc power | $w_t=\dfrac{2\sigma_t-1}{2m\sigma_t}$ |

The Gaussian entry uses the half-width $m+1$ of the stencil. The NFCT and NFST
modules place the stencil differently and use $m+\tfrac12$ instead.

## Definitions

Write $t=nx$ for the position in grid units, with $n=n_t$ the FFT length of the
dimension. The code evaluates the following functions. The $\mathbf{B}$ step
multiplies by $\varphi$, and the $\mathbf{D}$ step divides by $\hat\varphi$.

### Kaiser-Bessel

With the shape parameter $b$ from the table above, $I_0$ the modified Bessel
function of the first kind and $r=\sqrt{|m^2-t^2|}$,

$$
\varphi(x)=\frac{1}{I_0(mb)}\cdot
\begin{cases}
\dfrac{\sinh(b\,r)}{\pi\,r}, & |t|<m,\\
\dfrac{b}{\pi}, & |t|=m,\\
\dfrac{\sin(b\,r)}{\pi\,r}, & |t|>m,
\end{cases}
\qquad
\hat\varphi(k)=\frac{I_0\!\bigl(m\sqrt{b^2-(2\pi k/n)^2}\bigr)}{I_0(mb)}.
$$

The code divides by $I_0(mb)$ so that $\hat\varphi(0)=1$. The factor cancels
between $\mathbf{D}$ and $\mathbf{B}$. The code evaluates $I_0$ in scaled forms
that do not overflow for large $mb$. The coefficients of the scaled Bessel
functions are generated. See `kernel/util/bessel_i0_data.h`.

The stencil has $2m+2$ points. A point with $|t|>m$ can lie in it. There the
code uses the oscillating continuation $\sin(b\,r)/(\pi r)$, not zero.

### Gaussian

With the shape parameter $b$ from the table above,

$$
\varphi(x)=\frac{1}{\sqrt{\pi b}}\,\mathrm{e}^{-t^2/b},
\qquad
\hat\varphi(k)=\mathrm{e}^{-b\,(\pi k/n)^2}.
$$

The Gaussian has no compact support. The stencil truncates it. The Gaussian is
the only window that supports the flags `FG_PSI` and `PRE_FG_PSI`. See
[Plans and flags](plans-and-flags.md).

### B-spline

With $B_{2m}$ the cardinal B-spline of order $2m$, supported on $[0,2m]$,

$$
\varphi(x)=\frac{1}{n}\,B_{2m}(t+m),
\qquad
\hat\varphi(k)=\frac{1}{n}\left(\frac{\sin(\pi k/n)}{\pi k/n}\right)^{2m}.
$$

$\varphi$ has compact support $|t|\le m$. The library evaluates $B_{2m}$ with the
algorithm of de Boor and, for single points, with Chebyshev series.

### Sinc power

With $w=\dfrac{2\sigma-1}{2m\sigma}$ and $a=\pi n w x$,

$$
\varphi(x)=w\left(\frac{\sin a}{a}\right)^{2m},
\qquad
\hat\varphi(k)=B_{2m}\!\left(\frac{k}{wn}+m\right).
$$

This window is the counterpart of the B-spline window. $\hat\varphi$ is a
B-spline, and $\varphi$ is a power of the sinc function. $\hat\varphi$ vanishes
for $|k|\ge mwn=n-N/2$.

### Dirac delta

$\hat\varphi(k)=1$, and $\varphi(x)=1$ if $|x|<10^{-7}$ and $0$ otherwise. The
default cut-off is 0. The window is nonzero only next to a grid point, so the
transform is meaningful only for nodes that lie on the oversampled grid. The
test suite does not compile with this window, and the CI does not build it.

## Choosing a window

The default suits most uses. The differences between the windows follow from the
tables above.

| Window | Notes |
|--------|-------|
| Kaiser-Bessel | Smallest default stencil in every precision. The shape parameter depends only on $\sigma_t$. |
| Gaussian | Largest default stencil. The only window that allows the FG precomputation flags. |
| B-spline | $\varphi$ is exactly zero outside $|t|\le m$. No shape parameter. The default cut-off is the same in all precisions. |
| Sinc power | $\hat\varphi$ has compact support. Default cut-off 11, and 13 in long double. |

The accuracy that a window reaches depends on $m$, $\sigma$ and the precision.
[Accuracy](accuracy.md) lists the error estimates that the test suite checks for
each window.

The tests cover the window functions on their own. `tests/window.c` compares the
Kaiser-Bessel, B-spline and sinc-power evaluations with reference values. The
values of the B-spline and sinc-power tables come from `tests/windowref`. The
values for the Bessel function come from `tests/besselgen`. See
[Testing](../development/testing.md).

## API

[NFFT API reference](../api/nfft.md), `get_window_name` and
`get_default_window_cut_off`.
