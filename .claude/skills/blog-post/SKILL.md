---
name: blog-post
description: Turn a directory of draft text and images into a markdown blog post for awebb.info. Copies the content in, follows any inline instructions in the draft, preserves the author's words verbatim, and previews the result. Use when given a folder or file of draft writing to publish.
---

# Build a blog post from a draft

Takes a reference to draft material — a directory, a file, a path — usually
somewhere temporary, and turns it into a post in this repo.

**The author's words are the deliverable. You are doing layout, not writing.**

## Hard rules

1. **Write no prose of your own.** No introduction, no conclusion, no summary,
   no linking sentences, no section headings that aren't already in the draft,
   no captions. If the post seems to need something, say so at the end — don't
   supply it.
2. **The text is verbatim.** You may add markdown and fix whitespace. You may
   not reword, reorder, condense, expand, or "improve" a sentence. Do not
   silently correct spelling, grammar or facts — report them instead.
3. **Copy everything in; link to nothing outside.** The draft location is
   temporary and will vanish. No path from it may survive into the post, the
   images, or the front matter.
4. **Never commit.** Write the files, preview, report. Committing is the
   author's decision.

## Steps

### 1. Read the draft

Read every file in the referenced location. Identify the prose, the images, and
any instructions to you.

**Instructions in the draft** look like `<the architecture diagram goes here>`
or `<make this a bulleted list>` — a directed note to whoever is assembling the
post, not content. Carry them out, then remove them: an instruction must never
appear in the published post. If one is ambiguous, or asks for something you
cannot do, do the rest and raise it at the end rather than guessing.

### 2. Copy the images in

Post images live in `images/blog_posts/<slug>/`, which is tracked by git. Copy
them there — do not reference the draft directory, and do not put them in
`images/copied_from_nb/`, which is generated and wiped on every build.

Reference them with a site-absolute path:

```markdown
![](/images/blog_posts/my-post-slug/diagram.png)
```

Alt text is text. If the draft's placeholder names the image
(`<the architecture diagram goes here>`), use that wording. Otherwise leave it
empty and say so in your report — do not invent a description.

Check both directions and report either: images in the draft that the text never
places, and placements in the text with no matching image.

### 3. Write the post

`_posts/YYYY-MM-DD-slug.md`, dated the day it is being written.

```yaml
---
layout: post
title: <from the draft>
description: <from the draft>
categories: [<existing category>]
image: /images/blog_posts/my-post-slug/thumbnail.png
toc: true
---
```

- `title` and `description` come **from the draft**. If it has no clear title or
  standfirst, ask — do not compose one.
- `image:` **needs the leading slash**, or the social preview 404s while the
  homepage thumbnail still looks right, so the breakage is invisible.
- `categories:` reuse an existing one where it fits — currently: `Bayesian`,
  `deep learning`, `dimensionality`, `distributed`, `inference`, `MCMC`,
  `presentation`, `probability`, `pytorch`, `sampling`, `simulation`, `SLAM`,
  `threejs`. Proposing a new one is fine; confirm it rather than deciding.
- `toc: true` for anything with headings.

Markdown you may add, because it is formatting rather than content: headings
for what are already headings, lists for what are already lists, fenced code
blocks with a language, emphasis the draft marks some other way, links where the
draft supplies the URL, and blockquotes for quoted material. Match the house
style by reading an existing post first.

### 4. Check the thumbnail will not be inverted

Figures on this site are light-theme and inverted in CSS, and **post-card
thumbnails are inverted by default**. See `CLAUDE.md` → Images.

- A light-background plot or diagram: correct as-is.
- A photograph, screenshot, or anything already dark: it will render as a
  negative. Add it to the `:not()` list on the `.post-card-media img` rule in
  `_sass/minima/custom-styles.scss`.

Inline images in the post body are not inverted, so they need nothing.

### 5. Preview

Use `/blog-preview`. Open the post and the home page, and look at them: images
present and the right way round, headings sensible, maths and code rendered, the
card and its thumbnail correct.

### 6. Report

Do not report success. Report:

- **Instructions found and how each was handled** — including any you skipped.
- **Anything ambiguous**, with the decision you made so it can be overridden.
- **Mistakes in the draft**: spelling, grammar, broken numbering, a claim that
  contradicts itself, a dead link. Quote them and leave them in the post. They
  are the author's to fix.
- **Anything you left empty** — alt text, description, a missing thumbnail.
- **What you changed structurally** — "made these five lines a bulleted list".
- That it is **uncommitted**, and which files are new.

Then stop. Don't commit, don't push.

## Verify before reporting

```bash
# no path from the draft directory survived
grep -rn "<draft-path>" _posts/<new-post>.md images/blog_posts/<slug>/ 2>/dev/null

# no unhandled instruction left in the post
grep -nE '<[^>]{4,}>' _posts/<new-post>.md

# every image the post references exists
grep -o '(/images/[^)]*)' _posts/<new-post>.md | tr -d '()' | while read p; do
  [ -f ".$p" ] || echo "MISSING: $p"
done
```

The second will also match legitimate inline HTML — read the hits, don't assume.
