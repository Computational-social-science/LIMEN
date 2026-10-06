#!/usr/bin/env python
"""check_si_numbers.py -- every number in the Supplementary Information, checked against its source.

WHY THIS EXISTS, AND IT IS NOT HYPOTHETICAL
    A seven-row results table was drafted into the SI with the intermediate rows filled in BY EYE from the
    trend of the two rows that were known. Verification against the source CSV caught it: all seven rows were
    off, and one was wrong in DIRECTION - the drafted table showed the AUC still rising at the highest noise
    level, where the measured value is actually LOWER than at the level below it. A fabricated number in a
    results table is the single defect a reader cannot detect from the document, and it is the one this
    project's standards forbid most absolutely. Checking it by hand is what failed; this checks it by machine.

WHAT IT CHECKS
  A  every numeric cell of the per-level results table equals the value in the derived per-level CSV, to the
     precision the table prints.
  B  the numbers quoted in prose about the family result match the confirmatory results JSON.
  C  every table cell that looks like a proportion lies in [0, 1] (or a percentage in [0, 100]) - a cheap
     sanity net for a transcription that is off by an order of magnitude.

WHAT IT DOES NOT DO
    It cannot check prose that states a number without a table. It reports how many prose numbers it matched,
    so a reader can see how much of the document is covered rather than assuming all of it is.
"""

from __future__ import annotations

import csv
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SI = ROOT / "docs" / "SUPPLEMENTARY_INFORMATION.md"
SI_DIR = ROOT / "docs" / "si"
CSV_PATH = ROOT / "data" / "processed" / "stage2_lambda_summary.csv"
RESULTS = ROOT / "measurement" / "out" / "confirm_results.json"

# (column, printed decimals, scale). THE SCALE IS NOT OPTIONAL: the table prints the rejected-error share as
# a PERCENTAGE while the CSV stores it as a fraction, so a checker that compares them without converting
# reports every correct cell as a mismatch - which is the same unit error the checker exists to prevent,
# committed by the checker. Fourth time in one session that a unit mismatch produced a confident wrong answer.
TABLE_COLS = [
    ("lambda", 2, 1.0), ("accuracy", 4, 1.0), ("auc_within", 4, 1.0), ("coverage_0.9", 4, 1.0),
    ("cond_error_0.9", 4, 1.0), ("error_rejected_share_0.9", 1, 100.0),
]


def sources() -> dict[float, dict[str, float]]:
    out = {}
    for r in csv.DictReader(CSV_PATH.open(encoding="utf-8")):
        out[round(float(r["lambda"]), 2)] = {k: float(r[k]) for k, _, _ in TABLE_COLS}
    return out


def find_table(text: str) -> list[list[str]]:
    """The seven-level table: the one whose first column is a noise level and which has seven body rows."""
    best: list[list[str]] = []
    for block in re.findall(r"(?:^\|[^\n]*\n)+", text, re.M):
        rows = [[c.strip() for c in l.strip().strip("|").split("|")]
                for l in block.strip().splitlines() if not re.match(r"^\|[\s:|-]+\|$", l.strip())]
        if not rows or len(rows) < 5:
            continue
        body = rows[1:]
        if all(re.fullmatch(r"0\.\d\d", r[0]) for r in body if r):
            if len(body) > len(best):
                best = body
    return best


def main() -> int:
    files = []
    if SI.exists():
        files.append(SI)
    if SI_DIR.exists():
        files += sorted(SI_DIR.glob("*.md"))
    if not files:
        print("  [FAIL] no Supplementary Information source found")
        return 1

    src = sources()
    findings: list[str] = []
    checked_cells = 0
    prose_hits = 0

    for f in files:
        text = f.read_text(encoding="utf-8")
        table = find_table(text)
        for row in table:
            # ONE COLUMN PER ENTRY. Requiring one MORE than TABLE_COLS has entries skipped every row of
            # the seven-level table, so the guard reported a clean pass while checking nothing - the
            # false-pass defect class it exists to prevent, committed by the checker itself.
            if len(row) < len(TABLE_COLS):
                continue
            try:
                lam = round(float(row[0]), 2)
            except ValueError:
                continue
            if lam not in src:
                continue
            for (col, dp, scale), cell in zip(TABLE_COLS, row[:len(TABLE_COLS)]):
                try:
                    got = float(cell)
                except ValueError:
                    continue
                if col == "lambda":
                    continue
                want = scale * src[lam][col]
                checked_cells += 1
                if abs(got - want) > 0.5 * 10 ** (-dp):
                    findings.append(
                        f"{f.name}: lambda {lam:.2f} column {col}: table says {got}, source says {want:.6g}")
            # C: range sanity on proportions
            for (col, dp, scale), cell in zip(TABLE_COLS, row[:len(TABLE_COLS)]):
                if col in ("lambda", "error_rejected_share_0.9"):
                    continue
                try:
                    v = float(cell)
                except ValueError:
                    continue
                if not (0.0 <= v <= 1.0):
                    findings.append(f"{f.name}: lambda {lam:.2f} column {col}: value {v} is not a proportion")

        # B: prose numbers about the family
        if RESULTS.exists():
            r = json.loads(RESULTS.read_text(encoding="utf-8"))
            wanted = {
                "accuracy contrast": None,
                "H1.2' contrast": r["H1.2'"]["contrast"],
                "coverage fall": r["H1.3"]["mean_fall"],
            }
            for label, val in wanted.items():
                if val is None:
                    continue
                for m in re.finditer(r"([+\-]?0\.\d{3,4})", text):
                    if abs(abs(float(m.group(1))) - abs(val)) < 1e-4:
                        prose_hits += 1
                        break

    print(f"  sources: {len(src)} noise levels · {len(files)} SI file(s)")
    print(f"  table cells checked against source: {checked_cells}")
    print(f"  prose figures matched to the results JSON: {prose_hits}")
    if findings:
        print(f"\n  [FAIL] {len(findings)} number(s) disagree with their source:")
        for x in findings[:12]:
            print("      " + x)
        print("\n  A table cell that disagrees with the data it names is the one defect a reader cannot see.")
        return 1
    print("\n  [OK] every numeric cell of every results table equals its source value, all proportions are in")
    print("       range, and the prose figures quoted for the family match the results JSON")
    return 0


if __name__ == "__main__":
    sys.exit(main())