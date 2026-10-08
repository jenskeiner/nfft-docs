# Testing

The tests use [CUnit](http://cunit.sourceforge.net). They check the direct
transforms against high-precision reference data and the fast transforms against
the direct ones. The same run also records the accuracy figures that CI turns
into an [accuracy report](#accuracy-reports).

## Running the tests

The tests build only when CUnit is found at configure time and the tests are
enabled.

=== "Autotools"

    ```bash
    ./configure --enable-all --enable-openmp --enable-tests
    make check
    ```

    `make check` builds and runs `tests/checkall`. With `--enable-openmp` it also
    runs `tests/checkall_threads`, the same suite against the
    [OpenMP library](../guide/openmp.md). `checkall` is a `check_PROGRAM`, so
    `make all` does not build it. Use `make -C tests checkall` to build it alone.

=== "CMake"

    ```bash
    cmake -S . -B build -DNFFT_ENABLE_TESTS=ON
    cmake --build build -j
    ctest --test-dir build --output-on-failure
    ```

    `ctest` runs `checkall` and, with OpenMP, `checkall_threads`.

`--enable-exhaustive-unit-tests` and `-DNFFT_ENABLE_EXHAUSTIVE_UNIT_TESTS=ON` add
larger and slower cases, for example the three- and four-dimensional online
tests. CI uses them.

### Reading the results

- The console shows the result of every test and a summary.
- `make check` writes `tests/checkall.log`, `tests/checkall.trs` and the same
  files for `checkall_threads`.
- CUnit writes `tests/CUnitAutomated-Results.xml` and
  `tests/CUnitAutomated_threads-Results.xml`. The stylesheet
  `tests/cunit2junit.xsl` converts them to JUnit. CI does this.
- To run one binary and read all output, call it directly: `tests/checkall`.

## What the suites cover

`tests/check.c` registers four suites.

| Suite | Content |
|-------|---------|
| `util` | The window functions and their helpers, the Bessel and B-spline routines, the version and window name functions, and the integer helpers `log2i` and `next_power_of_2`. |
| `nfft` | Forward and adjoint NFFT in 1, 2 and 3 dimensions, and 4 dimensions in the exhaustive set. |
| `nfct` | The same for the cosine transform. |
| `nfst` | The same for the sine transform. |

The modules NNFFT, NSFFT, MRI, FPT, NFSFT, NFSOFT and the solver have no CUnit
suite. Their examples and applications are built but not run by `make check`.

Each transform suite has two classes of test.

1. **File-based check.** The test reads a reference from `tests/data/*.txt`. It
   runs both the direct and the fast transform on the input of the file and
   compares them with the reference. This validates the direct transform. The reference comes from the [generator](#reference-data).
2. **Online check.** The test creates random input with a fixed seed and
   computes the reference with the direct transform. It compares the fast
   transform against it at larger sizes. It reads no file.

The fast transforms run with several initialisation variants: `init_1d`,
`init_2d`, `init_3d`, `init`, and `init_guru` with different flags. A Gaussian
window build adds the `FG_PSI` variants and the tests with fixed small $m$.

### Error and bound

Each case computes

$$
\text{err}=\frac{\max_j\,\lvert f_j-\tilde f_j\rvert}{\sum_k\lvert\hat f_k\rvert}
$$

for the forward transform. The adjoint swaps the roles of $f$ and $\hat f$. A case
passes when $\text{err}<\text{bound}$. The direct transforms have a bound of the
form $C\,\varepsilon$ from round-off. The fast transforms have a window and
precision dependent bound that adds the truncation error. The formulas are on the
[Accuracy](../guide/accuracy.md) page. The bounds scale with the machine
epsilon of the build precision, so they follow the precision automatically.

### Reference data

The files in `tests/data/` come from a Python generator, `tests/refgen/`. It
computes the direct transform with `mpmath` at 64 digits and writes

- the data files `tests/data/*.txt`,
- the C headers `tests/data/generated/<module>_testcases.h` with the case lists,
- the file list in `tests/data/Makefile.am`.

The C build does not run Python. The generated files are committed. Regenerate
them from the repository root with:

```bash
uv run --with mpmath==1.3.0 python -m tests.refgen.generate --module all --precision 64
```

The generator has its own tests:

```bash
uv run --with mpmath==1.3.0 --with pytest python -m pytest tests/refgen/tests -q
```

A data file holds blank-line separated sections, one number per line: the
dimension, the bandwidths $N_t$, the node count $M$, the nodes, the input
coefficients or samples, and the reference output. File names follow
`<module>[_adjoint]_<d>d_<N0>[_<N1>...]_<M>.txt`. The nodes and the input are
single-precision numbers, so they are exact in every build precision. The
output carries at least 64 significant digits. The C reader rounds each value to
the build precision. One set of files serves every precision.

### Window and special function tests

`tests/window.c` bounds the window evaluations against reference values. The
Kaiser-Bessel tables come from `mpmath` and are in the file with the recipe. The
B-spline and sinc-power tables come from a generator:

```bash
uv run --with mpmath==1.3.0 python -m tests.windowref.generate
```

The generator prints C literals for pasting into `tests/window.c`. The tests call
the window kernels of `include/infft.h` directly, so they run in every window
build.

The coefficient tables of the Bessel function $I_0$ and of $\log|\mathrm{sinc}|$
come from two other generators, `tests/besselgen` and `tests/sincgen`. Do not
edit `kernel/util/bessel_i0_data.h` or `kernel/util/sinc_data.h` by hand. Run
the generators:

```bash
uv run --with mpmath==1.3.0 python -m tests.besselgen.generate
uv run --with mpmath==1.3.0 python -m tests.sincgen.generate
```

## Accuracy reports

Every case can also write its error and bound to a file. CI builds an HTML
report from these records. The report shows the value of the error, so a slow
drift is visible before a case crosses its bound. It never decides whether CI
passes. Only the comparison in C decides.

### How the report is made

1. **Record.** When the environment variable `NFFT_BENCH_OUT` names a file, each
   case appends one JSON line with module, oracle, dimension, `N`, `M`, the init
   variant, the transform name, the error and the bound. Without the variable
   nothing is written. `checkall_threads` writes to `$NFFT_BENCH_OUT.threads` and
   marks its records `"openmp": 1`.
2. **Aggregate.** `tests/accuracy/ndjson_to_bmf.py` groups the records by the
   parameters that shape the error. It takes the maximum over `N` and `M`,
   whose effect the bound already contains. The result has one metric per group.
   The metric name is
   `<module>/<runtime>/<oracle>/<speed>/<direction>/<dim>d/<init>`. `runtime` is
   `serial` or `omp`.
3. **Render.** `tests/accuracy/htmlreport.py` writes one self-contained HTML
   file. It uses no JavaScript. Each window is a tab. Each module is a table with
   one column per precision. A cell is coloured by its margin: the digits of
   accuracy, $-\log_{10}(\text{err}_{\max})$, minus the digits of the bound.
   Red is an error above the bound, yellow is barely passing and green has
   headroom. Grey is missing data.

The metric name must stay stable. The pull request diff joins two reports by
this name, so a renamed metric shows as added and removed.

### In CI

The `Build Linux` workflow runs `make check` with `NFFT_BENCH_OUT` set. Each
gcc cell converts its records and uploads them. The `accuracy-report` job then
builds the report.

| Event | Result |
|-------|--------|
| Push to `develop` | The dashboard and the baseline data go to `gh-pages` under `accuracy/`. |
| Pull request from the repository | The job compares the pull request with the baseline, publishes the report under `accuracy/pr/<n>/`, and posts a check and a comment with the changes per module. A case counts as changed when its digits move by 0.5 or more. |
| Pull request from a fork | A second workflow, `accuracy-report-fork.yml`, posts the comment and the check. It links to the `develop` dashboard. |

The published dashboard of the `develop` branch is at
`https://nfft.github.io/nfft/accuracy/`. The report steps do not fail the build.
If the comment link does not work, GitHub Pages may be off for the repository.

### Locally

```bash
NFFT_BENCH_OUT="$PWD/tests/accuracy.ndjson" tests/checkall > /dev/null
# With OpenMP, this also writes tests/accuracy.ndjson.threads:
NFFT_BENCH_OUT="$PWD/tests/accuracy.ndjson" tests/checkall_threads > /dev/null
cat tests/accuracy.ndjson tests/accuracy.ndjson.threads > tests/accuracy.all.ndjson 2>/dev/null \
  || cp tests/accuracy.ndjson tests/accuracy.all.ndjson
mkdir -p /tmp/bmf
uv run python -m tests.accuracy.ndjson_to_bmf tests/accuracy.all.ndjson \
  /tmp/bmf/local_gcc_kaiserbessel_double.bmf.json
uv run python -m tests.accuracy.dashboard /tmp/bmf /tmp/site
```

Open `/tmp/site/index.html`. The name of the `.bmf.json` file is the testbed:
`<os>_<compiler>_<window>_<precision>`. Only the NFFT, NFCT and NFST suites
write records. To add a module, include `accuracy_log.h` in its test harness and
call `accuracy_log_append` once per case.

## Adding tests for a new transform

1. In `tests/refgen/`, add the direct transform and the frequency index set to
   `transforms.py`, the grids to `grids.py`, and the module name to
   `registration.py`. Add self-tests under `tests/refgen/tests`.
2. Copy `tests/nfct.c` for a real transform or `tests/nfft.c` for a complex one.
   Change the included header, the number of coefficients, the direct bound
   constant, the bound tables for each window and precision, and the grids.
   Include `data/generated/<module>_testcases.h` for the file-based cases.
3. In `tests/check.c`, add the include, an `#ifdef HAVE_<MODULE>` guard, the
   `X(name)` definition, a suite and the tests.
4. Add the sources to `tests/Makefile.am` and to the list in
   `tests/CMakeLists.txt`. Add the generated header to `EXTRA_DIST`.
5. Run the generator for the module, then `make check`.

The module must provide `init` functions, `precompute_one_psi`, `trafo`,
`trafo_direct`, `adjoint`, `adjoint_direct`, `check` and `finalize`, and a plan
with the members `x`, `f`, `f_hat`, `m`, `sigma`, `d`, `N`, `M_total` and
`flags`. A transform without an exact reference, such as an iterative solver,
needs another kind of test, for example a check of convergence or of the
recovery of a known input.

## Other checks in CI

| Check | Where |
|-------|-------|
| Julia examples, `simple_test*.jl` | `Build Linux`, double precision |
| Octave interface tests | Separate job `cmake-octave` in `Build Linux` |
| `make distcheck` | Job `distcheck` in `Build Linux` |
| API page generator against `include/nfft3.h` | `Docs` workflow |
| Site checks after `zensical build --strict` | `Docs` workflow |

See [Build matrix](build-matrix.md) for the workflows.
