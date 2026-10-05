#!/usr/bin/env python
"""o3_leakage_probe.py -- can an item be answered by SURFACE MATCHING against its own criteria?

WHY THIS EXISTS
    O3's remaining human pass is only ever needed to confirm that an item is plausible and unambiguous -
    never to decide its answer, because `intent_gold` is a construction invariant (the item is rendered
    from a scenario kernel whose domain is known). So the question a human pass adds is "would a reader
    find this clear", and that is a measured question.

    But there is a second question a human pass would NOT reliably answer, and it is a bigger threat to the
    experiment: **every item ships the four domain CRITERIA as part of the question** (each option is a
    domain label with a definition attached). If the state text shares more content words with the gold
    domain's definition than with the rivals', then the item can be routed by lexical overlap rather than
    by understanding what the request is about. A model that never reads the criteria but pattern-matches
    the text would score well, and H1 would be measuring keyword sensitivity instead of semantic routing.

    This is not hypothetical: the criteria are written in the same domain vocabulary as the states
    ("charge", "invoice", "password", "lock"), so the overlap is a design property to be measured.

WHAT IT MEASURES
    For each item and each option d:
        overlap(state, criteria[d]) = |content_words(state) INTERSECT content_words(criteria[d])|
                                      / |content_words(criteria[d])|
    `leak_gold`  = overlap for the gold domain
    `leak_rival` = the largest overlap among the non-gold options
    `margin`     = leak_gold - leak_rival      (>0 means the surface favours the right answer)

    `margin > 0` is not automatically bad - some overlap is unavoidable and even desirable, because a
    request about a charge SHOULD mention charges. The defect is a margin so large that the rival options
    are effectively eliminated without reading them.

WHAT IT DOES NOT DO
    It does not edit the bank. A measured property that triggers a redesign is a finding; silently
    rewording the criteria to lower the overlap would destroy the evidence that the overlap existed.
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import statistics
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BANK = REPO_ROOT / "measurement" / "item_bank.jsonl"
OUT = REPO_ROOT / "measurement" / "o3_leakage.json"

STOP = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "of", "to", "in", "on", "at", "for",
    "with", "about", "or", "and", "that", "this", "it", "its", "as", "by", "from", "into", "not", "no",
    "my", "our", "your", "their", "i", "we", "you", "they", "me", "us", "them", "should", "which",
    "request", "getting", "one", "some", "any", "if", "so", "but", "than", "then", "when", "what",
}


def words(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'-]+", text)} - STOP


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--top", type=int, default=12, help="how many worst items to list")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = [json.loads(l) for l in BANK.read_text(encoding="utf-8").splitlines()]
    recs = []
    for r in rows:
        intent = r["intent"]
        crit = intent.get("criteria") or {}
        opts = intent.get("options") or list(crit)
        gold = r["intent_gold"]
        if gold not in crit:
            continue
        sw = words(r["state"])
        ov = {}
        for d in opts:
            cw = words(crit.get(d, ""))
            ov[d] = (len(sw & cw) / len(cw)) if cw else 0.0
        rivals = [ov[d] for d in opts if d != gold]
        recs.append({"item_id": r["item_id"], "domain": r["domain"], "gold": gold,
                     "leak_gold": ov[gold], "leak_rival": max(rivals) if rivals else 0.0,
                     "margin": ov[gold] - (max(rivals) if rivals else 0.0),
                     "n_options": len(opts)})

    if not recs:
        print("  [FAIL] no item carried a criteria block for its own gold; nothing to measure")
        return 1

    margins = [x["margin"] for x in recs]
    print(f"  items scored: {len(recs)}   options per item: "
          f"{dict(collections.Counter(x['n_options'] for x in recs))}")
    print(f"  margin (leak_gold - leak_rival):  median {statistics.median(margins):+.3f}   "
          f"mean {statistics.mean(margins):+.3f}   min {min(margins):+.3f}   max {max(margins):+.3f}")
    for t in (0.0, 0.10, 0.20, 0.30):
        share = sum(1 for m in margins if m > t) / len(margins)
        print(f"    share with margin > {t:<5.2f}: {share:.3f}")
    print(f"  items where the state does NOT lexically favour the gold (margin <= 0): "
          f"{sum(1 for m in margins if m <= 0)} "
          f"({100 * sum(1 for m in margins if m <= 0) / len(margins):.1f} %)")

    by_dom = collections.defaultdict(list)
    for x in recs:
        by_dom[x["domain"]].append(x["margin"])
    print("\n  by domain (median margin):")
    for d, ms in sorted(by_dom.items()):
        print(f"    {d:10s} n={len(ms):4d}  median {statistics.median(ms):+.3f}")

    worst = sorted(recs, key=lambda x: -x["margin"])[: args.top]
    print(f"\n  worst {len(worst)} by margin — these are routable by surface overlap alone:")
    for x in worst:
        print(f"    {x['item_id']:22s} gold={x['gold']:8s} leak_gold={x['leak_gold']:.3f} "
              f"rival={x['leak_rival']:.3f} margin={x['margin']:+.3f}")

    payload = {"n": len(recs), "median_margin": statistics.median(margins),
               "mean_margin": statistics.mean(margins),
               "share_margin_gt_0.20": sum(1 for m in margins if m > 0.20) / len(margins),
               "share_margin_le_0": sum(1 for m in margins if m <= 0) / len(margins),
               "by_domain_median": {d: statistics.median(ms) for d, ms in by_dom.items()},
               "worst": worst}
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, indent=2))
    print(f"\n  written to {OUT}")
    print("  NOTE: this measures a CONFOUND, it does not fix one. Rewording the criteria to lower the")
    print("        overlap would destroy the evidence that the overlap was there; the response is to")
    print("        pre-register the margin as a covariate, or to say which items are affected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())