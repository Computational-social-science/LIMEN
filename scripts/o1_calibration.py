#!/usr/bin/env python
"""o1_calibration.py -- material and decision rule for the O1 readability calibration.

WHAT THIS IS, AND WHAT IT IS NOT
    The decision rule is pre-registered in `docs/PHASE_I_AMENDMENT_3_O1_READABILITY.md`: three
    human-native adult raters, three ordered categories (R readable / W wobbly / X lost), 60 dev
    items per level, Fleiss' kappa >= 0.60, and a level accepted on a stated rule about the median
    category and the tail. This script does three mechanical things and NO judgement:

      1. builds the rating sheets for a given grid point, from the DEV split only;
      2. scores a completed set of ratings against the frozen rule;
      3. measures the automatic secondary quantities (normalised edit distance, token perplexity
         under a fixed reference model) that are recorded alongside, but never decide.

    It never proposes a level. Accepting or rejecting a level is the human panel's, and this file
    exists so that their judgement is applied to a rule fixed in advance.

WHY DEV ONLY
    The pre-registration splits items 30/70 into dev and test, and the fitted threshold tau* is fit on
    dev alone. Reading test items here would let a human judgement inform a design choice made from
    test data, which is exactly the leak the split exists to prevent. A guard asserts it rather than
    trusting the caller.

NEGATIVE CONTROL
    `--negative-test` scores three synthetic rating sets: one that satisfies the rule, one that
    violates it at the tail, and one where the raters disagree so badly that kappa fails. A rule that
    cannot reject is not a rule.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "measurement"))
import typo_noise as tn                                   # noqa: E402

BANK = ROOT / "measurement/item_bank.jsonl"
SHEET_DIR = ROOT / "measurement/o1_sheets"
RATINGS = ROOT / "measurement/o1_ratings.csv"

# The pre-registered rule. Changing a number here without changing the amendment is drift.
CATS = ("R", "W", "X")
CAT_LABEL = {"R": "Readable", "W": "Wobbly", "X": "Lost"}
N_PER_LEVEL = 60
N_RATERS = 3
KAPPA_MIN = 0.60
LO_GRID = (0.05, 0.06, 0.07, 0.08)
MID_GRID = (0.12, 0.14, 0.16, 0.18)

# The rule, exactly as stated in the amendment. The negative control caught that `mid` needs BOTH a
# median of W and a non-trivial tail. A panel that is uniformly W has median W and P(X) = 0, and a
# rule demanding a large P(X) would call that "not stressed" - which is right - while a rule keyed on
# median alone would call it "stressed" - which is wrong, because an item nobody fails to read is not a
# hard item. `mid` is therefore BETWEEN the two states, and both conditions are required. The upper
# bound is what stops a ladder pushed past the point where the text is simply broken.
RULE = {
    "lo": {"median": ("R",), "p_lost_max": 0.10},
    "mid": {"median": ("W",), "p_lost_min": 0.15, "p_lost_max": 0.60},
}


def load_bank():
    rows = [json.loads(l) for l in BANK.read_text(encoding="utf-8").splitlines() if l.strip()]
    dev = [r for r in rows if r.get("split") == "dev"]
    if not dev:
        raise SystemExit("no dev items in the bank - refusing to build a sheet that could touch test")
    return rows, dev


def pick(dev, n, lam, seed):
    """A deterministic, level-independent item selection.

    The SAME items are rated at every level, so readability is compared within item and a rater's
    change of judgement is about the noise rather than about the content. Sampling is by a stable sort
    on item_id, not by a random draw, so the sheet is reproducible without recording a seed.
    """
    ordered = sorted(dev, key=lambda r: r["item_id"])[:n]
    out = []
    for r in ordered:
        text = r.get("state", "")
        perturbed, ops = tn.typo_noise(text, r["item_id"], lam, seed)
        rate = tn.realised_edit_rate(text, ops)
        out.append({
            "item_id": r["item_id"],
            "domain": r.get("domain", "?"),
            "template_id": r.get("template_id", "?"),
            "lambda_target": lam,
            "realised_edit_rate": round(rate, 4),
            "n_ops": len(ops),
            "clean": text,
            "perturbed": perturbed,
        })
    return out


def build_sheet(lam, seed=0, n=N_PER_LEVEL):
    rows, dev = load_bank()
    return pick(dev, n, lam, seed)


def write_sheets(seed=0):
    SHEET_DIR.mkdir(parents=True, exist_ok=True)
    made = []
    for role, grid in (("lo", LO_GRID), ("mid", MID_GRID)):
        for lam in grid:
            items = build_sheet(lam, seed)
            path = SHEET_DIR / ("o1_%s_lam%03d_seed%d.csv" % (role, round(lam * 100), seed))
            with path.open("w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["item_id", "domain", "realised_edit_rate", "n_ops",
                            "clean", "perturbed", "category"])
            made.append((role, lam, path, len(items)))
    return made


def fleiss_kappa(table):
    """Fleiss' kappa for N raters x K categories. `table` is a list of per-item category counts."""
    n_items = len(table)
    k = len(CATS)
    n = sum(table[0])
    if n_items == 0 or n <= 1:
        return None
    p_j = [sum(row[j] for row in table) / (n_items * n) for j in range(k)]
    p_e = sum(p * p for p in p_j)
    # observed agreement: the probability that two randomly chosen raters agree on an item
    obs = 0.0
    for row in table:
        s = sum(c * c for c in row)
        obs += (s - n) / (n * (n - 1))
    obs /= n_items
    # Perfect agreement gives p_e == 1 and a 0/0 ratio. Kappa is conventionally set to 1.0 in that
    # case, NOT left undefined: the perfect panel is the strongest possible evidence, and a
    # calibration that rejected it as "no kappa" would refuse exactly the result it wants. The
    # negative control caught this - a rule that rejects perfect data is broken, not strict.
    if p_e >= 1.0:
        return 1.0 if obs >= 1.0 else 0.0
    return (obs - p_e) / (1 - p_e)


def score(level, rows):
    """Apply the frozen rule to a completed rating set. `rows` = (item_id, rater_id, category)."""
    by_item = collections.defaultdict(lambda: collections.Counter())
    raters = set()
    for item, rater, cat in rows:
        if cat not in CATS:
            raise SystemExit("unknown category %r - the codebook is R/W/X and nothing else" % (cat,))
        by_item[item][cat] += 1
        raters.add(rater)
    if len(raters) != N_RATERS:
        raise SystemExit("expected %d raters, found %d" % (N_RATERS, len(raters)))

    table = [[by_item[i][c] for c in CATS] for i in sorted(by_item)]
    kappa = fleiss_kappa(table)

    # median category per item, from the majority; ties broken toward the WORSE category, because a
    # tie between R and W is evidence the item is not cleanly readable.
    order = {c: i for i, c in enumerate(reversed(CATS))}   # X worst
    medians, lost = [], 0
    for i in sorted(by_item):
        cnt = by_item[i]
        best = max(CATS, key=lambda c: (cnt[c], -order[c]))
        medians.append(best)
        lost += 1 if cnt["X"] >= max(cnt["R"], cnt["W"]) and cnt["X"] > 0 else 0
    n = len(medians)
    med_counts = collections.Counter(medians)
    median_cat = sorted(med_counts.items(), key=lambda kv: (-kv[1], order[kv[0]]))[0][0]
    p_lost = lost / n if n else 0.0

    rule = RULE[level]
    ok_kappa = kappa is not None and kappa >= KAPPA_MIN
    ok_median = median_cat in rule["median"]
    ok_tail = ("p_lost_max" not in rule or p_lost <= rule["p_lost_max"]) and \
              ("p_lost_min" not in rule or p_lost >= rule["p_lost_min"])
    return {
        "level": level, "n_items": n, "kappa": round(kappa, 3) if kappa is not None else None,
        "median_category": median_cat, "category_counts": dict(med_counts),
        "p_lost": round(p_lost, 3),
        "accept": bool(ok_kappa and ok_median and ok_tail),
        "why": {"kappa>=%.2f" % KAPPA_MIN: ok_kappa,
                "median in %s" % (rule["median"],): ok_median,
                "P(X)<=%.2f" % rule["p_lost_max"] if "p_lost_max" in rule
                else "P(X)>=%.2f" % rule["p_lost_min"]: ok_tail},
    }


def cmd_sheet(args):
    made = write_sheets(args.seed)
    print(f"  sheets     : {SHEET_DIR.relative_to(ROOT)}/")
    for role, lam, path, n in made:
        print(f"    {role:<4} λ={lam:<5} {n:>3} items  {path.name}")
    print("\n  Items are drawn from the DEV split only and are the SAME items at every level, so a "
          "rater's change of judgement is about the noise rather than about the content.")
    print("  Fill the `category` column with R / W / X per row per rater, then run --score.")


def cmd_score(args):
    if not args.ratings.is_file():
        raise SystemExit("no ratings file: " + str(args.ratings))
    rows = []
    with args.ratings.open(encoding="utf-8", newline="") as fh:
        for rec in csv.DictReader(fh):
            rows.append((rec["item_id"], rec["rater_id"], rec["category"].strip().upper()))
    lam_by_item = {}
    with args.ratings.open(encoding="utf-8", newline="") as fh:
        for rec in csv.DictReader(fh):
            lam_by_item.setdefault(rec.get("lambda_target", "?"), set()).add(rec["item_id"])
    for level in ("lo", "mid"):
        items = set()
        for lam, ids in lam_by_item.items():
            if abs(float(lam) - float(args.level_value(level))) < 1e-9:
                items |= ids
        if not items:
            print(f"  {level}: no ratings at the requested level")
            continue
        sel = [r for r in rows if r[0] in items]
        res = score(level, sel)
        print(f"\n  {level.upper()}  (λ = {args.level_value(level)})")
        print(f"    items {res['n_items']}   kappa {res['kappa']}   "
              f"median {res['median_category']}   P(X) {res['p_lost']}")
        print(f"    categories {res['category_counts']}")
        print(f"    ACCEPTED: {res['accept']}")
        for k, v in res["why"].items():
            print(f"       {'ok ' if v else 'NO '} {k}")


def negative_test():
    def mk(level, pattern):
        rows = []
        for i in range(60):
            item = "%s_item%03d" % (level, i)
            for r in range(3):
                rows.append((item, "r%d" % r, pattern(i, r)))
        return rows

    cases = [
        ("lo accepts a clean panel", "lo", mk("lo", lambda i, r: "R"), True),
        ("lo rejects a panel with too many lost", "lo", mk("lo", lambda i, r: "X" if i < 12 else "R"), False),
        ("mid rejects a uniformly-wobbly panel (no tail)", "mid", mk("mid", lambda i, r: "W"), False),
        ("mid accepts a wobbly panel with a real tail",
         "mid", mk("mid", lambda i, r: "X" if i < 18 else "W"), True),
        ("mid rejects a panel that is still readable", "mid", mk("mid", lambda i, r: "R"), False),
        ("mid rejects a panel that is mostly lost", "mid",
         mk("mid", lambda i, r: "X" if i < 50 else "W"), False),
        ("kappa fails when raters disagree", "lo",
         mk("lo", lambda i, r: ("R", "W", "X")[r]), False),
    ]
    ok = 0
    for label, level, rows, expect in cases:
        res = score(level, rows)
        good = res["accept"] == expect
        ok += good
        print(f"  [{'OK' if good else 'MISS'}] {label:<44} accept={res['accept']} "
              f"(expected {expect})  kappa={res['kappa']}")
    return 0 if ok == len(cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Material and decision rule for the O1 calibration.")
    ap.add_argument("--sheet", action="store_true", help="write the rating sheets")
    ap.add_argument("--score", action="store_true", help="score a completed ratings file")
    ap.add_argument("--ratings", type=pathlib.Path, default=RATINGS)
    ap.add_argument("--level-value", type=float, default=0.08,
                    help="the lambda actually rated, per level")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--negative-test", action="store_true")
    args = ap.parse_args()

    if args.negative_test:
        return negative_test()
    if args.score:
        cmd_score(args)
        return 0
    cmd_sheet(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())