# Amendment 3 — O1: the λ readability calibration

**Status:** DRAFT for decision. Nothing here is frozen; §12 item 2 remains `λ PENDING` until you
accept or amend it.
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

**Who reads.** A panel of **three English-native adult raters**, recruited outside the research team,
each rating independently. A single rater's judgement is an anecdote; three is the smallest panel whose
disagreement can be measured rather than assumed away.

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
from test), and raters agreeing at Fleiss' κ ≥ 0.60:

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

## 5. Why three measures and not one

The obvious cheap alternative is an automatic readability score. It is rejected as the *decision*
criterion for one reason: it is not the quantity the protocol names. §12 says *human-readable*, and a
metric that scores character-level entropy answers a different question. **It is still recorded**, as a
secondary column — normalised edit distance and token-level perplexity under a fixed reference model —
because a human judgement that cannot be related to any quantity is harder to reproduce. The human panel
decides; the automatic measures explain.

## 6. Cost and what this buys

120 items × 2 conditions × 3 raters = **720 ratings**, each a three-way choice on a short text —
roughly 25–40 minutes per rater. No GPU, no model, no API. It is the cheapest open item on the board and
it is the one standing between the programme and a sealed pre-registration.

## 7. Decisions this document needs from you

1. **Accept the three-category scheme and the grid**, or state the alternative criterion.
2. **Name the rater panel** — three English-native adults, or someone else you trust to define the
   reader. The protocol says the reader is human; it does not say who counts as one.
3. **Accept that `mid` failing to reach median W with `0.15 ≤ P(X) ≤ 0.60` is a finding about the
   edit classes** rather than a licence to raise λ past the band.

Until (1)–(3) are answered, §12 item 2 stays `λ PENDING` and no confirmatory data may be generated.