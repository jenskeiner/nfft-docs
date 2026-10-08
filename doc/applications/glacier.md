# Reconstruction of a glacier from scattered data

An example of the [solver](../transforms/solver.md) module. The program
reconstructs the surface of a glacier from height values at scattered points.
It interpolates the data with a bivariate trigonometric polynomial. The solver
finds the polynomial coefficients with the conjugate gradient method, and the
[NFFT](../transforms/nfft.md) applies the system matrix. The program is in
`examples/solver/`.

## The problem

The data set has $M = 8345$ samples $(\mathbf{x}_j, y_j)$, where
$\mathbf{x}_j \in [-\tfrac{1}{2},\tfrac{1}{2})^2$ is a point on a level curve
and $y_j$ is the height. The task is to find a trigonometric polynomial

$$
f(\mathbf{x}) = \sum_{\mathbf{k} \in I_N^2} \hat f_{\mathbf{k}}\,
{\rm e}^{-2\pi{\rm i}\,\mathbf{k}\mathbf{x}},
\qquad I_N^2 = \{\mathbf{k} \in \mathbb{Z}^2 : -N/2 \le k_t < N/2\},
$$

with $f(\mathbf{x}_j) = y_j$ for all $j$. The user chooses $N$ so that the number
of coefficients $N^2$ is larger than $M$. The system $\mathbf{A}\hat{\mathbf f} = \mathbf{y}$ is
underdetermined, so many polynomials interpolate the data. The program selects
the one with the smallest damped norm,

$$
\hat{\mathbf f} = \arg\min \sum_{\mathbf{k} \in I_N^2}
\frac{|\hat f_{\mathbf{k}}|^2}{\hat w_{\mathbf{k}}}
\quad \text{subject to} \quad \mathbf{A}\hat{\mathbf f} = \mathbf{y}.
$$

The solver computes it with CGNE, the conjugate gradient method on the normal
equations of the second kind. The damping factors $\hat w_{\mathbf{k}}$ are a
generalised Sobolev weight. They decay for large $|\mathbf{k}|$, so the
minimiser is smooth. In each dimension the weight is

$$
w(z; a, b, c) = \frac{\left(\tfrac{1}{4} - z^2\right)^{b}}{c + |z|^{2a}},
\qquad \hat w_{\mathbf{k}} = w\!\left(\frac{k_0}{N}; a, b, c\right)
w\!\left(\frac{k_1}{N}; a, b, c\right),
$$

with $a = \tfrac{1}{2}$, $b = 3$ and $c = 0.001$. The source calls this function
`my_weight`.

```c
--8<-- "examples/solver/glacier.c:33:37"
```

## The program `glacier`

```
./glacier N M
./glacier N M M_CV_START M_CV_STEP M_CV_END
```

With two arguments, `glacier` reconstructs the surface. With five arguments,
it runs a cross validation test.

| Argument | Meaning |
|----------|---------|
| `N` | The polynomial has $N \times N$ coefficients. |
| `M` | The number of samples. |
| `M_CV_START`, `M_CV_STEP`, `M_CV_END` | The range of the number of samples that the cross validation leaves out. |

Input
:   `input_data.dat` with $M$ lines `x y height`, separated by white space. The
    coordinates must lie in $[-\tfrac{1}{2},\tfrac{1}{2})^2$.

Output
:   The program writes the coefficients $\hat f_{\mathbf{k}}$ to `stdout`. There
    are $N^2$ lines `Re Im`. The residual norm of every iteration goes to
    `stderr`.

Method
:   The NFFT plan has the bandwidth $N \times N$, the cut-off $m = 6$ and the
    FFT length $n = $ the next power of 2 that is not less than $N$ in both
    dimensions. The flags are `PRE_PHI_HUT`, `PRE_FULL_PSI`, `FFTW_INIT` and
    `FFT_OUT_OF_PLACE`. The solver flags are `CGNE` and `PRECOMPUTE_DAMP`. The
    program starts from zero and runs 40 iterations.

```c
--8<-- "examples/solver/glacier.c:40:103"
```

### Cross validation

The cross validation leaves out $M_{\rm cv}$ of the samples. It reconstructs the
surface from the other $M - M_{\rm cv}$ samples and measures the error at the
samples that it left out. For every $M_{\rm cv}$ from the start to the end value
in steps of the step value, the program tests three variants.

1. CGNE with damping, size $N$.
2. CGNR without damping, size $N$.
3. CGNR without damping, size $N/4$.

Every variant prints two relative errors. The first is the residual at the
samples that were used. The second is the error at the samples that were left
out. Both are divided by the norm of all samples. The output on `stdout` is one
line of a LaTeX table for every $M_{\rm cv}$. The line has the form
`$M_cv$ & $r$ & $r_1$ & $r$ & $r_1$ & $r$ & $r_1$ & XXX \\`.

## Data and scripts

`vol87.dat`
:   The data set. The first line holds the header `3 8345 16`. Then follow the
    8345 lines `x y height` of the samples. The x and y values are in the
    original units, the height values are the level of the curve, for example
    1300. The README of the example refers to the data set of R. Franke.

`glacier.m`
:   Prepares the data, runs `glacier`, and plots the result. The script skips the
    header of `vol87.dat` and scales the coordinates to
    $[-\tfrac{1}{2} + \varepsilon, \tfrac{1}{2} - \varepsilon]$ with
    $\varepsilon = 0.1$. It writes `input_data.dat` and calls `glacier` with
    `N` and $M = 8345$. It reads `output_data.dat`, evaluates the polynomial on
    an equispaced grid with an FFT, and draws the surface (`glacier1.eps`) and
    the contour lines with the sample points (`glacier2.eps`). The plots omit a
    border of $\varepsilon N$ points. The script does not set `N`. Set `N` in
    the MATLAB or Octave workspace before you run it.

`glacier_cv.m`
:   Cross validation. The script shuffles the samples, writes
    `input_data.dat`, and runs `glacier` with the range 200, 200, 1000 for
    the cross validation. The result goes to `output_data_cv.tex`. Set `N` before
    you run the script.

## Build and run

The solver module and the NFFT are always built. The example needs no optional
module. The default configuration builds it.

```bash
./configure
make
```

`--disable-examples` switches all examples off. The executable is
`examples/solver/glacier` in the build tree. It is built from `glacier.c`.
The source uses the public
header `nfft3mp.h`, so it follows the precision of the library. To run it, change
to `examples/solver/`, start MATLAB or Octave, set `N` in the workspace and run
`glacier.m`. The script calls `./glacier` in the current directory.

## Reference

S. Kunis and D. Potts. Stability Results for Scattered Data Interpolation by
Trigonometric Polynomials. SIAM J. Sci. Comput. 29, 1403 - 1419, 2007.

## API

[Solver](../transforms/solver.md),
[NFFT](../transforms/nfft.md),
[Solver API reference](../api/solver.md)
