# Templates and fastpages reference notebooks

Not published. These live outside `_notebooks/` and `_posts/` so the converter
and Jekyll ignore them, and `_templates` is listed under `exclude:` in
`_config.yml` so nothing here is copied into the built site.

- `2017-02-27-template.ipynb` — scaffold for a new notebook post: front matter
  keys, `#collapse-hide` / `#collapse-show` / `#hide_input` directives, and the
  image-embedding syntax. Copy it into `_notebooks/` with a new date to start a post.
- `2020-02-20-test.ipynb`, `2020-01-14-test-markdown-post.md` — the upstream
  fastpages demo posts, kept for reference on what the converter supports.

They were previously in `_notebooks/` and `_posts/` with `hide: true`. That keeps
a post off the listing but not out of the sitemap or the search index, so all
three were publicly reachable and indexed -- including one titled "Title".
