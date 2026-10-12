# Proposition A, model side: the two human error processes are NOT separable in model loss

**Date**: 2026-10-13
**Instrument**: `convaiinnovations/laya` @ `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`, CUDA (RTX 4070)
**Harness**: `measurement/prop_a_injection.py` (reuses `Router`, `item_bank.jsonl`, `typo_noise.py`)
**Data**: `measurement/out/prop_a_injection.jsonl`, `prop_a_rate0.3.jsonl`, `prop_a_rate0.5.jsonl`
**Items**: 150 from the bank's **dev** split; the confirmatory split was not touched
**Design**: paired -- every item appears in all three arms; 450 model calls per level

---

## 1. What was asked

`docs/PARADIGM_TYPING_AS_REGULATED_PROCESS.md` establishes from 300,000 corpus
sentences that human residual error is **two processes with different governing
variables**: a geometry-indexed class (adjacent-key substitution) whose rate is
flat across word length (0.98x from length 2 to 12), and a structure-indexed
class (deletion, insertion) whose rate scales with it (2.5x, 4.9x).

The programme's generator `N_en` implements the **geometry** process and gives it
60% of the weight, while the structure process -- 61.3% of measured residual
error -- has no representation.

The Shannon note's Proposition A asks whether physical and cognitive noise are
separable. This measures the **model half**: inject each family at a **matched
token-damage rate** and compare loss. The note's own prediction is explicit:

> If matched-π physical and cognitive schedules produce the same loss, the notes'
> "damaged-token count dominates edit type" claim is confirmed on this slice, and
> a fourth SSL component indexed by edit type is unnecessary.

## 2. What was done

Two families, matched on the quantity that matters -- the number of clean tokens
no longer intact in the noisy text -- not on edit count:

- **geometry**: adjacent-key substitution and transposition (N_en's own classes)
- **structure**: deletion and insertion, **including at whitespace**, so token
  boundaries can merge or split (the mechanism the corpus measurement implicates)

Matching is enforced per item by calibrating the edit count to the target damage
(§5 records two bugs found in that calibration). Achieved damage:

| target rate | geometry | structure | difference |
|---|---|---|---|
| 0.12 | 0.1126 | 0.1090 | -0.0036 |
| 0.30 | 0.2945 | 0.2909 | -0.0036 |
| 0.50 | 0.4889 | 0.4862 | -0.0027 |

Damage is matched to within 0.4 percentage points at every level.

## 3. Result

Paired accuracies (n = 150 items, identical items across arms), with exact
McNemar tests:

| target rate | clean | geometry | structure | structure − geometry | p |
|---|---|---|---|---|---|
| 0.12 | 0.8667 | 0.8867 | 0.8800 | −0.0067 | **1.000** |
| 0.30 | 0.8667 | 0.8533 | 0.8600 | +0.0067 | **1.000** |
| 0.50 | 0.8667 | 0.7800 | 0.8467 | +0.0667 | **0.099** |

**The two families are indistinguishable in model loss at every damage level
tested.** At the highest level the structure family is *less* damaging than
geometry (84.7% vs 78.0%), the opposite of the prediction, and even that
difference does not reach significance (p = 0.099, 10 vs 20 discordant pairs).

## 4. What this means

**The note's prediction is confirmed on this slice.** Loss tracks the
damaged-token count, not the edit family. The consequence for the programme is
concrete and it is a *relief*, not a problem:

> `N_en`'s mis-weighting is **not** a first-order error for this instrument.
> Because the model responds to damage *rate* rather than to edit *structure*,
> the generator's 60/40 split between geometry and structure does not by itself
> bias a Phase I loss estimate -- provided the damage **rate** is right.

That relocates the defect rather than removing it. §4.1 of the paradigm document
showed λ is ambiguous by ~5.6x between produced and surviving errors, and **that**
is the quantity this instrument is sensitive to. The class-composition error
matters for *ecological validity* -- the generator does not model what human
typing error actually looks like -- but it does not, on this evidence, propagate
into a loss difference.

**A second finding, which was not predicted and is worth stating.** At the two
lower damage levels there is **no measurable loss at all**: 86.7% clean vs 88.7%
and 88.0% at ~11% damage, and 85.3% / 86.0% at ~29% damage. All paired tests are
p = 1.000. Accuracy is *higher* under 11% noise, which is noise around zero, not
a real improvement. The model absorbs roughly a third of its tokens being damaged
before accuracy moves. This is the note's "models absorb a large amount of QWERTY
corruption before accuracy falls sharply" -- and it holds for the **structure**
family too, which the note did not claim.

## 5. Two bugs found in the matched-damage control, recorded because the control is the experiment

Both were caught by dry-running the injector without the model, and both would
have produced a confident wrong answer.

1. **A positional damage metric is an alignment artefact.** The first version
   compared tokens positionally. Inserting one space splits a token and shifts
   every later token by one, so 2 edits reported **14 damaged tokens** on a
   14-token sentence. The count was measuring misalignment, not damage. Replaced
   with a boundary-aware test: a clean token counts as intact if it still occurs
   in the noisy text bounded by non-letters on both sides. This is stable under
   insertion and deletion, which is precisely what the structure family does.
2. **A binary search over edit counts does not work here.** The damage curve is
   monotone but not linear (structure: 3 edits -> 3 tokens, 4 edits -> 9, because
   one deletion can merge two tokens and change both surfaces). Binary search
   returned damage 1 when the target was 4. Replaced with an upward scan that
   stops at the first count reaching the target.

Neither bug would have been visible in the final accuracy table. Both would have
inflated or erased the family difference.

## 6. What this does NOT establish

- **One instrument, one language, one task.** 150 English intent-classification
  items on a 421M model, accuracy as the endpoint. A larger model, a generative
  task, or a longer context may respond differently, and the note's Proposition B
  is about a damage ladder *within* a prompt, which this design does not test.
- **Power is adequate for the effect the note cares about, not for small ones.**
  With 150 items and ~6% discordance on the key comparison, the paired SE is
  ~0.020, so a 5-point effect would be detected. A 1-2 point effect would not.
- **This is accuracy, not the programme's actual endpoint.** Phase I's estimand is
  `SilentError@τ` and `Coverage@ε` -- the control law -- not plain accuracy. A
  family difference could exist in the confidence gate while being invisible in
  accuracy. **This is the obvious next measurement and it is not done here.**
- **The confound in §3 of the corpus analysis is not addressed**: word length
  correlates with word frequency, so "structure scales with length" may partly be
  "structure scales with lexical difficulty".

## 7. The one-line answer to Proposition A

> On this instrument, at matched damaged-token rate, geometry-indexed and
> structure-indexed noise are **not separable in accuracy** -- loss tracks the
> damage rate, exactly as the Shannon note predicted. But the human data say the
> two are separable in *production*, so a generator that models only the geometry
> process is ecologically wrong while being, for this endpoint, metrically
> harmless. Whether it is harmless for the **confidence gate** is untested.
