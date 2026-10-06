#!/usr/bin/env python
"""omml.py -- LaTeX to OMML, via MathJax's own MathML and Office's own XSLT.

WHY THIS ROUTE
    python-docx cannot emit OMML and pandoc is absent on this host, so a DOCX built naively carries each
    equation as raw TeX. Both halves of a real fix happen to be present:

      1. MathJax, already installed for the HTML, emits an ASSISTIVE MathML copy of every expression it
         typesets - a complete <math> element, hidden for accessibility, sitting in the rendered page.
      2. Office ships `MML2OMML.XSL`, the vendor's own MathML-to-OMML transform.

    So the pipeline is: TeX -> (MathJax in a browser) -> MathML -> (MML2OMML.XSL via lxml) -> OMML, and the
    OMML is inserted into the DOCX as raw XML. Nothing is re-implemented, and the transform is the same one
    Word itself uses, so what the document contains is what Word would have produced.

WHY IT IS TWO STAGES
    The first half needs a browser and the second needs Python. The harvest stage renders every expression of
    a document on ONE page and returns a TeX-to-MathML map as JSON; the build stage consumes that map. The map
    is a checked artefact: if an expression is missing from it, the DOCX falls back to the TeX text AND the
    build reports the miss, rather than silently degrading.
"""

from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

XSLT_CANDIDATES = (
    r"C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL",
    r"C:\Program Files (x86)\Microsoft Office\root\Office16\MML2OMML.XSL",
    r"C:\Program Files\Microsoft Office\Office16\MML2OMML.XSL",
)


def find_xslt() -> pathlib.Path:
    import os
    for p in XSLT_CANDIDATES:
        if pathlib.Path(p).is_file():
            return pathlib.Path(p)
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if not base:
            continue
        for p in pathlib.Path(base).glob("Microsoft Office/**/MML2OMML.XSL"):
            return p
    raise SystemExit("MML2OMML.XSL not found. It ships with Microsoft Office.")


_engine = None


def mml_to_omml(mml: str) -> str | None:
    """MathML -> OMML. Returns None (never raises) so a caller can fall back and report."""
    global _engine
    from lxml import etree
    if _engine is None:
        _engine = etree.XSLT(etree.parse(str(find_xslt())))
    try:
        src = etree.fromstring(mml.encode("utf-8"))
        out = str(_engine(src))
    except Exception:
        return None
    # Strip the XML declaration: the fragment is embedded inside a document part that already has one.
    out = out.split("?>", 1)[-1].strip()
    if "oMath" not in out:
        return None
    return out


def extract_spans(md: str) -> list[str]:
    """Every TeX span in a Markdown document, display first, deduplicated, order-preserving."""
    spans: list[str] = []
    for m in re.finditer(r"\$\$.+?\$\$", md, re.S):
        spans.append(m.group(0))
    for m in re.finditer(r"(?<!\$)\$(?!\$)(?!\s)([^\n$]*?)(?<!\s)\$(?!\$)", md):
        spans.append(m.group(0))
    seen, out = set(), []
    for s in spans:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def harvest_page(spans: list[str], scripts_block: str) -> str:
    """The page the browser renders so MathJax typesets every span at once.

    Each span is placed in its own element with a data index, and display spans are given `$$` delimiters so
    MathJax sets them as display - which is what makes the extracted assistive MathML carry display semantics.
    """
    import html as _html
    body = "\n".join(
        f'<div class="mm" data-i="{i}">{_html.escape(s)}</div>' for i, s in enumerate(spans)
    )
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>mml harvest</title>"
        "<style>.mm{margin:6px 0}</style>" + scripts_block + "</head><body>" + body + "</body></html>"
    )


def harvest_js() -> str:
    """The extraction expression the browser evaluates after MathJax finishes."""
    return """(() => {
  const out = {};
  document.querySelectorAll('.mm').forEach(d => {
    const c = d.querySelector('mjx-container');
    const m = c ? c.querySelector('mjx-assistive-mml math') : null;
    out[d.getAttribute('data-i')] = m ? m.outerHTML : null;
  });
  return JSON.stringify({count: Object.keys(out).length,
                         missing: Object.values(out).filter(v => !v).length, map: out});
})()"""


def load_map(path: pathlib.Path) -> dict[str, str]:
    d = json.loads(path.read_text(encoding="utf-8"))
    return d.get("map", d)
