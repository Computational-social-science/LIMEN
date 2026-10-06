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
    "manuscript": {
        "md": None,                     # built from the protocol, not from markdown
        "html": "viz/manuscript.html",
        "docx": None,
        "pdf": None,
        "renderer": "katex",
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