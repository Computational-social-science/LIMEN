# Phase II pre-registration — the cross-channel phase

**Status: DRAFT, unfrozen.** This document fixes the Phase II design before any Phase II data exists. It is
filed under the protocol's §5.1 entry criterion 3, which requires a new pre-registration for Phase II
hypotheses and forbids any retroactive change to Phase I.

**Governing artefact:** the pinned protocol (content digest in `config/anchor.json`). This document does not
replace it; where the two disagree, the protocol governs and this document is amended.

---

## 1. Entry criteria, and the evidence for each

The protocol's §5.1 states three gates. Phase I is complete, so each can be assessed now rather than promised.

| Gate | Evidence | Status |
|---|---|---|
| Pipeline error rate below the pre-set bound | Phase I confirmatory: **13,692 trial records, 0 failures** | **met** |
| Noise process and labels stable under an independent re-run | Phase I ran three frozen seeds; the clean condition is verified identical across seeds, and the generator seed is carried in the pack name after a failure in which regenerating at seed 1 silently overwrote seed 0 | **met** |
| A new pre-registration filed for Phase II hypotheses | this document | **this document** |

**What the entry criteria do not say, and what must not be inferred from them.** Passing a gate means the
component is **used exactly as shipped**; it does not mean the component was validated. Phase I's instrument,
bank and noise process were *admitted*, not *validated*, and the same posture carries forward — a Phase II that
opened by improving the instrument would make every cross-channel contrast a statement about the improvement.

---

## 2. What Phase I changed about this plan

**This section exists because the protocol's §5.4 was written before Phase I produced a result, and Phase I
refuted the hypothesis that §5.4 rests on.**

The protocol's H2.2 is stated as *SilentError@0.9 contrast > 0*. That form cannot be tested, and the reason is
machine-checked, not empirical: **the risk at a threshold is non-increasing in that threshold** (`risk_mono`: `Risk b xs <= Risk a xs`
for `a <= b`, with `silent_iff_acceptedAndWrong` fixing what a silent error is), so no confidence-deflating
manipulation can raise a fixed-threshold silent-error *rate* — the trials leave the admitted set before they can be counted. Phase I found the same
defect in its own H1.2, refuted it on development data in four independent formulations, and replaced it
before the confirmatory run. The refutation is itself machine-checked and carries the protocol's own name in
its own: **`protocol_said_nondecreasing_is_FALSE`**.

**So Phase II inherits the correction rather than repeating the error.** Three consequences, and they change
what Phase II is:

1. **The silent-error rate is not an endpoint, here or there.** Any hypothesis phrased as a rise in it is
   withdrawn in advance. This is not a weakening: it is the same correction, applied once instead of twice.
2. **The cross-channel claim is a claim about the FRONTIER and about SENSITIVITY, not about a rate at a
   threshold.** The theoretical frame states why: coverage and the conditional error are criterion-dependent
   readings of where the operating point sits, while discrimination is criterion-free. A channel difference
   that is a criterion difference and a channel difference that is a sensitivity difference call for different
   conclusions and different remedies, and a design that measures one family cannot tell them apart.
3. **The Phase I mechanism supplies a directional prediction across channels, and it is falsifiable.** Phase I's
   account is that confidence falls when the surface form is improbable *under the intended meaning* — which is
   why channel-side noise is loud. That account **predicts that the loudness is a property of the noise
   process, not of noise as such**: a channel whose corruption leaves the surface form unsurprising while
   changing the answer should produce errors that do not announce themselves. See §7.

---

## 3. The object

One primary contrast: the orthographic channel $s$, at two levels, English ($s_{\mathrm{en}}$) and one second
channel ($s_1$), each crossed with its own noise grid. The estimand is the **difference in the frontier and in
the discrimination between channels**, holding the intention and the instrument fixed.

**Phase I fixed $s$ and varied $\lambda$; Phase II varies both.** The protocol's staging principle is that no
single phase tests both fully, and the reason this phase comes second is that the plumbing — the confidence
rule, the gate, the record schema, the guards — has now been shown to work once, so a second channel
introduces one new variable rather than several at once.

---

## 4. Design

| Factor | Levels |
|---|---|
| Channel $s$ | $s_{\mathrm{en}}$, $s_1$ |
| Noise $\lambda$ | $0$, $\lambda_{\mathrm{lo}}$, $\lambda_{\mathrm{mid}}$ — **channel-specific generators, not shared levels** |
| Seeds | frozen, at least three, carried in the pack name as in Phase I |
| Items | parallel intentions across channels, within-item pairing preserved |

**Within-item, and what "parallel" has to mean.** The Phase I design pairs every item against itself across
noise levels; Phase II must additionally pair an item against **its counterpart in the other channel**. A
"parallel intention" is therefore not a translation of the English item — it is the same decision task,
constructed independently in $s_1$ under the same template and the same constructive gold-label rule, so that
the label is computed from the item's own construction rather than judged. **A translated bank would make every
cross-channel contrast a statement about the translation.**

---

## 5. Channel selection ($s_1$)

The protocol's §5.3 permits a non-Latin script with documented digital-input confusions, a distinct orthographic
standard within one language family, or an IME-mediated input ecology. This section fixes the **criteria**; the
choice is recorded as an amendment once made, before any data.

**Required:**

- (i) parallel intentions can be constructed under the same template, with constructive labels;
- (ii) the noise process can be built **faithfully** from that channel's own input ecology;
- (iii) the instrument can be pinned at a revision that reads the channel.

**Forbidden:** implementing $\mathcal{N}_{s_1}$ as English typo operations applied to transliterated text. That
would make the noise an artefact of the transliteration and the contrast a statement about it.

**A prediction that favours one kind of channel over another, recorded before the choice is made.** Phase I's
mechanism says the loudness of channel-side noise comes from the surface form being improbable under the
intended meaning. A substitution-style channel (wrong character, implausible surface) should therefore be
*loud*; a **segmentation or conversion channel** — an IME that commits to a wrong but perfectly ordinary word, a
script without word delimiters where the wrong segmenation is still readable — produces **a surprising surface
and a wrong answer**, which is the model-side signature. **If the choice is free, choosing a channel of the
second kind makes the experiment test the mechanism rather than illustrate it.** The choice must still satisfy
(i)–(iii); the mechanism is a tie-breaker, not a criterion.

---

## 6. Noise equivalence, and what is not allowed to justify it

The protocol's §5.2 forbids equating levels by "the same edit rate as English" alone. Levels are equated by one
of two admissible routes, **stated here before any calibration runs**:

- **(a) a human pilot** measuring recoverability of the intended word under the channel's own noise; or
- **(b) documented per-channel empirical error rates** from an external source.

**Phase I's route was a published human anchor, and the same index applies.** Phase I fixed its levels with a
non-saturating recoverability index — the noisy-channel posterior mass on the intended word, with the channel
being the generator's own model — anchored on the interior-scrambled condition of Rayner et al. (2006),
recovered 0.4480 of the time. Phase II uses the same index per channel, and reports the anchor it used.

**Two earlier instruments were measured and rejected in Phase I and are not revisited**: an absolute
three-level rating that never emitted its lowest category (weighted $\kappa$ 0.073), and pairwise comparison
against clean text, which saturated at 0.90–1.00 even at the mildest level. **Neither was a rater failure; both
were instrument failures**, and the same reasoning applies to any Phase II instrument that fails the same way.

---

## 7. Hypotheses, frozen with their directions

Each hypothesis carries its predicted **direction** as part of its statement, and enters the Holm family only
when the observed movement agrees with that direction. A significant movement the wrong way is recorded as a
**direction violation** and never counted as support — the rule Phase I adopted after its original silent-error
hypothesis moved significantly in the *opposite* direction.

Let $F_s$ denote the channel's coverage–error frontier and $\mathrm{AUC}_s$ the within-arm discrimination.

**H2.1 — the criterion differs by channel.** The operating point moves differently: at matched recoverability,
coverage at a fixed threshold differs between channels, $|\mathrm{Cov}_\tau(s_1) - \mathrm{Cov}_\tau(s_{\mathrm{en}})| > 0$,
in a direction fixed by the calibration result recorded before the run (§6). *This is a criterion claim and is
reported as one.*

**H2.2 — sensitivity differs by channel, and it is the claim of substance.** $\mathrm{AUC}_{s_1} \neq \mathrm{AUC}_{s_{\mathrm{en}}}$
at matched recoverability, with the **direction fixed in advance** by §5's mechanism prediction: a
substitution-style channel is predicted *more* discriminative under noise (configural, and the errors announce
themselves), a segmentation-or-conversion channel *less* (the surface is unremarkable, and the errors do not).

**H2.3 — the frontier differs by channel, priced as a disparity.** At matched recoverability, the reachable
(coverage, conditional-error) pairs differ systematically between channels, reported as the **frontier gap** at
a pre-declared pair of operating points rather than as a single number. *This replaces the protocol's
SilentError@0.9 disparity, which §2 withdraws.*

**H2.4 — the Phase I mechanism predicts which side of the partition a channel lands on.** For a channel whose
noise is substitution-style, the Phase I signature reproduces: rejection share rises with severity and the
conditional error does not. For a segmentation-or-conversion channel the reverse is predicted: rejection share
roughly flat or falling, conditional error rising. **This is the hypothesis that turns Phase I's partition from a
description into a mechanism**, and it is the one most likely to be wrong.

**Withdrawn in advance:** any hypothesis asserting a rise in a fixed-threshold silent-error rate (§2).

---

## 8. Estimands and the multiplicity family

- **Paired within-item contrasts**, as in Phase I: exact paired permutation under exchangeability, $+1$
  correction, no distributional assumption.
- **The family is declared before the run** and contains H2.1–H2.4 at the pre-registered primary level, with
  Holm correction; channel × noise exploratory contrasts are reported outside the family and marked as such.
- **Complements are declared, not corrected.** Conditional error and conditional accuracy among admitted trials
  are functions of one another; a study reporting both as independent evidence has counted one thing twice, and
  no multiplicity correction repairs that because it corrupts the family rather than the p-value. Which quantity
  is a function of which is decided before the family is written, and stated with it.
- **Threshold-dependent quantities carry their absolute threshold.** The scale-free result licenses the ordering
  claims and nothing else: on Phase I's record, rescaling every confidence by a strictly increasing family left
  the AUC's spread at exactly 0.000 while moving a threshold quantity by 43.6 points. Any quantity bounded at an
  absolute threshold inherits the instrument's calibration and is reported as design-relative.

---

## 9. Power

**No power number is stated here, and that is deliberate.** Phase I's power came from its measured paired
discordance ($\pi_d = 0.2036$), which is a property of its manipulation. **Phase II's discordance is unknown
until its noise process exists**, and a discordance borrowed from Phase I would be exactly the unmeasured
proxy this project forbids in a success criterion.

**The procedure, fixed now so the number cannot be chosen later:**

1. Build the $s_1$ noise process and calibrate its levels (§6).
2. Measure $\pi_d$ for the cross-channel contrast on **development items only**.
3. Set $N$ from the measured $\pi_d$ at 80% power against a minimum detectable effect **fixed before step 2**.
4. Record the ambiguity: Phase I's MDE was 5.41 accuracy points against a pre-registered target of 5.0 — a
   margin of 0.41 points, reported as such rather than as a pass.

---

## 10. What would falsify the programme

Stated before the run, because a partition that predicts which side of itself a new manipulation lands on is a
mechanism, and a mechanism that cannot be wrong is a taxonomy.

- **If a substitution-style channel produced Phase I's signature and a segmentation-or-conversion channel did
  not, H2.4 holds** and Phase I's mechanism survives the channel change. **If both produce the same signature,
  the mechanism is wrong** and the partition is descriptive only.
- **If sensitivity differences vanish at matched recoverability, the cross-channel claim reduces to a criterion
  difference** — a real finding about operating points and not a claim about capability, and it must be reported
  as the former.
- **If the frontier gap is zero at matched recoverability while the AUC gap is not**, the two families of
  measure have come apart in a way the frame does not predict, and the frame is what is wrong.

---

## 11. The feedback axis — deferred, and previewed as theory rather than as a plan

Phase I's Discussion defers *feedback and accommodation between turns*. Two classical results bear on it and
**neither is invoked as a hypothesis here, because neither has been measured on this loop:**

- **Multi-turn joint decoding.** Slepian and Wolf show that correlated sources can be decoded jointly at the sum
  of their rates even when they cannot communicate — the classical statement that *decoding jointly recovers
  more than decoding separately*. A multi-turn interaction is a sequence of correlated observations of one
  intention, so the result gives the form of a prediction: the coverage cost of channel noise should fall when
  turns are decoded together rather than independently. **Stated as the form of a prediction, not as an
  instance**: whether a human's turns are the kind of correlated sources the theorem bounds is exactly what has
  not been established.
- **Token allocation under noise.** Water-filling allocates power across a channel by giving more to the
  sub-channels with better signal-to-noise, and less to the bad ones. If a re-prompting policy is a power
  allocation over semantic regions, the same shape predicts that spending tokens where the posterior is flat
  beats spending them uniformly at equal budget. Again the shape, not the theorem.

**Both are listed here so that a future phase cannot present them as new.** Neither enters Phase II's
hypotheses, and a phase that measures them needs its own pre-registration.

---

## 12. Instrument

The protocol's §5.5 governs: keep the Phase I pinned instrument as the backbone where possible; if a
multilingual checkpoint or router is required for $s_1$, **pin it by revision digest and per-file SHA-256** and
report the English cells under **the same** artifact for comparability, with a sensitivity run using the Phase I
pin on English cells only.

**Ambiguity is a result, not a nuisance.** If the second channel requires a different artifact, then the English
cells under the two artifacts differ, and *that difference is a measurement about the artifact, not about the
channel*. It is reported as such, and it is the reason the sensitivity run is mandatory rather than optional.

---

## 13. Deviations log

Amendments to this document are numbered, dated, and state the reason, as in Phase I. **A change after any
Phase II data exists is a deviation and is reported in the manuscript as one**, not folded silently into the
design.

| # | Date | Change | Reason |
|---|---|---|---|
| — | — | (none yet) | — |
