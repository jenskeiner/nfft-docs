# Precision and name mangling

The same C sources compile in three precisions. All three libraries can be
installed side by side and linked into one program, so every exported name
carries a precision prefix.

## The three builds

| Precision | Real type | Complex type | Library | FFTW | Prefix |
|-----------|-----------|--------------|---------|------|--------|
| single | `float` | `fftwf_complex` | `libnfft3f` | `libfftw3f` | `nfftf_` |
| double | `double` | `fftw_complex` | `libnfft3` | `libfftw3` | `nfft_` |
| long double | `long double` | `fftwl_complex` | `libnfft3l` | `libfftw3l` | `nfftl_` |

Double is the default. The others are selected at configure time with
`--enable-float` or `--enable-long-double`, and each needs its own configured
tree. See [Build from source](../getting-started/build-from-source.md).

Every module has its own prefix, and each of those has the same three forms:
`nfct_`/`nfctf_`/`nfctl_`, `nfsft_`/`nfsftf_`/`nfsftl_`, and so on. The
[API reference](../api/index.md) lists all three names for every function.

!!! warning "Only some modules exist in single and long double precision"
    The header declares all three forms of every function, but the library
    contains them only for NFFT, NFCT, NFST, the solver and the utility
    functions. The NFSFT, NFSOFT, NNFFT, NSFFT, MRI and FPT modules are built in
    double precision only. `./configure --enable-float` and
    `--enable-long-double` switch these modules off, and `--enable-nfsft` and
    the like stop with an error in such a tree.

## Writing precision-agnostic code

Include `nfft3mp.h` instead of `nfft3.h`, define exactly one precision macro
before the include, and write the unprefixed name inside a module macro.

```c
#define NFFT_PRECISION_DOUBLE
#include "nfft3mp.h"

NFFT(plan) p;
NFFT(init_1d)(&p, N, M);
NFFT(trafo)(&p);
NFFT(finalize)(&p);
```

Switching the program to single precision is then one line: define
`NFFT_PRECISION_SINGLE` and link `-lnfft3f`. Omitting all three macros is a
compile error, not a silent default.

| Macro | Expands to |
|-------|------------|
| `NFFT_PRECISION_SINGLE` | selects `float` |
| `NFFT_PRECISION_DOUBLE` | selects `double` |
| `NFFT_PRECISION_LONG_DOUBLE` | selects `long double` |

### What `nfft3mp.h` gives you

| Name | Meaning |
|------|---------|
| `NFFT_R` | The real type of the selected precision. |
| `NFFT_C` | The matching FFTW complex type. |
| `NFFT_K(x)` | A real literal in the selected precision. Use it for every constant. |
| `NFFT_M(name)` | Appends the precision suffix to a name. |
| `FFTW(name)` | The FFTW name for the selected precision. |
| `NFFT(name)` | The NFFT name, `nfft_trafo` and so on. |
| `NFCT(name)`, `NFST(name)` | The [NFCT](../transforms/nfct.md) and [NFST](../transforms/nfst.md) names. |
| `NFSFT(name)` | The [NFSFT](../transforms/nfsft.md) names. |
| `SOLVER(name)` | The [solver](../transforms/solver.md) names. |
| `NFFT_KPI` | $\pi$ in the selected precision. |
| `NFFT_CSWAP(x,y)` | Swap two complex vectors. |

There is **no** convenience macro for NNFFT, NSFFT, NFSOFT, FPT or MRI. Write
the prefix out, or define your own:

```c
#define NFSOFT(name) NFFT_CONCAT(nfsoft_, name)
```

### Printing

`printf` needs a different length modifier per precision, so `nfft3mp.h`
provides the format strings.

| Macro | Use |
|-------|-----|
| `NFFT__FE__` | A real in full precision, `% 20.16lE` in double. |
| `NFFT__FES__` | The bare exponent specifier, `lE` in double. |
| `NFFT__FGS__`, `NFFT__FIS__` | The `g` and `f` specifiers. |
| `NFFT__FI__`, `NFFT__FR__` | Ready-made `%lf` and `%le` forms. |
| `NFFT__D__` | An `NFFT_INT`. Windows needs `%Id` where others need `%td`. |

They are string literals, so they concatenate into the format:

```c
printf("t_fft = %1.1" NFFT__FES__ "\n", t_fft);
```

## Accuracy and the cut-off

The precision also changes the default cut-off `m`, because a shorter mantissa
needs fewer window points to reach its own accuracy. Do not hard-code it:

```c
int m = NFFT(get_default_window_cut_off)();
```

For the Kaiser-Bessel window that returns 4 in single precision, 8 in double and
9 in long double on a platform where `long double` is the x87 80-bit type. What
the cut-off does is explained in the [guide](index.md).

## Related

- [API reference](../api/index.md), the mangled names of every function.
- [Build from source](../getting-started/build-from-source.md), the configure
  flags.
