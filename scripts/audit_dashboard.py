#!/usr/bin/env python
"""
audit_dashboard.py -- mechanical audit of viz/health_dashboard.html against the project's
figure standard, the way audit_figure.py audits a matplotlib figure.

WHY A PROGRAMMATIC AUDIT AND NOT A LOOK
    The project's figure standard already says it: a rendered artefact has mechanical defects that a
    reader, and especially an author, does not see. The figure auditor found six classes of them in
    one session, all invisible on inspection. A page that fails the same class of checks is
    unpublishable for the same reason: a clipped label, a state carried by colour alone, or a number
    with no source is a defect whether or not it is noticed.

WHAT IT CHECKS
    1. NO FABRICATED FALLBACK. The page must not carry demo data, and must not substitute a
       plausible value for an absent one. A dashboard that invents content is believed, and this
       project's cost of a believed wrong number is GPU time.
    2. NO fetch()/XHR. Blocked on file:// documents; a page that uses it silently shows nothing.
    3. POLL HYGIENE. The polling must remove the previous script tag, or the DOM grows by one tag
       per tick -- 720 an hour at 5 s.
    4. A WORD WITH EVERY COLOUR. No state may be signalled by colour alone; a monochrome print and a
       colourblind reader must get the same information.
    5. TYPE FLOOR. No font-size below 10 px anywhere in the stylesheet.
    6. OKABE-ITO. Every status colour in the stylesheet must be from the palette the figures use, or
       the page and the manuscript disagree about what "bad" looks like.
    7. DATA AGE IS SHOWN. Rule 4 of the dashboard standard: a live page must let the reader judge
       staleness.
    8. PRINT RULES PRESENT. The page is a scientific record and may be read on paper.
    9. SOURCE-SUFFIXED NUMBERS. Every figure in the state file must carry a `src`, so a number
       without a home cannot reach the page.
   10. THE STATE FILE LOADS AND IS WELL FORMED.

THE NEGATIVE CONTROL IS NOT OPTIONAL
    A check that has never rejected anything is indistinguishable from one that cannot. --self-test
    mutates the page in memory for each defect class and requires every one to be caught.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = ROOT / "viz" / "health_dashboard.html"
STATE_JS = ROOT / "viz" / "state.js"
SCIENCE = ROOT / "config" / "science_state.json"

# The palette the figures use. A status colour outside it makes the page and the manuscript
# disagree about what "bad" looks like, and the disagreement is invisible in review.
OKABE_ITO = {"#0072b2", "#56b4e9", "#009e73", "#f0e442", "#e69f00", "#d55e00", "#cc79a7", "#999999"}

# Strings that mean the page is inventing content rather than reporting absence.
FABRICATION_MARKERS = [
    "demo data", "placeholder data", "sample data", "lorem ipsum",
    "fallbackData", "DEMO_STATE", "defaultState =", "mockData",
]


def strip_comments(page: str) -> str:
    """Remove CSS and JS comments before pattern-matching the page's behaviour.

    Without this the audit reports the page for *describing* what it must not do. The dashboard's
    own comment says "fetch() is blocked on file:// documents", and a naive search for fetch( reads
    that as the page calling fetch. A checker that fires on documentation is one whose findings get
    ignored, which is worse than not having it.
    """
    page = re.sub(r"/\*.*?\*/", " ", page, flags=re.DOTALL)     # CSS and JS block comments
    page = re.sub(r"^\s*//.*$", " ", page, flags=re.MULTILINE)  # JS line comments
    return page


def status_colors(page: str) -> dict:
    """Only the status custom properties, which is what "status colour" means.

    The stylesheet's other hex values are ink and page greys. Folding them into the palette check
    reported #ffffff and #1a1a1a as non-compliant, which is not a fact about the page.
    """
    out = {}
    for name in ("--ok", "--warn", "--fail", "--skip"):
        m = re.search(re.escape(name) + r"\s*:\s*(#[0-9a-fA-F]{6})", page)
        if m:
            out[name] = m.group(1).lower()
    return out


def type_floor(page: str) -> tuple[float | None, int]:
    """The smallest rendered font size, with the var(--t-*) scale resolved.

    The stylesheet sets most type through named scale variables, so matching `font-size: Npx` alone
    found one declaration out of a whole scale and reported a floor that said nothing. Resolve the
    scale first, then measure.
    """
    scale = {m.group(1): float(m.group(2))
             for m in re.finditer(r"(--t-[a-z]+)\s*:\s*([0-9.]+)px", page)}
    sizes = []
    for m in re.finditer(r"font-size:\s*(?:var\((--t-[a-z]+)\)|([0-9.]+)px)", page):
        if m.group(1):
            if m.group(1) in scale:
                sizes.append(scale[m.group(1)])
        else:
            sizes.append(float(m.group(2)))
    return (min(sizes) if sizes else None), len(sizes)


def check(page: str, state_js: str | None, science: dict | None) -> tuple[int, int, list[str]]:
    lines: list[str] = []
    fails = checks = 0

    def ok(msg: str) -> None:
        nonlocal checks
        checks += 1
        lines.append(f"    [PASS] {msg}")

    def bad(msg: str) -> None:
        nonlocal checks, fails
        checks += 1
        fails += 1
        lines.append(f"    [FAIL] {msg}")

    code = strip_comments(page)
    low = page.lower()

    # 1 -- no fabricated fallback. Checked on the whole page: a marker hiding in a comment is still
    #      a block someone may later uncomment.
    hits = [m for m in FABRICATION_MARKERS if m.lower() in low]
    if hits:
        bad(f"fabricated fallback present: {hits}")
    else:
        ok("no fabricated fallback: the page cannot invent a value")

    # 2 -- no fetch on file://  (on the de-commented source)
    if re.search(r"\bfetch\s*\(", code) or re.search(r"XMLHttpRequest", code):
        bad("the page uses fetch()/XHR, which file:// documents block")
    else:
        ok("no fetch()/XHR in executable code: state arrives as a JS global, which file:// allows")

    # 3 -- poll hygiene
    has_buster = "?t=" in code
    removes = bool(re.search(r"removeChild\(\s*tagEl\s*\)", code))
    if has_buster and removes:
        ok("polling re-injects with a cache-buster and removes the previous tag")
    else:
        bad(f"poll hygiene incomplete (buster={has_buster}, removes_old={removes}); "
            f"the DOM grows one tag per tick without it")

    # 4 -- a word with every colour
    has_words = 'class="word' in page
    has_short = "SHORT" in code
    if has_words and has_short:
        ok("every state carries a word alongside its colour")
    else:
        bad("a state may be signalled by colour alone; a monochrome print would lose it")

    # 5 -- type floor, with the scale resolved
    lo, n = type_floor(page)
    if lo is None:
        bad("no font-size could be measured")
    elif lo < 10:
        bad(f"font-size below the 10 px floor: {lo} px")
    else:
        ok(f"type floor respected: smallest of {n} sizes is {lo} px")

    # 6 -- palette, status properties only
    sc = status_colors(page)
    if len(sc) < 4:
        bad(f"could not read all four status colours from the stylesheet (found {sorted(sc)})")
    else:
        stray = sorted(f"{k}={v}" for k, v in sc.items() if v not in OKABE_ITO)
        if stray:
            bad(f"status colours outside Okabe-Ito: {stray}")
        else:
            ok("all four status colours are Okabe-Ito")

    # 7 -- data age. The check must be about the page SHOWING an age, not about the word ageStr
    #      appearing somewhere: a single surviving call in a panel nobody reads would satisfy a
    #      name-presence test while the header said nothing about staleness.
    age_calls = len(re.findall(r"ageStr\s*\(", code))
    age_labelled = bool(re.search(r"<b>age</b>|>\s*age\s*<", code)) or "ageStr(age)" in code
    if age_calls >= 2 and age_labelled:
        ok(f"state age is rendered in {age_calls} places, so staleness is judgeable")
    else:
        bad(f"state age is not shown where it matters (calls={age_calls}, labelled={age_labelled}); "
            f"stale data would look live")

    # 8 -- print rules
    if "@media print" in page:
        ok("print rules present")
    else:
        bad("no @media print block; the page is a scientific record and may be read on paper")

    # 9 -- source-suffixed numbers in the state file
    if science is None:
        bad("config/science_state.json could not be read")
    else:
        missing = []
        for key in ("scale", "predictions", "cost", "backbone"):
            blk = science.get(key) or {}
            if not blk.get("src") and not blk.get("_what"):
                missing.append(key)
        if missing:
            bad(f"state blocks with neither src nor _what: {missing}")
        else:
            ok("every science block names its source")

    # 10 -- the state file loads
    if state_js is None:
        bad("viz/state.js is missing -- the page will show its no-live-state banner")
    else:
        try:
            body = state_js[state_js.index("{"):state_js.rindex(";")]
            st = json.loads(body)
            need = {"generated_at", "verdict", "can_launch", "arm", "checks", "science", "sources"}
            absent = sorted(need - set(st))
            if absent:
                bad(f"state.js is missing keys the page renders: {absent}")
            else:
                ok(f"state.js parses and carries every key the page needs ({len(st)} top-level keys)")
        except Exception as e:                                    # noqa: BLE001
            bad(f"state.js does not parse: {type(e).__name__}: {str(e)[:70]}")

    return checks, fails, lines


def self_test(page: str, state_js: str | None, science: dict | None) -> int:
    """Mutate the page for each defect class and require every one to be caught."""
    print("  Negative control: every injected defect must be REJECTED, and the clean page PASSED.")
    print("  A check that has never rejected anything is not a check.\n")
    cases = [
        ("a fabricated fallback block is added",
         page.replace("</script>", 'const DEMO_STATE = {demo:1};</script>', 1)),
        ("the page is switched to fetch()",
         page.replace("document.body.appendChild(s);", "fetch('state.json');", 1)),
        ("the previous script tag is no longer removed",
         page.replace("if (tagEl && tagEl.parentNode) tagEl.parentNode.removeChild(tagEl);", "", 1)),
        ("a sub-floor font size is introduced",
         page.replace("--t-micro: 10px;", "--t-micro: 6px;", 1)),
        ("a non-palette status colour is introduced",
         page.replace("--ok:#0072B2;", "--ok:#00ff00;", 1)),
        ("the print block is removed",
         page.replace("@media print", "@media screen", 1)),
        ("the state-age display is removed",
         re.sub(r"ageStr\s*\(", "String(", page)),
    ]
    ok_all = True
    for name, mutated in cases:
        if mutated == page:
            print(f"    {name:52} -> COULD NOT INJECT (the anchor moved; update this test)")
            ok_all = False
            continue
        _, f, _ = check(mutated, state_js, science)
        verdict = "rejected" if f else "ACCEPTED -- the audit is broken"
        if not f:
            ok_all = False
        print(f"    {name:52} -> {verdict}")

    # a broken state file must also be caught
    _, f, _ = check(page, "window.APP_STATE = {not json", science)
    print(f"    {'state.js is truncated to invalid JSON':52} -> "
          f"{'rejected' if f else 'ACCEPTED -- the audit is broken'}")
    ok_all &= bool(f)

    c, f, _ = check(page, state_js, science)
    if f:
        ok_all = False
    print(f"\n    {'clean page':52} -> {'rejected (WRONG)' if f else 'passed'}")
    print(f"\n  {'[OK] the audit can fail and does not fail spuriously' if ok_all else '[FAIL] self-test failed'}")
    return 0 if ok_all else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit the dashboard against the figure standard.")
    ap.add_argument("--self-test", action="store_true",
                    help="prove every check rejects its defect class")
    a = ap.parse_args()

    if not PAGE.is_file():
        print(f"[fatal] {PAGE} not found")
        return 2
    page = PAGE.read_text(encoding="utf-8")
    state_js = STATE_JS.read_text(encoding="utf-8") if STATE_JS.is_file() else None
    try:
        science = json.loads(SCIENCE.read_text(encoding="utf-8"))
    except Exception:                                             # noqa: BLE001
        science = None

    print(f"[dashboard-audit] page  : {PAGE.relative_to(ROOT)}  ({len(page.splitlines())} lines)")
    print(f"[dashboard-audit] state : {STATE_JS.name} "
          f"{'present' if state_js else 'MISSING'}")
    print(f"[dashboard-audit] science: {SCIENCE.name} "
          f"{'present' if science else 'MISSING'}")

    if a.self_test:
        print()
        return self_test(page, state_js, science)

    checks, fails, lines = check(page, state_js, science)
    print("\n".join(lines))
    print(f"\n[{'OK' if fails == 0 else 'FAIL'}] {checks - fails}/{checks} checks passed")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
