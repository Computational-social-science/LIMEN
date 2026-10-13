# The main proposition, and the hypothesis family derived from it

**This document states the programme's central claim and the hypotheses that test it.** It replaces the earlier
gap statement, which was written against the literature's coverage rather than against a mechanism. **The
instruments — the generator, the corpora, the depth metric — are named here only as instruments**, and each is
listed in §5 with what it is subordinated to.

---

## 1. The proposition

> **Whether a language model's errors are visible to its own confidence is determined by the orthographic depth
> of the script it is reading — not by the model.**

**"Silent error" means an error the system commits with high confidence**: the answer is wrong and the model's
confidence gate does not flag it. It is the failure a deployment cannot detect from the inside, and the quantity
this programme has carried as a dependent variable since Phase I.

**The mechanism, in three steps.**

**Step 1 — the decoder's strategy is fixed.** Wang et al. (ACL 2025 Findings) measured that LLMs reconstruct
scrambled words from **word form**, that **context contributes little**, and that attention **reallocates toward
form rather than toward context as scrambling rises** — "a fixed process rather than an adaptive response". **The
strategy does not adapt to the perturbation.**

**Step 2 — a fixed strategy is survivable only while the input still carries a signal of its own degradation.**
In an alphabetic script, a corrupted word **looks corrupted**: the letter string is not the intended one and is
often not a word, so the uncertainty is visible in the input. **This is why, in English, the errors are loud** —
Phase I measured that **93.6 % of noise-induced errors fall below the confidence gate**, against 71.4 % when
clean, and that the gate becomes **more** discriminative under noise, not less (AUC 0.6014 → 0.7601).

**Step 3 — in a logographic script the signal is absent, because the error does not corrupt the form at all.**
Measured over CSCD-NS, **81.4 % of observed Chinese character substitutions (12,334 of 15,143, pooled over all three
splits) have identical romanisation**. The wrong character is **phonologically identical** to the intended one — `惟→唯`, `作→做`, `在→再`. **A
model reading `惟` in place of `唯` sees a perfectly ordinary, frequent character. Nothing in the input is
degraded.** **With no degraded form and no adaptive reweighting toward context, there is nothing from which to
infer that anything is wrong.**

**The conclusion the three steps force**: **a form-reliant, non-adaptive decoder should produce errors that are
loud in a shallow alphabetic script and silent in a logographic one.** The loud/silent distinction is then
**not a property of the decoder**; it is a property of **the script's depth**, acting through the mismatch
between a fixed strategy and a code whose redundancy was destroyed without leaving a mark.

### 1.1 Why this is deeper than a robustness comparison

**It makes the programme's own Phase I result a hypothesis rather than a premise.** "Errors are loud" was
measured **in English**. **If depth governs visibility, that result must not replicate in the logographic arm** —
and **the programme's own prior finding becomes the thing under test.**

**It converts a published description into a prediction.** The ACL 2025 finding of non-adaptation is a
description of English behaviour. **Combined with the measured 81.4 %, it is a mechanism that predicts a specific
failure mode in a script the paper excluded.**

**And it is a deployment risk, not a benchmark gap.** A system that answers confidently and wrongly in a
logographic script **cannot detect its own failure**. Every multilingual calibration result in the literature
(§5) is measured on **clean input**, where this failure has nowhere to occur.

---

## 2. The hypothesis family

**Derived from §1, in the order the derivation forces. Each names its operationalisation, its direction, and what
falsifies it.** All are within one Holm family; direction is part of the hypothesis, so opposite-direction
movement is excluded rather than counted as support (the Phase I convention, retained).

### H2.1 — Silent error rises with depth (primary)

**Claim.** The share of errors committed above the confidence gate, `SilentError@τ`, **increases as orthographic
depth increases**, holding the noise rate fixed.

**Operationalisation.** Depth from `config/depth_axis.json` — borrowed from a published measurement, never
re-derived (rule 19). Noise rate operational and frozen (`config/phase2_levels.json`). Arms: the generator's
segmental languages spanning its measured within-cluster range, **plus Chinese at the outlier end**.

**Direction.** Positive association between depth and `SilentError@τ`.

**Falsified if** `SilentError@τ` is flat in depth, or falls with it.

### H2.2 — The gate stops improving where the input stops signalling (mechanism)

**Claim.** Gate discriminability (AUC) **rises under noise in the segmental arms and does not rise in the
logographic arm.** This is the direct test of step 2: **the gain requires a degradation signal in the input**, and
the logographic arm has none.

**Direction.** AUC gain under noise, positive in segmental arms, **≤ 0 in the logographic arm**.

**Why it is the mechanism test rather than a second outcome.** Phase I already measured the gain at **+0.1587** in
English. **Reproducing it in the segmental arms is a manipulation check; failing to reproduce it in the
logographic arm is the mechanism.**

**Falsified if** the logographic arm shows the same positive AUC gain as English. **That would mean the gate
detects the errors without a degraded form to detect it from** — which would refute the Step 3 argument and
require the 81.4 % structure to be doing nothing.

### H2.3 — Context substitutes for form exactly where form fails (the trade-off itself)

**Claim.** The effect of **context availability** on silent error is **larger in the deep arm than in the segmental
arms.** This is the form/context division of labour stated as a quantity: **where form cannot carry recovery,
context must, and its removal should cost more.**

**Operationalisation.** Context varied on the published **Context Integrity** scale, **CI ∈ {0, 0.25, 0.5, 0.75,
1}** (Wang et al.), applied as an additional factor. **This factor is new to Phase II — Phase I did not vary
context, and without it the trade-off cannot be measured at all.**

**Direction.** Interaction: the CI slope on `SilentError@τ` is **steeper** in the logographic arm.

**Falsified if** the CI effect is equal across arms — which is what the ACL 2025 finding, if it generalised,
would predict, and would mean context contributes little everywhere.

### H2.4 — The ordering is the claim, not any single difference

**Claim.** Across arms, `SilentError@τ` **orders by measured depth**, and the ordering holds **within** the
segmental cluster as well as across the segmental/logographic gap.

**Why this hypothesis exists, and why it is honestly weak-expected.** The `structure\/segmental_cluster` entry of `config/depth_axis.json` records
that the segmental cluster spans only **0.216** in transparency — **so within-cluster ordering is a small effect
that may sit near the noise floor.** **H2.4 is therefore an ordered prediction that may fail within the cluster
while H2.1 succeeds across the gap**, and **that split outcome is informative rather than embarrassing**: it
would locate the depth effect at the grain-size discontinuity rather than as a smooth gradient.

**Falsified within the cluster if** the within-cluster ordering is random — which is the expected outcome if the
effect is a discontinuity rather than a gradient.

---

## 2.5 The instrument-validity prerequisite — binding on every hypothesis above

**No gate-based hypothesis in §2 may be tested until the gate's own primitive has passed a validity check on
known-answer probes.** This is not a precaution; it is a prerequisite, and the measurement that makes it one was
already run on this project and is recorded in `docs/C2_NOUL_VALIDITY.md`.

### 2.5.1 The measurement that makes this binding

Twelve probes whose intended answers were not in doubt — six unambiguous and actionable, six missing the
information — were asked the same question two ways, on **byte-identical state text**, so any difference is the
primitive and not the input:

| Method | mean p(true), actionable | mean p(true), vague | separation | accuracy @ 0.5 |
|---|---|---|---|---|
| **`noul`** (as the protocol specified it) | 0.5145 | 0.4379 | **+0.0766** | **0.5000** |
| **workaround** (two-option `choice`, neutral keys) | 0.5752 | 0.7116 | **−0.1365** | **0.3333** |

**`noul` scored exactly chance, and the documented workaround did worse than chance and in the wrong direction**
— it rated the *vague* probes higher on "clear enough to act on" than the unambiguous ones. **An unambiguous,
urgent, self-contained request was scored as not actionable by both methods**, and the two methods disagreed by up
to **0.60** on identical input, which is a conflict rather than noise.

**And the same study found the other primitive sound.** `choice` reproduced the pilot's clean accuracy **to the
item** (104/120, difference +0.0000). **So the finding is not that the instrument is unusable; it is that the
instrument's primitives differ by an unbounded amount in whether they measure their construct — and that
difference is invisible from the interface.**

### 2.5.2 The consequence, stated as a prerequisite

**A gate primitive that does not measure its construct voids every number computed from it, and the void is
undetectable in the numbers themselves**: a chance-level primitive still returns well-formed probabilities, still
has a spread, and still produces a coverage figure at any ε. **Nothing except a known-answer probe reveals it.**

**Therefore, before H2.1 or H2.2 is run on any arm:**

1. **The gate primitive must be named** — `choice`, `score`, `noul`, or a logit-derived alternative — and the
   choice recorded.
2. **It must be checked against probes with known answers**, with the probes' intended answers fixed **before**
   the check and reported, in the manner of the study above.
3. **A primitive that fails is replaced or dropped, not reported as invalid alongside the result.** Carrying a
   primitive known not to measure its construct adds a liability without adding an endpoint.
4. **If the design gates a claim on more than one primitive, each is checked separately** — the study above
   checked two and they disagreed by 0.60.

**And it must be checked per arm, not once.** **Across scripts the gate is the same question asked about
different text**, and the primitive's validity is a property of the pair, exactly as §2.2 of
`docs/PHASE_II_NOISE_EVIDENCE.md` shows an index value to be a property of the (condition, channel) pair rather
than of the condition. **The failure mode this prevents is the one already met once: a probability that looks like
a confidence, built on across several hypotheses, and chance.**

### 2.5.3 A candidate instrument, with its permitted surface stated

**Clef** (`Cloudflare/clef`, Apache-2.0, post-trained from Qwen3.8-27B) is a decision model that turns a **state**
plus a **schema of typed questions** into **a probability for every allowed option of every question in a single
forward pass**, with **no free-form generation and no output parsing**. Its API is Jev/SystemOne-compatible,
which is the interface family the project's existing harness already speaks.

**It is a good fit for the gate and it is not a substitute for the prerequisite.** The surface is restricted by
§2.5.1 rather than by preference:

| Clef question type | Status for gate use |
|---|---|
| **`choice`** — returns `choice`, `confidence`, `probabilities` | **Permitted, subject to the per-arm check in §2.5.2.** Same family as the `intent` primitive that reproduced to the item |
| **`score`** — ordered options | **Not verified. Requires its own check before use** |
| **`noul`** — returns p(true) | **FORBIDDEN AS A GATE.** Measured at chance, with the documented workaround inverting the ordering |

**Two constraints on its use that are not about validity.** Its release was tested on **a single H200**, and a
27B backbone does not fit this host's **12 GB** card — so its use requires either a larger machine or the
provider's endpoint, and that is a resourcing decision rather than a scientific one. **And its published
leaderboard is a claimant's table, not a reviewed result**: the programme's rule is that published work is a
candidate or an instrument and never an authority, so any figure taken from it is labelled as the claimant's.

---

## 3. The design the hypotheses require

**A three-factor design**, because the form/context question cannot be asked with two:

| Factor | Levels | Source |
|---|---|---|
| **Depth** | the measured axis (`config/depth_axis.json`) | borrowed published measurement |
| **Context integrity** | **CI ∈ {0, 0.25, 0.5, 0.75, 1}** | published operational scale |
| **Noise rate** | operational grids already frozen (`config/phase2_levels.json`) | programme |

**Dependent variables** — unchanged from Phase I, so the two phases are commensurable: **Accuracy**,
**SilentError@τ**, **Coverage@ε**, and **AUC** for H2.2. **τ ∈ {0.80, 0.90}**, **ε = 0.05**.

**Within-item paired design retained**, with the exact paired permutation estimator and Holm correction.

---

## 4. What would end the programme's current direction

**Stated so the claim can fail.**

**If all arms behave like English** — silent error flat in depth, AUC gaining under noise everywhere, context
mattering little everywhere — **then "form reliance" is a property of the model shared across scripts, the
recoverability argument in §1 Step 3 is wrong about what a logographic channel can carry, and the depth axis is
not the variable.** **That is a clean, reportable refutation**, and it would be a stronger result than a
confirmatory one: it would mean a widely-held intuition about script structure does not reach model behaviour.

---

## 5. The instruments, and what they serve

**Listed here only so their role is unambiguous: none of these is the object of study.**

| Instrument | Serves |
|---|---|
| **MultiTypo** (MIT) | the **manipulation** — one mechanism across the segmental range, operational `τ`, fixed seeds. **Its measured boundary at the logographic end is why the observed corpus is required there** (`docs/THEORETICAL_ANCHOR.md` §D1.2) |
| **CSCD-NS**, **Birkbeck**, **QALB** | the **logographic arm** the generator cannot reach; and the **validity criterion** for the generator wherever both exist |
| **Depth metric** (Torres & Futrell 2025) | the **independent variable's values** — borrowed, not re-derived |
| **Steyvers et al. (2024, NMI)** | the **vocabulary** for confidence and discrimination gaps — adopted rather than re-invented |
| **Wang et al. (ACL 2025)** | the **CI scale**, and the **claim H2.3 tests** |

**The proposition in §1 does not depend on any of them.** If a better generator, a better corpus or a better
depth metric appears, §1 is unchanged and only §5 is edited.
