# Dev pre-run on the pinned instrument — measured, before the seal

**When:** 2026-10-05 · **Instrument:** `convaiinnovations/laya` @ `55cf4c4ebb4e…`, cuda, 421M, frozen
**Data:** the **dev** split only (280 items) · λ ∈ {0.0, 0.18}, seed 0 · **560 trial records, 0 failures**
**Not confirmatory data.** The test split is untouched, and nothing here enters a confirmatory result.

---

## 1. Feasibility: the run is minutes, not hours

| | |
|---|---|
| records | 560 in **28.8 s** (≈ 20–35 rows/s including model fetch) |
| failures | **0** |
| projected confirmatory load | 652 test items × 3 λ × 3 seeds ≈ **5,900 conditions** |
| projected wall clock | **under 10 minutes** of GPU time |

So GPU time is not the constraint on this study, and the plan is feasible as frozen.

**Confidence contamination re-checked on the larger sample:** `c == 0.5` appears in **0 of 560** rows,
`c` spans 0.296–1.000 over 514 distinct values. The library's invalid-temperature warning concerned a route
this model does not take on this task. `scripts/check_confidence_contamination.py` keeps that as an
invariant rather than a hope.

---

## 2. The effect is large

| λ | accuracy | error rate | median `c` |
|---|---|---|---|
| 0.0 (clean) | **0.8750** | 0.1250 | 0.8859 |
| 0.18 | **0.7571** | 0.2429 | 0.7650 |

**An 11.8 percentage-point accuracy drop** from typo noise at λ = 0.18, with median confidence falling
0.886 → 0.765. The manipulation does something large and confidence moves with it.

---

## 3. `π_d` measured, against the value that froze `N`

| | |
|---|---|
| frozen in Amendment 1 (used to set `N_test = 652`) | **0.1833** |
| **measured here on the pinned model, dev, λ 0.0 vs 0.18** | **0.2036** |

Discordant split: 45 items right→wrong, 12 wrong→right, 200 right→right, 23 wrong→wrong.

**The measured value is 11 % higher than the frozen one, and that direction is favourable**: `π_d` is the
paired-information rate, so more discordance means more information per item, which makes a fixed `N` more
powerful rather than less. **So `N = 652` remains conservative and needs no erratum on this evidence** —
but the direction is stated because it was checked rather than assumed, and a future run on the test split
should confirm it.

---

## 4. THE FINDING: H1.2's direction is contradicted by the instrument itself

| probe | clean | λ = 0.18 | hypothesis |
|---|---|---|---|
| accuracy | 0.8750 | 0.7571 | H1.1 predicts **falls** ✓ |
| Coverage@0.9 | 0.4321 | 0.2179 | H1.3 predicts **falls** ✓ |
| **SilentError@0.9** | **0.0357** | **0.0107** | **H1.2 predicts RISES — it FALLS** ✗ |

**H1.2 as pre-registered is stated in the wrong direction, and the mechanism is one this project already
proved.** `risk_mono` (§15) establishes that `SilentError@τ` is **non-increasing in τ**. Typo noise lowers
confidence — median `c` 0.886 → 0.765 — which moves the operating point toward a *stricter effective gate*:
fewer trials clear τ = 0.9 at all (coverage 0.432 → 0.218), so the share that are both admitted and wrong
falls with them.

**A fixed-τ silent-error rate therefore CANNOT rise under a manipulation that deflates confidence.** The
hypothesis asked the wrong question of the right quantity. The quantity that is supposed to rise — errors
reaching the reader through the gate — is the **conditional** one, and the protocol already has it:
`CondErr@τ` (§6.1), the error rate **among admitted trials**, which was introduced in v1.5 for a different
reason and now turns out to be the one H1.2 needed.

**The response, and why it is legitimate to make it now.** The confirmatory run has not happened and the test
split is untouched, so this is a pre-run finding about the pre-registration, not a result about the world.
Two options, and the choice is a scientific one rather than a technical one:

1. **Restate H1.2 on the conditional quantity**: `CondErr@0.9(λ_mid) > CondErr@0.9(0)` — the error rate among
   admitted trials, which is the quantity the mechanism predicts rises. `CondErr` is already defined (§6.1),
   already known to be the complement of the H1.1 co-report (so H1.1's co-report becomes the H1.2 contrast),
   and its rise while coverage falls is precisely the "silent error" the programme exists to describe.
2. **Keep the fixed-τ estimand and reverse the predicted sign**, which would make H1.2 assert that noise
   makes the gate *safer* — true arithmetically, and not what the study is about.

**Recommendation: option 1**, tabled as an amendment. It is the only one of the two that keeps H1.2
answering the question the protocol's own §0.4 says the programme is for.

**Until that amendment is accepted, `H1.2` must not be run as written**, because the analysis code enforces
direction and would record a correct measurement as a direction violation.


---

## 5. Power recomputed on the measured values — and the frozen `N` is correctly sized

`scripts/phase1_power.py` recomputes Phase I power from what the pre-run measured rather than from what the
pilot assumed. McNemar is a binomial test on the *discordant* pairs, so power depends on `N · π_d` and on the
conditional split `π = c / (b + c)`, not on `N` directly.

| | |
|---|---|
| expected discordant pairs at N = 652 | 652 × 0.2036 = **132.7** |
| conditional asymmetry measured | 45 with the hypothesis vs 12 against → **π = 0.7895** |
| Holm-adjusted α (three-test family) | 0.05 / 3 = **0.0167** |
| **achieved power at N = 652** | **1.0000** |
| **minimum detectable effect at 80 % power** | **π = 0.6328 → 5.41 accuracy points** |
| the effect this design pre-registered | **5.0 points** |

**The minimum detectable effect is 5.41 points against a pre-registered target of 5.0 — a match to within a
point.** So the frozen `N` is sized for exactly the effect it said it cared about, and the measured effect
(11.8 points, roughly twice the target) is why achieved power reads ~1.0. **The pre-run says the target was
the conservative choice, not the optimistic one.**

### A correction made mid-analysis, recorded because it changed the answer

**The first draft of the power script reported the design as "OVER-powered, 5.11×"** — obtained by comparing
against the *measured* effect rather than against the *pre-registered target*. That comparison is wrong: a
design is sized for the effect it declares, and a larger observed effect does not make the sizing a defect.
The script now translates `π` into accuracy points, and the conclusion reverses:

> **5.41 points against a 5.0-point target is correct sizing. 5.11× is what falls out of testing the design
> against a number it never claimed to be powered for.**

**`N = 652` needs no erratum**, and the honest description of what it buys is: 80 % power at a 5.4-point
effect, with the observed effect roughly twice that.


---

## 6. All three frozen seeds, and both grid endpoints — the directions are seed-robust

2,520 records (280 dev items × λ ∈ {0, 0.05, 0.18} × seeds {0,1,2}) in **69.9 s, 0 failures**.

| λ | seed | accuracy | SilentError@0.9 | Coverage@0.9 | median `c` |
|---|---|---|---|---|---|
| 0.00 | 0/1/2 | **0.8750** | 0.0357 | 0.4321 | 0.8859 |
| 0.05 | 0 | 0.9071 | 0.0321 | 0.3929 | 0.8573 |
| 0.05 | 1 | 0.8643 | 0.0179 | 0.3821 | 0.8583 |
| 0.05 | 2 | 0.8714 | 0.0357 | 0.4107 | 0.8704 |
| 0.18 | 0 | 0.7571 | 0.0107 | 0.2179 | 0.7650 |
| 0.18 | 1 | 0.7464 | 0.0214 | 0.2107 | 0.7386 |
| 0.18 | 2 | 0.7679 | 0.0143 | 0.2179 | 0.7499 |

**Three things this adds, and one of them is a self-check that passes.**

1. **The clean condition is byte-identical across seeds** — 0.8750 / 0.0357 / 0.4321 three times. That is
   correct (`λ = 0` introduces no noise, so the seed cannot matter) and it is an internal consistency check
   on the generator and the pipeline: had the clean cell moved with the seed, the noise generator would have
   been perturbing something at λ = 0.

2. **`λ_lo = 0.05` does not degrade performance at all.** Its accuracy (0.8643–0.9071, mean 0.881) is
   statistically indistinguishable from clean (0.8750), and its seed spread is 4.3 points wide. **So `lo` is
   a genuinely unperturbed condition**, which is exactly what the calibration selected it for — the anchor
   said "readable", and the model agrees.

3. **Every direction is consistent across all three seeds.** H1.1's direction holds (λ_mid 0.746–0.768
   against clean 0.875); **H1.2's is contradicted at both noisy levels and in every seed** (0.0357 → 0.029 →
   0.015); H1.3's holds (0.432 → 0.395 → 0.215). **The H1.2 contradiction is therefore not a seed artefact**,
   which is the strongest form the finding could take before the confirmatory run.

**Confidence contamination re-checked over the full sample: 0 of 2,520 rows carry the substituted constant.**


---

## 7. The conditional formulation was proposed, then measured, then refuted by the same data

**Option (a) — restate H1.2 on `CondErr@τ` — was recommended in this document's §4 on a mechanism argument:
noise deflates confidence, so a fixed-τ silent-error rate must fall, and the quantity that should rise is the
error rate *among admitted trials*. That argument was made without measuring `CondErr`. It was then
measured, and it is wrong.**

| τ | clean `CondErr` | λ = 0.18 | difference | z |
|---|---|---|---|---|
| 0.80 | 0.0854 (51/597) | 0.0886 (31/350) | +0.0031 | **0.17** — no significant change |
| 0.90 | 0.0826 (30/363) | 0.0718 (13/181) | −0.0108 | **−0.45** — no significant change |

**`CondErr` does not rise either. It is statistically flat at both thresholds.** The reason is a selection
effect the mechanism argument missed: noise deflates confidence, so the trials that still clear τ = 0.9 are
the ones the model is most certain of, and **noise-induced errors are disproportionately NOT among them**.
Filtering the same errors by any of three formulations gives the same answer:

| formulation | clean | λ = 0.18 | direction |
|---|---|---|---|
| `SilentError@0.9` (errors admitted, per trial) | 0.0357 | 0.0107 | falls |
| `CondErr@0.9` (errors among admitted) | 0.0826 | 0.0718 | flat |
| admitted errors as a share of ALL errors | 10/35 = **0.286** | 3/68 = **0.044** | falls |

### A second obstacle, measured: `CondErr@τ` is not a paired quantity

The admitted set differs between arms — 121 items clean, 61 under noise, **intersection 51**. So the
denominator of `CondErr` changes with the condition, the within-item pairing that §4.5 relies on does not
exist for it, and **the exact paired permutation estimator does not apply**. Putting H1.2 on `CondErr` would
therefore require a different estimator *and* a direction the data does not support.

### So what does the pre-run actually support?

**Every formulation points the same way, and it is the opposite of the premise the programme was built to
test: typo noise's damage is concentrated in what the model declines to answer, not in what it confidently
gets wrong.** Accuracy falls 11.8 points and coverage halves — while the error rate among admitted trials is
flat and the share of errors that pass the gate *falls* from 0.286 to 0.044.

That is a reportable claim, and it is a falsifiable one. It is also **not a directional hypothesis in the
same form as H1.2**, so it cannot simply be substituted in:

1. **Equivalence hypothesis** — `CondErr@τ` is invariant to noise within a pre-registered margin. Supported
   by the data, but needs a margin chosen *now*, and needs the non-paired estimator above.
2. **Drop H1.2 from the confirmatory family**, report `CondErr@τ` as a co-reported descriptive quantity, and
   let Phase I's confirmatory family be H1.1 (accuracy) and H1.3 (coverage) — **both of which are per-item
   binaries and therefore genuinely paired**.
3. **Coverage-matched contrast** — hold the gate's coverage fixed across arms and ask whether the conditional
   error then rises. This is the question the mechanism argument was really about, and it cannot be answered
   by a fixed-τ design, because under noise a fixed τ *is* a more selective gate.

**Option (a) is withdrawn. It is recorded here rather than deleted because the argument for it was plausible,
it was acted on, and the measurement is what settled it — which is the sequence this whole document exists to
demonstrate.**


---

## 8. Options (c) and (d) probed on existing dev trials — one is testable, one is refuted

`scripts/probe_h12_options.py` runs nothing on the model. It reads the 2,520 dev trials already on disk
(280 items × λ ∈ {0, 0.05, 0.18} × 3 seeds) and computes what each option would actually assert. Option (a)
was recommended on argument and withdrawn on measurement; the point of probing (c) and (d) before adopting
either is not to repeat that.

### (c) Equivalence on `CondErr@τ` — TESTABLE, and the margin is not vacuous

| τ | clean `CondErr` | λ = 0.18 | difference | 90 % CI | margin on dev | **projected to the confirmatory window** |
|---|---|---|---|---|---|---|
| 0.80 | 0.0854 | 0.0886 | +0.0031 | [−0.0281, +0.0344] | 3.44 pts | **2.05 pts** |
| 0.90 | 0.0826 | 0.0718 | −0.0108 | [−0.0503, +0.0287] | 5.03 pts | **2.59 pts** |

**At the confirmatory sample size the design could declare an equivalence margin of ±2.6 points on
`CondErr@0.9`, against a clean value of 8.3 points.** A margin that is a quarter to a third of the baseline
is a substantive claim rather than a vacuous one — it would say the conditional error rate moves by less than
2.6 points, which is falsifiable and informative. **The observed difference (−1.08 points) sits inside it.**

**Cost, and it is real:** `CondErr@τ` is not a paired quantity (§7), so (c) needs its own estimator —
a two-proportion contrast or an unpaired permutation — alongside §4.5's paired permutation. The protocol
would then name two estimators rather than one.

### (d) Coverage-matched contrast — REFUTED as a directional hypothesis

Per-arm τ set to the (1−q) quantile of `c` so both arms admit the same share, then `CondErr` compared:

| q | τ clean | τ noisy | clean `CondErr` | noisy `CondErr` | difference | p |
|---|---|---|---|---|---|---|
| 0.15 | 0.9723 | 0.9339 | 0.0909 | 0.0630 | −0.0279 | 0.49 |
| 0.20 | 0.9598 | 0.9078 | 0.0877 | 0.0710 | −0.0167 | 0.69 |
| 0.25 | 0.9483 | 0.8837 | 0.0845 | 0.0664 | −0.0182 | 0.59 |
| 0.30 | 0.9377 | 0.8634 | 0.0824 | 0.0791 | −0.0033 | 1.00 |
| 0.35 | 0.9236 | 0.8453 | 0.0909 | 0.0814 | −0.0096 | 0.77 |
| 0.40 | 0.9066 | 0.8088 | 0.0796 | 0.0861 | +0.0064 | 0.78 |
| 0.45 | 0.8992 | 0.7829 | 0.0787 | 0.0976 | +0.0189 | 0.37 |
| 0.50 | 0.8853 | 0.7499 | 0.0780 | 0.0974 | +0.0194 | 0.33 |

**Noise is above clean at only 3 of 8 matched levels and nowhere significantly; below it at the other 5.**
Matching coverage does not make the conditional error rise. **(d) cannot carry a directional hypothesis.**

**And it costs more than it returns:** matching coverage requires per-arm thresholds that differ by 13.5
points of confidence at q = 0.50 (0.8853 versus 0.7499), which replaces the protocol's fixed τ ∈ {0.80, 0.90}
with a coverage target. That is a large design change for a contrast the data does not support.

### What the three probes now say together

| option | what it asserts | verdict on dev |
|---|---|---|
| (a) `CondErr` differs directionally | noise raises conditional error | **refuted** (§7, z = −0.45) |
| (d) coverage-matched, noise raises it | same claim, gate held equally selective | **refuted** (no level significant) |
| (c) `CondErr` is invariant within a margin | noise does not raise conditional error | **supported**, margin 2.59 pts at τ = 0.9 |
| (b) drop H1.2, keep H1.1 + H1.3 | — | **no claim staked on the contrast** |

**Three independent probes of the same question agree: under typo noise the model's committed answers do not
become more often wrong.** Accuracy and coverage fall; the quality of what is still committed does not. That
is a coherent, falsifiable, and reportable position — and **(c) is the only one of the three that turns it
into a pre-registered claim**, at the cost of a second estimator.

**All of this is dev, non-confirmatory, and computed without running the model. The decision is the user's.**


---

## 9. (b) versus (c), priced — and a third option that dominates both

### First, a correction to this document's own §8

§8 reported the **"smallest declarable margin"** for an equivalence claim as 2.59 pts at τ = 0.9 and treated
it as the margin the design could use. **That number is a confidence-interval statement at the observed
point; it is not a margin with 80 % power.** `scripts/probe_h12_decision.py` computes the actual TOST power
curve, and at a 2.6-pt margin the power is **0.228** — the design would fail to conclude equivalence roughly
three times in four even if the conditional error really is flat.

> **This is the same class of error as the withdrawn option (a): a plausible number used without converting
> it into the quantity the decision depends on.** It is recorded rather than silently fixed because it is the
> second time in this document that converting units reversed a conclusion.

### (c) priced honestly

| τ | margin for 80 % power | as a share of baseline | to hold 2.6 pts would need |
|---|---|---|---|
| 0.80 | **3.41 pts** | **40 %** of 8.54 | 1.8× more trials |
| 0.90 | **5.00 pts** | **60 %** of 8.26 | 6.7× more trials |

**A margin that is 60 % of the baseline it bounds is a weak claim**: at τ = 0.9 it says the conditional error
moves by less than 5 points when the baseline is 8.3, which permits the rate to almost double. (c) is
runnable, but what it would assert at usable power is thinner than §8 implied.

### (b) priced honestly, and it is not free

Holm with three hypotheses tests the smallest p against α/3 = 0.0167. **Drop H1.2 and the first threshold
becomes α/2 = 0.025 — the decision rule for the hypotheses that remain is loosened by 1.50×.** No conclusion
changes at the measured effects (both remaining contrasts are ~1.0 power), but the pre-registered threshold
is no longer the one H1.1 and H1.3 were evaluated against, and a reviewer may reasonably ask why a hypothesis
left the family.

### The third option, found while pricing (c): a directional claim that needs no margin

If noise deflates confidence generally, then "noise errors carry lower confidence" is a trivial level shift.
**It is not a level shift.** Within each arm, comparing the confidence of correct against incorrect trials:

| λ | median `c` correct | median `c` error | separation | **within-arm AUC** | share of errors the gate rejects |
|---|---|---|---|---|---|
| 0.00 | 0.8924 | 0.7930 | +0.0994 | **0.653** | 0.714 |
| 0.05 | 0.8712 | 0.6773 | +0.1939 | **0.697** | 0.760 |
| 0.18 | 0.8001 | 0.5314 | **+0.2687** | **0.773** | **0.936** |

**Correct trials' median confidence falls too (0.8924 → 0.8001) — but the errors' median falls more than
twice as far (0.7930 → 0.5314). The separation and the AUC rise monotonically, and the share of errors the
gate rejects rises from 0.714 to 0.936.**

**`H1.2′ — the confidence gate becomes MORE discriminative under noise.`** Why this dominates both (b) and (c):

1. **It is directional**, so it needs no equivalence margin and no second inferential framework.
2. **It has ample power** — the dev effect is large (AUC 0.773 on 204 error trials at λ = 0.18; median
   difference 0.262, permutation p < 1e-4) and the confirmatory window is larger.
3. **It keeps the frozen three-test family**, so no multiplicity threshold moves.
4. **It is a mechanism, not a null** — it *explains* why the conditional error is flat instead of merely
   asserting that it is.
5. **It is scale-free.** The within-arm AUC is invariant to any monotone transform of `c`, so it does not
   depend on the instrument's confidence being calibrated on an absolute scale — **which is exactly the
   fragility the library's invalid-temperature warning creates.** (c), by contrast, bounds a rate at an
   absolute τ and therefore rests on the calibration the warning questions.

**And it is the sharpest form of the critical-review claim this programme exists to make: the "silent error"
premise fails because noise-induced errors are LOUD, not silent.** Accuracy falls 11.8 points and coverage
halves, while 93.6 % of the new errors announce themselves below the gate.

**All dev, non-confirmatory, computed without running the model.**


---

## 10. H1.2' drafted and its estimator verified before pre-registration

### The estimator needs no second framework — verified, not asserted

The design is paired at the **unit level** (item × noise seed), and each unit carries one clean and one
noisy observation with its own `(confidence, correctness)`. **Under the null that noise does not change that
joint distribution, the two arm labels within a unit are exchangeable**, so the exact permutation
distribution is generated by independently swapping each unit's two observations. **H1.2' therefore reuses
§4.5's within-unit paired permutation and requires no second inferential framework** — the cost that made
option (c) unattractive does not apply to it.

`scripts/analyze_h12_auc.py`, on the dev trials:

| | |
|---|---|
| exchangeable units | **840** (280 items × 3 seeds) |
| AUC(clean) | **0.6533** (735 correct, 105 error) |
| AUC(λ = 0.18) | **0.7734** (636 correct, 204 error) |
| contrast | **+0.1201** |
| one-sided paired permutation | **p = 0.00020** (0 of 5,000 permutations at least as extreme) |
| **positive control** (noisy ERROR trials shifted down, correct untouched) | contrast **+0.2935** — **DETECTED** |
| **negative control** (random arm assignment, 20 draws) | mean **−0.0048**, range [−0.0494, +0.0626] — centred on zero |

### Two defects found in this script and fixed, both recorded because both are instructive

1. **Key collision collapsed the dataset.** Enumerating observations within a unit produced keys like
   `"0.0|0"` for every unit, so flattening left **2 observations in total** — and the script still printed a
   p-value of 0.00005 instead of failing. Fixed by putting the unit key into every observation key, and now
   guarded by an assertion that the flattened count equals `2 × units`.
2. **The positive control was inert, and it was inert in a way that looked like a pass.** It shifted the
   *entire* noisy arm by a constant — which is a monotone transform, and **a within-arm AUC is exactly
   invariant to a monotone transform**, so the control printed the observed contrast straight back. It now
   shifts **only the error trials** and reaches +0.2935. **A control that moves the wrong thing and reports
   success is worse than no control**, and the assertion that it must exceed the observed contrast now
   fails the script if it does not.

### What H1.2' would assert, in pre-registration form

**H1.2'.** The confidence gate's discriminability **increases** with typo noise. The estimand is the
within-arm AUC between correct and incorrect trials, `AUC(λ) = P(c_correct > c_error | λ)`, and the
hypothesis is `AUC(λ_mid) > AUC(0)`.

- **Estimator:** the exact within-unit paired permutation of §4.5 — no additional estimator.
- **Family:** replaces H1.2 in the frozen three-test Holm family at FWER 0.05, so **the multiplicity
  structure and therefore the thresholds H1.1 and H1.3 are judged against are unchanged.**
- **Why it is stronger than the two alternatives:** directional, so no equivalence margin and no TOST;
  scale-free, so it is invariant to any monotone miscalibration of `c` — **including exactly the
  miscalibration the library's invalid-temperature warning describes**; a mechanism rather than a null, since
  it explains why the conditional error stays flat; and its dev effect is large (AUC 0.773 on 204 error
  trials, p = 2e-4) with a larger confirmatory window.
- **What it makes the study say:** the "silent error" premise fails because **noise-induced errors are loud,
  not silent** — 93.6 % of them arrive below the gate the study was built around.

**Dev only, non-confirmatory, computed without running the model.**
