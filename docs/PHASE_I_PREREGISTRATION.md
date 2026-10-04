# Phase I — Pre-Registration (draft for staged filing)

**This document is the Phase I pre-registration required by the protocol's §12 checklist. It is not
complete, and it says so item by item: some entries are **FIXED NOW** and some are **PENDING** because
the protocol's own sequencing requires a measurement first. Nothing marked PENDING may be guessed
later and called pre-registered; it must be frozen by an amendment filed **before** the confirmatory
run, with the measurement that set it named.**

Governing document: `protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md` v1.1
(`sha256 ed34582c…`). Where this file and the protocol disagree, the protocol wins.

---

## §12 checklist, item by item

| # | Protocol requirement | Status | Entry |
|---|---|---|---|
| 1 | English only; no script factor in confirmatory tests | **FIXED NOW** | `s = s_en` for every confirmatory cell. No script factor exists in Phase I. No cross-script claim may be made from Phase I evidence (§7, §8). |
| 2 | Typo classes and λ rates fixed | **PARTLY FIXED** | Classes FIXED: adjacent-key substitution (QWERTY), character transposition, deletion, insertion. Rates **PENDING** the §4.2 readability calibration (see "Open items"). |
| 3 | Generator seed policy | **FIXED NOW** | The generator is a pure function of `(item_id, λ, seed)`. Seeds are integers. The confirmatory run uses `noise_seed ∈ {0,1,2}` per item and λ; every `(item_id, λ, seed)` triple appears exactly once. The seed list is frozen with the item bank. |
| 4 | Model ID + commit + SHA256 | **FIXED NOW** | `E:/2026-AI4S/calib/rsi_jev_v1_0_08b`; tower sha256 `60f8ea11…cff67`, scorer sha256 `22cb924e…11a06`, directory manifest sha256 `f9dcc09b…b6675d2`. Full record: `docs/PHASE_I_PIN.md`. |
| 5 | Q₀ frozen (`intent`, `ok`, `escalate`) | **FIXED NOW** | The three questions of §3.1 are frozen verbatim in the item bank. `intent` is `choice` with per-item `criteria`; `ok` and `escalate` are `noul`. The primary endpoint question is `intent`. |
| 6 | Confidence rule frozen | **FIXED NOW** | choice: `c = max_j p_j`; noul: `c = max(p, 1-p)`. No alternative functional is computed, reported, or substituted. |
| 7 | τ ∈ {0.80, 0.90}; ε = 0.05 | **FIXED NOW** | Both τ values are reported everywhere. `Coverage@0.05` uses `τ*` fitted on **dev only** — never on test, never refitted after seeing test. |
| 8 | Dev/test split by item | **FIXED NOW** | Split by `item_id`, never by trial: 30% dev / 70% test. Every λ and every seed for a given `item_id` falls in the same side. The split is frozen with the item bank and its id list is recorded. |
| 9 | Primary endpoints H1.1–H1.3 | **FIXED NOW** | As §4.4. Co-primaries are **H1.2** (`SilentError@0.9` rises) and **H1.3** (coverage falls **or** accepted-error rises — the protocol requires this be pre-registered, so it is: **coverage falls** is the co-primary form; accepted-error rise is reported as a secondary in the same direction). H1.1 is reported but is **not** a confirmatory endpoint on its own. |
| 10 | FAILURES policy | **FIXED NOW** | Every attempted trial is appended to the record with its outcome, including the ones that fail and the ones that are excluded. Exclusions require a stated mechanical reason (malformed item, generator error, state hash mismatch) and are counted. No silent row deletion. A run that fails a hypothesis ships the full record. |
| 11 | No confirmatory training | **FIXED NOW** | θ is frozen. No fine-tuning, no QLoRA, no adapter, no prompt-fitting on the confirmatory path. If any parameter updates, the artefact is no longer the pinned one and the run is void. |
| 12 | Cross-script claims reserved for Phase II | **FIXED NOW** | Stated in the manuscript, the README, and `CURRENT_OBJECT.md`. Phase II files its own pre-registration only after Phase I instruments are frozen, and Phase I is not re-opened afterwards (§0.2, §5.1). |

---

## Open items — must be resolved by a pre-run amendment

These are the protocol's own sequencing requirements, not gaps in this draft.

### O1 — λ levels (§4.2): requires a readability calibration

The protocol fixes λ_lo / λ_mid **after** a short calibration, with a stated criterion: items remain
**human-readable at lo** and are **stressed at mid**. The indicative bands are ~5–8% and ~12–18%
character corruption.

**Procedure.** Generate a candidate ladder (e.g. 3%, 5%, 8%, 12%, 18%, 25%); score a small sample of
items for readability; select the two levels that bracket the criterion. Record the chosen rates and
the readability evidence. **This is calibration of an instrument, not a test of a hypothesis, so it
runs before the pre-registration is sealed and its data is excluded from the confirmatory test set.**

### O2 — N_item (§4.3): requires the discordance rate π_d

The protocol sets N by power for detecting (a) a **≥5 absolute-point** mid-vs-clean error increase and
(b) a `SilentError@0.9` increase, at **80% power**. The design is **paired** — the same items appear
under λ=0, lo, mid — so the correct test is **McNemar**, and its required N depends on the
**discordance rate** π_d (the share of items that flip), which is **not yet measured**.

Analytic requirement, two-sided α = 0.05, power = 0.80, δ = 0.05:

| π_d | N required (McNemar) |
|---|---|
| 0.06 | 186 |
| 0.08 | 249 |
| 0.10 | 312 |
| 0.12 | 375 |
| 0.15 | 469 |
| 0.20 | 626 |

For the `SilentError@0.9` endpoint the requirement rises as the clean baseline falls:

| clean SilentError@0.9 | N required |
|---|---|
| 0.02 | 266 |
| 0.05 | 432 |
| 0.08 | 587 |
| 0.12 | 775 |

**Procedure.** Run a pilot on the pinned artefact over a small item sample, measure **π_d** and the
**clean-baseline `SilentError@0.9`**, then set N as the **maximum** of the two requirements, with the
30% dev share on top. State the measured inputs and the resulting N in the sealed pre-registration.
**Pilot data is excluded from the confirmatory test set.**

**A conservative fallback if the pilot is not run:** the unpaired two-proportion bound gives 903–1,562
per group across clean-accuracy 0.45–0.85. N at that scale is safe but costs precision on effect size;
the pilot is the cheaper path and is the protocol's intent.

### O3 — the item bank (§4.3): must be built, and it is new

Domain: **short service / routing intents** — billing, access, urgency, info — with **locked English
gold labels for `intent`**. Nothing on this machine supplies this bank: the RSI-Jev distillation corpus
that earlier work used is a different domain with a different question-type mix, and it is archived
with the retired object rather than reused here.

**Requirements.** ≥ 4 items per condition cell; parallel structure across λ; gold frozen before the
run; the split (O-split) frozen with it. Item construction bias is named as a Phase I limitation (§10)
and mitigated by an adjudication codebook.

---

## Analysis plan (frozen now)

- **Models.** Paired / mixed models with **item random intercepts**; factor λ. For the binary endpoints,
  McNemar on paired item outcomes, with the item as the unit.
- **Intervals.** Bootstrap CIs on the SilentError and Coverage contrasts.
- **Multiplicity.** Holm across the H1.1–H1.3 family, with the family defined here and not later.
- **Unit of inference.** The **item**, throughout. A trial count does not create power; the item count
  does. This is stated because a large response count over few items is the classic false-positive
  route in this design class.

## Interpretation boundaries (frozen now)

Fixed by the protocol §4.4, restated here so the result cannot be narrated into more than it is:

- **H1.1 supported, H1.2 supported** → typo noise is a material disturbance of understanding **and**
  control.
- **H1.1 supported, H1.2 not** → errors rise but confidence tracks; the control law is partially
  healthy. This is a **result**, not a failure.
- **Nothing may be concluded about writing systems from Phase I.**

## Deliverables (§4.6)

Frozen set: item bank · `N_en` generator · model pin (this document's §12 item 4) · trial JSONL in the
§3.5 schema · analysis notebook · FAILURES log · short report.
