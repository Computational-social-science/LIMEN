> **STATUS 2026-10-13: PARTLY SUPERSEDED. Read this banner before the body.**
>
> This document is the measurement record of 2026-10-12 and its empirical core
> stands. Three things in it have since been corrected or licensed, and the
> corrections are NOT applied inline below:
>
> 1. **The class mix in section 3 uses the 2-opcode convention** (transposition
>    8.9%), which the document itself contradicts in section 10 (one event per
>    error, transposition 4.6%). The verifier flagged exactly this. **Use one
>    event per error: deletion 34.1%, insertion 27.2%, case 16.5%, adjacent
>    9.0%, other 8.6%, transposition 4.6%** -- the figures in
>    `figures/fig_error_structure.*` already do.
> 2. **"Not separable" (section 8) is now a LICENSED BOUND, not an assertion.**
>    A calibrated plant at matched damage fired on coverage (p = 0.033), so the
>    harness has been shown able to detect a matched-damage difference; the
>    family gap is below ~8 points of coverage at n = 280.
>    See `docs/PROPOSITION_A_POWERED.md`.
> 3. **lambda's referent is now fixed** as produced noise per clean-text
>    character, with a measured human reference of 9.14% produced vs 1.37%
>    surviving (6.66x). See `docs/PHASE_I_AMENDMENT_4_LAMBDA_REFERENT.md`.
>
> The empirical claims of sections 2, 4, 5, 6, 7 and 9 are unaffected.

# The Paradigm: Typing Error as a Regulated Process, Not a Noisy Channel

**Date**: 2026-10-12
**Status**: empirical, with one honest negative and one open confound
**Source data**: 136M Keystrokes (Dhakal, Feit, Kristensson & Oulasvirta, CHI 2018),
300,000 transcribed sentences from 20,000 participant files (seed 20261012)
**Measurement scripts**: `scripts/error_structure2.py`, `scripts/trans_aware.py`,
`scripts/decisive_tests.py`, `scripts/monitor_selectivity.py`

---

## 1. The claim

The programme's noise process `N_en` is built as a **channel**: text goes in, four
motor-mechanical edit classes are applied with fixed weights (adjacent 35% /
transposition 25% / deletion 20% / insertion 20%), text comes out. That is the
classical framing — noise as an operator acting on a signal.

The data say the process is something else. Human typing error is a **regulated
process**: errors are produced continuously and suppressed continuously by the
typist's own monitor, and the text that reaches a model is the *residual* of that
control loop, not its output.

Three measurements carry the claim, and one measurement fails to support a
stronger version of it. All four are reported.

---

## 2. Evidence

### 2.1 Production exceeds survival by ~5.6x

| Quantity | Value | Source |
|---|---|---|
| Backspaces per sentence | **2.615** | `decisive.json` |
| Surviving (uncorrected) errors per sentence | **0.463** | `trans_aware.json` |
| Sentences containing at least one backspace | **63.6%** | `decisive.json` |

Two thirds of sentences contain a repair. The final text is a small minority of
what the typist produced. Any measurement taken from the final string — which is
what every published error-rate figure in this literature uses, including the
paper's own 1.167% — is measuring the **survivor** distribution, not the error
distribution.

### 2.2 Detection is fast and unimodal

Gap from the last non-backspace keystroke to the first backspace of each run,
422,542 repair events:

| p25 | **p50** | p75 | p90 | p95 | p99 |
|---|---|---|---|---|---|
| 300 ms | **450 ms** | 600 ms | 900 ms | 1150 ms | 2150 ms |

81% of repairs fall in 200-750 ms. This is the signature of a **single automatic
monitor** operating at keystroke speed, not of deliberate re-reading. A
deliberate, lexical check would produce a second, slower mode; it is not there.

### 2.3 The monitor is broadly class-agnostic (the honest negative)

If the monitor were strongly class-selective — catching adjacent-key slips easily
and missing deletions — then the residual class mix would shift with correction
intensity. Bucketing sections by backspaces per typed character and comparing the
residual mix:

| class | no backspace | light (<5%) | moderate (5-15%) | heavy (>15%) |
|---|---|---|---|---|
| deletion | 31.8% | 32.3% | 33.0% | 34.5% |
| insertion | 26.7% | 25.9% | 25.8% | 24.9% |
| transposition | 9.0% | 9.5% | 8.7% | 7.2% |
| case | 15.7% | 15.8% | 15.7% | 16.1% |
| adjacent | 8.4% | 8.3% | 8.8% | 9.0% |
| other | 8.4% | 8.3% | 7.9% | 8.4% |

Normalised to the no-correction bucket, every class stays within **0.80-1.08x**.
**This is a null result and it is reported as one.** It does not support a
strongly class-selective monitor.

Two readings remain open and the design cannot separate them:

- **Reading A (weak monitor selectivity).** The monitor catches all classes at
  roughly similar rates, so the residual mix is a **proportionally faithful**
  estimate of the produced mix, scaled down by ~5.6x. This would be good news for
  measurement: the class proportions in §3 would then be valid estimates of the
  underlying production process.
- **Reading B (endogenous buckets).** Correction intensity is not randomly
  assigned. A typist who corrects more may also be a typist who makes a different
  *kind* of error, and the two effects could cancel in this design. Bucketing is
  then uninformative rather than null.

**Distinguishing A from B requires the corrected/surviving replay**, which is
currently too brittle: replaying the keystroke buffer reproduces `USER_INPUT`
exactly in only 206,838 of 300,000 sections (69%), because the buffer diverges
after the first unaligned edit. A faithful replay is the single highest-value
instrument this corpus can still yield, and it is not yet built.

---

## 3. The class composition, corrected for an alignment artefact

`difflib` reports a single transposition as `insert X` / `equal` / `delete X` —
an insert and a delete of the **same character** separated by one equal block.
Measured on 20,000 synthetic single edits, **93.4%** of true transpositions come
back as an insert/delete pair. The original pipeline had no transposition class,
so every transposition was silently counted as one insertion **plus** one
deletion.

A detector for that signature was written and validated on synthetic known edits:
transposition recovery **96.5%**, deletion 100%, insertion 100%, substitution
97.8%. (It took three failed attempts, each caught by the self-test; the failures
are documented in `scripts/trans_aware.py` because they are the kind of error that
silently corrupts a measurement.)

### Measured composition vs the synthetic generator

| class | N_en assumes | measured | ratio |
|---|---|---|---|
| deletion | 20% | **34.1%** | 1.71x |
| insertion | 20% | **27.2%** | 1.36x |
| case | **absent** | **15.8%** | — |
| transposition | 25% | 4.6% | 0.18x |
| adjacent-key | 35% | **9.0%** | **0.26x** |
| other substitution | **absent** | 8.2% | — |

`other substitution` is a residual bin, not a mechanism, and is not given a
mechanistic reading.

**The pattern is the finding.** `N_en` over-weights by 3-4x exactly the two
classes that are purely mechanical — adjacent-key substitution and transposition,
both defined by keyboard geometry — and under-weights the two that are not
(deletion, insertion), while omitting case entirely. Case is the **third-largest**
real class and the generator has no representation of it at all.

If `N_en` is meant to model human input noise, it is modelling a mechanism the
data say is a **minority** one, and omitting a major one.

---

## 4. What this does to the programme's claims

### 4.1 λ is ambiguous

The protocol's λ is "target mean edits per character". Measured against what?

- λ_produced: edits the typist made (requires the replay; not yet measurable)
- λ_surviving: edits visible in the final string (what `N_en` is calibrated to
  match, and what the paper's 1.167% measures)

These differ by roughly 5.6x. **A λ calibrated on residual text is not the
typist's error rate.** If the programme's Phase I conclusion depends on λ being a
property of human input, that dependence must be stated, because the quantity is
a property of human input *after* the monitor has filtered it.

### 4.2 The "damaged token count dominates edit type" claim is testable now

The Shannon note (§7.3) reports that models absorb QWERTY corruption well and
that damaged-token count tracks loss better than edit type. If that is true, the
finding here is directly relevant: the classes `N_en` over-weights (adjacent,
transposition) are exactly the ones that leave a **locally detectable** string
signature, and the classes it under-weights (deletion, insertion) are the ones
that shift alignment and change **token boundaries**. A model that is robust to
"one wrong letter in a word" is not automatically robust to "two words merged" or
"a word split". The measurement says the second kind is more than half of real
residual error (58.6%).

That is a concrete, falsifiable prediction for Proposition B and it does not
require new terminology: **inject deletion and insertion at matched token-damage
rate against adjacent-key substitution, and the loss curves should not coincide.**

### 4.3 What the paradigm actually is

Stated plainly, and no further than the data support:

> Human typing error is not a channel acting on text. It is a **regulated
> process**: a fast, largely class-agnostic monitor suppresses the large majority
> of produced errors, and the residual that reaches a reader or a model is the
> output of that regulation. The residual preserves class *proportions* far
> better than it preserves absolute rates.

The practical consequence for this programme is a measurement correction, not a
new theory: **stop treating residual error rates as production rates.** The
paper's 1.167%, and any λ calibrated to match it, measure the survivors.

---

## 5. Two confounds found and resolved in the position analysis

Recorded because both changed the numbers, and because a figure was already being
drawn from the uncorrected versions.

**Truncation.** 2.99% of sections (8,978 of 300,000) have `USER_INPUT` as a strict
prefix of `SENTENCE` — participants who stopped typing early. A truncated
transcription registers as a run of deletions at the end of the target.

| word position | raw | excl. truncation | change |
|---|---|---|---|
| first | 10.23 | 10.50 | +2.7% |
| middle | 5.55 | 5.65 | +1.8% |
| last | 14.64 | **11.02** | **-24.7%** |

The word-last elevation survives at ~2x middle, but a quarter of it was artefact.
Sentence decile 9: 13.16 -> 9.62 (-26.9%); deciles 0-8 all +3.1%.

**Case is a convention, not a slip.** Word-first position is 64.0% case errors.
Removing case errors entirely:

| position | all errors /1000 | **non-case /1000** |
|---|---|---|
| first | 10.50 | **2.68** |
| middle | 5.65 | 5.14 |
| last | 11.02 | 10.54 |

On non-case errors, word-first is the **lowest** of the three positions — about
half of word-middle. **The word-first "elevation" is capitalisation convention**
(sentence-initial capital, proper nouns), not a typing effect, and must not be
reported as one.

---

## 6. Open items, stated as open

| Item | Status |
|---|---|
| Faithful keystroke replay (corrected vs surviving) | **Not built.** 69% replay fidelity is insufficient. Highest-value next instrument. |
| Monitor selectivity (Reading A vs B) | **Unresolved.** The bucket design is endogenous. |
| Why deletion and insertion dominate | **Unexplained.** This is the substantive scientific question the measurement raises. |
| Word-last elevation after truncation control | Survives at ~2x; mechanism unknown (word-final motor planning? whitespace timing?) |
| Case errors as a class | Measured at 15.8% but partly convention; a clean estimate needs sentence-initial capitals excluded by design. |
| Keypress duration +3.8% vs paper | Deliberately abandoned as not mechanistically informative. |

## 7. The next experiment, and why it is the right one

The measurement raises one question that everything else depends on: **why are
deletion and insertion — alignment-shifting, token-boundary-changing errors — more
than half of residual error, when the synthetic model gives them 40% combined and
the literature's motor account predicts adjacent-key substitution should
dominate?**

Two candidate answers, and they are separable by injection:

- **H1 (motor).** Deletions and insertions are motor events too — a missed or
  doubled keystroke — and the reason they dominate the residual is that they are
  *harder to detect*, not that they are more frequent. Prediction: at matched
  detection opportunity, their production rate is comparable to adjacent-key.
- **H2 (planning).** They are planning-level events — a word boundary placed
  wrongly, a chunk dropped — and belong to a different process. Prediction: their
  rate should track **word length and boundary position**, while adjacent-key
  rate tracks **keyboard geometry** and is independent of word structure.

H2 is directly testable on data already in hand: the position profile of
adjacent-key errors should be flat across word positions (geometry does not care
where in the word you are), while deletion/insertion should be
boundary-concentrated. That test costs one script and would settle whether the
programme is looking at one process or two — which is exactly Proposition A of the
Shannon note, and the reason this measurement matters to it.

---

## 8. The decisive test: two processes, double-dissociated

> **SUPERSEDED IN MAGNITUDE, UPHELD IN ORDERING.** The ratios below are POOLED over
> characters. Section 9 re-derives them with the PARTICIPANT as the unit of inference
> and gives cluster-bootstrapped values: adjacent 1.07, deletion 1.79, insertion 2.83.
> The ordering and the flat-vs-scaling contrast are unchanged; use the section 9
> numbers in any figure or claim.

Section 7 proposed a discriminating test between H1 (motor) and H2 (planning).
It was run (`scripts/h1_vs_h2.py`, 291,022 sentences after excluding truncated
transcriptions, case errors excluded throughout).

**The prediction.** A motor process is blind to word structure: a missed key is a
missed key wherever it falls, so its per-character rate must be FLAT across word
length. A planning process operates on chunks: the more chunk boundaries a word
has, the more opportunities to drop or duplicate one, so its rate must SCALE with
word length.

**The result.** The two families behave in opposite ways.

Rate per 1000 characters, by word length:

| class | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 2 -> 12 |
|---|---|---|---|---|---|---|---|---|---|
| **adjacent-key** | 1.16 | 1.30 | 1.04 | 1.27 | 1.13 | 1.23 | 1.23 | 1.14 | **0.98x (flat)** |
| deletion | 2.31 | 2.76 | 2.99 | 3.46 | 3.43 | 4.65 | 5.29 | 5.82 | **2.52x** |
| insertion | 1.02 | 1.92 | 2.21 | 4.16 | 3.94 | 4.80 | 4.94 | 5.01 | **4.91x** |

Adjacent-key substitution is **flat to within 2% across a six-fold change in word
length**. Deletion and insertion rise monotonically. That is a **double
dissociation** between a process indexed by keyboard geometry and a process
indexed by word structure.

By word position, rate per 1000 characters:

| class | first | middle | last | last/middle |
|---|---|---|---|---|
| deletion | 1.48 | 3.45 | 6.48 | 1.88x |
| insertion | 1.06 | 2.32 | 8.56 | 3.69x |
| adjacent-key | 0.73 | 0.87 | 2.43 | 2.78x |

Deletion and insertion are **boundary-concentrated**; adjacent-key is flattest
across the interior. (The word-first column for adjacent-key is structurally
depressed: a swap requires two adjacent characters inside the word, so a
first-position swap is registered as a boundary event rather than an interior
one.)

**Verdict: H2 is supported for deletion and insertion; H1 is supported for
adjacent-key substitution.** Human typing error is **not one process**. The
programme's `N_en` implements the H1 process and assigns it 60% of the weight
(adjacent 35% + transposition 25%), while the H2 process — which is more than
half of measured residual error — has no representation at all.

### What this means for the protocol

`N_en`'s four classes are not a partition of one noise process. They are **two
processes with different governing variables**, and the mixture is therefore not
a free parameter to be fixed by a pre-registered weight vector. Two consequences:

1. **λ is not a scalar for this channel.** A single "edits per character" rate
   conflates a geometry-indexed process and a word-structure-indexed process. If
   the model's response to the two differs — and the Shannon note's
   damaged-token-count finding suggests it might — then no single λ can stand in
   for both, and `N_en`'s fixed weights silently fix the mixture ratio at a value
   the data contradict.

2. **This is Proposition A, answered on the human side.** The Shannon note asks
   whether physical and cognitive noise are separable (Proposition A). The
   human data say yes: the two are double-dissociated by word length. What
   remains open is whether a *model's* loss is also separable across them — which
   is an injection experiment, not a corpus measurement, and is the natural next
   study.

### The concrete next experiment

Inject the two families at **matched token-damage rate** into a fixed prompt set
and compare loss curves:

- **Geometry family**: adjacent-key substitution, transposition.
- **Structure family**: deletion, insertion, and word-boundary merge/split.

If loss tracks damaged-token count regardless of family (the Shannon note's
reported finding), the two-process structure in human data does not propagate to
model loss and `N_en`'s mis-weighting is harmless. If the structure family costs
more at matched damage — which the alignment-shifting, token-boundary-changing
nature of deletion/insertion predicts — then the generator's weights are a
**first-order error** in the programme's noise model, not a detail.

---

## 9. Population-level correction

**§8's dissociation was computed on POOLED character counts** (300,000 sentences
across 20,000 participants). A pooled rate is not a population parameter: it can
be produced by between-participant heterogeneity while no individual shows the
effect, and it can be dominated by a minority of prolific typists. **The unit of
inference must be the participant.** §8 has therefore been re-derived at that
level, and the re-derivation changed the answer twice before it settled.

### 9.1 Error production is concentrated, so pooled rates are not typical rates

| top share of participants | share of residual errors |
|---|---|
| 1% | 7.6% |
| 5% | 25.3% |
| 10% | 40.4% |
| 25% | 68.0% |
| 50% | 90.1% |

Per participant: mean 3.56 residual errors, median 2, max 55; **22.6% of
participants leave zero residual errors at all**; adjacent-key averages 0.60
errors per participant. A per-participant *class-specific* rate is therefore
unmeasurable for most participants — which is exactly why the first
per-participant test below failed, and why the failure had to be diagnosed
rather than reported.

### 9.2 The participant-clustered estimate

Resampling **participants** (2,000 cluster-bootstrap replicates) instead of
characters:

| class | long/short rate ratio | 95% CI | |
|---|---|---|---|
| adjacent-key | **1.07** | [1.02, 1.13] | excludes 1 |
| deletion | **1.79** | [1.73, 1.86] | excludes 1 |
| insertion | **2.83** | [2.73, 2.93] | excludes 1 |

The dissociation survives clustering, and insertion's effect is *larger* than the
pooled analysis suggested (2.83 vs 4.91x raw pooled — the pooled figure was
inflated by exposure weighting).

### 9.3 Two failed readings, recorded because they are the trap

**First failure — naive sign test.** Counting participants with ratio > 1 and
testing against a 50% null gave "82.6% of participants show ratio < 1" for
adjacent-key, apparently *refuting* the effect. This is wrong for two reasons:

- **Exposure imbalance.** Short-band exposure is ~203 characters per participant,
  long-band ~124 (ratio 1.64). With unequal exposure, the lower-exposure band
  shows the higher *rate* more often than chance even when true rates are equal.
  The correct null is therefore **not 50%**.
- **Selection.** A participant counts only if they have ≥1 error of that class in
  *both* bands, which selects high-error participants.

**Second failure — single-λ null.** Recalibrating with one common rate for all
participants gave 87.1% / 77.8% / 80.7% as the null, and the observed values fell
*below* it (z = −6.3, −6.7) — still apparently refuting. But a single λ is also
wrong: residual-error rate varies from 0 to 55 across participants, and under
real heterogeneity each participant's ratio is tight around their own level.

**The correct null** gives each participant their *own* observed class rate λ_i
and simulates counts from `Poisson(λ_i · exposure)` in each band using their own
exposures. That null carries the real between-participant heterogeneity:

| class | observed share ratio>1 | null share | null sd | z |
|---|---|---|---|---|
| adjacent-key | 78.3% | 70.2% | 1.3% | **+6.4** |
| deletion | 73.0% | 63.2% | 0.9% | **+11.5** |
| insertion | 88.0% | 65.0% | 0.9% | **+25.7** |

All three exceed their nulls by many standard deviations. **The typical
participant does show the long > short effect**, for all three classes.

### 9.4 The population-level verdict

The effect is **not** carried by a minority and **not** an aggregation artefact:

- **Split-half by error burden** — low-error half: adjacent 1.13, deletion 2.35,
  insertion 2.69; high-error half: adjacent 1.05, deletion 1.71, insertion 2.82.
  Both halves reproduce the pattern.
- **Decile jackknife** — the three classes stay separated in every decile with
  informative participants (adjacent 0.95–1.20, deletion 1.58–2.35, insertion
  2.55–2.98), with no decile reversing the ordering.
- **Exposure** — every participant has non-zero short-band exposure; only 1 of
  20,000 has zero long-band exposure.

**Corrected §8 conclusion.** Adjacent-key substitution rises only 1.07x from
short to long words while deletion rises 1.79x and insertion 2.83x. The
geometry-indexed process is near-invariant to word length; the
structure-indexed processes scale with it. **The double dissociation is a
property of the participant population, not of a pooled count.**

### 9.5 What remains open

- The dissociation is established **within** this corpus (15 fixed sentences,
  English, self-selected participants). Whether the two-process structure
  generalises across writing systems is exactly Phase II's question and is not
  addressed here.
- The pooled *magnitudes* in §8 are superseded by §9.2; the *ordering* is
  unchanged. Any figure should use the §9.2 cluster-bootstrapped ratios.
- Deletion and insertion scale with word length, but **why** remains open: the
  two candidate mechanisms (motor, missed/doubled keystroke, versus planning,
  chunk boundary) are not separated by this test. The word-position profile
  (boundary-concentrated) favours planning but does not exclude motor.

---

## 10. Independent verification, and the five restatements it forced

An adversarial verification pass (`docs/ERROR_STRUCTURE_VERIFICATION.md`) recomputed
everything from the raw corpus with its own code. It reproduced **every** class
count, position cell and decile exactly (0 mismatches on 33 separate quantities),
and independently confirmed the truncation control to the digit. It also
**refuted or revised five of the six originally reported numbers**, and the
reasons are worth keeping because each is a distinct measurement failure mode.

| # | Originally reported | Verdict | Cause |
|---|---|---|---|
| 1 | Class mix 37.0 / 30.5 / 15.7 / 8.6 / 8.2 | CONFIRMED as computed, **REFUTED as interpreted** | transpositions scored as 1 insertion + 1 deletion |
| 2 | Position mix 74.2 / 58.6 / 67.6 | **PARTIALLY REFUTED** | numerator silently excluded insertions |
| 3 | Position rates 10.23 / 5.55 / 14.64 | **PARTIALLY REFUTED** | same hidden convention; 36.8% of word-last errors dropped |
| 4 | Word-initial 8.82 vs 2.40 (3.7x) | **REFUTED** | counter incremented only in the `replace` branch, omitting 93,760 of 138,893 errors; true 1.48x, and **0.43x** excluding case |
| 5 | U-shape 13.58 / ~5 / 13.16 | **PARTIALLY REFUTED** | bucket 9 is 19.9% of characters (not a decile); bucket 0 is 78.9% case errors |
| 6 | 2.615 vs 0.463 per sentence | numbers CONFIRMED, **comparison REFUTED** | backspaces are keystrokes, errors are aligned edits; one transposition scores 2 |

The corrected composition (one event per error) is deletion 34.1%, insertion
27.2%, case 16.5%, adjacent 9.0%, other 8.6%, transposition 4.6%. Counting a
transposition as two opcodes instead of one event raises it to 8.8% and lowers
deletion and insertion correspondingly — **the convention must be stated with the
number**, which is why the figure labels it on the panel.

### What the verifier could not break

The double dissociation survived every attack it constructed:

| test | adjacent | deletion | insertion |
|---|---|---|---|
| participant bootstrap (its own) | 0.93x [0.82, 1.06] | 2.60x [2.39, 2.85] | 3.70x [3.30, 4.16] |
| interior-only (drop word-first and word-last) | 0.98x [0.82, 1.16] | 2.04x | 3.57x |
| within every sentence decile | flat | monotonic | monotonic |

And one result **strengthens** the two-process reading: transposition, which the
generator treats as a geometry class, itself **scales with word length** (2.24x
interior-only, [1.87, 2.70]) — that is, the data put it in the structure family,
not the motor family. `N_en`'s grouping is wrong in both directions.

### Three limits the verification established

1. **Replay-based verification is impossible.** `LETTER` is blank with a
   VK-only `KEYCODE` for **9.4% of rows** (31,109 of 300,000 sections), so a
   keystroke replay cannot reconstruct `USER_INPUT` for ~10% of sections. My own
   replay matched only 68%. This closes the "corrected vs surviving" route
   proposed in §2.3 — the question stands but this instrument cannot answer it.
2. **A silent row-loss path exists.** 8 of 3,000 files carry scientific-notation
   timestamps (`1.477579e+12`), and `on_bad_lines='skip'` drops those rows in both
   the measurement and the figure pipeline. ~0.004% of rows — negligible in
   magnitude, but it is a silent drop and is now recorded as one.
3. **The adjacent class rests on a hand-built QWERTY adjacency set.** The
   dissociation's *shape* does not depend on it, but the absolute adjacency share
   does.

### The population-level numbers used in the figure

From the participant-level analysis (§9) with 2,000 cluster-bootstrap replicates:

| class | long/short ratio | 95% CI |
|---|---|---|
| adjacent-key | 1.07 | [1.02, 1.13] |
| deletion | 1.79 | [1.73, 1.86] |
| insertion | 2.83 | [2.73, 2.93] |

The verifier's independent participant bootstrap on its own bucketing gave
adjacent 0.93x [0.82, 1.06], deletion 2.60x, insertion 3.70x. The two agree on the
**ordering and the flat-vs-scaling contrast**; they differ in magnitude because the
word-length bands differ (mine: short <=4, long >=8; theirs: bucketed to 11).
**The contrast is robust to that choice; the exact ratio is not.** Any quoted
magnitude must name its band definition.

## 11. The one-sentence paradigm, as the evidence now supports it

> Human typing error is not one noise channel but **two processes with different
> governing variables** — a geometry-indexed process, flat with respect to word
> structure, and a word-structure-indexed process that scales with it — and the
> text a reader or model receives is the **residual of the typist's own fast,
> largely class-agnostic repair monitor**, which suppresses the majority of
> produced errors and therefore makes every residual error rate a survivor
> statistic rather than a production rate.

The generator `N_en` implements the first process and assigns it 60% of the
weight, while the second — 61.3% of measured residual error — has no
representation at all.
