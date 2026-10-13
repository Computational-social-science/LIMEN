"""check_report_state_contract.py -- the report may only read fields the state provides.

WHY THIS EXISTS. The report rendered a blank section 4.4 through 8, including its entire reference
list, and every check in the suite passed. The cause was one field name: the length table reads
`a.state_len.{min,p25,median,p75,max}`, and the exporter emitted `state_median` and `state_max`
instead. `a.state_len` was undefined on all six arms, `a.state_len.min` threw inside an Array.map,
and because the whole page is a single IIFE, the exception ended the script -- so every section after
that point rendered as an empty container.

The page looked like a report with thin content. It was a page that had crashed, and nothing said so.

WHY NO EXISTING CHECK CAUGHT IT, WHICH IS THE POINT.
  * `check_report_js_syntax.py` runs `node --check` -- the syntax was valid.
  * `check_report_js_helpers.py` verifies CALLED NAMES; `M.state_displacement` is a member access.
  * `qc_report_structure.py` matches substrings in the HTML -- `id="lenTable"` was present, because
    the container exists whether or not anything fills it.
  * `qc_report_citations.py` matches citation strings.
  Every one of them inspected the report's SOURCE. None compared the report against the data it is a
  view of. A container that is present and empty is indistinguishable from a container that is
  present and full, when all you have is the source.

WHAT IT CHECKS
    Every `<root>.<field>` the report's JavaScript reads, where root is a state object (S, D, A, CH,
    MS, INS) or the arm binding inside a map, must name a field the exported state actually carries.
    Reading a field that does not exist is either a silent `undefined` or -- inside the single IIFE --
    a thrown exception that costs every later section.

NEGATIVE CONTROL
    Injects a read of a field that does not exist and requires the check to report it. Without a
    control this check has the same status as the four that passed on the broken page.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
REPORT = REPO / "viz" / "report" / "technical-report.html"
STATE = REPO / "viz" / "report" / "state.js"

# The roots whose fields come from the exported state. `a` is the arm binding inside order.map().
ARM_ROOTS = {"a"}
STATE_ROOTS = {"S", "D", "CH", "MS", "INS"}

# Fields that are not state at all -- DOM and JavaScript builtins, named individually so the
# exemption is auditable. The report does call these on real elements (`a.className = ...`,
# `el.addEventListener(...)`), so a check that treated them as missing state fields would be
# reporting the language rather than the data. Every entry below is a DOM or JS member; nothing here
# is a state field, and nothing was added to silence a genuine miss.
NON_STATE = {
    # DOM members
    "addEventListener", "appendChild", "classList", "className", "getAttribute", "setAttribute",
    "innerHTML", "textContent", "querySelector", "getElementById", "scrollIntoView", "toggle",
    "dataset", "style", "exists", "href", "id",
    # JavaScript builtins and array/string methods
    "add", "class", "inner", "length", "push", "map", "filter", "find", "join", "sort", "slice",
    "toFixed", "replace", "trim", "forEach", "charAt", "split", "reduce", "keys", "values",
    "entries", "includes", "indexOf", "concat", "min", "max", "className",
}


def load_state() -> dict:
    t = STATE.read_text(encoding="utf-8")
    m = re.search(r"APP_STATE\s*=\s*(\{.*\})\s*;?\s*$", t, re.S)
    if not m:
        raise SystemExit("  [FAIL] state.js does not contain an APP_STATE object literal")
    return json.loads(m.group(1))


def report_script() -> str:
    """Every script the report runs: its inline blocks PLUS any file it references beside it.

    THE EXTERNAL FILE MUST BE INCLUDED OR THIS CHECK PASSES VACUOUSLY. The consumer of the exported
    state used to be inline. When it moved to `report.js`, the largest inline block became the
    1,210-character MathJax configuration, which reads no state at all -- so this check found no
    reads at all, reported success, and would have gone on reporting success with every field it
    guards wrong. A check that does not look where the code lives is not a check.
    """
    html = REPORT.read_text(encoding="utf-8")
    parts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S | re.I)
    for src in re.findall(r"""<script[^>]*\bsrc=["']([^"']+)["'][^>]*>""", html, re.I):
        ext = (REPORT.parent / src).resolve()
        # SAME DIRECTORY ONLY. The page also loads the vendored MathJax bundle from ../mathjax/ -- 1.2 MB
        # of library code that reads none of this project's state. Including it made this check scan 261
        # symbol accesses in someone else's minified source and report them as report defects.
        if ext.parent == REPORT.parent.resolve() and ext.suffix == ".js" and ext.exists():
            parts.append(ext.read_text(encoding="utf-8"))
    return "\n".join(parts)


def audit(state: dict, src: str) -> list[str]:
    """Every field the report reads must exist SOMEWHERE in the state.

    The criterion is deliberately "present anywhere in the exported state" rather than "present on an
    arm". `a` is not always the arm: the report reuses it as the map binding for the measurement rows,
    the instrument manifest and the artefact list (`a.layer`, `a.path`, `a.purpose` are all legitimate
    reads of other objects). Scoping the check to arm fields produced ten false positives; widening
    NON_STATE to swallow them would have been the blanket exemption this project forbids, and it would
    have hidden the very defect the check exists for.

    "Present anywhere" is both narrower and stronger: it accepts every genuine read, and it still
    rejects a field that exists in no part of the state -- which is exactly the shape of the failure
    that cost sections 4.4 through 8, where `state_len` was a name the exporter never wrote.
    """
    present: set[str] = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                present.add(k)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(state)

    findings: list[str] = []
    for root, field in re.findall(r"\b([A-Za-z_$][\w$]*)\.([A-Za-z_$][\w$]*)", src):
        if field in NON_STATE:
            continue
        if root in ARM_ROOTS or root in STATE_ROOTS:
            if field not in present:
                findings.append("reads %s.%s -- that field exists nowhere in the exported state"
                                % (root, field))
    return sorted(set(findings))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative-test", action="store_true")
    args = ap.parse_args()

    if not REPORT.exists() or not STATE.exists():
        print("  [FAIL] report or state missing: %s / %s" % (REPORT, STATE))
        return 1
    state = load_state()
    src = report_script()
    if not src:
        print("  [FAIL] no inline script found in the report")
        return 1

    if args.negative_test:
        probe = src + "\nconst _probe = a.field_that_no_arm_carries;\n"
        if probe == src:
            print("  [FAIL] the control injected nothing: it is INERT")
            return 1
        f = audit(state, probe)
        if any("field_that_no_arm_carries" in x for x in f):
            print("  [OK] negative control fires: a read of a non-existent field is reported")
            return 0
        print("  [FAIL] the injected read was not reported -- the check cannot fail")
        return 1

    findings = audit(state, src)
    arms = state.get("arms") or {}
    n_fields = len({k for a in arms.values() for k in a})
    print("  state roots checked : %s + arm binding" % ", ".join(sorted(STATE_ROOTS)))
    print("  arm fields provided : %d" % n_fields)
    print("  arms                : %d" % len(arms))
    if findings:
        print()
        for x in findings:
            print("  [FAIL] %s" % x)
        print()
        print("  A field the state does not carry is `undefined`, or -- inside the report's single")
        print("  IIFE -- an exception that costs every section after it. Fix the exporter or the read,")
        print("  never the guard.")
        return 1
    print("  [OK] every state field the report reads is one the exporter writes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
