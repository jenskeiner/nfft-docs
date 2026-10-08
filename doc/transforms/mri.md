# MRI

Transforms in magnetic resonance imaging. The library module `mri` computes the
measurement model of MRI with a correction for the inhomogeneity of the magnetic
field. It is built on the [NFFT](nfft.md) and it provides two plan types, one
for each of two methods: the 2d1d method and the 3d method. Both plan types work
with the [solver](solver.md) module, so you can invert the model iteratively. The
application programs that use these plans are described under
[Applications](../applications/mri.md).

## Model

A two-dimensional image with the pixel values $\hat f_{\mathbf{k}}$,
$\mathbf{k}\in I_{\mathbf{N}}^2$, is sampled in the frequency space at $M$ nodes
$\mathbf{x}_j\in[-\tfrac{1}{2},\tfrac{1}{2})^2$ at the readout times $\tau_j$. The
field inhomogeneity $\omega_{\mathbf{k}}$ at each pixel adds a phase that grows
with the readout time. The model of the measured signal is

$$
f_j = \sum_{\mathbf{k}\in I_{\mathbf{N}}^2} \hat f_{\mathbf{k}}\,
\mathrm{e}^{-2\pi\mathrm{i}\,\omega_{\mathbf{k}}\,\tau_j}\,
\mathrm{e}^{-2\pi\mathrm{i}\,\mathbf{k}\mathbf{x}_j},
\qquad j=0,\dots,M-1.
$$

Here $\omega_{\mathbf{k}}$ is a frequency in cycles per unit of time and
$I_{\mathbf{N}}^2$ is the frequency set of the [NFFT](nfft.md) with
$\mathbf{N}=(N_0,N_1)$. Without the inhomogeneity the model is a plain
two-dimensional NFFT.

## What the plans compute

The plans work with scaled quantities. Each plan holds the scaled readout times
$t_j$ in `t` for the 2d1d method, or in the third coordinate of the nodes for the
3d method. It holds the scaled field values $w_{\mathbf{k}}$ in `w`. With the
integer $N_3$, the transform is

$$
f_j = \sum_{\mathbf{k}\in I_{\mathbf{N}}^2} \hat f_{\mathbf{k}}\,
\mathrm{e}^{-2\pi\mathrm{i}\,N_3\,w_{\mathbf{k}}\,t_j}\,
\mathrm{e}^{-2\pi\mathrm{i}\,\mathbf{k}\mathbf{x}_j},
\qquad j=0,\dots,M-1,
$$

and the adjoint transform is

$$
\hat f_{\mathbf{k}} = \sum_{j=0}^{M-1} f_j\,
\mathrm{e}^{+2\pi\mathrm{i}\,N_3\,w_{\mathbf{k}}\,t_j}\,
\mathrm{e}^{+2\pi\mathrm{i}\,\mathbf{k}\mathbf{x}_j},
\qquad \mathbf{k}\in I_{\mathbf{N}}^2.
$$

The plans evaluate both sums approximately. The routines `mri_inh_2d1d_trafo`,
`mri_inh_2d1d_adjoint`, `mri_inh_3d_trafo` and `mri_inh_3d_adjoint` compute them.

### Scaling

The example programs derive the scaled quantities from the physical ones. Let
$T_s$ be the middle of the readout interval, $\tau_{\min}$ and $\tau_{\max}$ its
ends, $m$ the cut-off and $\sigma$ the oversampling factor of the window. The
programs choose the even integer

$$
N_3 = \left\lceil \left( \max_{\mathbf{k}}|\omega_{\mathbf{k}}|\,
\frac{\tau_{\max}-\tau_{\min}}{2} + \frac{m}{2\sigma} \right) 4\sigma
\right\rceil
$$

and a field scale $W$ with $w_{\mathbf{k}} = \omega_{\mathbf{k}}/W$.

- In the 2d1d method, $T = \frac{\tau_{\max}-\tau_{\min}}{2}\big/\left(\tfrac{1}{2}-\tfrac{m}{N_3}\right)$,
  $W = N_3/T$ and $t_j = (\tau_j - T_s)/T$. The window in time has compact
  support, so this choice keeps $|t_j|\le\tfrac{1}{2}-m/N_3$.
- In the 3d method, $W = \max_{\mathbf{k}}|\omega_{\mathbf{k}}|\big/\left(\tfrac{1}{2}-\tfrac{m}{N_3}\right)$
  and the third node coordinate is $t_j = (\tau_j - T_s)\,W/N_3$. This choice
  keeps $|w_{\mathbf{k}}|\le\tfrac{1}{2}-m/N_3$.

In both methods $N_3 w_{\mathbf{k}} t_j = \omega_{\mathbf{k}}(\tau_j - T_s)$. The
shift by $T_s$ adds the factor $\mathrm{e}^{2\pi\mathrm{i}\,\omega_{\mathbf{k}} T_s}$
to the pixel values, which the programs remove from the reconstructed image.

## The two methods

**2d1d method.** The plan holds a two-dimensional NFFT plan. For each index
$l=-N_3/2,\dots,N_3/2$ of a regular grid in time, the transform multiplies the
coefficients with $\mathrm{e}^{-2\pi\mathrm{i}\,w_{\mathbf{k}}l}/\hat\varphi(N_3 w_{\mathbf{k}})$
and runs the NFFT. It sums the results over $l$, weighted with the window
function $\varphi(t_j - l/N_3)$. The cost is $N_3+1$ two-dimensional NFFTs.

**3d method.** The plan holds a three-dimensional NFFT plan. The time direction
is the third dimension. The transform spreads each coefficient over the third
dimension with the window $\varphi(w_{\mathbf{k}} - l/N_3)$, runs one
three-dimensional NFFT at the nodes $(\mathbf{x}_j, t_j)$ and divides the samples
by $\hat\varphi(N_3 t_j)$. The cost is one NFFT of the size
$N_0\times N_1\times N_3$.

The window function $\varphi$ has a compact support of $2m+2$ grid points. The
parameters `m`, `N3` and `sigma3` control the accuracy of the approximation of
the phase factor.

## Using a plan

The two plans have the members `plan`, `N3`, `sigma3`, `t` and `w` in addition
to the six members that all plans share. `plan` is the inner NFFT plan. The
plans set `N_total` to $N_0N_1$.

1. Call `mri_inh_2d1d_init_guru(&p, N, M, n, m, sigma, nfft_flags, fftw_flags)`
   or `mri_inh_3d_init_guru` with the same arguments. `N` has three entries
   $N_0$, $N_1$ and $N_3$. `n` holds the oversampled lengths of the inner NFFT.
   `m` is the cut-off, `sigma` the oversampling factor of the window in the time
   direction, and the two flag arguments are those of `nfft_init_guru`. The
   example programs pass `PRE_PHI_HUT | PRE_PSI | MALLOC_X | MALLOC_F_HAT |
   MALLOC_F | FFTW_INIT`. The 2d1d method uses only `n[0]` and `n[1]`.
2. Write the nodes into `p.plan.x`. In the 2d1d method, node $j$ holds the two
   frequency-space coordinates in `p.plan.x[2*j]` and `p.plan.x[2*j+1]`, and the
   scaled readout time is in `p.t[j]`. In the 3d method, node $j$ holds the three
   coordinates in `p.plan.x[3*j]`, `p.plan.x[3*j+1]` and `p.plan.x[3*j+2]`, and
   the last coordinate is the scaled readout time.
3. Write the scaled field values into `p.w`. It has $N_0N_1$ entries.
4. Call the precomputation routine of the inner plan, for example
   `nfft_precompute_one_psi(&p.plan)`.
5. Write the pixel values into `p.f_hat` and call the forward transform, or write
   the samples into `p.f` and call the adjoint transform.
6. Call `mri_inh_2d1d_finalize` or `mri_inh_3d_finalize`.

The 2d1d routines replace the array `f` in the forward transform and the array
`f_hat` in the adjoint transform with newly allocated arrays. Read the result
through `p.f` or `p.f_hat` and do not keep the old pointer.

The library implements the module in double precision. The header also declares
the prefixes `mrif_` and `mril_`, but the library does not define them.

## Example

The program `applications/mri/mri2d/reconstruct_data_inh_2d1d.c` reconstructs an
image from measured data with the 2d1d plan and the [solver](solver.md) module.
It first chooses $N_3$, $T$ and $W$ from the data and creates the plan.

```c
--8<-- "applications/mri/mri2d/reconstruct_data_inh_2d1d.c:86:100"
```

Then it reads the nodes, the readout times and the field values and applies the
scaling.

```c
--8<-- "applications/mri/mri2d/reconstruct_data_inh_2d1d.c:143:161"
```

Finally it binds the plan to a solver plan of the type `solver_plan_complex`. The
solver flags are `CGNR | PRECOMPUTE_DAMP`, and the program adds
`PRECOMPUTE_WEIGHT` when the user asks for weights. The cast to
`nfft_mv_plan_complex` is valid because the plans share their first members.

```c
--8<-- "applications/mri/mri2d/reconstruct_data_inh_2d1d.c:107:111"
```

## References

Knopp, T., Kunis, S. and Potts, D. A note on the iterative MRI reconstruction
from nonuniform k-space data.

Eggers, H., Knopp, T. and Potts, D. Field Inhomogeneity Correction based on
Gridding Reconstruction for Magnetic Resonance Imaging.

## API

[MRI API reference](../api/mri.md)
