# Stage 1 Registered Report — draft

**Working title.** Orthographic channels and input noise as structural disturbances in human–model
interaction: a pre-registered phased protocol.

**Target.** *Nature Human Behaviour* (Registered Report, Stage 1).
**Status.** Draft. Nine of twelve pre-registration items are fixed; three are pending a measurement
(see §7). **No data have been collected on the confirmatory path.**

Governing protocol: `protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md` v1.1
(`sha256 ed34582c…`). Instrument: `docs/PHASE_I_PIN.md`. Pre-registration: `docs/PHASE_I_PREREGISTRATION.md`.

---

## 1. The claim under test, and what would falsify it

The programme's thesis is that human–model language interaction is a **structurally biased coupled
control system** in which writing systems and input noise are **normal disturbances, not exceptions**.

Stage 1 tests one restricted, falsifiable consequence of that thesis. Under English orthography only:

> **H1.** Keyboard-faithful typo noise is a material disturbance of a typed-decision model's
> understanding **and its control law** — not merely a nuisance for text generation.

Three pre-registered endpoints, on a locked test split, with Holm correction across the family:

| | Endpoint | Direction tested |
|---|---|---|
| **H1.1** | accuracy against noise intensity λ | `Acc(λ_mid) < Acc(0)` |
| **H1.2** | `SilentError@0.9` — wrong **and** confident | `SilentError@0.9(λ_mid) > SilentError@0.9(0)` |
| **H1.3** | `Coverage@0.05` under a dev-fitted gate | `Coverage(λ_mid) < Coverage(0)` |

**Co-primaries are H1.2 and H1.3.** H1.1 is reported but is not a confirmatory endpoint on its own.
The reason is substantive: an accuracy drop is compatible with a *healthy* system. A system whose
accuracy falls while its errors stay unconfident has degraded gracefully, which is what a working
control law is for. The claim is about the control law, so the control-law endpoints carry the claim.
This choice is pre-registered, not derived from any result.

**The interpretation boundaries are fixed in advance** (protocol §4.4), and the two non-trivial
outcomes are both results:

- **H1.1 and H1.2 both supported** → noise is a material disturbance of understanding **and** control.
- **H1.1 supported, H1.2 not supported** → errors rise but confidence tracks them; **the control law is
  partially intact.** This is not a failed study; it is the more interesting of the two outcomes for
  any system that gates on confidence. *(Mechanistic support, found 2026-10-04: arXiv:2609.35475,
  "Spontaneous Context Restoration" — models sometimes recover from corrupted inputs, which is one way
  this branch arises.)*

**⚠️ Pre-emption notice — mandatory before submission.** A mechanism-level search of the 2026 arXiv
frontier (`docs/GAP_VERDICT.md`) found that **both mechanisms this protocol relies on are already
published**: the "confidently wrong bypasses abstention" motivation (arXiv:2608.09768) and the
"gating magnifies disparity across groups" result (arXiv:2010.14134, Jones et al. 2020). The channel
space is likewise occupied (arXiv:2602.11174 "The Script Tax"; arXiv:2606.20770 "orthographic bias").

**Consequently H1.1 is demoted in the text, and the contribution this report leads with is the
two-factor interaction** — whether added noise changes the *channel ordering* of coverage, rather than
merely lowering every channel. `SilentError@τ` and `Coverage@ε` are presented as **inherited
instrumentation, cited and re-measured**, never as novelties. See `docs/GAP_VERDICT.md` for the quote
behind each pre-emption and for the narrowed claim that survives.

## 2. Why this design and not an easier one

**Within-item, across λ.** Every item appears at λ = 0, lo and mid. Between-item comparison would
confound item difficulty with noise intensity; the within-item design makes each item its own control.
This is also what makes the correct test **McNemar** rather than a two-proportion comparison, and it is
why the required N depends on the discordance rate rather than on accuracy alone.

**Three item-level constants.** The same `item_id` sits in the same split at every λ and every seed
(pre-registration item 8). A split that moved items between conditions would break the pairing that
the whole design rests on.

**The gate is pre-registered, and fitted only on dev.** `τ ∈ {0.80, 0.90}` is fixed; the coverage
endpoint uses `τ*` fitted on dev at ε = 0.05. Fitting on dev and reporting on a locked test is what
stops the coverage number from being a description of the fitting set.

**The item is the unit of inference.** The design will generate many model decisions, but they are not
independent observations: they come from a bounded set of items. Reporting response-level uncertainty
over a small item set is the classic route to a false positive in this design class, and the analysis
plan forecloses it by inference at the item level with item random intercepts.

## 3. Instrument

The JEV link is **instrumentation, not an object of study**. It was selected on the programme owner's
criterion — the best option in the current ecosystem that is free of academic controversy and openly
accessible — and is used as a toolbox (`docs/JEV_TOOLBOX_SELECTION.md`).

**Pinned:** `convaiinnovations/laya`, the English root checkpoint; Apache-2.0; ModernBERT-large; 421M
parameters; non-autoregressive; `choice` / `noul` / `score` primitives, with per-option criteria.
Local inference only; no API on the confirmatory path.

**Two facts about this instrument are load-bearing and are disclosed here rather than buried:**

1. **It ships over-confident.** Its own model card reports a mean ECE of 0.466 falling to 0.081 after a
   temperature refit per (question type, option count). **The refit is part of setting up the
   instrument, not part of the test:** it is fitted on dev, frozen before the confirmatory run, and its
   data is excluded from the test set. The protocol's confidence *rule* (`c = max_j p_j` for choice;
   `c = max(p, 1-p)` for noul) is unchanged. Without this step the `SilentError@τ` estimate would be an
   artefact of the model's optimism rather than a property of its control behaviour.
2. **Its `noul` primitive is reported to sometimes follow its option labels rather than the state.** The
   card documents a workaround (ask the same question as a two-option `choice` with neutral keys). Since
   Phase I uses `noul` for two of its three questions, the choice between direct `noul` and the
   workaround is decided on dev by measurement and frozen in the amendment — because **changing the
   primitive changes what is measured**.

**The pin is not yet complete.** The revision hash and per-file sha256 are not recorded, so
pre-registration item 4 is unsatisfied and no confirmatory run may start. This is stated as a defect of
the current state, not as a plan.

## 4. Materials

**Item bank.** Short English service / routing requests across four domains (billing, access, urgency,
info), each carrying a frozen three-question set: `intent` (`choice`, 2–4 caller-defined options with
per-option criteria), `ok` (`noul`), `escalate` (`noul`). **Gold labels are locked before any model
sees an item** — a model's answer never informs a label, because that would invert the measurement.

**Noise process.** Deterministic in `(item_id, λ, seed)`, restricted to the four pre-registered edit
classes: QWERTY-adjacent substitution, transposition, deletion, insertion. λ is a target mean edit rate.
**Adversarial misspellings, OCR, ASR, full-word substitution and cross-lingual material are out of
scope** (protocol §4.2).

**Provenance of the bank.** It is built for this programme. No item is drawn from, or paraphrased from,
any earlier corpus, and no item is generated by the pinned model itself — the latter would make the
model both question-setter and answerer.

## 5. Threats to validity, named before the run

| Threat | Why it matters | What is done about it |
|---|---|---|
| **Low clean accuracy on the pinned checkpoint** | The root checkpoint is reported at 0.362 zero-shot on typed decisions while its fine-tune reaches 0.766. If clean accuracy is near chance, a 5-point drop may be undetectable and the study underpowered. | Measured in the pilot, **before** the amendment fixes N. If accuracy is too low, that is **reported as a limitation of the pin** — the checkpoint is **not** swapped mid-phase, because swapping after seeing results would invalidate the pre-registration. |
| **Gold-label subjectivity** | An item whose correct answer is arguable measures the annotator, not the model. | Ambiguity is a **rejection**, not a tiebreak; the rejection rate is reported. Inter-annotator agreement is published with the bank. Labels are locked before any model runs. |
| **Construction bias in a newly built bank** | A bank built for this hypothesis could favour it. | An adjudication codebook is written before labelling (spec §4); item structure varies option count so chance accuracy is not constant; the bank's own record publishes counts per domain, per option-count and per split. |
| **Instrument miscalibration** | `SilentError@τ` lives or dies on whether `c` is meaningful. | The temperature refit (§3) is done on dev and frozen; the raw and refitted distributions are both reported so a reader can see the effect. |
| **Primitive substitution** | Replacing `noul` with a two-option `choice` measures a different task. | Decided on dev, frozen in the amendment, and **disclosed as a deviation from the protocol's literal wire format** if taken. |
| **Contamination of the fine-tune's domain** | If the pinned checkpoint had been fine-tuned on workflows resembling the bank, a high score would measure memorisation. | This is why the **root** checkpoint is pinned, not `laya-typed-decisions` (`docs/PHASE_I_PIN.md`). |
| **Inference-unit inflation** | Many decisions over few items manufacture significance. | Item-level inference with item random intercepts; the analysis plan fixes the unit before data collection. |
| **Phase creep** | Reporting a cross-script claim from English evidence is the failure mode this programme exists to avoid. | Phase II files its own pre-registration only after Phase I instruments are frozen; Phase I is never re-opened afterwards. |

## 6. Analysis plan (frozen)

Paired / mixed models with **item random intercepts**; factor λ. McNemar on paired item outcomes for
the binary endpoints. Bootstrap CIs on the SilentError and Coverage contrasts. **Holm** across the
H1.1–H1.3 family, defined here and not later. The item is the unit of inference throughout.

## 7. What is not yet fixed, and how it will be

Three pre-registration items remain **PENDING** because the protocol's own sequencing requires a
measurement first. **Nothing pending may be guessed later and called pre-registered**; each is frozen
by an amendment filed *before* the confirmatory run, naming the measurement that set it.

| | Pending item | What fixes it |
|---|---|---|
| **O1** | λ_lo and λ_mid | A readability calibration: items must remain human-readable at lo and be stressed at mid (indicative bands 5–8% and 12–18% character corruption). |
| **O2** | N | A pilot measuring the **discordance rate** π_d and the **clean `SilentError@0.9`** baseline. Analytic requirement at 80% power, δ = 0.05, McNemar: **N = 186–626** across π_d = 0.06–0.20, rising to **775** for a low baseline SilentError. |
| **O3** | The confirmatory item bank | Built to the frozen spec; size set by O2. |

## 8. Scale of work, and why a single consumer GPU suffices

Phase I **freezes θ and trains nothing** (confirmatory fine-tuning is an explicit non-goal). The work
is: build the bank, generate the perturbed conditions, run one forward pass per (item, condition, seed),
and analyse. The pinned model is a 421M encoder; on a single RTX 4070 (12 GB) it runs in milliseconds
per decision. **This is what makes the required design feasible at home:** a within-item × λ × seed
design at the N that power demands would be an expensive proposition with text generation, and is a
routine one with a typed-decision head. The GPU's role is throughput on a frozen instrument, not
training.

## 9. Open science

Two pre-registrations (Phase I; Phase II after the Phase I freeze). Release the typo generator, the
item bank (or controlled access), the JSONL schema and the analysis code. All confirmatory model
revisions pinned. Negative results published in full, with the failure record intact.

## 10. What this Stage 1 does not claim

It does not claim a cross-script result, a writing-system fairness result, or anything about universal
noise intensity across languages — all of those are reserved for Phase II and forbidden from Phase I
evidence. It does not claim that typo noise is the *largest* disturbance, only that it is a
first-class one. And it claims nothing from the instrument's vendor-reported numbers, which are quoted
here only to justify instrument setup.
