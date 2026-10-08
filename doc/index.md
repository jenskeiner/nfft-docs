---
hide:
  - navigation
---

# NFFT3

A C library for the **nonequispaced fast Fourier transform** and a family of
related transforms.

The fast Fourier transform has two shortcomings. It needs equispaced sampling,
and it is restricted to the complex exponential functions. NFFT3 is a C
subroutine library for computing the nonequispaced discrete Fourier transform
(NDFT) and its generalisations in one or more dimensions, of arbitrary input
size, and of complex data. It evaluates the trigonometric sum

$$
f_j \;=\; \sum_{\mathbf k \in I_{\mathbf N}} \hat f_{\mathbf k}\,
\mathrm{e}^{-2\pi\mathrm{i}\,\mathbf k \mathbf x_j},
\qquad j = 0,\dots,M-1,
$$

at arbitrary nodes $\mathbf x_j \in \mathbb{T}^d$ in
${\cal O}(|I_{\mathbf N}| \log |I_{\mathbf N}| + M)$ operations instead of the
${\cal O}(|I_{\mathbf N}|\,M)$ of the direct sum, at an accuracy you choose
through two parameters.

<div class="grid cards" markdown>

-   __Get started__

    Install the library, compile a first transform, build from source.

    [Install](getting-started/index.md)

-   __Guide__

    What the transform computes, plans and flags, windows, precision, OpenMP.

    [Concepts](guide/index.md)

-   __Transforms__

    NFFT, NFCT, NFST, NNFFT, NSFFT, NFSFT, NFSOFT, FPT and the inverse solvers.

    [Overview](transforms/index.md)

-   __Applications__

    Fast summation, MRI, polar FFT, Radon transform, quadrature on the sphere.

    [Overview](applications/index.md)

-   __Interfaces__

    Julia and MATLAB/Octave bindings.

    [Julia](interfaces/julia.md)

-   __Publications__

    The papers behind the algorithms, with BibTeX entries.

    [Publications](reference/publications.md)

</div>

## What the library contains

The core module is the NFFT, the forward transform and its adjoint. The
generalisations of the NFFT are:

- [NNFFT](transforms/nnfft.md), nonequispaced in time and in frequency,
- [NFCT and NFST](transforms/nfct.md), nonequispaced fast cosine and sine
  transforms for real data,
- [NSFFT](transforms/nsfft.md), the sparse transform on the hyperbolic cross,
- [FPT](transforms/fpt.md), the fast polynomial transform,
- [NFSFT](transforms/nfsft.md), the transform on the sphere $\mathbb{S}^2$,
- [NFSOFT](transforms/nfsoft.md), the transform on the rotation group
  $\mathrm{SO}(3)$.

The library also provides the inversion of these transforms by iterative
methods, such as CGNR and CGNE. See the [solver](transforms/solver.md).

Example programs use these transforms for:

- medical imaging, with magnetic resonance imaging and computerised
  tomography,
- summation schemes: fast summation, the fast Gauss transform, singular kernels
  and zonal kernels,
- the polar FFT, the discrete Radon transform and the ridgelet transform.

They are described under [Applications](applications/index.md).

## License

NFFT3 is free software. You can redistribute it and modify it under the terms of
the GNU General Public License, version 2 or at your option any later version.
See [License](reference/license.md). Answers to common questions are in the
[FAQ](reference/faq.md). To cite the library, see
[How to cite](reference/publications.md#how-to-cite).
