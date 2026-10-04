#!/usr/bin/env python
"""fix_math_delimiters.py -- make LaTeX render in GitHub-flavoured Markdown.

THE DEFECT
    Every maths expression in the anchor and the README was written with LaTeX's NATIVE delimiters,
    inline backslash-paren and display backslash-bracket. GitHub-flavoured Markdown does not render
    those: it renders `$...$` and `$$...$$`. So 145 expressions displayed as literal source,
    backslashes and all - which is why the formal coupling arrived as a column of fragments.

    Native LaTeX delimiters are correct in a `.tex` file and wrong in a `.md` file. The protocol is a
    Markdown document, so the delimiters must match the renderer.

WHY A REGEX IS NOT ENOUGH, AND WHAT IS USED INSTEAD
    An expression such as inline(`Acc`) with a nested `(\lambda)` inside it is split in half by any
    pattern that stops at the first closing delimiter: the left half is converted, the right half is
    left behind, and the stray closing delimiter then reads as the start of the next expression. A
    regex converter therefore CORRUPTS the file and is not idempotent. The first version of this
    script did exactly that and was caught by its own second-pass check.

    Delimiters are consequently located by SCANNING for the literal two-character tokens and COUNTING
    parentheses, so a nested group cannot terminate an expression.

WHAT IT DELIBERATELY DOES NOT DO
    - It does not touch `$` or `$$` that already work.
    - It does not touch fenced code blocks, where a backslash is a backslash and a dollar a dollar.
    - It does not reformat the mathematics. Only the delimiters change.

IDEMPOTENCE
    Running it twice must be a no-op the second time. A converter that is not idempotent cannot be run
    twice without risk, which would make it worse than not running it at all - so the second pass is
    computed on every run and a non-zero result is an error exit.
"""
from __future__ import annotations

import argparse
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

FENCE = re.compile(r"```.*?```", re.S)

# Built from parts so this file does not match its own scanner.
OPEN_INLINE = chr(92) + "("
CLOSE_INLINE = chr(92) + ")"
OPEN_DISPLAY = chr(92) + "["
CLOSE_DISPLAY = chr(92) + "]"

# A display formula is its own line pair with the body between. Built with explicit escapes rather
# than a run of backslashes: the first version wrote four of them, which matches TWO literal
# backslashes, and the document contains one - so the pattern matched nothing and reported
# "0 display converted" while eight were sitting there unconverted.
DISPLAY_OPEN = re.compile(r"^[ \t]*" + re.escape(OPEN_DISPLAY) + r"[ \t]*\n", re.M)
DISPLAY = re.compile(r"^([ \t]*)" + re.escape(OPEN_DISPLAY) + r"[ \t]*\n(.*?)\n[ \t]*"
                     + re.escape(CLOSE_DISPLAY) + r"[ \t]*$", re.S | re.M)


def _tok(text: str, i: int) -> str:
    """The two-character delimiter starting at i, or '' when there is none."""
    return text[i:i + 2] if text[i] == chr(92) else ""


def scan_inline(text: str):
    """(start, end_exclusive, body) for every balanced inline expression."""
    out = []
    i, n = 0, len(text)
    while i < n - 1:
        if _tok(text, i) == OPEN_INLINE:
            depth = 0
            j = i + 2
            closed = False
            while j < n - 1:
                two = _tok(text, j)
                if two == CLOSE_INLINE:
                    if depth == 0:
                        out.append((i, j + 2, text[i + 2:j]))
                        i = j + 2
                        closed = True
                        break
                    depth -= 1
                    j += 2
                    continue
                if two == OPEN_INLINE:
                    depth += 1
                    j += 2
                    continue
                j += 1
            if not closed:
                i += 1
        else:
            i += 1
    return out


def convert_inline(text: str):
    spans = scan_inline(text)
    if not spans:
        return text, 0
    parts, last = [], 0
    for a, b, body in spans:
        parts.append(text[last:a])
        parts.append("$" + body.strip() + "$")
        last = b
    parts.append(text[last:])
    return "".join(parts), len(spans)


def _split_fences(text: str):
    fences = []

    def take(m):
        fences.append(m.group(0))
        return "\x00F%d\x00" % (len(fences) - 1)

    return FENCE.sub(take, text), fences


def _put_fences(text: str, fences):
    return re.sub(r"\x00F(\d+)\x00", lambda m: fences[int(m.group(1))], text)


def _display(m):
    indent, body = m.group(1), m.group(2)
    return "{0}$$\n{1}\n{0}$$".format(indent, body)


def convert(path: pathlib.Path, write: bool):
    original = path.read_text(encoding="utf-8")
    text, fences = _split_fences(original)

    text, n_inline = convert_inline(text)
    text, n_display = DISPLAY.subn(_display, text)

    text = _put_fences(text, fences)
    changed = text != original
    if write and changed:
        path.write_text(text, encoding="utf-8", newline="\n")

    probe, _ = _split_fences(text)
    return changed, n_inline, n_display, len(scan_inline(probe)), len(DISPLAY.findall(probe))


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert LaTeX native delimiters to GFM delimiters.")
    ap.add_argument("--write", action="store_true", help="apply the change; default is a dry run")
    ap.add_argument("--files", nargs="*", default=None)
    args = ap.parse_args()

    if args.files:
        targets = [pathlib.Path(f) for f in args.files]
    else:
        targets = [p for p in sorted(ROOT.rglob("*.md"))
                   if ".git" not in p.relative_to(ROOT).parts
                   and "archive" not in p.relative_to(ROOT).parts
                   and ".p2a-work" not in p.relative_to(ROOT).parts]

    print("  file                                                            inline  display  status")
    total = 0
    for p in targets:
        if not p.is_file():
            continue
        changed, ni, nd, li, ld = convert(p, args.write)
        total += ni + nd
        if changed or li or ld:
            status = "converted" if changed else "already clean"
            if li or ld:
                status += "   !! {0} inline / {1} display left".format(li, ld)
            print("  {0:<64} {1:>6} {2:>8}  {3}".format(p.relative_to(ROOT).as_posix(), ni, nd, status))

    print("\n  total expressions converted: {0}".format(total))

    again = 0
    for p in targets:
        if p.is_file():
            _, ni, nd, _, _ = convert(p, False)
            again += ni + nd
    print("  second pass (idempotence): {0} remaining   {1}".format(
        again, "IDEMPOTENT" if again == 0 else "NOT IDEMPOTENT"))
    return 0 if again == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())