# MRI 3D

The programs in `applications/mri/mri3d/` construct and reconstruct data of a
stack of $Z$ images of $N \times N$ pixels. The [MRI overview](mri.md) explains
the model, the data files, the MATLAB scripts and the build. This page lists the
programs.

Two approaches exist for a stack.

Slice by slice, "2d1d"
:   The k-space data is sampled in the plane, with the same nodes in every
    slice. In the third direction the data lies on a regular grid. A 1D FFT
    along the third direction separates the slices. Each slice is then a 2D
    problem. The constructor applies the 1D FFT first and then one 2D NFFT per
    slice. The reconstructor solves one 2D problem per slice and then applies a
    1D inverse FFT.

Full 3D
:   The nodes lie in 3D k-space. One 3D NFFT connects the image stack and the
    samples. The reconstructor solves the 3D problem with CGNR.

The command lines use these arguments.

| Argument | Meaning |
|----------|---------|
| `FILENAME` | The file with the k-space samples. The constructors write it, the reconstructors read it. |
| `N` | The image size $N \times N$ of one slice. |
| `M` | The total number of samples of all slices. |
| `Z` | The number of slices. |
| `ITER` | The maximum number of CGNR iterations. |
| `WEIGHTS` | Nonzero: use the weights in `weights.dat`. Zero: do not use them. |

In the slice programs, every slice has $M/Z$ nodes.

The k-space files have one line per sample with the columns `x y z Re Im`. The
image files `output_real.dat` and `output_imag.dat` have $Z$ lines. Every line
holds the $N^2$ pixel values of one slice.

## construct_data_2d1d

Simulates k-space data of a stack of images. The source file is
`construct_data_2d1d.c`. It exists for the slice by slice approach.

```
./construct_data_2d1d FILENAME N M Z
```

Input
:   `knots.dat` with 3 columns per line. The program reads the first $M/Z$ lines
    and uses the first two columns `x y`. All slices use these nodes. `input_f.dat` with $Z$ rows of
    $N^2$ real pixel values.

Output
:   `FILENAME` with $M$ lines `x y z Re Im`. The value $z$ of slice $l$ is
    $l/Z - 1/2$.

Formula
:   For every pixel $\mathbf{k}$, the program computes a 1D FFT along the $Z$
    slices, with the zero position shifted to the middle of the stack. This
    gives the values $g_l(\mathbf{k})$. Then, for every slice $l = 0,\dots,Z-1$
    and every node $j = 0,\dots,M/Z-1$, it computes
    $f(\mathbf{x}_j, l/Z - 1/2) = \sum_{\mathbf{k} \in I_N^2} g_l(\mathbf{k})\,
    {\rm e}^{-2\pi{\rm i}\,\mathbf{k}\mathbf{x}_j}$.

```c
--8<-- "applications/mri/mri3d/construct_data_2d1d.c:47:74"
```

## construct_data_3d

Simulates k-space data with one 3D NFFT.

```
./construct_data_3d FILENAME N M Z
```

Input
:   `knots.dat` with $M$ lines of 3 columns. `input_f.dat` with $Z$ rows of
    $N^2$ real pixel values.

Output
:   `FILENAME` with $M$ lines `x y z Re Im`.

Formula
:   The bandwidth is $(Z, N, N)$. The program assigns the columns of
    `knots.dat` to the NFFT node so that the third column is the coordinate
    that belongs to the size $Z$. It writes the columns in the same order as it
    reads them. The formula is the NFFT
    $f(\mathbf{x}_j) = \sum_{\mathbf{k}} \hat f_{\mathbf{k}}\,
    {\rm e}^{-2\pi{\rm i}\,\mathbf{k}\mathbf{x}_j}$ with
    $\mathbf{k} \in I_{(Z,N,N)}$.

Parameters
:   $\sigma = 1.2$, $m = 6$.

```c
--8<-- "applications/mri/mri3d/construct_data_3d.c:45:57"
```

## reconstruct_data_2d1d

Reconstructs a stack of images slice by slice, then applies a 1D inverse FFT.
The source file is `reconstruct_data_2d1d.c`.

```
./reconstruct_data_2d1d FILENAME N M Z ITER WEIGHTS
```

Input
:   `FILENAME` with $M$ lines `x y z Re Im`, in the order of the slices. The
    program ignores the column `z`. If `WEIGHTS` is nonzero, also `weights.dat`
    with $M/Z$ weights. All slices use these weights.

Output
:   `output_real.dat` and `output_imag.dat`, each with $Z$ lines of $N^2$
    numbers.

Method
:   For every slice the program solves the 2D problem of `reconstruct_data_2d`
    with CGNR. The solver starts from zero. It runs at most `ITER` steps per
    slice and stops earlier when the squared weighted residual is below
    $3 \cdot 10^{-7}$. The parameters are $\sigma = 1.2$ and $m = 6$. The damping
    factor is 1 inside the disc $|\mathbf{k}| \le N/2$ and 0 outside. The
    program computes the matrix $B$ of the NFFT once, because the nodes are the
    same in all slices. After the last slice a 1D inverse FFT runs along the
    stack. The program divides the result by $Z$.

```c
--8<-- "applications/mri/mri3d/reconstruct_data_2d1d.c:97:138"
```

## reconstruct_data_3d

Reconstructs a stack of images with one 3D NFFT and CGNR.

```
./reconstruct_data_3d FILENAME N M Z ITER WEIGHTS
```

Input
:   `FILENAME` with $M$ lines `x y z Re Im`. If `WEIGHTS` is nonzero, also
    `weights.dat` with $M$ weights.

Output
:   `output_real.dat` and `output_imag.dat`, each with $Z$ lines of $N^2$
    numbers.

Method
:   The NFFT has the bandwidth $(Z, N, N)$, $\sigma = 1.2$ and $m = 6$. The
    solver flags are `CGNR` and `PRECOMPUTE_DAMP`, plus `PRECOMPUTE_WEIGHT` if
    `WEIGHTS` is nonzero. The damping factor is 1 inside the ball
    $|\mathbf{k}| \le N/2$ and 0 outside. The program sets the damping factors in
    a loop over $N$ slices, so use $Z = N$. The stop criterion is the same as in
    `reconstruct_data_2d`.

The node columns `x y z` go to the NFFT node in the same order as in
`construct_data_3d`.

## reconstruct_data_gridding

Reconstructs a stack of images with one adjoint 2D NFFT per slice, then applies
a 1D inverse FFT.

```
./reconstruct_data_gridding FILENAME N M Z ITER WEIGHTS
```

Input
:   `FILENAME` with $M$ lines `x y z Re Im`, and `weights.dat` with $M/Z$
    weights. The program opens `weights.dat` also if `WEIGHTS` is zero.

Output
:   `output_real.dat` and `output_imag.dat`, each with $Z$ lines of $N^2$
    numbers.

Formula
:   For every slice $l$, the program computes
    $g_l(\mathbf{k}) = \sum_{j} w_j\, y_{j,l}\,
    {\rm e}^{+2\pi{\rm i}\,\mathbf{k}\mathbf{x}_j}$. If `WEIGHTS` is zero, all
    $w_j = 1$. A 1D inverse FFT along the stack and the division by $Z$ give the
    image.

Parameters
:   $\sigma = 1.2$, $m = 6$. The program ignores `ITER`. It exists only to keep
    the command line equal to the one of `reconstruct_data_2d1d`.

## Example session

The script `mri.m` in `mri3d/` runs these steps with $N = Z = 48$. The value
`M` is the number of nodes that `construct_knots_spiral.m` returns.

```
./construct_data_2d1d output_phantom_nfft.dat 48 M 48
./reconstruct_data_2d1d output_phantom_nfft.dat 48 M 48 3 1
./reconstruct_data_gridding output_phantom_nfft.dat 48 M 48 0 1
./reconstruct_data_3d output_phantom_nfft.dat 48 M 48 1 1
```

The script `precompute_weights_2d.m` writes `weights.dat` before the
reconstruction. For 3D radial nodes, `construct_knots_radial_3d.m` writes the
nodes and the weights. Use these nodes with `construct_data_3d` and
`reconstruct_data_3d`.
