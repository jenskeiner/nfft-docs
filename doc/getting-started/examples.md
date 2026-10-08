# Examples

The directory `examples/` holds small programs that show how to use each
module. Every module has a `simple_test` program that is a good starting point.
Some directories hold more programs, for example timing and accuracy tests. The
[first transform](first-transform.md) page walks through `examples/nfft/simple_test.c`.

## Build and run

The examples are built by default, together with the library. A module must be
enabled to build its examples. The `--enable-all` option enables every module.
See [Build from source](build-from-source.md) for the options.

```bash
./configure --enable-all
make
```

The programs are not installed. They stay in `examples/<module>/` of the build
tree. Run a program from that directory, for example

```bash
cd examples/nfft
./simple_test
```

`--disable-examples` switches all examples off. To build only the examples of
one module, run `make` in its directory.

The programs are compiled in the precision of the library. The NFFT, NFCT, NFST
and solver examples work in all three precisions. The examples of the other
modules need double precision, because those modules exist only in double
precision.

## NFFT

Directory `examples/nfft/`. Needs no module option. See the
[NFFT](../transforms/nfft.md) page.

| Program | Task |
|---------|------|
| `simple_test` | Introduction. Computes a 1D and a 2D NDFT, NFFT and adjoint NFFT and prints the results and the run times. |
| `simple_test_threads` | The same with the OpenMP library and a large problem. It prints the number of threads and the run time. Only with `--enable-openmp`. |
| `flags` | Compares the precomputation strategies of the NFFT. Arguments: `type first last trials d m`. Type 1 measures the accuracy against the run time. Type 2 measures the accuracy against the table size $K$ of the linear interpolation. Types 0 and 1 need `--enable-measure-time`. |
| `ndft_fast` | Compares the NDFT, an NDFT with Horner scheme and a fully precomputed NDFT with the NFFT. Arguments: `type first last trials`. |
| `nfft_times` | Compares the run times of NFFTs and FFTs in 1, 2 and 3 dimensions. It prints a LaTeX table. |
| `taylor_nfft` | Compares the NFFT with an NFFT based on a Taylor expansion. Arguments: `type first last trials sigma_nfft sigma_taylor`. |
| `nfft_benchomp` | Benchmark of the OpenMP code. It runs `nfft_benchomp_createdataset` and `nfft_benchomp_detail_single` and `nfft_benchomp_detail_threads` and writes the result as pgfplots data to `nfft_benchomp_results_plots.tex`. Only with `--enable-openmp`. For a detailed measurement, configure also with `--enable-measure-time --enable-measure-time-fftw`. |

The MATLAB scripts `flags.m`, `ndft_fast.m` and `taylor_nfft.m` show the results.
`flags.m` reads data files that the program `flags` wrote earlier. `ndft_fast.m`
and `taylor_nfft.m` call the executables.

Reference: S. Kunis and D. Potts. Time and memory requirements of the
nonequispaced FFT. Preprint 2006-1, Chemnitz University of Technology, Faculty
of Mathematics.

## NFCT and NFST

Directories `examples/nfct/` and `examples/nfst/`. Need `--enable-nfct` and
`--enable-nfst`. See the [NFCT](../transforms/nfct.md) and
[NFST](../transforms/nfst.md) pages.

| Program | Task |
|---------|------|
| `nfct/simple_test` | Computes a 1D NDCT, NFCT, adjoint NDCT and adjoint NFCT. |
| `nfst/simple_test` | Computes a 1D NDST, NFST, adjoint NDST and adjoint NFST. |

Reference: M. Fenn and D. Potts. Fast summation based on fast trigonometric
transforms at nonequispaced nodes. Numer. Linear Algebra Appl., 12:161-169,
2005.

## NNFFT

Directory `examples/nnfft/`. Needs `--enable-nnfft`. See the
[NNFFT](../transforms/nnfft.md) page.

| Program | Task |
|---------|------|
| `simple_test` | Computes a 1D NNDFT and NNFFT and prints the results. The source also holds the adjoint transform, the 2D transform, a 1D inverse NNFFT and a run time test. They are commented out in `main`. |
| `accuracy` | Measures the accuracy of the NNFFT in 1, 2 and 3 dimensions for the cut-off $m = 0, \dots, 9$. `accuracy.m` shows the result. |

Reference: D. Potts, G. Steidl, and M. Tasche. Fast Fourier transforms for
nonequispaced data: A tutorial. In: Modern Sampling Theory: Mathematics and
Applications, J.J. Benedetto and P. Ferreira (Eds.), Chapter 12, pages 249-274,
1998.

## NSFFT

Directory `examples/nsfft/`. Needs `--enable-nsfft`. See the
[NSFFT](../transforms/nsfft.md) page.

| Program | Task |
|---------|------|
| `simple_test` | Computes a 2D and a 3D NSDFT and NSFFT, and their adjoints. |
| `nsfft_test` | Tests the NSFFT on the hyperbolic cross. Arguments: `type d [first last trials]`. Type 1 tests the accuracy of the NSFFT against the NSDFT. Type 2 tests the run time of the NSDFT, the NFFT and the NSFFT. |

Reference: M. Fenn, S. Kunis, and D. Potts. Fast evaluation of trigonometric
polynomials from hyperbolic crosses.

## NFSFT

Directory `examples/nfsft/`. Needs `--enable-nfsft`. See the
[NFSFT](../transforms/nfsft.md) page.

| Program | Task |
|---------|------|
| `simple_test` | Computes an NDSFT, an NFSFT, an adjoint NDSFT and an adjoint NFSFT for a small example. |
| `simple_test_threads` | The same with the OpenMP library. It prints the number of threads. Only with `--enable-openmp`. |
| `nfsft_benchomp` | Benchmark of the OpenMP code. It runs `nfsft_benchomp_createdataset`, `nfsft_benchomp_detail_single` and `nfsft_benchomp_detail_threads` and writes pgfplots data. Only with `--enable-openmp`. For a detailed measurement, configure also with `--enable-measure-time --enable-measure-time-fftw`. |

## NFSOFT

Directory `examples/nfsoft/`. Needs `--enable-nfsoft`. See the
[NFSOFT](../transforms/nfsoft.md) page.

| Program | Task |
|---------|------|
| `simple_test` | Computes an NDSOFT and an NFSOFT and their adjoints for random rotations. It prints the run times and the maximum error. Arguments: `N M`, the bandwidth and the number of rotations, for example `./simple_test 8 64`. |

Reference: D. Potts, J. Prestin, and A. Vollrath. A Fast Algorithm for
Nonequispaced Fourier Transforms on the Rotation Group. To appear in Num. Alg.

## FPT

Directory `examples/fpt/`. Needs `--enable-fpt`. See the
[FPT](../transforms/fpt.md) page.

| Program | Task |
|---------|------|
| `simple_test` | Evaluates a Legendre expansion of degree $N = 8$ at the Chebyshev nodes with the fast polynomial transform. |

The file `simple_test.nb` is a Mathematica notebook for the same example.

## Solver

Directory `examples/solver/`. The solver is always built. See the
[Solver](../transforms/solver.md) page.

| Program | Task |
|---------|------|
| `simple_test` | Introduction to the solver. It computes a 1D inverse NFFT with $N = 16$ coefficients and $M = 8$ samples, and prints the residual of every iteration. The solver uses the default method CGNR. |
| `glacier` | Reconstruction of a glacier from scattered data. See [the glacier example](../applications/glacier.md). |

Reference: S. Kunis and D. Potts. Stability Results for Scattered Data
Interpolation by Trigonometric Polynomials. SIAM J. Sci. Comput. 29, 1403 -
1419, 2007.

## MRI

The directory `examples/mri/` holds no program. The MRI programs are in
`applications/mri/`. See the [MRI](../applications/mri.md) page.
