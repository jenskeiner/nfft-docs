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
make check          # optional, needs --enable-tests and CUnit
sudo make install
```

`./configure --help` lists every option. It also lists the generic options of
Autoconf, Automake and Libtool, for example `--prefix` and `--enable-shared`.
The sections below describe the options that NFFT adds. Each row gives the
default and the effect.

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
| `--enable-examples` | on | The programs under `examples/`. |
| `--enable-applications` | on | The programs under `applications/`. |
| `--enable-tests` | off | The CUnit test programs. See [Testing](#testing). |

The module flags come from the macro `AX_NFFT_MODULE`. It takes its default
from `--enable-all` (`nfft/m4/ax_nfft_module.m4:3`, `9-10`). `--enable-all` is
off unless maintainer mode is on. The examples and
the applications do not depend on `--enable-all`.

Only NFCT and NFST compile in all three precisions. In single or long double
precision, the other modules default to off, also with `--enable-all`. If you enable one of them explicitly,
`configure` stops.

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

Both flags are off by default. If you give
both, `configure` stops.

All three can be installed side by side and linked into the same program; the
name prefixes keep them apart. See the [API index](../api/index.md).

### Window function

```bash
./configure --with-window=kaiserbessel
```

`kaiserbessel` (the default), `gaussian`, `bspline`, `sinc` or `delta`. Any other value stops `configure`. The choice is
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

This adds a second library, `libnfft3_omp`, alongside the serial one, and a
second test binary `tests/checkall_threads`. If the compiler does not support
OpenMP, `configure` stops.

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
| `--enable-matlab-argchecks` | on | Check the arguments of each MEX call. Defines `MATLAB_ARGCHECKS`. |
| `--with-matlab-fftw3-libdir=DIR` | `bin/ARCH` under the MATLAB root | The directory of the FFTW library that the MEX file links. |
| `--enable-matlab-threads` | value of `--enable-openmp` | Link the MEX file against the OpenMP library. Needs `--enable-openmp`. |
| `--with-octave=DIR` | off | The Octave interface. Without `DIR`, `configure` searches for Octave. |
| `--with-octave-libdir=DIR` | detected | The Octave library directory. |
| `--with-octave-includedir=DIR` | detected | The Octave include directory. |

`--with-matlab` and `--with-octave` exclude each other. With `--enable-long-double`, the MATLAB
interface stops `configure`.

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
| `--enable-debug` | off | Defines `NFFT_DEBUG`. Replaces `CFLAGS` with `-g -O2` and the address and undefined behaviour sanitizers. Adds GCC warnings. |
| `--enable-measure-time` | off | Defines `MEASURE_TIME`. Fills the `MEASURE_TIME_t` members of the plans. |
| `--enable-measure-time-fftw` | off | Defines `MEASURE_TIME_FFTW`. Also measures the time of the FFTW calls. |
| `--enable-mips-zbus-timer` | off | Defines `HAVE_MIPS_ZBUS_TIMER`. Uses the MIPS ZBus cycle counter as the clock. |
| `--enable-exhaustive-unit-tests` | off | Defines `NFFT_EXHAUSTIVE_UNIT_TESTS`. The larger, slower test set. What CI runs. |

### Compiler optimization

| Flag | Default | Effect |
|------|---------|--------|
| `--with-gcc-arch=ARCH` | `-march=native` if the compiler accepts it, else a guess | Pass `ARCH` to `-march` and `-mtune`. |
| `--enable-portable-binary` | off | Do not use flags that tie the binary to the build machine, such as `-march=native`. |

`configure` selects optimization flags only when you do not set `CFLAGS`. In a cross build it does not use
`-march=native`.

### Developer options

The options below are for work on NFFT itself. They are described under
[Development](../development/index.md) and
[Benchmarks](../development/benchmarks.md).

| Flag | Default | Effect |
|------|---------|--------|
| `--enable-maintainer-mode` | off | Sets the default of `--enable-all` to on and adds GCC warnings. |
| `--enable-benchmarks` | off | Build the benchmark programs. Needs CodSpeed, else `configure` stops. |
| `--with-codspeed=DIR` | off | The CodSpeed C++ library in `DIR`. |
| `--with-benchmarks-prefix=PREFIX` | empty | A prefix for the benchmark names. |
| `--with-agnostic-benchmarks=FLAGS` | all on | Which benchmarks ignore the window, the precision or OpenMP. Used only in CI. |
| `--enable-doxygen-doc` | on | Any Doxygen output, through `make doc`. Turn off with `--disable-doxygen-doc`. |
| `--enable-doxygen-dot` | on | Graphs in the Doxygen output. |
| `--enable-doxygen-html` | on | Doxygen HTML. |
| `--enable-doxygen-chm`, `--enable-doxygen-chi` | off | Compressed HTML help, and its separate index. |
| `--enable-doxygen-man` | off | Doxygen manual pages. |
| `--enable-doxygen-rtf` | off | Doxygen RTF. |
| `--enable-doxygen-xml` | off | Doxygen XML. |
| `--enable-doxygen-pdf`, `--enable-doxygen-ps` | off | Doxygen PDF and PostScript. |

## Testing

```bash
./configure --enable-tests
make check
```

`make check` builds and runs the programs in `check_PROGRAMS`:

- `tests/checkall`, the serial suite, linked against `libnfft3` It tests the NFFT, and the NFCT and
  the NFST if those modules are on.
- `tests/checkall_threads`, the same sources linked against `libnfft3_omp`, only with `--enable-openmp`.

The tests need `--enable-tests` and CUnit. Without `--enable-tests`, the list
is empty and `make check` runs no test. With
`--enable-tests` and no CUnit, `configure` stops.

A test program exits with a failure status if one CUnit test fails. `make check` then reports `FAIL` for that
program and exits with a nonzero status. The details are in
`tests/checkall.log` and in `tests/CUnitAutomated-Results.xml`. The suites, the
accuracy report and the reference data are described under
[Testing](../development/testing.md).

## Cleaning

```bash
make clean       # object files
make distclean   # everything configure produced
```

A second precision or a second window means a second configured tree, not a
`make clean` in this one.
