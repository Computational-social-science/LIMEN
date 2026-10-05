#!/usr/bin/env python
"""check_o1_anchor.py -- the O1 readability floor is a PUBLISHED number; keep it from drifting.

WHY THIS IS A GUARD AND NOT A SENTENCE IN A DOCUMENT
    `lo` is accepted on the condition `mean_r(lambda_lo) >= 0.448`, and 0.448 is the measured value of a
    published human condition (Rayner et al. 2006: interior letters rearranged, comprehension intact). A
    number that lives only in prose gets retyped, rounded, or quietly re-derived the next time someone
    edits the document - and a criterion whose floor has silently moved is worse than one with no floor,
    because it still reads as anchored. So the constant lives in exactly one place
    (scripts/o1_recoverability.py:RAYNER_ANCHOR_MEAN_R), the measurement that uses it is written to an
    artefact, and this guard checks that the artefact and the constant still agree and that the ladder
    still clears the floor.

WHAT IT CHECKS
  A  the anchor artefact exists and carries the same constant the instrument uses
  B  the measured Rayner condition is reported, and both variants are BELOW the mildest ladder point
     (if a Rayner variant ever came out above the ladder, the anchor would stop being an upper bound on
     what humans tolerate and the criterion would be inverted)
  C  lambda_lo as selected by the anchor IS the smallest grid point that clears the floor
  D  the margin at lo is positive

EXIT
  0  all pass      1  at least one failure

NEGATIVE CONTROL
  `--negative-test` raises the anchor above the mildest ladder point and requires check C or D to fail.
  A guard for an anchored threshold that has never been shown to fail is a guard that would accept any
  threshold at all.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
VALIDATION = REPO_ROOT / "measurement" / "o1_validation"
ANCHOR_JSON = VALIDATION / "anchor.json"
INSTRUMENT = REPO_ROOT / "scripts" / "o1_recoverability.py"


def constant_in_instrument() -> float:
    text = INSTRUMENT.read_text(encoding="utf-8")
    m = re.search(r"^RAYNER_ANCHOR_MEAN_R\s*=\s*([0-9.]+)", text, re.M)
    if not m:
        raise SystemExit("scripts/o1_recoverability.py no longer declares RAYNER_ANCHOR_MEAN_R; the anchor "
                         "has left its single home and this guard cannot mean anything")
    return float(m.group(1))


def run(anchor_override: float | None = None) -> list[str]:
    findings: list[str] = []
    if not ANCHOR_JSON.exists():
        return ["measurement/o1_validation/anchor.json is missing; run "
                "`scripts/o1_recoverability.py --anchor` before this guard can check anything"]

    data = json.loads(ANCHOR_JSON.read_text(encoding="utf-8"))
    declared = constant_in_instrument()
    recorded = float(data.get("anchor_mean_r", -1))
    floor = declared if anchor_override is None else anchor_override

    # A - the artefact and the instrument must agree on the number
    if abs(recorded - declared) > 1e-9:
        findings.append(f"A: the artefact records {recorded} but the instrument declares {declared}; "
                        f"one of them was edited without the other")

    grid = {float(k): float(v) for k, v in (data.get("grid_mean_r") or {}).items()}
    if not grid:
        findings.append("A: the artefact carries no grid, so nothing can be shown to clear the floor")
        return findings
    lo = min(grid)

    # B - the published condition must sit BELOW the mildest ladder point
    measured = data.get("rayne_conditions_measured") or {}
    if not measured:
        findings.append("B: the Rayner conditions were not recorded, so the anchor value is unattributed")
    for name, val in measured.items():
        if float(val) >= grid[lo]:
            findings.append(f"B: the Rayner '{name}' condition measures {float(val):.4f}, which is NOT below "
                            f"the mildest ladder point {grid[lo]:.4f}; the anchor would stop being an upper "
                            f"bound on what humans tolerate")

    # C - lambda_lo by the anchor must be the smallest clearing point
    clearing = sorted(l for l in grid if grid[l] >= floor)
    expected = clearing[0] if clearing else None
    recorded_lo = data.get("lambda_lo_by_anchor")
    if recorded_lo is None or abs(float(recorded_lo) - (expected or -1)) > 1e-9:
        findings.append(f"C: the artefact selects lambda_lo={recorded_lo} but the smallest grid point "
                        f"clearing {floor:.4f} is {expected}")

    # C2 - lambda_mid by the anchor must be the LARGEST clearing point: the band is calibrated as
    # "readable at the mild end, maximally stressed at the harsh end, both inside human tolerance".
    expected_mid = clearing[-1] if clearing else None
    recorded_mid = data.get("lambda_mid_by_anchor")
    if recorded_mid is None or abs(float(recorded_mid) - (expected_mid or -1)) > 1e-9:
        findings.append(f"C2: the artefact selects lambda_mid={recorded_mid} but the largest grid point "
                        f"clearing {floor:.4f} is {expected_mid}")

    # D - the margin at lo must be positive
    margin = grid[lo] - floor
    if margin <= 0:
        findings.append(f"D: the margin at the mildest point is {margin:+.4f}; the ladder does not clear "
                        f"the published floor, so `lo` is not acceptable at any grid point")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--negative-test", action="store_true",
                    help="raise the floor above the mildest point and require a failure")
    args = ap.parse_args()

    if args.negative_test:
        data = json.loads(ANCHOR_JSON.read_text(encoding="utf-8"))
        grid = {float(k): float(v) for k, v in (data.get("grid_mean_r") or {}).items()}
        if not grid:
            print("  [FAIL] no grid in the artefact; the control cannot run and must not report OK")
            return 1
        raised = max(grid.values()) + 0.05
        findings = run(anchor_override=raised)
        if findings:
            print(f"  negative control: a floor of {raised:.4f} was refused  OK")
            for f in findings[:2]:
                print("      " + f)
            return 0
        print("  [FAIL] negative control: a floor ABOVE every ladder point was accepted")
        return 1

    findings = run()
    if findings:
        print(f"  [FAIL] the O1 anchor is not holding up ({len(findings)} finding(s)):")
        for f in findings:
            print("      " + f)
        return 1
    data = json.loads(ANCHOR_JSON.read_text(encoding="utf-8"))
    grid = {float(k): float(v) for k, v in data["grid_mean_r"].items()}
    print(f"  OK: anchor {data['anchor_mean_r']:.4f} ({data['anchor_citation'][:48]}...) · "
          f"lambda_lo={data['lambda_lo_by_anchor']} by the anchor · "
          f"margin {data['margin_at_lo']:+.4f} at the mildest point")
    return 0


if __name__ == "__main__":
    sys.exit(main())