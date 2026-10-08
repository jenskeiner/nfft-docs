---
name: site-design
description: Use when changing how the NFFT3 docs site looks - typography, spacing, colour palette, code blocks, admonitions, tables, landing page layout, dark mode. Lists the Zensical and Material CSS variables, the theme options and palette in zensical.toml, and how to verify a visual change without screenshots. Triggers - "design", "CSS", "theme", "palette", "dark mode", "typography", "UI polish", "extra.css".
---

# Site design

## Where the frame lives

| Piece | Where |
|-------|-------|
| Custom CSS | `doc/stylesheets/extra.css`, loaded by `extra_css` in `zensical.toml` |
| Theme features | `features` in `[project.theme]` of `zensical.toml` |
| Palette | the three `[[project.theme.palette]]` blocks of `zensical.toml` |
| Logo, favicon | `doc/assets/logo.png`, `doc/assets/favicon.png` |
| Template overrides | `support/overrides/main.html`, `{% extends "base.html" %}` |
| MathJax setup | `doc/javascripts/mathjax.js`. Not a design file. Do not change it. |

Zensical is MkDocs Material compatible. The build uses the `modern`
stylesheets: see the `<link>` to `assets/stylesheets/modern/` in any built
page. Read the theme rules there, never guess them.

`extra.css` holds the brand colours and layout rules for wide tables,
display formulas and API signatures. Read it before you add a rule.

## Palette today

- Three toggles: system, light (`default` scheme), dark (`slate` scheme).
- Light and dark use `primary = "custom"` and `accent = "red"`.
- `extra.css` sets the custom colours. Light: primary `#b81414`, light
  `#d63232`, dark `#8c0f0f`, accent `#d63232`. Dark: header primary
  `#1e1e22`, accent `#ff4d4d`, links `#ff6b6b`.
- The colours come from the logo, a red N on dark grey.
- The system toggle sets no primary and no accent. Its `<input>` in the
  built HTML carries `data-md-color-primary="indigo"` and
  `data-md-color-accent="indigo"`. Check what a reader sees in that mode
  before you change the palette.

## Variables

Set variables in `:root` for the light scheme and in
`[data-md-color-scheme="slate"]` for the dark scheme. Prefer a variable to
a new selector.

| Concern | Variables |
|---------|-----------|
| Brand | `--md-primary-fg-color`, `--md-primary-fg-color--light`, `--md-primary-fg-color--dark`, `--md-primary-bg-color`, `--md-accent-fg-color`, `--md-accent-bg-color` |
| Text and page | `--md-default-fg-color` with `--light`, `--lighter`, `--lightest`; `--md-default-bg-color` with the same suffixes; `--md-typeset-color`, `--md-typeset-a-color` |
| Fonts | `--md-text-font` (Inter today), `--md-code-font` (JetBrains Mono today) |
| Code | `--md-code-fg-color`, `--md-code-bg-color`, `--md-code-hl-color`, `--md-code-hl-*-color` for keyword, string, number, comment, function, name, operator, punctuation, constant, variable, special, generic |
| Admonitions | `--md-admonition-fg-color`, `--md-admonition-bg-color`, `--md-admonition-icon--<type>` |
| Tables | `--md-typeset-table-color`, `--md-typeset-table-color--light` |
| Marks and keys | `--md-typeset-mark-color`, `--md-typeset-del-color`, `--md-typeset-ins-color`, `--md-typeset-kbd-*` |
| Footer | `--md-footer-bg-color`, `--md-footer-bg-color--dark` |

List the variables the theme defines with
`grep -o -- '--md-[a-z-]*' site/assets/stylesheets/modern/*.css | sort -u`.
The modern palette also defines RGB triplets such as `--color-foreground`
and `--color-background` per scheme. List them with
`grep -o -- '--color-[a-z-]*' site/assets/stylesheets/modern/palette.*.css | sort -u`.

## Theme options

- Features: the `features` list. Names follow Material, for example
  `navigation.tabs`, `content.code.copy`, `toc.follow`. Add or remove one
  feature per PR and say what it changes in the DOM.
- Palette: `scheme`, `primary`, `accent`, `media`, `toggle.icon`,
  `toggle.name` per block.
- Do not add fonts, scripts or external requests. Do not add plugins.

## Verify without screenshots

1. Before the change: build, then copy the pages the issue names and
   `site/index.html` to `/tmp/before/`.
2. After the change: build again, copy to `/tmp/after/`, `diff` each pair.
   A CSS-only change gives no HTML diff. Then show the rule in the built
   `site/stylesheets/extra.css` and the theme rule it overrides, found by
   `grep -o` in `site/assets/stylesheets/modern/main.*.css`.
3. Find which elements a selector hits: `grep -c '<class name>'` on the
   built pages. Zero hits means the rule does nothing on that page.
4. Both schemes: every colour set in `:root` needs a check in the `slate`
   block, and the reverse.
5. Contrast: compute the WCAG ratio, at least 4.5 to 1 for text.

   ```
   python3 -c "
   def l(h):
       c=[int(h[i:i+2],16)/255 for i in (1,3,5)]
       c=[x/12.92 if x<=0.03928 else ((x+0.055)/1.055)**2.4 for x in c]
       return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2]
   a,b=sorted([l('#b81414'),l('#ffffff')]); print(round((b+0.05)/(a+0.05),2))"
   ```

6. Run the strict build and `python -m support.checks.site`.
7. In the PR, describe the change per scheme: element, rule, old value,
   new value, contrast ratio.
