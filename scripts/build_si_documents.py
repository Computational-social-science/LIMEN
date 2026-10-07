#!/usr/bin/env python
"""build_si_documents.py -- render the Supplementary Information to HTML, DOCX and PDF.

The SI is authored once as Markdown (`docs/SUPPLEMENTARY_INFORMATION.md`, generated with every number read
from its source artefact) and rendered here into the formats a submission needs. One source, three outputs:
a second copy of the text would be a second thing to keep true.

PDF comes from a headless Edge print of the HTML rather than from a second typesetting chain, so the PDF and
the HTML cannot disagree about layout or content.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import si_render as SR      # mathematics protection and local KaTeX

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "SUPPLEMENTARY_INFORMATION.md"
OUT_HTML = ROOT / "viz" / "supplementary_information.html"
OUT_DOCX = ROOT / "viz" / "supplementary_information.docx"
OUT_PDF = ROOT / "viz" / "supplementary_information.pdf"
BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"]

CSS = """
 body{font:10.5pt/1.55 Georgia,"Times New Roman",serif;color:#1a1a1a;max-width:44rem;margin:3rem auto;
      padding:0 1.4rem;background:#fff}
 h1{font-size:1.5rem;line-height:1.3;margin:0 0 1rem}
 h2{font-size:1.12rem;margin:2.6rem 0 .7rem;padding-bottom:.25rem;border-bottom:1px solid #d8d8d8}
 h3{font-size:.98rem;margin:1.7rem 0 .5rem}
 p{margin:.7rem 0}
 table{border-collapse:collapse;width:100%;font-size:.85rem;margin:1rem 0}
 th,td{border-top:1px solid #ccc;border-bottom:1px solid #ccc;padding:.32rem .5rem;text-align:left;
       vertical-align:top}
 th{background:#f6f6f6;font-weight:600}
 code{font-family:Consolas,monospace;font-size:.88em;background:#f3f3f3;padding:.05em .3em;border-radius:2px}
 em{color:#444}
 hr{border:0;border-top:1px solid #e2e2e2;margin:2rem 0}
 .li{margin-left:1.1rem;text-indent:-1.1rem}
 .mathcount{font-size:.75rem;color:#999;text-align:right;margin-top:3rem}
 .mathfail{border:1px solid #c00;color:#c00;padding:.5rem}
 .nfig{margin:1.2rem 0;text-align:center}
 .nfig img{max-width:100%;height:auto}
 .katex-display{margin:.9em 0;overflow-x:auto;overflow-y:hidden}
 @media print{body{margin:0;max-width:none;padding:0} h2{page-break-after:avoid} table{page-break-inside:avoid}}
"""


def md_to_html_body(md: str) -> str:
    """Minimal, dependency-free renderer for the subset this document uses.

    Deliberately small: headings, paragraphs, tables, code spans, bold/italic, rules. The manuscript builder
    carries a full renderer for the protocol; this document needs none of its machinery, and a second heavy
    dependency for one file is a cost with no return.
    """
    out, tbl = [], []
    def flush():
        if not tbl:
            return
        rows = [r for r in tbl if not re.match(r"^\|[\s:|-]+\|$", r)]
        celled = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
        head, body = celled[0], celled[1:]
        html = ["<table><thead><tr>" + "".join(f"<th>{c}</th>" for c in head) + "</tr></thead><tbody>"]
        html += ["<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in body]
        html.append("</tbody></table>")
        out.append("".join(html))
        tbl.clear()

    for line in md.splitlines():
        s = line.rstrip()
        if s.startswith("|"):
            tbl.append(s)
            continue
        flush()
        if not s:
            continue
        if s.startswith("### "):
            out.append(f"<h3>{s[4:]}</h3>")
        elif s.startswith("## "):
            out.append(f"<h2>{s[3:]}</h2>")
        elif s.startswith("# "):
            out.append(f"<h1>{s[2:]}</h1>")
        elif s.startswith("---"):
            out.append("<hr>")
        else:
            out.append(f"<p>{s}</p>")
    flush()
    html = "\n".join(out)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", html)
    html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)
    html = html.replace("&nbsp;", "&nbsp;")
    return html


def build_docx(md: str) -> None:
    try:
        import docx
        from docx.shared import Pt
    except ImportError:
        r = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "python-docx"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("  [WARN] python-docx unavailable; DOCX skipped")
            return
        import docx
        from docx.shared import Pt
    doc = docx.Document()
    doc.styles["Normal"].font.name = "Georgia"
    doc.styles["Normal"].font.size = Pt(10.5)
    tbl_buf: list[str] = []
    def flush():
        if not tbl_buf:
            return
        rows = [r for r in tbl_buf if not re.match(r"^\|[\s:|-]+\|$", r)]
        cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
        if cells:
            t = doc.add_table(rows=0, cols=len(cells[0]))
            t.style = "Light Grid Accent 1"
            for i, row in enumerate(cells):
                rc = t.add_row().cells
                for j, c in enumerate(row[:len(cells[0])]):
                    rc[j].text = re.sub(r"\*\*(.+?)\*\*", r"\1", c)
        tbl_buf.clear()
    for line in md.splitlines():
        s = line.rstrip()
        if s.startswith("|"):
            tbl_buf.append(s)
            continue
        flush()
        if not s:
            continue
        if s.startswith("### "):
            doc.add_heading(s[4:], level=3)
        elif s.startswith("## "):
            doc.add_heading(s[3:], level=2)
        elif s.startswith("# "):
            doc.add_heading(s[2:], level=1)
        elif s.startswith("---"):
            doc.add_paragraph("")
        else:
            doc.add_paragraph(re.sub(r"\*\*(.+?)\*\*", r"\1", re.sub(r"`([^`]+)`", r"\1", s)))
    flush()
    # THE DOCX HAS ONE OWNER: THE OMML BUILDER. Two builders wrote the same path and the one that ran last
    # silently won, so the equation-native DOCX could be replaced by a TeX-source one without any error
    # appearing - the document still opened, only its mathematics regressed. This delegates instead.
    r = subprocess.run([str(sys.executable), str(ROOT / "scripts" / "build_docx.py"), "--build",
                        "--src", str(ROOT / "docs" / "SUPPLEMENTARY_INFORMATION.md"),
                        "--out", str(OUT_DOCX)], capture_output=True, text=True, encoding="utf-8")
    for line in (r.stdout or "").strip().splitlines()[-2:]:
        print("  " + line)
    if r.returncode != 0:
        print("  [FAIL] the OMML builder failed; the DOCX was NOT regenerated")
        print((r.stderr or "").strip()[-300:])
        raise SystemExit(1)


def build_pdf() -> None:
    exe = next((b for b in BROWSERS if pathlib.Path(b).exists()), None)
    if not exe:
        print("  [WARN] no Edge/Chrome; PDF skipped")
        return
    prof = ROOT / "viz" / ".si_pdf_profile"
    subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--user-data-dir={prof}", f"--print-to-pdf={OUT_PDF}", OUT_HTML.resolve().as_uri()],
                   capture_output=True, text=True, timeout=300)
    shutil.rmtree(prof, ignore_errors=True)
    if OUT_PDF.exists() and OUT_PDF.stat().st_size > 10_000:
        n = len(re.findall(rb"/Type\s*/Page[^s]", OUT_PDF.read_bytes()))
        print(f"  wrote {OUT_PDF.relative_to(ROOT)}  ({OUT_PDF.stat().st_size // 1024} KB, ~{n} pages)")
    else:
        print("  [WARN] PDF not produced")


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    args = ap.parse_args()
    if not SRC.exists():
        print(f"  [FAIL] no source at {SRC}; run scripts/build_supplementary_information.py first")
        return 1
    md = SRC.read_text(encoding="utf-8")
    body = SR.md_to_html_body(md)
    n_inline = len(re.findall(r"(?<!\$)\$(?!\$)", body))
    OUT_HTML.write_text(
        "<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<title>Supplementary information — LIMEN Phase I</title>"
        f"<style>{CSS}</style>" + SR.MATHJAX_SCRIPTS + "</head><body>\n" + body + "\n</body></html>\n",
        encoding="utf-8", newline="\n")
    ver = SR.copy_mathjax(ROOT / "viz" / "mathjax")
    print(f"  mathjax   : {ver} (copied locally; no network request)")
    print(f"  math      : {n_inline // 2} inline span(s) preserved through rendering")
    print(f"  wrote {OUT_HTML.relative_to(ROOT)}  ({OUT_HTML.stat().st_size // 1024} KB)")
    build_docx(md)
    build_pdf()
    return 0


if __name__ == "__main__":
    sys.exit(main())