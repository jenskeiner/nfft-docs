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
