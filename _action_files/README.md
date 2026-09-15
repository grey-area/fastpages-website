# Notebook converter

Turns `_notebooks/*.ipynb` into Jekyll posts in `_posts/`. Run by CI on every
push, before the Jekyll build.

```
_action_files/
├── nb2post.py                    the converter
├── requirements.txt              pinned dependencies
└── templates/fastpages/          nbconvert template (conf.json + index.html.j2)
```

## Running it

```bash
make convert-local                        # direct, needs python3
make convert                              # via docker-compose
python3 _action_files/nb2post.py          # same thing, explicitly
```

Output goes to `_posts/`, and images referenced from notebooks are copied into
`images/copied_from_nb/`. Both are build artifacts, gitignored, and regenerated
on every build — don't commit them and don't edit them by hand.

## What replaced what

This used to be a Docker action built `FROM hamelsmu/fastpages-nbdev`: an
untagged, unmaintained 2020 image pinning nbdev 0.2.18, plus pandoc for a Word
`.docx` → post path that this blog never used. It was the last piece of the
original fastpages stack and the only thing standing between the notebooks and
a broken build if that image ever went away.

Neither half could be upgraded in place:

- nbdev 2.x is Quarto-based and has no `notebook2html`; the 0.2 API is gone.
- `fastpages.tpl` / `hide.tpl` extended `basic.tpl`, the nbconvert **5**
  template format, which nbconvert 6 removed.

So both were rewritten against nbconvert 7. The `basic` template still emits the
legacy class vocabulary (`input_area`, `output_area`, `output_png`,
`output_wrapper`, `highlight`, …) that `_sass/minima/fastpages-styles.scss` and
`custom-styles.scss` target, so the stylesheets were unchanged.

## Supported notebook features

Front matter goes in the first markdown cell:

```
# "Post title"
> "Subtitle, which becomes the description."

- toc: true
- categories: [probability]
- image: /images/blog_posts/something.png
```

`image:` needs a **leading slash**. Without one, `jekyll-seo-tag` resolves it
against the post's own URL and every social preview 404s.

In code cells, as a comment on its own line:

| directive | effect |
|---|---|
| `#hide` | drop the cell entirely |
| `#hide_input` | drop the input, keep the output |
| `#hide_output` | drop the output, keep the input |
| `#collapse-show` | input in an open `<details>` |
| `#collapse-hide` | input in a closed `<details>` (`#collapse` is an alias) |

In markdown cells:

- `> youtube: https://youtu.be/ID?t=123` becomes a centred embed, keeping the
  start time.
- Images with a path relative to `_notebooks/` are copied into the site and
  rewritten. Remote images are left alone.

Empty code cells render nothing. Directive comments stay visible in the rendered
code, which is what the old converter did.

**Not supported:** the `> Note:` / `> Warning:` / `> Tip:` / `> Important:`
callouts fastpages recognised. No post uses them and the site has no CSS for
them, so they would render unstyled. Add them to `nb2post.py` and to the
stylesheet together.

## Changing the dependencies

`requirements.txt` is pinned deliberately. In particular nbconvert 7.16.4 breaks
against mistune ≥ 3.1 (`'MathBlockParser' object has no attribute
'parse_axt_heading'`), so keep mistune pinned below 3.1 whenever nbconvert moves.

After any change, re-run the golden comparison: convert all notebooks, build the
site, and diff the rendered posts against the previous output. `_posts` is not
committed, so a converter regression is otherwise invisible until it is live.
