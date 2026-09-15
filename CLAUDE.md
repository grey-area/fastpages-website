# CLAUDE.md

Source for [awebb.info](https://www.awebb.info) — Andrew M. Webb's blog, CV and
publications. Jekyll site, posts written as Jupyter notebooks. `README.md` is
for humans writing posts; this file is the operational detail an agent needs.

Originally generated from [fastpages](https://github.com/fastai/fastpages), which
is unmaintained. The build has been rebuilt on current pinned software and no
longer depends on any fastpages infrastructure — don't reintroduce it, and treat
fastpages docs found online as describing a stack this repo no longer runs.

## Skills

- `/blog-preview` — build and serve the site locally, then actually look at it.
- `/blog-post` — turn a directory of draft text and images into a markdown post.
  The author's words are preserved verbatim; the skill does layout, not writing.

## Pipeline

```
_notebooks/*.ipynb ─▶ _action_files/nb2post.py ─▶ _posts/*.md ─▶ Jekyll ─▶ gh-pages ─▶ awebb.info
```

`.github/workflows/ci.yaml` runs the whole thing on every push to `master`:
Python 3.12 + nbconvert 7 (pinned in `_action_files/requirements.txt`), then
Ruby 3.2 + Jekyll 4.4 (pinned in `Gemfile.lock`), then `peaceiris/actions-gh-pages`.
`gh-page.yaml` then checks the Pages build succeeded. **Pushing to `master`
deploys** — there is no staging environment.

### Generated, never committed

`_posts/*.md` and `images/copied_from_nb/` are build artifacts. Editing them is
always wrong; edit the notebook and re-run the converter. `_notebooks/` is the
source of truth.

`_posts/` holds converter output *and* any hand-written markdown post, so the
converter writes a `_posts/.gitignore` naming only the files it generated. That
is why the ignore list is per-file rather than `_posts/*.md`: a blanket rule
would take hand-written posts with it.

## Working locally

The host has Ruby 2.6, too old for Jekyll 4.4. Use containers:

```bash
# convert notebooks -> _posts
docker run --rm -v "$PWD":/repo -w /repo python:3.12-slim \
  bash -c "pip install -q -r _action_files/requirements.txt && python _action_files/nb2post.py"

# build the site into a scratch dir ($OUT, outside the repo)
docker run --rm -v "$PWD":/data -v "$OUT":/out -w /data ruby:3.2 \
  bash -c "bundle install --quiet && JEKYLL_ENV=production bundle exec jekyll build -d /out/site --strict_front_matter"

make server   # converter + Jekyll on :4000, installs Node (see below)
make convert-local   # converter directly, no Docker
```

## Verifying a change

`_posts` is not committed, so a converter regression is invisible until it is
live. Don't eyeball it — diff against the live site:

1. Capture the published posts from `https://www.awebb.info` as a baseline.
2. Reconvert, rebuild.
3. Compare structure (tag + class sequence, aligned with `difflib`), visible
   text, embedded-image payload sizes, and the `<title>` / `og:*` metadata.

Differences that survive that comparison are real; nbconvert defaults and
Pygments token changes produce a lot of noise that looks alarming and isn't.

For visual changes, render in a browser and look. A green build says the build
ran, not that the output is right.

## Images

Three populations, handled differently:

| where it comes from | how it ends up on the page |
|---|---|
| notebook cell outputs (matplotlib) | base64 data URIs embedded by the converter, inside `.output_png` |
| images in notebook markdown cells | copied to `images/copied_from_nb/`, wrapped in `<figure>` as `img.docimage`; a `width=N` attribute becomes `style="max-width: Npx"` |
| post card thumbnails | `images/blog_posts/*.png`, named by the `image:` front matter key |

### Figures are light-theme and inverted in CSS

The site is dark; the figures are not. They are inverted at render time in
`custom-styles.scss` — **never by rewriting the image bytes**:

```scss
.output_png img,
img[src*="net_schematic"],
.post-card-media img:not([src*="arm_summit"]):not([src*="orb_slam"]) {
  filter: invert(90.6%) hue-rotate(180deg);
}
```

`90.6%` is calibrated, not arbitrary: `invert(n)` maps white to `(1 - n)`, and
`1 - 24/255` lands white panels exactly on the `#181818` page background. Full
`invert(100%)` gives black rectangles sitting on charcoal. `hue-rotate(180deg)`
restores the data colours afterwards.

Rewriting the PNGs instead was tried and reverted. Anti-aliased edges of
coloured curves blend toward the old white background, so a pixel-wise invert
leaves the line core coloured and the fringe light — every smooth curve becomes
a dotted stripe. It also inverts the notebooks themselves, which each post links
to via its GitHub/Colab/Binder badges, where a light background is correct.

**The scoping is what will bite you**, because it differs per population:

- Thumbnails are inverted **by default**. Adding a *photograph* as a post image
  means adding it to the `:not()` list, or it renders as a negative.
- Markdown-cell images are inverted **only if named** — currently just
  `net_schematic`. A new diagram or line drawing needs adding to the selector.
- Notebook outputs need nothing; `.output_png` covers them.

Check any new image on the live dark background rather than assuming.

## Traps that have already cost time

**Front matter `image:` needs a leading slash.** `jekyll-seo-tag` resolves a
relative path against the post's own URL, so `image: images/x.png` produces
`awebb.info/probability/2019/03/22/images/x.png` — a 404, so the social preview
breaks. Nothing on the site surfaces this: the homepage cards use `relative_url`
and resolve correctly, so the thumbnail looks fine while the share card is dead.

**`hide: true` does not unpublish.** It removes a post from the listing but not
from `sitemap.xml` or `search-data.json`. To take something out of circulation,
move it out of `_notebooks/` (see `_templates/`).

**CSS changes can appear not to work.** GitHub Pages serves HTML at
`max-age=600` but CSS at `max-age=14400`, and the CDN can refresh one without
the other, leaving new markup against a four-hour-old stylesheet. The stylesheet
link carries `?v={{ site.time }}` to defeat this — keep it. If a style change
looks ignored, check `last-modified` on the CSS before suspecting the selector.

**KaTeX renders in the browser, and only at the delimiters it is given.** The
list lives in `custom-head.html`: `$$`, `$`, `[%`, and the bare LaTeX
environments `align`, `align*`, `equation`, `equation*`, `gather`, `gather*`.
A `\begin{...}` written bare, with no `$$` around it, is left on the page as raw
source unless its environment is in that list — MathJax used to pick these up
natively and was removed, so this is a standing gap, not a one-off. Add the
environment to the delimiters (and to the `has_math` gate) rather than editing
the author's maths.

**KaTeX 0.16 is stricter than the 0.11 it replaced.** `_` inside `\text{}` must
be `\_`, and multi-token subscripts need braces (`\mathbb{E}_{\hat{\eta}}`).
There is no MathJax fallback any more, so a bad expression renders as raw source.

Because rendering is client-side, `curl` cannot check any of this — the fetched
HTML still has the raw `$…$`. Load the page in a browser and count `.katex`,
`.katex-error`, and leftover `\begin{`/`\frac` in `innerText` with `pre`, `code`
and `annotation` stripped (KaTeX puts the original TeX in an `<annotation>`, so
leaving those in makes every correctly-rendered post look broken).

**KaTeX only loads on pages that contain maths** (`custom-head.html` checks the
page content). It is ~195 KB; don't make it unconditional.

**`head.html` includes `custom-head.html`.** Anything emitted in both appears
twice — duplicate `<title>`, duplicate canonical, a tracking snippet counting
every hit twice. Check the built HTML after touching either.

**Markdown posts work** and are first-class. One difference: `$$…$$` in a
markdown post is rendered at build time by `kramdown-math-katex`, which needs a
JavaScript runtime. CI has Node; the `jekyll` compose service installs it at
start-up for parity. Notebook posts don't need it — their content is a raw HTML
block kramdown passes through, so KaTeX runs client-side.

**Pins are load-bearing.** nbconvert 7.16.4 breaks against mistune ≥ 3.1
(`'MathBlockParser' object has no attribute 'parse_axt_heading'`). Keep mistune
below 3.1 whenever nbconvert moves.

## Conventions

- Small changes go straight to `master`; that is the repo's history. Anything
  touching the converter or the build should go via a branch and PR, because it
  regenerates every post.
- `LICENSE` is Apache 2.0, inherited from fastpages, and still warranted —
  the notebook stylesheets, search, notebook layout and badges are
  fastpages-derived. It covers the code, not the writing.
