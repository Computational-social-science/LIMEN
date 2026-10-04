#!/usr/bin/env python
"""c2_noul_validity.py -- is the `noul` primitive measuring the STATE, or its own labels?

The pinned instrument's card warns that `noul` can "follow its option labels instead of the state",
returning a confident "no" for clearly positive input, and documents a workaround: ask the same
question as a two-option `choice` with NEUTRAL keys.

This is a VALIDITY check, not a hypothesis test and not tuning. If the primitive does not measure what
the protocol's 3.1 wire format says it measures, every number computed from `ok` and `escalate` is
void -- which is why this check is inside the pipeline's remit.

DESIGN
    Two probe sets whose intended answers are not in doubt:
      POSITIVE -- unambiguous, self-contained, actionable requests.
      NEGATIVE -- requests that lack the information needed to act.
    Each probe is asked three ways:
      1. `noul` direct, as the protocol's wire format specifies.
      2. The documented workaround: a two-option `choice` with neutral keys (A/B), so the key text
         carries no semantic content the model could follow.
    A primitive that measures the state must SEPARATE the two sets. The metric is the separation
    (mean p(true) on POSITIVE minus on NEGATIVE) and the classification accuracy at a 0.5 threshold.

    Byte-identical states are used across the two methods, so any difference is the primitive, not
    the input.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys

PINNED_REVISION = "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"

# --- probes: intended answers are not in doubt -----------------------------------------
PROBES = [
    # (id, polarity, state)
    ("c2_pos_01", "pos", "Hi, I was charged twice for my subscription this month and the second "
                          "charge was not authorised. Please refund the duplicate charge."),
    ("c2_pos_02", "pos", "My invoice for March shows a $40 line item I do not recognise. I need it "
                          "explained and, if it is an error, removed."),
    ("c2_pos_03", "pos", "I need my account access restored: the password reset email never arrives "
                          "and I am locked out of the dashboard."),
    ("c2_pos_04", "pos", "Our team's production service is returning errors for every request since "
                          "09:15 this morning. Please escalate this now."),
    ("c2_pos_05", "pos", "The annual plan renewed today but I cancelled it last week. Please reverse "
                          "the renewal and confirm by email."),
    ("c2_pos_06", "pos", "I want to change the card on file for my subscription before the next "
                          "billing date, which is in three days."),
    ("c2_neg_01", "neg", "Something is wrong with my account. Please look into it and let me know "
                          "what you find."),
    ("c2_neg_02", "neg", "It is not working. Can you fix it?"),
    ("c2_neg_03", "neg", "I have a problem. Please advise."),
    ("c2_neg_04", "neg", "There seems to be an issue somewhere. Thanks."),
    ("c2_neg_05", "neg", "Please review my account and do the needful."),
    ("c2_neg_06", "neg", "Things are not as they should be. Let me know."),
]

# Question under test: the protocol's `ok` question.
OK_INSTRUCTIONS = "Is the request clear enough to act on?"


def q_noul() -> dict:
    """Method 1: `noul` exactly as the protocol's 3.1 wire format specifies."""
    return {
        "ok": {"type": "noul", "instructions": OK_INSTRUCTIONS},
    }


def q_workaround() -> dict:
    """Method 2: the card's documented workaround -- two-option choice, NEUTRAL keys.

    The keys are A/B so the option text carries no semantic content to follow; the meaning is placed
    in the criteria, which describe the decision rule rather than the answer.
    """
    return {
        "ok": {
            "type": "choice",
            "instructions": f"{OK_INSTRUCTIONS} Choose A if it is clear enough to act on, B if it is not.",
            "options": ["A", "B"],
            "criteria": {
                "A": "the request contains enough specific information to act on",
                "B": "the request lacks the information needed to act on it",
            },
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="noul primitive validity check.")
    ap.add_argument("--revision", default=PINNED_REVISION)
    ap.add_argument("--device", default=None)
    ap.add_argument("--out", default="measurement/c2_noul_validity.json")
    args = ap.parse_args()

    import torch
    import laya
    from laya import Router

    print("=" * 78)
    print("C2 -- noul primitive validity: state or labels?")
    print("=" * 78)
    print(f"laya {laya.__version__} | torch {torch.__version__} | cuda {torch.cuda.is_available()}")
    router = Router(device=args.device, revision=args.revision)
    agent = router.load("english")
    print(f"resolved rev: {getattr(agent, 'revision', None)}   device: {agent.device}")
    print(f"probes: {len(PROBES)} ({sum(1 for p in PROBES if p[1]=='pos')} positive, "
          f"{sum(1 for p in PROBES if p[1]=='neg')} negative)")
    print()

    rows = []
    for pid, pol, state in PROBES:
        r_noul = router.predict(state, q_noul())
        r_work = router.predict(state, q_workaround())

        p_true = float(r_noul["answers"]["ok"]["noul"])
        w = r_work["answers"]["ok"]
        probs = w["probabilities"]
        # A = clear enough to act on -> p(true) is P(A)
        p_true_work = float(probs.get("A", 0.0))

        rows.append({
            "probe_id": pid, "polarity": pol, "state": state,
            "noul_p_true": p_true, "noul_c": max(p_true, 1 - p_true),
            "workaround_p_true": p_true_work, "workaround_c": max(p_true_work, 1 - p_true_work),
            "workaround_argmax": w["choice"],
        })
        print(f"  {pid} [{pol}]  noul p(true)={p_true:.4f}   workaround p(A)={p_true_work:.4f} "
              f"(argmax={w['choice']})")

    def sep(key):
        pos = [r[key] for r in rows if r["polarity"] == "pos"]
        neg = [r[key] for r in rows if r["polarity"] == "neg"]
        return statistics.mean(pos), statistics.mean(neg), statistics.mean(pos) - statistics.mean(neg)

    def acc(key):
        # a perfect primitive puts pos above 0.5 and neg below it
        ok = sum(1 for r in rows if (r[key] >= 0.5) == (r["polarity"] == "pos"))
        return ok / len(rows)

    print()
    print("  === does each method SEPARATE the two sets? ===")
    print(f"  {'method':<26}{'mean pos':>10}{'mean neg':>10}{'separation':>12}{'accuracy@0.5':>14}")
    res = {}
    for name, key in (("noul (as specified)", "noul_p_true"), ("workaround (neutral A/B)", "workaround_p_true")):
        mp, mn, s = sep(key)
        a = acc(key)
        res[name] = {"mean_pos": mp, "mean_neg": mn, "separation": s, "accuracy_at_0.5": a}
        print(f"  {name:<26}{mp:>10.4f}{mn:>10.4f}{s:>12.4f}{a:>14.4f}")

    print()
    verdict = ("noul MEASURES THE STATE (sets separate; keep the protocol's wire format)"
               if res["noul (as specified)"]["separation"] > 0.3 and res["noul (as specified)"]["accuracy_at_0.5"] >= 0.9
               else "noul DOES NOT cleanly separate the sets -> the card's warning is live for our items; "
                    "use the documented workaround and disclose the deviation from the 3.1 wire format")
    print(f"  VERDICT: {verdict}")

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "question_under_test": OK_INSTRUCTIONS,
        "revision": getattr(agent, "revision", args.revision),
        "methods": res, "verdict": verdict, "rows": rows,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"\n  record -> {out} ({out.stat().st_size} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
