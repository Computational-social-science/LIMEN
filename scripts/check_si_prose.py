"""A paragraph written at 110 columns ships as a dozen broken paragraphs.

The renderer joins nothing: a blank line ends a paragraph, and any other newline is a paragraph break. So a
source file authored with wrapped lines delivers its emphasis split across the break - `**12.1
points**` - and
the page shows literal `**` and, next to it, raw `$...$`. Two sections were authored that way, one of them
AFTER the same defect had already been found and fixed in another, which is the reason this is a check and not
another careful note to self.

Rule: one paragraph, one line. Lists, tables, headings, block quotes and fenced code are exempt.

NEGATIVE CONTROL: a wrapped paragraph is written to a scratch file in the same directory and must be reported.
"""
from __future__ import annotations
import argparse, pathlib, re, sys

SPECIAL = re.compile(r"^\s*(#|\||[-*+]\s|\d+\.\s|```|>)")


def wrapped(text: str) -> list[tuple[int, str]]:
    """Return (line number, text) for paragraphs that span more than one line.

    The CONTENTS BLOCK is exempt by name. It is an index in which one entry per line is the correct form - the
    opposite of the prose rule - so it would otherwise be reported on every run and the guard would be turned
    off, which is how a real signal gets lost.
    """
    # blank out the contents index, preserving line count so reported numbers stay true
    lines = text.splitlines()
    try:
        start = next(n for n, l in enumerate(lines) if l.strip() == "## Contents")
        stop = next((n for n in range(start + 1, len(lines)) if lines[n].strip() == "---"), len(lines))
        lines = lines[:start + 1] + [""] * (stop - start - 1) + lines[stop:]
        text = "\n".join(lines)
    except StopIteration:
        pass

    bad, buf, in_code = [], [], False
    start = 0
    def flush():
        nonlocal buf
        if len(buf) > 1:
            bad.append((start, buf[0].strip()[:70]))
        buf = []
    for n, l in enumerate(text.splitlines(), 1):
        if l.strip().startswith("```"):
            flush(); in_code = not in_code; continue
        if in_code:
            continue
        if not l.strip():
            flush(); continue
        if SPECIAL.match(l):
            flush(); continue
        if not buf:
            start = n
        buf.append(l)
    flush()
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--no-negative-control", action="store_true")
    args = ap.parse_args(argv)
    root = pathlib.Path(args.root).resolve()
    files = sorted((root / "docs" / "si").glob("*.md")) + [root / "docs" / "SUPPLEMENTARY_INFORMATION.md"]
    total, findings = 0, []
    for f in files:
        if not f.exists():
            continue
        total += 1
        for n, line in wrapped(f.read_text(encoding="utf-8")):
            findings.append(f"{f.name}:{n} paragraph continues past its first line - {line!r}")
    print(f"  SI sources checked for wrapped paragraphs: {total}")

    if not args.no_negative_control:
        probe = root / "docs" / "si" / "__wrap_negative_control__.md"
        probe.write_text("## X. probe\n\nA paragraph that keeps\ngoing on the next line.\n", encoding="utf-8")
        try:
            fired = bool(wrapped(probe.read_text(encoding="utf-8")))
            print(f"  negative control: injected wrapped paragraph -> {'FAILS as required' if fired else 'NOT DETECTED'}")
            if not fired:
                findings.append("negative control did not fire: a wrapped paragraph was not detected")
        finally:
            probe.unlink(missing_ok=True)

    if findings:
        print(f"\n  [FAIL] {len(findings)} wrapped paragraph(s):")
        for f in findings[:12]:
            print(f"      {f}")
        return 1
    print("\n  [OK] every paragraph in every SI source is a single line, and the check fails on one that is not")
    return 0


if __name__ == "__main__":
    sys.exit(main())
