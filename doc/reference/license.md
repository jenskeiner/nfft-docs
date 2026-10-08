# License

NFFT3 is free software. You can redistribute it and modify it under the terms
of the GNU General Public License, version 2, or at your option any later
version. If not stated otherwise, this applies to all files in the package and
its sub-directories.

## Copyright holders

Copyright (c) 2002, 2017 Jens Keiner, Stefan Kunis, Daniel Potts

The software was written by Jens Keiner, Stefan Kunis and Daniel Potts. It was
developed at the Mathematical Institute of the University of Luebeck and at the
Faculty of Mathematics of Chemnitz University of Technology. Other
contributors are listed on the [People](people.md) page.

## License notice

The source files of the library carry this notice in their header:

```text
Copyright (c) 2002, 2017 Jens Keiner, Stefan Kunis, Daniel Potts

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc., 51
Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
```

Most MATLAB interface files carry the same notice. Some files, for example the
Julia interface files in `julia/`, have no notice in the header. The statement
above, from `README.md`, applies to them.

## The license text

The full text of the GNU General Public License, version 2, is the file
`COPYING` in the top directory of the source tree and of every release
tarball. The file is also available in the
[repository](https://github.com/NFFT/nfft/blob/develop/COPYING). The text is
not repeated here.

## Linking and proprietary programs

The last paragraph of `COPYING` states:

> This General Public License does not permit incorporating your program into
> proprietary programs. If your program is a subroutine library, you may
> consider it more useful to permit linking proprietary applications with the
> library. If this is what you want to do, use the GNU Library General Public
> License instead of this License.

NFFT3 is a subroutine library distributed under the General Public License, not
under the Library General Public License. The `README.md` file makes no further
statement about linking.

## Third-party files

Some files carry a different notice.

- `include/cycle.h` is taken from FFTW. It carries the copyright of Matteo
  Frigo and the Massachusetts Institute of Technology and a permissive license
  notice in its header.
- The directory `3rdparty/` contains code that is needed to build NFFT3 and is
  not part of the library proper. Its `README` states that all code in the
  subpackages is copyright of the respective authors as stated in each package.
  Currently the directory holds `cstripack`, a C version of the Fortran package
  STRIPACK by Robert J. Renka for Delaunay triangulations and Voronoi
  partitions on the unit sphere. The package is used only by the
  [sphere inversion application](../applications/iterS2.md) and is not part of
  `make dist`.
- The FFTW3 library is a separate hard dependency. It is not part of the NFFT3
  package. See <https://fftw.org>.
