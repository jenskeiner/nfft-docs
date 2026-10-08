# MRI

Image reconstruction in magnetic resonance imaging (MRI) from nonuniform
k-space data. An MRI scanner measures samples of the Fourier transform of the
image. The sample positions, the k-space trajectory, are often not on a
Cartesian grid. The [NFFT](../transforms/nfft.md) evaluates the forward model
for such positions. The [solver](../transforms/solver.md) module inverts it.

The programs in `applications/mri/` construct simulated k-space data and
reconstruct images from it. They follow two papers.

- T. Knopp, S. Kunis, and D. Potts. A note on the iterative MRI reconstruction
  from nonuniform k-space data.
- H. Eggers, T. Knopp, and D. Potts. Field Inhomogeneity Correction based on
  Gridding Reconstruction for Magnetic Resonance Imaging.

The programs come in two groups.

| Page | Programs | Data |
|------|----------|------|
| [MRI 2D](mri-2d.md) | `mri2d/` | One image of $N \times N$ pixels. Optional field inhomogeneity. |
| [MRI 3D](mri-3d.md) | `mri3d/` | A stack of $Z$ images of $N \times N$ pixels. |

## The problem

Let $I_N^2 := \{\mathbf{k} \in \mathbb{Z}^2 : -N/2 \le k_t < N/2\}$ index the
pixels of an $N \times N$ image $\hat f_{\mathbf{k}}$. The scanner samples the
Fourier transform of the image at $M$ nodes
$\mathbf{x}_j \in [-\tfrac{1}{2},\tfrac{1}{2})^2$ in k-space:

$$
f(\mathbf{x}_j) = \sum_{\mathbf{k} \in I_N^2} \hat f_{\mathbf{k}}\,
{\rm e}^{-2\pi{\rm i}\,\mathbf{k}\mathbf{x}_j},
\qquad j=0,\dots,M-1.
$$

This is the NFFT. Given the samples $y_j$, the reconstruction has to find the
image $\hat f$.

### Gridding

The simplest reconstruction is the adjoint NFFT with density compensation
weights $w_j$:

$$
\hat f_{\mathbf{k}} \approx \sum_{j=0}^{M-1} w_j\, y_j\,
{\rm e}^{+2\pi{\rm i}\,\mathbf{k}\mathbf{x}_j}.
$$

The weight $w_j$ is the area of the Voronoi cell of the node $\mathbf{x}_j$,
normalised to sum 1. The MATLAB script `precompute_weights.m` computes it.
The result is fast, but it is only an approximation of the inverse.

### Iterative reconstruction

The iterative method solves the weighted least squares problem

$$
\hat{\mathbf f} = \arg\min \sum_{j=0}^{M-1} w_j
\left| \sum_{\mathbf{k}} \hat f_{\mathbf{k}}\,
{\rm e}^{-2\pi{\rm i}\,\mathbf{k}\mathbf{x}_j} - y_j \right|^2
$$

with CGNR, the conjugate gradient method on the normal equations. See the
[solver](../transforms/solver.md) page. All reconstruction programs start with
$\hat f = 0$ and use damping factors $\hat w_{\mathbf{k}}$. The damping factor
is 1 for the pixels inside the disc $|\mathbf{k}| \le N/2$ and 0 outside. This
limits the solution to the disc inscribed in the image.

The iteration stops after `ITER` steps. It also stops when the weighted squared
residual `dot_r_iter` falls below $3 \cdot 10^{-7}$. The programs print the
residual norm of every step to `stderr`.

### Field inhomogeneity

The magnetic field is not perfectly homogeneous. A field map $w_{\mathbf{k}}$
gives the frequency offset of every pixel, in cycles per unit of the readout
time. Sample $j$ is taken at the readout time $t_j$. The forward model gains a
phase factor. The plans of the MRI module evaluate

$$
f(\mathbf{x}_j) = \sum_{\mathbf{k} \in I_N^2} \hat f_{\mathbf{k}}\,
{\rm e}^{-2\pi{\rm i}\, w_{\mathbf{k}} (t_j - T_s)}\,
{\rm e}^{-2\pi{\rm i}\,\mathbf{k}\mathbf{x}_j},
\qquad T_s := \frac{t_{\min} + t_{\max}}{2}.
$$

The shift $T_s$ centres the readout times around 0. The plans work with the
scaled values $t'_j = (t_j - T_s)/T$ and $w'_{\mathbf{k}} = w_{\mathbf{k}}/W$,
where the constants $T$ and $W$ depend on the field map and the readout times.
The API of the plans is on the [MRI API page](../api/mri.md).

A direct evaluation of the model costs $\mathcal{O}(N^2 M)$ operations. Three
fast methods exist. They differ in how they treat the extra phase.

2d1d
:   For every point of a grid of $N_3$ values in the time direction, the method
    computes one 2D NFFT. A window function interpolates between the grid
    points. The plan is `mri_inh_2d1d_plan`.

3d
:   The method adds a third dimension to the NFFT. The third node coordinate is
    the scaled readout time. The field map enters through a window function
    that spreads every coefficient over $N_3$ points in the third frequency
    direction. The plan is `mri_inh_3d_plan`.

NNFFT
:   The method uses the [NNFFT](../transforms/nnfft.md) with the nodes
    $(\mathbf{x}_j, (t_j - T_s)W/N_3)$ in space and the frequency nodes
    $(\mathbf{k}/N, w_{\mathbf{k}}/W)$. It needs no MRI plan.

The three methods use the cut-off $m = 2$ and the oversampling factor
$\sigma = 1.25$. The number of grid points $N_3$ follows from the field map and
the readout times.

$$
N_3 = \left\lceil \left( \max_{\mathbf{k}} |w_{\mathbf{k}}|\,
\frac{t_{\max} - t_{\min}}{2} + \frac{m}{2\sigma} \right) 4\sigma
\right\rceil .
$$

The NNFFT program uses a different rule, see [MRI 2D](mri-2d.md).

## Programs

All programs are in `applications/mri/`. Each is a separate executable that
reads and writes plain text files in the current directory.

| Program | Task |
|---------|------|
| `mri2d/construct_data_2d` | Simulate k-space data with a 2D NFFT. |
| `mri2d/construct_data_inh_2d1d` | Simulate data with field inhomogeneity, 2d1d method. |
| `mri2d/construct_data_inh_3d` | Simulate data with field inhomogeneity, 3d method. |
| `mri2d/reconstruct_data_2d` | Iterative reconstruction. |
| `mri2d/reconstruct_data_gridding` | Gridding reconstruction. |
| `mri2d/reconstruct_data_inh_2d1d` | Iterative reconstruction with field correction, 2d1d method. |
| `mri2d/reconstruct_data_inh_3d` | Iterative reconstruction with field correction, 3d method. |
| `mri2d/reconstruct_data_inh_nnfft` | Iterative reconstruction with field correction, NNFFT method. |
| `mri3d/construct_data_2d1d` | Simulate data of a stack of images: 1D FFT, then 2D NFFT per slice. |
| `mri3d/construct_data_3d` | Simulate data with a 3D NFFT. |
| `mri3d/reconstruct_data_2d1d` | Reconstruct slice by slice, then 1D inverse FFT. |
| `mri3d/reconstruct_data_3d` | Iterative reconstruction with a 3D NFFT. |
| `mri3d/reconstruct_data_gridding` | Gridding reconstruction slice by slice, then 1D inverse FFT. |

The programs share the argument order `FILENAME N M`, followed by `Z` in 3D
and by `ITER WEIGHTS` for reconstruction. Every program prints a usage line
when it gets too few arguments. Every program returns the exit status 1, also
after a successful run.

## Data files

All files are plain text. The programs read them from the current directory.
Numbers are in `%le` format, separated by white space.

| File | Content |
|------|---------|
| `knots.dat` | Nodes $\mathbf{x}_j$ in k-space. One node per line, 2 columns in 2D. In 3D each line has 3 columns. The slice programs use the first two columns of the first $M/Z$ lines. The 3D programs use all 3 columns of $M$ lines. |
| `input_f.dat` | The image, real valued. $N^2$ numbers in the order of the NFFT coefficient array. In 3D $Z$ rows of $N^2$ numbers. |
| `FILENAME` | The k-space samples. One line per node: `x y Re Im` in 2D, `x y z Re Im` in 3D. |
| `weights.dat` | The weights $w_j$, one per node. |
| `readout_time.dat` | The readout times $t_j$, one per node. Only for field inhomogeneity. |
| `inh.dat` | The field map $w_{\mathbf{k}}$, $N^2$ numbers. Only for field inhomogeneity. |
| `output_real.dat`, `output_imag.dat` | The reconstructed image. $N^2$ numbers in 2D, $Z$ lines of $N^2$ numbers in 3D. |

## MATLAB and Octave scripts

The directories contain scripts that create the input files and show the
result. They call the executables with `system`, so start MATLAB or Octave in
the directory that holds the executables.

`mri.m`
:   Complete demonstration. It creates a phantom and spiral knots, simulates the
    data, computes the weights, reconstructs iteratively and by gridding, and
    prints the relative error.

`mri_inh.m`
:   Only in `mri2d/`. The same with field inhomogeneity. It compares the
    reconstruction with and without the field map. To try the other methods,
    replace `2d1d` by `3d` or `nnfft` in the command.

`construct_knots_spiral.m`, `construct_knots_radial.m`, `construct_knots_rose.m`, `construct_knots_linogram.m`
:   Write `knots.dat` for the chosen trajectory and return the number of nodes.
    `mri3d/` adds `construct_knots_radial_3d.m`, which writes `knots.dat` and
    `weights.dat` for 3D radial nodes. Use these nodes only with
    `construct_data_3d` and `reconstruct_data_3d`.

`precompute_weights.m`
:   Computes the Voronoi weights and writes `weights.dat`. The 3D version is
    `precompute_weights_2d.m`. It repeats the weights of one slice for all
    slices.

`construct_readout_time.m`, `construct_inh.m`
:   Only in `mri2d/`. Write `readout_time.dat` and `inh.dat`.

`phantom.m`, `construct_phantom.m`
:   Write the Shepp-Logan phantom to `input_f.dat`, in 2D and 3D.

`visualize_data.m`, `rms.m`
:   Show the result and write the relative error
    $\|f - \tilde f\| / \|f\|$ to a text file.

`verschiebung.m`
:   Only in `mri2d/`. Multiplies the samples in `output_phantom_nfft_600.dat`
    with a phase factor, which shifts the image.

## Build and run

The MRI module and the NNFFT module are off by default. The programs need both,
because `reconstruct_data_inh_nnfft` uses the NNFFT. Both modules exist only in
double precision.

```bash
./configure --enable-mri --enable-nnfft
make
```

`--enable-all` includes both modules. The application programs are built by
default. `--disable-applications` switches them off. The executables appear in
`applications/mri/mri2d/` and `applications/mri/mri3d/` of the build tree. To
run the demonstration, change to one of these directories and start
`octave mri.m` or the same script in MATLAB.

## Example

From `reconstruct_data_2d.c`. The first excerpt sets up the solver. The second
excerpt starts from the zero guess and runs the CGNR loop.

```c
--8<-- "applications/mri/mri2d/reconstruct_data_2d.c:61:66"
```

```c
--8<-- "applications/mri/mri2d/reconstruct_data_2d.c:116:132"
```

## API

[MRI API reference](../api/mri.md),
[NFFT](../transforms/nfft.md),
[NNFFT](../transforms/nnfft.md),
[Solver](../transforms/solver.md)
