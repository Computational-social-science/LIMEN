# CURRENT OBJECT

**This file records what the programme is working on, what it has retired, and what state it is in.**
It is subordinate to the **global anchor** —
`protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md` — which holds the objective itself
(§0–§1 there is the only answer to "what are we working on?"). Where this file disagrees with that
protocol **about the objective**, the protocol wins. Where this file disagrees with **another
document about a fact** — what exists, what is pinned, what is blocked — this file wins, because its
claims are checked against the repository by `scripts/check_anchor.py`.

---

## The live object

**Orthographic Channels and Input Noise as Structural Disturbances in Human–Model Interaction** —
a pre-registered, phased protocol, version 1.1, integrating System One / JEV-ecosystem tooling.

The protocol in full: `protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md`.

> **Thesis.** Human–model language interaction is a structurally biased coupled control system;
> writing systems and input noise are normal disturbances, not exceptions. System One tooling makes
> the control law — confidence-gated action — directly observable and programmable.

**Staging.** The programme is deliberately phased, and the phasing is methodological rather than
convenient: noise processes, gold labels and power calculations are channel-specific, so a
cross-script claim cannot be earned from English evidence.

| Phase | Channel | Noise | Confirmatory claim |
|---|---|---|---|
| **I (anchor)** | English, standard Latin orthography only | English keyboard-faithful typos | Noise is a normal operating disturbance for the control metrics (error, SilentError, coverage) |
| **II (extension)** | + ≥1 non-English or non-Latin channel | Script-faithful noise — never Latin rules copied | Script × noise interaction; cross-channel allocational disparity |

**Phase II pre-registration is filed only after Phase I instruments are frozen.** Phase I is never
re-opened to hunt interactions after Phase II results are seen.

**Phase I needs no training.** The confirmatory arms freeze θ. Confirmatory fine-tuning and QLoRA are
explicit non-goals of the protocol (§8). This matters for what may live in this repository — see the
retirements below.

**Primary dependent variables.** `Acc(λ)`, `SilentError@τ(λ)` — wrong *and* confident — and
`Coverage@ε(λ)` — share of items answered while holding accepted-item error at ≤ ε. Plain accuracy is
not the endpoint; the control law is.

**Theoretical frame (2026-10-04).** Shannon's noisy-channel coding theorem plus the cybernetics
classics (Ashby's requisite variety; Conant & Ashby's good-regulator theorem; Wiener) are the
programme's foundational reference frame — **and it is load-bearing, not decorative.** Under it the gate
`g_τ` is a code, `Coverage@ε` is the rate, `SilentError@τ` is the residual error, and the programme's
surviving claim becomes a **geometric one: do the channels' rate–error curves shift in parallel under
noise, or do they cross?** Mapping, four concrete changes, and five explicit refusals:
`docs/THEORETICAL_FOUNDATIONS.md`. **The frame supplies no empirical content** — nothing about an LLM's
typo behaviour follows from a theorem about the existence of codes, and "capacity" may only be used as
"effective capacity estimated from the observed rate–error curve".

---

## Retired — do not work on these

Two objects dominated this repository before the current object was fixed. Both are retired. Their
artefacts are preserved under `archive/` and remain readable as records; neither is a target.

### R1 — The JevRSI loop objective (retired 2026-10-04)

*"Reproduce the RSI-Jev self-improvement loop on a Qwen3-0.6B backbone; the deliverable is the curve."*

**Why retired.** The NHB protocol's confirmatory arms require a **frozen** θ and name confirmatory
fine-tuning as a non-goal. A self-improvement loop trains the model; it is therefore not the
instrument this programme uses, and a curve of loop gain is not one of its estimands. The question
the loop was built to answer — whether the loop or the backbone limits curve length — is a real
question, but it is a different question from the one this repository is now asking, and running both
would leave neither properly pre-registered.

**Also load-bearing in the decision:** the loop's only completed arm was quarantined as evidence on
2026-10-04 for four independent reasons (instrument never calibrated at the time, irreproducible
because it had no resume path, a single seed against a three-seed gate, and a training regime at 96%
VRAM), and the per-arm cost was never reconciled with the source's record. The loop's cost profile
was never established on this hardware.

**Retired artefacts.** `archive/R1_jevrsi_loop_objective_2026-10-04/` — the arm-0 dossier (spec,
acceptance gate, host feasibility, probe evidence, timing correction, eval-batch correction), the
arm-0 evidence set (launch record, audit, probe records, result, cost ledger), the reproduction and
pipeline audits, the approach re-distillation, the v1.0 environment builder, the edit guard and its
checker, the arm-0 spec checker and quarantine script, the health dashboard, its exporter, its
auditor, and the dashboard's state export. Hash manifest in that directory.

**What is deliberately NOT retired with it.** Several files in this repository were built *for* the
loop but are **instruments** the current object needs, and they stay live — see "Live instruments"
below. A file is retired with R1 only if its content is about the loop, the arm, or the curve.

### R2 — The RTX 4070 harness-first self-evolving proposal (retired 2026-10-04)

*"A 24/7 local multi-fidelity controller evolving harness modules around a frozen AgentJev-0.6B, with
a six-week held-out success criterion."*

**Why retired.** It is a different object from the current one: its deliverable is an evolved
configuration and a progress curve, its seed is a named checkpoint from a retired ecosystem, and its
harness-first posture is a route rather than a question. It was never adopted here; it arrived as
unvalidated generated text.

**Provenance, stated plainly.** Both of the generated documents that arrived on 2026-10-04 were
produced by a language model in an app-builder workspace, carry no run, no data and no measurement
behind any number in them, and use vocabulary this programme had already retired (`AgentJev-0.6B`,
harness-first, AnyJev levels, a Laya root). They are inputs that were filtered, not sources. The
material is preserved outside this repository at
`E:/2026-AI4S/proposals_2026-10-04/` with a provenance note; the app-builder scaffolding that carried
it was removed from this repository's tree.

---

## Live instruments — verified to exist, 2026-10-04

**This table is a claim that can be checked, so it is checked.** Every path below was verified to
exist at the repository root on 2026-10-04. A path that fails verification is removed from this table
and recorded in `docs/INSTRUMENT_LEDGER.md`.

| Path | Role under the current object | Verified |
|---|---|---|
| `measurement/typo_noise.py` | The Phase I noise process `N_en`: four edit classes, a pure function of `(item_id, λ, seed)`. | ✓ |
| `measurement/run_phase1.py` | The confirmatory `predict → JSONL` runner (§3.5 schema), resumable, failures recorded not dropped. | ✓ |
| `measurement/smoke_predict.py` | The minimal end-to-end check that the pinned checkpoint runs locally and returns per-option probabilities. | ✓ |
| `measurement/c2_noul_validity.py` | The `noul` primitive's measurement-validity check. | ✓ |
| `measurement/item_bank.jsonl` + `item_bank_manifest.json` | The confirmatory item bank, gold as a construction invariant, with its counts. | ✓ |
| `measurement/pilot_items.jsonl`, `pilot_results.json` | The 120-item pilot and its 360-trial record; the measurement that set O2. | ✓ |
| `measurement/trials_pilot_replay.jsonl` | The 1080-row independent replay; the measurement that exposed the π_d definition error. | ✓ |
| `scripts/build_item_bank.py` | The deterministic bank builder (O3, option C). | ✓ |
| `scripts/check_object_drift.py` | The mechanical contamination guard. **Known to be incomplete — see its audit.** | ✓ |
| `config/pin_laya.json` | The instrument pin: revision plus per-file sha256. | ✓ |
| `config/pin.json` | The earlier pin record, superseded in substance by `pin_laya.json`. | ✓ |

### Removed from this table on 2026-10-04 — they were listed as "kept" and were not

**An earlier version of this section listed nine paths under the heading "Live instruments — kept, and
why", and asserted that "the current object needs them".** On verification, **all nine did not exist**
at the repository root; every one of them is under
`archive/R1_jevrsi_loop_objective_2026-10-04/`:

`paths.py` · `config/paths.json` · `scripts/calibrate_against_release.py` ·
`measurement/report_from_items.py` · `measurement/build_synth_split.py` · `scripts/health.py` ·
`scripts/run_with_heartbeat.py` · `TOOLS.md` · `docs/BOOTLOOPS.md`

**This is recorded rather than quietly corrected, because it is the more informative defect.** The R1
archival moved the files and left the authority document promising them — a promise the repository
could not keep and nobody checked. **The lesson is a missing mechanical check, not a missing sentence:
a live document that references a path must have that path verified to exist, and the drift guard did
not do this.** The replacements above were each verified; `docs/INSTRUMENT_LEDGER.md` records what each
retired instrument did and where it went.

---

## Drift signals — what to do when these fire

1. **A live file defines the project by a loop, a curve, an arm, or a self-improvement objective.**
   That is R1 drift. The file is either archived or rewritten; it is not "updated".
2. **A live file names a seed from the retired ecosystem** (`AgentJev`, `AnyJev`, a Laya root) as the
   model to pin. That is R2 drift. The protocol pins *one* English-capable System One artefact and
   records commit + SHA256 (§3.2, §12).
3. **A live file proposes training on the confirmatory path.** The protocol freezes θ and lists
   confirmatory fine-tuning as a non-goal. Training on the confirmatory path is a protocol violation,
   not a design choice.
4. **A claim spans scripts while only English evidence exists.** The protocol reserves every
   cross-script claim for Phase II and forbids equating λ across channels by "same edit rate as
   English" (§5.2). Phase I must not be narrated into a writing-system result.
5. **A number appears without provenance.** Every external number carries a source (model id + commit
   + SHA256, or a document plus date). Generated text is not a source.
6. **A phase is re-opened after the next phase's results were seen.** The staging rule is one-way.

---

## The JEV link is instrumentation, not an object of study (2026-10-04)

The pipeline this programme measures with is a **toolbox**. Choosing it is **not a research question**
and it is **not to be optimised**. The criterion, fixed by the programme owner, is:

> **the best option in the current JEV ecosystem that is free of academic controversy and openly
> accessible — then use it and leave it alone.**

Selected: **`convaiinnovations/laya`** (English root, Apache-2.0, 421M). Full reasoning and evidence:
`docs/JEV_TOOLBOX_SELECTION.md`; the pin: `docs/PHASE_I_PIN.md`.

**Two consequences, recorded so they are not re-litigated:**

1. **The instrument's internals are not a target.** If it is slow or awkward, we do not optimise it —
   we report the constraint, and if it blocks a measurement we say so.
2. **The instrument must be pinnable.** A pre-registered protocol needs a fixed artefact with a
   recorded revision and hashes, not a moving "best model". A pin without a revision is not a pin.

**Drift signal for this rule:** any live file that proposes measuring, benchmarking, tuning or
improving the JEV link itself — its kernels, its optimiser, its throughput, its architecture — rather
than using it to measure something else. That is instrument-tinkering, and it belongs to a different
programme (it is what R1 did).

## Toolboxes are not contamination (2026-10-04)

**The purification in this document is about the research OBJECT — the direction — and about nothing
else.** AGENTS, MCP servers, harnesses, verifiers, knowledge-graph tooling, formal-verification
substrates: these are **research-productivity infrastructure** and are **to be used**, not retired.

Owner's directive, verbatim in intent: **do not refuse accessible toolboxes — AGENTS / MCP / HARNESS
and the like — that productively serve research productivity.**

**The distinguishing question is one line:** *does this artefact assert what we are working on, or does
it help us do the work?*
- It asserts an object → it is drift, and the retirement rules above apply.
- It helps do the work → **it is a toolbox; keep it, use it, and do not spend programme time polishing
  it** (the same posture as the JEV link: instrumentation, not an object of study).

**This reverses an earlier over-reach.** `D:/2026-AI4S/AGENTS.md` (the multi-agent / MCP / wiki system
description) was tentatively raised as "historical material, possibly to be handled". **It is not.** It
describes tooling. It stays, and where its tooling works it should be used.

**Known live toolboxes (checked 2026-10-04):** Hermes MCP — `arxiv` (21 tools), `semantic-scholar`
(37 tools), `lwow`; project-declared MCP — analysis, deepxiv, filesystem, github, memory, pandoc,
playwright, repl, sequential-thinking, tavily; global substrates — BootLoops (`E:/2026-AI4S/bootloops`,
`~/.bootloops/config.json`), Lean 4 (`~/.elan`), the `understand-anything` plugin.

**Two rules for using them, so the posture stays honest:**
1. **A toolbox must be verified reachable before it is counted on.** A declaration in a document is not
   an available tool; a call that returns is. Where a declared server turns out not to be wired into
   this runtime, say so rather than assuming it.
2. **A toolbox report is not evidence.** A search, a plot, or a verifier's `PASS` is a tool result;
   it enters a claim only with its provenance attached.

## Published work is a claimant or an instrument — never an authority (2026-10-04)

**Owner's directive, verbatim in intent:** *not every conclusion or mechanism in SCIENCE/NATURE
literature holds; treating the polysemy of an abbreviation as LLM hallucination is precisely a
conclusion we want to challenge — and exactly the scientific gap we are after, for critical review.*

**A published result enters this programme in one of exactly two roles, and the role must be declared:**

- **an instrument** — a tool or method we use (a calibration procedure, an estimator, a benchmark). It
  is cited with its **provenance**.
- **a claimant** — an assertion we are testing. It is cited with its **scope condition**.

**It is never an authority.** The inference *published ⇒ correct* is forbidden, and a venue is not
evidence.

**Consequence for the kind of gap this programme seeks.** The gap is not "nobody measured X" (a coverage
gap); it is **"the published X is mis-specified, and here is the measurement that shows where its
signature and its target come apart"** — a construct/taxonomic gap. Pre-emption is therefore **not a bar
to novelty but the obligation to engage**, and `docs/GAP_VERDICT.md` is amended accordingly.

**The worked instance, because it is our own object:** classifying an abbreviation's polysemy as
*hallucination* merges **fabrication** with **a legitimate reading that disagrees with the annotator's
intent**. Being different constructs they have different signatures, and the merge is measurable — the
review instrument is `docs/CRITICAL_REVIEW_PROTOCOL.md`.

**Drift signal for this rule:** any live document that imports a published *conclusion* into this
programme's premises without declaring it a claimant, or that treats a venue as evidence of
correctness.

## Status of the live object

**Phase I is under way — instrument work only; no hypothesis has been tested.**

| Step (§13 runbook) | State | Record |
|---|---|---|
| 1. Pin System One checkpoint | **COMPLETE & VERIFIED** ✅ | `convaiinnovations/laya`, **root (English)** variant, Apache-2.0, 421M, at immutable revision **`55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`**. Per-file sha256 for all 5 files in `config/pin_laya.json` (846.20 MB). **Verified by execution:** `measurement/smoke_predict.py` ran on CUDA at that revision and returned per-option probabilities, `truncated=false`. Authority: `docs/PHASE_I_PIN.md`. **Two recorded caveats:** (a) the revision carries **three** variants — the root is the pinned one, so "Laya" alone is ambiguous; (b) Hub `main` had drifted to `7b928d82…` — **main is not the pin**. |
| 2. English intent items + gold | **BUILT & VERIFIED** ✅ | **932 items** measured on disk (`measurement/item_bank.jsonl`): **652 test / 280 dev**. Gold is a **construction invariant** of the generator rather than a human label, which is what makes it checkable. Composition and the template-conformance threat are recorded in `docs/TEMPLATE_COMPOSITION_FINDING.md`. |
| 3. `N_en` noise generator | **BUILT & VERIFIED** ✅ | `measurement/typo_noise.py` — four classes, pure function of `(item_id, λ, seed)`. Exercised over 1080 rows: λ=0 gives zero ops, λ=0.05 and λ=0.12 give mean realised rates 0.0502 / 0.1148 (well calibrated; the feature is **spread**, SD 0.026 / 0.036, and at λ=0.05 an item can receive **zero** edits). **λ levels pending O1.** |
| 4. `predict → JSONL` | **BUILT & VERIFIED** ✅ | `measurement/run_phase1.py` — 1080 rows in 10 s, 0 failures, ≈107 rows/s, so the frozen confirmatory size (17,604 rows) is ~3 min of GPU. Seven schema/logic checks pass against the written record. Resumable. **`error` is `null` where no gold exists**, never 0. Record: `docs/PREDICT_JSONL_RUNNER.md` |
| 5–6. Fit τ\*, test H1.1–H1.3 | **BLOCKED ON ONE THING** | **Everything except the λ levels is closed.** Resolved and measured: the pin (§12 item 4, verified against disk by `scripts/check_pin_integrity.py`), O2 (`N_test = 652`, bank = 932), A4(3) (**criteria RETAINED**), and C2 (**ANSWERED, and it FAILED** — `noul` scores exactly chance, 0.5000 over 12 probes, and the documented two-option workaround does *worse* than chance in the inverted direction; `ok`/`escalate` are **dropped** under B4, disclosed as a deviation from §3.1, with H1.1/H1.2 unaffected because they rest on `intent`; record `docs/C2_NOUL_VALIDITY.md`). **O3 is half closed, and the half that remains is the half that needs a person.** The *collection* question is answered: the bank reached 932 and the template-composition threat was **measured rather than assumed** — all 932 items are paired across all 21 conditions (7λ × 3 seeds), template × λ is orthogonal, and template explains **η² = 0.0064** of realised edit rate (`scripts/orthogonality_check.py`). Under a within-item design that is a description, not a confound. What is **not** closed is O3's **human pass over the bank**: `docs/ITEM_BANK_SPEC.md` requires gold to be confirmed by a human, `docs/O3_BANK_DECISION.md` records it, and no such pass has been run. **An earlier edit of this file claimed O3 was closed outright. That was an overclaim** — it read 'the confound was measured' as 'the item is done', and they are different questions. **An overclaim is a promotion, not a shorthand.** **What remains is O1 (the λ readability calibration) and O3's human pass over the item bank** — the first needs three decisions from the researcher, the second needs a person to read 932 items. Nothing about the instrument, the bank or the noise generator is outstanding. |
| 7. Freeze all artefacts | **BLOCKED BY TWO OPEN ITEMS** | `docs/PHASE_I_AMENDMENT_2.md` is the last amendment before the seal and closes four questions. **B1** the τ\* tie-break is **DECLARED** (least admissible threshold) and is now **machine-checked**: the `lean-nhb` formalisation builds clean at 12 theorems, zero errors, zero `sorry`, every one verified by Lean's kernel via `#print axioms`, and `least_admissible_maximises_coverage` proves the declared rule *maximises* coverage among admissible thresholds. The guarantee is a maximum and **not** a strict one, which the protocol now states. **B2** `realised_edit_rate` enters as a covariate, the per-λ distribution and the zero-op share are all reported; **B3** π_d is defined in the analysis code with the four-way item breakdown; **B4** `ok`/`escalate` are **dropped** (C2 measured `noul` at chance). A4(3) resolved as **criteria RETAINED**, with the confound probe committed and **measured**. **The seal is blocked by exactly two things: O1 (the λ readability calibration) and O3's human pass over the item bank.** Nothing else is outstanding — not the instrument, not the bank's size, not the noise generator, not the template composition. No confirmatory data may be collected before the seal. |

**Pin-time calibrations: BOTH NOW RESOLVED** (`docs/PHASE_I_PIN.md`). **No temperature refit** — the
checkpoint is used as shipped, because refitting `c` would measure a different instrument
(`docs/INSTRUMENT_POSTURE.md`). **C2 answered, and it failed**: `noul` is not used at all, and `ok`
and `escalate` are dropped under B4 (`docs/C2_NOUL_VALIDITY.md`). The primary endpoint rests on
`intent`, a `choice`, so this does not touch it.
Both are decided on dev and frozen; neither may be revisited after the confirmatory results are seen.

The Phase I pre-registration is drafted at `docs/PHASE_I_PREREGISTRATION.md`: **nine of the twelve
§12 items are FIXED NOW**, and three are **PENDING** because the protocol's own sequencing requires a
measurement first (λ rates from a readability calibration; N from a pilot discordance rate; the item
bank). Nothing PENDING may be guessed later and called pre-registered — each must be frozen by an
amendment filed **before** the confirmatory run, naming the measurement that set it.

**Nothing in this repository is cited as evidence for any claim in the protocol.** The protocol carries
its own pre-registration (§12) and its own artefact freeze (§4.6).
