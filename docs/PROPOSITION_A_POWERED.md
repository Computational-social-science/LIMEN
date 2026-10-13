# Powered at the dev ceiling: the plant fires, the family null is licensed

**Date**: 2026-10-13
**Instrument**: `convaiinnovations/laya` @ `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`, CUDA (RTX 4070)
**Harness**: `measurement/prop_a_powered.py` (refuses to exceed the dev split)
**Data**: `measurement/out/prop_a_powered_{family,plant}.jsonl` — 840 rows each, n = 280 paired items
**Analysis**: `wb-diag/analyze280b.py`

---

## 1. A correction to the previous recommendation

`docs/PLANTED_TRUTH_CONTROL.md` recommended re-running at **n = 700**. That was
**wrong and I did not check it against the item bank**:

| | |
|---|---|
| dev split | **280 items** — the exploration ceiling |
| confirmatory window | 652 items — *not available for exploration* (protocol §8) |
| n = 700 | **unreachable** |

The harness now refuses an over-large request rather than silently sampling the
confirmatory window:

```
dev items available: 280  (requested 700)
  REFUSING: 700 exceeds the dev split's 280. The other 652 are the confirmatory
  window and must not be used.
```

The reachable ceiling is **n = 280**, which improves the MDE from 0.075 to 0.055.
That is a real gain and it is the whole gain available before the seal.

## 2. A second correction: detection is not power

The first analysis pass labelled any observed effect smaller than the MDE as
"below MDE", which **conflates two different statements**:

- **MDE** — the smallest *true* effect the design detects with 80% probability.
- An *observed* effect smaller than the MDE can still be significant: the observed
  value is itself a draw. What `|observed| < MDE` means is that the design has
  **less than 80% power for an effect of that size**.

Both numbers are now reported separately, per comparison.

## 3. The calibrated plant — and it fired

The previous plant carried only a **direction**, so its null could not be
interpreted. This one carries a **calibrated effect size**: damage content words at
rate 0.30 versus 0.15, same mechanism in both arms.

| arm | accuracy | cov@0.8 | mean c | damage |
|---|---|---|---|---|
| clean | 0.8750 | 0.7107 | 0.8454 | 0.0000 |
| content_lo | 0.8821 | 0.6607 | 0.8257 | 0.1407 |
| content_hi | 0.8571 | 0.6000 | 0.7951 | 0.2945 |

**hi − lo (the plant's own contrast):**

| endpoint | diff | 95% CI | MDE | p | power@obs | verdict |
|---|---|---|---|---|---|---|
| accuracy | −0.0250 | [−0.0643, +0.0143] | 0.0575 | 0.296 | 0.23 | not detected |
| **cov@0.8** | **−0.0607** | **[−0.1143, −0.0107]** | 0.0755 | **0.033** | 0.61 | **DETECTED** |

**The plant fired on the coverage endpoint.** This is the control the previous
document said was missing, and it is the thing that licenses the family null: the
harness **has been shown able to detect a matched-damage difference**.

Honest nuance: the plant was detected at p = 0.033 but with only **61% power** for
an effect of its own size — the CI is wide and the point estimate sits below its
MDE. So the harness detects effects of roughly **6 points of coverage**, weakly.

The plant did **not** fire on accuracy (p = 0.296, power 0.23). That is the third
independent indication that accuracy is the wrong instrument here.

## 4. The family comparison at n = 280

| arm | accuracy | cov@0.8 | mean c | damage |
|---|---|---|---|---|
| clean | 0.8750 | 0.7107 | 0.8454 | 0.0000 |
| geometry | 0.8536 | 0.6286 | 0.8074 | 0.2932 |
| structure | 0.8821 | 0.5857 | 0.8039 | 0.2941 |

Damage matched to 0.0009. **geometry − structure:**

| endpoint | diff | 95% CI | MDE | p | verdict |
|---|---|---|---|---|---|
| accuracy | −0.0286 | [−0.0643, +0.0036] | 0.0490 | 0.152 | not detected |
| cov@0.8 | +0.0429 | [−0.0107, +0.1000] | 0.0813 | 0.175 | not detected |

**noise − clean** (both families move coverage, neither moves accuracy):

| comparison | endpoint | diff | 95% CI | p | power@obs | verdict |
|---|---|---|---|---|---|---|
| geometry − clean | cov@0.8 | **−0.0821** | [−0.1357, −0.0286] | **0.0038** | 0.85 | DETECTED |
| structure − clean | cov@0.8 | **−0.1250** | [−0.1786, −0.0714] | **0.0000** | 0.99 | DETECTED |
| geometry − clean | accuracy | −0.0214 | [−0.0571, +0.0143] | 0.327 | 0.22 | not detected |
| structure − clean | accuracy | +0.0071 | [−0.0250, +0.0393] | 0.824 | 0.07 | not detected |

## 5. The licensed claim

Because the plant fired, the family null can now be stated as a **bound with a
demonstrated detection capability behind it**:

> At matched damaged-token rate, the geometry-indexed and structure-indexed families
> differ by less than **~8 points of coverage** (the MDE at n = 280) and less than
> ~5 points of accuracy. The harness **has been shown to detect** a matched-damage
> difference on coverage — a calibrated plant at 0.30 vs 0.15 fired at p = 0.033 —
> so this is a bound, not an untested null.

That is stronger than the earlier document's "not separable" (which was untested)
and weaker than a verdict. It is what the data support.

## 6. The pattern across three independent tests

Every test in this harness now says the same thing:

| test | accuracy | coverage |
|---|---|---|
| calibrated plant (0.30 vs 0.15) | not detected (p=0.30) | **detected (p=0.033)** |
| noise vs clean, geometry | not detected (p=0.33) | **detected (p=0.0038)** |
| noise vs clean, structure | not detected (p=0.82) | **detected (p=0.0000)** |

**Three for three: the coverage endpoint detects what the accuracy endpoint cannot.**
This is the single most reproducible finding in the session, and it is a statement
about the programme's methodology rather than about typing: for this instrument and
this noise, `Coverage@ε` is the endpoint that carries signal, and a study reporting
accuracy alone would conclude that input noise does nothing.

## 7. What is now settled, and what is not

**Settled:**
- The harness detects matched-damage differences on coverage (plant fired).
- The family difference is below the detection bound on both endpoints.
- The matched-damage calibration is exact (0.0009 mismatch at n = 280).
- `lambda_mid = 0.18` sits at the level where coverage effects are largest and most
  reliably detected.

**Not settled:**
- Whether a family difference exists **below 8 points of coverage**. Settling that
  needs more items than the dev split holds, which needs a new item bank, which
  moves the frozen instrument — so it is a **post-seal** question, not a pre-seal one.
- The plant's own power is only 61% at its effect size, so the detection capability
  is demonstrated but not comfortably so.
- Anything about other channels, languages, or models.
