# O1 instrument validation — measured results

**Date:** 2026-10-05 · **Status:** measured, not yet written into the protocol
**Question answered:** can an autonomous rater replace the three-reader human panel that Amendment 3 proposed?

**Short answer: partly.** The rater reliably orders *this study's* manipulation. It does **not** reproduce a
human readability annotation well enough to stand in for one on an absolute scale. The instrument that
follows from the measurements is a **pairwise ordinal** one, not a category-assigning one.

---

## 1. The human criterion, and its own validation first

jfleg (`jhu-clsp/jfleg`, 1503 sentences) ships **four independent human corrections per sentence**. The
spread among those four IS a human annotation of whether the intended content came through unambiguously:
low spread = the annotators agreed on what the sentence meant.

**The criterion was validated before being used as ground truth**, against a quantity computed
independently of it — the distance from the original to each correction, i.e. how much needed repairing:

| Quantity | Value |
|---|---|
| n | 1501 |
| Spearman(human spread, independent repair distance) | **+0.723** |
| median spread | 0.1319 |
| tertile cut points | 0.0887 / 0.1798 |

Human disagreement rises with how damaged the sentence is, so the label is a sensible measure of sentence
damage. **Whatever fails below is the rater, not the criterion.**

---

## 2. Mode A — absolute category assignment (what Amendment 3 proposed)

Frozen instrument: local `Qwen3.6-35B-A3B-UD-Q4_K_M`, `enable_thinking=false`, temperature 0, **blind**
(the rater is not shown the clean text — see §5).

| Configuration | weighted κ | unweighted κ | Spearman(rater, human) | pairwise concordance | notes |
|---|---|---|---|---|---|
| Qwen3.6-35B, thinking off, n=120 | 0.073 | 0.038 | −0.252 | — | **emitted `X` zero times in 120 sentences** |
| Qwen3.8-27B, thinking off, n=120 | 0.137 | 0.075 | −0.352 | 0.633 (5032 pairs, null 0.499) | emits `X`; latency 26.1 s/item |
| Qwen3.6-35B, thinking **on**, n=120 | — | — | — | — | **0/120 parsed — see §6, this is a harness defect** |

**Both absolute configurations fail the protocol's own κ ≥ 0.60 floor, by an order of magnitude.**
The confusion structure is the diagnosis: Qwen3.6 never emits `X` at all, and Qwen3.8 emits it for 26 of 40
highest-ambiguity sentences while still calling 14 of them readable. The scale collapses toward its easy end.

**On the κ statistic, and a flaw in its use here.** The human label is *relative* — a third of these
sentences are the most ambiguous, not necessarily unrecoverable — while R/W/X is *absolute*. Forcing equal
tertiles onto an absolute scale charges the rater for the mapping's assumption. The order is what both
scales actually carry, which is why pairwise concordance is reported alongside, on a shuffled null (0.499)
so the number has a reference point.

---

## 3. Mode B — sensitivity to this study's own manipulation

Same sentence corrupted by the frozen generator at three λ, absolute labels (frozen default):

| λ | mean readability (R=2, W=1, X=0) | R/W/X |
|---|---|---|
| 0.05 | 1.680 | 35/14/1 |
| 0.12 | 1.540 | 28/21/1 |
| 0.18 | 1.500 | 26/23/1 |

Spearman(λ, mean readability) = **−1.000** (correct direction), but **per-item monotone only 35/50 = 0.700**.

So the direction is right and the item-level noise is large — the signature of a rater whose *mean* tracks
the manipulation while individual judgements do not.

---

## 4. Pairwise mode — the instrument the measurements point to

Ordering two texts is better posed for a language model than placing one on an absolute scale. Both sides
are presented for half the pairs, so position preference is measured rather than assumed away.

| Test | concordance | position-A rate | n |
|---|---|---|---|
| vs the human ordering (gap ≥ 0.05, jfleg) | **0.714** | 0.455 | 77 (8 ties) |
| **vs this study's own manipulation** (λ 0.05 vs 0.18, same sentence) | **0.967** | 0.500 | 60 |

**This is the load-bearing result.** The rater orders *this study's* manipulation at 0.967 with no side
bias, and orders a foreign human annotation at 0.714 — short of the 0.80 floor, and above the 0.633 the
absolute form managed.

**What that combination means.** The instrument is fit for the question O1 actually asks ("is `mid` harder
than `lo`") and only moderately fit for the transfer question ("does it agree with humans on other people's
errors"). The transfer is limited for a reason that is visible in the data: jfleg's spread is inflated by
**paraphrase-equivalent corrections** — annotators who disagree about wording while agreeing about meaning —
which is noise with respect to recoverability. The +0.723 self-validation bounds that contamination but does
not remove it.

---

## 5. Why the judgement is blind

Amendment 3 had the rater see the clean text and then the perturbed text. **A real reader has no clean
text.** Judging with the answer in view is a different and easier task, and — decisively — it is the task
**no external dataset can validate**, because jfleg provides no clean original to show. Blind is both the
faithful operationalisation and the validatable one.

---

## 6. Two harness defects found on the way, both of which would have been misread

**A. An authentication failure was being counted as "unparseable".** Launched from an environment without
`HERMES_LOCAL_LLAMACPP_KEY`, every call returns HTTP 401; an earlier version of the runner recorded each as
an unparsed judgement and printed `0/120 parsed`. That reads like *a rater that will not answer* when in
fact **the rater was never asked**. A run now aborts with an explicit auth error. *An authentication
failure is a fact about the harness and must stop the run rather than become a statistic.*

**B. `--thinking on` reported as 0/120 is not a result about the model.** The comparison override raised
thinking without raising `max_tokens`, so all 64 tokens were consumed by reasoning and no answer was
emitted. **This must not be reported as "thinking-on fails".** The frozen configuration is thinking OFF; the
comparison is un-run, and is recorded as un-run rather than as a failure.

**C. Temperature 0 is not determinism on this server.** Repeat runs of 24 items under the frozen config
agreed on 22/24. Continuous batching changes the numerics, so the instrument is *not* bit-reproducible under
concurrency. This is a property of the serving stack and must be stated wherever the rater's labels are
reported as reproducible.

---

## 7. The configuration is part of the instrument

Measured: **with reasoning enabled the rater answers `R` on a sentence where, with reasoning disabled, it
answers `W`** — 28 s versus 2 s per item. A rater whose label depends on whether it may deliberate is two
raters. The configuration is therefore frozen and written down:

```
model           Qwen3.6-35B-A3B-UD-Q4_K_M   (local, free; no paid route)
endpoint        http://127.0.0.1:18434/v1/chat/completions
temperature     0
enable_thinking false          <- changes the label; pinned for that reason
max_tokens      64             <- valid ONLY while thinking is off
prompt          frozen in scripts/o1_agent_rater.py:PROMPT / PAIRWISE_PROMPT
judgement       BLIND (never shown the clean text)
```

Changing any field invalidates the validation above and requires re-running it.

---

## 8. What this means for O1, stated without softening

1. **The human panel is not replaceable by an absolute autonomous rating.** κ = 0.073 / 0.137 against a
   floor of 0.60. On a scale the protocol intends to threshold, that is not usable, and no averaging
   decision changes it.
2. **A pairwise rater IS usable for the comparative core**, and that is what the design actually needs:
   `mid` is required to be harder than `lo`. 0.967 on this study's own manipulation, no position bias.
3. **The absolute criterion `0.15 ≤ P(X) ≤ 0.60` is not externally validated.** No configuration produced a
   trustworthy absolute `X` rate, and the transfer dataset cannot calibrate one cleanly. Either the `X`
   cut is anchored on external human data explicitly, or the criterion is restated ordinally.
4. **Transfer to a human annotation is moderate (0.714) and must be reported as a limitation**, not
   presented as agreement.

**Therefore O1's instrument becomes: pairwise comparisons → a ranking → thresholds applied to the ranking,
with any absolute `X` cut anchored on the jfleg human spread rather than on the rater's own labels.** The
protocol's median criterion survives unchanged; its `P(X)` clause is the part that needs the anchor.

**Until that anchoring is written down and accepted, §12 item 2 stays `λ PENDING`.** This document does not
close O1; it replaces "who reads" with a measured instrument and states exactly which part of the criterion
that instrument can and cannot support.


---

## 9. The calibration run, and why it refutes the criterion it was written to satisfy

`--calibrate` scored all 60 dev items at all eight grid points against each item's **own clean version**,
both sides presented, so `s = (times the perturbed text is called harder) / 2`.

| λ | 0.05 | 0.06 | 0.07 | 0.08 | 0.12 | 0.14 | 0.16 | 0.18 |
|---|---|---|---|---|---|---|---|---|
| `P(s = 1)` | 0.983 | 0.900 | 0.967 | 0.950 | 1.000 | 0.983 | 1.000 | 0.983 |
| position-A rate | .517 | .533 | .483 | .517 | .500 | .517 | .500 | .517 |

**The rater calls the perturbed text harder than the clean text on 90–100 % of items at EVERY grid point,
including the mildest.** Position bias is flat at ~0.5 throughout, so this is not a side artefact.

**The question is trivial.** One of the two texts contains typos; asking which is harder to recover is
answered by noticing the typos, at any rate. The instrument detects *that* corruption is present, not *how
much*.

**So the `lo` rule `P(s = 1) ≤ 0.10` is unsatisfiable by construction with this instrument.** It does not
fail because the edit classes are too harsh at λ = 0.05 — that was the message the script printed, and it is
wrong: the run's own numbers show the rate barely varies across a 3.6× range of λ, which is the signature of
a saturated question, not of a harsh one. **The rate would read the same at λ = 0.005.**

**What this does and does not disturb.**

- **Unaffected: the comparative core.** The 0.967 concordance was measured at λ 0.05 **versus** λ 0.18 — an
  ordering *across* noise levels — and that is a different, well-posed question the rater answers reliably.
- **Refuted: `lo`'s absolute readability.** "Items remain human-readable at `lo`" is anchored to the clean
  text, and the only comparison that reaches clean is the saturated one. The 0.714 transfer against human
  judgement (floor 0.80) says the same thing from the other direction.

## 10. Consequence: the autonomous-rater substitution does not cover O1's `lo` criterion

The decision taken was to replace the three-reader panel with an autonomous rater validated against human
data. **Measured, that substitution holds for the comparative half and fails for the absolute half.**
No third restatement of the criterion changes this: each restatement so far has moved the goal to whatever
the instrument could reach, which is the failure mode the project guards against.

**What O1's `lo` needs is one of:**

1. **human raters**, as Amendment 3 originally proposed — the instrument this was meant to replace; or
2. **an externally anchored threshold**: a λ whose readability is fixed by published human data rather than
   by this rater, with the transfer limitation stated as a limitation.

`P(s=1) ≈ 0.95` at every λ is reported either way, because it is the measurement that makes the choice
necessary rather than a preference.
