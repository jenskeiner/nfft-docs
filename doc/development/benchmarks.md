# Benchmarks

The benchmarks track the speed of the transforms from commit to commit. They use
the [CodSpeed](https://codspeed.io) C++ integration, which is built on
google_benchmark. CI runs them to catch performance regressions. Build them with
CMake.

## What is measured

Four programs live in `benchmarks/`. Each has an OpenMP variant with the
suffix `_omp`, built when OpenMP is on.

| Program | Content |
|---------|---------|
| `bench_nfft_direct` | `nfft_trafo_direct` and `nfft_adjoint_direct` in 1, 2 and 3 dimensions. |
| `bench_nfft_fast` | `nfft_precompute_one_psi`, `nfft_trafo` and `nfft_adjoint` with the `PRE_PSI` precomputation. |
| `bench_nfct_direct` | The direct cosine transforms, same layout as `bench_nfft_direct`. |
| `bench_nfst_direct` | The direct sine transforms, same layout as `bench_nfft_direct`. |

`bench_nfft_fast` runs size sweeps in 1, 2 and 3 dimensions, one 4-dimensional
case that uses the generic path, a sweep over the node count $M$ at fixed $N$
in 1 dimension, and a sweep of the cut-off $m$ around its default. Every plan
comes from `nfft_init_guru` with the flags `PRE_PHI_HUT | PRE_PSI | MALLOC_X |
MALLOC_F_HAT | MALLOC_F | FFTW_INIT | FFT_OUT_OF_PLACE`, with $\sigma=2$. The
OpenMP adjoint therefore uses atomic additions, see [OpenMP](../guide/openmp.md).
Precomputation and the two transforms are separate benchmarks. The transform
benchmarks reuse the table that the precomputation benchmark of the same
geometry left behind.

### Benchmark names

The name of a benchmark is the unit that CodSpeed tracks. Keep it stable when
you change code. The name has the form

```text
benchmarks/<file>.cpp::<BENCHMARKS_PREFIX><function><suffix>/<arguments>
```

`BENCHMARKS_PREFIX` is `<BUILD_CONFIG>/` with
`BUILD_CONFIG = <os>_<compiler>_<window>_<precision>`. The suffix is `_omp` in the
OpenMP programs and empty otherwise. CodSpeed adds the file prefix. The `BENCH`
macro in `benchmarks/util.h` builds the middle part.

## Building and running

The CMake build fetches and builds the CodSpeed library itself. One option,
`NFFT_BENCHMARK_MODE`, turns the benchmarks on and selects the measurement mode.
The mode is fixed when you build.

| Mode | Effect |
|------|--------|
| `off` | The benchmarks are not built. This is the default. |
| `simulation` | Counts instructions. The binary measures only under `valgrind --tool=callgrind`. Read the `I refs` value. Run directly, it does nothing. |
| `walltime` | Measures the wall-clock time. The binary writes statistics as JSON to `$CODSPEED_PROFILE_FOLDER/results/<pid>.json`. It needs no valgrind and no runner. |

```bash
cmake -S . -B build-cmake -DNFFT_BENCHMARK_MODE=walltime -DNFFT_ENABLE_OPENMP=ON \
      -DCMAKE_C_FLAGS="-O3 -g -fomit-frame-pointer -fstrict-aliasing -ffast-math"
cmake --build build-cmake -j
CODSPEED_PROFILE_FOLDER=/tmp/wt build-cmake/benchmarks/bench_nfft_direct
```

To switch the mode, configure again with another `-DNFFT_BENCHMARK_MODE`, or use
a second build directory.

Further options:

| Option | Effect |
|--------|--------|
| `-DBENCHMARKS_PREFIX=<text>` | The prefix in every benchmark name. |
| `-DNFFT_AGNOSTIC_BENCHMARKS="window:1,openmp:0,precision:1"` | Selects the matrix cells that build the benchmarks. At present only `window` has an effect: with `window:0` the benchmarks are not built. |
| `-DFETCHCONTENT_SOURCE_DIR_CODSPEED=<path>` | Uses a checkout of `codspeed-cpp` instead of fetching it. Useful offline. |

CI builds the benchmarks for the `kaiserbessel` window only. The dev container
contains the CodSpeed fork of valgrind and the `codspeed` command line tool.

!!! note "Autotools"

    The older Autotools path, `./configure --enable-benchmarks
    --with-codspeed=<path>` and `make bench`, needs a hand-built `codspeed-cpp`
    and prints no measurements. Use the CMake build.

## Stable measurements

The programs contain a few measures against noise from the environment.

- The setup function limits the OpenMP team to 2 threads, unless
  `OMP_NUM_THREADS` is set. A small fixed team does not depend on the host.
- The setup function also sets the allocation hooks of the library,
  `nfft_malloc_hook` and `nfft_free_hook`. Every plan array then starts at a
  multiple of 64 bytes and has a size that is a multiple of 64 bytes. Without
  this, a change in the size of one early allocation can shift the other arrays
  and move a cache-resident benchmark by several percent.
- `bench_nfft_fast` keeps one plan alive at a time and reuses it for all
  benchmarks of the same geometry. Each benchmark has a warm-up of 0.1 s, so the
  clock ramp-up and the start of the OpenMP team do not fall into the first
  measured rounds.

## In CI

The workflow `.github/workflows/bench-linux.yml` runs the benchmarks.

| Item | Value |
|------|-------|
| Trigger | Push to `main`, `develop` or `master`, pull requests to them, and manual dispatch. Only changes in `kernel/`, `include/`, `benchmarks/`, `cmake/`, `CMakeLists.txt` or the workflow file start it. |
| Runner | `codspeed-macro` |
| Matrix | gcc, Kaiser-Bessel window, double and float precision, OpenMP on |
| Mode | `walltime` |
| Compiler flags | `-O3 -g -fomit-frame-pointer -fstrict-aliasing -ffast-math -falign-functions=64 -falign-loops=32` |
| Programs | All four programs, and the `_omp` variants, with `--benchmark_min_time=0.1s` |
| OpenMP environment | `OMP_PROC_BIND=close`, `OMP_PLACES=cores`, `OMP_DYNAMIC=false` |

The alignment flags fix the code layout, so that the change of one function does
not move the hot loop of another. The workflow builds CodSpeed `v2.3.0` and caches
the checkout.

A pull request run waits for the approval of a reviewer, because the job refers
to the protected environment `benchmarks`. Pushes to the default branches and
manual runs start at once. A new push to a pull request cancels the older run of
that pull request. The workflow uses the event `pull_request`, never
`pull_request_target`, so code from forks runs without a write token and without
secrets.

## Adding a benchmark

1. Write the benchmark function. Register it with `BENCH(function, SUFFIX)`, so
   that the name gets the prefix and the `_omp` suffix.
2. Add the program or the source to `benchmarks/CMakeLists.txt` and to
   `benchmarks/Makefile.am`. Add an `_omp` target in the OpenMP section.
3. Add the program to the run list in `bench-linux.yml`.
4. Do not rename existing benchmarks. A new name starts a new history in
   CodSpeed.
