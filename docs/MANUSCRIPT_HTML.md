# Manuscript HTML — generated, offline, and stamped with the anchor's hash

**Build:** `python scripts/build_manuscript_html.py`
**Output:** `viz/manuscript.html` (+ `viz/katex/` assets, + `viz/protocol.md`)

## Why it is generated rather than written

The protocol is the programme's single authority. A hand-written HTML manuscript would be a **second
copy of the objective**, and two copies of an objective drift — which is the failure this repository
exists to prevent. So the Markdown is the source, and the build **stamps the anchor's `sha256` and
version into the page header**. If the anchor moves and the page is not rebuilt, the stamp is stale and
the discrepancy is visible rather than silent.

**Do not edit `viz/manuscript.html`.** Edit the Markdown and rebuild.

## Math: KaTeX, local, no network

A CDN script was tried first and returned **HTTP 200 with a zero-byte body** from this host. A page that
loads KaTeX from a CDN therefore renders correctly on the author's machine and **silently fails to
render everywhere else** — the worst possible failure for a manuscript. So the KaTeX distribution is
**copied into `viz/katex/`** (KaTeX 0.16.47: `katex.min.js`, `katex.min.css`, `auto-render.min.js`,
60 font files) and the page makes **no network request at all**.

Verified in a real browser, not by file inspection: **129 KaTeX nodes, 9 display blocks, 0 errors**,
computed font `KaTeX_Main`. The page prints its own render count into its header, so a reader can see
whether maths rendered rather than taking it on trust.

## Three defects the build hit, each of which would have produced a healthy-looking bad page

All three were found **by opening the page**, not by reading the code. That is the argument for checking
a render rather than a build log.

1. **Markdown ate the LaTeX.** `\,` `\;` `\cdot` are all Markdown escape sequences, so the parser
   consumed them before the renderer ever saw the expression — the page showed
   `\xrightarrow{;E(\cdot,,` with the symbols missing. **No renderer can recover from damage that
   happens upstream of it.** The fix lifts each expression into an HTML comment before parsing and
   restores it afterwards, so the TeX reaches KaTeX byte-identical to the source.

2. **`defer` + `onload` never fires.** The auto-render script was loaded with `defer` and its work
   attached to `onload`; that combination does not fire, so `renderMathInElement` was never called.
   The page rendered headings and tables perfectly and contained **zero** maths. The scripts are now
   loaded plainly, with an explicit initialiser.

3. **The delimiters were stripped on restore.** The restore step cut `$$…$$` down to its body, so KaTeX
   received bare TeX with nothing to match against and again reported **0 expressions** — from a build
   that had exited 0 and reported success. The build's own output was the misleading part.

**Each of these is a case where the toolchain reported success and the artefact was wrong.** The only
thing that caught them was rendering the page and asking what was actually in the DOM.

## A no-JavaScript fallback

The body carries the class `no-js`, removed by the first inline script. If scripting is unavailable, the
raw TeX stays visible rather than an empty gap — for a manuscript, readable source beats a blank box.
The initialiser also writes an explicit failure notice if KaTeX is missing, so the failure is stated
instead of assumed away.