# Install

NFFT3 is a C library. It needs [FFTW3](https://fftw.org) and a C compiler.

## FFTW

FFTW is the only hard dependency. Install it from your package manager.

=== "Debian, Ubuntu"

    ```bash
    sudo apt install libfftw3-dev
    ```

=== "Fedora, RHEL"

    ```bash
    sudo dnf install fftw-devel
    ```

=== "macOS"

    ```bash
    brew install fftw
    ```

=== "Windows, MSYS2"

    ```bash
    pacman -S mingw-w64-x86_64-fftw
    ```

If you build FFTW yourself, configure it with `--enable-shared`, and with
`--enable-threads` as well if you want the multi-threaded NFFT.

The library is precision-agnostic and links against the FFTW variant of the
precision it was configured for: `libfftw3f` for float, `libfftw3` for double,
`libfftw3l` for long double.

## NFFT3

There is no distribution package. Build from source; it is three commands.

```bash
git clone https://github.com/NFFT/nfft.git
cd nfft
./bootstrap.sh
./configure --enable-all --enable-openmp
make -j
sudo make install
```

`./bootstrap.sh` is only needed when you work from a git checkout; a release
tarball ships a ready `configure`. Every flag is described under
[Build from source](build-from-source.md).

Optional but recommended, run the test suite before installing. It needs
CUnit and a tree that was configured with `--enable-tests`:

```bash
make check
```

## Compile against it

One configured tree builds one precision. The precision suffix is empty for
double, `f` for float and `l` for long double (`nfft/configure.ac:131-135`).
The suffix goes into the library name, the `pkg-config` module name and the
FFTW library name.

### Flags per build

| Precision | Build | `pkg-config` module | Compiler flags | Linker flags |
|-----------|-------|---------------------|----------------|--------------|
| double | serial | `nfft3` | none | `-lnfft3 -lfftw3 -lm` |
| float | serial | `nfft3f` | none | `-lnfft3f -lfftw3f -lm` |
| long double | serial | `nfft3l` | none | `-lnfft3l -lfftw3l -lm` |
| double | OpenMP | none | `-fopenmp` | `-fopenmp -lnfft3_omp -lfftw3_omp -lfftw3 -lm` |
| float | OpenMP | none | `-fopenmp` | `-fopenmp -lnfft3f_omp -lfftw3f_omp -lfftw3f -lm` |
| long double | OpenMP | none | `-fopenmp` | `-fopenmp -lnfft3l_omp -lfftw3l_omp -lfftw3l -lm` |

Sources for the table:

- The install writes one `pkg-config` file, `nfft3@PREC_SUFFIX@.pc`
  (`nfft/Makefile.am:95-101`). Its `Libs` line is
  `-L${libdir} -lnfft3@PREC_SUFFIX@`. It requires the FFTW module of the same
  precision, `fftw3@PREC_SUFFIX@` (`nfft/nfft3.pc.in:9-11`).
- No `pkg-config` file exists for the OpenMP library. The file names only
  the serial library (`nfft/nfft3.pc.in:10`).
- The serial library links against `@fftw3_LIBS@`
  (`nfft/Makefile.am:56-57`). Configure sets this to the FFTW library and
  `-lm` (`nfft/m4/nfft_lib_fftw3.m4:105-107`).
- `--enable-openmp` builds `libnfft3@PREC_SUFFIX@_omp` and an identical
  `libnfft3@PREC_SUFFIX@_threads` (`nfft/Makefile.am:43-53`, `61-71`). Each
  contains the full threaded kernel. Link one of them in place of the serial
  library, not in addition to it.
- The OpenMP library links against `@fftw3_LIBS_omp@` and is built with
  `$(OPENMP_CFLAGS)` (`nfft/Makefile.am:68-70`).

The OpenMP flag depends on the compiler. Configure tries `-fopenmp` first,
which GCC and Clang accept. Other compilers use `-qopenmp`, `-openmp` or
`-xopenmp` (`nfft/m4/ax_openmp.m4:84-91`). For Apple Clang, the source names
`-Xpreprocessor -fopenmp -lomp` (`nfft/m4/ax_openmp.m4:82-83`).

The FFTW threads library is `libfftw3@PREC_SUFFIX@_omp`. If it is missing,
configure takes `libfftw3@PREC_SUFFIX@_threads` instead, and with it
`-lpthread` where the link needs it. If neither exists, FFTW runs on one
thread and the link needs no FFTW threads library
(`nfft/configure.ac:427-444`, `nfft/m4/nfft_lib_fftw3.m4:113-150`).
Use the variant that configure reported for your build.

On some systems, OpenMP atomic operations on floating-point values also need
`-latomic` (`nfft/m4/nfft_openmp_atomic_float.m4:90-99`,
`nfft/configure.ac:396-410`). Add it when the link reports undefined
`__atomic` symbols.

### An example program

`examples/nfft/simple_test.c` includes the precision-agnostic header
`nfft3mp.h`:

```c
--8<-- "examples/nfft/simple_test.c:18:22"
```

Its `main` runs a one-dimensional and a two-dimensional transform:

```c
--8<-- "examples/nfft/simple_test.c:150:161"
```

`nfft3mp.h` stops with an error unless exactly one precision macro is set
(`nfft/include/nfft3mp.h:29-63`). The upstream build sets it on the command
line (`nfft/examples/nfft/Makefile.am:1`). Do the same. For the double
build:

```bash
cc -DNFFT_PRECISION_DOUBLE simple_test.c $(pkg-config --cflags --libs nfft3) -lm -o simple_test
```

For the float build, use `-DNFFT_PRECISION_SINGLE` and the module `nfft3f`.
For the OpenMP double build, use the flags from the table:

```bash
cc -fopenmp -DNFFT_PRECISION_DOUBLE simple_test.c -lnfft3_omp -lfftw3_omp -lfftw3 -lm -o simple_test
```

### Library in a non-standard prefix

If you installed with `./configure --prefix=$HOME/opt/nfft`, the compiler,
the linker, `pkg-config` and the dynamic loader do not search there. Tell each
of them:

```bash
PREFIX=$HOME/opt/nfft
export PKG_CONFIG_PATH=$PREFIX/lib/pkgconfig:$PKG_CONFIG_PATH
cc -DNFFT_PRECISION_DOUBLE simple_test.c $(pkg-config --cflags --libs nfft3) -lm -Wl,-rpath,$PREFIX/lib -o simple_test
# without pkg-config:
cc -DNFFT_PRECISION_DOUBLE -I$PREFIX/include simple_test.c -L$PREFIX/lib -lnfft3 -lfftw3 -lm -Wl,-rpath,$PREFIX/lib -o simple_test
```

The `pkg-config` file is in `$(libdir)/pkgconfig` (`nfft/Makefile.am:100`).
`-Wl,-rpath` records the library directory in the program. As an alternative,
set `LD_LIBRARY_PATH` on Linux or `DYLD_LIBRARY_PATH` on macOS before you run
the program. If FFTW is in a different prefix too, add its directories in the
same way.

## Next

[Write a first transform](first-transform.md).
