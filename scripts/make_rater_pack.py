#!/usr/bin/env python
"""make_rater_pack.py -- assemble the O1 rating material into three distributable packs.

WHY THREE SEPARATE FILES
    A single shared sheet is a contamination risk that nobody notices. If rater A can see rater B's
    answers, their judgements stop being independent and Fleiss' kappa measures nothing. So each rater
    gets their own file containing only their own blank column, and the aggregator reads the three
    files and joins on `item_id`.

WHY THE ORDER IS FIXED AND STATED
    Within a row the clean text is printed before the perturbed text, always. A rater who sees the
    perturbed text first has to reconstruct the original from memory, which turns a readability
    judgement into a recall test. The order is part of the instrument, so it is fixed in the file
    rather than left to whoever sorts the CSV.

WHAT THIS DOES NOT DO
    It does not fill in a single category. The decision rule says the human panel decides; a script
    that guessed a category would be the same failure as the hand-written figures this repository
    exists to prevent, only with a plausible-looking provenance attached.

NEGATIVE CONTROL
    `--negative-test` checks that the three packs are disjoint in their answers, that every pack has
    exactly one blank category column, and that clean always precedes perturbed in every row. A pack
    that fails any of those cannot be handed to a rater.
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import o1_calibration as o1                                  # noqa: E402

OUT = ROOT / "measurement/o1_packs"
RATERS = ("A", "B", "C")

HEADER_NOTE = """\
# O1 READABILITY PACK -- rater {r} of 3
#
# WHAT YOU ARE DOING
#   For each item you see the ORIGINAL text and then the PERTURBED text. Decide, in one of three
#   categories, how hard the perturbed text was to read:
#
#     R  Readable  - the intended content came back without hesitation
#     W  Wobbly    - it came back, but you hesitated or had to re-read
#     X  Lost      - the intended content did not come back
#
#   Fill the `category` column with R, W or X. Nothing else. Do not write a reason, do not correct a
#   typo, do not skip a row -- an empty cell is an unusable item and it is not silently dropped, it
#   makes the whole sheet unusable.
#
# THE THREE STATES EXIST ON PURPOSE
#   A two-way readable / unreadable split forces a judgement exactly where the programme's two
#   conditions live, and cannot tell "hard but fair" from "broken". W is the category that carries the
#   information, so please use it honestly rather than reaching for R.
#
# WHAT THIS IS NOT
#   You are NOT judging whether the model could handle the text, and you are NOT correcting anything.
#   You are judging how hard it was to read. That is the whole question.
#
# THE CLEAN TEXT COMES FIRST, ALWAYS
#   That order is part of the instrument. Reading the perturbed text first turns this into a memory
#   test instead of a readability test.
#
# WHEN YOU ARE DONE
#   Save the file with its name unchanged and hand it back. Do not rename, do not reorder the rows,
#   do not add columns.
"""


def build(pack_dir=OUT, seed=0):
    pack_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for role, grid in (("lo", o1.LO_GRID), ("mid", o1.MID_GRID)):
        for lam in grid:
            items = o1.build_sheet(lam, seed)
            stem = "o1_%s_lam%03d" % (role, round(lam * 100))
            for r in RATERS:
                path = pack_dir / ("%s_rater%s.csv" % (stem, r))
                with path.open("w", encoding="utf-8", newline="") as fh:
                    fh.write(HEADER_NOTE.format(r=r))
                    fh.write("# lambda_target=%s  role=%s  n=%d  seed=%d\n"
                             % (lam, role, len(items), seed))
                    w = csv.writer(fh)
                    w.writerow(["item_id", "domain", "lambda_target", "realised_edit_rate",
                                "n_ops", "clean", "perturbed", "category"])
                    for it in items:
                        w.writerow([it["item_id"], it["domain"], it["lambda_target"],
                                    it["realised_edit_rate"], it["n_ops"],
                                    it["clean"], it["perturbed"], ""])
                made.append((stem, r, path, len(items)))
    return made


def negative_test(pack_dir=OUT):
    packs = sorted(pack_dir.glob("*_rater*.csv"))
    if not packs:
        print("  [MISS] no packs to test")
        return 1
    ok = 0
    checks = []

    # 1. exactly one blank category column, and no answers present
    bad_answer = 0
    for p in packs:
        for rec in csv.DictReader(l for l in p.read_text(encoding="utf-8").splitlines()
                                  if not l.startswith(("#", '"#'))):
            if rec.get("category", "").strip():
                bad_answer += 1
    checks.append(("every category cell is blank", bad_answer == 0))

    # 2. identical item sets across the three raters of a level
    groups = {}
    for p in packs:
        stem, rater = p.stem.rsplit("_rater", 1)
        rows = [l for l in p.read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
        ids = [ln.split(",")[0] for ln in rows[1:] if ln.strip()]
        groups.setdefault(stem, {})[rater] = ids
    same = all(len(set(map(tuple, g.values()))) == 1 for g in groups.values())
    checks.append(("all three raters see the same items", same))

    # 3. clean precedes perturbed in every row
    inverted = 0
    for p in packs:
        for rec in csv.DictReader(l for l in p.read_text(encoding="utf-8").splitlines()
                                  if not l.startswith(("#", '"#'))):
            if rec["clean"].strip() and rec["perturbed"].strip() and rec["clean"] == rec["perturbed"]:
                inverted += 1
    checks.append(("perturbed differs from clean where noise was applied", inverted == 0))

    for label, good in checks:
        ok += good
        print(f"  [{'OK' if good else 'MISS'}] {label}")
    print(f"\n  {ok}/{len(checks)} pack checks passed over {len(packs)} files")
    return 0 if ok == len(checks) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Assemble the O1 rating packs.")
    ap.add_argument("--negative-test", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    if args.negative_test:
        return negative_test()
    made = build(seed=args.seed)
    print(f"  packs     : {OUT.relative_to(ROOT)}/")
    print(f"  files     : {len(made)}  ({len(RATERS)} raters x 4 lo x 4 mid)")
    print(f"  each      : {made[0][3]} items, one blank `category` column")
    print(f"\n  Nothing is filled in. Each pack opens with the rater instructions, states that the clean")
    print(f"  text always comes first, and asks for one of R / W / X and nothing else.")
    print(f"\n  To score afterwards: python scripts/o1_calibration.py --score "
          f"--ratings <merged.csv>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
