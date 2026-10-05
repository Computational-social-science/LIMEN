# Amendment 3 — O1: the λ readability calibration

**Status:** decisions (1) and (3) of §7 are **ACCEPTED**; decision (2) is **ANSWERED** — the human
panel is replaced by an autonomous rater, which was then validated against human-annotated data.
**§12 item 2 remains `λ PENDING`**, for a narrower reason than before: see §8. The measured evidence
is in `measurement/o1_validation/RESULTS.md`, and the instrument is `scripts/o1_agent_rater.py`.
**Scope:** closes O1 only. O3 (the human pass over the item bank) and the template imbalance reported by
`scripts/template_confound_probe.py` are untouched by this document and remain open.

---

## 1. What O1 has to decide, and what it does not

§12 item 2 requires the typo classes **and the λ rates** to be fixed, and the protocol's own words are
that *items must remain human-readable at `lo` and stressed at `mid`*. That sentence already answers
the question the checklist raises — **who reads** — and the answer is a human reader. So O1 does not
decide whether humans can read typos; that is given. What O1 must supply is **the measurement that makes
the judgement reproducible**, because "readable" is otherwise a private impression and a reviewer cannot
check it.

**Three things are therefore in scope:** the exact λ values, the criterion that decides each one, and
the procedure that applies the criterion. **Two things are explicitly out of scope:** whether the model
can be expected to handle the resulting text (that is what Phase I measures), and any tuning of the
generator to make a chosen λ look good (the generator is frozen by contract and is not adjusted here).

## 2. What was measured before designing anything

Measured on the sealed 932-item bank, 120 items per level, `seed = 0`
(`measurement/typo_noise.py:typo_noise`, contract: `typo_noise(text, item_id, lam, seed) -> (text, ops)`,
`lam` = target edits per character):

| λ (target) | 0.03 | 0.05 | 0.08 | 0.12 | 0.18 | 0.25 |
|---|---|---|---|---|---|---|
| realised mean | 0.0282 | 0.0510 | 0.0784 | 0.1184 | 0.1788 | 0.2579 |
| realised / target | 0.940 | 1.020 | 0.980 | 0.987 | 0.993 | 1.032 |
| SD | 0.0136 | 0.0196 | 0.0226 | 0.0323 | 0.0391 | 0.0487 |
| coefficient of variation | 48 % | 38 % | 29 % | 27 % | 22 % | 19 % |
| items with zero edits | 2.5 % | 0.8 % | 0 % | 0 % | 0 % | 0 % |

**Three consequences, and they changed what this document had to propose.**

1. **The generator does not need recalibrating.** The realised-to-target ratio stays within 0.94–1.03
   across the whole ladder, so λ already means what §4.2 says it means. A calibration that "corrected"
   these numbers would be inventing a discrepancy that does not exist.
2. **λ is a target, not an achievement, and the spread is wide.** At λ = 0.05 the per-item realised rate
   ranges from 0 to 0.107 — a genuinely perturbed item and a genuinely untouched item at the *same* λ.
   This is not a defect; it follows from Poisson sampling of edit counts per item. It does mean the
   confirmatory analysis must treat `realised_edit_rate` as a covariate rather than assuming λ is a
   constant (Amendment 2, B2), and it means **readability must be judged on the realised distribution**,
   not on λ.
3. **Zero-edit items at λ > 0 are accidental controls and must be reported, not discarded.** At
   λ = 0.03, 2.5 % of items are untouched. They are informative — they bound the noise effect from one
   side — and dropping them would bias the contrast.

## 3. The criterion: three readers, one pre-registered decision

§12 asks for *who reads* and *what counts as readable*. This section fixes both, and — the part that
matters for a pre-registration — it fixes **the decision rule before any rating is collected.**

**Who reads.** An **autonomous pairwise rater**, frozen and validated. The protocol's sentence says the
reader is human; the reader is now a machine, and that substitution is only defensible with evidence, so the
evidence is measured rather than asserted.

**The human panel was the first proposal, and it was replaced for a reason that matters more than cost.**
Three human raters measure disagreement *between people*; a single model at temperature 0 disagrees with
itself not at all, so its self-agreement is 1.0 by construction and is not evidence of anything. Replacing a
panel with one model therefore **removes** the very quantity κ was there to measure. Validity evidence has
to come from outside — from human annotations the rater did not produce and cannot influence.

**What was measured, and what it forced.** Against a human readability annotation derived from four
independent annotators (`measurement/o1_validation/RESULTS.md`):

- **Absolute R/W/X assignment fails**: weighted κ = 0.073 (Qwen3.6-35B) and 0.137 (Qwen3.8-27B) against the
  protocol's own floor of 0.60, with the scale collapsing toward its easy end — the first model emitted `X`
  zero times in 120 sentences.
- **Pairwise ordering succeeds**: 0.967 concordance on *this study's own* manipulation (λ 0.05 vs 0.18, same
  sentence), with a position-A rate of 0.500. Against the foreign human annotation it reaches 0.714 — short
  of 0.80, and above the 0.633 the absolute form managed.

So the instrument is **pairwise ordinal**: it orders two texts, it does not place one on a scale. The
category assignment is then derived from the ordering rather than demanded of the model directly.

**Blind, not comparative.** The rater is shown **only** the perturbed text. Amendment 3 had it see the clean
text first; a real reader has no clean text, and — decisively — the comparative form is the one **no
external dataset can validate**, because the validation corpus ships no clean original to show. Blind is
both the faithful operationalisation and the validatable one.


**What counts as readable.** For each item the rater sees the clean text and the perturbed text, in
that order, and assigns one of three ordered categories — no free-text field is analysed, to keep the
rating itself from becoming a prompt:

| Code | Category | Operational meaning |
|---|---|---|
| **R** | Readable | the intended content is recoverable without hesitation |
| **W** | Wobbly | recoverable, but the reader visibly hesitates or must re-read |
| **X** | Lost | the intended content is not recoverable from the perturbed text |

**Why three categories and not two.** A binary readable/unreadable split forces a judgement exactly at
the boundary where the programme's two conditions live, and it cannot distinguish "hard but fair" from
"broken". `W` is the category that carries the information: the hypothesis is that `lo` is mostly R with
some W, and that `mid` is mostly W with some X. A rule that cannot express that cannot test it.

**The frozen decision rule.** With `n = 60` items per level (drawn from the **dev** split only — never
from test). The reliability clause is now the rater's own validated one — **pairwise concordance ≥ 0.80 with
position-A rate within 0.15 of 0.5** — rather than Fleiss' κ, because there is one rater and a single rater
cannot have inter-rater agreement. `κ ≥ 0.60` is retained as the **floor for any human spot-check** that is
run against the rater, where it remains the right statistic:

| Level | Accept iff | Otherwise |
|---|---|---|
| **λ_lo** | median category **R** and `P(X) ≤ 0.10` | lower λ and re-run |
| **λ_mid** | median category **W** and `0.15 ≤ P(X) ≤ 0.60` | raise λ if the median is still R; lower λ if `P(X) > 0.60` |

**Why `mid` needs both a median and a tail, and why the tail is two-sided.** The first draft of this
rule asked `mid` for a median of W *or* R together with `P(X) ≥ 0.25`. Scoring a synthetic panel through
it showed the flaw immediately: a panel in which **every** item is W has median W and `P(X) = 0`, so it
failed a rule that demanded a large lost fraction — correctly, because an item nobody fails to read is
not a hard item. But loosening the median to "W or R" would then accept that same panel, which is worse.
The fixed rule requires `mid` to sit **between** the two states: typically wobbly, with a real minority
genuinely lost. The upper bound matters for the opposite reason — past it, the text is broken rather than
stressed, and a protocol that ran it anyway would be measuring comprehension failure, not a disturbance
effect. **This is why the ladder is not simply pushed upward until something satisfies a threshold.**

**And the band the protocol already suggested (§4.2: ~5–8 % and ~12–18 %) is the search range**, searched
on a fixed grid inside it — `lo ∈ {0.05, 0.06, 0.07, 0.08}`, `mid ∈ {0.12, 0.14, 0.16, 0.18}` — so the
search is finite and is reported in full whether or not it succeeds. **The first grid point that
satisfies the rule is taken**, scanning `lo` upward and `mid` upward; there is no discretion after the
grid is fixed.

**Why the rule is written on the MEDIAN and on `P(X)`.** The median states the typical experience, which
is what "human-readable" means in the protocol's sentence. `P(X)` states the tail, because a level at
which 40 % of items are unreadable is not "stressed", it is broken, and a protocol that ran it anyway
would be measuring a comprehension failure rather than a disturbance effect.

## 4. What is recorded, and what would falsify this document

Every rating is written to `measurement/o1_ratings.csv` with rater id (anonymised), item id, λ, seed,
category, and the realised edit rate of that item — so the readability judgement can be related to the
noise actually delivered rather than to the λ that was requested.

**Four outcomes are all informative, and three of them are not "failed calibration":**

| Outcome | Reading |
|---|---|
| both levels accepted on the first grid points | the suggested bands in §4.2 are adequate |
| `lo` accepted only after descending | §4.2's indicative band was too high; the band was a guess and is now measured |
| **λ_mid cannot reach median W with `0.15 ≤ P(X) ≤ 0.60` at λ ≤ 0.18** | **the edit classes are too gentle** — this is evidence about §4.2's class list, not about λ |
| κ < 0.60 | the three categories do not capture what readers experience; the instrument is wrong, not the items |

The third row matters most: if `mid` never becomes hard enough, no choice of λ can satisfy the
criterion, and the honest response is to say so rather than to extend the ladder past the band until it
does. **The ladder is not extended beyond 0.18 without an amendment.**

## 5. Why the rater decides, and why an automatic score still only explains

The obvious cheap alternative — a character-level entropy or word-error score — is rejected as the
*decision* criterion for the reason Amendment 3 gave: it is not the quantity the protocol names. §12 says
*human-readable*, and a metric that scores character statistics answers a different question. That argument
survives the panel's replacement unchanged: a validated rater standing in for a reader is still answering
the reader's question, and a WER is not. **The automatic measures remain recorded**, so the readability
judgement can be related to a quantity a reviewer can recompute.

**What did not survive is the assumption that a rater can simply be substituted without being measured.**
The validation above is the price of the substitution, and it turned out to change the instrument's form —
from category assignment to pairwise ordering — rather than merely its operator. §8 states which parts of
the criterion that instrument can support and which part it cannot.

### 5.1 Measured, and it changed the instrument

`scripts/o1_auto_indices.py` computes four indices on all eight grid points, 60 dev items each,
`seed = 0`. No model is loaded, so nothing here can drift with a checkpoint.

| role | λ | WER | word recoverability | char lost | sentence recoverability | realised rate |
|---|---|---|---|---|---|---|
| lo | 0.05 | 0.216 | 0.936 | 0.0011 | **0.958** | 0.050 |
| lo | 0.06 | 0.247 | 0.917 | 0.0010 | 0.942 | 0.059 |
| lo | 0.07 | 0.264 | 0.909 | 0.0016 | 0.917 | 0.066 |
| lo | 0.08 | 0.278 | 0.882 | 0.0021 | 0.817 | 0.080 |
| mid | 0.12 | 0.296 | 0.818 | 0.0026 | **0.642** | 0.122 |
| mid | 0.14 | 0.297 | 0.811 | 0.0017 | 0.608 | 0.134 |
| mid | 0.16 | 0.297 | 0.766 | 0.0025 | 0.383 | 0.160 |
| mid | 0.18 | 0.297 | 0.749 | 0.0024 | 0.342 | 0.174 |

**WER SATURATES AND THEREFORE CANNOT SEPARATE THE `mid` GRID.** From λ = 0.12 upward the word error rate
moves by less than 0.001 — 0.2962, 0.2968, 0.2968 — while the realised edit rate keeps climbing from
0.122 to 0.174. The standard measure has stopped responding to the manipulation. `char_lost` is worse
still: it sits between 0.0010 and 0.0026 across the whole ladder and moves non-monotonically, so it
carries no signal at all.

**This is the concrete argument for the protocol's ordering.** If WER had been the criterion, the four
`mid` grid points would have been indistinguishable and the calibration would have had nothing to
choose between — not because the levels are equivalent to a reader, but because the measure stopped
moving. A human panel is not a luxury added to an automatic method here; it is the only instrument in
this set that still discriminates.

**Sentence recoverability is the one automatic index that keeps discriminating**, falling 0.642 → 0.342
across exactly the range where WER is flat. It is the share of sentences retaining at least 80 % of
their words within edit distance 1. It is recorded as a secondary column and is **not** promoted to a
decision criterion: it is a proportion computed from the item, whereas the protocol's requirement is a
judgement about reading, and the two agree often enough to be informative and not often enough to
decide.

### 5.2 What the numbers say about the grid, before any human rating

Read as evidence rather than as a decision:

- **`lo` at 0.05 leaves 96 % of sentences intact**, which is consistent with "readable" and would be
  consistent with "too easy to be a disturbance" if the panel agrees. The grid is correctly placed to
  distinguish those.
- **`mid` at 0.12 already sits at 64 % sentence recoverability**, which is plausibly the "wobbly"
  region. If the panel's median at 0.12 is already **W** with a tail, the rule may be satisfied at the
  **first** grid point, and the upper three become unnecessary.
- **If the panel's median at 0.18 is still R**, the finding is about §4.2's edit classes rather than
  about λ, exactly as §4 anticipates. Sentence recoverability at 0.342 says the text is heavily
  damaged while nearly every word survives at distance 1 — which is a *specific* mechanism
  (character-level corruption rather than word destruction) and is worth stating in that case.

**None of this is a result.** It is a prediction with a stated uncertainty, made before the ratings
exist, so that the panel's answer can be compared against it rather than rationalised after the fact.

## 6. Cost, and how the ladder is actually walked

Measured from the generated packs: **24 packs, 60 items each, 1 440 item-ratings in total** — 480 per
rater if the whole grid is rated, at a median of 366 characters per item (both texts together).

**The whole grid is NOT the plan; it is the budget ceiling.** The rule scans `lo` upward and `mid`
upward and takes the **first** grid point that satisfies it, so the expected cost is far lower:

| what is rated | item-ratings |
|---|---|
| `lo` at 0.05 and `mid` at 0.12 — the first point of each, if both pass | **360** |
| `lo` through 0.08 and `mid` at 0.12 — the likely case if `lo` needs one step | 540 |
| the entire grid, both ladders exhausted | 1 440 |

At a three-way choice on a ~180-character pair, roughly 25–40 minutes per 60 items, so the expected
total is **about 30–60 minutes per rater**, and the ceiling is about two hours. No GPU, no model, no API.

**Why walk upward rather than rating everything.** Each additional grid point costs three raters a full
panel, and the decision rule only needs the first point that passes. Rating the whole grid in advance
would also create a temptation the protocol should not have: with eight measured levels in hand, it
becomes easy to pick the one whose numbers look best rather than the first one the rule accepts. The
scan order is fixed in advance precisely so that the choice cannot be made after seeing the panel.

**The `--score` path exists for either route.** Rate what the walk asks for, then
`python scripts/merge_ratings.py` followed by `python scripts/o1_calibration.py --score`.

## 7. Decisions — all three now answered

1. **Accept the three-category scheme and the grid.** **ACCEPTED.** R/W/X and the grid
   `lo ∈ {0.05, 0.06, 0.07, 0.08}`, `mid ∈ {0.12, 0.14, 0.16, 0.18}`, first satisfying point taken, scanning
   upward.
2. **Name the rater panel.** **ANSWERED — and the question changed the answer's shape.** The panel is
   replaced by an autonomous rater, validated against human-annotated data. The measurement forced the
   instrument from *category assignment* (which failed: κ = 0.073 / 0.137 against a 0.60 floor) to
   *pairwise ordinal judgement* (0.967 on this study's own manipulation, 0.714 on the foreign human
   annotation). Evidence: `measurement/o1_validation/RESULTS.md`.
3. **Accept that `mid` failing to reach the band is a finding about the edit classes**, not a licence to
   raise λ past 0.18. **ACCEPTED.** The ladder is not extended beyond 0.18 without an amendment.

## 8. What is still open, and why §12 item 2 stays `λ PENDING`

The median half of the criterion is supported: the rater orders this study's manipulation reliably, so
"`mid` is harder than `lo`" and "the median item at `mid` is W rather than R" are answerable.

The **tail half is not**. `0.15 ≤ P(X) ≤ 0.60` needs an *absolute* cut — how many items are genuinely lost —
and no configuration produced a trustworthy absolute `X` rate: the first model never emitted `X` at all, and
the transfer corpus cannot calibrate the rate cleanly because its spread is inflated by
paraphrase-equivalent corrections, which is disagreement about wording rather than about meaning.

**Therefore one of two things must be written down before the seal:**

- **anchor the `X` cut on the external human data** — fix the jfleg spread value at which annotators
  effectively lost the meaning, and carry that cut across to the ranking of our items; or
- **restate the criterion ordinally**, replacing `P(X)` with a rank-based tail (e.g. the share of `mid`
  items ranked harder than the 90th percentile of the `lo` items), which needs no absolute anchor and is
  evaluable with the instrument that was actually validated.

Both are amendments and neither is assumed here. **Until one is accepted, §12 item 2 stays `λ PENDING` and
no confirmatory data may be generated.** This document replaces "who reads" with a measured instrument; it
does not close O1.
