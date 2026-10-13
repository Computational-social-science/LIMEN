"""check_report_js_syntax.py -- the report's JavaScript must actually parse.

WHY THIS EXISTS, AND WHY IT IS EMBARRASSING. The reference list was converted from an array of strings
to an array of `{key, text}` objects so that a citation could resolve to an entry. The conversion
consumed each entry's closing quote, so all 26 `t:` values ended unquoted. The reference list was
invalid JavaScript and would not have rendered.

Nothing noticed. `check_report_js_helpers.py` inspects identifiers, `qc_report_structure.py` inspects
markup and text, and `qc_report_citations.py` matches strings -- not one of them parses the language
the report is written in. Three textual guards passed on a document whose script could not load.

`node` was available the whole time. This runs it.

WHAT IT CHECKS
    Every inline `<script>` block is extracted and passed to `node --check`. An external `<script src>`
    is skipped: it is a separate file with its own delivery. If node is unavailable the check reports
    that it could not run rather than passing, because "I did not look" and "there is nothing there"
    must not produce the same output.

NEGATIVE CONTROL
    Writes a block with a deliberate syntax error to the scratch directory and requires the check to
    reject it, so the check is known to be capable of failing before its pass is believed.
"""
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[1]
REPORT = REPO / "viz" / "report" / "technical-report.html"
SCRIPT_RE = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.S | re.I)


def node_check(src: str, tmp: pathlib.Path):
    tmp.write_text(src, encoding="utf-8")
    try:
        r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        return False, "NODE_MISSING"
    except subprocess.TimeoutExpired:
        return False, "node --check timed out"
    if r.returncode == 0:
        return True, ""
    return False, (r.stdout + r.stderr).strip().split("\n")[-6:]


def main() -> int:
    node = shutil.which("node")
    if not node:
        print("  [FAIL] node is not on PATH, so the report's JavaScript cannot be parsed.")
        print("         This check reports that it could not run rather than passing.")
        return 1
    if not REPORT.exists():
        print("  [FAIL] report not found: %s" % REPORT)
        return 1

    html = REPORT.read_text(encoding="utf-8")
    blocks = [("inline", b) for b in SCRIPT_RE.findall(html)]
    # A REFERENCED LOCAL SCRIPT IS PART OF THIS DOCUMENT. The report's consumer moved out of the HTML
    # into report.js; checking only inline blocks then reported "1 of 1 parses" while the 64 KB file
    # that actually renders the page went unchecked. SAME DIRECTORY ONLY: the page also loads the
    # MathJax bundle from ../mathjax/, which is a vendored library and not this report's code -- and
    # which is large enough to swamp any check that reads it.
    for src in re.findall(r"""<script[^>]*\bsrc=["']([^"']+)["'][^>]*>""", html, re.I):
        ext = (REPORT.parent / src).resolve()
        if ext.parent == REPORT.parent.resolve() and ext.suffix == ".js" and ext.exists():
            blocks.append((src, ext.read_text(encoding="utf-8")))

    if "--negative-test" in sys.argv:
        with tempfile.TemporaryDirectory() as d:
            ok, err = node_check("const REFS = [ { k: 'a', t: unquoted text } ];",
                                 pathlib.Path(d) / "probe.js")
        if not ok and err != "NODE_MISSING":
            print("  [OK] negative control fires: an unquoted value is rejected by node")
            return 0
        print("  [FAIL] the control was NOT rejected -- this check cannot fail, so it proves nothing")
        return 1

    if not blocks:
        print("  [FAIL] no inline script blocks found; the report has no JavaScript to check")
        return 1

    bad = 0
    with tempfile.TemporaryDirectory() as d:
        for n, (label, b) in enumerate(blocks, 1):
            ok, err = node_check(b, pathlib.Path(d) / ("blk%d.js" % n))
            if ok:
                print("  [OK] %s script %d of %d parses (%d chars)"
                      % (label, n, len(blocks), len(b)))
            else:
                print("  [FAIL] %s script %d of %d does not parse:" % (label, n, len(blocks)))
                if isinstance(err, list):
                    for line in err:
                        print("         %s" % line)
                else:
                    print("         %s" % err)
                bad += 1
    if bad:
        print()
        print("  A script that does not parse does not run: the page renders without it.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
