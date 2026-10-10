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
default and the line of the `AC_ARG_ENABLE` or `AC_ARG_WITH` call in `nfft/`.

### Modules

| Flag | Default | Effect | Source |
|------|---------|--------|--------|
| `--enable-all` | off | Sets the default of every module flag below to on. | `nfft/configure.ac:160-162` |
| `--enable-nfct`, `--enable-nfst` | value of `--enable-all` | The real-valued [cosine](../transforms/nfct.md) and [sine](../transforms/nfst.md) transforms. | `nfft/configure.ac:193-194` |
| `--enable-nfsft` | value of `--enable-all` | [Sphere](../transforms/nfsft.md). Also builds the FPT. | `nfft/configure.ac:195-196` |
| `--enable-nfsoft` | value of `--enable-all` | [Rotation group](../transforms/nfsoft.md). Also builds the FPT. | `nfft/configure.ac:197-198` |
| `--enable-nnfft` | value of `--enable-all` | [NNFFT](../transforms/nnfft.md). | `nfft/configure.ac:199-200` |
| `--enable-nsfft` | value of `--enable-all` | [NSFFT](../transforms/nsfft.md). | `nfft/configure.ac:201` |
| `--enable-mri` | value of `--enable-all` | The [MRI](../applications/mri.md) plans. | `nfft/configure.ac:202` |
| `--enable-fpt` | value of `--enable-all` | [Fast polynomial transform](../transforms/fpt.md). | `nfft/configure.ac:203-204` |
| `--enable-examples` | on | The programs under `examples/`. | `nfft/configure.ac:165-167` |
| `--enable-applications` | on | The programs under `applications/`. | `nfft/configure.ac:170-172` |
| `--enable-tests` | off | The CUnit test programs. See [Testing](#testing). | `nfft/configure.ac:630` |

The module flags come from the macro `AX_NFFT_MODULE`. It takes its default
from `--enable-all` (`nfft/m4/ax_nfft_module.m4:3`, `9-10`). `--enable-all` is
off unless maintainer mode is on (`nfft/configure.ac:161`). The examples and
the applications do not depend on `--enable-all`.

Only NFCT and NFST compile in all three precisions. In single or long double
precision, the other modules default to off, also with `--enable-all`
(`nfft/m4/ax_nfft_module.m4:4-8`). If you enable one of them explicitly,
`configure` stops (`nfft/m4/ax_nfft_module.m4:13-17`).

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

Both flags are off by default (`nfft/configure.ac:110-111`, `119`). If you give
both, `configure` stops (`nfft/configure.ac:120-123`). The library suffix comes
from `nfft/configure.ac:131-135`.

All three can be installed side by side and linked into the same program; the
name prefixes keep them apart. See the [API index](../api/index.md).

### Window function

```bash
./configure --with-window=kaiserbessel
```

`kaiserbessel` (the default), `gaussian`, `bspline`, `sinc` or `delta`
(`nfft/configure.ac:237-256`). Any other value stops `configure`. The choice is
baked into the library. Which one you linked is reported by
`nfft_get_window_name()`. What the window does is explained in the
[guide](../guide/index.md).

!!! warning "Use `delta`, not `dirac`"

    The help text says `dirac`, but `configure` accepts only `delta`. See
    [Window functions](../guide/windows.md).

### Threads

| Flag | Default | Effect | Source |
|------|---------|--------|--------|
| `--enable-openmp` | off | Build the OpenMP library in addition to the serial one. | `nfft/configure.ac:207` |

```bash
./configure --enable-all --enable-openmp
```

This adds a second library, `libnfft3_omp`, alongside the serial one, and a
second test binary `tests/checkall_threads`. If the compiler does not support
OpenMP, `configure` stops (`nfft/configure.ac:392-394`).

`configure` looks for a threaded FFTW (`nfft/configure.ac:427-444`). It prefers
the OpenMP variant of FFTW. If it finds only the generic threads variant, it
prints a warning and uses that variant. If it finds no threaded FFTW, it prints
a warning. Then only the NFFT code runs in parallel, and the FFTs run on one
thread.

### Interfaces

| Flag | Default | Effect | Source |
|------|---------|--------|--------|
| `--enable-julia` | value of `--enable-all` in double precision with shared libraries, else off | The Julia interface. Other precisions or `--disable-shared` stop `configure`. | `nfft/configure.ac:175-190` |
| `--with-matlab=DIR` | off | The MATLAB interface. `DIR` is the MATLAB root. | `nfft/m4/ax_prog_matlab.m4:37-40` |
| `--with-matlab-arch=ARCH` | detected | The MATLAB architecture name, for example `glnxa64`. | `nfft/m4/ax_prog_matlab.m4:42-45` |
| `--enable-matlab-argchecks` | on | Check the arguments of each MEX call. Defines `MATLAB_ARGCHECKS`. | `nfft/m4/ax_prog_matlab.m4:47-55` |
| `--with-matlab-fftw3-libdir=DIR` | `bin/ARCH` under the MATLAB root | The directory of the FFTW library that the MEX file links. | `nfft/m4/ax_prog_matlab.m4:57-59`, `242-249` |
| `--enable-matlab-threads` | value of `--enable-openmp` | Link the MEX file against the OpenMP library. Needs `--enable-openmp`. | `nfft/m4/ax_prog_matlab.m4:61-65`, `nfft/configure.ac:462-464` |
| `--with-octave=DIR` | off | The Octave interface. Without `DIR`, `configure` searches for Octave. | `nfft/m4/ax_prog_matlab.m4:31-34`, `344-345` |
| `--with-octave-libdir=DIR` | detected | The Octave library directory. | `nfft/m4/ax_prog_matlab.m4:384-386` |
| `--with-octave-includedir=DIR` | detected | The Octave include directory. | `nfft/m4/ax_prog_matlab.m4:388-390` |

`--with-matlab` and `--with-octave` exclude each other
(`nfft/m4/ax_prog_matlab.m4:67-68`). With `--enable-long-double`, the MATLAB
interface stops `configure` (`nfft/configure.ac:458-460`).

### Finding FFTW and CUnit

If FFTW is not where the compiler looks:

```bash
./configure --with-fftw3=/opt/fftw
# or, separately
./configure --with-fftw3-includedir=/opt/fftw/include \
            --with-fftw3-libdir=/opt/fftw/lib
```

| Flag | Default | Effect | Source |
|------|---------|--------|--------|
| `--with-fftw3=DIR` | compiler search path | Use `DIR/include` and `DIR/lib`. | `nfft/m4/nfft_lib_fftw3.m4:46-47` |
| `--with-fftw3-includedir=DIR` | compiler search path | The FFTW header directory. | `nfft/m4/nfft_lib_fftw3.m4:53-55` |
| `--with-fftw3-libdir=DIR` | compiler search path | The FFTW library directory. | `nfft/m4/nfft_lib_fftw3.m4:49-51` |
| `--with-cunit-includedir=DIR` | compiler search path | The CUnit header directory. | `nfft/m4/nfft_lib_cunit.m4:60-62` |
| `--with-cunit-libdir=DIR` | compiler search path | The CUnit library directory. | `nfft/m4/nfft_lib_cunit.m4:64-66` |

### Debugging and timing

| Flag | Default | Effect | Source |
|------|---------|--------|--------|
| `--enable-debug` | off | Defines `NFFT_DEBUG`. Replaces `CFLAGS` with `-g -O2` and the address and undefined behaviour sanitizers. Adds GCC warnings. | `nfft/configure.ac:210-215`, `357-375` |
| `--enable-measure-time` | off | Defines `MEASURE_TIME`. Fills the `MEASURE_TIME_t` members of the plans. | `nfft/configure.ac:217-220` |
| `--enable-measure-time-fftw` | off | Defines `MEASURE_TIME_FFTW`. Also measures the time of the FFTW calls. | `nfft/configure.ac:223-227` |
| `--enable-mips-zbus-timer` | off | Defines `HAVE_MIPS_ZBUS_TIMER`. Uses the MIPS ZBus cycle counter as the clock. | `nfft/configure.ac:229-234` |
| `--enable-exhaustive-unit-tests` | off | Defines `NFFT_EXHAUSTIVE_UNIT_TESTS`. The larger, slower test set. What CI runs. | `nfft/configure.ac:260-266` |

### Compiler optimization

| Flag | Default | Effect | Source |
|------|---------|--------|--------|
| `--with-gcc-arch=ARCH` | `-march=native` if the compiler accepts it, else a guess | Pass `ARCH` to `-march` and `-mtune`. | `nfft/m4/ax_gcc_archflag.m4:76-77`, `nfft/configure.ac:348-352` |
| `--enable-portable-binary` | off | Do not use flags that tie the binary to the build machine, such as `-march=native`. | `nfft/m4/ax_cc_maxopt.m4:66-67`, `nfft/configure.ac:348-352` |

`configure` selects optimization flags only when you do not set `CFLAGS`
(`nfft/m4/ax_cc_maxopt.m4:70`). In a cross build it does not use
`-march=native` (`nfft/configure.ac:348`).

### Developer options

The options below are for work on NFFT itself. They are described under
[Development](../development/index.md) and
[Benchmarks](../development/benchmarks.md).

| Flag | Default | Effect | Source |
|------|---------|--------|--------|
| `--enable-maintainer-mode` | off | Sets the default of `--enable-all` to on and adds GCC warnings. | `nfft/configure.ac:52`, `161`, `366-375` |
| `--enable-benchmarks` | off | Build the benchmark programs. Needs CodSpeed, else `configure` stops. | `nfft/configure.ac:268`, `652-656` |
| `--with-codspeed=DIR` | off | The CodSpeed C++ library in `DIR`. | `nfft/m4/nfft_lib_codspeed.m4:41-42` |
| `--with-benchmarks-prefix=PREFIX` | empty | A prefix for the benchmark names. | `nfft/configure.ac:269-270` |
| `--with-agnostic-benchmarks=FLAGS` | all on | Which benchmarks ignore the window, the precision or OpenMP. Used only in CI. | `nfft/configure.ac:272-296` |
| `--enable-doxygen-doc` | on | Any Doxygen output, through `make doc`. Turn off with `--disable-doxygen-doc`. | `nfft/m4/ax_prog_doxygen.m4:265`, `414`, `nfft/Makefile.am:124-125` |
| `--enable-doxygen-dot` | on | Graphs in the Doxygen output. | `nfft/configure.ac:94`, `nfft/m4/ax_prog_doxygen.m4:422` |
| `--enable-doxygen-html` | on | Doxygen HTML. | `nfft/configure.ac:95`, `nfft/m4/ax_prog_doxygen.m4:473` |
| `--enable-doxygen-chm`, `--enable-doxygen-chi` | off | Compressed HTML help, and its separate index. | `nfft/configure.ac:96-97`, `nfft/m4/ax_prog_doxygen.m4:455`, `465` |
| `--enable-doxygen-man` | off | Doxygen manual pages. | `nfft/configure.ac:98`, `nfft/m4/ax_prog_doxygen.m4:431` |
| `--enable-doxygen-rtf` | off | Doxygen RTF. | `nfft/configure.ac:99`, `nfft/m4/ax_prog_doxygen.m4:439` |
| `--enable-doxygen-xml` | off | Doxygen XML. | `nfft/configure.ac:100`, `nfft/m4/ax_prog_doxygen.m4:447` |
| `--enable-doxygen-pdf`, `--enable-doxygen-ps` | off | Doxygen PDF and PostScript. | `nfft/configure.ac:101-102`, `nfft/m4/ax_prog_doxygen.m4:481`, `490` |

## Testing

```bash
./configure --enable-tests
make check
```

`make check` builds and runs the programs in `check_PROGRAMS`
(`nfft/tests/Makefile.am:21-23`):

- `tests/checkall`, the serial suite, linked against `libnfft3`
  (`nfft/tests/Makefile.am:16`, `37-39`). It tests the NFFT, and the NFCT and
  the NFST if those modules are on (`nfft/tests/Makefile.am:25-35`).
- `tests/checkall_threads`, the same sources linked against `libnfft3_omp`,
  only with `--enable-openmp` (`nfft/tests/Makefile.am:5-7`, `45-51`).

The tests need `--enable-tests` and CUnit. Without `--enable-tests`, the list
is empty and `make check` runs no test (`nfft/tests/Makefile.am:5-19`). With
`--enable-tests` and no CUnit, `configure` stops
(`nfft/configure.ac:633-639`).

A test program exits with a failure status if one CUnit test fails
(`nfft/tests/check.c:196-201`). `make check` then reports `FAIL` for that
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
