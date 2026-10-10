# Build from source

## Prerequisites

[FFTW3](https://fftw.org) development files, `make` and a C compiler. Download the
source archive and unpack it. The archive contains `configure`. The unit tests
need [CUnit](http://cunit.sourceforge.net).

## Configure and build

```bash
./configure --enable-all --enable-openmp
make -j
make check          # optional, see Testing
sudo make install
```

`./configure --help` lists every option. It also lists the generic options of
Autoconf, Automake and Libtool, for example `--prefix` and `--enable-shared`.
The sections below describe all options that NFFT adds. Each row gives the
default and the effect. The last sections cover options that most users do not
need, with a note on when they apply.

### Modules

| Flag | Default | Effect |
|------|---------|--------|
| `--enable-all` | off | Sets the default of every module flag below to on. |
| `--enable-nfct`, `--enable-nfst` | value of `--enable-all` | The real-valued [cosine](../transforms/nfct.md) and [sine](../transforms/nfst.md) transforms. |
| `--enable-nfsft` | value of `--enable-all` | [Sphere](../transforms/nfsft.md). Also builds the FPT. |
| `--enable-nfsoft` | value of `--enable-all` | [Rotation group](../transforms/nfsoft.md). Also builds the FPT. |
| `--enable-nnfft` | value of `--enable-all` | [NNFFT](../transforms/nnfft.md). |
| `--enable-nsfft` | value of `--enable-all` | [NSFFT](../transforms/nsfft.md). |
| `--enable-mri` | value of `--enable-all` | The [MRI](../applications/mri.md) plans. |
| `--enable-fpt` | value of `--enable-all` | [Fast polynomial transform](../transforms/fpt.md). |
| `--enable-examples` | on | The example programs. |
| `--enable-applications` | on | The application programs. |
| `--enable-tests` | off | The CUnit test programs. See [Testing](#testing). |

`--enable-all` is off unless maintainer mode is on. The examples and the
applications do not depend on `--enable-all`.

The NFFT core, the solver, NFCT and NFST compile in all three precisions. In
single or long double precision, the other modules default to off, also with
`--enable-all`. If you enable one of them explicitly, `configure` fails with an error.

The [NFFT](../transforms/nfft.md) core and the [solver](../transforms/solver.md)
are always built.

### Precision

The same C sources compile in three precisions. Each one needs its **own configured tree**.

| Flag | Real type | Library | FFTW variant |
|------|-----------|---------|--------------|
| default | `double` | `libnfft3` | `libfftw3` |
| `--enable-float` (or `--enable-single`) | `float` | `libnfft3f` | `libfftw3f` |
| `--enable-long-double` | `long double` | `libnfft3l` | `libfftw3l` |

Both flags are off by default. They are mutually exclusive.

All three can be installed side by side and linked into the same program; the
name prefixes keep them apart. See the [API index](../api/index.md).

### Window function

```bash
./configure --with-window=kaiserbessel
```

`kaiserbessel` (the default), `gaussian`, `bspline`, `sinc` or `delta`. The `delta` window is deprecated and will be removed in a
future release. Any other value makes `configure` fail with an error. The choice is
baked into the library. Which one you linked is reported by
`nfft_get_window_name()`. What the window does is explained in the
[guide](../guide/index.md).

!!! warning "Use `delta`, not `dirac`"

    The help text says `dirac`, but `configure` accepts only `delta`. See
    [Window functions](../guide/windows.md).

### Threads

| Flag | Default | Effect |
|------|---------|--------|
| `--enable-openmp` | off | Build the OpenMP library in addition to the serial one. |

```bash
./configure --enable-all --enable-openmp
```

This adds a second library, `libnfft3_omp`, alongside the serial one. If the compiler does not support
OpenMP, `configure` fails with an error.

`configure` looks for a threaded FFTW. It prefers
the OpenMP variant of FFTW. If it finds only the generic threads variant, it
prints a warning and uses that variant. If it finds no threaded FFTW, it prints
a warning. Then only the NFFT code runs in parallel, and the FFTs run on one
thread.

### Interfaces

| Flag | Default | Effect |
|------|---------|--------|
| `--enable-julia` | value of `--enable-all` in double precision with shared libraries, else off | The Julia interface. Other precisions or `--disable-shared` stop `configure`. |
| `--with-matlab=DIR` | off | The MATLAB interface. `DIR` is the MATLAB root. |
| `--with-matlab-arch=ARCH` | detected | The MATLAB architecture name, for example `glnxa64`. |
| `--enable-matlab-argchecks` | on | Check the arguments of each MEX call. |
| `--with-matlab-fftw3-libdir=DIR` | `bin/ARCH` under the MATLAB root | The directory of the FFTW library that the MEX file links. |
| `--enable-matlab-threads` | value of `--enable-openmp` | Link the MEX file against the OpenMP library. Needs `--enable-openmp`. |
| `--with-octave=DIR` | off | The Octave interface. Without `DIR`, `configure` searches for Octave. |
| `--with-octave-libdir=DIR` | detected | The Octave library directory. |
| `--with-octave-includedir=DIR` | detected | The Octave include directory. |

`--with-matlab` and `--with-octave` exclude each other. With `--enable-long-double`, the MATLAB
interface makes `configure` fail with an error.

### Finding FFTW and CUnit

If FFTW is not where the compiler looks:

```bash
./configure --with-fftw3=/opt/fftw
# or, separately
./configure --with-fftw3-includedir=/opt/fftw/include \
            --with-fftw3-libdir=/opt/fftw/lib
```

| Flag | Default | Effect |
|------|---------|--------|
| `--with-fftw3=DIR` | compiler search path | Use `DIR/include` and `DIR/lib`. |
| `--with-fftw3-includedir=DIR` | compiler search path | The FFTW header directory. |
| `--with-fftw3-libdir=DIR` | compiler search path | The FFTW library directory. |
| `--with-cunit-includedir=DIR` | compiler search path | The CUnit header directory. |
| `--with-cunit-libdir=DIR` | compiler search path | The CUnit library directory. |

### Debugging and timing

| Flag | Default | Effect |
|------|---------|--------|
| `--enable-debug` | off | Builds with `-g -O2`, the address and undefined behaviour sanitizers and extra GCC warnings. Replaces `CFLAGS`. |
| `--enable-measure-time` | off | Measures the run time of the transforms and stores it in the plans. |
| `--enable-measure-time-fftw` | off | Also measures the time of the FFTW calls. |

### Compiler optimization

| Flag | Default | Effect |
|------|---------|--------|
| `--with-gcc-arch=ARCH` | `-march=native` if the compiler accepts it | Pass `ARCH` to `-march` and `-mtune`. |
| `--enable-portable-binary` | off | Do not tie the binary to the build machine. Use it if you run the library on another machine. |

`configure` selects optimization flags only when you do not set `CFLAGS`.

### Benchmarks

Use these options if you measure the speed of the library. A normal build
does not need them. The [benchmark](../development/benchmarks.md) page
describes how to run the programs.

| Flag | Default | Effect |
|------|---------|--------|
| `--enable-benchmarks` | off | Build the benchmark programs. |
| `--with-benchmarks-prefix=PREFIX` | empty | Prefix for the names of the benchmarks. |
| `--with-agnostic-benchmarks=FLAGS` | all on | Choose which benchmarks to build. `FLAGS` is a comma-separated list of `parameter:flag` pairs, for example `window:1,openmp:0,precision:1`. The parameters are `window`, `openmp` and `precision`. The flag is `0` or `1`. Parameters that you do not list are off. Any other parameter makes `configure` fail with an error. |
| `--with-codspeed=DIR` | off | Link the benchmarks with the CodSpeed C++ library in `DIR`. Use it if you track the benchmark results with CodSpeed. |

### Documentation output

Use these options if you build the C API documentation with Doxygen. You do
not need them to use the library or to read this site. Each option has a
`--enable-doxygen-NAME` form. For the features that are on by default, the
form is `--disable-doxygen-NAME`.

| Feature `NAME` | Default | Output |
|----------------|---------|--------|
| `doc` | on | Any Doxygen documentation. |
| `html` | on | Plain HTML. |
| `dot` | on | Graphs in the documentation. |
| `man` | off | Manual pages. |
| `rtf` | off | RTF. |
| `xml` | off | XML. |
| `chm` | off | Compressed HTML help. |
| `chi` | off | Separate index file for compressed HTML help. |
| `ps` | off | PostScript. |
| `pdf` | off | PDF. |

### Other options

| Flag | Default | Effect |
|------|---------|--------|
| `--enable-exhaustive-unit-tests` | off | Add the exhaustive cases to the unit tests. They take longer to run. See [Testing](../development/testing.md). |
| `--enable-mips-zbus-timer` | off | Use the MIPS ZBus cycle counter for time measurements. Relevant only on MIPS hardware with `--enable-measure-time`. |
| `--enable-maintainer-mode` | off | Turn on the Automake maintainer rules. This also turns on the default of `--enable-all` and the extra compiler warnings. It is for people who work on the library. |

## CMake build

CMake builds the same sources. It needs CMake 3.20 or later, and 3.24 or
later for the Julia interface. You do not run `./bootstrap.sh`.

!!! note "Autotools is the authoritative build"

    The project supports CMake on a best-effort basis. Autotools is the
    authoritative build system. If the two builds differ, the Autotools build
    is the reference. Use Autotools when you need an option that only
    `configure` offers.

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

### Differences from the Autotools build

| Topic | Autotools | CMake |
|-------|-----------|-------|
| Modules | One flag for each module. | No module flags. The precision selects the modules. |
| Julia interface | On with `--enable-all` in a double precision, shared build. | Off. Set `-DNFFT_ENABLE_JULIA=ON`. |
| Dirac window | `--with-window=delta`. `configure` rejects `dirac`. | `-DNFFT_WINDOW=dirac`. |
| Optimization flags | Chosen by `configure` unless you set `CFLAGS`. | `NFFT_ENABLE_MAXOPT`, on by default. Skipped when you set `CMAKE_C_FLAGS`. |
| Debug build, timing, portable binary | `--enable-debug`, `--enable-measure-time`, `--enable-measure-time-fftw`, `--enable-portable-binary`. | No such options. |
| Location of FFTW | `--with-fftw3`, `--with-fftw3-includedir`, `--with-fftw3-libdir`. | `FFTW3_ROOT`, `FFTW3_INCLUDEDIR`, `FFTW3_LIBDIR`. |
| Running the tests | `make check`. | `ctest`. |
| Installed files | Libraries, headers and pkg-config files. | The same, and the CMake package files. |

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

## Testing

```bash
./configure --enable-tests
make
make check
```

`make check` runs the unit tests. They need [CUnit](http://cunit.sourceforge.net).
Without `--enable-tests`, `make check` runs no test. With `--enable-tests` and
no CUnit, `configure` fails with an error. If CUnit is not in the default search path, use
`--with-cunit-includedir` and `--with-cunit-libdir`. With `--enable-openmp`, the
tests also run against the OpenMP library.

If a test fails, `make check` prints `FAIL` for the test program and exits with
a nonzero status. The suites, the accuracy report and the reference data are
described under [Testing](../development/testing.md).

## Cleaning

```bash
make clean       # object files
make distclean   # everything configure produced
```

A second precision or a second window means a second configured tree, not a
`make clean` in this one.
