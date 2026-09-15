# CLAUDE.md

Source for [awebb.info](https://www.awebb.info) — Andrew M. Webb's blog, CV and
publications. Jekyll site, posts written as Jupyter notebooks. `README.md` is
for humans writing posts; this file is the operational detail an agent needs.

Originally generated from [fastpages](https://github.com/fastai/fastpages), which
is unmaintained. The build has been rebuilt on current pinned software and no
longer depends on any fastpages infrastructure — don't reintroduce it, and treat
fastpages docs found online as describing a stack this repo no longer runs.

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

The converter writes a `_posts/.gitignore` naming exactly the files it produced,
so generated posts are ignored while hand-written markdown posts in `_posts/`
stay tracked. **Never replace that with a blanket `_posts/*.md` rule** — it
silently swallows hand-written posts, which then never get committed, never
reach CI, and never publish, with no error anywhere.

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

1. Capture the 12 published posts from `https://www.awebb.info` as a baseline.
2. Reconvert, rebuild.
3. Compare structure (tag + class sequence, aligned with `difflib`), visible
   text, embedded-image payload sizes, and the `<title>` / `og:*` metadata.

This method has caught: pilcrows and `In [n]:` prompts leaking into text,
duplicated cell labels, a stray `<pre>` from an empty cell, and a dropped
`?t=` YouTube start time. All were invisible at a glance.

For visual changes, render in a browser and look. A green build says the build
ran, not that the output is right.

## Traps that have already cost time

**Front matter `image:` needs a leading slash.** `jekyll-seo-tag` resolves a
relative path against the post's own URL, so `image: images/x.png` produces
`awebb.info/probability/2019/03/22/images/x.png` — a 404. Every post's social
preview was broken for years this way; it stayed invisible because the homepage
cards use `relative_url`, which resolves correctly.

**`hide: true` does not unpublish.** It removes a post from the listing but not
from `sitemap.xml` or `search-data.json`. To take something out of circulation,
move it out of `_notebooks/` (see `_templates/`).

**CSS changes can appear not to work.** GitHub Pages serves HTML at
`max-age=600` but CSS at `max-age=14400`, and the CDN can refresh one without
the other, leaving new markup against a four-hour-old stylesheet. The stylesheet
link carries `?v={{ site.time }}` to defeat this — keep it. If a style change
looks ignored, check `last-modified` on the CSS before suspecting the selector.

**Don't rewrite figure image bytes for the dark theme.** Matplotlib figures are
light-themed and are inverted at render time in `custom-styles.scss`:

```scss
filter: invert(90.6%) hue-rotate(180deg);
```

`90.6%` is calibrated, not arbitrary: `invert(n)` maps white to `(1 - n)`, and
`1 - 24/255` lands white panels exactly on the `#181818` page background. Full
`invert(100%)` gives black rectangles on charcoal. A pixel-wise rewrite of the
PNGs was tried and reverted — anti-aliased edges of coloured curves blend toward
the old white background, so inverting "greyscale" pixels leaves a dotted white
fringe along every line. It also breaks the notebooks on GitHub/Colab/Binder,
which each post links to.

**KaTeX 0.16 is stricter than the 0.11 it replaced.** `_` inside `\text{}` must
be `\_`, and multi-token subscripts need braces (`\mathbb{E}_{\hat{\eta}}`).
There is no MathJax fallback any more, so a bad expression renders as raw source.
After touching maths, render every `$…$` and `$$…$$` in `_notebooks` and `_posts`
through the exact KaTeX build the site loads.

**KaTeX only loads on pages that contain maths** (`custom-head.html` checks the
page content). It is ~195 KB; don't make it unconditional.

**`head.html` includes `custom-head.html`.** Anything emitted in both appears
twice. That is how the site ended up with two `<title>` tags, two canonicals and
a double-counting analytics snippet. Check the built HTML after touching either.

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
- Dead fastpages scaffolding has been removed deliberately (`_fastpages_docs/`,
  `setup.yaml`, `issue_reminder.yaml`, `check_config.yaml`, the Word/pandoc
  path). Don't restore it.
