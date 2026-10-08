# Polar FFT

Fast Fourier transforms on the polar grid, the modified polar grid and the
pseudo-polar (linogram) grid. Each transform evaluates the two-dimensional
Fourier transform of an $N \times N$ array at nodes on lines through the origin.
The [NFFT](../transforms/nfft.md) computes it fast. The [solver](../transforms/solver.md)
module computes the inverse. The programs in `applications/polarFFT/` test the
accuracy of both directions.

The polar FFT is the basis of the [Radon transform](radon.md) in this
repository.

## The problem

Let $I_N^2 = \{\mathbf{k} \in \mathbb{Z}^2 : -N/2 \le k_t < N/2\}$ index the
array $\hat f_{\mathbf{k}}$. For a set of nodes
$\mathbf{x}_{t,j} \in [-\tfrac{1}{2},\tfrac{1}{2})^2$, the transform computes

$$
f_{t,j} = \sum_{\mathbf{k} \in I_N^2} \hat f_{\mathbf{k}}\,
{\rm e}^{-2\pi{\rm i}\,\mathbf{k}\mathbf{x}_{t,j}}.
$$

This is the NFFT with a special node set. The inverse problem is to find
$\hat f$ from the values $f_{t,j}$. The programs solve it in the weighted least
squares sense,

$$
\hat{\mathbf f} = \arg\min \sum_{t,j} w_{t,j}
\left| \sum_{\mathbf{k}} \hat f_{\mathbf{k}}\,
{\rm e}^{-2\pi{\rm i}\,\mathbf{k}\mathbf{x}_{t,j}} - f_{t,j} \right|^2 ,
$$

with CGNR. The weights $w_{t,j}$ compensate for the varying density of the
nodes.

## The grids

Every grid has $T$ directions and $R$ offsets. The offset index $j$ and the
direction index $t$ run over
$I_R = \{-R/2, \dots, R/2-1\}$ and $I_T = \{-T/2, \dots, T/2-1\}$. The array
size $N$ is independent of $T$ and $R$. The test scripts use $T = 3N$ and
$R = 3N/2$.

### Polar grid

The nodes lie on concentric circles around the origin. For
$(j,t) \in I_R \times I_T$, the signed radius is
$r_j := j/R \in [-\tfrac{1}{2},\tfrac{1}{2})$ and the angle is
$\theta_t := \pi t/T \in [-\tfrac{\pi}{2},\tfrac{\pi}{2})$. The nodes are

$$
\mathbf{x}_{t,j} := r_j \left(\cos\theta_t, \sin\theta_t\right)^{\top}.
$$

The number of nodes is $M = TR$. The origin is included $T$ times.

The weights compensate for the local density. The program associates a small
area with every node. In the polar grid these areas are ring segments. The area
of the segment around $\mathbf{x}_{t,j}$ with $j \ne 0$ is

$$
w_{t,j}
= \frac{\pi}{2TR^2}\left(\left(|j|+\frac{1}{2}\right)^2-
\left(|j|-\frac{1}{2}\right)^2\right)
= \frac{\pi |j| }{TR^2}.
$$

The area of the small circle of radius $\frac{1}{2R}$ around the origin is
$\frac{\pi}{4R^2}$. The program divides it by the multiplicity $T$ of the
origin and gets $w_{t,0} := \frac{\pi}{4TR^2}$. The sum of all weights is
$\frac{\pi}{4}(1+\frac{1}{R^2})$. The program divides every weight by this sum,
so the normalised weights sum to 1. In the source the normalised weights are
$|j|/W$ for $j \ne 0$ and $1/(4W)$ for $j = 0$, with
$W = T\,((R/2)^2 + 1/4)$.

```c
--8<-- "applications/polarFFT/polar_fft_test.c.in:73:92"
```

### Modified polar grid

The modified polar grid has more concentric circles than the polar grid. It
drops the nodes that are not in the unit square. The nodes are

$$
\mathbf{x}_{t,j} := r_j \left(\cos\theta_t, \sin\theta_t\right)^{\top},
\qquad (j,t)^{\top} \in I_{\sqrt{2}R} \times I_T ,
$$

with $r_j$ and $\theta_t$ as for the polar grid. In the program the offset
index runs over $-R_2/2, \dots, R_2/2-1$ with
$R_2 = 2\lceil \sqrt{2}\,R/2 \rceil$. The program keeps a node if both
coordinates lie in $[-\tfrac{1}{2} - \tfrac{1}{R}, \tfrac{1}{2} + \tfrac{1}{R}]$.
The number of nodes is about
$M \approx \frac{4}{\pi}\log(1+\sqrt{2})\,T R$. The weights are $|j|$ for
$j \ne 0$ and $1/4$ for $j = 0$, divided by their sum.

```c
--8<-- "applications/polarFFT/mpolar_fft_test.c.in:58:99"
```

### Linogram grid

The linogram grid is also called the pseudo-polar grid. The nodes lie on $T$
lines through the origin. The slopes of the lines are equispaced, not the
angles. For $t < 0$ the nodes are

$$
\mathbf{x}_{t,j} = r_j \left(1, \frac{4t}{T} + 1\right)^{\top},
$$

and for $t \ge 0$

$$
\mathbf{x}_{t,j} = r_j \left(1 - \frac{4t}{T}, 1\right)^{\top},
$$

with $r_j = j/R$. On every line the nodes are equispaced in the coordinate along
the main axis. The number of nodes is $M = TR$. The weights are those of the
polar grid.

```c
--8<-- "applications/polarFFT/linogram_fft_test.c.in:47:76"
```

## Method

The programs compute the transform in three ways.

Direct
:   `nfft_trafo_direct` evaluates the sum as written. This is the reference.

Fast
:   `nfft_trafo` with the oversampling factor $\sigma = 2$, that is $n = 2N$ in
    both dimensions, and the cut-off $m$ as a parameter. The flags are
    `PRE_PHI_HUT`, `PRE_PSI`, `FFTW_INIT` and `FFT_OUT_OF_PLACE`.

Inverse
:   The solver flags are `CGNR` and `PRECOMPUTE_WEIGHT`. The weights are the
    grid weights above. The iteration starts from zero. `max_i` is the number of
    iterations. If `max_i` is less than 1, the result is the first iterate, the
    weighted adjoint $\hat f = \mathbf{A}^{\mathsf H}\mathbf{W} f$.

The three programs have the same structure. The function names carry the grid
name, for example `polar_grid`, `polar_dft`, `polar_fft` and `inverse_polar_fft`.

```c
--8<-- "applications/polarFFT/polar_fft_test.c.in:176:209"
```

## Programs

The three programs are `polar_fft_test`, `mpolar_fft_test` and
`linogram_fft_test`. They use the same command line.

```
./polar_fft_test N T R
./mpolar_fft_test N T R
./linogram_fft_test N T R
```

| Argument | Meaning |
|----------|---------|
| `N` | The array size $N \times N$. |
| `T` | The number of directions. |
| `R` | The number of offsets. |

Input
:   `input_data_r.dat` and `input_data_i.dat`. The files hold the real and the
    imaginary parts of the $N^2$ values $\hat f_{\mathbf{k}}$, in text format.

Test
:   Every program runs two tests. All errors are relative errors in the maximum
    norm, $\|x - y\|_\infty / \|x\|_\infty$.

    1. The fast transform with $m = 1, \dots, 12$ against the direct transform.
       The error for every $m$ goes to `polar_fft_error.dat`. The 12 values are
       one per line.
    2. The inverse of the direct result for $m = 3, 6, 9$ against $\hat f$, for
       an increasing number of iterations. The errors go to
       `polar_ifft_error3.dat`, `polar_ifft_error6.dat` and
       `polar_ifft_error9.dat`. The programs run 0 to 100 iterations in steps of
       10 for the polar grid, and 0 to 20 iterations in steps of 2 for the
       modified polar and the linogram grid. Each file has 11 lines.

Output
:   The programs print the same numbers to the terminal. The files for the
    other grids are `mpolar_fft_error.dat`, `mpolar_ifft_error{3,6,9}.dat`,
    `linogram_fft_error.dat` and `linogram_ifft_error{3,6,9}.dat`.

`mpolar_fft_test` and `linogram_fft_test` run in a second mode when the number
of arguments is not 3. They print the usage. Then they compare the run time of
FFTW, of the fast transform and of the inverse transform for
$N = 2^4, \dots, 2^8$ with $T = 3N$ and $R = 3N/2$. The result goes to
`mpolar_comparison_fft.dat` or `linogram_comparison_fft.dat` in a form that can
be pasted into a LaTeX table. The programs exit with an error status after this
comparison.

## MATLAB and Octave scripts

`fft_test.m`
:   Demonstration. It creates the input files from `fft2(phantom(N))`, runs the
    three programs with $T = 3N$ and $R = 3N/2$, reads the error files and plots
    the errors. The plots show the error of the fast transform against $m$ and
    the error of the inverse transform against the number of iterations.

`phantom.m`
:   Creates the modified Shepp-Logan phantom of Toft as an $N \times N$ matrix.

## Build and run

The programs are built with the default configuration. They need no optional
module. They use the public header `nfft3mp.h` and the precision of the
library.

```bash
./configure
make
```

`--disable-applications` switches the application programs off. The executables
appear in `applications/polarFFT/` of the build tree. To run the demonstration,
change to this directory and run `fft_test.m` in MATLAB or Octave. The programs
read their input from the current directory.

## References

1. M. Fenn, S. Kunis, and D. Potts. On the computation of the polar FFT. Appl.
   Comput. Harmon. Anal., accepted.
2. D. Potts and G. Steidl. A new linogram algorithm for computerized
   tomography. IMA J. Numer. Anal. 21, 769-782, 2001.

## API

[NFFT](../transforms/nfft.md),
[Solver](../transforms/solver.md),
[NFFT API reference](../api/nfft.md)
