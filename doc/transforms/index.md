# Transforms

The library is organised in modules. Each one has its own plan type, its own
prefix and its own page below. The public declarations of all of them are in
`include/nfft3.h`.

| Module | Transform | API |
|--------|-----------|-----|
| [NFFT](nfft.md) | Trigonometric sum at arbitrary nodes, and its adjoint. The core module. | [`nfft_`](../api/nfft.md) |
| [NFCT](nfct.md) | Cosine transform at arbitrary nodes, real data. | [`nfct_`](../api/nfct.md) |
| [NFST](nfst.md) | Sine transform at arbitrary nodes, real data. | [`nfst_`](../api/nfst.md) |
| [NNFFT](nnfft.md) | Arbitrary nodes in time **and** in frequency. | [`nnfft_`](../api/nnfft.md) |
| [NSFFT](nsfft.md) | Frequencies on a hyperbolic cross instead of a full grid. | [`nsfft_`](../api/nsfft.md) |
| [MRI](mri.md) | Nonuniform k-space sampling with a correction for the field inhomogeneity in magnetic resonance imaging. | [`mri_`](../api/mri.md) |
| [NFSFT](nfsft.md) | Spherical harmonics on the sphere $\mathbb{S}^2$. | [`nfsft_`](../api/nfsft.md) |
| [NFSOFT](nfsoft.md) | Wigner-D functions on the rotation group $\mathrm{SO}(3)$. | [`nfsoft_`](../api/nfsoft.md) |
| [FPT](fpt.md) | Polynomial coefficients to Chebyshev coefficients. Used by NFSFT and NFSOFT. | [`fpt_`](../api/fpt.md) |
| [Solver](solver.md) | Inverse transforms by iterative methods. | [`solver_`](../api/solver.md) |

The application programs that use the MRI plans are described under
[Applications](../applications/mri.md). The [FPT](fpt.md) module has no plan. It
works on a set of transforms. The [solver](solver.md) module wraps the plan of
another module.

## Common structure

The modules with a plan follow one pattern, with small differences that their
own pages describe. The NFSFT and the NFSOFT need an additional precomputation
before the plan. The example uses the NFFT.

1. Declare a plan: `nfft_plan p;`
2. Initialise it: `nfft_init_1d(&p, N, M);`
3. Fill the nodes `p.x`, then precompute if the plan flags ask for it:
   `if (p.flags & PRE_ONE_PSI) nfft_precompute_one_psi(&p);`
4. Fill the input, `p.f_hat` for the forward transform or `p.f` for the adjoint.
5. Transform: `nfft_trafo(&p)` or `nfft_adjoint(&p)`, and read the other array.
6. Release: `nfft_finalize(&p);`

The modules with a plan also provide the slow, exact `..._trafo_direct` and
`..._adjoint_direct` for testing the fast routine against the definition. The
MRI module has no such routines.

The library is built for one window function. The choice of the window changes
the accuracy and the default cut-off, see the [guide](../guide/index.md). The
NSFFT module needs the Gaussian window.

The modules exist in three precisions. The prefixes `nfft_`, `nfftf_` and
`nfftl_` select double, single and long double precision. The same rule holds for
the other modules, except for the MRI module, which the library implements in
double precision only.

All transform plan structures start with the same six members, so a
plan can be handed to the [solver](solver.md) as a generic matrix-vector product:

| Member | Meaning |
|--------|---------|
| `N_total` | Total number of coefficients. |
| `M_total` | Total number of samples. |
| `f_hat` | Coefficients. |
| `f` | Samples. |
| `mv_trafo` | The forward transform. |
| `mv_adjoint` | The adjoint transform. |

In the NFCT and the NFST the members `f_hat` and `f` are real arrays.
