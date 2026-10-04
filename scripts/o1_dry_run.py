#!/usr/bin/env python
"""o1_dry_run.py -- exercise the whole O1 chain with a MACHINE panel, and say plainly what it is not.

WHY THIS EXISTS, AND WHY IT IS NOT A SUBSTITUTE FOR THE PANEL
    Amendment 3 freezes a decision rule and a three-rater panel. Running that chain once, end to end,
    proves the machinery works before a human spends an hour on it - and a dry run that fails on the
    first real pack wastes the panel's goodwill, which is the scarcest thing here.

    **The panel produced here is a deterministic function of the text, not a reader.** It exists to
    exercise the pipeline and to show what the rule does on data of a known shape. It CANNOT calibrate
    lambda and must never be reported as if it had. The output is written to a path that says so, and
    the acceptance verdict it prints is labelled MACHINE throughout.

WHAT THE MACHINE PANEL ACTUALLY USES
    `sentence_recoverability` from o1_auto_indices, thresholded into the three categories with cut points
    chosen to span the observed range, plus a small deterministic per-item jitter so that Fleiss' kappa
    is not a degenerate 1.0 and the merge's duplicate-identity check is exercised on real data rather
    than on obviously-identical packs.

    Three different "raters" with different thresholds and different jitter seeds is the minimum that
    exercises: independent judgement, disagreement, the kappa threshold, and the tie-break path.
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import o1_calibration as o1            # noqa: E402
import o1_auto_indices as auto        # noqa: E402
import merge_ratings as merge         # noqa: E402

# Three pseudo-raters: different strictness, different jitter. NOT readers.
# Three pseudo-raters with WIDE separation. The first dry run used thresholds close together and the
# merge's duplicate-identity check fired at lambda 0.05 - every machine rater returned the same category
# for every item. That was not a bug and it was worth keeping: at the lightest level the text is
# uniformly readable, so a panel that agrees unanimously is the CORRECT reading. But it means the
# thresholds here are chosen to span the observed range, which is what a real panel of readers does
# naturally and a tight-threshold machine panel does not.
# The jitter is not decorative: two pseudo-raters with thresholds 0.96/0.93 and 0.99/0.93 turned out to
# produce byte-identical packs at EVERY level, because the data never lands between those cut points.
# Real readers differ in more than their cut points, so the seed jitter is widened until the panel
# actually disagrees - otherwise the dry run cannot exercise the kappa threshold at all, and a test
# that never reaches the threshold it exists to test is not a test.
PANEL = [
    {"id": "A", "hi": 0.95, "mid": 0.70, "seed": 11, "jit": 0.14},
    {"id": "B", "hi": 0.90, "mid": 0.55, "seed": 23, "jit": 0.10},
    {"id": "C", "hi": 0.98, "mid": 0.85, "seed": 37, "jit": 0.18},
]


def categorise(rec, p):
    """Map a record's sentence recoverability to R / W / X with this rater's thresholds.

    The jitter is a deterministic function of (item_id, rater seed), not a random draw, so a re-run
    reproduces the dry run exactly - which is the only property that makes it useful as a test.
    """
    h = sum(ord(ch) for ch in rec["item_id"] + p["id"]) % 89 / 89.0
    jitter = (h - 0.5) * p["jit"]
    s = rec["sentence_recoverability"] + jitter
    if s >= p["hi"]:
        return "R"
    if s >= p["mid"]:
        return "W"
    return "X"


def run(out_dir=None, lambdas=None, seed=0, n=o1.N_PER_LEVEL):
    tmp = pathlib.Path(out_dir) if out_dir else None
    own = tmp is None
    tmp = tmp or (pathlib.Path(tempfile.mkdtemp()) / "packs")
    try:
        tmp.mkdir(parents=True, exist_ok=True)
        grid = lambdas or {"lo": list(o1.LO_GRID), "mid": list(o1.MID_GRID)}
        filled = 0
        for role, lams in grid.items():
            for lam in lams:
                items = o1.build_sheet(lam, seed, n=n)
                rows = []
                for it in items:
                    d = auto.indices(it["clean"], it["perturbed"])
                    d["item_id"] = it["item_id"]
                    rows.append(d)
                stem = "o1_%s_lam%03d" % (role, round(lam * 100))
                for p in PANEL:
                    path = tmp / ("%s_rater%s.csv" % (stem, p["id"]))
                    with path.open("w", encoding="utf-8", newline="") as fh:
                        w = csv.writer(fh)
                        w.writerow(["item_id", "domain", "lambda_target", "realised_edit_rate",
                                    "n_ops", "clean", "perturbed", "category"])
                        for it, d in zip(items, rows):
                            w.writerow([it["item_id"], it["domain"], it["lambda_target"],
                                        it["realised_edit_rate"], it["n_ops"],
                                        it["clean"], it["perturbed"], categorise(d, p)])
                            filled += 1
        merged = tmp.parent / "o1_dryrun_ratings.csv"
        out, nrows, blanks = merge.merge(tmp, merged)
        # Clean up only AFTER the caller has read the file. An earlier version removed the temp tree in
        # the `finally` of this function, so the caller was handed a path that no longer existed - and
        # the traceback pointed at the caller rather than at the deletion, which is where the work was.
        keep = tmp if out_dir else None
        return merged, nrows, blanks, filled, keep
    finally:
        if own and tmp.exists() and out_dir is None:
            pass  # the caller removes it after reading


def main() -> int:
    ap = argparse.ArgumentParser(description="Exercise the O1 chain with a machine panel.")
    ap.add_argument("--keep", type=pathlib.Path, default=None,
                    help="write the filled packs here instead of a temp dir")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--lame", type=float, action="append", default=None)
    args = ap.parse_args()

    print("  MACHINE PANEL DRY RUN - this does NOT calibrate lambda and is not a result.")
    print("  It exists to prove the chain runs before a human panel is asked to spend an hour.\n")

    merged, nrows, blanks, filled, keep = run(out_dir=args.keep, seed=args.seed)
    print(f"  packs filled    : {filled} item-ratings across 3 machine 'raters'")
    print(f"  merged          : {nrows} rows -> {merged}")
    print(f"  blanks          : {len(blanks)}  (must be 0 for the scorer to run)")

    if blanks:
        print("  [FAIL] the merge reported blanks; the chain is not ready")
        return 1

    print("\n  --- applying the frozen rule to MACHINE data ---")
    ok = 0
    for role, grid in (("lo", o1.LO_GRID), ("mid", o1.MID_GRID)):
        for lam in grid:
            rows = []
            with merged.open(encoding="utf-8", newline="") as fh:
                for rec in csv.DictReader(fh):
                    if rec["role"] == role and abs(float(rec["lambda_target"]) - lam) < 1e-9:
                        rows.append((rec["item_id"], rec["rater_id"], rec["category"]))
            if not rows:
                continue
            res = o1.score(role, rows)
            mark = "ACCEPTED (MACHINE)" if res["accept"] else "rejected (MACHINE)"
            print(f"    {role} λ={lam:<5} kappa={res['kappa']}  median={res['median_category']}  "
                  f"P(X)={res['p_lost']}   {mark}")
            ok += bool(res["accept"])

    print("\n  The rule ran to completion on every grid point, which is what this was for.")
    print("  The verdicts above are properties of the MACHINE panel, not of the protocol: a real")
    print("  panel may accept a different level, and it is the panel's answer that freezes λ.")
    if args.keep:
        print(f"\n  Filled packs kept at {args.keep} (clearly synthetic - do not report as human data).")
    elif keep and keep.parent.exists():
        shutil.rmtree(keep.parent, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
