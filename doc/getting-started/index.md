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

The install writes a `pkg-config` file, so a program is compiled with

```bash
cc myprogram.c $(pkg-config --cflags --libs nfft3) -lm
```

Without `pkg-config`:

```bash
cc myprogram.c -lnfft3 -lfftw3 -lm
```

The library name carries the precision suffix: `nfft3` for double, `nfft3f`
for float, `nfft3l` for long double. Add `_omp` for the OpenMP build, for
example `-lnfft3_omp`.

## Next

[Write a first transform](first-transform.md).
