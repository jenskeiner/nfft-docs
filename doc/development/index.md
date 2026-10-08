# Contributing

NFFT3 is a research-grade numerical library in C. This page describes how to set
up a working tree, the conventions the code follows, and what a change needs
before it can merge. The other pages in this section cover the
[build matrix](build-matrix.md), the [tests](testing.md), the
[benchmarks](benchmarks.md) and [releases](releasing.md).

## Set up a working tree

The repository has a development container in `.devcontainer/`. It is Ubuntu
24.04 with gcc 14, clang, FFTW in all three precisions, CUnit, Octave, Julia,
the Autotools and clang-format. You can also install these tools on your host.

Build from a git checkout with Autotools:

```bash
./bootstrap.sh
./configure --enable-all --enable-openmp --enable-tests
make -j
make check
```

`bootstrap.sh` generates `configure`. Run it again after each change of a
`Makefile.am` or of `configure.ac`. The tests are off by default, so pass
`--enable-tests`. [Build from source](../getting-started/build-from-source.md)
lists all options.

CMake builds the same sources. It exists next to Autotools and does not replace
it. A change to a build file of one system must not break the other. The list of
configuration macros in `configure.ac` is the source of truth. The file
`cmake.config.h.in` mirrors it, and `cmake/config-parity-check.sh` compares the
two.

| Task | Autotools | CMake |
|------|-----------|-------|
| Configure | `./configure --enable-all --enable-openmp --enable-tests` | `cmake -S . -B build -DNFFT_ENABLE_TESTS=ON` |
| Build | `make -j` | `cmake --build build -j` |
| Test | `make check` | `ctest --test-dir build` |
| Clean | `make clean`, `make distclean` | remove the build directory |

Each precision and each window needs its own configured tree, in either system.

## Repository layout

| Path | Content |
|------|---------|
| `include/` | `nfft3.h` and `nfft3mp.h`, the two installed headers. `infft.h` and `api.h` are internal. |
| `kernel/<module>/` | One directory per module. The NFFT is `kernel/nfft/nfft.c`. |
| `kernel/util/` | Helpers shared by all modules: the window functions, memory, sorting, error norms, threads. |
| `tests/` | The CUnit suites, the reference data and its generators. See [Testing](testing.md). |
| `examples/` | Small programs for each module. |
| `applications/` | Larger programs, such as fast summation, MRI and the Radon transform. |
| `benchmarks/` | The CodSpeed benchmarks. See [Benchmarks](benchmarks.md). |
| `matlab/`, `julia/` | The MATLAB, Octave and Julia interfaces. |
| `doc/`, `support/`, `zensical.toml` | The documentation site and its tools. |
| `cmake/`, `m4/` | The CMake modules and the Autotools macros. |
| `docs/adr/`, `CONTEXT.md` | Architecture decisions and the project vocabulary. |

## Code conventions

The library is **precision agnostic**. The same sources compile in float, double
and long double. `CONVENTIONS.md` in the repository root holds the rules. This
section summarises them.

### Types and macros

The internal header `include/infft.h` defines these names for library code.

| Name | Meaning |
|------|---------|
| `R` | The real type of the build: `float`, `double` or `long double`. |
| `C` | The matching complex type. |
| `INT` | The integer type for sizes and strides, `ptrdiff_t`. |
| `K(x)` | A real literal of type `R`. Write `K(0.5)`, never `0.5`. |
| `X(name)` | A name local to a module. In the NFCT module `X(foo)` expands to the prefix `nfct_` followed by `foo`. |
| `Y(name)` | A name exported by the whole library. `Y(foo)` expands to `foo` with the prefix `nfft_`, `nfftf_` or `nfftl_`. |
| `FFTW(name)` | The FFTW name of the precision, for example `fftw_plan_dft`. |
| `NFFT(name)`, `NFCT(name)`, `NFST(name)`, `NFSFT(name)`, `SOLVER(name)` | The names of the modules in the precision of the build. |
| `A(cond)` | An assertion that is active only with `--enable-debug`. |
| `CK(cond)` | A check that is always active. |

Never write the prefix `nfft_`, `nfftf_` or `nfftl_` by hand. Use `Y(foo)` for a
name that other files or users call, and `X(foo)` inside a module. A name that is
not exported needs no mangling.

The macros `EPSILON`, `MANT_DIG`, `KPI` and `K2PI` give the machine epsilon, the
mantissa length and the constants $\pi$ and $2\pi$ in the build precision.
Precision dependent code branches on `MANT_DIG`: 24 for float, 53 for double, 64
for x87 long double and 113 for quadruple precision. Programs that use the
library, not the library itself, follow the rules on the
[precision](../guide/precision.md) page.

### Code style

- Indent with two spaces. Do not use tabs.
- Separate operators and operands with one space, as in `int a = 0x1 + 0x2;`.
- Use the BSD brace style for new code. `CONVENTIONS.md` shows it. The GNU
  variant with a space before the parenthesis of a call is also allowed. Use one
  style in one file.
- Follow the style of the lines around your change. Do not reformat lines you do
  not change. If a change touches an existing section, refactor that section to
  the chosen style.
- The repository has a `.clang-format` file. Use `clang-format` on the lines you
  add, not on a whole file. Its settings differ from `CONVENTIONS.md` in one
  point: it puts the opening brace of a control statement on the same line. Follow
  the surrounding code where the two disagree.
- New source files carry the license header from `support/copyright.txt`.

### Portability

New code must keep the whole matrix working: the three precisions, all four
windows, with and without OpenMP, and both build systems. The
[build matrix](build-matrix.md) lists what CI checks.

## Adding a module

Each transform module has its own directory under `kernel/` with its own
`Makefile.am`. A new module touches these places.

1. **Sources.** Create `kernel/<module>/<module>.c` and
   `kernel/<module>/Makefile.am`. If the module has OpenMP code, build a second
   library `lib<module>_threads.la` from the same source with `$(OPENMP_CFLAGS)`.
   `kernel/nfft/Makefile.am` is an example.
2. **Autotools.** In `configure.ac`, add
   `AX_NFFT_MODULE([<module>],[<MODULE>],[<description>],["no"])`. The
   fourth argument is `"no"` for a module that builds in double precision only and
   `"yes"` for a module that builds in every precision. The macro defines the flag
   `--enable-<module>` and the conditional `HAVE_<MODULE>`. In
   `kernel/Makefile.am`, add the `LIB_` and `DIR_` variables, the entry in
   `SUBDIRS` and the library in `libkernel_la_LIBADD`. Add the threaded library
   to `libkernel_threads_la_LIBADD`. Run `./bootstrap.sh`.
3. **CMake.** Add the source to `NFFT_KERNEL_SOURCES` in
   `kernel/CMakeLists.txt`, in the double-only list if that applies. Set
   `HAVE_<MODULE>` in `cmake/nfft_config.cmake` and add the `#cmakedefine` line to
   `cmake.config.h.in`.
4. **Public header.** In `include/nfft3.h`, add the name mangling macros and a
   `<MODULE>_DEFINE_API(X, ...)` macro, and expand it once per precision. The
   plan structure and the functions belong in that macro.
5. **Documentation.** Document each function in a `/** */` block above its
   prototype inside the macro, in Markdown. Add the module to `MODULES` in
   `support/apigen/generate.py`, write a page under `doc/transforms/`, and add it
   to the navigation in `zensical.toml` and to the file list in the top-level
   `Makefile.am`. See below.
6. **Tests.** Add a test suite as described in [Testing](testing.md), or state in
   the pull request why the module has none.
7. **Example.** Add a small program under `examples/<module>/`. Both build
   systems must build it.

## Documentation

The documentation site is built with [Zensical](https://zensical.org). The
Markdown sources are in `doc/`. The API reference under `doc/api/` is generated
from `include/nfft3.h` and is not in git. Run every command from the repository
root.

```bash
# Generate the API pages. They are an input of the build.
uv run python -m support.apigen

# Preview at http://127.0.0.1:8000
uv run --with-requirements support/docs-requirements.txt zensical serve

# Build into site/. --strict stops on broken links and anchors.
uv run --with-requirements support/docs-requirements.txt zensical build --strict
```

Zensical is alpha, and `support/docs-requirements.txt` pins it. `--strict` checks
only links and anchors inside pages. It does not check the navigation, the
extra style sheets and scripts, or the theme features. Look at the built `site/`
after you change `zensical.toml`. CI runs `.github/scripts/docs-check-site.py`
for these checks.

Two rules apply to the doc comments in `include/nfft3.h`:

- Every line of the comment ends with a backslash. The line that closes the
  comment would otherwise end the `#define`.
- The body is Markdown with `$...$` for math. It is not Doxygen markup.

`support/apigen/test_apigen.py` tests both rules. Run it with
`uv run python -m support.apigen.test_apigen`.

Zensical copies every file of `doc/` that is not Markdown into the site. Keep
build products out of `doc/`.

The repository also builds an offline HTML documentation with Doxygen, in
`doxygen/html`. The Zensical site is the primary documentation.

## Generated files

Two coefficient tables are generated. Do not edit them by hand.

| File | Generator |
|------|-----------|
| `kernel/util/bessel_i0_data.h`, used by the Kaiser-Bessel window | `uv run --with mpmath==1.3.0 python -m tests.besselgen.generate` |
| `kernel/util/sinc_data.h`, used by the B-spline and sinc-power windows | `uv run --with mpmath==1.3.0 python -m tests.sincgen.generate` |

The test data is generated as well. See [Testing](testing.md#reference-data).

## Branches and pull requests

The default branch is `develop`. CI runs for pushes and pull requests to
`develop`, `main` and `master`.

1. Branch from `develop`.
2. Build with your usual configuration and run `make check`. For a change to the
   numerics, build a second window or a second precision as well.
3. Open a pull request against `develop`.
4. CI builds the [matrix](build-matrix.md) and posts an accuracy comment. When
   the change touches the kernel, the headers or the benchmarks, it also runs the
   [benchmarks](benchmarks.md) after a reviewer approves.
5. Label the pull request. The release drafter groups the release notes by
   label: `feat`, `refactor` and `style`, `removal`, `bug` and `fix`,
   `deprecation`, `docs`, and `chore`. See [Releasing](releasing.md).

Do not commit build products. The tree contains generated files that are not
tracked, such as `doc/api/` and `site/`.

## Project vocabulary and decisions

`CONTEXT.md` fixes the words the project uses, for example *precision suffix*,
*file-based check*, *online check*, *accuracy metric* and *benchmark name*. Use
these terms in code comments, issues and pull requests. The directory
`docs/adr/` records the decisions behind the build and test design:

| ADR | Decision |
|-----|----------|
| 0001 | A CMake build next to Autotools, never instead of it. |
| 0002 | A Python and mpmath generator for the reference data. |
| 0003 | The reference data is ready for quadruple precision. The quad build is not implemented. |
| 0004 | HTML accuracy reports in the tree, published with GitHub Pages. |
| 0005 | The documentation site with Zensical, versioned on `gh-pages`. |

If a change contradicts an ADR, say so in the pull request.
