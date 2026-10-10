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

## Packages

Several package managers ship NFFT3. Each package below builds all modules
(`--enable-all`), unless the tab says otherwise. Without that flag, the
library has only the NFFT, NFCT and NFST modules. Each package uses the
default Kaiser-Bessel window, unless the tab names a variant. Each
package is double precision only, unless the tab says otherwise.

=== "Debian and Ubuntu"

    ```bash
    sudo apt install libnfft3-dev
    ```

    `libnfft3-dev` holds the header and the `pkg-config` file. It pulls in
    the libraries `libnfft3-single4`, `libnfft3-double4` and, on most
    architectures, `libnfft3-long4`. The package builds all modules, with
    OpenMP, in float, double and long double precision. It ships no static
    library. `libnfft3-doc` holds the API documentation.
    `libnfft3-julia` holds the Julia interface.

    Older releases, for example Debian 11 and Ubuntu 22.04, ship an older
    upstream release under other library package names, such as
    `libnfft3-double2`. `libnfft3-dev` is correct on all of them.

    Sources: [Debian packaging](https://sources.debian.org/src/nfft/),
    [packages.ubuntu.com](https://packages.ubuntu.com/search?keywords=libnfft3-dev),
    [Repology](https://repology.org/project/nfft/).

=== "Arch Linux"

    The official repositories have no package. The AUR package `nfft`
    builds from source on your machine:

    ```bash
    git clone https://aur.archlinux.org/nfft.git
    cd nfft
    makepkg -si
    ```

    It builds all modules with OpenMP.

    Source: [AUR package nfft](https://aur.archlinux.org/packages/nfft).

=== "Gentoo"

    ```bash
    sudo emerge --ask sci-libs/nfft
    ```

    The ebuild builds all modules. The USE flag `openmp` adds the OpenMP
    library, `doc` adds the documentation. The package has only testing
    keywords (`~amd64`, `~x86`). Accept the keyword in
    `/etc/portage/package.accept_keywords` before you install it.

    Source: [packages.gentoo.org](https://packages.gentoo.org/packages/sci-libs/nfft).

=== "Nix"

    ```bash
    nix-shell -p nfft
    ```

    The attribute is `nfft`. It builds all modules with OpenMP.

    Source: [nixpkgs package.nix](https://github.com/NixOS/nixpkgs/blob/master/pkgs/by-name/nf/nfft/package.nix).

=== "FreeBSD"

    ```bash
    sudo pkg install nfft
    ```

    The port is `math/nfft`. It builds all modules. The port option
    `OPENMP` adds the OpenMP library. It is on by default on amd64,
    aarch64, powerpc64 and powerpc64le. To change an option, build the port
    with `make config install` in `/usr/ports/math/nfft`.

    Source: [FreshPorts math/nfft](https://www.freshports.org/math/nfft/).

=== "MSYS2"

    ```bash
    pacman -S mingw-w64-ucrt-x86_64-nfft
    ```

    The package exists for each MSYS2 environment:
    `mingw-w64-ucrt-x86_64-nfft`, `mingw-w64-x86_64-nfft`,
    `mingw-w64-clang-x86_64-nfft` and `mingw-w64-clang-aarch64-nfft`.
    Install the one for the environment you compile in. It builds all
    modules with OpenMP.

    Source: [packages.msys2.org](https://packages.msys2.org/base/mingw-w64-nfft).

=== "MacPorts"

    ```bash
    sudo port install nfft-3
    ```

    The port name is `nfft-3`. It builds all modules. Variants change the
    build:

    | Variant | Effect |
    |---------|--------|
    | `+openmp` | Adds the OpenMP library `libnfft3_omp`. |
    | `+gaussian` | Uses the Gaussian window. |
    | `+bspline` | Uses the B-spline window. |
    | `+sinc` | Uses the sinc power window. |

    The three window variants exclude each other. Add variants to the
    install command, for example `sudo port install nfft-3 +openmp +gaussian`.
    [Window functions](../guide/windows.md) compares the windows.

    Source: [ports.macports.org](https://ports.macports.org/port/nfft-3/).

=== "Spack"

    ```bash
    spack install nfft
    ```

    The package builds one library for each precision that the `fftw`
    package provides. It does not pass `--enable-all` or `--enable-openmp`,
    so it has only the NFFT, NFCT and NFST modules and no OpenMP library.

    Source: [Spack package nfft](https://packages.spack.io/package.html?name=nfft).

Fedora and openSUSE have no current package. Fedora shipped `nfft` only in
EPEL 7. For all other ecosystems, see Repology:
[nfft](https://repology.org/project/nfft/) and
[nfft-3](https://repology.org/project/nfft-3/). A Homebrew package is not
available yet.

The badges below come from Repology and show the current package versions.

[![Packaging status for nfft](https://repology.org/badge/vertical-allrepos/nfft.svg)](https://repology.org/project/nfft/versions)

[![Packaging status for nfft-3](https://repology.org/badge/vertical-allrepos/nfft-3.svg)](https://repology.org/project/nfft-3/versions)

## Source build

To build by hand, for example for a module, precision or window that no
package has, see [Build from source](build-from-source.md). The short form:

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
