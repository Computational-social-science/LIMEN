#!/usr/bin/env python
"""sync_lean_counts.py -- rewrite every DERIVED Lean figure that appears outside the Lean source.

WHY THIS IS A SCRIPT
    The theorem count, the line count, the error count and the sorry count appear in the status record,
    in the protocol and in the amendments, and every one of them is a claim about the Lean source module
    that a reader treats as authority. Updating them by hand has now been done three times in this project, and
    each time the freshness guard caught a place that was missed - twice a line-wrapped "N theorems" that
    a `\\bN theorems\\b` pattern walks straight past, once a figure inside an amendment rather than the
    protocol. Being caught is the guard working; being repeatedly caught is the process being wrong.

WHAT IT DERIVES FROM
    The counts come from the Lean source module and from the kernel checker's output, never from the
    documents
    being corrected. That direction matters: a synchroniser that reads one document and writes another
    can launder a stale figure into agreement with another stale figure.

WHAT IT REFUSES TO DO
    It does not touch a figure it cannot attribute. A number followed by "theorems" in prose is rewritten;
    a number followed by "theorems" inside a quote of an older revision is skipped and reported, because
    the protocol keeps its version history verbatim and history that has been silently rewritten is not
    history. Anything skipped is printed so the omission is visible rather than assumed.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LEAN_ROOT = REPO_ROOT.parent / "lean-nhb"
# EVERY KERNEL SOURCE. Counting only Core.lean reported 23 theorems while the kernel holds 27, and reported
# the source-file count as 1 - a number the reader has no way to falsify from the document. The count is now
# derived from the same glob the kernel checker uses, so the two cannot disagree about what the kernel is.
PHASE = LEAN_ROOT / "NHB" / "PhaseI"
SOURCES = sorted(p for p in PHASE.glob("*.lean") if not p.name.startswith("__"))

STATUS = REPO_ROOT / "docs" / "LEAN_FORMALIZATION_STATUS.md"
ALSO = [
    REPO_ROOT / "protocol" / "NHB_Orthographic_Channels_JEV_Research_Protocol.md",
    REPO_ROOT / "docs" / "PHASE_I_AMENDMENT_2.md",
]

# Lines inside the protocol's version-history table quote older revisions verbatim; rewriting a number
# there would make the record claim a revision said something it never said.
HISTORY_MARKERS = ("> | **1.", "> |--", "| v1.", "| v 1.")


def derive() -> dict:
    texts = {p.name: p.read_text(encoding="utf-8") for p in SOURCES}
    out = {
        "theorems": sum(len(re.findall(r"^theorem\s", t, re.M)) for t in texts.values()),
        "lines": sum(len(t.splitlines()) for t in texts.values()),
        "files": len(texts),
        "per_file": {k: len(re.findall(r"^theorem\s", v, re.M)) for k, v in texts.items()},
    }
    try:
        proc = subprocess.run(
            [sys.executable, "-B", str(REPO_ROOT / "scripts" / "check_lean_axioms.py")],
            capture_output=True, text=True, timeout=300,
        )
        m = re.search(r"OK: (\d+) theorem\(s\)", proc.stdout)
        out["kernel_checked"] = int(m.group(1)) if m else None
    except Exception:
        out["kernel_checked"] = None
    return out


def rewrite(path: pathlib.Path, n: int, nl: int, checked: int | None, apply: bool,
            nf: int = 1) -> list[str]:
    before = path.read_text(encoding="utf-8")
    after = before
    skipped: list[str] = []

    # `N theorems` possibly wrapped across a line - the exact shape that defeated the earlier hand pass.
    def sub_theorems(m: re.Match) -> str:
        line_start = after.rfind("\n", 0, m.start()) + 1
        line = after[line_start:after.find("\n", m.start())]
        if any(line.lstrip().startswith(h) for h in HISTORY_MARKERS):
            skipped.append(f"{path.name}: history line left verbatim -> {line.strip()[:80]}")
            return m.group(0)
        return f"{n}{m.group(1)}"

    after = re.sub(r"\d+(\s*\ntheorems|\s+theorems)", sub_theorems, after)
    # THE SOURCE-FILE COUNT AND THE PATH FORM ARE DERIVED TOO, not typed: "1 file, Core.lean, 507 lines"
    # was true of the file the script happened to read and false about the kernel, and a reader had no way
    # to tell which of the two it meant.
    after = re.sub(r"source files\s*: \d+", f"source files          : {nf}", after)
    after = re.sub(r"NHB/PhaseI/[A-Za-z0-9_]+\.lean, \d+ lines",
                   f"NHB/PhaseI/*.lean, {nl} lines", after)
    after = re.sub(r"theorem count\s*: \d+", f"theorem count         : {n}", after)
    if checked is not None:
        after = re.sub(r"theorems machine-checked: \d+", f"theorems machine-checked: {checked}", after)
        after = re.sub(r"OK: \d+ theorem\(s\)", f"OK: {checked} theorem(s)", after)

    if after != before:
        if apply:
            path.write_text(after, encoding="utf-8", newline="\n")
        changed = sum(1 for a, b in zip(before.split("\n"), after.split("\n")) if a != b)
        print(f"  [FIX ] {path.relative_to(REPO_ROOT)}  ({changed} line(s))")
    else:
        print(f"  [ok  ] {path.relative_to(REPO_ROOT)}")
    return skipped


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    d = derive()
    print(f"  derived from {len(SOURCES)} source file(s) under {PHASE.relative_to(LEAN_ROOT)} "
          f"+ the kernel checker:")
    print(f"    theorems={d['theorems']}  lines={d['lines']}  files={d['files']}  "
          f"kernel_checked={d['kernel_checked']}")
    for k, v in d["per_file"].items():
        print(f"      {k}: {v} theorem(s)")
    if d["kernel_checked"] is not None and d["kernel_checked"] != d["theorems"]:
        print("    [WARN] the kernel checked a different number of theorems than the source declares.")
        print("           converging on the SOURCE count would hide a genuinely uncheckable theorem.")
        print("           fix the formalisation first; this script will not paper over it.")
        return 1
    print()

    skipped: list[str] = []
    for path in [STATUS, *ALSO]:
        if path.exists():
            skipped += rewrite(path, d["theorems"], d["lines"], d["kernel_checked"],
                               not args.dry_run, d["files"])

    if skipped:
        print("\n  skipped, and reported rather than silently left:")
        for s in skipped:
            print(f"    - {s}")
    if args.dry_run:
        print("\n  --dry-run: nothing written")
    else:
        print("\n  next: re-pin the anchor if the protocol changed, rebuild, run the guards.")
    return 0


if __name__ == "__main__":
    sys.exit(main())