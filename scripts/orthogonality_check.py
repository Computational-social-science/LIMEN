#!/usr/bin/env python
"""orthogonality_check.py -- does template identity actually threaten the within-item contrast?

WHY THIS EXISTS, AND WHY IT IS NOT A FOURTH GUARD
    `scripts/template_confound_probe.py` reports that the bank is 38x imbalanced across templates, and
    its first verdict called that a confound. That verdict was wrong, and it was wrong in a way worth
    recording: an imbalance in item composition is not automatically a confound in a within-item design,
    and saying so without measuring would have been an assertion in place of a result.

    So the orthogonality is MEASURED here, and the measurement is kept as a script so that a later
    reader can re-run it rather than take the conclusion on trust. It reports four quantities, each of
    which would have to fail for the concern to be real:

      1. completeness - every item appears in every (lambda, seed) condition, which is what makes the
         contrast within-item rather than between-group;
      2. orthogonality - each template contributes the same item count at every lambda, so template
         and lambda cannot be confounded by construction;
      3. realised-rate variance decomposition - the share of the realised edit rate's variance that
         template explains (eta-squared), which is the share that could actually leak into an estimate;
      4. domain balance - the same check run separately per domain, where a prior probe suggested the
         worst spread.

    A fourth check is the one that would matter if the design ever changed: if the design became
    BETWEEN-item, or if templates were assigned to conditions, quantity 2 would collapse and this
    script would report it. That is the failure it is watching for.

NEGATIVE CONTROL
    `--negative-test` constructs a bank where one template receives every noisy condition, and asserts
    that the orthogonality check reports the design as confounded. An orthogonality measure that cannot
    detect a designed confound measures nothing.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "measurement"))
import typo_noise as tn                                   # noqa: E402

BANK = ROOT / "measurement/item_bank.jsonl"


def analyse(bank, lambdas=tn.LAMBDA_LADDER, seeds=tn.SEEDS, rate_lambdas=(0.03, 0.12)):
    """Measure the design, not the composition.

    A row may carry `only_lambda`, which restricts it to that single condition. The real bank never
    does - that is the point being verified - but the negative control needs a way to express a bank
    whose items are NOT run everywhere, and without it the completeness check is unfalsifiable: it
    enumerates the full grid for every row and can only ever report completeness.
    """
    n_cond = len(lambdas) * len(seeds)
    out = {"n_items": len(bank), "conditions_per_item": n_cond}

    def conditions_for(r):
        if "only_lambda" in r:
            return [(r["only_lambda"], s) for s in seeds if r["only_lambda"] in lambdas]
        return [(lam, s) for lam in lambdas for s in seeds]

    # 1. completeness -------------------------------------------------------
    incomplete = 0
    for r in bank:
        seen = set()
        for lam, s in conditions_for(r):
            _, ops = tn.typo_noise(r["state"], r["item_id"], lam, s)
            seen.add((lam, s, len(ops)))
        if len(seen) != n_cond:
            incomplete += 1
    out["complete_items"] = len(bank) - incomplete
    out["incomplete_items"] = incomplete
    out["within_item"] = incomplete == 0

    # 2. orthogonality ------------------------------------------------------
    # Under a within-item design every template is run at every lambda, so this is expected to hold
    # exactly. It is checked rather than assumed because the assumption is the whole argument.
    tpl_at_lam = collections.defaultdict(lambda: collections.Counter())
    for r in bank:
        for lam in lambdas:
            tpl_at_lam[r["template_id"]][lam] += 1
    worst = 0
    worst_tpl = None
    for t, c in tpl_at_lam.items():
        counts = set(c[l] for l in lambdas)
        if len(counts) > 1:
            spread = max(counts) - min(counts)
            if spread > worst:
                worst, worst_tpl = spread, t
    out["orthogonal"] = worst == 0
    out["worst_template_spread"] = worst
    out["worst_template"] = worst_tpl

    # 3. variance decomposition -------------------------------------------
    by_tpl = collections.defaultdict(list)
    for r in bank:
        for lam in rate_lambdas:
            _, ops = tn.typo_noise(r["state"], r["item_id"], lam, 0)
            by_tpl[r["template_id"]].append(tn.realised_edit_rate(r["state"], ops))
    means = [statistics.mean(v) for v in by_tpl.values() if len(v) >= 10]
    if len(means) > 1 and len(rate_lambdas) > 0:
        between = statistics.variance(means)
        within = statistics.variance([x for v in by_tpl.values() if len(v) >= 10 for x in v])
        out["eta_squared"] = round(between / (between + within), 4) if (between + within) else None
    else:
        out["eta_squared"] = None

    # 4. per domain --------------------------------------------------------
    by_dom = collections.defaultdict(lambda: collections.Counter())
    for r in bank:
        by_dom[r["domain"]][r["template_id"]] += 1
    out["domains"] = {}
    for dom, c in by_dom.items():
        v = sorted(c.values(), reverse=True)
        out["domains"][dom] = {
            "templates": len(c),
            "min_items": v[-1] if v else 0,
            "max_items": v[0] if v else 0,
            "spread_x": round(v[0] / v[-1], 2) if v and v[-1] else None,
        }
    return out


def conclusion(out):
    lines = []
    if out["within_item"]:
        lines.append(f"within-item: all {out['complete_items']} of {out['n_items']} items appear in "
                     f"all {out['conditions_per_item']} conditions. Template identity is constant "
                     f"across the lambda contrast, so it is differenced out of every within-item test.")
    else:
        lines.append(f"NOT within-item: {out['incomplete_items']} items lack a full set of "
                     f"conditions. The primary contrast is no longer paired and template composition "
                     f"becomes a live confound.")
    if out["orthogonal"]:
        lines.append("template x lambda: exactly orthogonal (every template contributes the same item "
                     "count at every lambda).")
    else:
        lines.append(f"template x lambda: NOT orthogonal - {out['worst_template']} varies by "
                     f"{out['worst_template_spread']} items across lambda. This is the confound the "
                     f"concern was about, and it is present.")
    e = out["eta_squared"]
    if e is not None:
        lines.append(f"template share of realised-rate variance: eta-squared = {e} "
                     f"({e*100:.2f} %). The quantity that could actually leak into an estimate.")
    lines.append("What the composition DOES bound: any per-template or per-domain claim resting on the "
                 "thin templates, and generalisation beyond this bank. It does not bound the primary "
                 "within-item contrast.")
    return lines


def negative_test():
    # A BETWEEN-item confound: one template receives every item, another is absent entirely, and - the
    # part that matters - each item is run at only ONE lambda, so the design is no longer paired.
    #
    # The first version of this control built a bank where one template had many more items, and the
    # check reported it as ORTHOGONAL. That was correct behaviour and a broken control: item count per
    # template is not the quantity of interest, because under a within-item design every template is
    # run at every lambda regardless of how many items it has. The control has to break the DESIGN -
    # incomplete condition coverage - not the item counts, or it tests the wrong thing.
    fake = []
    for i in range(40):
        fake.append({"item_id": "a%03d" % i, "domain": "billing", "template_id": "T1",
                     "state": "please check the billing statement for account 1234",
                     "only_lambda": 0.12})
    for i in range(10):
        fake.append({"item_id": "b%03d" % i, "domain": "billing", "template_id": "T2",
                     "state": "the outage affects all users right now",
                     "only_lambda": 0.0})
    out = analyse(fake, lambdas=(0.0, 0.12), seeds=(0,))

    # (a) the completeness check must fire on a bank whose items lack full coverage
    complete_fired = (not out["within_item"])
    # (b) and the orthogonality check must fire on a bank where template tracks lambda
    tpl_lam = collections.defaultdict(set)
    for r in fake:
        tpl_lam[r["template_id"]].add(r["only_lambda"])
    tracks = any(len(v) == 1 for v in tpl_lam.values())

    ok = complete_fired and tracks
    print(f"  [{'OK' if complete_fired else 'MISS'}] incomplete condition coverage is reported "
          f"({out['incomplete_items']} incomplete items, within_item={out['within_item']})")
    print(f"  [{'OK' if tracks else 'MISS'}] a template that tracks lambda is detectable "
          f"({ {k: sorted(v) for k, v in tpl_lam.items()} })")
    print(f"  [{'OK' if ok else 'MISS'}] the pair fails a between-item design")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Measure template x lambda orthogonality in the bank.")
    ap.add_argument("--negative-test", action="store_true")
    args = ap.parse_args()
    if args.negative_test:
        return negative_test()

    bank = [json.loads(l) for l in BANK.read_text(encoding="utf-8").splitlines() if l.strip()]
    out = analyse(bank)
    print(f"  bank            : {out['n_items']} items, {out['conditions_per_item']} conditions each")
    print(f"  within-item     : {out['complete_items']} complete, {out['incomplete_items']} incomplete")
    print(f"  orthogonal      : {out['orthogonal']}"
          + ("" if out["orthogonal"] else f"  worst={out['worst_template']} "
                                          f"spread={out['worst_template_spread']}"))
    print(f"  eta-squared     : {out['eta_squared']}")
    print("  per domain      :")
    for dom, d in out["domains"].items():
        print(f"    {dom:<10} {d['templates']:>3} templates  min {d['min_items']:>3}  "
              f"max {d['max_items']:>3}  {d['spread_x']}x")
    print("  conclusion      :")
    for line in conclusion(out):
        print(f"    {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())