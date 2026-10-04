#!/usr/bin/env python
"""template_confound_probe.py -- is the template a confound, or is the bank homogeneous?

THE QUESTION
    Option C expanded the bank from 12 to 48 templates per domain so that content diversity would not
    be confounded with the noise manipulation. That decision is only safe if the templates are
    actually used in comparable numbers. If one template carries 38 items and another carries 1, then
    a condition effect estimated across items is partly a comparison between templates - and the
    within-item design no longer isolates lambda, because item identity and template identity are
    partly the same variable.

    So this measures the distribution rather than asserting it is harmless. The earlier build report
    found 47 of 48 templates in use with a 38x spread, which is exactly the situation in which the
    claim needs evidence rather than reassurance.

WHAT IT DOES, AND DELIBERATELY DOES NOT DO
    It reads the sealed bank and reports, per domain and overall: templates used, items per template,
    the spread, the imbalance ratio, and the per-condition template histogram overlap. It computes no
    accuracy and touches no model, so it can run before the confirmatory path exists.

    It does NOT decide whether the bank is adequate. That judgement needs the readability calibration
    (O1) and the human pass (O3), both of which are named blockers in the protocol's section 12. This
    probe removes one *measurable* objection and leaves the others exactly where they were.

NEGATIVE CONTROL
    `--negative-test` builds a bank that is deliberately concentrated on one template and asserts the
    probe reports it. A concentration measure that cannot detect concentration measures nothing.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BANK = ROOT / "measurement/item_bank.jsonl"


def load(path=BANK):
    if not path.is_file():
        raise SystemExit("item bank not found: measurement/item_bank.jsonl - run "
                         "scripts/build_item_bank.py first")
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def split_of(row):
    return row.get("split", "?")


def report(rows):
    by_dom = collections.defaultdict(list)
    for r in rows:
        by_dom[r.get("domain", "?")].append(r)

    out = {"total_items": len(rows), "domains": {}}
    for dom, items in sorted(by_dom.items()):
        tpl = collections.Counter(i.get("template_id", "?") for i in items)
        counts = sorted(tpl.values(), reverse=True)
        spread = (counts[0] / counts[-1]) if counts and counts[-1] else float("inf")
        # condition balance per template: does a template appear in both split arms equally?
        per_tpl_split = collections.defaultdict(collections.Counter)
        for i in items:
            per_tpl_split[i.get("template_id", "?")][split_of(i)] += 1
        out["domains"][dom] = {
            "items": len(items),
            "templates_used": len(tpl),
            "items_per_template": {"min": counts[-1] if counts else 0,
                                   "max": counts[0] if counts else 0,
                                   "median": statistics.median(counts) if counts else 0,
                                   "imbalance_ratio": round(spread, 2)},
            "by_split": {t: dict(c) for t, c in sorted(per_tpl_split.items())},
        }

    all_tpl = collections.Counter(r.get("template_id", "?") for r in rows)
    counts = sorted(all_tpl.values(), reverse=True)
    out["overall"] = {
        "templates_used": len(all_tpl),
        "items_per_template": {"min": counts[-1] if counts else 0,
                               "max": counts[0] if counts else 0,
                               "median": statistics.median(counts) if counts else 0,
                               "imbalance_ratio": round(counts[0] / counts[-1], 2)
                               if counts and counts[-1] else None},
    }
    return out


def verdict(out):
    """A measurement with no threshold is not a verdict. Thresholds are stated, not tuned."""
    lines = []
    ov = out["overall"]
    ratio = ov["items_per_template"]["imbalance_ratio"]
    if ratio is None:
        return ["no template information: every item shares one template"]
    if ratio > 3.0:
        lines.append(f"IMBALANCE {ratio}x across templates (max {ov['items_per_template']['max']}, "
                     f"min {ov['items_per_template']['min']}). Template identity is partly "
                     f"confounded with condition; report per-template results or rebalance.")
    else:
        lines.append(f"homogeneous within {ratio}x; template is unlikely to confound the "
                     f"within-item contrast.")
    for dom, d in out["domains"].items():
        r = d["items_per_template"]["imbalance_ratio"]
        if r and r > 3.0:
            lines.append(f"  {dom}: {r}x imbalance across {d['templates_used']} templates.")
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(description="Measure template homogeneity in the sealed item bank.")
    ap.add_argument("--negative-test", action="store_true")
    args = ap.parse_args()

    if args.negative_test:
        # A deliberately concentrated bank must be reported as imbalanced.
        fake = [{"template_id": "T1", "domain": "billing", "split": "test"} for _ in range(20)]
        fake += [{"template_id": "T2", "domain": "billing", "split": "test"}]
        out = report(fake)
        v = verdict(out)
        ratio = out["overall"]["items_per_template"]["imbalance_ratio"]
        ok = any("IMBALANCE" in x for x in v) and ratio and ratio > 3
        print(f"  [{'OK' if ok else 'MISS'}] a 20:1 concentration is reported as an imbalance")
        return 0 if ok else 1

    rows = load()
    out = report(rows)
    print(f"  bank        : measurement/item_bank.jsonl  ({out['total_items']} items)")
    print(f"  templates   : {out['overall']['templates_used']} used")
    ip = out["overall"]["items_per_template"]
    print(f"  per template: min {ip['min']}, median {ip['median']}, max {ip['max']}, "
          f"imbalance {ip['imbalance_ratio']}x")
    print("  per domain:")
    for dom, d in out["domains"].items():
        i = d["items_per_template"]
        print(f"    {dom:<10} {d['items']:>4} items  {d['templates_used']:>3} templates  "
              f"min {i['min']:>3} max {i['max']:>3}  {i['imbalance_ratio']}x")
    print("  verdict:")
    for line in verdict(out):
        print(f"    {line}")
    print("\n  NOTE: this measures ONE measurable objection. The remaining blockers for sealing "
          "the bank are O1 (lambda readability calibration) and the O3 human pass, both named in "
          "the protocol's section 12. Neither is addressed by a homogeneity number.")
    return 0


if __name__ == "__main__":
    sys.exit(main())