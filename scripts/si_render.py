#!/usr/bin/env python
"""si_render.py -- render the Supplementary Information with mathematics intact, to HTML and PDF.

THE DEFECT THIS REPLACES
    The first version of the SI renderer ran its inline transforms (bold, italic, code) directly over the
    text, and Markdown knows nothing about `$`. So `$s_{\\mathrm{en}}$` had its two underscores paired into an
    `<em>` spanning the mathematics, `$\\lambda_\\mathrm{lo}$` lost its subscript, and the document shipped
    with mangled formulas. The manuscript builder had documented this exact failure and solved it; this module
    applies the same solution rather than rediscovering it.

THE SOLUTION
    MATHEMATICS IS EXTRACTED BEFORE ANY INLINE TRANSFORM RUNS AND RESTORED AFTER. Every display span
    (`$$...$$`) and inline span (`$...$`) is replaced by a private-use sentinel that no transform can match,
    the transforms run on what remains, and the spans are put back verbatim. A private-use codepoint is used
    rather than an ASCII marker so that a stray occurrence in the source cannot be confused with a sentinel.

RENDERING
    KaTeX, copied into the output directory at build time so the page needs no network, with the browser
    auto-render extension applying to the delimiters that survived. A private-use sentinel survives into the
    final HTML and is what KaTeX finally sees, so the delimiters must be restored BEFORE the page is written -
    which they are.
"""

from __future__ import annotations

import pathlib
import re
import shutil

SENT_D, SENT_I = "\ue000", "\ue001"          # private use: display, inline
ROOT = pathlib.Path(__file__).resolve().parent.parent


MATHJAX_FILE = "tex-mml-chtml.js"          # the self-contained combined component


def find_mathjax() -> pathlib.Path:
    """Locate the MathJax combined component without a network fetch and without an absolute literal.

    `tex-mml-chtml.js` is a webpack bundle carrying the TeX input, the MathML input, the CHTML output and the
    fonts, so a single copied file makes the rendered pages work offline.
    """
    import os
    cands = []
    if os.environ.get("MATHJAX_ES5"):
        cands.append(pathlib.Path(os.environ["MATHJAX_ES5"]))
    cands += [ROOT / "node_modules/mathjax/es5",
              ROOT / "viz/mathjax",
              ROOT / "node_modules/mathjax-full/es5"]
    for hh in (os.environ.get("LOCALAPPDATA"), os.environ.get("APPDATA")):
        if hh:
            cands.append(pathlib.Path(hh) / "hermes-agent/node_modules/mathjax/es5")
            cands.append(pathlib.Path(hh) / "hermes/node/node_modules/mathjax/es5")
    for c in cands:
        if (c / MATHJAX_FILE).is_file():
            return c
    raise SystemExit("MathJax not found. Set $MATHJAX_ES5, or run `npm install mathjax@3` in the "
                     "repository root.")


def copy_mathjax(dest: pathlib.Path) -> str:
    src = find_mathjax()
    dest.mkdir(parents=True, exist_ok=True)

    def place(source: pathlib.Path, name: str) -> None:
        """Copy into place, but be IDEMPOTENT and tolerant of a file already in use.

        The destination usually already holds the assets from an earlier build, and on Windows a reader's
        browser or a headless print profile can hold them open. Re-copying identical bytes is pointless, and
        failing the whole build because a browser has the stylesheet open would be an operational error
        masquerading as a rendering one. If the destination exists and is non-empty, it is used as-is.
        """
        target = dest / name
        if target.is_file() and target.stat().st_size > 0:
            return
        try:
            shutil.copy2(source, target)
        except PermissionError:
            if not target.is_file():
                raise

    place(src / MATHJAX_FILE, MATHJAX_FILE)
    ver = "local"
    m = re.search(r"MathJax(?:-v)?[ _]?(?:version[^0-9]{0,4})?([0-9]+\.[0-9]+\.[0-9]+)",
                  (dest / MATHJAX_FILE).read_text(encoding="utf-8", errors="ignore")[:200000])
    if m:
        ver = m.group(1)
    return ver


def protect_math(md: str) -> tuple[str, list[str]]:
    """Replace every math span with a sentinel, so no inline transform can reach inside one.

    Display spans are taken first: a `$$...$$` contains `$...$` if the inline pattern runs first, and the
    result is a document where display equations are chopped into fragments.
    """
    store: list[str] = []

    def stash(text: str) -> str:
        store.append(text)
        return SENT_D + str(len(store) - 1) + SENT_D

    md = re.sub(r"\$\$.+?\$\$", lambda m: stash(m.group(0)), md, flags=re.S)

    def stash_i(text: str) -> str:
        store.append(text)
        return SENT_I + str(len(store) - 1) + SENT_I

    # Inline: a `$` not preceded or followed by `$`, and no newline inside (a stray currency `$` in prose
    # must not swallow the rest of the paragraph).
    # The opening `$` may not be followed by a space and the closing `$` may not be preceded by one, which is
    # the standard prose-safe heuristic: without it, "the cost was $5 and then $7 more" is read as one inline
    # span. A real equation does not open with a space, so the tightening costs nothing.
    md = re.sub(r"(?<!\$)\$(?!\$)(?!\s)([^\n$]*?)(?<!\s)\$(?!\$)", lambda m: stash_i(m.group(0)), md)
    return md, store


def restore_math(html: str, store: list[str]) -> str:
    def put_d(m):
        return store[int(m.group(1))]
    def put_i(m):
        return store[int(m.group(1))]
    html = re.sub(SENT_D + r"(\d+)" + SENT_D, put_d, html)
    html = re.sub(SENT_I + r"(\d+)" + SENT_I, put_i, html)
    return html


def md_to_html_body(md: str) -> str:
    """Render the SI's Markdown subset, with mathematics protected across every transform."""
    md, store = protect_math(md)
    out: list[str] = []
    tbl: list[str] = []

    def flush_table() -> None:
        if not tbl:
            return
        rows = [r for r in tbl if not re.match(r"^\|[\s:|-]+\|$", r)]
        cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
        head, body = cells[0], cells[1:]
        h = ["<table><thead><tr>" + "".join(f"<th>{c}</th>" for c in head) + "</tr></thead><tbody>"]
        h += ["<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in body]
        h.append("</tbody></table>")
        out.append("".join(h))
        tbl.clear()

    for raw in md.splitlines():
        s = raw.rstrip()
        if s.startswith("|"):
            tbl.append(s)
            continue
        flush_table()
        if not s:
            continue
        if s.startswith("### "):
            out.append(f"<h3>{s[4:]}</h3>")
        elif s.startswith("## "):
            out.append(f"<h2>{s[3:]}</h2>")
        elif s.startswith("# "):
            out.append(f"<h1>{s[2:]}</h1>")
        elif s.strip() == "---":
            out.append("<hr>")
        elif s.startswith("- "):
            out.append(f"<p class=\"li\">{s[2:]}</p>")
        elif re.match(r"^\d+\.\s", s):
            out.append(f"<p class=\"li\">{s}</p>")
        else:
            out.append(f"<p>{s}</p>")
    flush_table()
    html = "\n".join(out)
    # Inline transforms, applied only to non-math text because the math is sentinelled.
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"(?<![\w*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", html)
    html = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", html)
    return restore_math(html, store)


MATHJAX_SCRIPTS = """<script>
window.MathJax = {
  tex: {
    inlineMath: [['$', '$']],
    displayMath: [['$$', '$$']],
    processEscapes: true,
    processEnvironments: true,
    packages: {'[+]': ['ams', 'boldsymbol', 'textmacros', 'noerrors', 'noundefined']}
  },
  options: {
    skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
    renderActions: {addMenu: []}
  },
  chtml: {scale: 1.0, displayAlign: 'center'},
  startup: {
    pageReady: function () {
      return MathJax.startup.defaultPageReady().then(function () {
        var n = document.querySelectorAll('mjx-container').length;
        var d = document.querySelectorAll('mjx-container[display="true"]').length;
        var badge = document.createElement('p');
        badge.className = 'mathcount';
        badge.textContent = 'math rendered: ' + n + ' expression(s), ' + d + ' display';
        document.body.appendChild(badge);
        if (n === 0) {
          var warn = document.createElement('p');
          warn.className = 'mathfail';
          warn.textContent = 'No mathematics was rendered. The TeX source below is still readable.';
          document.body.insertBefore(warn, document.body.firstChild);
        }
      });
    }
  }
};
</script>
<script src="mathjax/tex-mml-chtml.js" id="MathJax-script"></script>
"""