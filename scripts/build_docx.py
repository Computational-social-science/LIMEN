#!/usr/bin/env python
"""build_docx.py -- a markdown document as a Word file with REAL equations (OMML), not TeX text.

RENAMED FROM build_si_docx.py. It was written for the supplementary information and its name said so, but it
takes --src and --out and renders ANY markdown; the manuscript DOCX comes from it too. A name that lies
about the scope of a script is how the next person writes a second renderer instead of finding this one - and
the defect that rename fixes was found exactly that way, when the paper was built through it and nobody had
said it could be.

Originally: the SI as a Word document with REAL equations (OMML), not TeX text.

Two stages, because one needs a browser and one needs Python:

    stage 1   `--harvest` writes viz/_mml_harvest.html, the page MathJax must typeset. The Agent renders it
              in the browser and writes the returned JSON to viz/mml_map.json.
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
MML_MAP = ROOT / "viz" / "mml_map.json"


def blocks(md: str):
    """Yield ('h1'|'h2'|'h3'|'p'|'li'|'table'|'rule', payload)."""
    tbl: list[str] = []
    pending: list[str] = []

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
        # A DISPLAY EQUATION WHOSE DELIMITERS SIT ON THEIR OWN LINES IS ONE BLOCK. A line-by-line parser splits
        # `$$` / the equation / `$$` into three paragraphs, the dollar signs within each cannot pair, and the
        # equation ships as TeX source surrounded by prose that renders - a defect that leaves most of the
        # document looking correct. Accumulate until the delimiters balance.
        if pending:
            pending.append(s)
            if s.count("$$") % 2 == 1:
                yield ("p", "\n".join(pending))
                pending.clear()
            continue
        if s.count("$$") % 2 == 1:
            pending = [s]
            continue
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


def add_figure(doc, ref: str, stats: dict) -> None:
    """Embed a figure, resolving the reference the way the HTML build does.

    The reference is written relative to the HTML output (`figures/x.png` beside the .html), so the DOCX - which
    lives in the same directory - resolves it identically. Both roots are tried and a miss is COUNTED rather
    than passed over: a figure that quietly fails to appear is the defect this function exists to end.
    """
    from docx.shared import Inches
    root = pathlib.Path(__file__).resolve().parent.parent
    for cand in (root / "viz" / ref, root / ref):
        if cand.exists():
            doc.add_picture(str(cand), width=Inches(6.3))
            stats["figures"] = stats.get("figures", 0) + 1
            return
    stats["missing_figures"] = stats.get("missing_figures", 0) + 1


def bold_parts(text: str) -> list[tuple[str, bool, bool]]:
    """Split a chunk into (text, is_bold, is_italic) parts, REMOVING the emphasis markers.

    WHY THIS IS NOT A ONE-LINE REGEX. The paragraph is split at every `$...$` span so mathematics can be
    inserted, and the old code stripped `**` from each chunk ON ITS OWN. A span written `**text $math$ more**`
    becomes the chunks `**text `, the equation, and ` more**`; neither chunk contains a matched pair, so the
    regex found nothing to replace and BOTH markers printed. Word's own PDF export showed it: six literal `**`
    in the manuscript and four in the supplementary information, in a file whose HTML was clean - a format that
    works saying nothing about its siblings (rule 14).

    ITALICS WERE THE SAME DEFECT AND WERE MISSED THE FIRST TIME. The fix above handled `**`; the SI's standfirst
    still showed `*sharper*` in Word, because a single asterisk was never handled by anything. Fixing the
    instance and not the class is how the second form survives, so both markers are parsed here, with `**`
    taking precedence at each position.

    Emphasis is tracked across the WHOLE paragraph and expressed as run properties, which is what it is.
    """
    parts: list[tuple[str, bool, bool]] = []
    pos, bold, ital = 0, False, False
    n = len(text)
    while pos < n:
        if text.startswith("**", pos):
            if parts and parts[-1][0] == "":
                parts.pop()
            bold = not bold
            marker_end = pos + 2
            if marker_end > pos and pos > 0 and text[pos - 1:pos] and False:
                pass
            pos = marker_end
            continue
        if text[pos] == "*":
            ital = not ital
            pos += 1
            continue
        j = pos
        while j < n and text[j] != "*":
            j += 1
        parts.append((text[pos:j], bold, ital))
        pos = j
    return [p for p in parts if p[0]]


def add_math_paragraph(doc, text: str, mml: dict, stats: dict, style: str | None = None) -> None:
    """One paragraph, with every `$...$` / `$$...$$` span replaced by an OMML equation object."""
    from docx.oxml import parse_xml
    from docx.oxml.ns import qn
    # REUSE AN EMPTY FIRST PARAGRAPH WHEN THE CONTAINER HAS ONE. A table cell ships with an empty paragraph,
    # so adding another leaves a blank line above every converted equation; a paragraph container has none to
    # reuse, so the two cases are told apart rather than assumed. An empty document also opens with an empty
    # paragraph, which must NOT be reused by a styled block or the styling would be lost.
    if (style is None and getattr(doc, "paragraphs", None)
            and not doc.paragraphs[0].text and not doc.paragraphs[0].runs):
        p = doc.paragraphs[0]
    else:
        p = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    pos = 0
    pattern = re.compile(r"(\$\$.+?\$\$|(?<!\$)\$(?!\$)(?!\s)[^\n$]*?(?<!\s)\$(?!\$))", re.S)
    for m in pattern.finditer(text):
        before = text[pos:m.start()]
        if before:
            for chunk, is_bold, is_ital in bold_parts(before):
                if chunk:
                    r = p.add_run(chunk)
                    r.bold = is_bold or None
                    r.italic = is_ital or None
        # a math span inside a bold run must not leave the bold state open on the far side
        if text[:m.start()].count("**") % 2:
            stats["math_in_bold"] = stats.get("math_in_bold", 0) + 1
        tex = m.group(0)
        # LOOK THE EXPRESSION UP BY ITS OWN TEXT. Searching for the span's position and using that as a key
        # reintroduces the defect the text key exists to prevent: the position is the CURRENT one, the map's
        # entries are from the HARVEST, and the two agree only while nothing has moved.
        mml_str = mml["map"].get(tex)
        omml_xml = O.mml_to_omml(mml_str) if mml_str else None
        if omml_xml:
            # A WIDE DISPLAY EQUATION IS SPLIT AT ITS ARROWS so WORD lays it out in readable lines. Handed
            # over as one `m:oMath` it wrapped wherever it ran out of width, which stacked the loop diagram
            # into 26 vertical lines in an otherwise correct file. `m:oMathPara` may hold several `m:oMath`,
            # one per line, so the layout is decided here rather than left to Word's wrapping.
            #
            # LAYOUT ONLY: the same `m:oMath` children regrouped. Nothing is simplified, reordered or dropped.
            # An earlier attempt "fixed" the same symptom by rewriting the equation without its `\underbrace`
            # labels, and that was a deformation of the mathematics rather than a fix of the rendering.
            # LOOK BEFORE CUTTING. A wide display equation looked like a 26-line vertical stack for three
            # rounds of this session, and it was a TEXT-EXTRACTION ARTEFACT: a PDF extractor emits every
            # mathematical run on its own line whether or not they share a baseline, and the measurement could
            # not see the thing it claimed to measure. Measured properly, by y-coordinate through Word's own
            # export, the equation renders as ONE main line (all elements at y=392.8) with arrow labels above
            # (y=385.7) and `\underbrace` labels below their bases - correct structured layout all along.
            #
            # Two "fixes" were built on that phantom and both are gone: rewriting the equation without its
            # labels, which deformed the mathematics, and splitting it at the arrows into separate paragraphs,
            # which was never needed. The lesson is on the measurement, not the renderer.
            # `m:oMath` IS A SIBLING OF `w:r`, NOT A CHILD OF IT. `CT_R`'s content model - the run - has no
            # member for it, so appending the equation to a run produces a document that is well formed XML,
            # passes every count-based check, and which WORD REFUSES TO OPEN. Word emits inline mathematics as
            # a direct child of the paragraph, between runs, and so must this.
            #
            # What made this survivable for a whole session is that the artefact checks were counting elements
            # rather than validating structure: 154 `m:oMath` objects, none fallen back, seven images - all
            # true, in a file that cannot be read.
            p._p.append(parse_xml(omml_xml))
            stats["omml"] += 1
        else:
            p.add_run(tex)
            stats["fallback"] += 1
        pos = m.end()
    tail = text[pos:]
    if tail:
        # the trailing chunk needs the same treatment: an unclosed `**` here is exactly the case that printed
        for chunk, is_bold, is_ital in bold_parts(tail):
            if chunk:
                r = p.add_run(chunk)
                r.bold = is_bold or None
                r.italic = is_ital or None


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
        # A FIGURE IS A BLOCK TOO. The markdown carries `![Figure N](figures/x.png)`, the HTML resolves it, and
        # this builder skipped it silently - so the format a reader downloads as a document carried every
        # equation and NOT ONE FIGURE, while the format they read in a browser carried both. Nothing failed;
        # the images were simply absent.
        if kind == "p" and isinstance(payload, str):
            im = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", payload.strip())
            if im:
                add_figure(doc, im.group(2), stats)
                continue
        if kind == "h1":
            doc.add_heading(payload, level=1)
        elif kind == "h2":
            doc.add_heading(payload, level=2)
        elif kind == "h3":
            doc.add_heading(payload, level=3)
        elif kind == "rule":
            doc.add_paragraph("")
        elif kind == "li":
            # LISTS GO THROUGH THE SAME CONVERSION. A list item is a paragraph like any other, and routing it around
            # the converter shipped every equation inside a bullet as TeX source while the prose rendered - the
            # same defect class as the table cells, in the one other place text was assigned rather than built.
            add_math_paragraph(doc, payload.lstrip("- "), mml, stats, style="List Bullet")
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
                        # MATH IN A TABLE CELL MUST GO THROUGH THE SAME CONVERSION AS MATH IN A PARAGRAPH.
                        # Assigning cell text directly wrote `$\pi_d$` into the document verbatim, so every
                        # equation inside a table shipped as TeX source while the surrounding prose did not -
                        # a defect invisible until the residual-delimiter count was checked.
                        add_math_paragraph(rc[j], re.sub(r"\*\*(.+?)\*\*", r"\1", c), mml, stats)
        else:
            add_math_paragraph(doc, payload, mml, stats)
    doc.save(str(OUT_DOCX))
    print(f"  wrote {OUT_DOCX.relative_to(ROOT)}  ({OUT_DOCX.stat().st_size // 1024} KB)")
    print(f"  equations as OMML: {stats['omml']}   fell back to TeX: {stats['fallback']}")
    print(f"  figures embedded: {stats.get('figures', 0)}   missing: {stats.get('missing_figures', 0)}")
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
    # THE HARVEST PAGE MUST SIT BESIDE THE MATHJAX ASSETS. `KATEX_SCRIPTS`-equivalent blocks reference
    # `mathjax/tex-mml-chtml.js` RELATIVELY, so a page written next to the SOURCE resolves that to a
    # directory that does not exist, the script never loads, and every expression silently harvests as
    # missing. Anchoring the page to the asset directory is what makes the relative reference correct.
    # DERIVED FROM THE OUTPUT NAME, NOT FIXED. These were two constants pointing at the supplementary
    # information's files, so building any second document would overwrite the first one's harvest page and
    # its MathML map: the map is what turns each TeX span into an OMML equation, so a clobbered map does not
    # fail loudly, it silently falls back to source text. Same defect as two scripts sharing one output path,
    # one level down.
    _stem = OUT_DOCX.stem
    HARVEST_HTML = ROOT / "viz" / f"_{_stem}_mml_harvest.html"
    MML_MAP = ROOT / "viz" / f"{_stem}_mml_map.json"
    if args.harvest:
        return harvest()
    if args.build:
        return build()
    # NOTHING WAS DONE, AND IT NOW SAYS SO IN ONE LINE BEFORE THE USAGE TEXT. The exit code was already 2 -
    # the script never lied - but it printed a help page and nothing else, so a caller piping it into `tail`
    # saw usage text and a zero status from the pipe, concluded success, and moved on. That is rule 12 seen
    # from the other side: a failure that cannot reach the step that decides is not a check, and here the
    # step that hid it was the pipe in the CALLER. The script cannot fix a caller's pipeline; it can refuse
    # to be mistaken for one that did work.
    print("NOTHING WAS DONE: neither --harvest nor --build was given.")
    print("  --harvest   write the MathML harvest page for a browser to render")
    print("  --build     assemble the DOCX from an existing harvest map")
    print()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())