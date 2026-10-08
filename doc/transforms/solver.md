# Solver

Inverse transforms. Every transform in this library has an adjoint, but the
adjoint is not the inverse. The solver module recovers the coefficients from
the samples with iterative methods.

## The problem

Write the transform as a matrix-vector product $\mathbf{A}\hat{\mathbf f}$, where
$\mathbf{A}$ has the entries $\mathrm{e}^{-2\pi\mathrm{i}\mathbf{k}\mathbf{x}_j}$ for
the [NFFT](nfft.md), and correspondingly for the other modules. Given samples
$\mathbf y$, the module solves

$$
\mathbf{A}\hat{\mathbf f} = \mathbf y .
$$

The system is rarely square. Two cases matter, and each has its own algorithm.

**More samples than coefficients**, $M > |I_{\mathbf{N}}|$. The system is
overdetermined and generally inconsistent, so the solution is the weighted least
squares minimiser

$$
\hat{\mathbf f} = \arg\min \left\| \mathbf{A}\hat{\mathbf f} - \mathbf y
\right\|_{\mathbf W}^2 ,
$$

computed with **CGNR**, conjugate gradients on the normal equations of the first
kind $\mathbf{A}^{\mathsf H}\mathbf{W}\mathbf{A}\hat{\mathbf f} =
\mathbf{A}^{\mathsf H}\mathbf{W}\mathbf y$. Each iterate minimises the residual in
the current Krylov subspace.

**Fewer samples than coefficients**, $M < |I_{\mathbf{N}}|$. The system is
underdetermined. The solution is the interpolant of minimal damped norm

$$
\hat{\mathbf f} = \arg\min \sum_{\mathbf{k}} \frac{|\hat f_{\mathbf{k}}|^2}{\hat w_{\mathbf{k}}}
\quad \text{subject to} \quad \mathbf{A}\hat{\mathbf f} = \mathbf y ,
$$

computed with **CGNE**, conjugate gradients on the normal equations of the
second kind. Each iterate minimises the error in the current Krylov subspace.

The diagonal matrix $\mathbf W$ holds the weights $w_j$, one per sample. They
compensate for a non-uniform node density. The diagonal matrix
$\hat{\mathbf W}$ holds the damping factors $\hat w_{\mathbf{k}}$, one per
coefficient. A small damping factor penalises its coefficient, so choose small
factors for the coefficients that you expect to be small, for example for the
high frequencies. In CGNR the damping factors act as a preconditioner.

## Flags

The flags select the iteration and the optional matrices. Pass them to
`solver_init_advanced_complex` or `solver_init_advanced_double`. Use exactly one
of the first four flags.

| Flag | Meaning |
|------|---------|
| `LANDWEBER` | The Landweber, or Richardson, iteration $\hat{\mathbf f} \leftarrow \hat{\mathbf f} + \alpha\,\hat{\mathbf W}\mathbf{A}^{\mathsf H}\mathbf{W}(\mathbf y - \mathbf{A}\hat{\mathbf f})$. The application must set the step size `alpha_iter`. |
| `STEEPEST_DESCENT` | The method of steepest descent, or gradient method. It uses the same update as the Landweber iteration and computes the optimal step size $\alpha$ in each step. |
| `CGNR` | The conjugate gradient method for the normal equation of the first kind. Use it for $M > \lvert I_{\mathbf{N}}\rvert$. |
| `CGNE` | The conjugate gradient method for the normal equation of the second kind. Use it for $M < \lvert I_{\mathbf{N}}\rvert$. |
| `NORMS_FOR_LANDWEBER` | The Landweber iteration updates the members `dot_r_iter` and `dot_z_hat_iter`. The other iterations always update them. |
| `PRECOMPUTE_WEIGHT` | The solver weights the samples with the diagonal matrix $\mathbf W$, for example to cope with a varying sampling density. It allocates the array `w`. |
| `PRECOMPUTE_DAMP` | The solver damps the Fourier coefficients with the diagonal matrix $\hat{\mathbf W}$, for example to favour fast decaying coefficients. It allocates the array `w_hat`. |

## Using it

The solver never touches a transform directly. It drives whatever plan is
handed to it through the six shared plan members, so the same solver works for
the NFFT, the NFSFT, the MRI plans and anything else that fills them in.

1. Set up the transform plan completely. Set its nodes and call its
   precomputation routine.
2. `solver_init_complex(&s, (nfft_mv_plan_complex*) &p)` binds the solver to a
   plan, with `CGNR` as the default. `solver_init_advanced_complex` takes the
   flags explicitly.
3. Write the samples into `s.y` and a starting guess into `s.f_hat_iter`. If you
   set `PRECOMPUTE_WEIGHT` or `PRECOMPUTE_DAMP`, write the weights into `s.w`
   (`M_total` entries) and the damping factors into `s.w_hat` (`N_total`
   entries).
4. `solver_before_loop_complex(&s)` computes the first residual.
5. Call `solver_loop_one_step_complex(&s)` as often as needed. The solver does
   not stop by itself. Watch `s.dot_r_iter`, the weighted squared norm
   $\mathbf r^{\mathsf H}\mathbf W\mathbf r$ of the residual
   $\mathbf r = \mathbf y - \mathbf{A}\hat{\mathbf f}$, and stop when it is small
   enough.
6. Read the result from `s.f_hat_iter`, then call `solver_finalize_complex(&s)`.

The solver uses the arrays `f` and `f_hat` of the bound plan as work space and
overwrites them. Finalise the solver before you finalise the plan.

The `..._double` variants of the same routines drive the real-valued transforms,
the [NFCT](nfct.md) and the [NFST](nfst.md). They use the plan type
`solver_plan_double` and the cast `nfft_mv_plan_double`. The prefixes `solverf_`
and `solverl_` select the single and the long double precision.

## Example

From `examples/solver/simple_test.c`:

```c
--8<-- "examples/solver/simple_test.c.in:86:150"
```

The program `examples/solver/glacier.c` reconstructs a glacier from sampled
level curves. It fits a two-dimensional trigonometric polynomial with $N\times N$
coefficients to $M$ scattered samples. The program uses a two-dimensional NFFT
plan with `PRE_FULL_PSI`, the solver flags `CGNE | PRECOMPUTE_DAMP` and 40
iterations. The damping factors are the product of a generalised Sobolev weight
in each dimension,

$$
\hat w_{\mathbf{k}} = \prod_{t=0}^{1} \frac{\left(\tfrac{1}{4} - z_t^2\right)^{b}}{c + |z_t|^{2a}},
\qquad z_t = \frac{k_t - N/2}{N},
$$

with $a=\tfrac{1}{2}$, $b=3$ and $c=10^{-3}$. The program reads the nodes and
the sample values from the file `input_data.dat`. Each line holds $x_0$, $x_1$
and the sample value. The MATLAB script `glacier.m` creates this file from the
data set `vol87.dat`, which holds 8345 samples. It scales the nodes into the
interior of the torus and runs the program with $N=256$ and $M=8345$. With more
arguments, the routine `glacier_cv` leaves out $M_{\text{cv}}$ samples, solves
with the rest and measures the error at the omitted samples, for a cross
validation. It compares `CGNE` with damping and `CGNR` for two sizes $N$ and
prints the rows of a LaTeX table. The script `glacier_cv.m` shuffles the samples, runs the program for $M_{\text{cv}}=200,400,\dots,1000$ and writes the table to `output_data_cv.tex`.

## References

Kunis, S. and Potts, D. Stability Results for Scattered Data Interpolation by
Trigonometric Polynomials, SIAM J. Sci. Comput. 29, 1403 - 1419, 2007.

## API

[Solver API reference](../api/solver.md)
