# People

The list follows the file `AUTHORS` in the source tree. The role of each person
is as stated there.

## Authors and maintainers

The NFFT3 package was developed and is maintained by the following persons.

**Prof. Dr. Daniel Potts**, TU Chemnitz, Fakultaet fuer Mathematik,
Reichenhainer Str. 39, 09107 Chemnitz, Germany.

**Dr. Jens Keiner**

- fast polynomial transform (`kernel/fpt`)
- NFFT on the sphere (`kernel/nfsft`)
- fast summation on the sphere (`applications/fastsumS2`)
- autotools, doxygen and friends
- MATLAB MEX interface for NFSFT (`matlab/nfsft`)

**Prof. Dr. Stefan Kunis**

- NFFT (`kernel/nfft`)
- inverse transforms (`kernel/solver`)
- NFFT on the hyperbolic cross (`kernel/nsfft`)
- fast Gauss transform (`applications/fastgauss`)
- MATLAB MEX interface for NFFT (`matlab/nfft`)

## Further contributors

Further contributions, in particular applications, are due to the following
persons.

**Dr. Markus Fenn**

- NFFT on the hyperbolic cross (`kernel/nsfft`)
- polar FFT (`applications/polarFFT`)
- discrete Radon transform and ridgelet transform (`applications/radon`)
- fast summation (`applications/fastsum`)

**Steffen Klatt**

- nonequispaced cosine transform (`kernel/nfct`)
- nonequispaced sine transform (`kernel/nfst`)

**Dr. Tobias Knopp**

- transforms in magnetic resonance imaging (`kernel/mri`)
- nonequispaced in time and frequency FFT (`kernel/nnfft`)
- reconstruction in magnetic resonance imaging (`applications/mri`)

**Dr. Antje Vollrath**

- transforms on the rotation group SO(3) (`kernel/nfsoft`)

**Dr. Toni Volkmer**

- OpenMP parallelization of NFFT (`kernel/nfft`)
- OpenMP parallelization of NFSFT (`kernel/nfsft`)
- OpenMP parallelization of fast summation (`applications/fastsum`)

**Dr. Michael Quellmalz**

- OpenMP parallelization of NFSOFT (`kernel/nfsoft`)
- MATLAB MEX interface for NFSOFT (`matlab/nfsoft`)

**Felix Bartel**

- MATLAB MEX interface for FPT (`matlab/fpt`)

**Melanie Kircheis**

- inverse NFFT in 1D (`matlab/infft1d`)

**Michael Schmischke**

- Julia interface (`julia`)

## Attributions in the source files

Some source files name a further author.

- Michael Hofmann: the radix sort of node indices in `kernel/util/sort.c`.
- Michael Quellmalz: the documentation of the flag `NFSFT_EQUISPACED`.
- Franziska Nestler: the function `cardinal_bspline` in the MATLAB class
  `matlab/infft1d/infft.m`.
- Markus Fenn: the MATLAB function `phantom.m` in the application directories.
- Felix Bartel: the MEX file `matlab/fpt/fptmex.c`, 2018.

## Contributors named in the ChangeLog

The [changelog](changelog.md) names these GitHub accounts as authors of
changes in version 3.6.0: @jenskeiner, @michaelquellmalz, @mnolander,
@wagnertheresa, @FranziskaN, @ralfHielscher and @DarthGandalf.

## Contact

Comments are welcome. Report bugs and missing or confusing instructions in the
[issue tracker](https://github.com/NFFT/nfft/issues) or directly to
[Daniel Potts](mailto:potts@mathematik.tu-chemnitz.de). The postal address is:

```text
Prof. Dr. Daniel Potts
TU Chemnitz, Fakultaet fuer Mathematik
Reichenhainer Str. 39
09107 Chemnitz
GERMANY
```

Alternatively, contact [Stefan Kunis](mailto:stefan.kunis@math.uos.de) or
[Jens Keiner](mailto:jens@nfft.org). The address `mail@nfft.org` is the bug
report address set in `configure.ac`.

If you find NFFT useful, the authors would like to hear which application you
use it for.
