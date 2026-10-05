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


def margin_of(state: str, criteria: dict, gold: str, options: list) -> float:
    """leak_gold - max(leak_rival). Split out so the self-test can exercise it on known cases."""
    sw = words(state)
    ov = {}
    for d in options:
        cw = words(criteria.get(d, ""))
        ov[d] = (len(sw & cw) / len(cw)) if cw else 0.0
    rivals = [ov[d] for d in options if d != gold]
    return ov[gold] - (max(rivals) if rivals else 0.0)


def self_test() -> int:
    """Known-answer controls for the margin.

    Written because the probe computed a metric and published 932 numbers with nothing behind it. Every
    metric in this project has been wrong at least once in a way only a known-answer case caught: kappa
    divided a proportion by n instead of n^2, and a channel's insertion branch divided by the wrong
    denominator and exceeded one on common letters. A margin is simpler, which is not the same as checked.
    """
    fails = []
    crit = {"access": "a request about getting in: sign-in, a password, a permission, or an account lock",
            "billing": "a request about money: a charge, an invoice, a refund, or a subscription"}
    opts = ["access", "billing"]

    all_gold = words(crit["billing"])
    if abs(margin_of(" ".join(sorted(all_gold)), crit, "billing", opts) - 1.0) > 1e-9:
        fails.append(f"a state made entirely of the gold criteria words should give margin 1.0, gave "
                     f"{margin_of(' '.join(sorted(all_gold)), crit, 'billing', opts)}")

    disjoint = "please reverse the renewal and confirm by email"
    m = margin_of(disjoint, crit, "billing", opts)
    if m != 0.0:
        fails.append(f"a state sharing nothing with either criterion should give margin 0, gave {m}")

    both = words(crit["billing"]) | words(crit["access"])
    m = margin_of(" ".join(sorted(both)), crit, "billing", opts)
    if m != 0.0:
        fails.append(f"a state covering BOTH criteria fully should give margin 0, gave {m}")

    # The rival max must exclude the gold even when the gold is also the largest
    m = margin_of("charge invoice refund subscription", crit, "billing", opts)
    if m < 0:
        fails.append(f"a gold-only state gave a negative margin ({m}); the rival max is including the gold")

    if fails:
        print("  [FAIL] margin self-test:")
        for f in fails:
            print("      -", f)
        return 1
    print("  [OK] margin self-test: gold-only -> 1.0 · disjoint -> 0 · both-criteria -> 0 · "
          "rival max excludes the gold")
    return 0


def template_audit(rows) -> int:
    """Mechanical checks on each template. What a reader would NOT have to look at.

    The human pass is for PLAUSIBILITY - whether a request looks like something a person would write.
    Everything mechanical is removed from their list first, so the 47 items they read are read for the one
    thing only they can judge.
    """
    import collections
    by_tpl = collections.defaultdict(list)
    for r in rows:
        by_tpl[r["template_id"]].append(r)
    problems = collections.Counter()
    findings = []
    for tpl, items in sorted(by_tpl.items()):
        states = [x["state"] for x in items]
        for s in states:
            if re.search(r"[{}<>]|\b(?:SLOT|PLACEHOLDER|NAN|None)\b", s):
                problems["unresolved slot or placeholder"] += 1
                findings.append(f"{tpl}: placeholder in state -> {s[:70]}")
            if not s[:1].isupper():
                problems["state does not start with a capital"] += 1
            if not s.rstrip().endswith((".", "?", "!")):
                problems["state has no terminal punctuation"] += 1
        dups = len(states) - len(set(states))
        if dups:
            problems["duplicate states within a template"] += dups
            findings.append(f"{tpl}: {dups} duplicate state(s) inside one template")
        # the option set and the criteria must cover exactly the same domains
        for x in items:
            it = x["intent"]
            o = set(it.get("options") or [])
            c = set((it.get("criteria") or {}))
            if o != c:
                problems["options and criteria disagree"] += 1
                findings.append(f"{tpl}: options {sorted(o)} vs criteria {sorted(c)}")
                break
            if x["intent_gold"] not in o:
                problems["gold is not among the options"] += 1
                findings.append(f"{tpl}: gold {x['intent_gold']} not in {sorted(o)}")
                break

    print(f"  template audit: {len(by_tpl)} templates, {len(rows)} items")
    if problems:
        for k, v in problems.most_common():
            print(f"    [FAIL] {k}: {v}")
        for f in findings[:10]:
            print("        " + f)
        return 1
    print("    [OK] no unresolved slots, no duplicate states inside a template, every option set")
    print("         matches its criteria block, and the gold is among the options")
    return 0


def review_pack(rows, out: pathlib.Path) -> None:
    """One item per template, chosen deterministically, for the plausibility pass.

    The stratification is justified by eta^2 = 0.9142 (templates explain 91.4% of the variance in the
    routability margin, and the between-template spread is 6.5x the within). This writes the 47 items so
    the pass is a single sitting rather than a sweep of 932.
    """
    import collections
    import csv as _csv
    best = {}
    for r in sorted(rows, key=lambda x: x["item_id"]):
        best.setdefault(r["template_id"], r)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = _csv.writer(fh)
        w.writerow(["template_id", "item_id", "domain", "intent_gold", "n_options",
                    "leak_margin", "state", "options", "criteria"])
        for tpl in sorted(best):
            r = best[tpl]
            it = r["intent"]
            o = it.get("options") or []
            m = margin_of(r["state"], it.get("criteria") or {}, r["intent_gold"], o)
            w.writerow([tpl, r["item_id"], r["domain"], r["intent_gold"], len(o), f"{m:+.3f}",
                        r["state"], " | ".join(o),
                        " || ".join(f"{d}: {it['criteria'][d]}" for d in o)])
    print(f"  review pack: {len(best)} items (one per template) -> {out.relative_to(REPO_ROOT)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--top", type=int, default=12, help="how many worst items to list")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true", help="known-answer controls for the margin")
    ap.add_argument("--template-audit", action="store_true", help="mechanical checks, one per template")
    ap.add_argument("--review-pack", action="store_true",
                    help="write one item per template for the plausibility pass")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    rows = [json.loads(l) for l in BANK.read_text(encoding="utf-8").splitlines()]

    if args.template_audit:
        return template_audit(rows)

    if args.review_pack:
        review_pack(rows, REPO_ROOT / "measurement" / "o3_review_pack.csv")
        return 0

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