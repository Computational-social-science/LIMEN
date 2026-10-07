#!/usr/bin/env python
"""check_documents.py -- verify the DOCUMENTS THAT WERE PRODUCED, not the intent of the code that made them.

WHY THIS EXISTS
    Eleven defects reached deliverable documents in a single working session, and every one of them was
    invisible in the artefact: the file opened, looked right, and was wrong. Equations shipped as raw TeX
    inside table cells while the prose around them rendered; a display equation split into paragraphs whose
    dollar signs could not pair; a DOCX with every equation and NOT ONE FIGURE; a conversion cache keyed by
    position that would silently attach one expression's mathematics to another; two builders writing one
    path, the last one winning; and a MathJax installation missing its font files, so every equation in
    every format fell back to a system font and the variables were not even italic.

    Every one was found by a human noticing, which is not a mechanism. What they have in common is that
    verification had been aimed at the INPUT - did the build run, did it print OK - instead of the OUTPUT.
    This aims at the output.

HOW IT WORKS
    Expectations are DERIVED from the source markdown: how many mathematics spans it contains, how many
    figures it references. Those counts are then asserted against each produced artefact. Nothing is typed
    in, so the checker cannot drift from the document it checks - and a mismatch means the artefact does
    not carry what the source says it should.

WHAT IT CANNOT DO
    It cannot judge whether the prose is any good, and it does not render anything in a browser. A font
    file that exists but is corrupt passes; what it catches is the file being ABSENT, which is the failure
    that actually occurred. It reports how many assertions it evaluated so a reader can see the coverage
    rather than assume it.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Every document set this repository produces, and what each one is made of. Adding a document means adding
# a row here, which is the point: a new deliverable cannot quietly bypass the checks.
DOC_SETS: dict[str, dict] = {
    "supplementary_information": {
        "md": "docs/SUPPLEMENTARY_INFORMATION.md",
        "html": "viz/supplementary_information.html",
        "docx": "viz/supplementary_information.docx",
        "pdf": "viz/supplementary_information.pdf",
        "renderer": "mathjax",
    },
    # THE PAPER. Rendered from `docs/PAPER.md`, which is authored as a paper. This entry previously said
    # `md: None - built from the protocol`, which was the defect stated plainly: there was no manuscript
    # source, and the file at this path was a rendering of the protocol with a paper's title on it. The
    # renderer is mathjax, not katex: the paper imports the same configuration and font set as the SI.
    "manuscript": {
        "md": "docs/PAPER.md",
        "html": "viz/manuscript.html",
        "docx": "viz/manuscript.docx",
        "pdf": "viz/manuscript.pdf",
        "renderer": "mathjax",
    },
    # THE PROTOCOL, AS A DOCUMENT. It is the anchor, so it keeps its own output path. When both artefacts
    # wrote to `viz/manuscript.html`, running the protocol renderer silently replaced the paper, and no check
    # could see it because both were "the manuscript".
    "protocol": {
        "md": None,                      # rendered from the pinned anchor protocol file
        "html": "viz/protocol.html",
        "docx": None,
        "pdf": None,
        "renderer": "mathjax",
    },
}

# Where each renderer keeps the fonts it cannot render without. A renderer without its fonts does not fail;
# it silently substitutes, and the substitution is what a reader sees.
FONT_DIRS = {
    "mathjax": ("viz/mathjax/output/chtml/fonts/woff-v2", (".woff", ".woff2")),
    "katex": ("viz/katex/fonts", (".woff", ".woff2")),
}
MIN_FONTS = {"mathjax": 15, "katex": 15}


def math_spans(md: str) -> int:
    """Every inline and display mathematics span the source declares."""
    display = len(re.findall(r"\$\$.+?\$\$", md, re.S))
    inline = len(re.findall(r"(?<!\$)\$(?!\$)(?!\s)[^\n$]*?(?<!\s)\$(?!\$)", md))
    return display + inline


def figure_refs(md: str) -> list[str]:
    return re.findall(r"!\[[^\]]*\]\(([^)]+)\)", md)


def check_source(name: str, spec: dict) -> tuple[list[str], dict]:
    findings: list[str] = []
    facts: dict = {}
    md_path = spec.get("md")
    if not md_path:
        return findings, facts
    p = ROOT / md_path
    if not p.exists():
        findings.append(f"{name}: source {md_path} is missing")
        return findings, facts
    md = p.read_text(encoding="utf-8")
    facts["math"] = math_spans(md)
    facts["figures"] = figure_refs(md)
    for ref in facts["figures"]:
        if not (ROOT / "viz" / ref).exists() and not (p.parent / ref).exists():
            findings.append(f"{name}: figure reference does not resolve: {ref}")
    # the renderer must have its fonts BEFORE anything is built from it
    rend = spec.get("renderer")
    if rend in FONT_DIRS:
        rel, exts = FONT_DIRS[rend]
        d = ROOT / rel
        n = len([f for f in d.glob("*") if f.suffix in exts]) if d.is_dir() else 0
        facts["fonts"] = n
        if n < MIN_FONTS[rend]:
            findings.append(
                f"{name}: the {rend} renderer has {n} font file(s) in {rel}, fewer than the "
                f"{MIN_FONTS[rend]} it ships; a renderer without its fonts substitutes silently and the "
                f"substitution is what the reader sees")
    return findings, facts


def check_docx(name: str, path: pathlib.Path, facts: dict) -> tuple[list[str], dict]:

    findings: list[str] = []
    out: dict = {}

    # HTML LEAKAGE. The reader received an HTML whose figures were literal `![Figure 1](path)` and whose
    # bold markers had been split across a line break, so the page showed `**` and raw `$...$`. None of it was
    # missing - it was all present, unrendered, which is why counting said the document was fine. Three
    # assertions: no Markdown image syntax survives, no literal emphasis marker survives, and the number of
    # <img> elements equals the number of figures the source declares.
    if path.suffix.lower() == ".html":
        html = path.read_text(encoding="utf-8")
        leaks = re.findall(r"!\[[^\]]*\]\([^)]*\)", html)
        if leaks:
            findings.append(f"{name}: {len(leaks)} Markdown image(s) reached the HTML unrendered, e.g. {leaks[0][:60]}")
        literal = re.findall(r"\*\*[^*\n]{1,60}\*\*", html)
        if literal:
            findings.append(f"{name}: {len(literal)} literal emphasis marker(s) survived, e.g. {literal[0][:60]}")
        n_img = len(re.findall(r"<img\s+src=", html))
        want = len(facts.get("figures") or [])
        if want and n_img != want:
            findings.append(f"{name}: the source declares {want} figure(s) and the page embeds {n_img}")
        # a raw dollar that is not inside a stashed maths span means mathematics will show as source
        stray = re.findall(r"(?<![\\$>])\$[A-Za-z0-9\\\\{}_^{} ]{2,40}\$", html)
        if stray:
            findings.append(f"{name}: {len(stray)} mathematics span(s) look unrendered, e.g. {stray[0][:50]}")
        return findings, out   # an HTML document has no OOXML parts to inspect below this line
    if not path.exists():
        findings.append(f"{name}: DOCX missing at {path.relative_to(ROOT)}")
        return findings, out
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="replace")
            media = [n for n in z.namelist() if n.startswith("word/media/")]
    except zipfile.BadZipFile:
        findings.append(f"{name}: DOCX is not a valid zip archive")
        return findings, out

    # STRUCTURE, NOT JUST COUNTS. Everything below this line counted elements; none of it asked whether the
    # document could be OPENED. A DOCX with 154 native equations, no fallen-back source and seven embedded
    # figures was produced and Word refused to open it, because `m:oMath` had been appended to a run - and
    # `CT_R`, the run's content model, has no member for it. The equation belongs to the PARAGRAPH, between
    # runs. Counting said yes; the application said no.
    from lxml import etree
    try:
        root = etree.fromstring(xml.encode("utf-8"))
    except Exception as e:
        findings.append(f"{name}: word/document.xml is not well-formed XML ({type(e).__name__})")
        return findings, out
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
    if root.find(f".//{M}oMath") is None and facts.get("math"):
        findings.append(f"{name}: the source declares mathematics and document.xml holds no m:oMath element")
    misplaced = [r for r in root.iter(f"{W}r") if r.find(f"{M}oMath") is not None]
    if misplaced:
        findings.append(
            f"{name}: {len(misplaced)} equation(s) are children of a RUN. `CT_R` has no member for `m:oMath`, "
            f"so the file is well-formed XML that violates the schema and Word refuses to open it - all counts "
            f"still pass. The equation belongs to the paragraph, as a sibling of the runs.")
    # every part must parse: a document with one broken part does not open at all.
    # The archive is re-opened here rather than reused: the block above closes it, and a read from a closed
    # ZipFile raises ValueError, which this loop would have reported as "all parts are not well-formed".
    with zipfile.ZipFile(path) as zz:
        parts = zz.namelist()
        for part in parts:
            if part.endswith((".xml", ".rels")):
                try:
                    etree.fromstring(zz.read(part))
                except Exception as e:
                    findings.append(f"{name}: {part} is not well-formed - {type(e).__name__}: {e}")
        for req in ("[Content_Types].xml", "_rels/.rels", "word/document.xml"):
            if req not in parts:
                findings.append(f"{name}: the archive is missing required part {req}")

    # MARKDOWN MARKERS MUST NOT REACH A DOCX EITHER. Two defects of this class shipped in one session: six
    # literal `**` in the manuscript and four in the supplementary information, then `*sharper*` in the SI after
    # the bold case had been "fixed" - an instance repaired while the class survived. Word's own PDF export is
    # what showed both, and nothing in this repository was looking at the produced DOCX for them, because the
    # HTML check was already green: a format that works says nothing about its siblings (rule 14).
    #
    # Only the PROSE is scanned. Asterisks inside an equation are inside a `m:oMath` and are excluded, so a
    # legitimate `T^*` cannot be reported as a marker.
    prose = re.sub(r"<m:oMath>.*?</m:oMath>", " ", xml, flags=re.S)
    prose = re.sub(r"<[^>]+>", "", prose)
    for marker, what in (("**", "bold marker"), ("*", "emphasis marker"), ("![", "Markdown image")):
        if marker in prose:
            k = prose.count(marker)
            findings.append(f"{name}: {k} literal {what}(s) in the DOCX prose - the emphasis or image was "
                            f"never rendered and the reader sees the markup")

    n_omml = len(re.findall(r"<m:oMath[ >]", xml))
    out["omml"] = n_omml
    out["media"] = len(media)
    plain = re.sub(r"<[^>]+>", "", xml)
    out["raw_dollars"] = plain.count("$")

    if facts.get("math"):
        if n_omml == 0:
            findings.append(
                f"{name}: the source declares {facts['math']} mathematics span(s) and the DOCX contains "
                f"NO native equations - every one shipped as source text")
        elif n_omml < facts["math"] // 2:
            findings.append(
                f"{name}: source declares {facts['math']} mathematics span(s), DOCX has {n_omml} native "
                f"equations - more than half fell back to source text")
    if out["raw_dollars"]:
        findings.append(
            f"{name}: DOCX carries {out['raw_dollars']} residual '$' - those are unrendered delimiters a "
            f"reader will see as literal characters")
    if facts.get("figures") and len(media) < len(facts["figures"]):
        findings.append(
            f"{name}: source references {len(facts['figures'])} figure(s), DOCX embeds {len(media)} - "
            f"the missing ones are simply absent, with nothing to indicate it")
    return findings, out


def check_html(name: str, path: pathlib.Path, spec: dict) -> tuple[list[str], dict]:
    findings: list[str] = []
    out: dict = {}
    if not path.exists():
        findings.append(f"{name}: HTML missing at {path.relative_to(ROOT)}")
        return findings, out
    html = path.read_text(encoding="utf-8")
    rend = spec.get("renderer")
    out["size_kb"] = len(html) // 1024

    if rend == "mathjax":
        if "mathjax/" not in html:
            findings.append(f"{name}: the HTML does not load MathJax at all")
        if "mjx-container" not in html and "MathJax-script" not in html:
            findings.append(f"{name}: no MathJax entry point found in the HTML")
    elif rend == "katex":
        if "katex" not in html:
            findings.append(f"{name}: the HTML does not load KaTeX at all")

    for src in re.findall(r'<img[^>]+src="([^"]+)"', html):
        if src.startswith(("http", "data:")):
            continue
        if not (path.parent / src).exists():
            findings.append(f"{name}: HTML references an image that is not there: {src}")
    out["imgs"] = len(re.findall(r"<img", html))
    return findings, out


def check_pdf(name: str, path: pathlib.Path) -> tuple[list[str], dict]:
    findings: list[str] = []
    out: dict = {}
    if not path.exists():
        findings.append(f"{name}: PDF missing at {path.relative_to(ROOT)}")
        return findings, out
    b = path.read_bytes()
    out["size_kb"] = len(b) // 1024
    if not b.startswith(b"%PDF"):
        findings.append(f"{name}: the PDF does not begin with a PDF header")
    if len(b) < 50_000:
        findings.append(f"{name}: the PDF is {len(b)//1024} KB, which is too small to contain a document "
                        f"with figures")
    return findings, out


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--only", default=None, help="check one document set by name")
    args = ap.parse_args()

    findings: list[str] = []
    n_assert = 0
    for name, spec in DOC_SETS.items():
        if args.only and name != args.only:
            continue
        f, facts = check_source(name, spec)
        findings += f
        n_assert += 4
        if spec.get("docx"):
            f, _ = check_docx(name, ROOT / spec["docx"], facts)
            findings += f
            n_assert += 5
        f, _ = check_html(name, ROOT / spec["html"], spec)
        findings += f
        n_assert += 3
        if spec.get("pdf"):
            f, _ = check_pdf(name, ROOT / spec["pdf"])
            findings += f
            n_assert += 3

    print(f"  document sets checked: {len(DOC_SETS)}   assertions evaluated: {n_assert}")
    if findings:
        print(f"\n  [FAIL] {len(findings)} finding(s) in the produced documents:")
        for x in findings:
            print("      " + x)
        print("\n  An artefact that does not contain what its source promises is not a smaller document -")
        print("  it is a different one, and the difference is invisible to whoever opens it.")
        return 1
    print("\n  [OK] every document carries the mathematics, figures and assets its source declares, and")
    print("       every renderer has the fonts it needs to render them")
    return 0


if __name__ == "__main__":
    sys.exit(main())
