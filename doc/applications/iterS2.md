# Inversion on the sphere

Iterative reconstruction on the sphere $\mathbb{S}^2$. Given values of a
function at scattered nodes on the sphere, the program finds the spherical
Fourier coefficients of a bandlimited function that fits the values, and
evaluates the function at other nodes.

!!! warning "Not built"

    The maintainers marked this application as not functional. The build
    system does not build it. `configure.ac` has the line for its Makefile
    commented out, `applications/Makefile.am` lists an empty directory for it,
    and the CMake build omits it. The source stays in the tree for later use, and the page
    describes what the source does.

## Problem

Let $Y_k^n$ be the orthonormal spherical harmonics, and let
$\boldsymbol{\xi}_j \in \mathbb{S}^2$, $j = 0,\dots,M-1$, be the nodes with the
given values $y_j$. The program looks for the coefficients
$\hat f_k^n$, $k = 0,\dots,N$, $n = -k,\dots,k$, with

$$
\sum_{k=0}^{N} \sum_{n=-k}^{k} \hat f_k^n\, Y_k^n(\boldsymbol{\xi}_j) = y_j,
\qquad j = 0,\dots,M-1.
$$

This is the system $\mathbf{A}\hat{\mathbf f} = \mathbf y$ with the matrix
$\mathbf{A}$ of the [NFSFT](../transforms/nfsft.md). The system has
$(N+1)^2$ unknowns and $M$ equations.

## Method

The program solves the system with the [solver](../transforms/solver.md)
module, which drives the NFSFT plan as a matrix-vector product. The solver
depends on the relation between $(N+1)^2$ and $M$.

More unknowns than equations, $(N+1)^2 > M$
:   The system is underdetermined. The program uses CGNE with damping factors
    $\hat w_k = (k+1)^{-2}$ for the coefficients of degree $k$. The solution is
    the interpolation of minimal damped norm.

Otherwise
:   The system is overdetermined. The program uses CGNR with weights for the
    nodes and the damping factors $\hat w_k = (k+1)^{-5/2}$. The weight of a
    node is the area of its Voronoi cell on the sphere. The weights make the
    nodes count according to the area they cover. The program computes the
    Voronoi cells from a Delaunay triangulation of the nodes on the sphere
    with the library `cstripack` from `3rdparty/`.

The program sets the start vector to zero, computes the first residual and
runs 29 iteration steps. It prints the norm of the residual before each step
to the standard error output. After the last step it evaluates the resulting
function at the evaluation nodes with an NFSFT.

## Program

The directory `applications/iterS2/` has the program `iterS2` and two MATLAB
and Octave scripts. The program reads its input from the standard input. It
writes the absolute value of the reconstructed function at each evaluation node
to the standard output, one value per line, for every test case.

### Input

The input consists of one or more test cases. Every test case has these lines.

```text
testcases=T                 first line, once
nfsft=0|1
nfft=0|1                    read if nfsft=1
cutoff=c                    read if nfft=1
fpt=0|1                     read if nfsft=1
threshold=t                 read if fpt=1
bandwidth=N
nodes=M
theta phi re im             M lines
nodes_eval=M2
theta phi                   M2 lines
```

The flags select the algorithms of the NFSFT. With `nfsft=1` the program uses
the NFSFT. `nfft=0` replaces its NFFT by the direct transform NDFT and `fpt=0`
replaces its FPT by the direct polynomial transform. `cutoff` is the NFFT
cut-off parameter and `threshold` the FPT threshold parameter.

The nodes are given in the classical spherical coordinates: the colatitude
$\vartheta \in [0,\pi]$ and the longitude $\varphi \in [0,2\pi)$, both in
radians. The values `re` and `im` are the real part and the imaginary part of
the function value.

### MATLAB and Octave scripts

`writeTestcase.m`
:   `writeTestcase(file, usenfsft, usenfft, cutoff, usefpt, threshold,
    bandwidth, theta, phi, f)` writes one test case. The vectors `theta`, `phi`
    and `f` hold the nodes and the values.

`writeImageTestcase.m`
:   Writes a test case from an image. The matrix `img` holds a function on a
    regular grid in $\vartheta$ and $\varphi$. The nonzero entries become the
    sample nodes. The evaluation nodes are a grid four times finer in each
    direction. The optional arguments `itheta` and `iphi` select a part of the
    image.

The `README` in the directory also names the files `iterS2.m`,
`readTestcase.m`, `example.in` and `example.out`. These files are not in the
repository.

## Example

The program selects the solver by the relation between the number of
unknowns and the number of nodes:

```c
--8<-- "applications/iterS2/iterS2.c:384:391"
```

It starts with the zero vector, computes the first residual and iterates:

```c
--8<-- "applications/iterS2/iterS2.c:497:515"
```
