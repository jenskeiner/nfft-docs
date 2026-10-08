# MRI 2D

The programs in `applications/mri/mri2d/` construct and reconstruct data of a
single image of $N \times N$ pixels. The [MRI overview](mri.md) explains the
model, the data files, the MATLAB scripts and the build. This page lists the
programs.

Every program reads its files from the current directory. The command lines use
these arguments.

| Argument | Meaning |
|----------|---------|
| `FILENAME` | The file with the k-space samples. The constructors write it, the reconstructors read it. |
| `N` | The image size $N \times N$. |
| `M` | The number of nodes and samples. |
| `ITER` | The maximum number of CGNR iterations. |
| `WEIGHTS` | Nonzero: use the weights in `weights.dat`. Zero: do not use them. |

## construct_data_2d

Simulates k-space data of an image with a 2D NFFT.

```
./construct_data_2d FILENAME N M
```

Input
:   `knots.dat` with $M$ lines `x y`, and `input_f.dat` with the $N^2$ real
    pixel values $\hat f_{\mathbf{k}}$.

Output
:   `FILENAME` with $M$ lines `x y Re Im`, where $\mathrm{Re}$ and $\mathrm{Im}$
    are the parts of $f(\mathbf{x}_j)$.

Formula
:   $f(\mathbf{x}_j) = \sum_{\mathbf{k} \in I_N^2} \hat f_{\mathbf{k}}\,
    {\rm e}^{-2\pi{\rm i}\,\mathbf{k}\mathbf{x}_j}$

The program creates the plan with `nfft_init_2d`, which sets the default
parameters, and calls `nfft_trafo`.

```c
--8<-- "applications/mri/mri2d/construct_data_2d.c:47:81"
```

## reconstruct_data_2d

Reconstructs the image from the samples with the iterative method. This is the
inverse 2D NFFT.

```
./reconstruct_data_2d FILENAME N M ITER WEIGHTS
```

Input
:   `FILENAME` with $M$ lines `x y Re Im`. If `WEIGHTS` is nonzero, also
    `weights.dat` with $M$ weights.

Output
:   `output_real.dat` and `output_imag.dat`, each with $N^2$ numbers.

Formula
:   $\hat{\mathbf f} = \arg\min \sum_j w_j \left| \sum_{\mathbf{k}} \hat
    f_{\mathbf{k}}\, {\rm e}^{-2\pi{\rm i}\,\mathbf{k}\mathbf{x}_j} - y_j
    \right|^2$

Parameters
:   The NFFT has oversampling factor $\sigma = 2$, that is $n = 2N$
    per dimension, and cut-off $m = 6$. The solver flags are `CGNR` and
    `PRECOMPUTE_DAMP`, plus `PRECOMPUTE_WEIGHT` if `WEIGHTS` is nonzero. The
    damping factor is 1 for the pixels with $\sqrt{k_0^2 + k_1^2} \le N/2$ and
    0 elsewhere. The iteration starts from zero. It stops when the squared
    weighted residual is below $3 \cdot 10^{-7}$.

See the [MRI overview](mri.md) for the iteration loop.

## reconstruct_data_gridding

Reconstructs the image with one adjoint NFFT. This is the gridding method.

```
./reconstruct_data_gridding FILENAME N M ITER WEIGHTS
```

Input
:   `FILENAME` with $M$ lines `x y Re Im`, and `weights.dat` with $M$ weights.
    The program opens `weights.dat` also if `WEIGHTS` is zero.

Output
:   `output_real.dat` and `output_imag.dat`, each with $N^2$ numbers.

Formula
:   $\hat f_{\mathbf{k}} = \sum_{j=0}^{M-1} w_j\, y_j\,
    {\rm e}^{+2\pi{\rm i}\,\mathbf{k}\mathbf{x}_j}$. If `WEIGHTS` is zero, all
    $w_j = 1$.

Parameters
:   $\sigma = 1.2$, $m = 6$. The program ignores `ITER`. It exists only to keep
    the command line equal to the one of `reconstruct_data_2d`.

```c
--8<-- "applications/mri/mri2d/reconstruct_data_gridding.c:59:80"
```

## construct_data_inh_2d1d

Simulates k-space data with field inhomogeneity. It uses the 2d1d method.

```
./construct_data_inh_2d1d FILENAME N M
```

Input
:   `knots.dat` with $M$ lines `x y`, `readout_time.dat` with $M$ readout times,
    `inh.dat` with the $N^2$ values of the field map, and `input_f.dat` with the
    $N^2$ real pixel values.

Output
:   `FILENAME` with $M$ lines `x y Re Im`.

Formula
:   The plan evaluates the model of the [overview](mri.md) on the coefficients
    $\hat f_{\mathbf{k}}\, {\rm e}^{2\pi{\rm i}\,T_s w_{\mathbf{k}}}$. The
    program multiplies the pixel values with this phase before the transform.

Parameters
:   $m = 2$ and $\sigma = 1.25$. The program derives $T_s$, $N_3$, $T$ and $W$
    from the field map and the readout times.

$$
T = \frac{(t_{\max} - t_{\min})/2}{1/2 - m/N_3}, \qquad W = \frac{N_3}{T}.
$$

```c
--8<-- "applications/mri/mri2d/construct_data_inh_2d1d.c:89:99"
```

## construct_data_inh_3d

Simulates k-space data with field inhomogeneity. It uses the 3d method. The
command line, the input files and the output file are the same as for
`construct_data_inh_2d1d`.

```
./construct_data_inh_3d FILENAME N M
```

The third node coordinate is $x_{j,2} = (t_j - T_s)\,W/N_3$. The constant $W$
is

$$
W = \frac{\max_{\mathbf{k}} |w_{\mathbf{k}}|}{1/2 - m/N_3}.
$$

The oversampled size in the third dimension is $\lceil \sigma N_3 \rceil$.
$N_3$, $m$ and $\sigma$ follow the rule of the [overview](mri.md).

## reconstruct_data_inh_2d1d

Reconstructs the image with field correction, 2d1d method. This is the
iterative method of `reconstruct_data_2d` with the plan `mri_inh_2d1d_plan`.

```
./reconstruct_data_inh_2d1d FILENAME N M ITER WEIGHTS
```

Input
:   `FILENAME` with $M$ lines `x y Re Im`, `readout_time.dat`, `inh.dat`, and
    `weights.dat` if `WEIGHTS` is nonzero.

Output
:   `output_real.dat` and `output_imag.dat`, each with $N^2$ numbers.

Parameters
:   $m = 2$, $\sigma = 1.25$, $N_3$, $T$ and $W$ as in
    `construct_data_inh_2d1d`. Here the program rounds an odd $N_3$ up to the
    next even number. The solver flags, the damping factors and the stop
    criterion are the same as in `reconstruct_data_2d`. After the last
    iteration the program multiplies every pixel with
    ${\rm e}^{-2\pi{\rm i}\,T_s w_{\mathbf{k}}}$. This removes the phase that
    `construct_data_inh_2d1d` adds.

## reconstruct_data_inh_3d

The same as `reconstruct_data_inh_2d1d`, with the 3d method and the plan
`mri_inh_3d_plan`. The constant $W$ and the third node coordinate are the ones
of `construct_data_inh_3d`. The program also rounds an odd $N_3$ up to the next
even number.

```
./reconstruct_data_inh_3d FILENAME N M ITER WEIGHTS
```

## reconstruct_data_inh_nnfft

The same task, solved with an [NNFFT](../transforms/nnfft.md) plan of
dimension 3 instead of an MRI plan.

```
./reconstruct_data_inh_nnfft FILENAME N M ITER WEIGHTS
```

The plan has $N^2$ frequency nodes and $M$ spatial nodes. The program sets
them as follows.

```c
--8<-- "applications/mri/mri2d/reconstruct_data_inh_nnfft.c:149:166"
```

Parameters
:   $m = 2$ and $\sigma = 1.25$. The program uses
    $N_3 = \lceil 4 \max_{\mathbf{k}} |w_{\mathbf{k}}|\,(t_{\max} -
    t_{\min})/2 \rceil$ and $W = 2 \max_{\mathbf{k}} |w_{\mathbf{k}}|$. It does
    not round $N_3$. The solver flags, the damping factors and the stop
    criterion are the same as in `reconstruct_data_2d`. After the last
    iteration the program multiplies every pixel with
    ${\rm e}^{+2\pi{\rm i}\,T_s w_{\mathbf{k}}}$. The programs for the 2d1d and
    3d methods use the opposite sign.

The program prints a line with $N_3$, $W$, the field map range, the readout time
range and $T_s$ to `stderr`.

## Example session

The script `mri.m` runs these steps.

```
./construct_data_2d output_phantom_nfft.dat 128 M
./reconstruct_data_2d output_phantom_nfft.dat 128 M 3 1
./reconstruct_data_gridding output_phantom_nfft.dat 128 M 5 1
```

Here `M` is the number of nodes that `construct_knots_spiral.m` returns. The
script `mri_inh.m` runs `construct_data_inh_2d1d` and
`reconstruct_data_inh_2d1d`, and then `reconstruct_data_2d` on the same data to
show the effect of the field map.
