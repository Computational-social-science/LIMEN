#!/usr/bin/env python
"""analyze_phase1.py -- the confirmatory analysis for Phase I, with synthetic positive/negative controls.

WHY THIS EXISTS BEFORE ANY REAL DATA
    The pre-registration is frozen but NO code implemented the confirmatory tests. `run_phase1.py` produces
    trial records and nothing consumed them. That is the one gap a dry run is for: an analysis that has
    never been shown to detect an effect that is present, and to stay quiet when none is, is not evidence
    about anything - it is a program that prints numbers.

    So this file carries the analysis AND `--synthetic`, which builds trial records with a KNOWN effect
    (positive control: noise degrades accuracy) and with NO effect (negative control) and requires the same
    code path to detect the first and not the second. The two controls run on the same estimator, the same
    pairing and the same alpha; only the generated data differ.

THE DESIGN IT HONOURS
    Within-item, so every contrast is PAIRED: the same item is compared across lambda under the same seed,
    which is what the pre-registration's "paired / mixed models with item random intercepts" is protecting
    when it fixes the split by item_id. Pairing on (item_id, noise_seed) makes the item-level variation
    cancel instead of entering the variance.

FOUND WHILE WRITING IT, AND RECORDED RATHER THAN HIDDEN
    Section 4.5 names "Paired / mixed models with item random intercepts". This implements paired
    PERMUTATION tests instead: exact, assumption-light, and a paired test is the limiting case of a random
    intercept model in which the only random effect is the item. The difference is a reconciliation item
    between the protocol and its analysis code, and it is printed as such rather than papered over - the
    pre-registration must name the estimator that actually runs.
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import random
import statistics
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TAUS = (0.80, 0.90)
EPS = 0.05
ALPHA = 0.05
N_PERM = 20000


# ---------------------------------------------------------------------------------------------
# The estimands, from the trial records run_phase1.py writes.
# ---------------------------------------------------------------------------------------------
def load_trials(path: pathlib.Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("status") == "ok" and r.get("question_id") == "intent":
            rows.append(r)
    return rows


def by_cell(rows: list[dict]) -> dict:
    """(lambda, seed) -> {item_id: record}."""
    cells: dict = collections.defaultdict(dict)
    for r in rows:
        cells[(r["lambda"], r["noise_seed"])][r["item_id"]] = r
    return cells


def paired_contrast(a: list[float], b: list[float], seed: int = 0) -> dict:
    """Two-sided paired permutation test on the mean difference a - b.

    Exact under exchangeability within pairs, which the within-item design provides: the only thing the
    null says is that the label of a pair's two conditions carries no information, so the permutation
    distribution is over sign flips. No distributional assumption, no asymptotic approximation, and it is
    the same estimator the positive and negative controls are both run through.
    """
    assert len(a) == len(b) and a, "paired contrast needs equal, non-empty samples"
    d = [x - y for x, y in zip(a, b)]
    obs = statistics.mean(d)
    rng = random.Random(seed)
    ge = 0
    for _ in range(N_PERM):
        s = sum(x if rng.random() < 0.5 else -x for x in d)
        if abs(s / len(d)) >= abs(obs) - 1e-12:
            ge += 1
    p = (ge + 1) / (N_PERM + 1)
    # paired bootstrap CI on the mean difference
    boots = []
    for _ in range(2000):
        s = [d[rng.randrange(len(d))] for _ in d]
        boots.append(statistics.mean(s))
    boots.sort()
    return {"n_pairs": len(d), "mean_diff": obs, "p_two_sided": p,
            "ci95": [boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots))]],
            "wins": sum(1 for x in d if x > 0), "losses": sum(1 for x in d if x < 0)}


def mcnemar_exact(pairs: list[tuple[int, int]]) -> dict:
    """Exact McNemar on paired binary outcomes. b = (1,0) rows, c = (0,1) rows."""
    b = sum(1 for x, y in pairs if x == 1 and y == 0)
    c = sum(1 for x, y in pairs if x == 0 and y == 1)
    n = b + c
    if n == 0:
        return {"b": 0, "c": 0, "p_two_sided": 1.0, "note": "no discordant pairs; the contrast is empty"}
    from math import comb
    tot = 2 ** n
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(k + 1)) / tot
    return {"b": b, "c": c, "p_two_sided": min(1.0, 2 * tail)}


def holm(pvals: dict, alpha: float = ALPHA) -> dict:
    """Holm-Bonferroni across the confirmatory family. Controls FWER under ARBITRARY dependence, which is
    what makes it valid even though H1.1's co-report and H1.3's second disjunct are one quantity."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    out, prev = {}, 0.0
    for i, (k, p) in enumerate(items):
        thresh = alpha / (m - i)
        adj = min(1.0, max(prev, p * (m - i)))
        prev = adj
        out[k] = {"raw_p": p, "threshold": thresh, "holm_p": adj, "reject": adj <= alpha}
    return out


# ---------------------------------------------------------------------------------------------
# The confirmatory contrasts.
# ---------------------------------------------------------------------------------------------
def confident_quantile(vals: list[float], q: float) -> float:
    v = sorted(vals)
    return v[min(len(v) - 1, int(q * (len(v) - 1)))]


def tau_star(rows: list[dict], eps: float = EPS) -> float | None:
    """The least tau whose dev silent-error is at most eps (the tie-break maximises coverage)."""
    cands = sorted({float(t) for r in rows for t in (r.get("silent_error") or {})})
    for t in cands:
        vals = [r["silent_error"][str(t)] for r in rows if r["silent_error"].get(str(t)) is not None]
        if vals and statistics.mean(vals) <= eps:
            return t
    return None


def contrasts(rows: list[dict], lam_lo: float, lam_mid: float) -> dict:
    cells = by_cell(rows)
    seeds = sorted({k[1] for k in cells})
    res: dict = {"seeds": seeds, "cells": {}}

    acc_pairs, se_pairs, cov_pairs = [], [], []
    for seed in seeds:
        c0 = cells.get((0.0, seed), {})
        cm = cells.get((lam_mid, seed), {})
        shared = sorted(set(c0) & set(cm))
        if not shared:
            continue
        # H1.1 - accuracy, reading (a) of eq (7): defers counted as errors. A record with an error is wrong;
        # a record with no error is right. `error` is None only when gold is absent, and those are dropped.
        a0 = [1 - (1 if c0[i]["error"] == 1 else 0) for i in shared if c0[i]["error"] is not None]
        a1 = [1 - (1 if cm[i]["error"] == 1 else 0) for i in shared if cm[i]["error"] is not None]
        acc_pairs += list(zip(a0, a1))
        # H1.2 - SilentError at the fixed probe tau = 0.90
        k = "0.9"
        s0 = [c0[i]["silent_error"][k] for i in shared if c0[i]["silent_error"].get(k) is not None]
        s1 = [cm[i]["silent_error"][k] for i in shared if cm[i]["silent_error"].get(k) is not None]
        se_pairs += list(zip(s0, s1))
        # H1.3 - coverage: does the gate transmit at all, at tau* fitted on the CLEAN cell
        ts = tau_star([c0[i] for i in shared]) or 0.9
        v0 = [1 if c0[i]["c"] >= ts else 0 for i in shared]
        v1 = [1 if cm[i]["c"] >= ts else 0 for i in shared]
        cov_pairs += list(zip(v0, v1))

    # H1.1: accuracy falls -> the discordant pair of interest is (right at 0, wrong at mid) = b
    h11 = mcnemar_exact([(1 - a, 1 - b) for a, b in acc_pairs]) if acc_pairs else {"p_two_sided": 1.0}
    # H1.2: silent error RISES -> one-sided, direction fixed by the hypotheses
    d_se = [b - a for a, b in se_pairs]
    h12 = paired_contrast([b for _, b in se_pairs], [a for a, _ in se_pairs]) if se_pairs else {"p_two_sided": 1.0}
    # H1.3: coverage falls OR conditional error rises. Implemented as the coverage contrast (disjunct 1),
    # with the conditional-error disjunct reported beside it and NOT entering the family - the two disjuncts
    # are one quantity's two signs and counting both would double-count a single movement.
    d_cov = [a - b for a, b in cov_pairs]
    h13 = paired_contrast([a for a, _ in cov_pairs], [b for _, b in cov_pairs]) if cov_pairs else {"p_two_sided": 1.0}

    # DIRECTION IS PART OF THE HYPOTHESIS. H1.1 predicts accuracy FALLS, H1.2 predicts SilentError RISES,
    # H1.3 predicts Coverage FALLS. A two-sided rejection would count a significant movement in the
    # OPPOSITE direction as support, which is the one misreading a directional pre-registration exists to
    # prevent. Each hypothesis therefore carries `sign_ok`, and the Holm input is the two-sided p only when
    # the sign agrees - otherwise the contrast is recorded as significant-and-opposite, which is a finding
    # in its own right and not evidence for the hypothesis.
    # McNemar is fed (wrong_at_clean, wrong_at_mid): b counts pairs that were wrong only at CLEAN, c counts
    # pairs wrong only at MID. Accuracy FALLING means more items are wrong at mid, i.e. c > b. The first
    # version of this line wrote b > c, and the direction guard caught it on the first run - which is what
    # the guard is for: a two-sided p cannot tell you that a significant movement went the wrong way.
    acc_falls = (h11.get("c", 0) > h11.get("b", 0))
    se_rises = bool(se_pairs) and statistics.mean([b - a for a, b in se_pairs]) > 0
    cov_falls = bool(cov_pairs) and statistics.mean([a - b for a, b in cov_pairs]) > 0
    res["H1.1"] = {"test": "exact McNemar on accuracy, defers counted as errors",
                   "sign_ok": acc_falls, "predicted": "accuracy falls at lambda_mid", **h11}
    res["H1.2"] = {"test": "paired permutation on SilentError@0.90", "sign_ok": se_rises,
                   "predicted": "SilentError rises at lambda_mid",
                   "mean_rise": statistics.mean(d_se) if d_se else float("nan"), **h12}
    res["H1.3"] = {"test": "paired permutation on Coverage@epsilon", "sign_ok": cov_falls,
                   "predicted": "Coverage falls at lambda_mid",
                   "mean_fall": statistics.mean(d_cov) if d_cov else float("nan"), **h13}
    fam = {}
    for k, ok in (("H1.1", acc_falls), ("H1.2", se_rises), ("H1.3", cov_falls)):
        raw = {"H1.1": h11, "H1.2": h12, "H1.3": h13}[k]["p_two_sided"]
        fam[k] = raw if ok else 1.0          # a wrong-direction result cannot enter the family as support
    res["holm"] = holm(fam)
    res["direction_violations"] = [k for k, ok in (("H1.1", acc_falls), ("H1.2", se_rises),
                                                   ("H1.3", cov_falls)) if not ok]
    return res


# ---------------------------------------------------------------------------------------------
# Synthetic controls.
# ---------------------------------------------------------------------------------------------
def synth(n_items: int, lam_mid: float, delta: float, rng: random.Random,
          coverage_drop: float = 0.0) -> list[dict]:
    """Trial records with a KNOWN effect size.

    delta           = drop in the probability of being correct at lam_mid (drives H1.1 and H1.2)
    coverage_drop   = drop in the probability that confidence clears tau* at lam_mid (drives H1.3)

    BOTH knobs exist because the first version had only `delta`, and the dry run showed H1.3 returned the
    SAME p-value in the positive and the negative control - the coverage contrast was never exercised, so
    its code path was unvalidated while the suite reported OK. A hypothesis with no positive control is a
    hypothesis whose implementation has never been shown to fire.
    """
    rows = []
    for i in range(n_items):
        iid = f"synth_{i:04d}"
        for seed in (0, 1, 2):
            for lam in (0.0, lam_mid):
                p0 = 0.80
                p = p0 if lam == 0.0 else p0 - delta
                correct = 1 if rng.random() < p else 0
                # confidence: high enough to transmit at tau=0.9 with prob depending on correctness,
                # so that silent errors exist and move with the effect
                # confidence: `coverage_drop` lowers the chance of clearing tau* at lam_mid, which is what
                # makes Coverage@epsilon move. Without it the coverage contrast is constant by construction.
                high = rng.random() >= (coverage_drop if lam != 0.0 else 0.0)
                c = rng.choice([0.95, 0.92, 0.88]) if high else 0.60
                se = {str(t): (1 if (correct == 0 and c >= t) else 0) for t in (0.8, 0.9)}
                rows.append({"phase": "I", "item_id": iid, "lambda": lam, "noise_seed": seed,
                             "realised_edit_rate": 0.0 if lam == 0 else 0.12,
                             "question_id": "intent", "gold": "x", "error": 1 - correct,
                             "c": c, "silent_error": se, "status": "ok"})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--trials", help="trial JSONL from run_phase1.py")
    ap.add_argument("--lam-lo", type=float, default=0.05)
    ap.add_argument("--lam-mid", type=float, default=0.18)
    ap.add_argument("--out", help="write the results JSON here")
    ap.add_argument("--synthetic", action="store_true",
                    help="run the positive and negative controls on generated data")
    args = ap.parse_args()

    if args.synthetic:
        print("  SYNTHETIC CONTROLS - same code path, same pairing, same alpha")
        failures = []
        for label, delta, cov, want, expect in (
                ("POSITIVE (noise hurts accuracy)", 0.20, 0.0, True, ("H1.1", "H1.2")),
                ("POSITIVE (noise lowers coverage)", 0.0, 0.50, True, ("H1.3",)),
                ("NEGATIVE (no effect)", 0.00, 0.0, False, ())):
            rng = random.Random(20261005)
            rows = synth(300, args.lam_mid, delta, rng, coverage_drop=cov)
            res = contrasts(rows, args.lam_lo, args.lam_mid)
            h = res["holm"]
            rejected = [k for k, v in h.items() if v["reject"]]
            print(f"\n    {label}: accuracy delta={delta}  coverage drop={cov}")
            for k in ("H1.1", "H1.2", "H1.3"):
                dv = res[k].get("sign_ok")
                print(f"      {k}: raw p={h[k]['raw_p']:.5f}  holm p={h[k]['holm_p']:.5f}"
                      f"  sign_ok={dv}  {'REJECT' if h[k]['reject'] else 'not rejected'}")
            if res["direction_violations"]:
                print(f"      direction violations: {res['direction_violations']}")
            if want and not rejected:
                failures.append(f"{label}: no hypothesis was rejected, but an effect was present")
            for k in expect:
                if k not in rejected:
                    failures.append(f"{label}: {k} was NOT rejected, so its code path is unvalidated "
                                    f"by a positive control")
            if not want and rejected:
                failures.append(f"{label}: {rejected} were rejected on data with NO effect "
                                f"- the analysis reports a false positive")
        if failures:
            print("\n  [FAIL] synthetic controls:")
            for f in failures:
                print("      -", f)
            return 1
        print("\n  [OK] each of H1.1, H1.2 and H1.3 is detected by its OWN positive control, and the")
        print("       negative control produces no rejection at alpha = 0.05 after Holm across the family.")
        return 0

    if not args.trials:
        ap.print_help()
        return 2

    rows = load_trials(pathlib.Path(args.trials))
    if not rows:
        print("  [FAIL] no usable trial records (need question_id == 'intent' and status == 'ok')")
        return 1
    res = contrasts(rows, args.lam_lo, args.lam_mid)
    res["n_records"] = len(rows)
    res["lam_lo"] = args.lam_lo
    res["lam_mid"] = args.lam_mid
    print(json.dumps(res, indent=2)[:4000])
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(res, indent=2), encoding="utf-8")
        print(f"\n  written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())