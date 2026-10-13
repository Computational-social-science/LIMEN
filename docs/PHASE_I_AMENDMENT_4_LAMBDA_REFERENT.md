# Phase I — Amendment 4 (filed before the seal)

**Filed:** 2026-10-13 · **Governing:** `protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md` v1.1
· **Amends:** `docs/PHASE_I_PREREGISTRATION.md` §2, `protocol/...§4.2`, `docs/PHASE_I_AMENDMENT_3_O1_READABILITY.md`

**This amendment fixes the REFERENT of λ. It does not change any λ value, any
hypothesis, any endpoint, or any analysis.** The ladder frozen by Amendment 3 v3
(`lambda_lo = 0.05`, `lambda_mid = 0.18`) is untouched. What changes is that the
quantity λ names becomes checkable against a measured human rate instead of being
readable three ways.

---

## B5 — DECLARED. λ names PRODUCED noise, per clean-text character

### The defect

Protocol §4.2 defines the intensity as *"target mean edits per token **or** per
character"*, with `λ_lo` "e.g. ~5–8 % character corruption" and `λ_mid` "~12–18 %".
Three readings are simultaneously admissible:

1. mean edits per **character** of the clean input — what the generator actually
   implements (`Poisson(λ · len(text))` edits applied to the clean text);
2. a rate comparable to the **published** figure the channel is validated against —
   the paper's 1.167 %, which is a *surviving* rate;
3. edits per **token** rather than per character.

These are not the same number, and the protocol does not say which one λ is.

### The measurement that separates them

From 300,000 transcribed sentences of the 136M Keystrokes corpus
(10,094,604 target characters; `docs/LAMBDA_AMBIGUITY.md`):

| quantity | count | per target character |
|---|---|---|
| **surviving** errors (visible in the final text) | 138,634 | **1.373 %** |
| repairs (backspaces, from the keystroke log) | 784,417 | 7.771 % |
| **produced** errors (surviving + repairs) | 923,051 | **9.144 %** |

**Ratio produced / surviving = 6.66x.**

The published 1.167 % is a surviving rate — it is computed by aligning the
presented and transcribed strings, so anything the typist repaired is absent by
construction. Our surviving rate agrees with it to a ratio of 1.18.

### The decision

**λ is the mean number of edits the generator applies per character of the CLEAN
input text. It names PRODUCED noise, not surviving noise.**

### Why this choice and not another

- **It is what the generator already does.** `typo_noise(text, item_id, lam, seed)`
  draws `Poisson(λ · len(text))` edits and applies them to `text`. Reading (1) is
  the implementation; readings (2) and (3) are interpretations layered on top.
- **It is the scientifically correct target.** The programme studies noise a human
  introduces into a model's input. A typist's error is produced whether or not the
  typist repairs it; conditioning on survival would model the typist's *monitor*
  rather than the typist's *noise*.
- **The frozen ladder already brackets it.** `λ_lo = 0.05` is 0.5x the measured
  produced rate and `λ_mid = 0.18` is 2.0x it, whereas the same values are 3.6x and
  13.1x the surviving rate. The ladder's intent is consistent with produced noise,
  so this amendment records the intent rather than changing it.

### The measured reference, stated beside the ladder

> On the 136M Keystrokes corpus the human produced error rate is **9.14 %** per
> target character (1.37 % surviving; the ratio is 6.66x). Against that reference
> `λ_lo = 0.05` is **0.5x** the human produced rate and `λ_mid = 0.18` is **2.0x** it.

### What this rules out

- **λ may not be calibrated on the paper's 1.167 %.** Doing so would place λ a
  factor of **6.7 too small**, because that figure is a surviving rate.
- **λ may not be read per token.** §4.2's "or per token" is struck; a per-token
  reading would be larger than the per-character value by roughly the mean token
  length.
- **No λ value changes.** This is a referent fix, not a redesign.

### The consequence that makes this worth an amendment

An independent measurement (`docs/PROPOSITION_A_POWERED.md`) established that at
matched damaged-token rate the two noise families are **not separable in this
instrument's loss**, while the **damage rate itself** drives the control-law
endpoint strongly: at `λ = 0.50` the coverage effect is −0.280 at p < 0.0001, against
an accuracy effect of −0.087 at p = 0.15. The generator's class composition is
therefore metrically harmless here; **λ is the quantity that moves a number.** A λ
whose referent is ambiguous by 6.7x is therefore the defect that can actually bias a
Phase I estimate, which is why it is closed before the seal rather than after.

### Bounds on the measurement, stated because they bound the claim

- **Backspaces are a proxy for repairs, not a count of errors.** A backspace can
  remove a correctly typed character after a change of mind, and one error may take
  several backspaces. The produced rate is an **upper bound**, so 6.66x is an upper
  bound on the ratio. The direction is not in doubt; the magnitude is approximate.
- **The surviving count is transposition-aware; the repair count is not.** Repairs
  are keystrokes and need no alignment. The two are not perfectly symmetric.
- **The per-token factor is an illustration, not a measurement.** Mean token length
  in this corpus was not measured for this amendment.
- **One corpus, English, 15 fixed sentences.** The ratio may differ for other
  channels — which is precisely why §5.2 forbids equating λ across scripts by "same
  edit rate as English".

### Effect on the twelve §12 items

**None.** This amendment changes no value, no hypothesis, no endpoint, and no
analysis. It records what λ refers to, and it adds one measured reference rate
beside the ladder. `docs/PHASE_I_PREREGISTRATION.md` item 2 ("Typo classes and λ
rates fixed") moves from **PARTLY FIXED** to **FIXED** on the referent question,
with the values unchanged.
