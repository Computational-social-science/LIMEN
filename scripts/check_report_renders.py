"""check_report_renders.py -- load the report in a real browser and require every section to render.

WHY THIS IS THE CHECK THAT WAS MISSING. The report's references, quality-control text, limitations and
reproduce commands were BLANK on the live page. The cause was one field name: the length table reads
`a.state_len`, the exporter wrote `state_median`, `a.state_len.min` threw inside an Array.map, and
because the page is a single IIFE the exception ended the script -- so every section after section 4.3
rendered as an empty container.

Five guards passed on that page:

  * check_report_js_syntax.py    -- `node --check`; the syntax was valid, the throw was at runtime
  * check_report_js_helpers.py   -- verifies CALLED names; `a.state_len` is a member access
  * qc_report_structure.py       -- matches substrings in the HTML; `id="lenTable"` is present whether
                                    or not anything ever fills it
  * qc_report_citations.py       -- matches citation strings, which were in the source
  * check_citation_links.py      -- citation keys resolved to entries that existed

Every one of them inspected the report as TEXT. A container that is present and empty is
indistinguishable from a present and full one when all you have is the source. For a rendered
artefact the only valid verification is to render it, and this is that check.

WHAT IT ASSERTS
  1. No uncaught page error and no console error.
  2. Every container the report is built from has content. The list is explicit rather than derived,
     so a section that is deleted from the markup is a failure to declare rather than a silent pass.
  3. The reference list is non-empty and every entry renders.

NEGATIVE CONTROL
  --negative-test loads a copy of the report whose state is missing the arm field the length table
  reads, and requires the check to report the resulting failure. This is the real defect, reproduced
  on demand, which is stronger evidence than a synthetic injection.

NOT IN run_all_guards.py unless playwright and a browser are both present: it needs a real browser and
about ten seconds. It belongs in the release path, and the suite reports it as skipped rather than
silently absent when the browser is unavailable.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[1]
REPORT = REPO / "viz" / "report" / "technical-report.html"

# Every container the report fills. Named explicitly: a derived list would quietly shrink if a
# section were removed from the markup.
CONTAINERS = [
    "refs", "qc", "limits", "repro", "sigChannel", "funnel", "tiles", "armTable", "layerChart",
    "lenTable", "consistency", "imeCard", "channelCard", "sources", "instruments", "artefacts",
    "vendored", "meas-pref", "meas-f2", "meas-shift", "meas-margin", "meas-crossarm", "meas-proot",
    "meas-diagnostics", "meas-paired", "repro-timing", "meas-summary",
]


def launch_browser(p):
    """Launch any Chromium the host actually has.

    The bundled binary is a 195 MB download that this host's connection fails part-way through
    (ECONNRESET, twice). A render check that refuses to run because a download did not finish leaves
    the report unverified, which is the state the report was in when this guard was written. The
    system Chrome and Edge are the same engine, so they are tried in turn and the one used is
    printed -- a check should say which browser rendered the page it is certifying.
    """
    last = None
    for kw in ({}, {"channel": "chrome"}, {"channel": "msedge"}):
        try:
            return p.chromium.launch(**kw), (kw.get("channel") or "bundled chromium")
        except Exception as e:  # noqa: BLE001
            last = e
    raise RuntimeError("no Chromium available: %s" % str(last).split("\n")[0])


def run(path: pathlib.Path) -> tuple[list[str], list[str], int]:
    """Returns (problems, console/page errors, n_refs, browser_used)."""
    from playwright.sync_api import sync_playwright

    problems: list[str] = []
    errors: list[str] = []
    n_refs = 0
    with sync_playwright() as p:
        browser, which = launch_browser(p)
        page = browser.new_page()
        page.on("pageerror", lambda e: errors.append("pageerror: %s" % e))
        page.on("console", lambda m: errors.append("console.%s: %s" % (m.type, m.text))
                if m.type == "error" else None)
        page.goto(path.as_uri())
        page.wait_for_timeout(2500)  # let MathJax and the state render settle
        report = page.evaluate(
            """(ids) => {
                 const out = {empty: [], missing: []};
                 for (const id of ids) {
                   const e = document.getElementById(id);
                   if (!e) out.missing.push(id);
                   else if (e.innerHTML.trim().length === 0) out.empty.push(id);
                 }
                 out.refs = document.querySelectorAll('#refs li').length;
                 out.banner = (document.getElementById('banner') || {}).className || '';
                 return out;
               }""", CONTAINERS)
        n_refs = report.get("refs", 0)
        for mid in report.get("missing", []):
            problems.append("container #%s is not in the document at all" % mid)
        for eid in report.get("empty", []):
            problems.append("container #%s rendered EMPTY" % eid)
        if n_refs == 0:
            problems.append("the reference list rendered no entries")
        if "bad" in (report.get("banner") or ""):
            problems.append("the page's own failure banner is showing")
        browser.close()
    return problems, errors, n_refs, which


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative-test", action="store_true")
    args = ap.parse_args()

    try:
        import playwright  # noqa: F401
    except ImportError:
        print("  [SKIP] playwright is not installed, so the report was NOT rendered.")
        print("         This check cannot pass without a browser; install it or treat the report as")
        print("         unverified. A skipped render check is not a passed one.")
        return 2
    if not REPORT.exists():
        print("  [FAIL] report not found: %s" % REPORT)
        return 1

    if args.negative_test:
        # Reproduce the real defect: the state omits the arm field the length table reads.
        state = (REPORT.parent / "state.js").read_text(encoding="utf-8")
        broken = re.sub(r'"state_len":\{[^}]*\},', "", state)
        if broken == state:
            print("  [FAIL] the control could not remove state_len from the state: it is INERT")
            return 1
        with tempfile.TemporaryDirectory() as td:
            tmp = pathlib.Path(td)
            (tmp / "state.js").write_text(broken, encoding="utf-8")
            (tmp / "technical-report.html").write_text(
                REPORT.read_text(encoding="utf-8"), encoding="utf-8")
            problems, errors, _, _which = run(tmp / "technical-report.html")
        if problems or errors:
            print("  [OK] negative control fires: with state_len removed the page fails to render")
            for x in (problems + errors)[:3]:
                print("       %s" % x[:110])
            return 0
        print("  [FAIL] removing state_len did not break the render -- the control is inert")
        return 1

    problems, errors, n_refs, which = run(REPORT)
    print("  rendered by        : %s" % which)
    print("  containers checked : %d" % len(CONTAINERS))
    print("  references rendered: %d" % n_refs)
    print("  page errors        : %d" % len(errors))
    if errors:
        print()
        for e in errors[:6]:
            print("  [FAIL] %s" % e[:150])
    if problems:
        print()
        for x in problems:
            print("  [FAIL] %s" % x)
        print()
        print("  A section that renders empty looks identical to a section that has no content.")
        print("  The page is one script: an exception anywhere ends it and costs every later section.")
        return 1
    print("  [OK] the report renders: every container has content, no page error, %d references"
          % n_refs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
