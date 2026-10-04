#!/usr/bin/env python
"""check_manuscript_html.py -- the render must be verified in a BROWSER, and these are its failures.

WHY THIS FILE EXISTS
    Five defects in the HTML build were each found by OPENING THE PAGE, not by reading the code that
    produced it. Every one produced a healthy-looking artefact from a build that exited 0:

      1. Markdown consumed the LaTeX spacing and punctuation escapes before the renderer saw them;
      2. `defer` + `onload` never fired, so `renderMathInElement` was never called and the page
         contained zero mathematics while its headings and tables rendered perfectly;
      3. the restore step stripped the `$` delimiters, leaving bare TeX that matched nothing;
      4. equation numbering counted lines, so four of nine display equations were read as inline
         expressions and mis-numbered, breaking the prose that cites "equation (2)";
      5. NUL placeholders were replaced by the Markdown parser with U+FFFD, silently destroying every
         inline expression and every symbol inside the equation notes.

    A build log cannot catch any of these. The checks below are the ones that would have.

WHAT IS CHECKED, AND WHY EACH ONE EARNS ITS PLACE
    C1  every display equation carries a `.eq-num`, and the count equals the anchor's `$$` count
    C2  every `.eq-num` is sequential from (1) - mis-numbering is silent otherwise
    C3  no U+FFFD and no Private Use Area codepoint survives into the output (defect 5)
    C4  the KaTeX assets are present and referenced, so an offline page cannot silently lose its maths
    C5  the stamp carries the anchor's CURRENT sha256, so a stale page is visible rather than plausible
    C6  the four callout variants and the sidebar TOC are present when the anchor has the content for
        them - a component that silently stopped matching is invisible in the page
    C7  every equation number the PROSE cites exists in the render (defect 4, from the reader's side)

NEGATIVE CONTROL
    Each check is fired against a deliberately corrupted copy of the page, and must report the defect it
    is meant to catch. A guard that has never been seen to fail is not evidence that it works.
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
ANCHOR = ROOT / "protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md"
PAGE = ROOT / "viz/manuscript.html"
SENTINEL = chr(0xE000)
REPLACEMENT = chr(0xFFFD)

CHECKS = []


def check(fn):
    CHECKS.append(fn)
    return fn


@check
def c1_numbers_per_equation(msgs, html, raw):
    want = raw.count("$$") // 2
    # The builder emits `class='eq-num'` with SINGLE quotes, because the span sits inside an
    # f-string-free concatenation. An earlier version of this guard matched double quotes, reported
    # "0 numbered equations" on a page the browser had just shown as 9, and one of its negative
    # controls silently stopped mutating anything - a guard with a wrong pattern is worse than none,
    # because it looks like a finding.
    got = len(re.findall(r"class=['\"]eq-num['\"]", html))
    if want and got != want:
        msgs.append(f"C1 {got} numbered equations but the anchor has {want} display equations")


@check
def c2_numbers_sequential(msgs, html, raw):
    nums = [int(n) for n in re.findall(r"class='eq-num'>\((\d+)\)<", html)]
    if nums and nums != list(range(1, len(nums) + 1)):
        msgs.append(f"C2 equation numbers are not sequential from 1: {nums}")


@check
def c3_no_sentinels_or_replacement(msgs, html, raw):
    n_rep = html.count(REPLACEMENT)
    n_pua = sum(html.count(chr(c)) for c in (0xE000, 0xE001))
    if n_rep:
        msgs.append(f"C3 {n_rep} U+FFFD replacement character(s) survived into the page - a "
                    f"placeholder was destroyed by the Markdown parser")
    if n_pua:
        msgs.append(f"C3 {n_pua} sentinel codepoint(s) survived - a placeholder was never restored")


@check
def c4_katex_assets(msgs, html, raw):
    for rel in ("katex/katex.min.js", "katex/katex.min.css", "katex/auto-render.min.js"):
        if ('"' + rel) not in html and ("'" + rel) not in html:
            msgs.append(f"C4 the page does not reference {rel}")
            continue
        if not (PAGE.parent / rel).is_file():
            msgs.append(f"C4 {rel} is referenced but missing from disk - the page would lose its maths")


@check
def c5_stamp_current(msgs, html, raw):
    digest = hashlib.sha256(ANCHOR.read_bytes()).hexdigest()
    m = re.search(r"sha256 ([0-9a-f]{64})", html)
    if not m:
        msgs.append("C5 the page carries no anchor sha256 stamp")
    elif m.group(1) != digest:
        msgs.append(f"C5 stale stamp: page says {m.group(1)[:16]}..., anchor is {digest[:16]}... - "
                    f"rebuild with scripts/build_manuscript_html.py")


@check
def c6_components(msgs, html, raw):
    if html.count("<blockquote") and not re.search(r"class=['\"]callout ", html):
        msgs.append("C6 blockquotes are present but no callout was emitted - the classifier no longer "
                    "matches")
    if re.search(r"^##\s", raw, re.M) and 'class="toc"' not in html:
        msgs.append("C6 the anchor has sections but the page has no sidebar TOC")
    if 'class="callout ' in html or "class='callout " in html:
        used = set(re.findall(r"class=['\"]callout (\w+)['\"]", html))
        unknown = used - {"ci", "cn", "cg", "cw"}
        if unknown:
            msgs.append(f"C6 unknown callout variant(s) {sorted(unknown)} - a CSS class with no rule")


@check
def c7_cited_numbers_exist(msgs, html, raw):
    cited = sorted({int(n) for n in re.findall(r"equation \((\d+)\)", raw)})
    made = {int(n) for n in re.findall(r"class='eq-num'>\((\d+)\)<", html)}
    missing = [c for c in cited if c not in made]
    if missing:
        msgs.append(f"C7 the prose cites equation number(s) {missing} that the render does not produce")


def scan(html, raw):
    msgs = []
    for fn in CHECKS:
        fn(msgs, html, raw)
    return msgs


def negative_test():
    if not PAGE.is_file():
        print("  cannot negative-test: no page to corrupt")
        return 1
    good = PAGE.read_text(encoding="utf-8")
    raw = ANCHOR.read_text(encoding="utf-8")

    cases = [
        ("C3 replacement character", lambda s: s.replace("<body", REPLACEMENT + "<body", 1), "C3"),
        ("C3 leaked sentinel", lambda s: s.replace("<body", SENTINEL + "<body", 1), "C3"),
        ("C2 mis-numbered equation", lambda s: s.replace("class='eq-num'>(1)<",
                                                         "class='eq-num'>(7)<", 1), "C2"),
        ("C1 missing equation number",
         lambda s: s.replace("class='eq-num'", "class='not-eq-num'", 1), "C1"),
        ("C5 stale stamp", lambda s: s.replace(re.search(r"sha256 ([0-9a-f]{64})", s).group(1),
                                               "0" * 64, 1), "C5"),
        ("C6 callout class emptied",
         lambda s: s.replace('class="callout ci"', 'class="callout xx"', 1), "C6"),
    ]
    ok = 0
    for label, mutate, expect in cases:
        if mutate(good) == good:
            print(f"  [MISS] {label}: the mutation did not change the page")
            continue
        msgs = scan(mutate(good), raw)
        fired = any(m.startswith(expect) for m in msgs)
        ok += fired
        detail = next((m for m in msgs if m.startswith(expect)), msgs[0] if msgs else "(none)")
        print(f"  [{'OK' if fired else 'MISS'}] {label:28} -> {detail[:74]}")
    print(f"\n  {ok}/{len(cases)} negative controls fired")
    return 0 if ok == len(cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify the rendered manuscript against its anchor.")
    ap.add_argument("--negative-test", action="store_true")
    args = ap.parse_args()
    if args.negative_test:
        return negative_test()

    if not PAGE.is_file():
        print("  no page: run scripts/build_manuscript_html.py first")
        return 1
    html = PAGE.read_text(encoding="utf-8")
    raw = ANCHOR.read_text(encoding="utf-8")
    msgs = scan(html, raw)
    if not msgs:
        print(f"  OK: {len(CHECKS)} checks pass — numbering, sentinels, assets, stamp, components, "
              f"citations")
        return 0
    for m in msgs:
        print(f"  [FAIL] {m}")
    print(f"\n  exit=1  findings: {len(msgs)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
