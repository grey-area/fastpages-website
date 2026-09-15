---
name: blog-preview
description: Preview awebb.info locally — convert notebooks, serve the site at localhost:4000, and report what changed. Use when asked to preview, serve, or look at the blog before publishing.
---

# Preview the blog locally

Builds and serves the site at http://localhost:4000 so changes can be seen
before anything is pushed. Pushing to `master` deploys, so previewing is how you
check work without publishing it.

## Run it

```bash
make server
```

That starts two containers: `converter` (notebooks → `_posts/`) and `jekyll`
(serves on :4000). Both use stock images, so nothing is built first.

Do **not** block the foreground waiting for it. Start it, then poll until the
server answers:

```bash
docker compose up -d jekyll converter
for i in $(seq 1 90); do
  curl -sf -o /dev/null http://127.0.0.1:4000/ && { echo "up"; break; }
  docker compose logs jekyll 2>/dev/null | grep -qi 'Conversion error\|JavaScript runtime' && { echo "BUILD FAILED"; break; }
  sleep 3
done
```

First start takes ~20–30s: the Jekyll container installs Node (needed for
`$$…$$` in markdown posts) and resolves the bundle. Later starts reuse both.

Stop with `make stop`, or `docker compose down` to remove the containers.

## Then actually look at it

Serving is not previewing. Open the pages the change affects and check them:

- the post or page that changed
- the home page, if a post was added — the card, its thumbnail, the date
- a notebook post, if the converter or its template was touched

Use a browser (Playwright) rather than curl when the question is visual. Report
what you saw, not that the server started.

Worth checking on any new or changed post:

- figures are visible against the dark background and not inverted photographs
  (see `CLAUDE.md` → Images — thumbnails are inverted by default)
- maths rendered, rather than raw `$…$` left in the text
- code blocks highlighted, collapsible cells opening
- no console errors (KaTeX parse failures show up there first)

## If the build fails

- `Could not find a JavaScript runtime` — the Jekyll container lost its Node
  install. `docker compose up -d --force-recreate jekyll`.
- A post missing from the site — check it was converted at all
  (`docker compose logs converter`), and that its filename starts with
  `YYYY-MM-DD-`.
- Styling looks stale — this is local, so it is not the CDN; do a hard reload.

## Notes

- The host Ruby is 2.6 and cannot build this site. Always go through Docker.
- Previewing does not commit or push anything, and must not.
