# awebb.info

Source for [awebb.info](https://www.awebb.info) — Andrew M. Webb's blog, CV and
publications. Posts are written as Jupyter notebooks; everything else is Jekyll.

Originally generated from [fastpages](https://github.com/fastai/fastpages), which
is no longer maintained. The build has since been rebuilt on current, pinned
software — see [Build](#build) below.

## Writing a post

Add a notebook to `_notebooks/`, named `YYYY-MM-DD-slug.ipynb`. The first
markdown cell is the front matter:

```
# "Post title"
> "Subtitle, which becomes the description and the social preview text."

- toc: true
- branch: master
- badges: false
- comments: false
- categories: [probability]
- hide: false
- search_exclude: false
- image: /images/blog_posts/something.png
```

`image:` needs a **leading slash**. Without one `jekyll-seo-tag` resolves it
against the post's own URL and the social preview 404s.

`hide: true` keeps a post off the listing, but it does **not** keep it out of
`sitemap.xml` or the search index — it stays publicly reachable. To take
something out of circulation entirely, move it out of `_notebooks/`.

Push to `master` and CI does the rest. `_templates/2017-02-27-template.ipynb` is
a scaffold to copy; `_action_files/README.md` documents every directive the
converter understands (`#hide`, `#collapse-show`, `> youtube:`, and so on).

## Build

```
_notebooks/*.ipynb  ──▶  _action_files/nb2post.py  ──▶  _posts/*.md  ──▶  Jekyll  ──▶  gh-pages
```

| stage | what runs it |
|---|---|
| notebook → post | Python 3.12 + nbconvert 7, pinned in `_action_files/requirements.txt` |
| post → site | Ruby 3.2 + Jekyll 4.4, pinned in `Gemfile.lock` |
| deploy | `peaceiris/actions-gh-pages` → `gh-pages` branch → GitHub Pages |

All of it is in `.github/workflows/ci.yaml`, on every push to `master`.
`gh-page.yaml` checks afterwards that the Pages build succeeded.

`_posts/` and `images/copied_from_nb/` are **generated** and gitignored.
Regenerate them; never commit or hand-edit them.

## Local development

```bash
make server         # converter + Jekyll at http://localhost:4000
make convert        # notebooks -> posts, no Jekyll
make convert-local  # same, without Docker (needs python3)
make stop
```

Both services run stock images (`python:3.12-slim`, `ruby:3.2`), so there is
nothing of ours to build first.

## Layout

| path | |
|---|---|
| `_notebooks/` | posts, as notebooks — the source of truth |
| `_action_files/` | the notebook converter ([README](_action_files/README.md)) |
| `_templates/` | post scaffold and converter reference notebooks; not published |
| `_pages/` | About, CV, Publications, QCircuits, search, 404 |
| `_sass/minima/custom-styles.scss` | the theme — dark palette, typography, layout |
| `_includes/`, `_layouts/` | overrides of the remote `minima` theme |
| `_plugins/` | `{% fn %}` / `fndetail` footnote tags |
| `misc/` | papers and CV as PDFs |
| `qcircuits/` | generated Sphinx docs for [QCircuits](https://github.com/grey-area/qcircuits) |

## Licence

The code is under the Apache 2.0 [LICENSE](LICENSE), inherited from fastpages.
Parts of this repo are still fastpages-derived — the notebook stylesheets,
search, the notebook layout and badges — so the licence and its attribution
stay.

That licence covers the code. It is not intended to cover the writing: blog
posts, the CV and the PDFs under `misc/` are © Andrew M. Webb, all rights
reserved.
