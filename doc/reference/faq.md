# FAQ

Frequently asked questions. The entries follow the FAQ of the NFFT project site
and add questions that the source tree answers. Each answer was checked against
the current source tree, except the compiler and platform issues under
[Known issues](#known-issues) that the changelog does not confirm.

## Installing

### How do I compile and install the NFFT?

See [Install](../getting-started/index.md) for the short version and
[Build from source](../getting-started/build-from-source.md) for every
`configure` option.

### The configure script cannot find the FFTW3 library

Install the FFTW3 development package of your system. It provides the header
`fftw3.h` and the libraries `libfftw3.so` and `libfftw3.a`.

If you compile FFTW3 yourself, configure it with `--enable-shared`, and with
`--enable-threads` for the multi-threaded NFFT. Then tell the NFFT `configure`
script where FFTW3 is installed. Use one of these ways:

- `--with-fftw3=DIR` sets the root directory of FFTW3. The script looks for
  headers in `DIR/include` or `DIR/api` and for libraries in `DIR/lib` or
  `DIR/.libs`.
- `--with-fftw3-includedir=DIR` and `--with-fftw3-libdir=DIR` set the two
  directories separately.
- The environment variables `CPPFLAGS` and `LDFLAGS` also work.

The entry for version 3.1.0 in the [changelog](changelog.md) spells the options
`--with-fftw-includedir` and `--with-fftw-libdir`. The current option names
contain `fftw3`. Run `./configure --help` to see them.

### Which modules are available in single and long double precision?

The options `--enable-float` and `--enable-long-double` select the precision.
They exclude each other. Build each precision in its own configured tree.

Only the modules NFFT, NFCT, NFST and the solver are built in single and in long
double precision. The modules NFSFT, NFSOFT, NNFFT, NSFFT, MRI and FPT are
built in double precision only. With `--enable-all` they are skipped in the
other precisions. If you enable one of them explicitly, `configure` stops with
the message that the module cannot be used with the selected floating point
precision. The continuous integration builds the programs
`examples/nfsft/simple_test`, `applications/quadratureS2/quadratureS2` and
`applications/mri/mri2d/construct_data_2d` in double precision only.

### Does the NFFT build on ARM, for example on Apple silicon?

Yes. The entry for version 3.6.0 in the [changelog](changelog.md) lists
"Allow configure to run on ARM". Build the library from source. The continuous
integration workflow `build-macos.yml` builds it on macOS.

### How do I run the test suite?

The test suite uses CUnit and is off by default. Install CUnit, configure with
`--enable-tests`, and run `make check`. If you enable the tests and `configure`
does not find CUnit, it stops with an error.

## Using the NFFT

### What do N, M and N_total mean?

The bandwidth is $\mathbf{N} = (N_0,\dots,N_{d-1})$. Each $N_t$ is even. It is
the length of the regular grid of frequencies in direction $t$. The total number
of regular samples, the Fourier coefficients, is the product $N_0 \cdots
N_{d-1}$. The plan stores it as `N_total`.

The number of irregular samples, the nodes, is $M$. The plan stores it as
`M_total`. The nodes $\mathbf{x}_j$ lie in the torus
$[-\frac12, \frac12)^d$.

### In which order are the Fourier coefficients stored?

Index the frequencies $\mathbf{k} = (k_0,\dots,k_{d-1})$ with
$-N_t/2 \le k_t < N_t/2$. The array `f_hat` holds the coefficients in the order
of the C plan: the last dimension runs fastest. The position of
$\hat f_{\mathbf{k}}$ for $d=2$ is $(k_0 + N_0/2)\,N_1 + (k_1 + N_1/2)$,
counted from zero. For $d=1$ the position is $k + N/2$.

The MATLAB class interface uses the columnwise order of MATLAB arrays and
converts it. See [MATLAB and Octave](../interfaces/matlab-octave.md).

### Is the transform normalised?

No. The functions `nfft_trafo` and `nfft_adjoint` evaluate the sums of the
[definition](../guide/index.md) without a factor.

### How do I convert my nonuniformly sampled data from the time domain to the frequency domain?

The forward transform of the NFFT goes in the opposite direction to the forward
transform of FFTW. FFTW turns samples on a regular grid into coefficients. The
function `nfft_trafo` evaluates a trigonometric polynomial with given
coefficients at the nodes:

$$
f_j = \sum_{\mathbf{k}\in I_{\mathbf{N}}} \hat f_{\mathbf{k}}\,
\mathrm{e}^{-2\pi\mathrm{i}\,\mathbf{k}\mathbf{x}_j}.
$$

The function `nfft_adjoint` takes samples $f_j$ at the nodes and computes

$$
\hat h_{\mathbf{k}} = \sum_{j=0}^{M-1} f_j\,
\mathrm{e}^{+2\pi\mathrm{i}\,\mathbf{k}\mathbf{x}_j}.
$$

The sign of the exponent is positive. To get the sums with the negative sign,
which is the sign of the FFTW forward transform, call `nfft_adjoint` with the
nodes $-\mathbf{x}_j$.

The NDFT and the NFFT are not orthogonal transforms in general. The adjoint
transform is not the inverse transform. To recover coefficients from samples,
use an inverse transform. The [solver](../transforms/solver.md) module computes
it by iterative methods. The example `examples/solver/simple_test.c` shows the
use. For one dimension, the MATLAB class `infft` computes the inverse NFFT
directly. It is available since version 3.4.1. See
[MATLAB and Octave](../interfaces/matlab-octave.md).

### How do I make the NFFT more accurate or faster?

Two parameters control the accuracy: the window cut-off `m` and the
oversampling factor $\sigma$. See
[What the NFFT computes](../guide/index.md#the-two-parameters) and
[Accuracy](../guide/accuracy.md).

### Which window function does my library use?

The window function is fixed when the library is built, with
`--with-window`. The default is the Kaiser-Bessel window. Call
`nfft_get_window_name()` to get the name from the library you linked.

### How do I use several threads?

Configure with `--enable-openmp`. The build then also produces the library
`libnfft3_omp`. Link against it. The functions `nfft_get_num_threads` and
`nfft_set_num_threads` read and set the number of threads. See
[OpenMP](../guide/openmp.md).

## Known issues

The project FAQ lists these compiler and platform issues.

### Wrong NFFT results in debug mode or with your own CFLAGS

Old GCC versions, 4.5.0 to 4.6.1, produce wrong results and buffer overflows
when the NFFT is compiled without the flag `-ffast-math`. If you do not set
`CFLAGS`, `configure` adds `-ffast-math` for you. Debug mode with
`--enable-debug` and your own `CFLAGS` replace the default flags. In these cases
add `-ffast-math` to `CFLAGS` yourself.

### Internal compiler error in the fastsum or MRI module

GCC 7.1.0, 7.2.0 and 7.3.0 abort with an internal compiler error in the
fastsum module. Version 3.4.0 contains a workaround. GCC 4.7.1 aborts with an
internal compiler error when the MRI module is enabled. Version 3.2.3 contains
a workaround. See the [changelog](changelog.md).

### Compilation fails when MRI is enabled and NNFFT is disabled

The program `reconstruct_data_inh_nnfft` in `applications/mri/mri2d` uses the
NNFFT module. Enable both with `--enable-nnfft --enable-mri`, or build all modules with `--enable-all`.

### Wrong NFSOFT results with AVX512 and GCC 7.4.0

On processors with AVX512 instructions, the NFSOFT module compiled with GCC
7.4.0 might produce wrong results. GCC 9.2.1 does not show the problem.

### Long double precision with OpenMP on Windows

A bug in MinGW makes many calculations run in double precision only when the
library is built in long double precision with OpenMP on Windows. OpenMP is off
by default. Do not pass `--enable-openmp` when you build in long double
precision on Windows.

## Other questions

### Under which license is the NFFT distributed?

Under the GNU General Public License, version 2 or later. See
[License](license.md).

### How do I cite the NFFT?

See [Publications](publications.md#how-to-cite).

### Where do I report a bug?

In the [issue tracker](https://github.com/NFFT/nfft/issues), or directly to the
authors. See [People](people.md#contact).
