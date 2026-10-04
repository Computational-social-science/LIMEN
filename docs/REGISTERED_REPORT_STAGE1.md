# Stage 1 Registered Report — draft

**Working title.** Orthographic channels and input noise as structural disturbances in human–model
interaction: a pre-registered phased protocol.

**Target.** *Nature Human Behaviour* (Registered Report, Stage 1).
**Status.** Draft for submission. **The pilot has run and the design's sample size is now frozen**
(π_d = 0.2083 → `N_test = 652`, bank 932; `docs/PHASE_I_AMENDMENT_1.md` §A2). **No data have been
collected on the confirmatory path, and none may be** until the remaining pre-registration items are
frozen (§7). One pre-registration entry was found to be **wrong** and is corrected in Amendment 1 §A1;
the instrument pin is being completed at an immutable revision.

Governing protocol: `protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md` v1.1
(`sha256 ed34582c…`). Instrument: `docs/PHASE_I_PIN.md`. Pre-registration: `docs/PHASE_I_PREREGISTRATION.md`.
Amendments: `docs/PHASE_I_AMENDMENT_1.md`.

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
   temperature refit per (question type, option count). **The refit will NOT be applied.** The
   instrument is used **as shipped**, and the reason is not economy: the research question is about
   *this* instrument's control law, and `c` enters that law directly. Passing `p` through a map fitted
   on our own dev data would measure the control law of **a different instrument** -- one we built --
   and would swap the object of study mid-protocol. **So the shipped over-confidence is reported as
   the instrument's real property**, with the vendor's own figures quoted as the vendor's. See
   `docs/INSTRUMENT_POSTURE.md`.
2. **Its `noul` primitive is reported to sometimes follow its option labels rather than the state.** The
   card documents a workaround (ask the same question as a two-option `choice` with neutral keys). Since
   Phase I uses `noul` for two of its three questions, the choice between direct `noul` and the
   workaround is decided on dev by measurement and frozen in the amendment — because **changing the
   primitive changes what is measured**.

**The pin is COMPLETE and verified.** At immutable revision
**`55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`** — the revision the `laya` package pins, not the
branch — with **per-file sha256 for all 5 files** recorded in `config/pin_laya.json` (846.20 MB;
`model.safetensors` = `891102d372688fc2…`). `measurement/smoke_predict.py` was then run **on CUDA at
that revision** and returned per-option probabilities for three hand-written items with
`state_tokens_dropped: 0` and `truncated: false`. **The pin is therefore verified by execution, not
merely by hash.**

**Three facts about the revision that a reader needs:**

1. **The revision carries three variants** — `model.safetensors` (root), `multilingual/`, and
   `typed-decisions/`. The **root** is what is pinned; saying "Laya" without naming the variant would
   be ambiguous.
2. **Hub `main` had drifted** to `7b928d82…` (2026-10-03). It is **not** the pin and no runner follows
   it. The root weights happen to be byte-identical across the two (`891102d372688fc2…`); the
   surrounding files differ. The drift is recorded rather than ignored, because a pin that silently
   tracks a branch is not a pin.
3. **The shipped temperature map contains exactly one out-of-range entry** — `choice:11+` = `0.1006`,
   below the package's `[0.5, 5]` floor, which the package clamps to `0.5` while warning *"Treat
   confidence from the affected entries as uncalibrated."* **Phase I's bank uses 2–4 options, so the
   entries it exercises are `choice:2` (1.906) and `choice:3-5` (1.760), both in range — the invalid
   entry is not reachable by this design.** But the warning fires at load for the whole map, so it
   appears in every run log and **must not be read as a defect in our runs**.

**On the temperature map, restated because the above sharpens it -- and corrected.** Fact 3 does not
schedule a repair. The out-of-range entry (`choice:11+`) is **unreachable at 2-4 options**, so it
cannot touch a Phase I number, and the map is **left exactly as shipped**. An earlier version of this
section called a dev-fitted refit **mandatory**; that was the wrong posture and is withdrawn. A refit
would substitute a different instrument and measure that instead. The shipped properties are
**disclosed as limitations**, not removed -- `docs/INSTRUMENT_POSTURE.md`.

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

## 5. Threats to validity, named before the run — and what the pilot already did to them

The pilot has run (`docs/PILOT_MEASUREMENT.md`; 120 items × 3 λ × 1 seed = 360 trials, 0 failures).
It therefore **converts three of these threats from contingencies into measurements**, and it
**materialised one of them against us.** Both are reported, because a Stage 1 that predicts only
threats it survived is not a Stage 1.

| Threat | Pilot outcome | What is done about it |
|---|---|---|
| **Low clean accuracy on the pinned checkpoint** | **NOT MATERIALISED — the opposite did.** Clean accuracy on `intent` was **0.8667** (104/120, CI [0.794, 0.916]) against a chance floor of 0.3611. The concern was near-chance performance; the measurement is high above it. | The bank is not swapped and the checkpoint is **not** changed after seeing results. But see §5.1: **high** accuracy raises the opposite problem, and that is now the live threat. |
| **CONSTRUCT VALIDITY — the accuracy is too high to be the intended task** ⚠️ | **MATERIALISED.** 0.8667 stands against the model card's claimed **0.362** for this checkpoint — a 24-point gap — and *exceeds* the card's fine-tuned figure (0.766). The likeliest cause is that the protocol's own §3.1 `criteria` field names each option's decision rule, making the intent task easy. | Recorded as a **measured** finding, not a contingency. Decision on retaining `criteria` is **open** and is the programme owner's (Amendment 1 §A4); it **must be settled before the confirmatory run**, because it determines what the headline endpoint measures. |
| **Gold-label subjectivity** | **PARTIAL.** Ambiguity-as-rejection was applied (12 items rejected, ~9 %, reported). But gold was **agent-assigned with no human pass** — a departure from this table's stated standard. | Disclosed, not smoothed. A human pass or a consistency audit is now a **required** step, not a mitigation. Inter-annotator agreement cannot be reported until it exists. |
| **Construction bias in a newly built bank** | The bank's counts per domain, per option-count and per split are published. | Adjudication codebook written before labelling; option count varies so chance accuracy is not constant; structure published. |
| **Instrument miscalibration** | Partially exercised: the raw (unrefit) distribution was used, and clean `SilentError@0.9` came out **0.0000**. | **No refit is applied** (`docs/INSTRUMENT_POSTURE.md`). The shipped `c` is the instrument's real behaviour, which is what the claim is about. The shipped over-confidence is reported as a disclosed property; the vendor's after-refit ECE is quoted as the vendor's figure, not adopted as ours. |
| **Primitive substitution** | Not yet decided on dev -- and this one is measurement validity, not tuning: if `noul` follows its labels the numbers are void. | Decided on dev, frozen in the amendment, **disclosed as a deviation from the protocol's literal wire format** if taken. |
| **Contamination of the fine-tune's domain** | Not applicable to the root checkpoint, which is what was pinned. | This is why the **root** checkpoint is pinned, not `laya-typed-decisions` — and the revision `7b928d82…` contains **three** variants, so the pin names the root explicitly rather than saying "Laya" (`docs/PHASE_I_PIN.md`). |
| **Inference-unit inflation** | Pilot MDE at N = 120 was **11.67 pp**, and the observed 8.33-pp drop was **not** significant. The pilot is therefore reported as a **non**-finding. | Item-level inference with item random intercepts; N now frozen at 652 for a 5-pp δ (Amendment 1 §A2). |
| **Phase creep** | — | Phase II files its own pre-registration only after Phase I instruments are frozen; Phase I is never re-opened afterwards. |

### 5.1 The threat the pilot created: the task may be easier than the claim requires

The pilot's clean accuracy of 0.8667 is **good for power and bad for construct clarity**. Two designs
produce it, and they are not equivalent:

- **The model is resolving the intent from the state**, in which case the endpoint measures what the
  claim is about, and noise perturbs that resolution;
- **The model is reading the decision rule off the `criteria` field**, in which case the endpoint
  measures rule-matching, and noise on the state may barely touch it — in which case a null result
  would be uninformative about the thesis rather than evidence against it.

**These are distinguishable**, and the distinction is a design choice rather than a post-hoc analysis:
weakening `criteria` to option names only raises difficulty and separates the two. The cost is that it
**invalidates the N frozen in Amendment 1 §A2** and requires a re-pilot. That trade — one re-pilot
against a confirmatory run whose headline endpoint may measure the wrong thing — is stated here because
a reviewer is entitled to see that we identified it before running, not after.

## 6. Analysis plan (frozen)

Paired / mixed models with **item random intercepts**; factor λ. McNemar on paired item outcomes for
the binary endpoints. Bootstrap CIs on the SilentError and Coverage contrasts. **Holm** across the
H1.1–H1.3 family, defined here and not later. The item is the unit of inference throughout.

## 7. What is not yet fixed, and how it will be

**O2 is RESOLVED.** The pilot measured **π_d = 0.2083** (25/120, Wilson 95 % CI [0.145, 0.289]), and
the pre-registration's **own** McNemar formula — independently re-implemented and checked against the
table already printed in that document, which it reproduces exactly — gives:

> **`N_test = 652` items · item bank = `932` items** (30 % dev / 70 % test, split by `item_id`) ·
> δ = 5 absolute pp · α = 0.05 two-sided · power 0.80.
> Self-consistency: the MDE at N = 652 is **5.01 pp**, the δ the design was built around.

Derivation, the zero-floor handling of `SilentError@0.9`, and the withdrawal of an earlier concern
about that endpoint are in `docs/PHASE_I_AMENDMENT_1.md` §A2–§A3.

**The remaining items** are still held to the same rule: **nothing pending may be guessed later and
called pre-registered.** Each is frozen by an amendment filed *before* the confirmatory run, naming the
measurement that set it.

| | Pending item | What fixes it | State |
|---|---|---|---|
| **O1** | λ_lo and λ_mid | A readability calibration: items must remain human-readable at lo and be stressed at mid (indicative bands 5–8 % and 12–18 % character corruption). **The calibration must state who reads and what counts as readable before the ladder is scored**, or it is post-hoc. | **OPEN** |
| **O3** | The confirmatory item bank | Built to the frozen spec; **size now bound at 932 by O2**. Four design approvals outstanding (`docs/ITEM_BANK_SPEC.md`): domain scope, option counts, bank size, gold labeller. | **OPEN** |
| **A4(3)** | Whether `criteria` is weakened | Programme owner's decision (Amendment 1 §A4). Weakening **invalidates the N above** and forces a re-pilot. | **OPEN — blocks the seal** |
| **S12-4** | The instrument pin | Revision hash + per-file sha256 recorded at immutable revision `7b928d82…`; the **root** variant named explicitly, since the revision contains three. | **IN PROGRESS** |
| **C2** | the `noul` primitive | The decision between direct `noul` and the two-option `choice` workaround, on dev evidence. **Measurement validity, not instrument tuning.** (C1, the temperature refit, is **dropped** -- `docs/INSTRUMENT_POSTURE.md`.) | **OPEN** |

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
