# A first transform

A one-dimensional NFFT: 14 Fourier coefficients evaluated at 19 arbitrary
nodes, checked against the direct sum.

## The program

This is `examples/nfft/simple_test.c`, which is built and run by the test
suite, so it cannot go stale. The excerpts below are taken from it. The file
includes `nfft3mp.h`, so one source serves all three precisions.

```c
#include <stdio.h>
#include <math.h>
#include <string.h>
#include <stdlib.h>

#define NFFT_PRECISION_DOUBLE

#include "nfft3mp.h"
```

`nfft3mp.h` is the precision-agnostic header. Define exactly one of
`NFFT_PRECISION_SINGLE`, `NFFT_PRECISION_DOUBLE` or
`NFFT_PRECISION_LONG_DOUBLE` before including it, and then write `NFFT(trafo)`
instead of `nfft_trafo`. Including `nfft3.h` directly and spelling the prefixes
out works too.

```c
--8<-- "examples/nfft/simple_test.c:24:73"
```

## What happens, step by step

`NFFT(init_1d)(&p, N, M)`
:   Sets up a plan for `N` coefficients and `M` nodes. It picks the
    oversampled FFT length, the cut-off `m` and a default set of flags, and
    allocates `p.x`, `p.f_hat` and `p.f` because `MALLOC_X`, `MALLOC_F_HAT` and
    `MALLOC_F` are among those defaults.

`NFFT(vrand_shifted_unit_double)(p.x, p.M_total)`
:   Fills the nodes with random values in $[-\tfrac{1}{2},\tfrac{1}{2})$. In
    your own program, write your nodes into `p.x` here.

`NFFT(precompute_one_psi)(&p)`
:   Precomputes the window values for those nodes. Which scheme it uses depends
    on the precomputation flag in `p.flags`, hence the `PRE_ONE_PSI` guard.
    Call it again whenever the nodes change.

`NFFT(check)(&p)`
:   Validates the plan and returns an error string, or a null pointer when the
    plan is sound. Call it once before the first transform; it catches the
    parameter mistakes that would otherwise show up as wrong numbers.

`NFFT(trafo)(&p)`
:   The fast transform. Reads `p.f_hat`, writes `p.f`.
    `NFFT(trafo_direct)` computes the same sum exactly and slowly; the example
    prints both so you can compare them.

`NFFT(adjoint)(&p)`
:   The adjoint. Reads `p.f`, writes `p.f_hat`. It is not the inverse; see
    the [solver](../transforms/solver.md) for that.

`NFFT(finalize)(&p)`
:   Frees everything the plan owns, including the arrays it allocated.

## Build and run it

```bash
cc first.c $(pkg-config --cflags --libs nfft3) -lm -o first
./first
```

The `ndft` and `nfft` vectors it prints agree to about the accuracy the cut-off
`m` and the oversampling buy you. The [guide](../guide/index.md) explains those
two parameters.

## Next

- [Build from source](build-from-source.md), every configure flag.
- [What the NFFT computes](../guide/index.md), the algorithm behind `trafo`.
- [Transforms](../transforms/index.md), the other modules.
