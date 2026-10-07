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

**The frozen decision rule (v2 — ordinal tail, 2026-10-05).** With `n = 60` dev items per grid point
(**dev only** — never test). The rater is pairwise and blind; every judgement is made against the item's
**own clean version**, so the score is a per-item difficulty relative to that item, not a position on a
shared absolute scale.

For each dev item and each grid λ, the λ-version and the clean version are presented **twice, both sides**,
and the item scores `s = (number of times the λ-version is called harder) / 2`, so `s ∈ {0, 0.5, 1}`.

| Level | Accept iff | Otherwise |
|---|---|---|
| **λ_lo** | `P(s = 1) ≤ 0.10` — the noisy text is essentially never harder than the clean one | lower λ and re-run |
| **λ_mid** | `median(s) = 1` **and** `P(s_mid = 1 and s_mid > p90(s_lo)) ∈ [0.15, 0.60]` | raise λ if the median is 0; lower λ if the share exceeds 0.60 |

**Why the tail is ordinal and no longer `P(X)`.** The previous rule asked for `0.15 ≤ P(X) ≤ 0.60`, where
`X` meant *the intended content is not recoverable*. That needs an **absolute** cut, and the validation
found none: the absolute rater emitted `X` **zero times in 120 sentences** at one configuration and
mis-called 14 of the 40 most-ambiguous sentences at another, with weighted κ 0.073 / 0.137 against a floor
of 0.60. **An absolute threshold on an instrument that cannot place a text on an absolute scale is a
number about the instrument, not about the text.**

The replacement keeps the intent — *`mid` must be genuinely stressed, not destroyed* — and expresses it in
the only currency the instrument was validated to carry. The upper bound is still two-sided on purpose:
past 0.60, the text is broken rather than stressed, and a protocol that ran it anyway would be measuring
comprehension failure rather than a disturbance effect.

**What was validated, and what was not.** Pairwise ordering against *this study's own* manipulation scored
**0.967** with position-A rate 0.500. Against a foreign human annotation it scored **0.714** (short of the
0.80 floor). So the rule is written on the within-item comparison — the validated part — and **the transfer
limitation is carried as a stated limitation, not as agreement**. Full evidence:
`measurement/o1_validation/RESULTS.md`.

**The band the protocol suggested (§4.2: ~5–8 % and ~12–18 %) is the search range**, searched on a fixed
grid — `lo ∈ {0.05, 0.06, 0.07, 0.08}`, `mid ∈ {0.12, 0.14, 0.16, 0.18}` — so the search is finite and
reported in full whether or not it succeeds. **The first grid point that satisfies the rule is taken**,
scanning `lo` upward and `mid` upward; there is no discretion after the grid is fixed.

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

## 8. The criterion, restated on the recoverability axis (v3 — FINAL)

**Three instruments were tried; only the third reaches the quantity the criterion names, and the two
failures are why the third is credible.**

| # | Instrument | What it measures | Verdict |
|---|---|---|---|
| 1 | LLM rater, absolute R/W/X | an absolute readability category | **refuted** — weighted κ 0.073 / 0.137 against a 0.60 floor; never emitted `X` once in 120 sentences |
| 2 | LLM rater, pairwise vs clean | which of two texts is harder | **saturated** — P(perturbed called harder) = 0.900–1.000 at every λ including the mildest; it detects *that* corruption is present, not *how much* |
| 3 | **noisy-channel recoverability index** | posterior mass on the intended word | **works** — non-saturating, monotone, resolved against generator noise, and anchored on a published human result |

### 8.1 The instrument

Bayesian noisy channel (Kernighan, Church & Gale 1990; Brill & Moore 2000; Jurafsky & Martin app. B):

```
r(w | surface) = P(surface | w) . P(w)  /  sum_w' P(surface | w') . P(w')
```

The **channel** is measured from this project's own frozen generator (2046 corrupted words; 507
substitution / 25 insertion / 22 deletion operations, add-k smoothed) — an estimate with a sample size.
The **prior** is published lexical norms via `wordfreq`'s aggregation of SUBTLEX and Leeds, deliberately
not counted from our own texts: a prior counted from the material being rated would make easy words easy
by construction. The item index is the mean of `r` over the item's content words.

### 8.2 The anchor

**Rayner, White, Johnson & Liversedge (2006), "Raeding wrods with jubmled lettres: There is a cost"**
(*Psychological Science* 17(3)): first and last letter of each word fixed, interior rearranged. Readers
answered comprehension questions **with high accuracy** and read **~11 % slower** — stressed but well
within tolerance. Scored with the same index on the same 60 dev items:

| Condition | `mean_r` |
|---|---|
| Rayner (2006), interior **scrambled** — the harsher variant, and the floor | **0.4480** *(measured under this index, not quoted from the paper)* |
| Rayner (2006), interior **adjacent transposed** | 0.4750 |
| our λ = 0.05 (mildest) | 0.5216 |
| our λ = 0.18 (harshest) | 0.4847 |

**Every grid point is more recoverable than both variants of a condition humans demonstrably handled.**
The harsher variant is the tighter bound, and the ladder clears it by 0.074 at its mildest point.

### 8.3 The criterion, and it is determinate

Because every grid point clears the published floor, the criterion needs no band and no discretion:

| | Rule | This grid |
|---|---|---|
| **λ_lo** | the **smallest** grid λ with `mean_r ≥ 0.448` | **0.05** |
| **λ_mid** | the **largest** grid λ with `mean_r ≥ 0.448` | **0.18** |
| **separation** | `mean_r(λ_lo) − mean_r(λ_mid)` must exceed twice the pooled seed SD | **0.0309 vs 2 × 0.0051 → 6.07 SD** ✓ |

**Why "largest" for `mid` and not a band.** The intent has always been *stressed, not destroyed*. The
anchor is the published statement of "not destroyed"; the largest λ clearing it is therefore the
**most stressed point that is still inside human tolerance**, which is exactly what `mid` is for. It also
coincides with the upper end of §4.2's suggested band, so the protocol's own guess was not displaced —
it was measured and confirmed.

**And the earlier worry that the narrow range might be noise is refuted by measurement, not left
standing:**

| λ | seed 0 | seed 1 | seed 2 | mean | SD |
|---|---|---|---|---|---|
| 0.05 | 0.5216 | 0.5234 | 0.5254 | 0.5235 | 0.0019 |
| 0.12 | 0.5059 | 0.5139 | 0.4995 | 0.5064 | 0.0072 |
| 0.18 | 0.4847 | 0.4917 | 0.5012 | 0.4925 | 0.0083 |

The separation is **6.07 pooled seed standard deviations**. Small in magnitude, clean in signal. `seed = 0`
also reproduces the frozen pack value exactly, which confirms independently that regenerating from the
clean text equals the packs while the generator is frozen.

### 8.4 Why the edit classes are NOT changed

An earlier revision of this section named strengthening the edit classes as the action item, on the grounds
that `mid` is only modestly stressed. **That is withdrawn.** Two reasons, and the second is decisive:

1. **H1 needs a measurable manipulation, not a large one.** The separation is 6.07 seed SD and both ends
   are anchored — that is a manipulation H1 can detect a model effect against.
2. **Changing the generator would invalidate every measurement this criterion now rests on** — the channel
   is measured from it, the stimulus packs are generated by it, and the anchor is measured on those packs.
   A change there buys a larger effect at the cost of re-deriving the whole instrument chain, for no gain
   in what the criterion establishes.

**The honest action item is therefore none, and the criterion is closed.** A narrow-but-real manipulation
is a fact about the design to be reported, not a defect to be engineered away.

### 8.5 State

**λ_lo = 0.05 and λ_mid = 0.18 are selected by a rule that is fully determined by measured quantities**,
so **§12 item 2 moves from `λ PENDING` to `FIXED — by Amendment 3 v3`**, with the criterion, the anchor
and the separation all carried and all guarded (`scripts/check_o1_anchor.py`, four checks plus a negative
control).

**Carried limitations, stated rather than buried:** the LLM rater's transfer to a foreign human annotation
was moderate (0.714 against a floor of 0.80), which is why it decides nothing here; temperature 0 is not
determinism on this server (24 repeats agreed 22/24) because continuous batching changes the numerics; and
the recoverability index's absolute level depends on the candidate vocabulary and the smoothing, which the
anchor is therefore doing the work of fixing rather than the index's raw scale.

**Authority:** `scripts/o1_recoverability.py` (`--build-channel`, `--demo`, `--anchor`, `--seed-variance`) ·
`measurement/o1_validation/anchor.json` · `measurement/o1_validation/seed_variance.json` ·
`measurement/o1_validation/channel.json` · `measurement/o1_validation/RESULTS.md` §9–11.
