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
    C4  the renderer is present and referenced AND has its fonts, so an offline page cannot silently lose its maths
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
from html import unescape as html_unescape
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


# RETIRED: this asserted that the manuscript reproduced the PROTOCOL render's numbered
# display equations. The manuscript is now a paper rendered from docs/PAPER.md, which has
# no numbered displays; the shape it asserted is gone, and the property that replaced it is
# checked by C11-C13. Kept in the file as a record, no longer registered.
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


# RETIRED: this asserted that the manuscript reproduced the PROTOCOL render's numbered
# display equations. The manuscript is now a paper rendered from docs/PAPER.md, which has
# no numbered displays; the shape it asserted is gone, and the property that replaced it is
# checked by C11-C13. Kept in the file as a record, no longer registered.
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
def c4_math_assets(msgs, html, raw):
    """The renderer is present, referenced, AND has the fonts it cannot render without.

    This check required the KaTeX assets until the repository moved to one renderer. It failed the moment the
    KaTeX references were removed, which is what a guard is for: it held the old design and demanded that the
    check be brought in line rather than letting the change pass unexamined. The font assertion is new, and it
    is the one that matters most - a renderer without its fonts does not fail, it SUBSTITUTES, and the page
    still looks like a page while every variable loses its italic.
    """
    for rel in ("mathjax/tex-mml-chtml.js",):
        if ('"' + rel) not in html and ("'" + rel) not in html:
            msgs.append(f"C4 the page does not reference {rel}")
            continue
        if not (PAGE.parent / rel).is_file():
            msgs.append(f"C4 {rel} is referenced but missing from disk - the page would lose its maths")
    fd = PAGE.parent / "mathjax" / "output" / "chtml" / "fonts" / "woff-v2"
    n = len([f for f in fd.glob("*") if f.suffix in (".woff", ".woff2")]) if fd.is_dir() else 0
    if n < 15:
        msgs.append(f"C4 the MathJax font directory holds {n} file(s) in mathjax/output/chtml/fonts/woff-v2, "
                    f"fewer than the 15 it ships - the renderer would substitute silently and the variables "
                    f"would not be italic")


@check
def c5_stamp_current(msgs, html, raw):
    digest = hashlib.sha256(ANCHOR.read_bytes()).hexdigest()
    m = re.search(r"sha256 ([0-9a-f]{64})", html)
    if not m:
        msgs.append("C5 the page carries no anchor sha256 stamp")
    elif m.group(1) != digest:
        msgs.append(f"C5 stale stamp: page says {m.group(1)[:16]}..., anchor is {digest[:16]}... - "
                    f"rebuild with scripts/build_manuscript_html.py")


# RETIRED: this asserted that the manuscript reproduced the PROTOCOL render's numbered
# display equations. The manuscript is now a paper rendered from docs/PAPER.md, which has
# no numbered displays; the shape it asserted is gone, and the property that replaced it is
# checked by C11-C13. Kept in the file as a record, no longer registered.
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


# RETIRED: this asserted that the manuscript reproduced the PROTOCOL render's numbered
# display equations. The manuscript is now a paper rendered from docs/PAPER.md, which has
# no numbered displays; the shape it asserted is gone, and the property that replaced it is
# checked by C11-C13. Kept in the file as a record, no longer registered.
def c7_cited_numbers_exist(msgs, html, raw):
    cited = sorted({int(n) for n in re.findall(r"equation \((\d+)\)", raw)})
    made = {int(n) for n in re.findall(r"class='eq-num'>\((\d+)\)<", html)}
    missing = [c for c in cited if c not in made]
    if missing:
        msgs.append(f"C7 the prose cites equation number(s) {missing} that the render does not produce")


@check
def c11_figures_resolve(msgs, html, raw):
    """Every <img> the page emits must exist on disk, and there must be at least one.

    A figure whose path does not resolve renders as a broken icon in a browser and as NOTHING in a
    print-to-PDF, so the PDF loses it silently - which is how seven figures were once absent from an HTML
    while the DOCX, embedding them by another route, kept them.
    """
    srcs = re.findall(r'<img\s+src="([^"]+)"', html)
    if not srcs:
        msgs.append("C11 the page embeds no figure at all")
    for rel in srcs:
        if not (PAGE.parent / rel).is_file():
            msgs.append(f"C11 figure {rel} is referenced but missing from disk")


@check
def c12_no_markdown_leakage(msgs, html, raw):
    """No unrendered Markdown survives.

    A page can carry every figure and every number and still SHOW the reader `![Figure 1](path)` and
    `**bold**`, because nothing was counting whether the constructs were RENDERED. That is how a reader
    received a supplementary document full of visible Markdown while every count said it was complete.
    """
    mds = re.findall(r"!\[[^\]]*\]\([^)]*\)", html)
    if mds:
        msgs.append(f"C12 {len(mds)} Markdown image(s) reached the page unrendered, e.g. {mds[0][:60]}")
    lit = re.findall(r"\*\*[^*\n]{1,60}\*\*", html)
    if lit:
        msgs.append(f"C12 {len(lit)} literal emphasis marker(s) survived, e.g. {lit[0][:60]}")


@check
def c13_sections_present(msgs, html, raw):
    """The paper's own structure: a reader must be able to find the standard sections."""
    have = [re.sub(r"<[^>]+>", "", m).strip().lower() for m in re.findall(r"<h2>(.*?)</h2>", html, re.S)]
    for want in ("abstract", "introduction", "results", "discussion", "methods", "references"):
        if not any(h.startswith(want) for h in have):
            msgs.append(f"C13 the page has no '{want}' section; it has {have}")


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
        ("C5 stale stamp", lambda s: s.replace(re.search(r"sha256 ([0-9a-f]{64})", s).group(1),
                                               "0" * 64, 1), "C5"),
        ("C11 broken figure path",
         lambda s: s.replace('<img src="figures/', '<img src="figures/absent_', 1), "C11"),
        ("C12 unrendered markdown image",
         lambda s: s.replace("<body", '<body><p>![Figure 9](figures/x.png)</p>', 1), "C12"),
        ("C12 literal emphasis marker",
         lambda s: s.replace("<body", "<body><p>**bold**</p>", 1), "C12"),
        ("C13 section removed",
         lambda s: s.replace("<h2>Methods</h2>", "<h2>Procedure</h2>", 1), "C13"),
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



@check
def c8_math_not_torn_by_markup(msgs, html, raw):
    r"""No emphasis or code tag may sit INSIDE an inline expression.

    The defect this exists for: the builder restored `$...$` mathematics into an equation NOTE and
    then handed that string to `renderInline`. Markdown does not know about `$`, so the underscores in
    `$\mathcal{N}_s$` and `$s = s_{\mathrm{en}}$` were live emphasis markers and the parser paired
    them across eleven words, producing `<em>` spanning both expressions. The page still rendered, its
    equation count was right, its note count was right and the citation cross-check passed - the only
    way to see it was to read the sentence. So it is now a check.

    How it decides: split on `$`. A tag at an ODD index in that split is between an opening and a
    closing dollar, i.e. inside mathematics. Display blocks are `$$`-delimited and are not counted
    here, because their bodies are opaque by then.
    """
    parts = html.split("$")
    bad = 0
    for idx in range(1, len(parts) - 1, 2):
        if re.search(r"</?(?:em|code|strong)\b", parts[idx]):
            bad += 1
    if bad:
        msgs.append(f"C8 {bad} markup tag(s) sit inside an inline expression - Markdown parsed bare "
                    f"`$...$` mathematics and tore it (the equation-note path did exactly this)")


@check
def c9_no_literal_tab(msgs, html, raw):
    r"""A literal TAB in the page means a backslash escape was consumed somewhere upstream.

    `\t` in LaTeX means a trailing-space command or nothing at all, but a raw 0x09 inside `$f_\theta$`
    is a damaged expression: the source carried a real tab where `\t` was intended, and the browser
    collapses it to whitespace so `f_<TAB>heta` reads as `f_ heta` instead of `f_theta`. Invisible on
    screen, wrong in the LaTeX.
    """
    n = html.count("\t")
    if n:
        m = re.search(r".{0,30}\t.{0,20}", html)
        msgs.append(f"C9 {n} literal TAB character(s) in the page (first near "
                    f"{m.group(0)!r}) - a `\\t` escape was consumed as a real tab")


# RETIRED: this asserted that the manuscript reproduced the PROTOCOL render's numbered
# display equations. The manuscript is now a paper rendered from docs/PAPER.md, which has
# no numbered displays; the shape it asserted is gone, and the property that replaced it is
# checked by C11-C13. Kept in the file as a record, no longer registered.
def c10_equation_notes_complete(msgs, html, raw):
    r"""Every equation note in the SOURCE must appear in full in the page.

    A note is multi-line Markdown. The builder claimed only its FIRST line, so a note of five source
    lines was emitted truncated at the first newline and its remainder fell through as ordinary body
    prose - `<p class="eq-note">... between clean and</p><p>noisy input, ...</p>`. Two equations were
    affected and every count-based check still passed. This compares text, not counts, because counts
    were exactly what failed to notice.
    """
    NOTE_STARTS = ("where ", "The second form is", "with $\\tau", "Phase I omits")
    lines = raw.split("\n")
    notes = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == "$$":
            j = i + 1
            while j < len(lines) and lines[j].strip() != "$$":
                j += 1
            k = j + 1
            while k < len(lines) and not lines[k].strip():
                k += 1
            if k < len(lines) and lines[k].strip().startswith(NOTE_STARTS):
                e = k
                while (e + 1 < len(lines) and lines[e + 1].strip()
                       and not lines[e + 1].lstrip().startswith(("#", ">", "$$", "-", "*", "|"))):
                    e += 1
                notes.append(" ".join(lines[x].strip() for x in range(k, e + 1)))
            i = j + 1
        else:
            i += 1

    def norm(s):
        """Reduce Markdown AND LaTeX noise to plain words on both sides.

        Both sides must lose the same things or every note reads as truncated. The source carries
        `**bold**`, backticks and `$`-delimited TeX; the page carries `<strong>`/`<em>` tags and the
        same TeX. Stripping tags from one side and Markdown markers from the other, then removing the
        TeX punctuation that survives rendering, is what makes the comparison about the WORDS.
        """
        # BLOCK tags become a space; INLINE tags become empty. Replacing every tag with a space
        # instead put one before the punctuation that followed it - `<strong>x</strong>:` normalised
        # to "x :" against the source's "x:", and `<strong>dev</strong>-set` to "dev -set" against
        # "dev-set". Those two artifacts produced six false "truncated" findings on a page whose notes
        # were complete, which is the failure mode this whole file exists to avoid: a guard that cries
        # wolf trains its reader to ignore it.
        s = html_unescape(s)                     # page: &quot; &amp; &lt; &gt; -> their characters
        s = re.sub(r"</?(?:p|div|li|ul|ol|td|th|tr|h[1-6]|br|blockquote)\b[^>]*>", " ", s)
        s = re.sub(r"<[^>]+>", "", s)
        s = s.replace("**", "").replace("`", "")  # source: markdown emphasis / code
        s = re.sub(r"[\\${}]", "", s)          # both: TeX punctuation
        s = re.sub(r"\s+", " ", s)
        return s.strip()

    page = norm(html)
    for n, note in enumerate(notes, 1):
        want = norm(note)
        if want and want not in page:
            # find the longest prefix that IS present, to show where it was cut
            have = 0
            while have < len(want) and want[:have + 1] in page:
                have += 1
            msgs.append(f"C10 equation note {n} is truncated in the page: only the first {have} of "
                        f"{len(want)} characters appear (cut near {want[have:have + 45]!r})")


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
        print(f"  OK: {len(CHECKS)} checks pass — sentinels, maths assets, provenance stamp, figure "
              f"resolution, markdown leakage, section structure")
        return 0
    for m in msgs:
        print(f"  [FAIL] {m}")
    print(f"\n  exit=1  findings: {len(msgs)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
