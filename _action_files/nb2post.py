#!/usr/bin/env python3
"""Convert _notebooks/*.ipynb into Jekyll posts under _posts/.

Self-contained replacement for the fastpages converter, which ran nbdev 0.2.18
inside the unmaintained hamelsmu/fastpages-nbdev image. nbdev 2.x is Quarto-based
and no longer has notebook2html, and the old fastpages.tpl/hide.tpl extended
`basic.tpl`, an nbconvert 5 template format that nbconvert 6 dropped -- so both
halves had to be rewritten rather than upgraded.

Only nbformat and nbconvert are needed; see requirements.txt for the pins.

Notebook features supported (the set this blog uses):

  * front matter in the first markdown cell:
        # "Title"
        > "Subtitle, becomes the description."

        - toc: true
        - categories: [probability]
        - image: /images/blog_posts/x.png
  * #hide           drop the cell entirely
  * #hide_input     drop the cell's input, keep its output
  * #hide_output    drop the cell's output, keep its input
  * #collapse-show  input in an open <details>
  * #collapse-hide  input in a closed <details>   (#collapse is an alias)
  * > youtube: <url>        in a markdown cell, becomes an embed
  * images referenced from markdown cells by a path relative to _notebooks/,
    copied into images/copied_from_nb/ and rewritten to point there

Directive comments are deliberately left visible in the rendered code, which is
what the fastpages converter did.

Not supported: the `> Note:` / `> Warning:` / `> Tip:` / `> Important:` callouts
fastpages recognised. No post uses them and the site has no CSS for them, so
they would render unstyled. Add them here and to the stylesheet together.

Usage:  python _action_files/nb2post.py [--notebooks DIR] [--posts DIR]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import nbformat
from nbconvert import HTMLExporter
from nbconvert.preprocessors import Preprocessor
from traitlets.config import Config

# Where images referenced from notebooks are copied to, and the URL prefix they
# are rewritten to. Matches the old converter's settings.ini doc_path/doc_baseurl.
COPIED_IMAGE_DIR = Path("images/copied_from_nb")
COPIED_IMAGE_URL = "/images/copied_from_nb"

# Jekyll requires _posts filenames to start with a date.
RE_POST_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}-")

# Front matter, from the first markdown cell.
RE_FM_TITLE = re.compile(r"^#\s+(.*?)\s*$")
RE_FM_SUBTITLE = re.compile(r"^>\s+(.*?)\s*$")
RE_FM_KEY_VALUE = re.compile(r"^-\s+([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*?)\s*$")

# A directive is a comment on its own line: "#hide", "# collapse-show", ...
RE_DIRECTIVE = re.compile(r"^\s*#\s*([a-zA-Z][a-zA-Z_-]*)\s*$", re.MULTILINE)

RE_YOUTUBE = re.compile(r"^>\s*youtube:\s*(\S+)\s*$", re.MULTILINE)
RE_YOUTUBE_ID = re.compile(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/))([A-Za-z0-9_-]+)")

# Image references in markdown cells: ![alt](path) and <img ...>.
RE_MD_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
RE_HTML_IMAGE_TAG = re.compile(r"<img\b[^>]*?/?>")
RE_HTML_ATTR = re.compile(r"""([\w:-]+)\s*=\s*["']([^"']*)["']""")


def strip_quotes(text: str) -> str:
    """Front matter titles are written quoted: # "Title"."""
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    return text


def yaml_scalar(text: str) -> str:
    """Quote a string so YAML reads it back verbatim.

    Titles routinely contain ':' and '?', which are structural in plain YAML.
    A JSON string is always a valid YAML double-quoted scalar.
    """
    return json.dumps(text, ensure_ascii=False)


def parse_front_matter(cell_source: str) -> dict[str, str] | None:
    """Parse the fastpages front matter cell. Returns None if it isn't one.

    Values from '- key: value' lines are passed through verbatim, so
    'categories: [a, b]' stays a YAML flow sequence and 'toc: true' stays a
    boolean, exactly as the old converter emitted them.
    """
    title = None
    description = None
    pairs: list[tuple[str, str]] = []

    for line in cell_source.splitlines():
        if not line.strip():
            continue
        if title is None and (m := RE_FM_TITLE.match(line)):
            title = strip_quotes(m.group(1))
        elif description is None and (m := RE_FM_SUBTITLE.match(line)):
            description = strip_quotes(m.group(1))
        elif m := RE_FM_KEY_VALUE.match(line):
            pairs.append((m.group(1), m.group(2)))
        else:
            # Anything else means this is ordinary prose, not front matter.
            return None

    if title is None:
        return None

    front: dict[str, str] = {"title": yaml_scalar(title)}
    if description is not None:
        front["description"] = yaml_scalar(description)
    for key, value in pairs:
        front[key] = value
    return front


def leading_directives(source: str) -> set[str]:
    """Directive comments anywhere in a code cell, normalised to underscores."""
    return {m.group(1).lower().replace("-", "_") for m in RE_DIRECTIVE.finditer(source)}


class FastpagesDirectives(Preprocessor):
    """Translate #hide / #collapse directives into cell metadata.

    The template reads that metadata; dropping whole cells has to happen here
    because a template cannot remove a cell from the stream.
    """

    def preprocess(self, nb, resources):
        kept = []
        for cell in nb.cells:
            if cell.cell_type == "code":
                if not cell.source.strip():
                    continue  # stray empty cell: render nothing at all
                directives = leading_directives(cell.source)
                if "hide" in directives:
                    continue  # drop the cell entirely, input and output
                if "hide_input" in directives:
                    cell.metadata["hide_input"] = True
                if "hide_output" in directives:
                    cell.metadata["hide_output"] = True
                if "collapse_show" in directives:
                    cell.metadata["collapse_show"] = True
                if "collapse_hide" in directives or "collapse" in directives:
                    cell.metadata["collapse_hide"] = True
            kept.append(cell)
        nb.cells = kept
        return nb, resources


def youtube_embed(url: str) -> str:
    """Build the embed markup, preserving a start-time parameter if present.

    `> youtube: https://youtu.be/ID?t=3704` has to keep ?t=3704, or the video
    starts from the beginning instead of the point the post is pointing at.
    """
    match = RE_YOUTUBE_ID.search(url)
    if not match:
        raise ValueError(f"could not extract a YouTube id from {url!r}")
    query = urlparse(url).query
    start = parse_qs(query).get("t") or parse_qs(query).get("start")
    suffix = f"?t={start[0]}" if start else ""
    return (
        f'<center><iframe width="560" height="315" '
        f'src="https://www.youtube.com/embed/{match.group(1)}{suffix}" '
        f'frameborder="0" allowfullscreen></iframe></center>'
    )


def copy_image(path: str, notebook_dir: Path, repo_root: Path, copied: list[str]) -> str | None:
    """Copy a notebook-relative image into the site. Returns its new URL."""
    if path.startswith(("http://", "https://", "//", "data:", "/", "{{")):
        return None  # remote or already absolute: leave the reference alone
    path = path[2:] if path.startswith("./") else path
    source_file = (notebook_dir / path).resolve()
    if not source_file.is_file():
        print(f"    WARNING: referenced image not found: {path}", file=sys.stderr)
        return None
    destination = repo_root / COPIED_IMAGE_DIR / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_file, destination)
    copied.append(path)
    return f"{COPIED_IMAGE_URL}/{path}"


def figure_markup(url: str, alt: str, width: str | None) -> str:
    """The markup fastpages produced for a notebook-local image.

    A bare <figure> (the stylesheet's figure.image rules don't apply to it, so
    this is just the browser's default figure margins) wrapping an img.docimage,
    with any width= attribute expressed as a max-width so the image still scales
    down on narrow screens.
    """
    style = f' style="max-width: {width}px"' if width else ""
    return f'<figure>\n<img class="docimage" src="{url}" alt="{alt}"{style}>\n</figure>'


def rewrite_images(source: str, notebook_dir: Path, repo_root: Path, copied: list[str]) -> str:
    """Copy notebook-relative images into the site and repoint the references.

    Only images we actually copy are rewrapped; remote images are left exactly
    as the author wrote them.
    """

    def replace_html(match: re.Match) -> str:
        attrs = dict(RE_HTML_ATTR.findall(match.group(0)))
        url = copy_image(attrs.get("src", ""), notebook_dir, repo_root, copied)
        if url is None:
            return match.group(0)
        return figure_markup(url, attrs.get("alt", ""), attrs.get("width"))

    def replace_md(match: re.Match) -> str:
        alt, path = match.group(1), match.group(2)
        url = copy_image(path, notebook_dir, repo_root, copied)
        if url is None:
            return match.group(0)
        return figure_markup(url, alt, None)

    source = RE_MD_IMAGE.sub(replace_md, source)
    return RE_HTML_IMAGE_TAG.sub(replace_html, source)


def convert(notebook_path: Path, posts_dir: Path, repo_root: Path, exporter: HTMLExporter) -> Path:
    notebook = nbformat.read(notebook_path, as_version=4)

    if not notebook.cells:
        raise ValueError("notebook has no cells")

    front = parse_front_matter("".join(notebook.cells[0].source))
    if front is None:
        raise ValueError(
            "first cell is not a fastpages front matter cell "
            '(expected `# "Title"` followed by `- key: value` lines)'
        )
    notebook.cells = notebook.cells[1:]

    copied: list[str] = []
    for cell in notebook.cells:
        if cell.cell_type != "markdown":
            continue
        cell.source = RE_YOUTUBE.sub(lambda m: youtube_embed(m.group(1)), cell.source)
        cell.source = rewrite_images(cell.source, notebook_path.parent, repo_root, copied)

    body, _ = exporter.from_notebook_node(notebook)

    nb_path = notebook_path.relative_to(repo_root).as_posix()
    front["nb_path"] = nb_path
    front["layout"] = "notebook"

    lines = ["---"]
    lines += [f"{key}: {value}" for key, value in front.items()]
    lines += [
        "---",
        "",
        "<!--",
        "#################################################",
        "### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###",
        "#################################################",
        f"# file to edit: {nb_path}",
        "-->",
        "",
        '<div class="container" id="notebook-container">',
        body.strip(),
        "</div>",
        "",
    ]

    out_path = posts_dir / (notebook_path.stem + ".md")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    if copied:
        print(f"    copied {len(copied)} image(s): {', '.join(copied)}")
    return out_path


def build_exporter() -> HTMLExporter:
    config = Config()
    config.HTMLExporter.preprocessors = [FastpagesDirectives]
    config.HTMLExporter.template_name = "fastpages"
    config.HTMLExporter.extra_template_basedirs = [str(Path(__file__).parent / "templates")]
    # Outputs are embedded as data URIs, as the fastpages converter did.
    config.HTMLExporter.embed_images = True
    # nbconvert 7 turns these on by default; fastpages did not emit them, and the
    # site's stylesheet draws its own In[n]/Out[n] labels, so real prompts would
    # duplicate them.
    config.HTMLExporter.exclude_input_prompt = True
    config.HTMLExporter.exclude_output_prompt = True
    # Heading anchors stay (custom-head.html swaps their contents for an icon),
    # but without nbconvert's default pilcrow leaking into the text.
    config.HTMLExporter.anchor_link_text = ""
    return HTMLExporter(config=config)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--notebooks", default=str(repo_root / "_notebooks"))
    parser.add_argument("--posts", default=str(repo_root / "_posts"))
    args = parser.parse_args()

    notebooks_dir = Path(args.notebooks).resolve()
    posts_dir = Path(args.posts).resolve()
    posts_dir.mkdir(parents=True, exist_ok=True)

    notebooks = sorted(notebooks_dir.glob("*.ipynb"))
    if not notebooks:
        print(f"No notebooks found in {notebooks_dir}", file=sys.stderr)
        return 0

    exporter = build_exporter()
    failures = 0
    for notebook_path in notebooks:
        if not RE_POST_DATE.match(notebook_path.name):
            print(f"  SKIP {notebook_path.name}: filename must start with YYYY-MM-DD-", file=sys.stderr)
            failures += 1
            continue
        try:
            out_path = convert(notebook_path, posts_dir, repo_root, exporter)
            try:
                shown = out_path.relative_to(repo_root)
            except ValueError:
                shown = out_path  # --posts can point outside the repo
            print(f"  {notebook_path.name} -> {shown}")
        except Exception as exc:  # noqa: BLE001 - report and keep going
            print(f"  FAILED {notebook_path.name}: {exc}", file=sys.stderr)
            failures += 1

    print(f"Converted {len(notebooks) - failures}/{len(notebooks)} notebooks")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
