# Publications

This page lists the papers named in the source tree: in `README.md`, in the
README files of the `examples/` and `applications/` directories, and in the
MATLAB files. The text of each entry follows the source. Entries marked as
"to appear" or "accepted" are given as the source states them.

## How to cite

The current general paper, the one recommended if you wish to cite NFFT, is

> J. Keiner, S. Kunis, and D. Potts. Using NFFT 3 - a software library for
> various nonequispaced fast Fourier transforms. ACM Trans. Math. Software 36,
> Article 19, 1-30, 2009. DOI: [10.1145/1555386.1555388](https://doi.org/10.1145/1555386.1555388)

BibTeX entry:

```bibtex
@article{KeKuPo09,
 author = {Jens Keiner and Stefan Kunis and Daniel Potts},
 title = {Using {NFFT3} - a Software Library for Various Nonequispaced Fast {Fourier} Transforms},
 journal = {{ACM} Trans. Math. Software},
 year = {2009},
 volume = {36},
 pages = {Article 19, 1--30},
 doi = {10.1145/1555386.1555388}}
```

## NFFT and its generalisations

- D. Potts, G. Steidl, and M. Tasche. Fast Fourier transforms for
  nonequispaced data: A tutorial. In: Modern Sampling Theory: Mathematics and
  Applications, J. J. Benedetto and P. Ferreira (Eds.), Chapter 12, pages
  249-274, 1998. This is the basis of the [NNFFT](../transforms/nnfft.md)
  example.
- S. Kunis and D. Potts. Time and memory requirements of the nonequispaced FFT.
  Preprint 2006-1, Chemnitz University of Technology, Faculty of Mathematics.
  The paper belongs to the [NFFT](../transforms/nfft.md) example programs.
- M. Fenn, S. Kunis, and D. Potts. Fast evaluation of trigonometric
  polynomials from hyperbolic crosses. This is the basis of the
  [NSFFT](../transforms/nsfft.md) example.

## Inverse transforms

- S. Kunis and D. Potts. Stability results for scattered data interpolation by
  trigonometric polynomials. SIAM J. Sci. Comput. 29, 1403-1419, 2007. The paper
  belongs to the [solver](../transforms/solver.md) examples.
- M. Kircheis. Die Direkte Inverse NFFT. Bachelor's Thesis, Chemnitz University
  of Technology, 2017.
  <https://www.tu-chemnitz.de/~kimel/paper/bachelorthesis.pdf>
- M. Kircheis and D. Potts. Direct inversion of the nonequispaced fast Fourier
  transform. arXiv:1811.05335, 2018.
  <https://www.tu-chemnitz.de/~kimel/paper/infft_1d.pdf>

The two papers of M. Kircheis describe the one-dimensional inverse NFFT of the
[MATLAB interface](../interfaces/matlab-octave.md).

## Sphere, rotation group and fast polynomial transform

- S. Kunis and D. Potts. Fast spherical Fourier algorithms. J. Comput. Appl.
  Math. 161, 75-98, 2003.
- D. Potts, J. Prestin, and A. Vollrath. A fast algorithm for nonequispaced
  Fourier transforms on the rotation group. To appear in Num. Alg. This is the
  basis of the [NFSOFT](../transforms/nfsoft.md) example.
- D. Potts. Fast algorithms for discrete polynomial transforms on arbitrary
  grids. Linear Algebra Appl. 366, 353-370, 2003.
  <https://www-user.tu-chemnitz.de/~potts/paper/ndct.pdf>
  The computations of the [FPT](../transforms/fpt.md) are based on this paper.
- J. Keiner, S. Kunis, and D. Potts. Fast summation of radial functions on the
  sphere. Computing 78, 1-15, 2006. The paper belongs to the
  [fast summation on the sphere](../applications/fastsumS2.md).

## Fast summation and fast Gauss transform

- D. Potts and G. Steidl. Fast summation at nonequispaced knots by NFFTs. SIAM
  J. Sci. Comput., 24:2013-2037, 2003.
- D. Potts, G. Steidl, and A. Nieslony. Fast convolution with radial kernels at
  nonequispaced knots. Numer. Math., 98:329-351, 2004.
- M. Fenn and G. Steidl. Fast NFFT-based summation of radial functions. Sampl.
  Theory Signal Image Process., 3:1-28, 2004.
- M. Fenn and D. Potts. Fast summation based on fast trigonometric transforms
  at non-equispaced nodes. Numer. Linear Algebra Appl., 12:161-169, 2005.

These four papers belong to the [fast summation](../applications/fastsum.md).
The paper of Fenn and Potts is also the reference of the
[NFCT](../transforms/nfct.md) and [NFST](../transforms/nfst.md) examples.

- S. Kunis, D. Potts, and G. Steidl. Fast Gauss transforms with complex
  parameters using NFFTs. J. Numer. Math., to appear, 2006. Preprint:
  <http://www.tu-chemnitz.de/~potts/paper/fastgauss.pdf>
  The paper belongs to the [fast Gauss transform](../applications/fastgauss.md).

## Magnetic resonance imaging

- T. Knopp, S. Kunis, and D. Potts. A note on the iterative MRI reconstruction
  from nonuniform k-space data. Available from
  <http://www.tu-chemnitz.de/~potts>
- H. Eggers, T. Knopp, and D. Potts. Field inhomogeneity correction based on
  gridding reconstruction for magnetic resonance imaging.

Both papers belong to the [MRI application](../applications/mri.md).

## Polar FFT, Radon transform and tomography

- M. Fenn, S. Kunis, and D. Potts. On the computation of the polar FFT. Appl.
  Comput. Harmon. Anal., accepted. The paper belongs to the
  [polar FFT](../applications/polarFFT.md).
- D. Potts and G. Steidl. A new linogram algorithm for computerized
  tomography. IMA J. Numer. Anal. 21, 769-782, 2001.
- D. Potts and G. Steidl. New Fourier reconstruction algorithms for
  computerized tomography. In: Proceedings of SPIE: Wavelet Applications in
  Signal and Image Processing VIII, A. Aldroubi, A. F. Laine, M. A. Unser
  (Eds.), Vol. 4119, pages 13-23, 2000.
- M. Fenn. Fast Fourier Transform at Nonequispaced Nodes and Applications. PhD
  Thesis, University of Mannheim, 2005.
- J. Ma and M. Fenn. Combined complex ridgelet shrinkage and total variation
  minimization. SIAM J. Sci. Comput. 28, 984-1000, 2006.
- P. Toft. The Radon Transform - Theory and Implementation. Ph.D. thesis. The
  test phantom of the MATLAB scripts refers to it.

The [Radon transform](../applications/radon.md) application lists the two
papers of Potts and Steidl, the thesis of Fenn and the paper of Ma and Fenn. The
polar FFT application lists the linogram paper of Potts and Steidl as well.

## Further information

The README files point to the NFFT website
<http://www.tu-chemnitz.de/~potts/nfft/> for news and updates.
