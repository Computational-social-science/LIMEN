#!/usr/bin/env python
"""check_math_renders.py -- LaTeX must use the delimiters the RENDERER understands.

    "Every maths expression in this repository was written with LaTeX's NATIVE delimiters, inline
     backslash-paren and display backslash-bracket. GitHub-flavoured Markdown does not render those.
     145 expressions displayed as literal source -- which is why the formal coupling arrived as a
     column of fragments. Native delimiters are correct in a .tex file and wrong in a .md file."

    A renderer difference is invisible in a text editor: the file reads correctly and renders wrong. So
    the property is checked mechanically, and the converter that fixed it ships alongside, so the fix is
    repeatable rather than a one-off edit.

CHECKS
  M  no native delimiter survives in any live Markdown file (outside fenced code)
  $  every `$$` display fence is balanced
  I  the converter is exhausted on the current tree, so re-running it cannot change anything

NEGATIVE CONTROL
  A file containing a native delimiter must be reported, and removing it must clear the report.
"""
from __future__ import annotations

import argparse
import importlib.util
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

OPEN_I = chr(92) + "("
CLOSE_I = chr(92) + ")"
OPEN_D = chr(92) + "["
CLOSE_D = chr(92) + "]"

FENCE = re.compile(r"```.*?```", re.S)
NEWLINE = chr(10)


def live_md():
    for p in sorted(ROOT.rglob("*.md")):
        rel = p.relative_to(ROOT)
        if any(x in rel.parts for x in (".git", "archive", ".p2a-work", "node_modules")):
            continue
        yield p


def strip_fences(text):
    return FENCE.sub(lambda m: NEWLINE * m.group(0).count(NEWLINE), text)


def scan(msgs):
    for p in live_md():
        rel = p.relative_to(ROOT).as_posix()
        try:
            body = strip_fences(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for tok, label in ((OPEN_I, "inline"), (OPEN_D, "display")):
            n = body.count(tok)
            if n:
                lines = [i for i, l in enumerate(body.splitlines(), 1) if tok in l][:5]
                msgs.append((label,
                             f"{rel} carries {n} native LaTeX {label} delimiter(s), first at "
                             f"line(s) {lines}; GFM wants $ inline and $$ display"))
        markers = len(re.findall(r"^[ \t]*[$][$][ \t]*$", body, re.M))
        if markers % 2:
            msgs.append(("fence", f"{rel} has an unbalanced $$ display fence ({markers} markers)"))


def converter_exhausted(msgs):
    spec = importlib.util.spec_from_file_location("fx", ROOT / "scripts/fix_math_delimiters.py")
    if spec is None or spec.loader is None:
        msgs.append(("idempotence", "the converter could not be loaded, so idempotence is UNKNOWN"))
        return
    fx = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fx)
    total = 0
    for p in live_md():
        _, ni, nd, _, _ = fx.convert(p, False)
        total += ni + nd
    if total:
        msgs.append(("idempotence",
                     f"{total} native delimiter(s) would still be converted - the tree is not in "
                     f"the state the converter produces"))


def main() -> int:
    ap = argparse.ArgumentParser(description="LaTeX must use renderer-compatible delimiters.")
    ap.add_argument("--negative-test", action="store_true")
    args = ap.parse_args()

    if args.negative_test:
        probe = ROOT / "docs/__math_negative_control__.md"
        probe.write_text("# probe" + NEWLINE * 2
                         + "An expression " + OPEN_I + "x = 1" + CLOSE_I + " here." + NEWLINE,
                         encoding="utf-8")
        msgs = []
        scan(msgs)
        caught = any("__math_negative_control__" in m[1] for m in msgs)
        probe.unlink()
        after = []
        scan(after)
        print(f"  [{'OK' if caught else 'MISS'}] a native delimiter is reported")
        print(f"  [{'OK' if not after else 'MISS'}] probe removed and the tree is clean")
        return 0 if (caught and not after) else 1

    msgs = []
    scan(msgs)
    converter_exhausted(msgs)
    if not msgs:
        print("  OK: renderer-compatible delimiters throughout · $$ balanced · converter exhausted")
        return 0
    for k, d in msgs:
        print(f"  [FAIL] {k}: {d}")
    print(NEWLINE + f"  exit=1  findings: {len(msgs)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())