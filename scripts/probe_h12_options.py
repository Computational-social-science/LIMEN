#!/usr/bin/env python
"""probe_h12_options.py -- can options (c) and (d) carry H1.2, measured on data already on disk?

WHY
    Option (a) was recommended on a mechanism argument, then measured, then withdrawn. The two remaining
    options both require a NEW design choice - (c) needs an equivalence margin, (d) needs a coverage-matching
    rule - and the lesson from (a) is that such choices must be TESTED AGAINST DATA BEFORE they are adopted,
    not after. This script settles what the existing dev trials can already say about each.

    It runs NOTHING on the model. It reads `measurement/out/dev_trials_3seed.jsonl` (2,520 records, 280 dev
    items x lambda in {0, 0.05, 0.18} x seeds {0,1,2}) and computes.

WHAT IT ANSWERS
    (c) EQUIVALENCE. `CondErr@tau` is invariant to noise within a margin Delta. Two things have to hold for
        this to be a usable pre-registration: the observed difference must actually be inside a margin small
        enough to be worth asserting, and that margin must be achievable at the confirmatory sample size.
        Both are computed, on dev and projected onto the test-split window.
    (d) COVERAGE-MATCHED. Calibrate tau per arm so both arms admit the same fraction of trials, then ask
        whether the conditional error rises. This is fully computable from the dev trials, because every
        record carries its own confidence.

EXIT
  0  both probes computed      1  input missing
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
import statistics
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TRIALS = REPO_ROOT / "measurement" / "out" / "dev_trials_3seed.jsonl"
CONFIRMATORY_N = 652
Z_90 = 1.6448536269514722       # one-sided 5%, the two one-sided tests of a TOST at alpha = 0.05
RNG_SEED = 20261005


def load() -> list[dict]:
    rows = []
    for line in TRIALS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("status") == "ok" and r.get("question_id") == "intent":
            rows.append(r)
    return rows


def cond_err(rows: list[dict], tau: float) -> tuple[int, int]:
    adm = [r for r in rows if r["c"] >= tau]
    return sum(r["error"] for r in adm), len(adm)


def ratio_ci(e0: int, n0: int, e1: int, n1: int) -> tuple[float, float, float, float]:
    p0, p1 = e0 / n0, e1 / n1
    d = p1 - p0
    se = math.sqrt(p0 * (1 - p0) / n0 + p1 * (1 - p1) / n1)
    return d, se, d - Z_90 * se, d + Z_90 * se


def perm_test_unpaired(a: list[int], b: list[int], n_perm: int = 20000) -> float:
    """Two-sided permutation on a difference of means, because CondErr@tau is NOT a paired quantity."""
    obs = abs(statistics.mean(b) - statistics.mean(a))
    pool = a + b
    na = len(a)
    rnd = random.Random(RNG_SEED)
    hits = 0
    for _ in range(n_perm):
        rnd.shuffle(pool)
        if abs(statistics.mean(pool[na:]) - statistics.mean(pool[:na])) >= obs:
            hits += 1
    return (hits + 1) / (n_perm + 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    args = ap.parse_args()
    if not TRIALS.exists():
        print(f"  [FAIL] no trial file at {TRIALS}; nothing can be probed")
        return 1

    rows = load()
    arms = {lam: [r for r in rows if r["lambda"] == lam] for lam in (0.0, 0.05, 0.18)}
    print(f"  dev trials on disk: {len(rows)}   arms: "
          + ", ".join(f"lambda={k} n={len(v)}" for k, v in sorted(arms.items())))

    # ------------------------------------------------------------------ (c) equivalence
    print("\n  ============ (c) EQUIVALENCE on CondErr@tau ============")
    for tau in (0.80, 0.90):
        e0, n0 = cond_err(arms[0.0], tau)
        e1, n1 = cond_err(arms[0.18], tau)
        d, se, lo, hi = ratio_ci(e0, n0, e1, n1)
        margin_needed = max(abs(lo), abs(hi))
        print(f"    tau={tau}:  CondErr {e0}/{n0} = {e0/n0:.4f}  vs  {e1}/{n1} = {e1/n1:.4f}")
        print(f"              difference {d:+.4f}   90% CI [{lo:+.4f}, {hi:+.4f}]"
              f"   ->  smallest declarable margin on DEV = {margin_needed:.4f} ({margin_needed*100:.2f} pts)")
        # project onto the confirmatory window: same rates, n scaled by 652/280 per seed, 3 seeds
        scale = CONFIRMATORY_N / 280.0
        n0p, n1p = n0 * scale, n1 * scale
        sep = math.sqrt((e0/n0) * (1 - e0/n0) / n0p + (e1/n1) * (1 - e1/n1) / n1p)
        mp = Z_90 * sep
        print(f"              projected to the confirmatory window ({n0p:.0f} and {n1p:.0f} admitted):")
        print(f"              smallest declarable margin = {mp:.4f} ({mp*100:.2f} pts)"
              f"  ->  {'FEASIBLE' if mp <= 0.03 else 'a margin this wide is NOT meaningful'}"
              f" against a clean CondErr of {e0/n0:.4f}")

    # ------------------------------------------------------------------ (d) coverage-matched
    print("\n  ============ (d) COVERAGE-MATCHED on CondErr ============")
    print("    per-arm tau is set to the (1-q) quantile of c, so both arms admit the same share q")
    print(f"\n    {'q':>6}  {'tau_c':>7} {'tau_n':>7} | {'clean CondErr':>14} {'noisy CondErr':>14}"
          f" | {'diff':>8} {'p(perm)':>9}")
    verdict = []
    for q in (0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50):
        cs = sorted(r["c"] for r in arms[0.0])
        cn = sorted(r["c"] for r in arms[0.18])
        tau_c = cs[max(0, min(len(cs) - 1, int(round((1 - q) * len(cs))) - 1))]
        tau_n = cn[max(0, min(len(cn) - 1, int(round((1 - q) * len(cn))) - 1))]
        ac = [r["error"] for r in arms[0.0] if r["c"] >= tau_c]
        an = [r["error"] for r in arms[0.18] if r["c"] >= tau_n]
        if not ac or not an:
            continue
        pc, pn = statistics.mean(ac), statistics.mean(an)
        p = perm_test_unpaired(ac, an)
        d, se, lo, hi = ratio_ci(sum(ac), len(ac), sum(an), len(an))
        print(f"    {q:>6.2f}  {tau_c:>7.4f} {tau_n:>7.4f} | {pc:>14.4f} {pn:>14.4f}"
              f" | {pn-pc:>+8.4f} {p:>9.4f}   90% CI [{lo:+.4f},{hi:+.4f}]")
        verdict.append((q, pn - pc, p))

    ups = [v for v in verdict if v[1] > 0]
    sig = [v for v in verdict if v[2] < 0.05 and v[1] > 0]
    print(f"\n    of {len(verdict)} matched-coverage levels: {len(ups)} show NOISE ABOVE clean, "
          f"{len(sig)} of those significant at 0.05")
    if sig:
        best = max(sig, key=lambda v: v[1])
        print(f"    largest significant rise: q={best[0]:.2f}, difference {best[1]:+.4f}, p={best[2]:.4f}")
        print("    -> (d) CAN carry a directional hypothesis at this coverage level")
    else:
        print("    -> (d) does NOT carry a directional hypothesis: matching coverage does not make the")
        print("       conditional error rise significantly above clean at any level probed")

    print("\n  NOTE: every number here is dev, non-confirmatory, and computed without touching the model.")
    return 0


if __name__ == "__main__":
    sys.exit(main())