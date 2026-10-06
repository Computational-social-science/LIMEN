# Phase I confirmatory results

**Run:** 2026-10-05 · pinned `convaiinnovations/laya` @ `55cf4c4ebb4e…`, cuda, frozen θ
**Data:** the **test** split, 652 items × 7 λ × 3 seeds = **13,692 trial records**, 0 failures, 366.5 s
**Analysis:** exact paired permutation (`scripts/analyze_phase1.py`), Holm at FWER α = 0.05 over the frozen
three-hypothesis family, **direction enforced as part of each hypothesis**.

## The family

| hypothesis | direction | raw p | Holm threshold | verdict |
|---|---|---|---|---|
| **H1.1** accuracy falls at λ_mid | falls | **4.42 × 10⁻³⁶** | 0.0167 | **REJECTED** — supported |
| **H1.2′** the gate's discriminability rises at λ_mid | rises | **2.00 × 10⁻⁴** | 0.0500 | **REJECTED** — supported |
| **H1.3** coverage falls at λ_mid | falls | **5.00 × 10⁻⁵** | 0.0250 | **REJECTED** — supported |

**No direction violations. Every hypothesis moved the way it was pre-registered to move.**

Discordant pairs for H1.1: **b = 71**, **c = 307** (b = wrong only when clean, c = wrong only under noise) —
more than four items newly wrong for every one newly right.

H1.2′: within-arm AUC **0.6014 → 0.7601**, contrast **+0.1587** over **1,956** exchangeable units.

H1.3: mean coverage fall **0.2904**, 95 % CI [0.2679, 0.3154].

**The original H1.2 is co-reported and nothing more.** `SilentError@0.9` moves **−0.0266**, i.e. it FALLS, in
the opposite direction to the pre-registered hypothesis. That is the finding that forced the v1.19
replacement, and it reproduces on the confirmatory data exactly as the dev pre-run predicted.

## The result in one sentence

**Typo noise at λ = 0.18 costs 11.8 accuracy points and 29 coverage points, and every one of the three
pre-registered hypotheses was confirmed — including the replacement hypothesis that the confidence gate
becomes MORE discriminative under noise rather than less.** The errors noise causes arrive below the gate:
93.6 % of them are rejected, up from 71.4 % clean. The "silent error" premise does not hold — **the errors are
loud, and the gate can hear them.**

## Pre-run predictions, and whether they held

| predicted before the confirmatory run | confirmatory result |
|---|---|
| π_d ≈ 0.2036 | 0.19 (b+c = 378 over 1,956 units) |
| minimum detectable effect 5.41 points | accuracy contrast ≈ 12 points |
| λ_lo = 0.05 does not degrade | as measured on dev |
| H1.2′ rises, AUC contrast ≈ +0.12 | **+0.1587** |
| original fixed-τ H1.2 falls | **−0.0266** |
| confidence contamination absent | **0 of 13,692 rows carry the substituted constant** |

## Provenance

Every number above comes from `measurement/out/confirm_results.json`, written by
`scripts/analyze_phase1.py` on `measurement/out/confirm_trials.jsonl`. `measurement/out/` is gitignored, so
the record is this document plus the scripts that produced it — both pinned by the anchor guard.
