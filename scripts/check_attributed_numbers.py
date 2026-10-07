#!/usr/bin/env python
"""check_attributed_numbers.py -- a value this project MEASURED may not be written as one it QUOTED.

WHY THIS EXISTS, AND THE EXACT FAILURE IT WAS WRITTEN FOR
    The manuscript's noise levels are anchored on a value, 0.4480, and five places across four documents said
    the anchor was "a published human result ... the interior-scrambled condition of Rayner et al. (2006), IN
    WHICH READERS RECOVERED THE INTENDED WORD 0.4480 OF THE TIME".

    Rayner et al. never reported that number. The project's own source says so outright:

        scripts/o1_recoverability.py:
            # This is the MEASURED value of that condition UNDER THIS INDEX (interior-scrambled variant,
            # the harsher of the two), and it is what `lo` has to clear.
            RAYNER_ANCHOR_MEAN_R = 0.4480

    0.4480 is what THIS project's recoverability index returns when applied to a published stimulus
    MANIPULATION. A number produced here was carried into the manuscript wearing the authority of a published
    human result - and it was load-bearing, because the anchor selects lambda_lo and lambda_mid. It was found
    by opening the cited work and reading its record, which is not a mechanism.

WHAT IS CHECKED, AND WHY THE SCOPE IS THIS NARROW
    Matching numbers to constants by VALUE does not work: of 27 candidate co-occurrences in this repository,
    all but one were collisions on small values (`0.05` against a significance level, `0.000` against a
    temperature). A check built on that produces mostly noise and gets disabled.

    The signal is in the DECLARATION, not the value. A constant is "anchor-shaped" when the comment above it
    cites an external work - a year in parentheses, a journal, "published", "anchor", "reported". Such a
    constant is a promise about WHERE a number came from, and the check asks only that the documents quoting
    the value say which side of that promise they are on.

    A quotation must carry an ATTRIBUTION MARKER in the same sentence: that the value is this index's reading
    of an external manipulation ("under this index", "measured here"), or explicitly not the source's number
    ("not a number quoted"). Without one, a reader attributes the value to the cited work.

EXIT
    0  every quoted anchor value says where it came from        1  at least one does not
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# A constant whose declaration is annotated as anchored to an external source.
ANCHOR_NAME = re.compile(r"^([A-Z][A-Z0-9_]{3,})\s*=\s*(-?\d+\.?\d*)\s*$")
EXTERNAL_HINT = re.compile(
    r"\((?:19|20)\d{2}\)|Psychological Science|Nature|arXiv|doi:|published|anchor|reported|"
    r"Rayner|Green|Swets|Shannon|Wiener", re.I)
COMMENT_LOOKBACK = 10          # lines of comment above the declaration

# Distinctive enough to identify: at least three decimals, so `0.05` cannot collide with a significance level.
DISTINCTIVE = re.compile(r"^-?\d+\.\d{3,}$")

# A quotation must say which side of the promise it is on.
MARKER = re.compile(
    r"under this index|measured under|measured here|this index|measured on|this paper'?s own|"
    r"not a number quoted|value this paper|computed here|our own index", re.I)

DOC_GLOBS = ("docs/**/*.md", "protocol/*.md", "*.md")

# EXCLUSIONS, STATED RATHER THAN SILENT - an unchecked document is not a pass, and the run prints this list.
EXCLUDED = {
    "docs/REFERENCE_AUDIT.md":
        "it QUOTES the misattribution verbatim as the record of the defect; the quotation is the evidence, "
        "not a repetition of the error",
    # THE PROTOCOL IS THE PINNED ANCHOR. Editing it changes its sha256, which is a RE-PIN - a governance act
    # with a version bump, not a prose fix, and it is recorded here as a KNOWN OPEN FINDING rather than
    # quietly corrected. Its lines 60 and 949 still say the anchor is 'published', which the corrected
    # attribution above shows is imprecise for the VALUE (the manipulation is published; the number is ours).
    "protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md":
        "PINNED BY CONTENT DIGEST - correcting it requires a version bump and a re-pin, which is a governance "
        "decision; held open deliberately and visible in this run",
}


def anchor_constants() -> dict[str, list[tuple[str, int, str]]]:
    """value -> [(file, line, constant name)] for every anchor-shaped declaration."""
    out: dict[str, list[tuple[str, int, str]]] = {}
    for f in sorted((REPO_ROOT / "scripts").glob("*.py")):
        lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
        for i, line in enumerate(lines):
            m = ANCHOR_NAME.match(line)
            if not m or not DISTINCTIVE.match(m.group(2)):
                continue
            above = "\n".join(lines[max(0, i - COMMENT_LOOKBACK):i])
            if EXTERNAL_HINT.search(above):
                out.setdefault(m.group(2), []).append((f.name, i + 1, m.group(1)))
    return out


def quoted(value: str) -> list[tuple[str, int, str]]:
    """(document, line number, the line) for every place a document writes this value."""
    out: list[tuple[str, int, str]] = []
    for pattern in DOC_GLOBS:
        for f in sorted(REPO_ROOT.glob(pattern)):
            rel = f.relative_to(REPO_ROOT).as_posix()
            if rel.startswith(("archive/", ".git/")) or "/archive/" in rel:
                continue
            if rel in EXCLUDED:
                continue
            try:
                text = f.read_text(encoding="utf-8")
            except Exception:
                continue
            # JOIN WRAPPED LINES BEFORE TESTING. A sentence in this repository's prose routinely spans two
            # physical lines, and the first version of this check tested the physical line - so a corrected
            # sentence whose attribution marker fell after the wrap was still reported as unattributed. The
            # marker belongs to the SENTENCE, and the unit of the test has to match the unit of the claim.
            # A line starting with a markdown structure character begins a new block; anything else continues.
            blocks: list[tuple[int, str]] = []
            for i, raw in enumerate(text.splitlines(), 1):
                if blocks and raw.strip() and not re.match(r"^\s*(#|\||>|-|\d+\.|\*\s|\*\*)", raw):
                    blocks[-1] = (blocks[-1][0], blocks[-1][1] + " " + raw.strip())
                else:
                    blocks.append((i, raw.strip()))
            for i, line in blocks:
                if re.search(rf"(?<![\d.]){re.escape(value)}(?![\d])", line):
                    out.append((rel, i, line))
    return out


def scan() -> tuple[int, list[str]]:
    anchors = anchor_constants()
    findings: list[str] = []
    checked = 0
    for value, sites in sorted(anchors.items()):
        for rel, ln, line in quoted(value):
            checked += 1
            if not MARKER.search(line):
                where = "; ".join(f"{f}:{i} {n}" for f, i, n in sites)
                findings.append(
                    f"{rel}:{ln} quotes {value} beside an external source and does not say where it came "
                    f"from; declared at {where} as MEASURED HERE. Say so, or the reader attributes it to the "
                    f"cited work.")
    return checked, findings


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--negative-test", action="store_true",
                    help="append a marker-free quotation of an anchor value, require this check to fail")
    args = ap.parse_args()

    if args.negative_test:
        probe = REPO_ROOT / "docs" / "_negative_control_attribution.md"
        anchors = anchor_constants()
        if not anchors:
            print("  [FAIL] no anchor constants declared; a check with nothing to check passes vacuously")
            return 1
        value = sorted(anchors)[-1]
        probe.write_text(f"The value {value} comes from a published human result.\n", encoding="utf-8")
        try:
            rc = subprocess.run([sys.executable, __file__], capture_output=True, text=True).returncode
        finally:
            probe.unlink(missing_ok=True)
        if rc == 0:
            print("  [FAIL] negative control was NOT caught - the check cannot fail and proves nothing")
            return 1
        print("  [OK]   negative control: an unattributed quotation of an anchor value -> FAILS as required")
        return 0

    anchors = anchor_constants()
    if not anchors:
        print("  [FAIL] no anchor-shaped constant found; the check has nothing to compare against")
        return 1
    print(f"  anchor-shaped constants: {len(anchors)}  "
          f"({', '.join(f'{v} <- {s[0][0]}:{s[0][2]}' for v, s in sorted(anchors.items()))})")
    checked, findings = scan()
    print(f"  quotations examined: {checked}")
    for rel, why in EXCLUDED.items():
        print(f"      (excluded: {rel} - {why[:96]}...)")
    if findings:
        print(f"\n  [FAIL] {len(findings)} attribution finding(s):")
        for x in findings[:10]:
            print(f"      {x}")
        print("\n  A value this project MEASURED, written as one it QUOTED, is the same defect as a kernel")
        print("  name with no theorem behind it: a source assertion with nothing on the other end.")
        return 1
    print("\n  [OK] every quotation of an anchored value states where the value came from")
    return 0


if __name__ == "__main__":
    sys.exit(main())
