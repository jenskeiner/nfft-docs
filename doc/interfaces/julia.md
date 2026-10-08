# Julia

The directory `julia/` of the source tree holds Julia bindings for the
[NFFT](../transforms/nfft.md), [NFCT](../transforms/nfct.md),
[NFST](../transforms/nfst.md) and [NFSFT](../transforms/nfsft.md) modules and
for the [fast summation](../applications/fastsum.md) application. Each binding
is a Julia module that calls a small C library through `ccall`. The C library
does not depend on your Julia installation.

## The NFFT3 Julia package

The NFFT3 is also available as a Julia package, hosted at
<https://github.com/NFFT/NFFT3>. The file `julia/README.md` gives these
commands:

```julia
using Pkg
Pkg.add("NFFT3")
using NFFT3
```

The rest of this page describes the in-tree bindings in `julia/`, which you
build together with the C library.

## Build the interface

Add `--enable-julia` to the `configure` call. See
[Build from source](../getting-started/build-from-source.md) for the other
options.

```bash
./configure --enable-all --enable-shared --enable-julia
make
```

The interface has two requirements, and `configure` stops with an error if one
is not met.

- The library must be built in double precision.
- Shared libraries must be enabled with `--enable-shared`.

With `--enable-all`, the Julia interface is enabled by default in double
precision when shared libraries are enabled.

Each module builds one shared library in its own subdirectory of `julia/`. The
libraries are `libnfftjulia`, `libnfctjulia`, `libnfstjulia`, `libnfsftjulia`
and `libfastsumjulia`. The suffix is `.so`, `.dll` on Windows and `.dylib` on
macOS. The modules `nfct`, `nfst` and `nfsft` are built when the corresponding
C module is enabled. The module `fastsum` is built when the application
programs are enabled.

The CMake build has the option `-DNFFT_ENABLE_JULIA=ON`. It needs CMake 3.24 or
newer, double precision and `-DBUILD_SHARED_LIBS=ON`. CMake installs each
library together with its `.jl` file into `share/nfft/julia/<module>/`.

## Load a module

A module finds its shared library in its own directory: the path is built from
`@__DIR__` and the library name. Do not move the `.jl` file away from the
library. To load the module, add its directory to the `LOAD_PATH`:

```julia
push!(LOAD_PATH, "/path/to/nfft/julia/nfft/")
using NFFT
```

Use the directory `nfct/`, `nfst/`, `nfsft/` or `fastsum/` for the other modules.
The Autotools build does not install the `.jl` files. Use them from the build
directory as above.

The file `julia/nfft/README.md` states that the interface was tested with Julia
1.0.0 and 1.1.0 and does not work with earlier versions. The example programs
also ran with Julia 1.12.7.

## Calling conventions

All modules share one pattern. A plan is a Julia object. You set its data by
assigning to its fields. You call a transform as a function of the module.

| Module | Plan constructor | Function prefix |
|--------|------------------|-----------------|
| `NFFT` | `Plan(N, M)` | `NFFT.trafo(p)` |
| `NFCT` | `NFCTplan(N, M)` | `NFCT.trafo(p)` |
| `NFST` | `NFSTplan(N, M)` | `NFST.trafo(p)` |
| `NFSFT` | `NFSFTplan(N, M)` | `NFSFT.trafo(p)` |
| `fastsum` | `fastsum.Plan(d, N, M, n, p, kernel, c, eps_I, eps_B, nn, m)` | `fastsum.trafo(p)` |

The modules `NFFT`, `NFCT`, `NFST` and `NFSFT` export their plan constructor.
The module `fastsum` exports nothing. The transform functions are not exported.
Call `NFFT.trafo(p)`, because the function names are the same in every module.

### NFFT, NFCT and NFST

`N` is a tuple with one entry per dimension, for example `(N,)` for one
dimension and `(N1, N2)` for two. The dimension `D` is the length of the tuple.
`M` is the number of nodes. Each entry of `N` must be a positive integer. For
`Plan` it must be even.

`Plan(N, M)` chooses the oversampling `n` per dimension as
$2 \cdot 2^{\lceil \log_2 N_t \rceil}$, the cut-off `m = 8` and default flags.
The long form sets all parameters:

```julia
Plan(N, M, n, m, f1, f2)
```

Here `n` is the tuple of oversampled FFT lengths, `m` is the window cut-off, `f1`
holds the NFFT flags and `f2` the FFTW flags. Both flags are `UInt32` values.
The module defines the flag names, for example `PRE_PHI_HUT`, `PRE_PSI`,
`FFTW_ESTIMATE` and `FFTW_MEASURE`. See [Plans and flags](../guide/plans-and-flags.md)
for their meaning. The long form of `Plan` uses
`nfft_get_default_window_cut_off` as default for `m`. The allocation flags
`MALLOC_X`, `MALLOC_F_HAT`, `MALLOC_F` and `FFTW_INIT` are always added.

A plan has the fields below. You assign `x`, `f` and `fhat`. The other fields
are read only, and an assignment gives a warning.

| Field | Type | Meaning |
|-------|------|---------|
| `x` | `Vector{Float64}` for $d=1$, `Matrix{Float64}` of size $d \times M$ for $d>1$ | Nodes. |
| `fhat` | `Vector{ComplexF64}` of length `prod(N)` | Fourier coefficients. |
| `f` | `Vector{ComplexF64}` of length `M` | Samples. |
| `N`, `M`, `n`, `m`, `f1`, `f2` | | The plan parameters. |
| `num_threads` | `Int64` | Number of threads in use. |

The types are strict. Assigning a vector of another element type raises an
error. For NFCT and NFST, `f` and `fhat` are `Vector{Float64}`. The length of
`fhat` is `prod(N)` for NFCT and `prod(N .- 1)` for NFST. The examples for NFCT and
NFST use nodes in $[0, 1/2]$.

The Fourier coefficients of a multidimensional plan are stored in the layout of
the C plan: the last dimension runs fastest. For an $N_1 \times N_2$ plan the
index of $\hat f_{k_0,k_1}$ in `fhat` is $(k_0 + N_1/2) N_2 + (k_1 + N_2/2)$,
counted from zero.

The first assignment to a field creates the C plan. Assigning `x` also runs the
node-dependent precomputation. Set `x` before you call a transform.

| Function | Effect |
|----------|--------|
| `NFFT.trafo(p)` | Forward transform. Reads `fhat`, writes `f`. |
| `NFFT.adjoint(p)` | Adjoint transform. Reads `f`, writes `fhat`. |
| `NFFT.trafo_direct(p)` | Direct forward transform. |
| `NFFT.adjoint_direct(p)` | Direct adjoint transform. |
| `NFFT.get_num_threads()` | Number of threads. |
| `NFFT.set_num_threads(n)` | Set the number of threads. |
| `NFFT.finalize_plan(p)` | Free the C plan. |

The plan is also freed by the Julia finalizer when the garbage collector removes
it.

The results of `trafo` and `adjoint` are views of C memory. Copy them, for
example with `copy(p.f)`, if you keep them after the next transform.

### NFSFT

`NFSFTplan(N, M)` takes the polynomial degree `N` and the number of nodes `M`.
The optional arguments are `flags`, `nfft_flags` and `nfft_cutoff`, with default
6. The constructor calls the precomputation of the NFSFT with the threshold
1000.0.

The nodes `x` are a `Matrix{Float64}` of size $2 \times M$. The vector `fhat`
has length $(2N+2)^2$. The function `NFSFT.nfsft_index(p, k, n)` returns the
zero-based position of the coefficient of degree `k` and order `n`. Use
`fhat[NFSFT.nfsft_index(p, k, n) + 1]`.

### Fast summation

`fastsum.Plan` takes the dimension `d`, the numbers of source and target nodes
`N` and `M`, the expansion degree `n`, the degree of smoothness `p`, the kernel
name, the kernel parameter `c`, the boundaries `eps_I` and `eps_B`, the
oversampled degree `nn` and the NFFT cut-off `m`. The fields to set are:

| Field | Type |
|-------|------|
| `x` | source nodes, `N` values for $d=1$, an $N \times d$ matrix otherwise |
| `y` | target nodes, `M` values for $d=1$, an $M \times d$ matrix otherwise |
| `alpha` | `Vector{ComplexF64}` of length `N` |
| `f` | result, read after the call |

Call `fastsum.trafo(p)` for the fast algorithm and `fastsum.trafo_exact(p)` for
the direct sum. The result is in `p.f`.

The Julia interface accepts these kernel names: `gaussian`, `multiquadric`,
`inverse_multiquadric`, `logarithm`, `thinplate_spline`, `one_over_square`,
`one_over_modulus`, `one_over_x`, `inverse_multiquadric3`, `sinc_kernel`,
`cosc`, `cot`, `one_over_cube`, `log_sin`, `laplacian_rbf`, `der_laplacian_rbf`,
`xx_gaussian` and `absx`. Any other name raises the error "Unkown kernel." The
kernel formulas are in the table on the page
[Fast summation](../applications/fastsum.md).

## Example

The program `julia/nfft/simple_test_1d.jl` computes a one-dimensional NFFT and
compares it with the direct sum.

```julia
--8<-- "julia/nfft/simple_test_1d.jl:1:45"
```

Run it from the directory `julia/nfft/` with `julia simple_test_1d.jl`. The
script then computes the error of the forward transform and runs the adjoint
transform in the same way.

The directory holds `simple_test_2d.jl` and `simple_test_3d.jl` for more
dimensions. The directories `julia/nfct/`, `julia/nfst/`, `julia/nfsft/` and
`julia/fastsum/` hold one example program per module.
