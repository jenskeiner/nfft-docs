# MATLAB and Octave

The directory `matlab/` of the source tree holds MEX interfaces to the C
library for MATLAB and for GNU Octave. Each module has a MEX gateway written in
C and a set of `.m` files that wrap it.

| Directory | Interface to |
|-----------|--------------|
| `matlab/nfft` | [NFFT](../transforms/nfft.md) |
| `matlab/nfct` | [NFCT](../transforms/nfct.md) |
| `matlab/nfst` | [NFST](../transforms/nfst.md) |
| `matlab/nnfft` | [NNFFT](../transforms/nnfft.md) |
| `matlab/nfsft` | [NFSFT](../transforms/nfsft.md) |
| `matlab/nfsoft` | [NFSOFT](../transforms/nfsoft.md) |
| `matlab/fpt` | [FPT](../transforms/fpt.md) |
| `matlab/fastsum` | [fast summation](../applications/fastsum.md) |
| `matlab/infft1d` | inverse NFFT in one dimension, MATLAB only |

## Build the interface

Give `configure` the installation directory of MATLAB or of Octave. The two
options exclude each other.

```bash
./configure --enable-all --enable-openmp --with-matlab=/path/to/matlab
./configure --enable-all --enable-openmp --with-octave=/path/to/octave
```

The related options are:

| Option | Meaning |
|--------|---------|
| `--with-matlab=DIR` | Directory where MATLAB is installed. |
| `--with-octave=DIR` | Directory where GNU Octave is installed. |
| `--with-matlab-arch=DIR` | MATLAB architecture acronym. |
| `--enable-matlab-argchecks` | Compile the interface with argument checks. The default is yes. |
| `--enable-matlab-threads` | Compile the interface with thread support. The default is the value of `--enable-openmp`. This option needs `--enable-openmp`. |
| `--with-matlab-fftw3-libdir=DIR` | Directory of the FFTW3 library for the MATLAB interface. |
| `--with-octave-libdir=DIR`, `--with-octave-includedir=DIR` | Octave library and include directories. |

The interface needs the library in double or in single precision. Long double
precision is an error. See
[Build from source](../getting-started/build-from-source.md) for the general
options.

The CMake build has the options `-DNFFT_WITH_OCTAVE=ON` and
`-DNFFT_WITH_MATLAB=/path/to/matlab`. The two exclude each other. The option
`-DNFFT_ENABLE_MATLAB_THREADS=ON` needs `-DNFFT_ENABLE_OPENMP=ON`.

The modules `nfft`, `fastsum` and `infft1d` are always built. The modules
`nfct`, `nfst`, `nfsft`, `nfsoft`, `nnfft` and `fpt` are built when the
corresponding C module is enabled.

The scripts `linux-build-mex.sh`, `macos-build-mex.sh` and `windows-build-dll.sh`
in the top directory build the Octave and MATLAB interfaces for Linux, macOS and
Windows. The Windows script builds statically linked DLLs and is meant for
MSYS2-MinGW64. A MATLAB installation must be given to build the MATLAB
interface.

## Install

`make install` puts the `.m` files of each module into
`share/nfft/matlab/<module>` under the installation prefix. The MEX library of
each module goes into the library directory, and a link `<module>mex` with the
MEX suffix of the platform points to it. The unit tests are installed to
`share/nfft/matlab/tests`.

Add these directories to the path before you use a module:

```matlab
addpath('/usr/local/share/nfft/matlab/nfft', '/usr/local/lib')
```

Replace `/usr/local` with your prefix. In the source tree after `make`, the
directory `matlab/<module>` holds both the `.m` files and the MEX file.

## Two calling styles

Every module offers two interfaces to the same plan.

**Function interface.** The functions mirror the C API. `nfft_init_1d` returns
a plan as a number, and the other functions take that number as first argument.

**Class interface.** A class of the module name wraps the plan. The class is a
handle class. Its constructor creates the plan and its destructor finalizes the
plan. You set nodes and coefficients by assigning to the properties.

| Module | Class | Constructor |
|--------|-------|-------------|
| NFFT | `nfft` | `nfft(d, N, M)` |
| NFCT | `nfct` | `nfct(d, N, M)` |
| NFST | `nfst` | `nfst(d, N, M)` |
| NNFFT | `nnfft` | `nnfft(d, N_total, M, N, ...)` |
| NFSFT | `nfsft` | `nfsft(N, M, nfsft_flags, kappa, nfft_cutoff, fpt_flags, nfft_flags)` |
| NFSOFT | `nfsoft` | `nfsoft(N, M, nfsoft_flags, nfft_flags, nfft_cutoff, fpt_kappa, fftw_size)` |
| fast summation | `fastsum` | `fastsum(d, kernel, c, flags, n, p, eps_I, eps_B, nn_x, m_x, nn_y, m_y)` |
| inverse NFFT | `infft` | `infft(y, N, ...)` |

The two interfaces differ in the layout of the data.

| | Function interface | Class interface |
|--|--------------------|-----------------|
| Nodes $\mathbf{x}$ | array of size $d \times M$ | array of size $M \times d$ |
| Fourier coefficients | one column vector in the layout of the C plan, the last dimension runs fastest | one column vector, the first dimension runs fastest: the columnwise linearisation of the $N_1 \times N_2$ matrix |

## Example, function interface

The script `matlab/nfft/simple_test.m` creates a plan for one dimension, sets
nodes and coefficients, runs the transform and compares the result with the
matrix product.

```matlab
--8<-- "matlab/nfft/simple_test.m:21:59"
```

The flags of the plan are functions without arguments. For example `PRE_PHI_HUT`
and `FFTW_MEASURE` return the flag value, and `bitor` combines them. The
function `nfft_init_guru` takes the dimension, the bandwidths `N1, ..., Nd`, the
number of nodes `M`, the oversampled lengths `n1, ..., nd`, the window cut-off
`m`, the NFFT flags and the FFTW flags. The function `ndft_trafo(plan)` runs the
direct algorithm on the same plan. The functions `nfft_get_num_threads` and
`nfft_set_num_threads` read and set the number of threads when the interface is
built with thread support.

## Example, class interface

The script `matlab/nfft/test_nfft1d.m` uses the class `nfft`. Assigning `x`
performs the node-dependent precomputation.

```matlab
--8<-- "matlab/nfft/test_nfft1d.m:26:52"
```

The methods of the class are `nfft_trafo`, `nfft_adjoint`, `ndft_trafo`,
`ndft_adjoint`, `nfft_precompute_psi` and `nfft_solver`. The method
`nfft_solver(plan, iterations)` runs the inverse NFFT by the
[solver](../transforms/solver.md) module. The properties are `x`, `fhat`, `f`
and `num_threads`.

## NFSFT

The class `nfsft` takes the degree `N` and the number of nodes `M`. The nodes
are a $2 \times M$ array of spherical coordinates $[\varphi; \vartheta]$. The
class `f_hat` stores spherical Fourier coefficients and gives access by degree
and order. The functions `gl` and `cc` return Gauss-Legendre and Clenshaw-Curtis
quadrature nodes and weights.

```matlab
--8<-- "matlab/nfsft/simple_test.m:28:76"
```

## Fast polynomial transform

The FPT has a function interface only. The script `matlab/fpt/simple_test.m`
shows the calls `fpt_init`, `fpt_precompute`, `fpt_trafo`, `fpt_trafo_direct`
and `fpt_finalize`. The functions `fpt_transposed` and `fpt_transposed_direct`
run the transposed transform.

## Fast summation

The class `fastsum` computes the sums

$$
f(y_j) = \sum_{k=1}^{N} \alpha_k K(x_k - y_j), \qquad j = 1,\dots,M.
$$

The properties `x` and `y` are arrays of size $N \times d$ and $M \times d$.
The property `alpha` is a column vector of length $N$. The methods are
`fastsum_trafo` and `fastsum_trafo_direct`. The result is the property `f`. The
kernel names are those of the [fast summation](../applications/fastsum.md)
application. The header of `matlab/fastsum/simple_test.m` lists them with their
formulas.

## Inverse NFFT in one dimension

The class `infft` in `matlab/infft1d` computes the inverse NFFT in one
dimension by the direct methods of Kircheis and Potts. See
[Publications](../reference/publications.md) for the papers. The methods depend
on the relation between the number `M` of nodes and the number `N` of
coefficients. The workflow is:

```matlab
plan = infft(y, N);     % initialisation and precomputation
plan.f = f;             % set function values
infft_trafo(plan)       % fast computation
infft_trafo_direct(plan)  % direct computation
```

The result is in `plan.fcheck`. The class works in one dimension only. It is
written for MATLAB. The file `matlab/infft1d/README` states that it is not
compatible with GNU Octave as of Octave version 5. The options `n`, `m`, `sigma`, `p`, `eps_I`, `m2`, `window` and `flag_toeplitz` are
described in `matlab/infft1d/README`.

## Tests

The directory `matlab/tests` holds unit tests for NFFT, NFSFT and NFSOFT.
`make check` runs them through MATLAB or Octave, whichever `configure` found.
