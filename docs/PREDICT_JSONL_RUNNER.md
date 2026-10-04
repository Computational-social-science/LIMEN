# The `predict -> JSONL` runner — built, exercised, verified

**File:** `measurement/run_phase1.py` · **Record of the exercising run:** `measurement/trials_smoke.jsonl`
(30 rows, 18,277 B) · **Instrument:** the pinned revision `55cf4c4e…` (`config/pin_laya.json`)

This is the mechanical link between the pinned instrument and the protocol's §3.5 trial record. It is
kept separate from analysis **on purpose**: the record must exist before anything reads it.

## What the exercising run proved

5 bank items × 2 λ × 1 seed × 3 questions = **30 planned rows, 30 written, 0 failures, 0.6 s on CUDA**
(≈ 50 rows/s). At the frozen confirmatory size — 652 items × 3 λ × 3 seeds × 3 questions = **17,604
rows** — that is on the order of **6 minutes** of instrument time. The GPU is not the constraint; the
item bank is.

Seven checks were run against the written record, not against the script's intentions:

| Check | Result |
|---|---|
| Every §3.5 field present in every row | ✓ none missing |
| `phase` = `I`, `script` = `en_latin` throughout | ✓ |
| **`error` defined only where gold exists** | ✓ `intent` carries 0/1; **`ok` and `escalate` are `null`** |
| `silent_error[τ]` = 1 **iff** `error == 1 and c ≥ τ` | ✓ 0 violations |
| `action[τ]` = `answer` iff `c ≥ τ`, else `defer` | ✓ 0 violations |
| λ = 0 ⇒ zero ops, realised rate 0.0000 | ✓ |
| λ = 0.05 ⇒ 93 ops over 15 rows, realised rate 0.0620 | ✓ non-empty |
| `state_hash` distinct per condition | ✓ |
| λ = 0 reproduces the pilot's clean direction (5/5 correct, c ∈ [0.86, 0.99]) | ✓ |

**The `null` in row 3 is the point of the row.** Writing `error = 0` for `ok` and `escalate` would have
claimed those answers were *correct* when the bank carries no gold for them and therefore cannot say.
A silent zero there is the kind of default that survives into an analysis unnoticed.

## A protocol detail the run exposed: λ is a TARGET, not an ACHIEVED rate

The generator's contract states that `lam` is the **target mean number of edits per character**; the
realised rate is a draw from that mean, so a single condition's achieved corruption **differs from its
label**.

**Measured over the full 120-item replay** (`measurement/trials_pilot_replay.jsonl`, 1080 rows):

| λ label | n | mean realised | median | min | max | SD | bias |
|---|---|---|---|---|---|---|---|
| 0.00 | 120 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | — |
| 0.05 | 120 | **0.0502** | 0.0473 | 0.0000 | 0.1310 | **0.0258** | **+0.4 %** |
| 0.12 | 120 | **0.1148** | 0.1142 | 0.0339 | 0.2278 | **0.0355** | **−4.4 %** |

> **Correction to an earlier figure in this document.** A 30-row sample first suggested a **24 %
> overshoot** at λ = 0.05. That was a **small-sample artefact**: the generator's mean is well calibrated
> (+0.4 % and −4.4 % at the two levels). **The real feature is the SPREAD, not a bias** — at λ = 0.05 the
> realised rate ranges from **0.0000** (an item that received no edit at all) to **0.1310**, with
> SD ≈ 0.026. The correction is recorded rather than quietly overwritten, because the original claim was
> drafted from 15 rows and would have been cited.

**Consequence, stated now rather than discovered later.** At λ = 0.05 an item can receive **zero** edits,
so some "noisy" trials are **byte-identical to their clean counterpart** (guaranteed at λ = 0, where the
rate is exactly 0 and the op list is empty). An analysis that treats `λ` as the achieved corruption will
attribute *realised-rate* variation to the *rate factor*, which inflates apparent noise effects. Two
defensible handlings, to be fixed in the amendment before the confirmatory run:

1. **Report the realised-rate distribution per λ** alongside every λ effect (the table above is the
   template), so a reader can see how much spread sat under each label; and
2. **Use `realised_edit_rate` as a covariate** in the model, with `λ` retained as the assigned factor —
   and, because of the zero-edit tail, consider reporting the **share of trials with zero ops** per λ as
   a separate quantity, since those trials are controls by accident.

Either is acceptable; **choosing after seeing the confirmatory results is not.** The runner records
`realised_edit_rate` and the full `typo_ops` list on every row precisely so this choice remains open and
cheap.

## Honest limits

- The exercising run is **5 items, one seed, two λ** — it proves the *pipeline*, not any protocol
  result. No hypothesis is tested here and no accuracy figure from it may be quoted as a finding.
- Gold for these items is **agent-assigned with no human pass** (Amendment 1 §A4). The runner faithfully
  carries whatever gold it is given; it cannot improve the labels.
- `ok` and `escalate` have **no gold in this bank**, so no error metric for them can be computed from
  this run. If the confirmatory bank keeps that property, those questions contribute to the *gate*
  analysis only, and that must be said in the Stage 1 rather than left implicit.
