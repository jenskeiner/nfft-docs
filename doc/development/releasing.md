# Releasing

## Version numbers

The version lives in `configure.ac` as four m4 defines:

```m4
m4_define([nfft_version_major], [3])
m4_define([nfft_version_minor], [6])
m4_define([nfft_version_patch], [0])
m4_define([nfft_version_type], [alpha])
```

Tags carry **no** `v` prefix: `3.6.0`, not `v3.6.0`.

The documentation site is versioned as `X.Y` only. A patch release redeploys
the same `X.Y`, because patch releases rarely change the documentation and the
version selector would otherwise grow with every one.

## Steps

1. Bump the m4 defines in `configure.ac`, and clear `nfft_version_type` for a
   final release. Merge that to `develop`.
2. `draft-release.yml` keeps a draft release up to date on every push to
   `develop`. Open it, check the notes, set the tag to `X.Y.Z`.
3. For a pre-release, **tick the pre-release box**. The docs workflow skips
   pre-releases, and `docs-version.sh` refuses any tag that is not exactly
   `X.Y.Z`, so an `-rc` tag cannot be published as `latest` either way.
4. Publish the release. `docs.yml` then runs `deploy-release`, which:
   - checks out the tag,
   - derives `X.Y` and refuses to continue unless it matches `configure.ac`,
   - generates the API pages, builds with `--strict`, runs the site checks,
   - `mike deploy --push --update-aliases X.Y latest`,
   - `mike set-default --push latest`.
5. Watch the run. `https://nfft.github.io/nfft/X.Y/` and `/latest/` should both
   answer, and the root should redirect to `/latest/`.

The release tarball is separate from the site. `make dist` runs Doxygen and
ships the HTML in `doxygen/html`, next to the Markdown sources of the site. It
needs `doxygen` and `graphviz` at configure time. `make distcheck` checks the
tarball.

To redeploy or backfill a version, run the `Docs` workflow manually with a
`version` input. **Dispatch it from the tag you mean**, not from `develop`, or
that version gets `develop`'s content.

## The gh-pages branch

Two jobs write it, and they must not fight:

- `docs.yml` deploys the site through `mike`, which owns the root
  `index.html`, `versions.json` and one directory per version.
- `build-linux.yml` publishes the accuracy dashboard under `accuracy/` through
  `.github/scripts/gh-pages-publish.sh`.

Both use `concurrency: { group: gh-pages }` and neither pushes with `--force`.
`gh-pages-publish.sh` retries on a rejected push by rebasing on the current tip.

### One-time move of the accuracy reports

The accuracy dashboard used to live at the root of `gh-pages`, which is where
`mike` now writes the version redirect. The scripts already publish to
`accuracy/`, but the files that were published **before** that change are still
at the root and have to be moved once, by hand:

```bash
git clone --branch gh-pages git@github.com:NFFT/nfft.git gh-pages-move
cd gh-pages-move
mkdir -p accuracy
git mv index.html baseline pr accuracy/ 2>/dev/null || true
# .nojekyll must stay at the root, or GitHub Pages starts running Jekyll.
git checkout HEAD -- .nojekyll 2>/dev/null || touch .nojekyll
git commit -m "Move the accuracy reports under accuracy/"
git push origin gh-pages
```

Until that runs, the old root copies simply sit there unused. Two consequences
worth knowing:

- Links to `/pr/<n>/` in existing pull request comments break once the move
  happens. They are not rewritten.
- The first `mike set-default --push latest` replaces the root `index.html`
  with the redirect to `/latest/`, so the old dashboard landing page disappears
  at that moment. Deploy `dev` first, or run the move first, so that
  `/accuracy/` is populated before the root is taken over.
