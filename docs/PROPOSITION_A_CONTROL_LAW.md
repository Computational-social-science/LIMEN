> **CORRECTED 2026-10-13 by a planted-truth control. Two claims below do not
> survive it** (`docs/PLANTED_TRUTH_CONTROL.md`).
>
> 1. "Not separable" is stated too strongly. A plant that damaged content
>    words versus function words at matched damage -- a difference that must
>    exist -- was **not detected** at n = 150. So the harness is underpowered
>    for effects of that size, and the correct claim is a **bound**: no family
>    difference above ~11 points of coverage (or ~6-10 points of accuracy)
>    exists at this n. A 5-point difference would not have been seen.
> 2. "At the two lower damage levels there is no measurable loss at all" is
>    **wrong for rate 0.12**. Its coverage effect (-0.060) is BELOW the
>    detection bound (0.101), so it is underpowered, not null. The 0.30 and
>    0.50 effects stand: they exceed their MDEs by 1.6x and 2.0x.
>
> The headline -- coverage is far more sensitive than accuracy -- is
> unaffected, and is strengthened: the coverage effect at rate 0.50 is ~2x
> its detection bound while the accuracy effect is below its own.

# Proposition A at the control-law endpoint: accuracy is the wrong instrument

**Date**: 2026-10-13
**Instrument**: `convaiinnovations/laya` @ `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`, CUDA (RTX 4070)
**Harness**: `measurement/prop_a_injection.py` (reuses `Router`, `item_bank.jsonl`)
**Data**: `measurement/out/propa_endpoint_{0.12,0.3,0.5}.jsonl`
**Design**: 150 dev-split items x 3 arms, fully paired (450 model calls per level)
**Analysis**: `wb-diag/propa_endpoint_analysis.py`, `auc_analysis.py`, `holm.py`

---

## 1. Why this replaced the first attempt

An earlier version of this experiment (`docs/PROPOSITION_A_MODEL_SIDE.md`) scored
**accuracy** and concluded the two families were indistinguishable. That
conclusion was correct about accuracy and **wrong about the programme**, because
accuracy is not the estimand. The protocol's endpoints are the control law:

- `SilentError@tau` -- wrong **and** confident
- `Coverage@eps` -- share answered while holding accepted-item error at <= eps
- `AUC(tau)` -- the gate's discriminability, H1.2'

Measuring those changes the answer. **Accuracy is blind to an effect that the
control law shows clearly.**

## 2. Result

### 2.1 The family difference does not survive correction

21 comparisons of `structure - geometry` across three damage levels and seven
endpoints. Not one survives Holm at FWER 0.05:

| rate | metric | diff | p_raw | p_Holm |
|---|---|---|---|---|
| 0.50 | silent@0.8 | -0.0467 | 0.0360 | 0.756 |
| 0.50 | mean_c | +0.0217 | 0.0874 | 1.000 |
| 0.30 | cov@0.8 | +0.0800 | 0.0982 | 1.000 |
| 0.50 | accuracy | +0.0667 | 0.1029 | 1.000 |
| 0.50 | auc | +0.1182 | 0.1040 | 1.000 |

The single nominal p < 0.05 (silent@0.8 at rate 0.50) is exactly what one expects
from 21 tests and it **points the other way** -- structure produces *less* silent
error than geometry. Reporting it alone would have been the multiple-comparisons
error the protocol's own Holm family exists to prevent.

**Proposition A stands as answered: geometry-indexed and structure-indexed noise
are not separable in this instrument's loss, at any endpoint measured.**

### 2.2 But noise DOES move the control law, while leaving accuracy flat

This is the finding, and it was invisible in the accuracy-only version. Comparing
`geometry` against `clean`, Holm-corrected:

| rate | metric | diff | p_raw | p_Holm | decision |
|---|---|---|---|---|---|
| 0.30 | cov@0.8 | **-0.1867** | 0.0001 | **0.0019** | REJECT H0 |
| 0.30 | mean_c | **-0.0610** | 0.0001 | **0.0019** | REJECT H0 |
| 0.50 | cov@0.8 | **-0.2800** | 0.0001 | **0.0019** | REJECT H0 |
| 0.50 | mean_c | **-0.1090** | 0.0001 | **0.0019** | REJECT H0 |
| 0.50 | accuracy | -0.0867 | 0.0132 | 0.146 | n.s. |
| 0.12 | mean_c | -0.0172 | 0.0191 | 0.191 | n.s. |

Read the two rows that matter together. At rate 0.50 the noise costs **28
percentage points of coverage** (0.727 -> 0.447) at p_Holm = 0.0019, while the
same noise costs only 8.7 points of accuracy at p_Holm = 0.146. **The control law
detects an effect that accuracy cannot resolve.**

Mechanically: the model's mean confidence falls (0.848 -> 0.739), so at a fixed
threshold tau = 0.8 it defers more items. Accuracy among what it still answers is
almost unchanged. The model has not lost the ability to classify; it has lost the
**confidence to act** -- and that is precisely what a coverage estimand is for.

### 2.3 H1.2' is non-monotonic, and only visible at the top of the ladder

`AUC(noisy) - AUC(clean)`, paired item bootstrap:

| rate | geometry | structure |
|---|---|---|
| 0.12 | -0.068 [-0.194, +0.062] | -0.026 [-0.158, +0.103] |
| 0.30 | -0.015 [-0.195, +0.170] | -0.062 [-0.203, +0.086] |
| 0.50 | +0.060 [-0.078, +0.216] | **+0.178 [+0.044, +0.321]** |

H1.2' predicts `AUC(lambda_mid) > AUC(0)` -- discriminability **rises** with noise.
At 0.12 and 0.30 it does not (both point estimates are negative). At 0.50 the
structure arm rises significantly. **The direction is damage-level dependent**,
which matters for the protocol because lambda_mid was fixed at 0.18 -- a level
where this instrument shows no rise.

## 3. What this means for the programme

1. **The choice of endpoint is load-bearing, not presentational.** The same
   experiment yields "no effect" on accuracy and a highly significant effect on
   coverage. A programme that reported accuracy would have concluded that input
   noise does not matter.
2. **`N_en`'s class mis-weighting is confirmed harmless for this instrument** --
   at every endpoint, not just accuracy. The ecological objection stands (the
   generator does not model what human error looks like), but it does not bias a
   loss estimate here.
3. **lambda's definition is what matters.** Since families are interchangeable at
   matched damage and damage rate drives coverage, the produced-vs-surviving
   ambiguity of ~5.6x is the defect that can actually move a Phase I number.
4. **The `defer` action is doing real work.** Coverage falls because the gate
   defers, and SilentError stays near its floor. The gate is behaving as the
   protocol's good-regulator reading predicts.

## 4. Limits, stated

- **One instrument, one language, one task**: 150 English intent items, a 421M
  model, `choice` with two options. A larger model or a generative endpoint may
  differ.
- **Exploratory, not confirmatory.** The dev split was used; the confirmatory
  split was not touched. These p-values are not pre-registered and Holm here
  corrects an exploratory family, which is stricter than required but weaker than
  a confirmatory test.
- **n = 150.** A 5-point accuracy effect is detectable; a 1-2 point one is not.
  The coverage effect is large enough to survive at this n.
- **The AUC interval is wide** ([0.74, 0.93] for the one that excludes zero), so
  the 0.50 result should be read as "the rise is detectable at high damage", not
  as a precise magnitude.
- **`mean_c` is not an endpoint** in the protocol; it is reported because it
  explains the coverage drop mechanically.
- **Three bugs were found in the harness while building this**, each of which
  would have produced a confident wrong answer: a positional damage metric that
  reported misalignment as damage (2 edits -> 14 damaged tokens); a binary search
  over a non-linear damage curve; and reading `result["probabilities"]` when the
  response nests them at `answers["intent"]["probabilities"]` -- which returned
  None and made SilentError and Coverage **exactly 0.0**, a ceiling artefact that
  looks like a clean null. All three are recorded in the commit messages.

## 5. One-line answer

> At matched damaged-token rate, geometry-indexed and structure-indexed noise are
> **not separable** in this instrument at any endpoint -- but **accuracy is the
> wrong instrument to have asked with**: the same noise costs 28 points of
> coverage at p = 0.002 while costing 8.7 points of accuracy at p = 0.146.
