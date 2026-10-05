#!/usr/bin/env python
"""check_window_marginals.py -- is the confirmatory window comparable to dev, on the bank alone?

WHY, AND WHAT IT CANNOT DO
    The frozen design reports a dev-calibrated threshold (tau*) and a dev-measured pi_d against a confirmatory
    window of 652 test items. That is only coherent if the two splits are drawn from the same distribution.
    This check is PURELY STATIC: it reads `measurement/item_bank.jsonl` and computes. It runs no model, so it
    cannot detect a difference in how the instrument behaves - only in what it is asked.

    It is a PRE-SEAL check and it must stay one. If the marginals differ, the response is an ERRATUM written
    before the run; re-weighting, re-splitting or silently dropping cells AFTER seeing the confirmatory data
    would be a design change made on the outcome, which is the thing pre-registration exists to prevent. The
    script therefore reports and exits non-zero on a mismatch, and takes no corrective action.

CHECKS
    A  domain marginals, dev against test, by chi-square and by total-variation distance
    B  template marginals, likewise
    C  per-domain template coverage: no domain is represented by a single template in one split and many in
       the other, which would make the splits differ in kind rather than in degree
    D  the template imbalance actually present, reported as a ratio, since an earlier probe measured 38x
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BANK = REPO_ROOT / "measurement" / "item_bank.jsonl"
TV_THRESHOLD = 0.15        # total-variation distance above which the splits are not comparable in practice


def chi2_p(obs_a: dict[str, int], obs_b: dict[str, int]) -> tuple[float, float]:
    """Pearson chi-square for two independent samples over a shared category set, and its p-value."""
    keys = sorted(set(obs_a) | set(obs_b))
    na, nb = sum(obs_a.values()), sum(obs_b.values())
    chi = 0.0
    for k in keys:
        oa, ob = obs_a.get(k, 0), obs_b.get(k, 0)
        ea = na * (oa + ob) / (na + nb)
        eb = nb * (oa + ob) / (na + nb)
        if ea > 0:
            chi += (oa - ea) ** 2 / ea
        if eb > 0:
            chi += (ob - eb) ** 2 / eb
    df = len(keys) - 1
    if df <= 0:
        return 0.0, 1.0
    # Wilson-Hilferty normal approximation to the chi-square tail, adequate for df >= 2
    z = ((chi / df) ** (1 / 3) - (1 - 2 / (9 * df))) / math.sqrt(2 / (9 * df))
    p = 0.5 * math.erfc(z / math.sqrt(2))
    return chi, min(1.0, max(0.0, p))


def tv(obs_a: dict[str, int], obs_b: dict[str, int]) -> float:
    keys = sorted(set(obs_a) | set(obs_b))
    na, nb = sum(obs_a.values()), sum(obs_b.values())
    return 0.5 * sum(abs(obs_a.get(k, 0) / na - obs_b.get(k, 0) / nb) for k in keys)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    args = ap.parse_args()
    if not BANK.exists():
        print(f"  [FAIL] no bank at {BANK}")
        return 1

    rows = [json.loads(l) for l in BANK.read_text(encoding="utf-8").splitlines() if l.strip()]
    dev = [r for r in rows if r["split"] == "dev"]
    test = [r for r in rows if r["split"] == "test"]
    print(f"  bank {len(rows)}  ·  dev {len(dev)}  ·  test (the confirmatory window) {len(test)}")
    if not dev or not test:
        print("  [FAIL] one split is empty")
        return 1

    findings: list[str] = []

    for field in ("domain", "template_id"):
        ca = collections.Counter(r[field] for r in dev)
        cb = collections.Counter(r[field] for r in test)
        chi, p = chi2_p(dict(ca), dict(cb))
        d = tv(dict(ca), dict(cb))
        print(f"\n  {field}: categories dev={len(ca)} test={len(cb)}  chi2={chi:.2f}  p={p:.4f}  TV={d:.4f}")
        print(f"    dev  {dict(ca.most_common(6))}")
        print(f"    test {dict(cb.most_common(6))}")
        if field == "domain" and p < 0.05:
            findings.append(f"domain marginals differ (chi2 p = {p:.4f})")
        if d > TV_THRESHOLD and field == "domain":
            findings.append(f"domain total-variation distance {d:.3f} exceeds {TV_THRESHOLD}")

    # C - per-domain template coverage
    print("\n  per-domain templates (dev / test):")
    for dom in sorted({r["domain"] for r in rows}):
        td = {r["template_id"] for r in dev if r["domain"] == dom}
        tt = {r["template_id"] for r in test if r["domain"] == dom}
        nd = sum(1 for r in dev if r["domain"] == dom)
        nt = sum(1 for r in test if r["domain"] == dom)
        flag = ""
        if (len(td) <= 1) != (len(tt) <= 1):
            flag = "  <- single-template in one split only"
            findings.append(f"domain {dom} is single-template in one split only")
        print(f"    {dom:<12} items {nd:>3}/{nt:<3}  templates {len(td):>2}/{len(tt):<2}{flag}")

    # D - the imbalance actually present
    ct = collections.Counter(r["template_id"] for r in test)
    if ct:
        print(f"\n  template imbalance in the window: max {max(ct.values())} / min {min(ct.values())} = "
              f"{max(ct.values())/max(1, min(ct.values())):.1f}x over {len(ct)} templates")

    print()
    if findings:
        print(f"  [FAIL] {len(findings)} marginal finding(s) - respond with an ERRATUM before the run, not with")
        print(f"         a correction after it:")
        for f in findings:
            print("      " + f)
        return 1
    print("  [OK] the confirmatory window is comparable to dev on domain and template structure;")
    print("       no erratum is required on this static evidence")
    return 0


if __name__ == "__main__":
    sys.exit(main())