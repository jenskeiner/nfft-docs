# Quadrature on the sphere

Fast evaluation of quadrature formulae on the sphere $\mathbb{S}^2$. A
quadrature formula with nodes $\boldsymbol{\xi}_d \in \mathbb{S}^2$ and weights
$w_d$ approximates an integral by

$$
\int_{\mathbb{S}^2} f(\boldsymbol{\xi})\, \mathrm{d}\boldsymbol{\xi}
\approx \sum_{d=0}^{D-1} w_d\, f(\boldsymbol{\xi}_d).
$$

The program applies such a formula to compute the spherical Fourier
coefficients of a function $f$ from its values on the nodes, and it measures how
well the formula does this. The computation is an adjoint
[NFSFT](../transforms/nfsft.md), which is fast for every node set.

## Method

Let $Y_k^n$ be the orthonormal spherical harmonics. The spherical Fourier
coefficients of $f$ are $\hat f_k^n = \langle f, Y_k^n \rangle$. The quadrature
formula gives the approximation

$$
\hat f_k^n \approx \sum_{d=0}^{D-1} w_d\, f(\boldsymbol{\xi}_d)\,
\overline{Y_k^n(\boldsymbol{\xi}_d)},
\qquad k = 0,\dots,N,\quad n = -k,\dots,k.
$$

The right side is the adjoint NDSFT applied to the weighted function values
$w_d f(\boldsymbol{\xi}_d)$. If the formula is exact for spherical polynomials
up to degree $2N$, the result is exact for every function of bandwidth $N$.

The program then evaluates the finite expansion

$$
f_N(\boldsymbol{\zeta}) = \sum_{k=0}^{N} \sum_{n=-k}^{k}
\hat f_k^n\, Y_k^n(\boldsymbol{\zeta})
$$

at test nodes $\boldsymbol{\zeta}$ with an NFSFT and compares $f_N$ with $f$.
The error measures the quality of the formula for the chosen function.

The test steps are:

1. Sample $f$ on the grid and multiply the values by the weights.
2. Adjoint NFSFT of bandwidth $N$ with the orthonormal basis, flag
   `NFSFT_NORMALIZED`.
3. NFSFT of the coefficients at the test nodes.
4. Compare with the exact values of $f$.

The errors are

$$
E_\infty = \frac{\|f_N - f\|_\infty}{\|f_N\|_\infty},
\qquad
E_2 = \frac{\|f_N - f\|_2}{\|f_N\|_2},
$$

with the norms taken over the test nodes.

## Grids

The program has five node sets. The parameter $S$ is the grid size
parameter.

| Number | Grid | Nodes | Weights |
|--------|------|-------|---------|
| 0 | Gauss-Legendre | $(S+1)(2S+2)$. $S+1$ Gauss-Legendre nodes in $\cos\vartheta$, $2S+2$ equispaced longitudes. | Gauss-Legendre weights, read from the input. |
| 1 | Clenshaw-Curtis | $(2S+1)(2S+2)$. Colatitudes $\vartheta_k = k\pi/(2S)$, $2S+2$ equispaced longitudes. | Clenshaw-Curtis weights, computed by the program. |
| 2 | HEALPix | $12S^2$. $S$ is the parameter $N_{\text{side}}$. | Equal, $4\pi/(12S^2)$. |
| 3 | Equidistribution | Both poles and rings at $\vartheta_k = k\pi/S$, $k = 1,\dots,S-1$. The number of nodes on a ring is chosen so that neighbouring nodes on the ring have a distance of about $\pi/S$. | Clenshaw-Curtis type ring weights, divided by the number of nodes on the ring. |
| 4 | Equidistribution, uniform weights | The same nodes as grid 3. | Equal, $4\pi$ divided by the number of nodes. |

## Test functions

The test functions use the Cartesian coordinates
$(x_1, x_2, x_3) = (\sin\vartheta\cos\varphi, \sin\vartheta\sin\varphi, \cos\vartheta)$
of the node.

| Number | Function |
|--------|----------|
| 0 | Random function of bandwidth `bandlimit`. The coefficients have random real and imaginary parts in $[-\tfrac12,\tfrac12]$. |
| 1 | $x_1 x_2 x_3$ |
| 2 | $0.1\,\mathrm{e}^{x_1+x_2+x_3}$ |
| 3 | $0.1\,(\lvert x_1\rvert + \lvert x_2\rvert + \lvert x_3\rvert)$ |
| 4 | $1/(\lvert x_1\rvert + \lvert x_2\rvert + \lvert x_3\rvert)$ |
| 5 | $0.1\,\sin^2(1 + \lvert x_1\rvert + \lvert x_2\rvert + \lvert x_3\rvert)$ |
| 6 | $1$ for $\vartheta \le \pi/2$, and $1/\sqrt{1 + 3\cos^2\vartheta}$ otherwise |
| other | $1$ |

## Program

The directory `applications/quadratureS2/` has one program, `quadratureS2`, and
MATLAB and Octave scripts. The program calls the
[NFSFT API](../api/nfsft.md). It reads its input from the standard input and
writes its output to the standard output.

### Build

The program needs the NFSFT module and the double precision library. The
applications are built by default. The NFSFT module is off by default.

```bash
./configure --enable-nfsft --enable-applications
make -j
cd applications/quadratureS2
```

`--enable-all` includes the NFSFT module. The CMake build builds the program
when the NFSFT module is on, with `NFFT_ENABLE_APPLICATIONS` on by default,
and places it in `build/applications/quadratureS2/`.

### Run

```bash
./quadratureS2 < example.in > example.out
```

The file `example.in` is an example input and `example.out` the output of the
program for it. The example has three test cases with the Gauss-Legendre grid
and the test function 1. The bandwidths and grid sizes are $(N,S) = (16,16)$
and $(32,32)$. The first two test cases use the NFSFT with the NFFT
cut-off parameter 3 and 6. The third one uses the direct NDSFT.

### Input

The input consists of one or more test cases. Every parameter is a line
`name=value`. The first line is `testcases=`, the number of test cases. Each test
case has the parameters in the order of the table. Parameters marked with an
asterisk are extra parameters. The program reads them only in the stated case.

| Parameter | Meaning |
|-----------|---------|
| `nfsft` | `1`: use the NFSFT. `0`: use the direct NDSFT. |
| `nfft`* | `1`: the NFSFT uses the NFFT. `0`: the NFSFT uses the direct NDFT. Read if `nfsft=1`. |
| `cutoff`* | Integer $> 0$, the NFFT cut-off parameter. Read if `nfft=1`. |
| `fpt`* | `1`: the NFSFT uses the FPT. `0`: the NFSFT uses the direct polynomial transform. Read if `nfsft=1`. |
| `threshold`* | Floating point number $> 0$, the FPT threshold parameter. Read if `fpt=1`. |
| `testmode` | `0`: error test. `1`: timing test. |
| `gridtype`* | Grid number from the [grid table](#grids). Read if `testmode=0`. |
| `testfunction`* | Function number from the [function table](#test-functions). Read if `testmode=0`. |
| `bandlimit`* | The bandwidth of the random function. Read if `testfunction=0`. |
| `repetitions`* | Use 1. The program runs the test once and divides the time and the errors by this number. Read if `testmode=0`. |
| `mode`* | `0`: evaluate at the grid nodes. `1`: evaluate at random nodes. Read if `testmode=0`. |
| `points`* | Number of random evaluation nodes. Read if `mode=1`. |
| `bandwidths` | Number of test runs. Lines with the parameters of each run follow. |

Each line after `bandwidths=` has the parameters of one run.

* In the error test, the line has two integers: the bandwidth $N$ and the grid
  size parameter $S$.
* In the timing test, the line has three integers: the bandwidth $N$, the
  number $S$ of random nodes and the number of repetitions of the adjoint
  transform.

For the Gauss-Legendre grid, the input then holds the weights and the nodes for
every run. For each run in the order of the lines, it has $S+1$ Gauss-Legendre
weights and $S+1$ values $\vartheta_k/(2\pi)$, where $\vartheta_k$ are the
Gauss-Legendre colatitudes. The MATLAB function `writeWeights.m` writes them.
The function `writeTestcase.m` writes a complete test case, with the weights
for the grid 0.

### Output

The program writes all input values without their names, then the results.
It writes one result line for each run.

* Error test: `time E_inf E_2`. The time is in seconds. It is the time of the
  multiplication with the weights, the adjoint transform and the transform.
* Timing test: the average time in seconds of the adjoint transform.

The program also prints progress lines to the standard error output.

### MATLAB and Octave scripts

`quadratureS2.m`
:   A menu selects one of the figures 6.1 (a), 6.1 (b), 6.2 (a) and 6.2 (b) of
    [1]. The script writes `data.in`, calls `./quadratureS2 < data.in >
    data.out`, reads the result and draws the figure. Run it in the directory
    with the program.

`writeTestcase.m`, `writeWeights.m`, `readTestcase.m`
:   Write a test case, write the Gauss-Legendre weights and nodes, and read
    the results of a run.

`lgwt.m`
:   Computes the Legendre-Gauss nodes and weights on an interval.

`plotGrid.m`
:   `plotGrid(gridType, p)` plots a quadrature grid. The values 0 to 3 of
    `gridType` select the Gauss-Legendre grid, the Clenshaw-Curtis grid, the
    HEALPix point set and the equidistribution point set.

## Example

The program multiplies the function values on the grid with the weights of
their ring. The weight `w[k]` belongs to the colatitude with index `k`.

```c
--8<-- "applications/quadratureS2/quadratureS2.c:990:1001"
```

The adjoint transform gives the Fourier coefficients:

```c
--8<-- "applications/quadratureS2/quadratureS2.c:1021:1030"
```

The transform evaluates the expansion at the test nodes:

```c
--8<-- "applications/quadratureS2/quadratureS2.c:1045:1054"
```

## References

1. J. Keiner and D. Potts. Fast evaluation of quadrature formulae on the
   sphere. Math. Comp. 77 (2008), 397-419.
