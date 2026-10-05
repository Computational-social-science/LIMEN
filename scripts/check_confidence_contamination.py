#!/usr/bin/env python
"""check_confidence_contamination.py -- the frozen instrument substitutes a constant into SOME confidences.

WHY THIS EXISTS
    `measurement/run_phase1.py` on the pinned revision prints, from the library itself:

        laya: this checkpoint ships invalid temperatures or values outside [0.5, 5]; using
        choice:11+=0.10058280825614929 -> 0.5. Treat confidence from the affected entries as uncalibrated.

    The whole design rests on `c = max_j p_j` being a comparable confidence: `SilentError@tau` and
    `Coverage@epsilon` are both functions of it, and tau is fixed at 0.80/0.90 on the assumption that c is
    on one scale. If the affected route substitutes 0.5, entries on that route carry a confidence that is
    not a probability of being right, and a tau gate over them measures the substitution.

    MEASURED, on the 24-item dev pre-run: 0 of 72 emitted confidences equal 0.5, and c spans 0.408-0.996
    over 68 distinct values. So the affected route was not reached in that sample. But the library's warning
    is explicit that the affected entries are uncalibrated, and the confirmatory run is 652 items x 3
    lambdas x 3 seeds - orders of magnitude more conditions. A one-off observation is not a guarantee, so
    the observation is turned into an INVARIANT that is checked on every trial file.

    This is the difference between reading a warning and acting on it: a warning you hope does not matter is
    not a control.

EXIT
  0  no substituted constant found      1  at least one contaminated row, or no rows to check
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SUBSTITUTED = 0.5          # the value the library reports substituting


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("trials", nargs="?", help="trial JSONL; defaults to the dev pre-run")
    ap.add_argument("--out", help="write the finding to this path even on success")
    args = ap.parse_args()

    path = pathlib.Path(args.trials) if args.trials else REPO_ROOT / "measurement" / "out" / "prerun_trials.jsonl"
    if not path.exists():
        print(f"  [FAIL] no trial file at {path}; there is nothing to certify, and an absent file must not "
              f"read as a clean one")
        return 1

    rows, bad = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("status") != "ok":
            continue
        rows.append(r)
        c = r.get("c")
        if c is not None and abs(float(c) - SUBSTITUTED) < 1e-9:
            bad.append(r)

    if not rows:
        print("  [FAIL] the trial file carries no ok rows; nothing was checked")
        return 1

    cs = sorted(float(r["c"]) for r in rows if r.get("c") is not None)
    summary = {"rows_checked": len(rows), "contaminated": len(bad), "substituted_value": SUBSTITUTED,
               "c_min": cs[0] if cs else None, "c_max": cs[-1] if cs else None,
               "c_distinct": len({round(x, 6) for x in cs})}
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"  rows checked {len(rows)}  c range {summary['c_min']:.4f}-{summary['c_max']:.4f} "
          f"({summary['c_distinct']} distinct)")
    if bad:
        print(f"  [FAIL] {len(bad)} row(s) carry the substituted constant {SUBSTITUTED}; their confidence "
              f"is not a probability of being right and no tau gate over them is interpretable")
        for r in bad[:5]:
            print(f"      {r.get('item_id')} lambda={r.get('lambda')} q={r.get('question_id')}")
        return 1
    print(f"  [OK] no row carries the substituted constant; the affected route was not reached here")
    return 0


if __name__ == "__main__":
    sys.exit(main())
