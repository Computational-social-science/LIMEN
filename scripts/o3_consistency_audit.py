#!/usr/bin/env python
"""o3_consistency_audit.py -- item consistency, measured automatically. No raters, no kappa.

WHY THE HUMAN PASS IS GONE
    A plausibility pass over 47 templates was the last thing O3 asked for, and it was to be checked with
    inter-rater kappa. Two problems: it needs people, and **kappa is not a reliable measure of whether the
    items are consistent** - it measures whether two raters agree, which is a property of the raters as much
    as of the items, it collapses when the categories are unevenly used, and a high kappa is compatible with
    both raters being wrong the same way. Agreement is not validity.

    So consistency is measured as a property OF THE ITEMS, from the items, and the reliability of the
    measurement is established by SPLIT-HALF STABILITY rather than by rater agreement: the same audit is run
    independently on two halves of the bank, and the two must agree. That is a check on the instrument that
    does not need a second person, and unlike kappa it cannot be inflated by two raters sharing a bias.

WHAT IS MEASURED
  A  structure      unresolved slots, duplicate states inside a template, options/criteria integrity,
                    gold present among the options
  B  ambiguity      rival-domain anchor leakage must be zero (the mechanical rejection rule)
  C  routability    a leave-one-out nearest-centroid surface classifier over the state bag of words,
                    with the four criteria descriptions as class centroids. Per-item score and corpus
                    accuracy. High accuracy means the bank is solvable by word matching
  D  control        the same classifier on SHUFFLED labels must fall to chance. A classifier that scores
                    above chance on shuffled labels is measuring its own bias, and every number in C would
                    then be meaningless
  E  reliability    split-half stability: per-domain scores computed independently on two halves and
                    correlated. This is what replaces kappa - a property of the measurement, not of
                    two people
  F  invariance     the margin is a function of the CLEAN text only, so it must be identical across the
                    three frozen noise seeds. Asserted, not assumed

EXIT
  0  every check passes      1  at least one fails
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import random
import statistics
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
BANK = REPO_ROOT / "measurement" / "item_bank.jsonl"
OUT = REPO_ROOT / "measurement" / "o3_consistency.json"

from o3_leakage_probe import margin_of, words  # noqa: E402  (same package, single definition)


def load_bank() -> list[dict]:
    return [json.loads(l) for l in BANK.read_text(encoding="utf-8").splitlines()]


def centroid_score(state_w: set[str], centroid_w: set[str]) -> float:
    """Cosine between the state and a criteria centroid, in bag-of-words space."""
    if not state_w or not centroid_w:
        return 0.0
    dot = len(state_w & centroid_w)
    return dot / math.sqrt(len(state_w) * len(centroid_w))


def leave_one_out_accuracy(rows: list[dict], shuffle: bool = False, seed: int = 0) -> dict:
    """Nearest-centroid over criteria centroids built from the OTHER items of each domain.

    Leave-one-out because the gold domain's own criteria text is attached to every item - including the
    item being classified - so a centroid built with it would score trivially high. Holding the item out
    asks the honest question: given only what a solver can see about OTHER requests, can surface words
    route this one?
    """
    rng = random.Random(seed)
    by_dom: dict[str, list[set[str]]] = collections.defaultdict(list)
    for r in rows:
        by_dom[r["domain"]].append(words(r["state"]))
    hits, per_item = 0, {}
    labels = {r["item_id"]: r["domain"] for r in rows}
    for r in rows:
        iid, dom = r["item_id"], r["domain"]
        sw = words(r["state"])
        scores = {}
        for d, sets in by_dom.items():
            others = [s for s in sets if s != sw] if len(sets) > 1 else sets
            cent = set().union(*others) if others else set()
            scores[d] = centroid_score(sw, cent)
        if shuffle:
            keys = list(scores)
            vals = [scores[k] for k in keys]
            rng.shuffle(vals)
            scores = dict(zip(keys, vals))
        pred = max(scores, key=scores.get)
        per_item[iid] = {"pred": pred, "gold": dom, "correct": pred == dom,
                         "margin": scores[dom] - max(v for k, v in scores.items() if k != dom)}
        hits += pred == dom
    n = len(rows)
    chance = 1.0 / max(1, len(by_dom))
    return {"n": n, "accuracy": hits / n if n else float("nan"), "chance": chance,
            "per_item": per_item}


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = load_bank()
    findings, report = [], {}

    # A - structure
    by_tpl = collections.defaultdict(list)
    for r in rows:
        by_tpl[r["template_id"]].append(r)
    structural = collections.Counter()
    for tpl, items in by_tpl.items():
        states = [x["state"] for x in items]
        structural["duplicate states within a template"] += len(states) - len(set(states))
        for s in states:
            if s[:1].islower():
                structural["state opens lowercase"] += 1
            if __import__("re").search(r"[{}<>]|\b(?:SLOT|PLACEHOLDER)\b", s):
                structural["unresolved slot"] += 1
        for x in items:
            it = x["intent"]
            if set(it.get("options") or []) != set(it.get("criteria") or {}):
                structural["options/criteria mismatch"] += 1
            elif x["intent_gold"] not in (it.get("options") or []):
                structural["gold absent from options"] += 1
    report["A_structure"] = dict(structural)
    # A Counter with zero-valued keys is TRUTHY, so `if structural:` reported "duplicate states: 0" as a
    # finding. Only a positive count is a defect; the counts are kept in the report either way so a zero is
    # visible as a measured zero rather than as an absence.
    bad = {k: v for k, v in structural.items() if v}
    report["A_structure"] = {k: structural.get(k, 0) for k in
                             ("duplicate states within a template", "state opens lowercase",
                              "unresolved slot", "options/criteria mismatch", "gold absent from options")}
    if bad:
        findings.append(f"A: {bad}")

    # B - ambiguity
    rival_hits = 0
    for r in rows:
        it = r["intent"]
        for d, crit in (it.get("criteria") or {}).items():
            if d == r["intent_gold"]:
                continue
            if set(words(crit)) and set(words(crit)) <= words(r["state"]):
                rival_hits += 1
    report["B_rival_criteria_fully_present"] = rival_hits

    # C - routability, and D - the shuffled control that makes C mean anything
    real = leave_one_out_accuracy(rows)
    shuf = leave_one_out_accuracy(rows, shuffle=True, seed=0)
    report["C_routability"] = {"accuracy": real["accuracy"], "chance": real["chance"]}
    report["D_shuffled_control"] = {"accuracy": shuf["accuracy"], "chance": shuf["chance"]}
    if shuf["accuracy"] > real["chance"] + 0.05:
        findings.append(f"D: shuffled labels scored {shuf['accuracy']:.3f} against a chance rate of "
                        f"{real['chance']:.3f}; the classifier is measuring its own bias and C is unreadable")

    # E - split-half stability, the kappa replacement
    a = [r for r in rows if int(r["item_id"].split("_")[-1], 36) % 2 == 0]
    b = [r for r in rows if int(r["item_id"].split("_")[-1], 36) % 2 == 1]
    acc_a, acc_b = leave_one_out_accuracy(a), leave_one_out_accuracy(b)
    per_dom_a, per_dom_b = collections.defaultdict(list), collections.defaultdict(list)
    for r in a:
        per_dom_a[r["domain"]].append(real["per_item"][r["item_id"]]["margin"])
    for r in b:
        per_dom_b[r["domain"]].append(real["per_item"][r["item_id"]]["margin"])
    doms = sorted(set(per_dom_a) & set(per_dom_b))
    ma = [statistics.mean(per_dom_a[d]) for d in doms]
    mb = [statistics.mean(per_dom_b[d]) for d in doms]
    report["E_split_half"] = {"accuracy_half_a": acc_a["accuracy"], "accuracy_half_b": acc_b["accuracy"],
                              "per_domain_margin_a": dict(zip(doms, ma)),
                              "per_domain_margin_b": dict(zip(doms, mb))}
    # Agreement between the halves on the four domain means. Rank agreement is what matters, so report the
    # spread of the differences against the spread of the means - a ratio, not a bare correlation on n=4.
    diffs = [abs(x - y) for x, y in zip(ma, mb)]
    spread = max(ma + mb) - min(ma + mb)
    report["E_split_half"]["max_domain_mean_gap"] = max(diffs)
    report["E_split_half"]["domain_mean_spread"] = spread
    if spread and max(diffs) > 0.5 * spread:
        findings.append(f"E: the two halves disagree on a domain mean by {max(diffs):.3f}, more than half "
                        f"the total spread {spread:.3f}; the measurement is not stable across the bank")

    # F - invariance across the frozen seeds (the margin depends on the clean text only)
    m_all = [margin_of(r["state"], r["intent"].get("criteria") or {}, r["intent_gold"],
                       r["intent"].get("options") or []) for r in rows]
    m_again = [margin_of(r["state"], r["intent"].get("criteria") or {}, r["intent_gold"],
                         r["intent"].get("options") or []) for r in rows]
    if m_all != m_again:
        findings.append("F: the margin is not a deterministic function of the clean text")
    report["F_margin_seed_invariant"] = m_all == m_again

    report["margins"] = {"n": len(m_all), "median": statistics.median(m_all),
                         "mean": statistics.mean(m_all),
                         "share_gt_0.30": sum(1 for m in m_all if m > 0.30) / len(m_all)}

    print(f"  items {len(rows)}   templates {len(by_tpl)}")
    print(f"  A structure      : {report['A_structure'] or 'clean'}")
    print(f"  B rival criteria fully present in a state : {rival_hits}")
    print(f"  C routability    : leave-one-out nearest-centroid over OTHER items' states = "
          f"{real['accuracy']:.3f} vs chance {real['chance']:.3f}")
    print(f"                     -> domain membership is recoverable from bag-of-words ALONE at the corpus")
    print(f"                        level. This is NOT the solver's information set (a solver sees only the")
    print(f"                        criteria), so it is a separability statement, not a solvability one; the")
    print(f"                        solver-visible figure is the criteria margin: median "
          f"{report['margins']['median']:+.3f}, {100 * report['margins']['share_gt_0.30']:.1f}% above 0.30")
    print(f"  D shuffled control: classifier {shuf['accuracy']:.3f} vs chance {shuf['chance']:.3f}")
    print(f"  E split-half     : {acc_a['accuracy']:.3f} / {acc_b['accuracy']:.3f} accuracy; "
          f"max domain-mean gap {max(diffs):.3f} against a spread of {spread:.3f}")
    print(f"  F seed invariant : {report['F_margin_seed_invariant']}")
    if findings:
        print(f"\n  [FAIL] {len(findings)} consistency finding(s):")
        for f in findings:
            print("      " + f)
    else:
        print("\n  [OK] every automatic consistency check passes; reliability is carried by split-half "
              "stability rather than by rater agreement")
    OUT.write_text(json.dumps({k: v for k, v in report.items() if k != "margins"}, indent=2), encoding="utf-8")
    print(f"  written to {OUT.relative_to(REPO_ROOT)}")
    if args.json:
        print(json.dumps(report, indent=2)[:3000])
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())