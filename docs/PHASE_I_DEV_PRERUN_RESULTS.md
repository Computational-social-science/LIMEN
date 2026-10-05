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
