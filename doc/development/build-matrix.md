# Build matrix

NFFT3 has three build-time choices that change the compiled code: the
[window function](../guide/windows.md), the [precision](../guide/precision.md)
and OpenMP. Two build systems, Autotools and CMake, build the same sources. CI
covers these choices in several workflows under `.github/workflows/`. This page
lists what each workflow builds and runs.

## The axes

| Axis | Values | Autotools | CMake |
|------|--------|-----------|-------|
| Window | Kaiser-Bessel, Gaussian, B-spline, sinc power | `--with-window=` with `kaiserbessel`, `gaussian`, `bspline` or `sinc` | `-DNFFT_WINDOW=` with the same names |
| Precision | double, float, long double | none, `--enable-float`, `--enable-long-double` | none, `-DNFFT_ENABLE_FLOAT=ON`, `-DNFFT_ENABLE_LONG_DOUBLE=ON` |
| OpenMP | off, on | `--enable-openmp` | `-DNFFT_ENABLE_OPENMP=ON`, the default |

The precisions exclude each other in one build tree. The Dirac window is not part
of any CI matrix. The modules NNFFT, NSFFT, MRI, FPT, NFSFT and NFSOFT build in
double precision only.

`BUILD_CONFIG` names a cell. It is `<os>_<compiler>_<window>_<precision>`. The
macOS workflow appends `_openmp` or `_singlethread`. The name appears in the
job title, in artifact names, and in the accuracy and benchmark reports.

## Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `build-linux.yml` | Push and pull request on `main`, `develop`, `master`; manual | The full window and precision matrix with Autotools and CMake, the tests, the accuracy report, `make distcheck`, an Octave job. |
| `build-macos.yml` | Same | Compilers and OpenMP on macOS, Kaiser-Bessel window. |
| `build-windows.yml` | Same | The core library with MinGW-w64 and CMake. |
| `bench-linux.yml` | Push and pull request when kernel, headers, benchmarks or CMake files change; manual | The [benchmarks](benchmarks.md). |
| `docs.yml` | Pull request, push to `develop`, release, manual | Builds the documentation site and deploys it. |
| `accuracy-report-fork.yml` | After `Build Linux` finished for a fork pull request | Posts the accuracy comment. |
| `draft-release.yml` | Push to `develop` | Keeps the draft release notes up to date. |

The three build workflows use one `concurrency` group each. A new run does not
cancel an older run.

## Build Linux

The workflow runs on `ubuntu-latest`. It has 17 cells.

| Compiler | Windows | Precisions | Cells |
|----------|---------|------------|-------|
| `gcc` | Kaiser-Bessel, Gaussian, B-spline, sinc power | double, float, long double | 12 |
| `clang` | Kaiser-Bessel | double, float, long double | 3 |
| `gcc-14` | Kaiser-Bessel | double | 1 |
| `gcc-snapshot` | Kaiser-Bessel | double | 1 |

OpenMP is on in every cell. Each cell first builds with Autotools and then, in
the same job, with CMake.

**Autotools.**

1. `./bootstrap.sh`
2. `./configure --with-window=<window> <precision> --enable-all --enable-openmp`.
   The `gcc` cells add `--enable-tests --enable-exhaustive-unit-tests`. Double
   precision cells add `--enable-julia`.
3. `make -j`
4. In the `gcc` cells only, `make check` with `NFFT_BENCH_OUT` set. It runs
   `checkall` and `checkall_threads`. The workflow converts the CUnit results to
   JUnit, publishes them, aggregates the accuracy records and uploads them as the
   artifact `accuracy-bmf-<BUILD_CONFIG>`.
5. In the double precision cells, the Julia examples `simple_test*.jl`.

**CMake.**

1. Configure with the same window and precision, `-DNFFT_ENABLE_OPENMP=ON`,
   `-DNFFT_ENABLE_TESTS=ON`, `-DNFFT_ENABLE_EXHAUSTIVE_UNIT_TESTS=ON`, the
   examples and the applications, and the C flags
   `-O3 -g -fomit-frame-pointer -fstrict-aliasing -ffast-math`. The double
   precision cells add `-DNFFT_ENABLE_JULIA=ON`.
2. `cmake/config-parity-check.sh` compares the macros of the Autotools
   `config.h` with the CMake `config.h`. It fails if CMake omits a macro.
3. Build. The job then checks that representative example and application
   binaries exist. The double precision cells check the double-only ones as well.
4. In the Kaiser-Bessel cells, install and check the installed header and the
   CMake package file. Run the Julia examples in double precision.

The CMake part builds the test programs but does not run `ctest`.

Three more jobs belong to the workflow.

| Job | Content |
|-----|---------|
| `accuracy-report` | Needs all cells. Downloads their accuracy data and publishes the [accuracy report](testing.md#accuracy-reports). Skipped for fork pull requests. |
| `distcheck` | `./configure --enable-all --enable-exhaustive-unit-tests` and `make distcheck`. |
| `cmake-octave` | Ubuntu 24.04, CMake with the Octave interface, double precision, OpenMP. Runs `ctest -L octave`. |

## Build macOS

The workflow runs on `macos-26` and uses Homebrew packages. It has 13 cells, all
with the Kaiser-Bessel window.

| Compiler | Precisions | OpenMP | Cells |
|----------|------------|--------|-------|
| `gcc` | double, float, long double | off | 3 |
| `clang`, `clang-homebrew` | double | off | 2 |
| `gcc-13`, `gcc-14`, `gcc-15`, `gcc-16` | double | off | 4 |
| `gcc-13`, `gcc-14`, `gcc-15`, `gcc-16` | double | on | 4 |

Each cell first builds with Autotools:

```bash
./configure --with-window=kaiserbessel <precision> --enable-all \
            --enable-exhaustive-unit-tests [--enable-openmp]
make
make check
```

`--enable-openmp` is set in the OpenMP cells. The cell then builds with CMake.
That build has OpenMP off, the examples and applications on, and it points to the
FFTW of Homebrew. It runs `ctest`, checks the install and runs the Julia
examples for double precision. Neither configure step enables the tests, see
[Where the tests run](#where-the-tests-run).

## Build Windows

One job on `windows-latest` with the MSYS2 MINGW64 shell. The compiler is
MinGW-w64 gcc, because the C99 complex code does not compile with the MSVC C
front end. The job configures CMake with Ninja, `Release`, shared libraries, no
OpenMP, and no examples and applications. It builds, installs, and builds a small
consumer program with `find_package` against the installed package. The
consumer runs.

## Where the tests run

The CUnit tests need `--enable-tests` or `-DNFFT_ENABLE_TESTS=ON`. Both default
to off, and `--enable-all` does not turn them on.

| Cell | Tests built | Tests run |
|------|-------------|-----------|
| Linux `gcc`, Autotools | Yes | `make check`, serial and OpenMP |
| Linux `gcc`, CMake | Yes | No |
| Other Linux compilers | No, for Autotools. Yes, for CMake. | No |
| macOS | No | No |
| Windows | No | No |

The window and precision combinations that run the tests are therefore the 12
`gcc` cells on Linux.

## Reproducing a cell

Use the commands of the workflow. One cell, for example `gcc`, Gaussian window,
float precision, with the tests:

```bash
./bootstrap.sh
./configure --with-window=gaussian --enable-float --enable-all --enable-openmp \
            --enable-tests --enable-exhaustive-unit-tests
make -j
make check
```

Each precision and each window needs its own configured tree. See
[Build from source](../getting-started/build-from-source.md).

## Other workflows

**Docs.** `docs.yml` builds the API pages, checks the generator against
`include/nfft3.h`, runs `zensical build --strict` and a site check, and uploads the
site as an artifact. A push to `develop` deploys the version `dev`. A published
release that is not a pre-release deploys its `X.Y` version and the alias
`latest`. A manual run deploys a named version. Pull requests also run an
external link check that does not fail the build. See [Releasing](releasing.md).

**Fork accuracy comment.** A fork pull request has a read-only token, so the
in-build job cannot post. `accuracy-report-fork.yml` runs from the default branch
after `Build Linux`. It reads only the accuracy data of the fork, never its code.

**Release notes.** `draft-release.yml` runs the release drafter on each push to
`develop`. The categories come from the labels of merged pull requests.
