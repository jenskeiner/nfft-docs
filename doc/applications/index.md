# Applications

The directory `applications/` of the source tree holds programs that use the
library for a specific task. Each one shows how to apply a transform to a real
problem. Some of them reproduce the figures and tables of a publication.

| Application | Problem | Programs | Needs |
|-------------|---------|----------|-------|
| [Fast summation](fastsum.md) | Sums $\sum_k \alpha_k K(y_j - x_k)$ for radial kernels in $d$ dimensions with the [NFFT](../transforms/nfft.md). | `fastsum_test`, `fastsum_matlab` | NFFT |
| [Fast Gauss transform](fastgauss.md) | One-dimensional Gauss transform with a complex parameter, based on the NFFT. | `fastgauss` | NFFT |
| [Fast summation on the sphere](fastsumS2.md) | Sums of radial kernels on the sphere $\mathbb{S}^2$ with the [NFSFT](../transforms/nfsft.md). | `fastsumS2` | NFSFT |
| [MRI](mri.md) | Simulation and reconstruction of magnetic resonance imaging data from nonuniform $k$-space samples. The programs are described in [MRI 2D](mri-2d.md) and [MRI 3D](mri-3d.md). | in `mri/mri2d` and `mri/mri3d` | MRI |
| [Polar FFT](polarFFT.md) | Fourier transform on polar, modified polar and pseudopolar grids. | `polar_fft_test`, `mpolar_fft_test`, `linogram_fft_test` | NFFT |
| [Radon transform](radon.md) | Fast discrete NFFT-based Radon transform and its inverse. | `radon`, `inverse_radon` | NFFT |
| [Quadrature on the sphere](quadratureS2.md) | Fast evaluation of quadrature formulae on $\mathbb{S}^2$ with an adjoint NFSFT. | `quadratureS2` | NFSFT |
| [Inversion on the sphere](iterS2.md) | Iterative reconstruction of a bandlimited function on $\mathbb{S}^2$ from scattered samples. The application is not built. | `iterS2` | NFSFT |
| [Glacier reconstruction](glacier.md) | Reconstruction of a surface from scattered data with the [solver](../transforms/solver.md) and an NFFT. | `glacier` in `examples/solver` | NFFT |

## Build

The application programs are built by default. The option
`--enable-applications` switches them on explicitly and
`--enable-applications=no` switches them off. Some applications need a module
that is off by default:

* `--enable-nfsft` for the applications on the sphere,
* `--enable-mri` for the MRI programs.

The option `--enable-all` selects all modules and builds the applications.

```bash
./configure --enable-all
make -j
```

The CMake build has the option `NFFT_ENABLE_APPLICATIONS`, on by default. It
builds the programs for the modules that are on.

The programs are not installed. `make` builds them in the subdirectory of
`applications/` of the build tree, and the CMake build places them in
`build/applications/<name>/`. Run a program from this directory, because the
MATLAB and Octave scripts of an application call the program in the current
directory. The libraries of the applications, for example `libfastsum`, are
built next to the programs and are not installed either. The
[API reference](../api/index.md) covers only the public library.

## MATLAB and Octave scripts

The applications include scripts. They write the input of the program, call it
and read the results back. Several scripts reproduce figures and tables of the
publication that describes the application. Each application page names its
scripts.
