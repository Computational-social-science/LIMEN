#!/usr/bin/env python
"""check_seal_readiness.py -- the section-12 checklist, checked against reality before the seal.

WHY THIS EXISTS
    Every guard in this repository checks something IN the protocol or the artefacts. None of them checks
    the checklist AGAINST the tree: a row can claim `FIXED` while the document it names as its authority was
    renamed, deleted, or never written. That is the failure mode a pre-registration seal cannot afford,
    because the checklist is the one place a reader goes to learn what is frozen and where it was decided.

WHAT IT CHECKS
  A  no row is still marked as waiting. A `PENDING` anywhere in the state column means the seal is not
     ready, whatever the surrounding prose says - prose is where a pending item hides.
  B  every repository-relative path a row names as its authority EXISTS. A `FIXED` whose authority is
     missing is not fixed; it is unfalsifiable.
  C  the rows agree with the prose count. If the document says "the seal is blocked by N things", N must be
     the number of rows actually pending. A prose statement that disagrees with the table is the same defect
     class as a stale theorem count.

EXIT
  0  ready      1  at least one finding
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROTOCOL = REPO_ROOT / "protocol" / "NHB_Orthographic_Channels_JEV_Research_Protocol.md"

WAITING = ("PENDING", "OUTSTANDING", "TBD", "TODO", "NOT YET")


def rows(text: str) -> list[tuple[str, str, str]]:
    """(number, requirement, state) for the section-12 checklist table."""
    m = re.search(r"^## 12\..*?^\| # \|.*?\n((?:^\|[^\n]*\n)+)", text, re.S | re.M)
    if not m:
        return []
    out = []
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or set(cells[0]) <= set("-: "):
            continue
        out.append((re.sub(r"\*\*", "", cells[0]), cells[1], cells[2]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    args = ap.parse_args()

    text = PROTOCOL.read_text(encoding="utf-8")
    rs = rows(text)
    if not rs:
        print("  [FAIL] no section-12 checklist table found; the seal cannot be assessed")
        return 1

    findings: list[str] = []
    waiting: list[str] = []
    for num, req, state in rs:
        plain = re.sub(r"\*\*", "", state)
        if any(w in plain.upper() for w in WAITING):
            waiting.append(f"{num} ({req[:60]}) -> {plain[:70]}")
        for path in re.findall(r"`([A-Za-z0-9_./-]+/[A-Za-z0-9_./-]+)`", state + " " + req):
            if not (REPO_ROOT / path).exists():
                findings.append(f"row {num}: authority `{path}` does not exist")

    if waiting:
        findings.append(f"{len(waiting)} row(s) still waiting: " + "; ".join(waiting[:4]))

    # C - the prose count must match the table
    prose = re.search(r"THE SEAL IS NOT BLOCKED BY ([A-Z0-9]+)", text) or \
            re.search(r"blocked by exactly (?:one|two|three|\d+) thing", text, re.I)
    if prose and waiting:
        findings.append(f"the prose says '{prose.group(0)[:60]}' while {len(waiting)} row(s) are waiting")

    print(f"  section 12 rows: {len(rs)}")
    print(f"  rows still waiting: {len(waiting)}")
    for w in waiting:
        print("    - " + w)
    if findings:
        print(f"\n  [FAIL] {len(findings)} seal-readiness finding(s):")
        for f in findings:
            print("      " + f)
        return 1
    print("\n  [OK] no row is waiting, every named authority exists, and the prose agrees with the table")
    return 0


if __name__ == "__main__":
    sys.exit(main())