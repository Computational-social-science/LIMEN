# Supplementary information

**The LIMEN Phase I report — Orthographic channels and input noise as structural disturbances in human–model interaction**

*Supplementary information is provided by the authors and is not edited.*

---

## Table of Contents

A&nbsp;&nbsp;Pre-registration, Deviations and Amendments &nbsp;·&nbsp; 2
B&nbsp;&nbsp;Stimuli, Noise Generator and Readability Calibration &nbsp;·&nbsp; 4
C&nbsp;&nbsp;The Instrument and Its Pinning &nbsp;·&nbsp; 7
D&nbsp;&nbsp;Power, Sample Size and the Paired Discordance Rate &nbsp;·&nbsp; 9
E&nbsp;&nbsp;Analysis: Estimator, Family and Direction Enforcement &nbsp;·&nbsp; 11
F&nbsp;&nbsp;Machine-Checked Core &nbsp;·&nbsp; 14
G&nbsp;&nbsp;Dev Pre-Run and the Replacement of H1.2 &nbsp;·&nbsp; 16
H&nbsp;&nbsp;Confirmatory Results &nbsp;·&nbsp; 19
I&nbsp;&nbsp;Guards, Negative Controls and Reproduction &nbsp;·&nbsp; 21

---

## Appendix A — Pre-registration, Deviations and Amendments

The main text reports a pre-registered phased study. This appendix records what was fixed before the confirmatory run, what changed, and what the changes cost.

The protocol holds the programme's commitments, and the **anchor governs** which content is current: version **1.23**, pinned by digest in `config/anchor.json` (sha256 `aff24898df9a4e8b…`, 101,011 bytes). Every amendment below is recorded **at the point in the protocol it applies to**, with the document that motivated it, so the protocol's own history remains legible.

### A.1 The frozen design

| Element | Frozen value |
|---|---|
| Design | Within-item; every item appears at every noise level under every seed |
| Noise grid | λ ∈ {0, 0.03, 0.05, 0.08, 0.12, 0.18, 0.25} |
| Seeds | 3, frozen, carried in the stimulus pack name |
| Confirmatory window | 652 items, test split only |
| Dependent variables | Accuracy, SilentError@τ, Coverage@ε, with τ ∈ {0.80, 0.90}, ε = 0.05 |
| Family | Three hypotheses, Holm at FWER α = 0.05 |
| Estimator | Exact paired permutation (§4.5 of the protocol) |
| Gate | Confidence rule `answer if c ≥ τ else defer` |

### A.2 Amendments, each made before the confirmatory run

**Amendment 1 — sample size.** `N = 652` from the pilot's paired-discordance estimate.

**Amendment 2 — four analysis choices frozen before data.** The tie-break takes the most lenient threshold that satisfies the admissibility constraint (maximising coverage); the realised edit rate is reported as a covariate with its per-λ distribution and the zero-edit proportion; the paired discordance is defined in the analysis code with a four-way decomposition; the `ok`/`escalate` question was dropped after measuring it at chance and is disclosed as a deviation from §3.1.

**Amendment 3 — the readability calibration (O1 / O2 / O3).** The noise levels `λ_lo` and `λ_mid` were fixed by a **non-saturating recoverability index** anchored on a **published human result** (Rayner et al. 2006, interior-scrambled text, mean recoverability 0.4480): `λ_lo = 0.05` is the smallest grid point clearing the anchor, `λ_mid = 0.18` the largest. Two earlier instruments were measured and rejected — absolute category ratings (never emitted the lowest category in 120 sentences) and pairwise comparisons against clean text (saturated: P(perturbed judged harder) was 0.90–1.00 at **every** λ including the mildest).

**The O3 deviation, and it is the one a reader should weigh.** The protocol's original design called for a human rater panel with an inter-rater κ floor. **That requirement was withdrawn and replaced by an automatic consistency audit with no human raters.** κ measures agreement between raters — a property of the raters as much as of the items — collapses with uneven category use, depends on rater count, and is compatible with both raters being wrong in the same direction. Agreement is not validity. The replacement audit performs six checks with a shuffled-label control and carries reliability on split-half stability, so reliability becomes a property of the measurement rather than of people.

## Appendix B — Stimuli, Noise Generator and Readability Calibration

In the main text we describe a typed-decision task whose stimuli are natural-language service requests. This appendix specifies the items, the keystroke-faithful typo generator and the calibration that fixed the two noise levels used in the confirmatory contrasts.

### B.1 The item bank

932 items across four domains (access, billing, info, urgency), each item carrying a state, a set of caller-defined options, and a **constructive** gold label — the invariant is computed from the item's own construction rather than annotated, so the label cannot drift from the item. The bank is split into 280 development items and **652 test items**, and the confirmatory window is the test split in full; there is no second selection step, which removes a degree of freedom.

Window comparability was checked **statically, on the bank alone, before the run**: domain marginals χ² p = 0.2932 (total variation 0.0562), template marginals χ² p = 0.7289, every domain covered by 10–12 templates in both splits. **No erratum was required.**

### B.2 The typo generator

Noise is keystroke-faithful: substitutions, transpositions, insertions and deletions drawn from a QWERTY-adjacency channel with class weights, at a per-character probability set by λ. The generator is frozen and carries its seed in the stimulus pack name — originally it did not, which would have made seed 1 overwrite seed 0 and silently converted "frozen before measurement" into "frozen for one seed". With the seed in the name, 96 packs (7 λ × 3 seeds × 3 rater tables) exist and seed 0 is **byte-identical to the frozen packs, 24 of 24 files**.

### B.3 Readability calibration, and why two instruments were rejected

| Instrument | What it measures | Outcome |
|---|---|---|
| Absolute 3-level rating (R/W/X) | rater judgement of recoverability | **rejected** — never emitted X in 120 sentences; weighted κ 0.073 and 0.137 |
| Pairwise vs. clean | which of two is harder | **rejected** — saturated, 0.90–1.00 at every λ |
| Kernel/Kernighan-style recoverability index | posterior mass on the intended word | **adopted** — non-saturating, monotone, resolved against the generator's own channel |

The adopted index is `log P(word|corrupted) ∝ log P(corrupted|word) + log P(word)`, with the channel being the generator's explicit QWERTY model and the prior a published frequency list. It is anchored on the published human result rather than on judgement: **`λ_lo = 0.05`, `λ_mid = 0.18`** are determined by rule, with no discretion.

## Appendix C — The Instrument and Its Pinning

The main text treats the instrument as a fixed, openly licensed measurement device rather than as a research object. This appendix records how that was enforced.

The model is a non-autoregressive encoder under a permissive licence, **pinned by revision digest and by per-file SHA-256**, with a guard that re-verifies the pin on every run. It was never trained: the confirmatory run holds θ frozen and uses the device only for inference. The pin exists because a measurement instrument that can change between runs makes every cross-run comparison uninterpretable.

### C.1 One measured caveat, carried as an invariant rather than an assumption

The library warns, unprompted, that the checkpoint ships temperatures outside its valid range and that **affected confidences are substituted with a constant and are uncalibrated**. The entire design rests on `c = max_j p_j` being a comparable confidence, because two of the three dependent variables are functions of it. The substitution was therefore **measured**: on the confirmatory run, **0 of 13,692 rows carry the substituted constant**, and `c` spans 0.2652–1.0000 over 5,026 distinct values. A one-off observation is not a guarantee, so the observation became a **checked invariant** (`scripts/check_confidence_contamination.py`) that fails on any trial file containing it. This is the difference between reading a warning and acting on one.

## Appendix D — Power, Sample Size and the Paired Discordance Rate

In the main text we state that the design is sized for a pre-registered minimum effect. This appendix gives the arithmetic and the inputs, both measured on the pinned instrument before the seal.

The test is McNemar — a binomial test on the **discordant** pairs — so power depends on `N · π_d` and on the conditional asymmetry `π = c / (b + c)`, not on `N` directly.

| Quantity | Value |
|---|---|
| Paired discordance `π_d`, measured on dev | **0.2036** (frozen pilot estimate 0.1833) |
| Expected discordant pairs at `N = 652` | 132.7 |
| Conditional asymmetry measured | 45 with the hypothesis vs 12 against → π = 0.7895 |
| Holm-adjusted α, three-test family | 0.05 / 3 = 0.0167 |
| **Minimum detectable effect at 80 % power** | **5.41 accuracy points** |
| Effect this design pre-registered | 5.0 points |

**The minimum detectable effect is 5.41 points against a pre-registered target of 5.0 — a match to within a point.** The sample size is therefore sized for exactly the effect the design declared, and `N = 652` needed no erratum.

**A correction that changed the answer, recorded because it did.** The first version of the power script reported the design as *over-powered by 5.11×*, obtained by comparing against the **measured** effect rather than the **pre-registered target**. That comparison is wrong: a design is sized for the effect it declares, and a larger observed effect does not make its sizing a defect. Translating `π` into accuracy points reverses the conclusion, and the translation is now in the script rather than in a reader's head.

## Appendix E — Analysis: Estimator, Family and Direction Enforcement

The main text names the estimator and the correction. This appendix specifies them exactly, and specifies the one estimand that is not a paired quantity.

### E.1 Exact paired permutation

The design is paired at the **unit** level — one clean and one noisy observation per (item, seed) — so the exact permutation distribution is generated by swapping each unit's two observations independently. The test is exact under exchangeability, requires no distributional assumption and no asymptotics, and is the limiting case of a random-intercept model carrying only the item effect. Two hypotheses are directional in the ordinary sense; the third is a **contrast on an AUC**, which is also tested this way because the AUC is a within-unit rank statistic and the same exchangeability argument applies.

### E.2 Direction is part of the hypothesis

Each hypothesis carries its predicted sign. The Holm input is the two-sided p **only when the sign agrees**; otherwise the contrast is recorded as *significant and opposite*, which is a finding in its own right and **never counted as support**. This rule is what converted a genuine result into a correction: the original silent-error hypothesis moved significantly in the *opposite* direction, and without the rule a two-sided p would have reported it as support.

### E.3 An estimand that is not paired: `CondErr@τ`

The conditional error rate among admitted trials has a denominator that **changes with the condition** — the admitted set is 121 items clean against 61 under noise, with an intersection of 51 — so the within-item pairing §4.5 relies on does not exist for it. It is reported, and it is **not** a family member. Naming an estimator the code does not implement is how a pre-registration and an analysis drift apart without anyone noticing; naming the one that runs is not bookkeeping.

## Appendix F — Machine-Checked Core

The main text refers to a formalization. This appendix records what it is, what it changed, and what it does not claim.

The core of the protocol is formalized in Lean 4, **core-only, with no Mathlib dependency**. Every theorem is checked at the kernel level by `#print axioms`, and the discipline is that no theorem may depend on `sorry`; the strongest statements are held to a stricter bar and report **no axioms at all**.

**The formalization is used as a feedback device, not as an appendix.** It found and corrected eight substantive protocol judgments, including the direction of the silent-error monotonicity statement (the protocol asserted non-decreasing; the kernel proves **non-increasing**), an unused premise in the tie-break argument, and an unforeseen small-N collapse in which `ε = 0.05` at `N < 20` makes the minimum admissible threshold an all-reject rule. Each correction is visible at the point in the protocol it changes.

**One theorem exists specifically to justify the replacement hypothesis.** The discriminability estimand was chosen over a bound on a rate because it is **scale-free**, and the instrument's own library warns that its confidence is uncalibrated on an absolute scale. That claim is therefore a theorem: the ordered-pair count — hence the AUC — is **invariant under any strictly increasing rescaling of the confidence scale**, and `#print axioms` reports that it depends on **no axioms at all**. A design justification that can be machine-checked should be machine-checked.

The status record lists **19** theorems with their statements and their axiom status.

## Appendix G — Dev Pre-Run and the Replacement of H1.2

The main text states that one hypothesis was replaced before the seal. This appendix is the record of why, and it is the part of the study we would most want a reader to check.

A pre-run executed the **whole chain** on the development split before any confirmatory data existed, for two reasons: a pre-registration whose pipeline has never run is a plan rather than a protocol, and operational surprises found after the seal can no longer be fixed without an amendment.

| | Measured on dev |
|---|---|
| Feasibility | 560 records in 28.8 s, 0 failures; projected confirmatory load ≈ 5,900 conditions |
| All three seeds | 2,520 records in 69.9 s, 0 failures |
| Clean condition across seeds | **identical** (0.8750 / 0.0357 / 0.4321 three times) |
| λ_lo = 0.05 | does **not** degrade accuracy (0.864–0.907 against clean 0.875) |

The clean cell being identical across seeds is a **self-check that passes**: at λ = 0 the seed has nothing to perturb, so a clean cell that moved with the seed would mean the generator was disturbing something at zero noise and every comparison would have been against a moving baseline.

### G.1 Four probes, and the hypothesis they refuted

The original H1.2 predicted that typo noise **raises** the silent-error rate — errors pushed past the gate. The dev pre-run measured the opposite, and four independent probes agreed:

| Formulation | Clean | λ = 0.18 | Direction |
|---|---|---|---|
| Silent error at the fixed threshold, per trial | 0.0357 | 0.0107 | **falls** |
| Conditional error among admitted trials | 0.0826 | 0.0718 | flat (z = −0.45) |
| Coverage-matched contrast, 8 levels | — | — | **refuted**, no level significant |
| Errors as a share of all errors | 0.286 | 0.044 | **falls** |

The mechanism is one the protocol had **already proved**: `risk_mono` makes the silent-error rate non-increasing in τ, and noise deflates confidence (median `c` 0.886 → 0.765), so fewer trials clear the gate at all and the admitted-and-wrong share falls with them. **A fixed-threshold silent-error rate cannot rise under a confidence-deflating manipulation.** The hypothesis asked the wrong question of the right quantity.

### G.2 The replacement, and its pre-run prediction

The replacement asks a different question of the same data: does the gate's **discriminability** rise? Measured on dev as the within-arm AUC between correct and incorrect trials, it does — and the confirmatory run then tested it. **What the pre-run predicted, and what the confirmatory run found, are compared in Appendix H**; agreement counts only when it was predicted.

### G.3 Predictions made on dev, before the seal

| Predicted | Confirmatory outcome |
|---|---|
| π_d ≈ 0.2036 | 0.19 (b + c = 378 over 1,956 units) |
| minimum detectable effect 5.41 points | accuracy contrast ≈ 12.1 points |
| H1.2′ contrast ≈ +0.1201 | **+0.1587** |
| original H1.2 falls | **−0.0266** |
| no confidence contamination | **0 of 13,692 rows** |

## Appendix H — Confirmatory Results

The main text reports the pre-registered family. This appendix gives the per-level table, the full family result and the co-reported quantities. The run used the test split: **652 items × 7 noise levels × 3 frozen seeds = 13,692 trial records, 0 failures**.

### H.1 The family

| Hypothesis | Predicted | raw p | Holm threshold | Verdict |
|---|---|---|---|---|
| **H1.1** accuracy falls | falls | 4.42e-36 | 0.0167 | **rejected — supported** |
| **H1.2′** gate discriminability rises | rises | 2.00e-04 | 0.0500 | **rejected — supported** |
| **H1.3** coverage falls | falls | 5.00e-05 | 0.0250 | **rejected — supported** |

**No direction violations.** H1.1 discordant pairs: b = 71, c = 307 — more than four items newly wrong for every one newly right. H1.2′ within-arm AUC contrast **+0.1587** over **1,956** exchangeable units. H1.3 mean coverage fall **0.2904**, 95 % CI [0.2679, 0.3154], 648 units down against 80 up.

### H.2 Per-level quantities

Table H1 gives every quantity at every noise level, from which Figures 1–3 of the main text are drawn.

| λ | Accuracy | Within-arm AUC | Coverage@0.9 | CondErr@0.9 | Errors rejected (%) | median c (correct) | median c (error) |
|---|---|---|---|---|---|---|---|
| 0.00 | 0.8926 | 0.6014 | 0.4479 | 0.0925 | 61.4 | 0.8876 | 0.7843 |
| 0.03 | 0.8834 | 0.6587 | 0.4080 | 0.0764 | 73.2 | 0.8764 | 0.7464 |
| 0.05 | 0.8707 | 0.6951 | 0.3850 | 0.0730 | 78.3 | 0.8669 | 0.6529 |
| 0.08 | 0.8574 | 0.7015 | 0.3308 | 0.0742 | 82.8 | 0.8474 | 0.6351 |
| 0.12 | 0.8246 | 0.7271 | 0.2878 | 0.0817 | 86.6 | 0.8181 | 0.5830 |
| 0.18 | 0.7720 | 0.7601 | 0.2111 | 0.0702 | 93.5 | 0.7831 | 0.5486 |
| 0.25 | 0.7025 | 0.7483 | 0.1585 | 0.0710 | 96.2 | 0.7493 | 0.5320 |

*Table H1.* Every value is read from `data/processed/stage2_lambda_summary.csv`, derived from the confirmatory trial record (13,692 rows). Nothing is interpolated or modelled.

### H.3 The co-reported quantity

The original fixed-threshold silent error is reported and nothing more: it moves **−0.0266**, i.e. it falls, opposite to the refuted hypothesis. It reproduces on confirmatory data exactly as the dev pre-run predicted, which is why it no longer occupies a slot in the family.

## Appendix I — Guards, Negative Controls and Reproduction

The main text states that the pipeline is released. This appendix specifies the controls that stand behind that claim.

Every check is a script, every script is exercised on **an injected defect that must make it fail**, and the whole suite runs as one command. The suite covers: object drift, anchor commitment and digest, relative paths, renderer-compatible mathematics, instrument pin integrity, kernel axioms and status freshness, provenance of every substantive claim, the readability anchor, the automatic consistency audit, the confidence-contamination invariant, the analysis controls, the window's comparability, the figure audit, and the ordering checks on the repository's own state.

Two of these are worth singling out because they caught real defects rather than confirming clean work.

**The provenance table is a checked claim, not a label.** A row marked as proved must name a theorem the kernel actually verified, and a row marked as measured must quote a value that appears in the pre-run record; the generator **fails** otherwise. It fired on its first run and refused two tokens that were not in the record. A measurement quoted from nowhere is the same defect as a proof that was never done.

**The ordering check caught scratch output committed to the repository.** Sixteen generated files sat in version control while the guard whose entire job was to catch exactly that reported a pass — because its rule tested for membership in a hand-written list of cache names instead of testing the property. The rule is now structural (any path component beginning with an underscore), and the check is verified by the real defect it found: it failed on those sixteen files and went quiet when they were removed. A guard is only as good as its rule, and a guard that reports a false pass is worse than no guard, because it converts an unknown problem into a believed-clean one.

### I.1 Reproduction

The confirmatory run is one command over the pre-built test bank (652 items, produced statically without running the model), followed by the pre-registered analysis, the replacement-hypothesis contrast, and the contamination invariant. The figures regenerate from the trial record through the per-level CSV, and the figure captions regenerate with every number derived from that CSV.

