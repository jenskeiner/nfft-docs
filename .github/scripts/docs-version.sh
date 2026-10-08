#!/usr/bin/env bash
# Usage: docs-version.sh <tag>
#
# Derives the X.Y docs version from a release tag and checks it against
# configure.ac. Writes `version=X.Y` on stdout for $GITHUB_OUTPUT.
#
# Tags carry no `v` prefix and look like 3.6.0. Anything else is refused: a
# pre-release published without the prerelease box ticked would otherwise be
# deployed as `latest`.
set -euo pipefail
tag="${1:?usage: docs-version.sh <tag>}"

if [[ ! "$tag" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
  echo "refusing to deploy docs for tag '$tag': expected X.Y.Z with no prefix" >&2
  exit 1
fi
major="${BASH_REMATCH[1]}"; minor="${BASH_REMATCH[2]}"

# configure.ac keeps major/minor/patch/type in separate m4 defines. Compare only
# major and minor: NFFT_VERSION also carries nfft_version_type ("alpha"), so it
# never equals the tag of a release.
ac_major="$(sed -n 's/^m4_define(\[nfft_version_major\], *\[\([0-9]*\)\]).*/\1/p' configure.ac)"
ac_minor="$(sed -n 's/^m4_define(\[nfft_version_minor\], *\[\([0-9]*\)\]).*/\1/p' configure.ac)"

if [ -z "$ac_major" ] || [ -z "$ac_minor" ]; then
  echo "could not read nfft_version_major/minor from configure.ac" >&2
  exit 1
fi

if [ "$major.$minor" != "$ac_major.$ac_minor" ]; then
  echo "tag $tag says $major.$minor but configure.ac says $ac_major.$ac_minor" >&2
  exit 1
fi

echo "version=$major.$minor"
