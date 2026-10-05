#!/usr/bin/env python
"""phase1_power.py -- Phase I power, recomputed on the values that were MEASURED rather than assumed.

WHY THIS IS NOT BOOKKEEPING
    The frozen N was derived from a pilot estimate of the paired discordance and an assumed effect. The dev
    pre-run has now measured both on the pinned instrument, and they are not the assumed values: pi_d came
    back 0.2036 against a frozen 0.1833, and the accuracy contrast came back at 11.8 points. Power computed
    on the wrong inputs is not a conservative number, it is an unexamined one - and an over-powered
    pre-registration is a real defect too, because it spends subjects and GPU time to detect effects far
    smaller than the one the design cares about.

WHAT IT COMPUTES
    McNemar is a binomial test on the DISCORDANT pairs, so power does not depend on N directly - it depends
    on the expected number of discordant pairs, `N * pi_d`, and on the conditional split among them,
    `pi = c / (b + c)`, where c counts the pairs that move in the hypothesised direction.
    From that:

      * achieved power at the frozen N, at the Holm-adjusted alpha for a three-test family
      * the minimum detectable pi at 80% power (the smallest asymmetry this design can see)
      * the N that would be needed for 80% power at the measured asymmetry

WHAT IT DOES NOT DO
    It does not propose changing N. A pre-registration that meets its own power requirement is met; this
    reports the margin so that a reader knows whether the study is comfortably or barely powered, and so
    that a future amendment would have a number to argue against instead of a hunch.
"""

from __future__ import annotations

import argparse
import math
import pathlib
import sys

ALPHA = 0.05
FAMILY = 3          # H1.1, H1.2, H1.3 under Holm; the first test runs at alpha / FAMILY
POWER_TARGET = 0.80

# MEASURED on the pinned instrument, dev split, 280 items, lambda 0.0 vs 0.18 (docs/PHASE_I_DEV_PRERUN_RESULTS.md)
MEASURED_PI_D = 0.2036
MEASURED_B = 12     # wrong -> right  (against the accuracy hypothesis)
MEASURED_C = 45     # right -> wrong  (with the accuracy hypothesis)
FROZEN_N = 652
FROZEN_PI_D = 0.1833


def binom_tail_ge(n: int, k: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p), computed in log space so it is stable for n in the thousands."""
    total = 0.0
    for i in range(k, n + 1):
        lg = (math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
              + i * math.log(p) + (n - i) * math.log1p(-p))
        total += math.exp(lg)
    return min(1.0, total)


def critical_k(n: int, alpha: float) -> int:
    """Smallest k with P(X >= k | Binomial(n, 0.5)) <= alpha. This is the two-sided McNemar critical value."""
    for k in range(n + 1):
        if binom_tail_ge(n, k, 0.5) <= alpha:
            return k
    return n + 1


def power(n_disc: int, pi: float, alpha: float) -> float:
    if n_disc <= 0:
        return 0.0
    k = critical_k(n_disc, alpha)
    return binom_tail_ge(n_disc, k, pi)


def mde_pi(n_disc: int, alpha: float, target: float = POWER_TARGET) -> float:
    """Smallest pi whose power reaches `target` at this many discordant pairs."""
    lo, hi = 0.5, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if power(n_disc, mid, alpha) >= target:
            hi = mid
        else:
            lo = mid
    return hi


def n_for_power(pi: float, alpha: float, target: float = POWER_TARGET, cap: int = 200000) -> int | None:
    for n in range(1, cap):
        if power(n, pi, alpha) >= target:
            return n
    return None


TARGET_EFFECT_POINTS = 5.0     # the minimum effect the protocol pre-registered, in absolute points


def points_from_pi(pi: float, n_items: int, pi_d: float) -> float:
    """Translate a conditional asymmetry into an ACCURACY difference in absolute percentage points.

    pi is the share of discordant pairs moving in the hypothesised direction, so (2*pi - 1) is the net
    directional excess, and multiplying by the expected discordant pairs N*pi_d and dividing by N gives the
    net accuracy change. Without this translation a reader cannot tell whether the design is over-powered or
    correctly powered for the effect it pre-registered - and the first draft of this script said
    "OVER-powered" on the strength of a pi it never converted.
    """
    return (2 * pi - 1) * pi_d * 100.0


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--n", type=int, default=FROZEN_N)
    ap.add_argument("--pi-d", type=float, default=MEASURED_PI_D)
    args = ap.parse_args()

    alpha_holm = ALPHA / FAMILY
    pi_meas = MEASURED_C / (MEASURED_B + MEASURED_C)
    n_disc = args.n * args.pi_d

    print("  INPUTS")
    print(f"    N                  = {args.n}   (frozen; Amendment 1)")
    print(f"    pi_d               = {args.pi_d:.4f}   (measured 0.2036 / frozen 0.1833)")
    print(f"    measured split     = {MEASURED_C} with the hypothesis vs {MEASURED_B} against")
    print(f"    pi (conditional)   = {pi_meas:.4f}")
    print(f"    expected discordant pairs = N * pi_d = {n_disc:.1f}")
    print(f"    Holm-adjusted alpha      = {ALPHA}/{FAMILY} = {alpha_holm:.4f}")
    print()

    nd = int(round(n_disc))
    pw = power(nd, pi_meas, alpha_holm)
    md = mde_pi(nd, alpha_holm)
    n80 = n_for_power(pi_meas, alpha_holm)
    print("  ACHIEVED")
    print(f"    power at N = {args.n}, at the measured asymmetry : {pw:.4f}"
          f"   {'(>= 0.80: the requirement is met)' if pw >= POWER_TARGET else '(BELOW the 0.80 requirement)'}")
    md_pts = points_from_pi(md, args.n, args.pi_d)
    meas_pts = points_from_pi(pi_meas, args.n, args.pi_d)
    print(f"    minimum detectable pi at 80% power               : {md:.4f}"
          f"   (the measured {pi_meas:.4f} is {'above' if pi_meas > md else 'at or below'} it)")
    print(f"    -> in accuracy points: MDE {md_pts:.2f} pts, measured effect {meas_pts:.1f} pts,"
          f" pre-registered target {TARGET_EFFECT_POINTS:.1f} pts")
    if n80:
        print(f"    N needed for 80% power at the measured asymmetry : {n80} discordant pairs"
              f"  ->  N = {math.ceil(n80 / args.pi_d)} items")
        ratio = args.n / (n80 / args.pi_d) if n80 else float("nan")
        print(f"    frozen N / needed N                              : {ratio:.2f}x")
    print()
    if pw >= POWER_TARGET and abs(md_pts - TARGET_EFFECT_POINTS) <= 1.0:
        print(f"  READING: the frozen N is CORRECTLY SIZED, not over-sized. Its minimum detectable effect is")
        print(f"           {md_pts:.2f} points at 80% power, against the {TARGET_EFFECT_POINTS:.1f} points this")
        print(f"           design pre-registered as the effect it cares about - a match to within a point. The")
        print(f"           measured effect is {meas_pts:.1f} points, i.e. roughly twice the target, which is")
        print(f"           why achieved power reads ~1.0. The N was chosen for the target, and the pre-run says")
        print(f"           the target was the conservative choice rather than the optimistic one.")
    elif pw >= POWER_TARGET and md_pts < TARGET_EFFECT_POINTS - 1.0:
        print(f"  READING: the frozen N is OVER-powered for its own target: its minimum detectable effect is")
        print(f"           {md_pts:.2f} points against a pre-registered target of {TARGET_EFFECT_POINTS:.1f}.")
        print(f"           Not a violation ('at least 80%'), but the design would detect effects smaller than")
        print(f"           the one it is about, and that is the honest description of what 652 items buy.")
    elif pw >= POWER_TARGET:
        print("  READING: the frozen N meets the 80% requirement with a margin that is real but not lavish.")
    else:
        print("  READING: the frozen N does NOT meet the 80% requirement at the measured asymmetry. This is a")
        print("           finding about the design and belongs in an amendment; it must NOT be met by quietly")
        print("           raising N after seeing dev data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())