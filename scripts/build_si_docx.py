#!/usr/bin/env python
"""build_si_docx.py -- the SI as a Word document with REAL equations (OMML), not TeX text.

Two stages, because one needs a browser and one needs Python:

    stage 1   `--harvest` writes viz/_mml_harvest.html, the page MathJax must typeset. The Agent renders it
              in the browser and writes the returned JSON to viz/_mml_map.json.
    stage 2   `--build` consumes that map and writes the DOCX, converting each expression through Office's
              own MML2OMML.XSL.

WHY THE MAP IS A FILE
    The conversion is auditable: every expression in the document has an entry, or the build says which one it
    could not convert and falls back to TeX FOR THAT EXPRESSION ONLY, with the count of fallbacks printed. A
    DOCX that silently contains TeX where the HTML contains mathematics is the kind of difference a reader
    discovers at the worst moment.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import omml as O
import si_render as SR

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "SUPPLEMENTARY_INFORMATION.md"
OUT_DOCX = ROOT / "viz" / "supplementary_information.docx"
HARVEST_HTML = ROOT / "viz" / "_mml_harvest.html"
MML_MAP = ROOT / "viz" / "_mml_map.json"


def blocks(md: str):
    """Yield ('h1'|'h2'|'h3'|'p'|'li'|'table'|'rule', payload)."""
    tbl: list[str] = []

    def flush():
        if tbl:
            rows = [r for r in tbl if not re.match(r"^\|[\s:|-]+\|$", r)]
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            yield_body = ("table", cells)
            tbl.clear()
            return yield_body
        return None

    for raw in md.splitlines():
        s = raw.rstrip()
        if s.startswith("|"):
            tbl.append(s)
            continue
        b = flush()
        if b:
            yield b
        if not s:
            continue
        if s.startswith("### "):
            yield ("h3", s[4:])
        elif s.startswith("## "):
            yield ("h2", s[3:])
        elif s.startswith("# "):
            yield ("h1", s[2:])
        elif s.strip() == "---":
            yield ("rule", None)
        elif s.startswith("- "):
            yield ("li", s[2:])
        else:
            yield ("p", s)
    b = flush()
    if b:
        yield b


def harvest() -> int:
    md = SRC.read_text(encoding="utf-8")
    spans = O.extract_spans(md)
    HARVEST_HTML.write_text(O.harvest_page(spans, SR.MATHJAX_SCRIPTS), encoding="utf-8", newline="\n")
    print(f"  harvest page: {HARVEST_HTML.relative_to(ROOT)}  ({len(spans)} expression(s) to typeset)")
    print(f"  render it, then evaluate scripts/omml.py:harvest_js() and save the JSON to "
          f"{MML_MAP.relative_to(ROOT)}")
    return 0


def add_math_paragraph(doc, text: str, mml: dict[str, str], stats: dict) -> None:
    """One paragraph, with every `$...$` / `$$...$$` span replaced by an OMML equation object."""
    from docx.oxml import parse_xml
    from docx.oxml.ns import qn
    p = doc.add_paragraph()
    pos = 0
    pattern = re.compile(r"(\$\$.+?\$\$|(?<!\$)\$(?!\$)(?!\s)[^\n$]*?(?<!\s)\$(?!\$))", re.S)
    for m in pattern.finditer(text):
        before = text[pos:m.start()]
        if before:
            p.add_run(re.sub(r"\*\*(.+?)\*\*", r"\1", before))
        tex = m.group(0)
        key = None
        for i, s in enumerate(mml["order"]):
            if s == tex:
                key = str(i)
                break
        mml_str = mml["map"].get(key) if key is not None else None
        omml_xml = O.mml_to_omml(mml_str) if mml_str else None
        if omml_xml:
            run = p.add_run()
            run._r.append(parse_xml(omml_xml))
            stats["omml"] += 1
        else:
            p.add_run(tex)
            stats["fallback"] += 1
        pos = m.end()
    tail = text[pos:]
    if tail:
        p.add_run(re.sub(r"\*\*(.+?)\*\*", r"\1", tail))
    if not text.strip():
        doc.add_paragraph("")


def build() -> int:
    try:
        import docx
        from docx.shared import Pt
    except ImportError:
        print("  [FAIL] python-docx not installed")
        return 1
    md = SRC.read_text(encoding="utf-8")
    spans = O.extract_spans(md)
    if MML_MAP.exists():
        raw = json.loads(MML_MAP.read_text(encoding="utf-8"))
        mml = {"map": raw.get("map", {}), "order": spans}
        if len(mml["map"]) < len(spans):
            print(f"  [NOTE] the MathML map holds {len(mml['map'])} of {len(spans)} expressions; the rest fall "
                  f"back to TeX and are counted below")
    else:
        mml = {"map": {}, "order": spans}
        print("  [NOTE] no MathML map found; every equation falls back to TeX. Run --harvest first for OMML.")

    doc = docx.Document()
    doc.styles["Normal"].font.name = "Georgia"
    doc.styles["Normal"].font.size = Pt(10.5)
    stats = {"omml": 0, "fallback": 0}
    for kind, payload in blocks(md):
        if kind == "h1":
            doc.add_heading(payload, level=1)
        elif kind == "h2":
            doc.add_heading(payload, level=2)
        elif kind == "h3":
            doc.add_heading(payload, level=3)
        elif kind == "rule":
            doc.add_paragraph("")
        elif kind == "li":
            doc.add_paragraph(payload.lstrip("- "), style="List Bullet")
        elif kind == "table":
            cells = payload
            if cells:
                t = doc.add_table(rows=0, cols=len(cells[0]))
                try:
                    t.style = "Light Grid Accent 1"
                except KeyError:
                    pass
                for row in cells:
                    rc = t.add_row().cells
                    for j, c in enumerate(row[:len(cells[0])]):
                        rc[j].text = re.sub(r"\*\*(.+?)\*\*", r"\1", c)
        else:
            add_math_paragraph(doc, payload, mml, stats)
    doc.save(str(OUT_DOCX))
    print(f"  wrote {OUT_DOCX.relative_to(ROOT)}  ({OUT_DOCX.stat().st_size // 1024} KB)")
    print(f"  equations as OMML: {stats['omml']}   fell back to TeX: {stats['fallback']}")
    if stats["fallback"] and not stats["omml"]:
        print("  [WARN] this DOCX carries NO native equations; the HTML and PDF do.")
    return 0


def main() -> int:
    # The `global` statement must precede the FIRST use of these names in the function: `--src`'s default
    # reads SRC, so declaring it later is a syntax error, not a style issue.
    global SRC, OUT_DOCX, HARVEST_HTML, MML_MAP
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--src", default=str(SRC), help="markdown source; defaults to the SI")
    ap.add_argument("--out", default=str(OUT_DOCX))
    ap.add_argument("--harvest", action="store_true")
    ap.add_argument("--build", action="store_true")
    args = ap.parse_args()
    # resolve(): a relative --src would leave HARVEST_HTML outside ROOT and break relative_to()
    SRC = pathlib.Path(args.src).resolve(); OUT_DOCX = pathlib.Path(args.out).resolve()
    HARVEST_HTML = SRC.parent / "_mml_harvest.html"; MML_MAP = SRC.parent / "_mml_map.json"
    if args.harvest:
        return harvest()
    if args.build:
        return build()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())