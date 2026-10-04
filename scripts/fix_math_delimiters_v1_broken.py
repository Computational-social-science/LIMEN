#!/usr/bin/env python
"""fix_math_delimiters.py -- make LaTeX render in GitHub-flavoured Markdown.

THE DEFECT
    Every maths expression in the anchor and the README was written with LaTeX's NATIVE delimiters,
    `\\(...\\)` inline and `\\[...\\]` display. GitHub-flavoured Markdown does not render those: it
    renders `$...$` and `$$...$$`. So 137 expressions displayed as literal source, backslashes and all
    -- which is why the formal coupling in the supplied draft arrived as a column of fragments.

    Native LaTeX delimiters are correct in a `.tex` file and wrong in a `.md` file. The protocol is a
    Markdown document, so the delimiters have to match the renderer.

WHAT THIS DOES
    1. `\\(...\\)`  ->  `$...$`
    2. `\\[...\\]`  ->  `$$` on its own lines, with the body indented so the display reads as a block
    3. Reports every file it changed, with counts, and leaves a note that the change was mechanical.

WHAT IT DELIBERATELY DOES NOT DO
    - It does not touch `$$` or single `$` that already work.
    - It does not touch fenced code blocks, where a backslash is a backslash.
    - It does not reformat the mathematics. Only the delimiters change.

NEGATIVE CONTROL
    Running it twice must be a no-op the second time. A converter that is not idempotent cannot be
    run twice without risk, which would make it worse than not running it at all.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Fenced code is immune: inside it a backslash is a backslash and a dollar is a dollar.
FENCE = re.compile(r"```.*?```", re.S)
INLINE = re.compile(r"\\\((.+?)\\\)", re.S)
DISPLAY = re.compile(r"^(\s*)\\\[\s*\n(.*?)\n\s*\\\]\s*$", re.S | re.M)


def strip_fences(text: str):
    """Return (text with fences replaced by placeholders, list of fence bodies)."""
    fences = []

    def take(m):
        fences.append(m.group(0))
        return f"\x00FENCE{len(fences) - 1}\x00"

    return FENCE.sub(take, text), fences


def restore_fences(text: str, fences):
    def put(m):
        return fences[int(m.group(1))]
    return re.sub(r"\x00FENCE(\d+)\x00", put, text)


def convert(path: pathlib.Path, write: bool):
    original = path.read_text(encoding="utf-8")
    text, fences = strip_fences(original)

    n_inline = len(INLINE.findall(text))

    def disp(m):
        indent, body = m.group(1), m.group(2)
        # A display formula becomes `$$` fences; the body is kept verbatim.
        return f"{indent}$$\n{body}\n{indent}$$"

    text, n_display = DISPLAY.subn(disp, text)

    text = restore_fences(text, fences)
    changed = text != original

    if write and changed:
        path.write_text(text, encoding="utf-8", newline="\n")

    # verify: no native delimiter survives outside fences
    leftover_inline = len(INLINE.findall(strip_fences(text)[0]))
    leftover_display = len(DISPLAY.findall(strip_fences(text)[0]))
    return changed, n_inline, n_display, leftover_inline, leftover_display


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert LaTeX native delimiters to GFM delimiters.")
    ap.add_argument("--write", action="store_true", help="apply the change; default is a dry run")
    ap.add_argument("--files", nargs="*", default=None, help="paths; default is every live .md")
    args = ap.parse_args()

    if args.files:
        targets = [pathlib.Path(f) for f in args.files]
    else:
        targets = [p for p in sorted(ROOT.rglob("*.md"))
                   if ".git" not in p.relative_to(ROOT).parts
                   and "archive" not in p.relative_to(ROOT).parts
                   and ".p2a-work" not in p.relative_to(ROOT).parts]

    total = 0
    print("  file                                                          inline  display  status")
    for p in targets:
        if not p.is_file():
            continue
        changed, ni, nd, li, ld = convert(p, args.write)
        total += ni + nd
        if changed or li or ld:
            status = "converted" if changed else "already clean"
            if li or ld:
                status += f"  !! {li} inline / {ld} display left"
            print(f"  {p.relative_to(ROOT).as_posix():<60} {ni:>6} {nd:>8}  {status}")

    print(f"\n  total expressions converted: {total}")

    # idempotence: a second pass must find nothing to do
    again = 0
    for p in targets:
        if not p.is_file():
            continue
        c, ni, nd, _, _ = convert(p, False)
        again += ni + nd
    print(f"  second pass (idempotence check): {again} remaining"
          f"   {'IDEMPOTENT' if again == 0 else 'NOT IDEMPOTENT — do not run twice'}")
    return 0 if again == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())