"""build_paper_html.py -- render the MANUSCRIPT from its own source.

WHY THIS EXISTS. `viz/manuscript.html` was produced by rendering the PROTOCOL file. It therefore read like a
protocol - sections named "Timeline", "Runbook", "Document control" - because it *was* one, with a manuscript's
title on top. A reader asking where the paper was would find the runbook, and the answer was that no paper had
been written: the generator's source line pointed at `protocol/..._Protocol.md`.

This builder renders `docs/PAPER.md`, which is authored as a paper (abstract, introduction, results,
discussion, methods) and cites the appendices for detail rather than reproducing them.

It REUSES `si_render` rather than re-implementing: the mathematics protection, the MathJax configuration, the
font copying and the image handling were each fixed against a real defect in that module, and a second
implementation would re-introduce every one of them. Load by path, never restate.
"""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "PAPER.md"
FIG_DIR = ROOT / "viz" / "figures"
OUT_HTML = ROOT / "viz" / "manuscript.html"
OUT_PDF = ROOT / "viz" / "manuscript.pdf"


def _load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SR = _load("si_render_", ROOT / "scripts" / "si_render.py")

CSS = """
body{font:10.5pt/1.6 Georgia,"Times New Roman",serif;color:#111;max-width:47rem;margin:3rem auto;
     padding:0 1.4rem;background:#fff}
h1{font-size:1.62rem;line-height:1.28;margin:0 0 .6rem;font-weight:700}
h2{font-size:1.16rem;margin:2.6rem 0 .7rem;padding-bottom:.25rem;border-bottom:1px solid #d8d8d8}
h3{font-size:1rem;margin:1.8rem 0 .5rem}
p{margin:.72rem 0;text-align:justify}
table{border-collapse:collapse;width:100%;font-size:.85rem;margin:1rem 0}
th,td{border-top:1px solid #ccc;border-bottom:1px solid #ccc;padding:.32rem .5rem;text-align:left;
      vertical-align:top}
th{background:#f6f6f6;font-weight:600}
code{font-family:Consolas,monospace;font-size:.88em;background:#f3f3f3;padding:.05em .3em;border-radius:2px}
em{color:#333}
hr{border:0;border-top:1px solid #e2e2e2;margin:2.2rem 0}
li{margin:.3rem 0}
blockquote{margin:1rem 0 1rem 1.1rem;padding-left:.9rem;border-left:3px solid #ddd;color:#333}
.nfig{margin:1.3rem 0;text-align:center}
.nfig img{max-width:100%;height:auto}
.mathcount{font-size:.75rem;color:#999;text-align:right;margin-top:3rem}
.mathfail{border:1px solid #c00;color:#c00;padding:.5rem}
@media print{body{margin:0;max-width:none;padding:0} h2{page-break-after:avoid} table{page-break-inside:avoid}
  .nfig{page-break-inside:avoid}}
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--no-pdf", action="store_true")
    args = ap.parse_args(argv)

    md = SRC.read_text(encoding="utf-8")
    # The paper does not carry the SI's figure plate; its figures are referenced where they are discussed and
    # the plate in the SI is the canonical presentation. Insert the plate markers here so a reader of the
    # manuscript alone still sees them.
    body = SR.md_to_html_body(md).replace(
        "<p><strong>Running title.</strong> Orthographic channels as structural disturbances in "
        "human–model interaction</p>", "")

    # PROVENANCE. The paper reports a pre-registered protocol, and the digest of the protocol file is what
    # makes a version number identify a content. Without it a reader cannot tell whether the paper and the
    # registration describe the same study.
    import hashlib
    anchor_path = ROOT / "protocol" / "NHB_Orthographic_Channels_JEV_Research_Protocol.md"
    digest = hashlib.sha256(anchor_path.read_bytes()).hexdigest() if anchor_path.is_file() else "?"
    stamp = (f'<p class="stamp"><em>This manuscript reports the pre-registered protocol pinned at '
             f'sha256 {digest}. The protocol, its amendments, the analysis code, the stimulus bank, the guard '
             f'suite and the formal development are released together; see Supplementary information.</em></p>')
    body = body + "\n" + stamp

    OUT_HTML.write_text(
        "<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<title>Typing errors make a language model's confidence gate sharper, not weaker</title>"
        f"<style>{CSS}</style>" + SR.MATHJAX_SCRIPTS + "</head><body>\n" + body + "\n</body></html>\n",
        encoding="utf-8", newline="\n")
    print(f"  wrote {OUT_HTML.relative_to(ROOT)}  ({OUT_HTML.stat().st_size // 1024} KB)")

    if not args.no_pdf:
        prof = ROOT / ".git" / "_paper_pdf_profile"
        html_url = OUT_HTML.resolve().as_uri()
        edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        for exe in (edge, r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"):
            if pathlib.Path(exe).exists():
                r = subprocess.run(
                    [exe, "--headless", "--disable-gpu", "--no-first-run",
                     f"--user-data-dir={prof}", f"--print-to-pdf={OUT_PDF}", html_url],
                    capture_output=True, text=True, timeout=180)
                if OUT_PDF.exists():
                    print(f"  wrote {OUT_PDF.relative_to(ROOT)}  ({OUT_PDF.stat().st_size // 1024} KB)")
                    return 0
                print(f"  [WARN] pdf step returned {r.returncode}; no PDF written")
                return 1
        print("  [WARN] no headless browser found; HTML written, PDF skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
