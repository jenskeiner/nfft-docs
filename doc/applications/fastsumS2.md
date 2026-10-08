# Fast summation on the sphere

Fast summation of radial functions on the sphere $\mathbb{S}^2$. The program
computes sums of the form

$$
f(\boldsymbol{\xi}_d) = \sum_{l=0}^{L-1} b_l\,
K\!\left(\boldsymbol{\eta}_l^{\mathrm{T}} \boldsymbol{\xi}_d\right),
\qquad d = 0,\dots,D-1,
$$

for $L$ source nodes $\boldsymbol{\eta}_l$ and $D$ target nodes
$\boldsymbol{\xi}_d$ on $\mathbb{S}^2$, complex coefficients $b_l$ and a kernel
$K : [-1,1] \to \mathbb{C}$. The kernel argument is the inner product of two
points on the sphere, so the kernel is a radial function on the sphere. The
kernels of the program are the Abel-Poisson kernel, the singularity kernel,
locally supported kernels and the spherical Gaussian kernel.

The fast algorithm uses the nonequispaced fast spherical Fourier transform
[NFSFT](../transforms/nfsft.md). The program can replace the parts of the NFSFT
by exact but slower algorithms and compare the fast sums with the direct
evaluation of the kernel.

## Method

Let $P_k$ be the Legendre polynomials. A kernel $K$ has the expansion

$$
K(x) = \sum_{k=0}^{\infty} \frac{2k+1}{4\pi}\, a_k\, P_k(x),
\qquad a_k = 2\pi \int_{-1}^{1} K(x)\, P_k(x)\, \mathrm{d}x,
$$

with the Fourier-Legendre coefficients $a_k$. The algorithm cuts the series at
the degree $M$, the cut-off degree. The addition theorem for spherical
harmonics writes the polynomials as

$$
P_k(\boldsymbol{\eta}^{\mathrm{T}}\boldsymbol{\xi}) =
\sum_{n=-k}^{k} \tilde Y_k^n(\boldsymbol{\xi})\,
\overline{\tilde Y_k^n(\boldsymbol{\eta})},
\qquad
\tilde Y_k^n(\vartheta,\varphi) = P_k^{|n|}(\cos\vartheta)\,
\mathrm{e}^{\mathrm{i} n\varphi}.
$$

The unnormalised basis $\tilde Y_k^n$ is the default basis of the
[NFSFT](../transforms/nfsft.md). The approximation becomes

$$
f_M(\boldsymbol{\xi}_d) = \sum_{k=0}^{M} \sum_{n=-k}^{k}
\frac{2k+1}{4\pi}\, a_k
\Bigl(\sum_{l=0}^{L-1} b_l\,
\overline{\tilde Y_k^n(\boldsymbol{\eta}_l)}\Bigr)
\tilde Y_k^n(\boldsymbol{\xi}_d).
$$

The fast algorithm has three steps.

1. Adjoint NFSFT of the coefficients $b_l$ at the source nodes.
2. Multiplication of the coefficient with index $(k,n)$ by
   $\tfrac{2k+1}{4\pi}\, a_k$.
3. NFSFT at the target nodes.

The error of the approximation is

$$
E_\infty = \frac{\|f - f_M\|_\infty}{\|b\|_1},
$$

with $f$ the direct sums and $f_M$ the fast sums. The method is described in
[1]. The NFSFT is described in [2].

The NFSFT itself has two parts that the program can exchange for exact
algorithms. The NFFT inside the NFSFT can be replaced by the direct transform
NDFT. The fast polynomial transform (FPT) inside the NFSFT can be replaced by
the direct discrete polynomial transform. The program can also skip the NFSFT
completely and use the direct NDSFT.

## Kernels

The program has four kernels. Each one has an explicit formula for its
Fourier-Legendre coefficients $a_k$. Here $x \in [-1,1]$.

| Kernel | Parameters | $K(x)$ | $a_k$ |
|--------|------------|--------|-------|
| Abel-Poisson, $Q_h$ | $h \in (0,1)$ | $\dfrac{1}{4\pi}\dfrac{1-h^2}{(1-2hx+h^2)^{3/2}}$ | $h^k$ |
| Singularity, $S_h$ | $h \in (0,1)$ | $\dfrac{1}{2\pi}\dfrac{1}{(1-2hx+h^2)^{1/2}}$ | $\dfrac{2}{2k+1}\,h^k$ |
| Locally supported, $L_{h,\lambda}$ | $h \in (-1,1)$, $\lambda \in \mathbb{N}_0$ | $\dfrac{\lambda+1}{2\pi(1-h)^{\lambda+1}}\,(x-h)_+^{\lambda}$ | recursion below |
| Spherical Gaussian, $G_\sigma$ | $\sigma > 0$ | $\mathrm{e}^{2\sigma(x-1)}$ | $2\pi\sqrt{\pi/\sigma}\,\mathrm{e}^{-2\sigma}\, I_{k+1/2}(2\sigma)$ |

Here $(x-h)_+ = \max\{x-h, 0\}$ and $I_\nu$ is the modified Bessel function of
the first kind. The static function `smbi` in `fastsumS2.c` computes
$I_{n+\alpha}(x)$ for $n = 0,\dots,nb-1$, real $x \ge 0$ and $0 \le \alpha < 1$,
optionally scaled by $\mathrm{e}^{-x}$. The program calls it with
$\alpha = \tfrac12$ and $x = 2\sigma$ and scaling, so it gets
$\mathrm{e}^{-2\sigma} I_{k+1/2}(2\sigma)$ directly. The routine is based on a
program of D. J. Sookne [3] that computes $J_\nu(x)$ or $I_\nu(x)$ for real
argument and integer order. W. J. Cody (Applied Mathematics Division, Argonne
National Laboratory) and J. Keiner (Institute of Mathematics, University of
Lübeck) modified it. The changes restrict the computation to $I_\nu(x)$ for
non-negative real argument, extend it to arbitrary non-negative orders $\nu$
and remove most underflow. The source lists [4] as a further reference.

The coefficients of the locally supported kernel follow from

$$
a_0 = 1, \qquad
a_1 = \frac{\lambda+1+h}{\lambda+2}\, a_0, \qquad
a_k = \frac{1}{k+\lambda+1}\Bigl((2k-1)\,h\,a_{k-1}
- (k-\lambda-2)\,a_{k-2}\Bigr), \quad k \ge 2.
$$

## Program

The directory `applications/fastsumS2/` has one program, `fastsumS2`, and MATLAB
and Octave helper scripts. The program calls the
[NFSFT API](../api/nfsft.md). It reads its input from the standard input and
writes its output to the standard output.

### Build

The program needs the NFSFT module and the double precision library. The
applications are built by default. The NFSFT module is off by default.

```bash
./configure --enable-nfsft --enable-applications
make -j
cd applications/fastsumS2
```

`--enable-all` includes the NFSFT module. The CMake build builds the program
when the NFSFT module is on, with `NFFT_ENABLE_APPLICATIONS` on by default,
and places it in `build/applications/fastsumS2/`.

### Run

```bash
./fastsumS2 < example.in > example.out
```

The file `example.in` is an example input and `example.out` the output of the
program for it. The example has three test cases with the Abel-Poisson kernel,
$h = 0.8$, $L = D = 1000$ nodes and the cut-off degrees $M = 4, 8, \dots, 256$.
The first test case uses the NFSFT with the direct NDFT and the FPT, the two
others use the NFFT with the cut-off parameters 3 and 6.

### Input

The program generates the nodes and the coefficients. The nodes are uniformly
distributed on the sphere. The real coefficients are uniformly distributed in
$[-\tfrac12, \tfrac12]$.

The input consists of one or more test cases. Every parameter is a line
`name=value`, separated by white space. The first parameter is
`testcases=`, the number of test cases. Each test case then has the parameters in
the order of the table. Parameters marked with an asterisk are extra parameters.
The program reads them only in the stated case. All values are integers or
floating point numbers. The program does not check the values.

| Parameter | Meaning |
|-----------|---------|
| `nfsft` | `1`: use the NFSFT. `0`: use the direct NDSFT. `2`: use both. |
| `nfft`* | `1`: the NFSFT uses the NFFT. `0`: the NFSFT uses the direct NDFT. Read if `nfsft` is not 0. |
| `cutoff`* | Integer $> 0$, the NFFT cut-off parameter. Read if `nfft=1`. |
| `fpt`* | `1`: the NFSFT uses the FPT. `0`: the NFSFT uses the direct polynomial transform. Read if `nfsft` is not 0. |
| `threshold`* | Floating point number $> 0$, the FPT threshold parameter. Read if `nfsft` is not 0, also if `fpt=0`. |
| `kernel` | `0` Abel-Poisson, `1` singularity, `2` locally supported, `3` spherical Gaussian. |
| `parameter_sets` | Number of kernel parameter sets. A test case can use one kernel with several sets of parameters. |
| `parameters` | Number of parameters per set: 1 for the kernels 0, 1 and 3, and 2 for the kernel 2. The values follow, one per line, set by set, in the order $h$, $\lambda$ for the kernel 2. |
| `bandwidths` | Number of cut-off degrees $M$. The list of the values follows, one per line. |
| `node_sets` | Number of node sets. Each node set has the parameters below. |
| `L`, `D` | Number of source nodes and target nodes. |
| `compare` | `1`: compare the fast result with the direct evaluation. `0`: no comparison. |
| `precomputed`* | `1`: precompute all kernel values for the direct evaluation and time only the summation. Read if `compare=1`. |
| `repetitions`* | Number of repetitions of the summation. The program averages the times over the repetitions. Read if `compare=1`; the default is 1. |

The MATLAB function `writeTestcase.m` writes one test case in this format.

### Output

The program writes all input values without their names, then the results.
For every kernel parameter set, every node set and every cut-off degree, in
this nesting order, it writes six numbers, one per line, and a blank line.

1. The time of the direct evaluation of the sums.
2. The time of the direct evaluation with precomputed kernel values.
3. The time of the fast summation with the direct NDSFT.
4. The time of the fast summation with the NFSFT.
5. The error $E_\infty$ of the fast summation with the direct NDSFT.
6. The error $E_\infty$ of the fast summation with the NFSFT.

Times are in seconds and averaged over the repetitions. A value that does not
apply to the parameter combination is $-1$. The error values need `compare=1`.
`readTestcase.m` reads a result file into MATLAB or Octave.

## MATLAB and Octave scripts

`fastsumS2.m`
:   Shows the fast summation. A menu selects one of the figures 5.1 (a) to (d)
    or Table 5.1 of [1]. The script writes the input to `data.in`, calls
    `./fastsumS2 < data.in > data.out`, reads the result and draws the figure
    or writes the table to `table.tex`. Run it in the directory with the
    program.

`writeTestcase.m`, `readTestcase.m`
:   Write a test case to a file and read the results of a run.

## Example

The main steps of `fastsumS2.c` start with the Fourier-Legendre coefficients
for the cut-off degree $M$. The last loop multiplies with the factor
$\tfrac{2k+1}{4\pi}$.

```c
--8<-- "applications/fastsumS2/fastsumS2.c:789:829"
```

Then the program creates one NFSFT plan for the source nodes and one for the
target nodes. Both plans share the array `f_hat`.

```c
--8<-- "applications/fastsumS2/fastsumS2.c:1086:1103"
```

The summation is the adjoint transform, the multiplication with the
coefficients and the transform. The program uses the direct transforms in the
`else` branches.

```c
--8<-- "applications/fastsumS2/fastsumS2.c:1164:1194"
```

## References

1. J. Keiner, S. Kunis and D. Potts. Fast summation of radial functions on the
   sphere. Computing 78, 1-15, 2006.
2. S. Kunis and D. Potts. Fast spherical Fourier algorithms. J. Comput.
   Appl. Math. 161, 75-98, 2003.
3. D. J. Sookne. Bessel functions of real argument and int order. NBS Jour. of
   Res. B 77B, 1973, pp. 125-132.
4. F. W. J. Olver and D. J. Sookne. A note on backward recurrence algorithms.
   Math. Comput. 26, 1972, pp. 125-132.
