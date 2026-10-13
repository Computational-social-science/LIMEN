# The planted-truth control: what the harness can and cannot detect

**Date**: 2026-10-13
**Trigger**: the BootLoops `planted-truth` skill — *"a checker that has never fired is
untested"*, and *"a null result from an instrument never shown to detect a difference
is not evidence of absence"*.
**Harness**: `measurement/prop_a_planted_control.py` (same items, same matched-damage
calibration, same endpoints as `prop_a_injection.py`)
**Data**: `measurement/out/prop_a_planted.jsonl` (450 rows, 150 dev items x 3 arms)

---

## 1. Why this was run, and what it corrects

`docs/PROPOSITION_A_CONTROL_LAW.md` concluded that geometry-indexed and
structure-indexed noise are **not separable** in this instrument's loss, at any
endpoint. That conclusion came from an instrument that had **never been shown able
to detect a difference at matched damage rate**. My own document listed this as a
limit and then drew the conclusion anyway.

The plant closes that gap — or shows that it cannot be closed at this n.

## 2. The plant

The same harness, the same items, the same matched damaged-token rate, the same
endpoints. The only change is **where the damage falls**:

- **content** — damage only content words (the words carrying the intent)
- **function** — damage only function words (stopwords: *the, a, in, was, …*)

Both arms use the **same geometry-family edits**, so the mechanism is identical and
the family is not the variable. Only the linguistic locus differs. For an intent
classifier, content words are the signal, so content damage must cost more.

**Prediction, written before the run**: `accuracy(content) < accuracy(function)`.

**Mechanical verification before the run**: damage fell *only* on the intended token
class in both arms, at matched rate (9 vs 8 damaged tokens on a 29-token item;
verified by mapping every alignment edit back to its token index).

## 3. Result — the plant did not fire

Damage matching held exactly (0.2953 in both arms, difference 0.0000). Marginals:

| arm | accuracy | cov@0.8 | mean c |
|---|---|---|---|
| clean | 0.9067 | 0.7467 | 0.8471 |
| content | 0.9133 | 0.6067 | 0.7981 |
| function | 0.8733 | 0.6200 | 0.8080 |

Paired tests, content − function:

| endpoint | diff | 95% CI | verdict |
|---|---|---|---|
| accuracy | **+0.0400** | [−0.0133, +0.0933] | includes 0 |
| cov@0.8 | −0.0133 | [−0.1000, +0.0667] | includes 0 |
| mean_c | −0.0098 | [−0.0351, +0.0145] | includes 0 |

McNemar (accuracy): content-only-right 11, function-only-right 5, **p = 0.210**.

**The point estimate has the opposite sign to the prediction, and nothing is
significant.** The plant — a difference that *should* exist by construction — was
not detected.

## 4. What the design could have detected

The useful output of a failed positive control is its **detection bound**. At
n = 150, 80% power, α = 0.05 two-sided:

| comparison | endpoint | discordance | **MDE** |
|---|---|---|---|
| plant: content vs function | accuracy | 0.107 | **0.075** |
| family: geometry vs structure | accuracy | 0.060 – 0.200 | 0.056 – 0.102 |
| family: geometry vs structure | cov@0.8 | 0.220 – 0.293 | **0.107 – 0.124** |
| noise vs clean | cov@0.8 | 0.20 – 0.29 | 0.101 – 0.137 |

**So the honest statement of the family null is not "the families are
indistinguishable". It is:**

> No family difference larger than **~11 percentage points of coverage** (or
> ~6–10 points of accuracy) exists at this n. A difference of 5 points would not
> have been seen.

That is a weaker claim than the one in `PROPOSITION_A_CONTROL_LAW.md`, and it is
the one the data support.

## 5. A second correction, which matters more

The same calculation applied to **noise vs clean** — the finding I reported as
significant — shows:

| rate | endpoint | observed diff | MDE | verdict |
|---|---|---|---|---|
| 0.12 | cov@0.8 | −0.0600 | 0.1006 | **below MDE** |
| 0.30 | cov@0.8 | −0.1867 | 0.1181 | DETECTABLE |
| 0.50 | cov@0.8 | −0.2800 | 0.1372 | DETECTABLE |

The 0.30 and 0.50 coverage effects are real and large — they exceed the detection
bound by 1.6x and 2.0x, which is why they survived Holm correction. But the
**rate-0.12 result is below the detection bound**, so the claim in the earlier
document that "at the two lower damage levels there is no measurable loss at all"
is **not supported**: at 0.12 the design simply could not see an effect of that
size. The 0.30 result stands; the 0.12 result is underpowered, not null.

This does not change the headline (coverage is far more sensitive than accuracy)
but it does change what may be asserted about the low-damage end.

## 6. What this establishes, and what it forbids

**Established:**
- The matched-damage calibration is sound (damage matched to 0.0000; damage placed
  only on intended tokens, verified by alignment mapping).
- The endpoints are live and responsive: the noise-vs-clean coverage effect is
  ~2x its MDE at rate 0.50 and survives Holm.
- A **detection bound** now exists for every comparison made in this harness.

**Forbidden:**
- Reporting "the families are not separable" as an established negative. The
  correct form is "no family difference above ~11 points of coverage was
  detected at n = 150".
- Reporting the rate-0.12 coverage result as evidence of no effect.
- Reporting the plant as confirming the harness. It did the opposite: it showed
  the harness is underpowered for effects of the size the plant was expected to
  produce.

## 7. What to do next

**1. Power the family comparison before re-running it.** To detect an 11-point
coverage difference at 80% power the design needed ~n = 150; to detect a 5-point
one it needs roughly **n = 700** by the same formula. If the family question is to
be settled rather than bounded, that is the sample size.

**2. Give the plant a known effect size, not just a known sign.** The plant as run
predicted a *direction*, so a null could not be interpreted. A better plant injects a
**calibrated** difference — e.g. damage content words at rate 0.30 versus 0.15 — so
the expected gap is computable and recovery can be demanded to that accuracy, which
is what the skill asks for ("recovery to worse accuracy than the claim tests a
weaker claim").

**3. Keep the MDE with every future null.** This is the transferable rule: a null
without a detection bound is not a result.

## 8. The skill's own rule, applied to itself

`planted-truth` §5 says: *"Prove each control can fail... A control's first
demonstrated failure is its birth certificate; before that it is a hope."* The
plant here is itself a control, and it **fired** — in the sense that it failed to
detect what it was built to detect. That is a successful control run: it produced
the information that the harness is underpowered, which is exactly what a plant is
for. The control that would still be a hope is any claim that the harness *can*
detect a matched-damage family difference; that claim remains unproven.
