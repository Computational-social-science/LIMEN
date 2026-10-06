#!/usr/bin/env python
"""build_figures_document.py -- deliver the Stage 2 figures WITH their long captions, as HTML/MD/DOCX/PDF.

WHY THE CAPTIONS LIVE HERE AND NOT IN THE IMAGE
    A caption is read in the manuscript, not inside the plot: Nature and its family set captions in the page's
    own type, below the figure, and a caption baked into the raster cannot be re-typeset, translated, or
    restyled, and it duplicates text that already belongs to the document. The figures therefore carry no
    caption, and this script puts each caption where it is read - under the figure, in each document format.

SINGLE SOURCE OF TRUTH
    The captions are READ from `viz/figures/FIGURE_CAPTIONS.md`, which `build_stage2_figures.py` generates with
    every number derived from the data CSV. This script does not retype them, so a caption cannot disagree
    with the figure it describes.

OUTPUTS
    viz/figures_stage2.html   self-contained: the PNGs are embedded, so the file travels as one artefact
    viz/figures_stage2.md     the markdown source, for pandoc and for diffing
    viz/figures_stage2.docx   if pandoc is available
    viz/figures_stage2.pdf    if pandoc is available and a PDF engine is present
"""

from __future__ import annotations

import argparse
import base64
import pathlib
import re
import shutil
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
FIG_DIR = REPO_ROOT / "viz" / "figures"
CAPTIONS = FIG_DIR / "FIGURE_CAPTIONS.md"
OUT_HTML = REPO_ROOT / "viz" / "figures_stage2.html"
OUT_MD = REPO_ROOT / "viz" / "figures_stage2.md"

TITLES = {
    "fig1_stage2_hypotheses": "Figure 1. The three pre-registered hypotheses across the noise grid",
    "fig2_stage2_error_destination": "Figure 2. Where the errors go: the gate rejects most of what noise breaks",
    "fig3_stage2_gate_separation": "Figure 3. Why the gate separates better under noise",
}


def parse_captions() -> dict[str, str]:
    """Split FIGURE_CAPTIONS.md into {stem: text}, taking the '## <stem>' sections."""
    text = CAPTIONS.read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for m in re.finditer(r"^## (\S+)\n\n(.*?)(?=\n## |\Z)", text, re.S | re.M):
        out[m.group(1)] = m.group(2).strip()
    return out


def inline_bold(s: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--no-convert", action="store_true", help="write HTML and MD only")
    args = ap.parse_args()

    if not CAPTIONS.exists():
        print(f"  [FAIL] no captions at {CAPTIONS}; run scripts/build_stage2_figures.py first")
        return 1
    caps = parse_captions()
    missing = [s for s in TITLES if s not in caps]
    if missing:
        print(f"  [FAIL] captions missing for {missing}")
        return 1

    md_lines = ["# LIMEN Phase I — Stage 2 figures", "",
                "Each figure is followed by its caption, as it would appear in the manuscript.", ""]
    html_body = []
    for stem, title in TITLES.items():
        png = FIG_DIR / f"{stem}.png"
        if not png.exists():
            print(f"  [FAIL] no figure at {png}")
            return 1
        b64 = base64.b64encode(png.read_bytes()).decode("ascii")
        md_lines += [f"## {title}", "", f"![{title}](figures/{stem}.png)", "", caps[stem], ""]
        html_body.append(
            f'<figure>\n  <img src="data:image/png;base64,{b64}" alt="{title}">\n'
            f'  <figcaption><span class="ftitle">{inline_bold(title)}</span> '
            f'{inline_bold(caps[stem])}</figcaption>\n</figure>'
        )
    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8", newline="\n")
    print(f"  wrote {OUT_MD.relative_to(REPO_ROOT)}")

    OUT_HTML.write_text(
        """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>LIMEN Phase I — Stage 2 figures</title>
<style>
 body { font: 11pt/1.5 Georgia, "Times New Roman", serif; color: #222; max-width: 46rem;
        margin: 3rem auto; padding: 0 1.2rem; background: #fff; }
 h1 { font-size: 1.35rem; border-bottom: 1px solid #ccc; padding-bottom: .4rem; }
 h2 { font-size: 1.05rem; margin-top: 2.6rem; }
 figure { margin: 0 0 2.4rem; }
 img { width: 100%; height: auto; display: block; }
 figcaption { font-size: .86rem; line-height: 1.45; color: #333; margin-top: .7rem;
              text-align: left; }
 .ftitle { font-weight: 700; }
 @media print { body { margin: 0; max-width: none; } figure { page-break-inside: avoid; } }
</style></head><body>
<h1>LIMEN Phase I — Stage 2 figures</h1>
<p>Each figure is followed by its caption, set in the document's own type as a manuscript would set it.
Captions are generated from the same data as the plots and are not part of the images.</p>
""" + "\n".join(html_body) + "\n</body></html>\n",
        encoding="utf-8", newline="\n")
    print(f"  wrote {OUT_HTML.relative_to(REPO_ROOT)}  (self-contained, {OUT_HTML.stat().st_size // 1024} KB)")

    if args.no_convert:
        return 0
    if not shutil.which("pandoc"):
        print("  [WARN] pandoc not on PATH - HTML and MD written, DOCX/PDF skipped")
        return 0
    for ext, extra in (("docx", []), ("pdf", ["--pdf-engine=xelatex"])):
        out = REPO_ROOT / "viz" / f"figures_stage2.{ext}"
        cmd = ["pandoc", str(OUT_MD), "-o", str(out),
               "--resource-path", str(REPO_ROOT / "viz"), *extra]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and out.exists():
            print(f"  wrote {out.relative_to(REPO_ROOT)}  ({out.stat().st_size // 1024} KB)")
        else:
            print(f"  [WARN] pandoc could not write {ext}: {(r.stderr or '').strip().splitlines()[:1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())