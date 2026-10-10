# Build from source

## Prerequisites

[FFTW3](https://fftw.org) development files, `make` and a C compiler. From a
git checkout you also need `autoconf`, `automake` and `libtool`. The unit tests
need [CUnit](http://cunit.sourceforge.net).

## Generate the build system

Only from a git checkout. A release tarball already contains `configure`.

```bash
./bootstrap.sh
```

Run it again after editing any `Makefile.am` or `configure.ac`.

## Configure and build

```bash
./configure --enable-all --enable-openmp
make -j
make check          # optional, needs CUnit
sudo make install
```

`./configure --help` lists every option. The ones that matter:

### Modules

| Flag | Effect |
|------|--------|
| `--enable-all` | Build every module, plus the examples and the applications. |
| `--enable-nfct`, `--enable-nfst` | The real-valued [cosine](../transforms/nfct.md) and [sine](../transforms/nfst.md) transforms. |
| `--enable-nnfft`, `--enable-nsfft` | [NNFFT](../transforms/nnfft.md), [NSFFT](../transforms/nsfft.md). |
| `--enable-nfsft`, `--enable-nfsoft` | [Sphere](../transforms/nfsft.md) and [rotation group](../transforms/nfsoft.md). Both pull in the [FPT](../transforms/fpt.md). |
| `--enable-fpt` | [Fast polynomial transform](../transforms/fpt.md). |
| `--enable-mri` | The [MRI](../applications/mri.md) plans. |
| `--enable-examples`, `--enable-applications` | The programs under `examples/` and `applications/`. |
| `--enable-tests` | The CUnit test programs. |

The [NFFT](../transforms/nfft.md) core and the [solver](../transforms/solver.md)
are always built.

### Precision

The same C sources compile in three precisions. They are mutually exclusive,
and each one needs its **own configured tree**.

| Flag | Real type | Library | FFTW variant |
|------|-----------|---------|--------------|
| default | `double` | `libnfft3` | `libfftw3` |
| `--enable-float` (or `--enable-single`) | `float` | `libnfft3f` | `libfftw3f` |
| `--enable-long-double` | `long double` | `libnfft3l` | `libfftw3l` |

All three can be installed side by side and linked into the same program; the
name prefixes keep them apart. See the [API index](../api/index.md).

### Window function

```bash
./configure --with-window=kaiserbessel
```

`kaiserbessel` (the default), `gaussian`, `bspline`, `sinc` or `dirac`. The
choice is baked into the library. Which one you linked is reported by
`nfft_get_window_name()`. What the window does is explained in the
[guide](../guide/index.md).

### Threads

```bash
./configure --enable-all --enable-openmp
```

This adds a second library, `libnfft3_omp`, alongside the serial one, and a
second test binary `tests/checkall_threads`. FFTW must have been built with
`--enable-threads`.

### Interfaces

| Flag | Effect |
|------|--------|
| `--enable-julia` | The Julia interface. Double precision and shared libraries only. |
| `--with-matlab=/path/to/matlab` | The MATLAB interface. |
| `--with-octave=/path/to/octave` | The Octave interface. |

### Finding FFTW

If FFTW is not where the compiler looks:

```bash
./configure --with-fftw3=/opt/fftw
# or, separately
./configure --with-fftw3-includedir=/opt/fftw/include \
            --with-fftw3-libdir=/opt/fftw/lib
```

`--with-cunit-includedir` and `--with-cunit-libdir` do the same for CUnit.

## CMake build

CMake builds the same sources. It needs CMake 3.20 or later, and 3.24 or
later for the Julia interface. You do not run `./bootstrap.sh`.

```bash
cmake -S . -B build
cmake --build build -j
ctest --test-dir build    # only with -DNFFT_ENABLE_TESTS=ON
cmake --install build --prefix /usr/local
```

Set an option with `-D<name>=<value>` in the first command. Without a build
type, CMake uses `Release`.

### Options

| Name | Default | Effect |
|------|---------|--------|
| `BUILD_SHARED_LIBS` | `ON` | Build shared libraries. `OFF` builds static libraries. |
| `NFFT_ENABLE_FLOAT` | `OFF` | Build `libnfft3f` in `float` precision. |
| `NFFT_ENABLE_LONG_DOUBLE` | `OFF` | Build `libnfft3l` in `long double` precision. |
| `NFFT_ENABLE_OPENMP` | `OFF` | Also build the OpenMP library `libnfft3_omp`. |
| `NFFT_ENABLE_MAXOPT` | `ON` | Add aggressive optimization flags, for example `-O3 -ffast-math -march=native`. Skipped when `CMAKE_C_FLAGS` is set. |
| `NFFT_ENABLE_TESTS` | `OFF` | Build the CUnit test programs. Without CUnit, the configure step skips them. |
| `NFFT_ENABLE_EXHAUSTIVE_UNIT_TESTS` | `OFF` | The larger, slower test set. Available only with `NFFT_ENABLE_TESTS=ON`. |
| `NFFT_BENCHMARK_MODE` | `off` | `off`, `simulation` or `walltime`. A value other than `off` builds the [benchmarks](../development/benchmarks.md) in that mode. |
| `NFFT_ENABLE_EXAMPLES` | `ON` | Build the programs under `examples/`. They are not installed. |
| `NFFT_ENABLE_APPLICATIONS` | `ON` | Build the programs under `applications/`. They are not installed. |
| `NFFT_WINDOW` | `kaiserbessel` | The window function: `kaiserbessel`, `gaussian`, `bspline`, `sinc` or `dirac`. |
| `NFFT_ENABLE_JULIA` | `OFF` | The Julia interface. Double precision and shared libraries only. |
| `NFFT_WITH_OCTAVE` | `OFF` | The Octave interface. Not with `long double`. |
| `NFFT_WITH_MATLAB` | empty | Path to a MATLAB installation. A non-empty path builds the MATLAB interface. Not with `long double`. |
| `NFFT_ENABLE_MATLAB_THREADS` | the value of `NFFT_ENABLE_OPENMP` | Build the Octave or MATLAB interface with the OpenMP kernel. Available only with one of these interfaces. Needs `NFFT_ENABLE_OPENMP=ON`. |
| `NFFT_VERSION_TYPE` | `alpha` | The suffix of the version string. |
| `NFFT_INSTALL_CMAKEDIR` | `<libdir>/cmake/nfft3` | The install directory of the CMake package files. Float and long double add `f` or `l`. |

The configure step stops with an error for these combinations:

- `NFFT_ENABLE_FLOAT` and `NFFT_ENABLE_LONG_DOUBLE` together.
- `NFFT_ENABLE_JULIA` with `float` or `long double`, or with `BUILD_SHARED_LIBS=OFF`.
- `NFFT_WITH_OCTAVE` and `NFFT_WITH_MATLAB` together.

As with Autotools, each precision and each window needs its own build tree.

### Modules

CMake has no module options. It always builds the NFFT, the NFCT, the NFST and
the solver. In double precision it also builds the NNFFT, the NSFFT, the MRI
plans, the FPT, the NFSFT and the NFSOFT. These six modules build in double
precision only.

A double precision CMake build thus has the modules of `./configure --enable-all`.
The differences:

- You cannot turn off one module.
- `--enable-all` also turns on the Julia interface in a double precision, shared
  build. CMake needs `-DNFFT_ENABLE_JULIA=ON`.

### Finding FFTW with CMake

If FFTW is not where CMake looks, give its root:

```bash
cmake -S . -B build -DFFTW3_ROOT=/opt/fftw
```

`FFTW3_ROOT` can also be an environment variable. `FFTW3_INCLUDEDIR` and
`FFTW3_LIBDIR` give the two directories separately. CMake looks for the FFTW
library of the selected precision, and for its `_omp` and `_threads` variants.

### Using the installed library from CMake

The install writes these files to `<libdir>/cmake/nfft3`, where `<libdir>` is
the library directory of the install, for example `lib`:

- `NFFT3Config.cmake` and `NFFT3ConfigVersion.cmake`.
- `NFFT3Targets.cmake`, with the imported target `NFFT3::nfft3`.
- `FindFFTW3.cmake`, which the package uses to find FFTW.

A float build writes `NFFT3fConfig.cmake` to `<libdir>/cmake/nfft3f` and exports
`NFFT3::nfft3f`. A long double build uses `l` in the same places. The package
accepts a request for the same major version. The install also writes the
pkg-config file `nfft3.pc`, `nfft3f.pc` or `nfft3l.pc`.

In your project:

```cmake
find_package(NFFT3 REQUIRED)
target_link_libraries(my_program PRIVATE NFFT3::nfft3)
```

The OpenMP library `libnfft3_omp` is installed, but it is not a target of the
package, and the pkg-config file names only the serial library. Link it by
name, `-lnfft3_omp`, with the OpenMP flag of your compiler.

### Other useful flags

| Flag | Effect |
|------|--------|
| `--enable-debug` | Extra runtime checks. |
| `--enable-measure-time` | Fill the `MEASURE_TIME_t` members of the plans. |
| `--enable-exhaustive-unit-tests` | The larger, slower test set. What CI runs. |
| `--with-gcc-arch=<arch>` | Pass an architecture to `-march`/`-mtune`. |

## Testing

```bash
make check
```

This builds and runs `tests/checkall`, and `tests/checkall_threads` as well
when the tree was configured with `--enable-openmp`. Details, and the accuracy
report the suite produces, are under [Testing](../development/testing.md).

## Cleaning

```bash
make clean       # object files
make distclean   # everything configure produced
```

A second precision or a second window means a second configured tree, not a
`make clean` in this one.
