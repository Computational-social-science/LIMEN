# The lambda ambiguity: 6.66x between the two things lambda could name

**Date**: 2026-10-13
**Basis**: 300,000 transcribed sentences, 10,094,604 target characters (20,000 participant
files, seed 20261012)
**Sources**: `figures/data/trans_aware.json`, `decisive.json`, `error_structure2.json`
**Script**: `wb-diag/lambda_ambiguity.py`

---

## 1. Why this matters more than the class weights

`docs/PROPOSITION_A_CONTROL_LAW.md` established two things:

1. geometry-indexed and structure-indexed noise are **not separable** in this
   instrument's loss, at any endpoint measured; and
2. noise **does** move the control law — 28 points of coverage at p_Holm = 0.002,
   against 8.7 points of accuracy at p_Holm = 0.146.

Together those say the generator's **class composition** is metrically harmless
(though ecologically wrong), while the **damage rate** is exactly the quantity the
instrument is sensitive to. So if lambda names the wrong rate, a Phase I number
moves. This document measures how far apart the candidates are.

## 2. The two candidates, measured

| quantity | count | per target character |
|---|---|---|
| target characters | 10,094,604 | — |
| **surviving** errors (visible in the final text) | 138,634 | **1.373 %** |
| repairs (backspaces, from the keystroke log) | 784,417 | 7.771 % |
| **produced** errors (surviving + repairs) | 923,051 | **9.144 %** |

**Ratio produced / surviving = 6.66x.**

## 3. Which one is the published number?

The paper's uncorrected error rate (1.167 %) is a **surviving** rate — it is
computed by aligning the presented and transcribed strings, so anything the typist
repaired is absent by construction. Our surviving rate is 1.373 %, a ratio of
1.18 to the published figure, which is the expected agreement given a different
sample and the transposition-aware classifier.

Our **produced** rate is 9.144 %, which is **7.8x** the published number.

## 4. Which one does the frozen ladder name?

Amendment 3 v3 froze `lambda_lo = 0.05` and `lambda_mid = 0.18`, described in the
protocol (§4.2) as "target mean edits per token or per character" with
"~5–8 % character corruption" for lo and "~12–18 %" for mid.

| | vs surviving (1.373 %) | vs produced (9.144 %) |
|---|---|---|
| `lambda_lo = 0.05` | 3.6x | **0.5x** |
| `lambda_mid = 0.18` | 13.1x | **2.0x** |

**The ladder brackets the produced rate and sits an order of magnitude above the
surviving rate.** Its intent is therefore consistent with modelling *produced*
input noise — which is the scientifically right target, since the programme is
about noise a human introduces into a model's input, not noise that survives to be
read.

## 5. The defect, stated precisely

The protocol text says lambda is "edits per token **or** per character", and the
paper figure the channel is validated against is a *surviving* rate. So the same
symbol lambda, in the same protocol, can be read three ways:

- edits per character, on the **clean** text — what the generator implements;
- a rate comparable to the paper's 1.167 % — which is **surviving**, 6.66x smaller;
- edits per **token** rather than per character — a further factor of roughly the
  mean token length, ~5.

**A lambda calibrated on the published number would be ~6.7x too small**; a lambda
read as per-token would be ~5x too large. Either error moves the coverage endpoint
substantially, and §4.2 of the protocol currently admits both readings.

## 6. The recommendation, and its scope

**Fix lambda's definition in the pre-registration as: mean edits per clean-text
character, applied to the input, and state the measured human reference rate
beside it.** Concretely, the amendment should say:

> lambda is the mean number of edits the generator applies per character of the
> clean input text. It names **produced** noise, not surviving noise. The
> reference human rate on the 136M Keystrokes corpus is **9.14 %** produced
> (1.37 % surviving; the ratio is 6.66x), so `lambda_lo = 0.05` is 0.5x the human
> produced rate and `lambda_mid = 0.18` is 2.0x it.

This is a **wording** change to a frozen artefact, so it needs an amendment filed
before the seal, and it must not be presented as a change of estimand: the ladder
values do not move. What moves is that lambda's referent becomes checkable.

## 7. What this does NOT establish

- **Backspaces are a proxy for repairs, not a count of errors.** A backspace can
  delete a correctly typed character after a change of mind, and one error can
  take several backspaces. The produced rate is therefore an **upper bound** on
  the error production rate, and the 6.66x ratio is correspondingly an upper
  bound. The direction is not in doubt; the magnitude is approximate.
- **The surviving rate is transposition-aware but the produced count is not.**
  Repairs are counted as keystrokes, which needs no alignment; surviving errors
  are counted by the validated detector. The two counts are not perfectly
  symmetric.
- **No claim about tokens.** The mean token length in this corpus is not measured
  here, so the per-token reading's factor of ~5 is an illustration, not a
  measurement.
- **This is one corpus, English, 15 fixed sentences.** The ratio could differ for
  other channels — which is precisely why Phase II cannot inherit lambda by
  "same edit rate as English" (protocol §5.2).
