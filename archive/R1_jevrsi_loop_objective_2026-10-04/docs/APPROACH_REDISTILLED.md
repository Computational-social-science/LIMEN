# The approach, re-distilled

Written 2026-10-03 after the observation that one arm costing 17.43 h is itself evidence that the
approach is wrong. That observation is correct, and this file says precisely what is wrong with it
and what replaces it.

## What 17.43 h is evidence of

One arm is not one measurement. The source's gate is defined on a **3-seed mean**, because its
per-seed sd is 0.0173 — of which 0.0137 is training-seed variance, larger than the evaluation's own
sampling error at n=2,000. So:

| | at 17.43 h a training |
|---|---|
| one arm (3 seeds) | 52.3 h |
| a four-arm curve | 8.7 days continuous |
| the source's search (204 arms) | 1.2 years |

**The approach cannot produce its own deliverable.** That is a design failure, not a performance
detail. A search loop needs hundreds of runs; this hardware affords one to three. The instrument was
chosen for a machine we do not have.

## The larger error, which the cost only made visible

**We changed the backbone before checking that the pipeline reproduces a known answer.**

The source published `typed_decisions` 0.6525 for its v1.0 at 2B and 0.6175 at 0.8B, with the
checkpoints. Those are free calibration targets. We never used them. Everything downstream rested on
an instrument that had never been asked a question whose answer was already known — so a defect
anywhere in the encode, the readout, the metric or the harness would have shown up as
"the 0.6B scores 0.5775" and would have looked like a result.

This is the cheapest possible error to have avoided, and it was avoided the wrong way round.

## What stays, because it is already sound

- **The metric is computed correctly.** Pooled top-1 reproduces from the records themselves:
  arm 0 = (0.5600·600 + 0.6367·600 + 0.5463·800)/2000 = 0.5775; zero-shot = 0.4025.
- **The spec is faithful.** `check_arm0_spec.py`: 83/83 against the published `meta.json`, one
  recorded deviation.
- **The tower trained.** Measured against the base weights: every layer moved, mean |Δw| between
  5.8e-05 and 9.7e-05, consistent with lr_base 5e-6 over 1,500 cosine steps. No frozen parameters.
- **Arm 0's only defect is its time.** `health.py validate` has been reporting exactly that:
  `train_seconds 62741 outside [600, 21600]`.

## What replaces it

### The instrument: one decisive comparison, not a search

A search explores; a comparison decides. The hardware affords the second, so the project should ask
questions only the second can answer — questions answerable by one to three runs against a
pre-specified prediction.

### The data: the source's published record, read as data

Its released scale map is a measurement, not background reading. It already carries most of the
answer this project was going to spend GPU time rediscovering:

| line | params | v1.0 | best | loop gain |
|---|---|---|---|---|
| Qwen3.5-0.8B | 0.80 | 0.6175 | 0.6791 | +0.0616 |
| Qwen3.5-2B | 2.00 | 0.6525 | 0.7925 | +0.1400 |

Fitted as a power law, the loop's gain is `A · N^0.90` — **very nearly linear in parameter count**
over this range. The law's upper edge is given by the source's own failure (a 4B tower on the v2.0
recipe "failed to train at all"), and its lower edge has **never been measured**, because the source
only went down to 0.8B.

### The three steps, only the last of which is an experiment

| step | what | cost | what it settles |
|---|---|---|---|
| **1. Calibrate** | evaluate the source's own released 0.8B checkpoint with our harness; it publishes 0.6175 | 3.5 GiB download + ~40 min | whether our numbers mean what we think. A match makes everything comparable; a mismatch finds the defect for 40 minutes instead of another 17 hours |
| **2. Fit and bound** | the power law above, from the source's released numbers, with the domain edge from its 4B failure | 0 | the law, and where it is known to fail |
| **3. Test** | one arm at 0.6B — **outside the fitted range**, so it is an extrapolation and not a confirmation | 1 arm = 3 seeds | whether the law extends below 0.8B |

Step 3 is the only GPU spend, and it is the one thing the source's data cannot give us: nobody has
measured below 0.8B. Both outcomes are results — the law extends, or its lower edge is located
between 0.6B and 0.8B.

### And the supporting evidence already in hand

Four of the five pre-registered predictions resolved at **zero GPU cost**, from measurements this
project had already made for other reasons plus the source's released record:

- **P1 CONFIRMED** — 0.4025 zero-shot and 0.5775 trained, both below the source's 2B v1.0.
- **P4 CONFIRMED** — the bf16 scorer defect does not reproduce; our normaliser casts to fp32 before
  the multiply, relative error 5.8e-03, argmax unchanged.
- **P5 NOT SUPPORTED** — the order gap *closed* (3.10 pp → −0.75 pp) instead of opening. A prediction
  resolved against itself is a result, and it stays in the record.
- **P3 supported at 0.8B** by the source's record: its 0.8B keeper "is a different recipe".

That ratio — four verdicts for zero GPU time, one experiment for 17.43 h — is the finding about
method, and it is the reason the plan above puts calibration first and experimentation last.
