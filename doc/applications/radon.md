# Radon transform

A fast discrete Radon transform and its inverse, based on the
[NFFT](../transforms/nfft.md). The Radon transform maps an image to its
projections along many directions. This map is the model of computerised
tomography. The programs in `applications/radon/` compute the transform and its
inverse. A MATLAB script uses them for image denoising with the discrete
ridgelet transform.

## The problem

The Fourier slice theorem connects the two transforms. The 1D Fourier transform
of the projection of an image along a direction is the 2D Fourier transform of
the image on a line through the origin in the same direction. The
[polar FFT](polarFFT.md) evaluates the 2D Fourier transform on such lines. A 1D
inverse FFT along every line then gives the projection.

Let $f_{\mathbf{k}}$, $\mathbf{k} \in I_N^2$, be a real $N \times N$ image. Let
$\mathbf{x}_{t,r}$ be the node with direction index $t \in I_T$ and offset index
$r \in I_R$ of the polar grid or of the linogram grid. The
[polar FFT page](polarFFT.md) defines both grids. The discrete Radon transform
is

$$
R_{t} f\!\left(\frac{s}{R}\right)
= \frac{1}{R}\,\mathrm{Re}\sum_{r \in I_R} w_r \sum_{\mathbf{k} \in I_N^2}
f_{\mathbf{k}}\,
{\rm e}^{-2\pi{\rm i}\,\mathbf{k}\mathbf{x}_{t,r}}\,
{\rm e}^{2\pi{\rm i}\, r s / R},
\qquad t \in I_T,\ s \in I_R .
$$

The inner sum is the 2D NFFT at the grid nodes. The outer sum is a 1D
inverse FFT for every direction $t$. The weights $w_r$ belong to a kernel.

Fejer kernel
:   $w_r = 1 - |r|/(R/2)$. The programs use this kernel. The macro `KERNEL` in
    the source defines it. The term $r = -R/2$ has the weight 0.

Dirichlet kernel
:   $w_r = 1$. The source contains this choice as a comment. To use it, change
    the macro `KERNEL` and rebuild.

The result is the sinogram: $T$ projections of $R$ values each.

## The inverse

The inverse transform reverses the two steps. For every direction, a 1D FFT of
the projection gives the values on the line, and a division by the kernel
$w_r$ removes the kernel. The value at $r = -R/2$ is set to 0 and gets the
weight 0. Then the program finds the image from the Fourier data on the grid.
It solves the weighted least squares problem

$$
f = \arg\min \sum_{t,r} \omega_{t,r}
\left| \sum_{\mathbf{k}} f_{\mathbf{k}}\,
{\rm e}^{-2\pi{\rm i}\,\mathbf{k}\mathbf{x}_{t,r}} - F_{t,r} \right|^2
$$

with CGNR from the [solver](../transforms/solver.md) module. Here $F_{t,r}$ is
the 1D FFT of the sinogram divided by the kernel, and $\omega_{t,r}$ are the
grid weights of the [polar FFT](polarFFT.md). The solver flags are `CGNR` and
`PRECOMPUTE_WEIGHT`. The iteration starts from zero. If the number of
iterations `max_i` is less than 1, the result is the first iterate, that is
the weighted adjoint. The program writes the real part.

## Programs

`radon`
:   Computes the sinogram of an image.

    ```
    ./radon gridfcn N T R
    ```

`inverse_radon`
:   Computes the image from a sinogram.

    ```
    ./inverse_radon gridfcn N T R max_i
    ```

| Argument | Meaning |
|----------|---------|
| `gridfcn` | `polar` or `linogram`. Any other string selects `linogram`. |
| `N` | The image size $N \times N$. |
| `T` | The number of directions. |
| `R` | The number of offsets. |
| `max_i` | The number of CGNR iterations of the inverse. |

Both programs use the NFFT with the oversampling factor $\sigma = 2$, that is
$n = 2N$ in both dimensions, and the cut-off $m = 4$.

Input and output
:   Both programs read and write binary files in the current directory. The
    numbers have the real type of the library, `double` in the default build.

    | Program | Reads | Writes |
    |---------|-------|--------|
    | `radon` | `input_data.bin`, $N^2$ values, one image row after the other | `sinogram_data.bin`, $T R$ values, the offsets of one direction one after the other |
    | `inverse_radon` | `sinogram_data.bin` | `output_data.bin`, $N^2$ values, one image row after the other |

Both programs return a nonzero exit status if a file cannot be opened.

The essential steps of `radon.c`: the NFFT at the grid nodes, then for every
direction the kernel weighting, the 1D inverse FFT and the scaling.

```c
--8<-- "applications/radon/radon.c.in:167:193"
```

The inverse: the 1D FFT and the division by the kernel for every direction, and
the CGNR iteration.

```c
--8<-- "applications/radon/inverse_radon.c.in:178:224"
```

## MATLAB and Octave scripts

The scripts call the executables with `system`, so start MATLAB or Octave in
the directory that holds them.

`radon.m`
:   Demonstration. It writes the phantom of $128 \times 128$ pixels to
    `input_data.bin`, runs `radon`, shows the sinogram, runs `inverse_radon`
    with 5 iterations and prints the maximum error of the reconstruction. The
    script uses the linogram grid with $T = R = 2N$. A commented line selects the
    polar grid with $T = 2.5N$ and $R = 1.5N$.

`ridgelet.m`
:   Denoising with the discrete ridgelet transform. The script adds noise to
    a test image and computes the sinogram with `radon`. It applies a
    translation-invariant discrete wavelet transform to every projection, sets
    the detail coefficients with an absolute value not above the threshold 17
    to zero, and transforms back. Then it writes the sinogram to
    `sinogram_data.bin`, runs `inverse_radon` and shows the reconstruction. The
    script needs the MATLAB toolbox WaveLab802 (D. Donoho et al.).

`phantom.m`
:   Creates the modified Shepp-Logan phantom of P. Toft as an $N \times N$
    matrix.

## Build and run

The programs need no optional module. The default configuration builds them.

```bash
./configure
make
```

`--disable-applications` switches the application programs off. The executables
`radon` and `inverse_radon` appear in `applications/radon/` of the build tree.
The source files are generated from `radon.c.in` and `inverse_radon.c.in`. They
use the public header `nfft3mp.h`, so they follow the precision of the library.
The MATLAB scripts read and write `double` values and work with the default
double precision.

## References

1. M. Fenn. Fast Fourier Transform at Nonequispaced Nodes and Applications. PhD
   Thesis, University of Mannheim, 2005.
2. J. Ma and M. Fenn. Combined complex ridgelet shrinkage and total variation
   minimization. SIAM J. Sci. Comput. 28, 984-1000, 2006.
3. D. Potts and G. Steidl. A new linogram algorithm for computerized
   tomography. IMA J. Numer. Anal. 21, 769-782, 2001.
4. D. Potts and G. Steidl. New Fourier reconstruction algorithms for
   computerized tomography. In: Proceedings of SPIE: Wavelet Applications in
   Signal and Image Processing VIII, A. Aldroubi, A.F. Laine, M.A. Unser
   (Eds.), Vol. 4119, pages 13-23, 2000.

## API

[NFFT](../transforms/nfft.md),
[Solver](../transforms/solver.md),
[NFFT API reference](../api/nfft.md)
