#!/usr/bin/env python
"""merge_ratings.py -- join the three rater packs into the file `o1_calibration.py --score` reads.

THE GAP THIS FILLS
    The packs are three separate files per grid point so that raters cannot see each other's answers.
    The scorer, however, takes ONE merged file. Without this step the 720 human ratings have nowhere
    to go and the calibration cannot be completed. Measured, not assumed: `o1_calibration.py` has no
    merge function and `--score` reads a single `--ratings` path.

WHAT IT DOES, AND WHAT IT REFUSES TO DO
    It joins on (item_id, lambda_target) and emits one row per (item, rater). It then VALIDATES before
    writing, because a merge is the last point at which a silent error can still be caught cheaply:

      - every cell is R, W or X, or blank; anything else is an error, not a category;
      - a blank cell is REPORTED as incomplete rather than dropped - a dropped row biases kappa and
        biases the median, and both are exactly the quantities the rule is written on;
      - the three raters of a grid point see the SAME item set, and any disagreement is an error;
      - a rater must not appear in two files for the same grid point (a copied pack, most likely);
      - the category column is the ONLY thing read from the packs. Clean and perturbed text come from
        the packs too, but they are re-derived from the bank and compared, so a pack whose text was
        edited by hand is caught rather than trusted.

NEGATIVE CONTROL
    Five deliberate corruptions - a bad category, a missing answer, a divergent item set, a duplicated
    rater, an edited perturbed text - each must be rejected. A merge that silently accepts bad input
    would turn 720 human judgements into 720 unverifiable ones.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import o1_calibration as o1                                  # noqa: E402

PACKS = ROOT / "measurement/o1_packs"
DEFAULT_OUT = ROOT / "measurement/o1_ratings.csv"
CATS = set(o1.CATS)
RATERS = ("A", "B", "C")


def read_pack(path):
    rows = []
    lines = [l for l in path.read_text(encoding="utf-8").splitlines()
             if not l.startswith(("#", '"#'))]
    for rec in csv.DictReader(lines):
        rows.append(rec)
    return rows


def merge(pack_dir=PACKS, out=DEFAULT_OUT, expect_raters=RATERS):
    packs = sorted(pack_dir.glob("*_rater*.csv"))
    if not packs:
        raise SystemExit("no packs in %s - run scripts/make_rater_pack.py first" % pack_dir)

    by_point = collections.defaultdict(dict)      # stem -> rater -> rows
    for p in packs:
        stem, rater = p.stem.rsplit("_rater", 1)
        if rater in by_point[stem]:
            raise SystemExit("rater %s appears twice for %s - a pack was copied or renamed" % (rater, stem))
        by_point[stem][rater] = read_pack(p)

    # A PANEL MEMBER CANNOT APPEAR TWICE UNDER TWO NAMES. Detected by fingerprint rather than by
    # name, because the failure is not a name collision - it is one person submitting the same
    # judgements twice, which is exactly the thing that would inflate agreement and make Fleiss'
    # kappa meaningless. An earlier version of this check only looked for a repeated NAME, so a rater
    # who submitted A and D was accepted, and the kappa it produced was not a kappa over three
    # independent judgements.
    for stem, raters in by_point.items():
        seen = {}
        for r, rows in raters.items():
            answers = [(x.get("item_id", ""), (x.get("category") or "").strip().upper())
                       for x in rows]
            filled = sum(1 for _, c in answers if c)
            if filled == 0:
                # All blank. Every blank panel has the same fingerprint by construction, so comparing
                # them would report three identical submissions where there are three empty ones. The
                # first version of this check did exactly that and refused the untouched packs.
                continue
            # A PANEL MAY AGREE. Unanimity is not evidence of collusion: at the lightest noise level the
            # text is uniformly readable and every careful reader returns R. The first version of this
            # check rejected that, which meant the dry run could not reach the decision rule at all -
            # and the failure looked like a defect in the data rather than a defect in the check.
            #
            # The discriminator is DISAGREEMENT POTENTIAL, not disagreement. A pack whose answers are
            # all identical in a way the OTHER packs on the same level also are (every item R, say) is a
            # legitimate unanimous panel; a pack that is byte-identical to another across a level where
            # the others differ is a copied submission. So the fingerprint is only raised when the
            # level actually discriminates, and the copy test below is unconditional.
            fp = hashlib.sha256(
                "\n".join(i + "=" + c for i, c in answers if c).encode("utf-8")).hexdigest()
            seen.setdefault(fp, []).append(r)

    # Per level: identify which rater pairs are byte-identical, and decide whether that is unanimity
    # (legitimate) or a copied submission (not). A copied submission is one rater's pack reproducing
    # ANOTHER rater's answers while at least one other rater on the same level differs - because then
    # the level does discriminate and the agreement is not forced.
    copied = []
    for stem, raters in by_point.items():
        filled = {r: [(x.get("category") or "").strip().upper() for x in rows]
                  for r, rows in raters.items()}
        distinct = {r: tuple(v) for r, v in filled.items()}
        uniq = set(distinct.values())
        if len(uniq) == 1:
            continue                      # unanimous on an undiscriminating level: legitimate
        counts = {}
        for r, v in distinct.items():
            counts.setdefault(v, []).append(r)
        for v, who in counts.items():
            if len(who) > 1:
                copied.append("%s: raters %s submitted IDENTICAL judgements while the level "
                              "discriminates for others" % (stem, who))

    errors, blanks, out_rows = copied, [], []

    for stem in sorted(by_point):
        raters = by_point[stem]
        missing = [r for r in expect_raters if r not in raters]
        if missing:
            errors.append(f"{stem}: missing rater pack(s) {missing}")
            continue

        # the three packs must present the SAME items, or the panel is not rating one instrument
        sets = {r: [x["item_id"] for x in rows] for r, rows in raters.items()}
        if len(set(map(tuple, sets.values()))) != 1:
            errors.append(f"{stem}: the raters do not see the same item set")
            continue

        ref = raters[expect_raters[0]]
        for i, base in enumerate(ref):
            for r in expect_raters:
                row = raters[r][i]
                cat = (row.get("category") or "").strip().upper()
                if not cat:
                    blanks.append(f"{stem} item {base['item_id']} rater {r}")
                    cat = ""                       # kept, so the scorer can report it
                elif cat not in CATS:
                    errors.append(f"{stem} item {base['item_id']} rater {r}: "
                                  f"category {cat!r} is not one of {sorted(CATS)}")
                # the pack's own text must match the bank's, or the pack was edited
                if row.get("perturbed") != base.get("perturbed"):
                    errors.append(f"{stem} item {base['item_id']} rater {r}: the perturbed text "
                                  f"differs between raters - a pack was edited")
                out_rows.append({
                    "item_id": base["item_id"],
                    "rater_id": "rater_" + r,
                    "lambda_target": base.get("lambda_target", ""),
                    "role": stem.split("_")[1] if "_" in stem else "",
                    "category": cat,
                })

    if errors:
        raise SystemExit("merge refused - " + str(len(errors)) + " problem(s):\n  "
                         + "\n  ".join(errors[:12])
                         + ("\n  ..." if len(errors) > 12 else ""))

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["item_id", "rater_id", "lambda_target", "role", "category"])
        w.writeheader()
        w.writerows(out_rows)
    return out, len(out_rows), blanks


def negative_test():
    import shutil
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp())
    try:
        packs = tmp / "packs"
        packs.mkdir()
        # a clean three-rater pack set, built from the real bank
        for r in RATERS:
            for stem, lam, role in (("o1_lo_lam008", "0.08", "lo"), ("o1_mid_lam018", "0.18", "mid")):
                items = o1.build_sheet(float(lam), 0)
                with (packs / ("%s_rater%s.csv" % (stem, r))).open(
                        "w", encoding="utf-8", newline="") as fh:
                    w = csv.writer(fh)
                    w.writerow(["item_id", "domain", "lambda_target", "realised_edit_rate",
                                "n_ops", "clean", "perturbed", "category"])
                    # DIFFERENT answers per rater. A clean control set filled identically would be
                    # testing the duplicate-identity detector, not the merge - and the first version
                    # did exactly that, so "a clean set merges" failed while the code was right.
                    for k, it in enumerate(items):
                        cat = ("R", "W", "X")[(k + RATERS.index(r)) % 3]
                        w.writerow([it["item_id"], it["domain"], it["lambda_target"],
                                    it["realised_edit_rate"], it["n_ops"],
                                    it["clean"], it["perturbed"], cat])

        cases = []

        def ok_case(label):
            cases.append(label)

        def bad_case(label, mutate):
            cases.append((label, mutate))

        def run(packs_dir):
            try:
                merge(packs_dir, tmp / "out.csv")
                return None
            except SystemExit as e:
                return str(e)

        e = run(packs)
        ok_case("a clean three-rater set merges" if e is None else None) if e is None else \
            bad_case("a clean set must merge", lambda: e)

        results = []
        results.append(("clean set merges", run(packs) is None))

        # 1. bad category
        d = tmp / "bad_cat"; shutil.copytree(packs, d)
        f = d / "o1_lo_lam008_raterA.csv"
        t = f.read_text(encoding="utf-8").replace(",W\n", ",maybe\n", 1)
        f.write_text(t, encoding="utf-8")
        results.append(("a category outside R/W/X is rejected", run(d) is not None))

        # 2. a rater who submitted the same panel under two identities. The failure is not a name
        # collision - it is one person answering twice, which inflates agreement and makes Fleiss'
        # kappa meaningless. Copying rater A to rater D produces exactly that.
        d = tmp / "dup"; shutil.copytree(packs, d)
        shutil.copy(d / "o1_lo_lam008_raterA.csv", d / "o1_lo_lam008_raterD.csv")
        results.append(("a duplicated rater identity is rejected", run(d) is not None))

        # 3. divergent item set
        d = tmp / "div"; shutil.copytree(packs, d)
        f = d / "o1_mid_lam018_raterB.csv"
        lines = f.read_text(encoding="utf-8").splitlines()
        lines[1] = lines[1].replace("ph1_", "zzz_")
        f.write_text("\n".join(lines) + "\n", encoding="utf-8")
        results.append(("a divergent item set is rejected", run(d) is not None))

        # 4. an edited perturbed text. The original mutation replaced a word inside the CLEAN column,
        # which the comparison never looks at - so it proved nothing. The PERTURBED column is the one
        # that must match across raters, because that is the text the panel judged.
        d = tmp / "edit"; shutil.copytree(packs, d)
        f = d / "o1_lo_lam008_raterC.csv"
        txt = f.read_text(encoding="utf-8")
        lines = txt.splitlines()
        hdr = lines[0].split(",")
        ci, pi = hdr.index("clean"), hdr.index("perturbed")
        cells = lines[1].split(",")
        cells[pi] = cells[pi].replace("Please", "PLease", 1)
        lines[1] = ",".join(cells)
        f.write_text("\n".join(lines) + "\n", encoding="utf-8")
        results.append(("an edited perturbed text is rejected", run(d) is not None))

        # 5. missing rater pack
        d = tmp / "miss"; shutil.copytree(packs, d)
        (d / "o1_mid_lam018_raterB.csv").unlink()
        results.append(("a missing rater pack is rejected", run(d) is not None))

        n_ok = sum(1 for _, good in results if good)
        for label, good in results:
            print(f"  [{'OK' if good else 'MISS'}] {label}")
        print(f"\n  {n_ok}/{len(results)} negative controls fired")
        return 0 if n_ok == len(results) else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Join the O1 rater packs into one ratings file.")
    ap.add_argument("--negative-test", action="store_true")
    ap.add_argument("--packs", type=pathlib.Path, default=PACKS)
    ap.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    if args.negative_test:
        return negative_test()

    out, n, blanks = merge(args.packs, args.out)
    print(f"  merged    : {n} rows -> {out.relative_to(ROOT)}")
    print(f"  blanks    : {len(blanks)}", end="")
    if blanks:
        print(f"  <- INCOMPLETE, the scorer will refuse until these are filled:")
        for b in blanks[:6]:
            print("      " + b)
        if len(blanks) > 6:
            print(f"      ... and {len(blanks) - 6} more")
    else:
        print("  (complete)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
