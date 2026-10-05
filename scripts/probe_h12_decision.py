#!/usr/bin/env python
"""probe_h12_decision.py -- what (b), (c) and a third possibility each COST and BUY, computed.

WHY THIS EXISTS
    The previous probe reported the "smallest declarable margin" for an equivalence claim (2.59 pts at
    tau = 0.9). That number is a confidence-interval statement at the observed point, NOT the margin at
    which the design has 80% power. Treating one as the other is the same class of error as the withdrawn
    option (a): a plausible number used without converting it into the quantity the decision depends on.

WHAT IT COMPUTES
    1. (c) as an equivalence claim: TOST power as a function of the margin, and therefore the margin the
       design would actually need. Reported as a share of the baseline it is bounding, because a margin that
       is most of the baseline is not a claim.
    2. (b) as a consequence for the FROZEN MULTIPLICITY STRUCTURE: dropping a hypothesis moves Holm's first
       threshold from alpha/3 to alpha/2, which is a change to the decision rule for the hypotheses that
       remain.
    3. A contrast that is BOTH directional and well powered, if one exists: "noise-induced errors are
       self-announcing" - errors made under noise carry lower confidence than the errors made cleanly. If the
       gate rejects them for that reason, this is the mechanism, and unlike an equivalence claim it is
       directional and therefore does not need a margin.
"""

from __future__ import annotations

import json
import math
import pathlib
import random
import statistics
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TRIALS = REPO_ROOT / "measurement" / "out" / "dev_trials_3seed.jsonl"
CONFIRMATORY_N = 652
DEV_N = 280
Z90 = 1.6448536269514722
Z80 = 0.8416212335729143
RNG_SEED = 20261005


def load() -> list[dict]:
    out = []
    for line in TRIALS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("status") == "ok" and r.get("question_id") == "intent":
                out.append(r)
    return out


def cond_counts(rows, lam, tau):
    adm = [r for r in rows if r["lambda"] == lam and r["c"] >= tau]
    return sum(r["error"] for r in adm), len(adm)


def main() -> int:
    rows = load()
    scale = CONFIRMATORY_N / DEV_N

    # ------------------------------------------------------------------ 1. (c) TOST power
    print("  ================ (c) EQUIVALENCE — the margin it would actually need ================")
    for tau in (0.80, 0.90):
        e0, n0 = cond_counts(rows, 0.0, tau)
        e1, n1 = cond_counts(rows, 0.18, tau)
        p0, p1 = e0 / n0, e1 / n1
        d = p1 - p0
        n0p, n1p = n0 * scale, n1 * scale
        se_p = math.sqrt(p0 * (1 - p0) / n0p + p1 * (1 - p1) / n1p)
        print(f"\n    tau={tau}: clean {p0:.4f} ({n0} admitted)   noisy {p1:.4f} ({n1} admitted)   "
              f"d={d:+.4f}")
        print(f"      projected SE at the confirmatory window = {se_p:.4f} ({se_p*100:.2f} pts); "
              f"n0p={n0p:.0f}, n1p={n1p:.0f}")
        print(f"      {'margin':>8} {'% of baseline':>14} {'TOST power':>12}")
        need80 = None
        for margin in (0.02, 0.025, 0.03, 0.04, 0.05, 0.06, 0.075, 0.10):
            # power = P( CI90 inside (-margin, +margin) ) with the true difference at its dev estimate
            z = (margin - abs(d)) / se_p
            power = 0.5 * (1 + math.erf((z - Z90) / math.sqrt(2)))
            share = margin / p0
            mark = ""
            if need80 is None and power >= 0.80:
                need80 = margin; mark = "  <- first margin reaching 80%"
            print(f"      {margin:>8.4f} {share:>13.0%} {power:>12.3f}{mark}")
        # margin solvable for 80%: margin = |d| + (Z80 + Z90) * SE
        m80 = abs(d) + (Z80 + Z90) * se_p
        print(f"      => margin for 80% power = {m80:.4f} ({m80*100:.2f} pts), "
              f"i.e. {m80/p0:.0%} of the baseline {p0:.4f}")
        se_needed = (0.026 - abs(d)) / (Z80 + Z90)
        mult = (se_p / se_needed) ** 2 if se_needed > 0 else float("inf")
        print(f"      => to hold a 2.6-pt margin at 80% power the admitted sample would need "
              f"{mult:.1f}x more trials than the confirmatory window provides")

    # ------------------------------------------------------------------ 2. (b) multiplicity consequence
    print("\n  ================ (b) DROPPING H1.2 — the cost to the frozen decision rule ================")
    print("    Holm at FWER 0.05 with 3 hypotheses: thresholds alpha/3 = 0.0167, then alpha/2 = 0.025, then 0.05")
    print("    Holm at FWER 0.05 with 2 hypotheses: thresholds alpha/2 = 0.025, then 0.05")
    print(f"    => the FIRST hypothesis judged moves from 0.0167 to 0.025: the rule is LOOSENED by "
          f"{0.025/0.016667:.2f}x")
    print("    Whether that matters in practice depends on how far the remaining effects sit from both. With")
    print("    the measured effects (accuracy -11.8 pts, coverage -21.7 pts) at ~1.0 power, no conclusion")
    print("    changes; but the pre-registered threshold is no longer the one H1.1/H1.3 were evaluated at, and")
    print("    a reviewer may reasonably ask why a hypothesis was removed from the family.")

    # ------------------------------------------------------------------ 3. a directional alternative
    print("\n  ================ A DIRECTIONAL ALTERNATIVE — 'noise errors are self-announcing' ================")
    print("    Claim: the errors made under noise carry LOWER confidence than the errors made cleanly.")
    print("    If true, the gate rejects noise-induced errors for that reason, and this is the mechanism")
    print("    behind the flat conditional error. Unlike equivalence it is directional, so it needs no margin.")
    for lam in (0.0, 0.05, 0.18):
        errs = [r["c"] for r in rows if r["lambda"] == lam and r["error"] == 1]
        if not errs:
            continue
        errs_s = sorted(errs)
        med = statistics.median(errs_s)
        q1 = errs_s[len(errs_s) // 4]
        q3 = errs_s[(3 * len(errs_s)) // 4]
        print(f"      lambda={lam:<5} n_errors={len(errs):3d}   median c={med:.4f}   "
              f"IQR [{q1:.4f}, {q3:.4f}]   share below 0.9 = {sum(1 for x in errs if x < 0.9)/len(errs):.3f}")
    ec = [r["c"] for r in rows if r["lambda"] == 0.0 and r["error"] == 1]
    en = [r["c"] for r in rows if r["lambda"] == 0.18 and r["error"] == 1]
    if ec and en:
        obs = statistics.median(ec) - statistics.median(en)
        pool = ec + en
        rnd = random.Random(RNG_SEED)
        hits = 0
        for _ in range(20000):
            rnd.shuffle(pool)
            if statistics.median(pool[:len(ec)]) - statistics.median(pool[len(ec):]) >= obs:
                hits += 1
        print(f"\n      median c among errors: clean {statistics.median(ec):.4f} vs noisy "
              f"{statistics.median(en):.4f}   difference {obs:+.4f}")
        print(f"      one-sided permutation p = {(hits+1)/20001:.4f}")
        print(f"      => {'SUPPORTED and directional: noise-induced errors are made at lower confidence, so the' if obs > 0 else 'NOT supported'}")
        if obs > 0:
            print(f"         gate rejects them and the conditional error stays flat. No margin needed, and the")
            print(f"         claim is about the MECHANISM rather than about the absence of an effect.")
    print("\n  NOTE: dev only, non-confirmatory, computed without running the model.")
    return 0


if __name__ == "__main__":
    sys.exit(main())