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
