# CURRENT OBJECT

**This file is the single authority on what this repository is working on and what it has retired.
Every other document is subordinate to it. If a live file disagrees with this one, this one wins and
the other file is drift.**

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

## Live instruments — kept, and why

These were built during R1 but are not about R1's object. The current object needs them.

| Path | Role under the current object |
|---|---|
| `paths.py`, `config/paths.json` | Path SSOT and environment precedence. Unchanged responsibility. |
| `scripts/calibrate_against_release.py` | Loads a **pinned** System One checkpoint and evaluates it against a published record. This is the protocol's "pin the artefact" step (§3.2) — the tool that establishes a checkpoint is loaded correctly before any noise is applied. |
| `measurement/report_from_items.py` | Recovers metrics from a trial record. Extend it with `SilentError@τ` and `Coverage@ε`; do not fork a second reporter. |
| `measurement/build_synth_split.py` | Builds typed-question splits over `choice` / `noul` / `score`. The protocol's `Q0` (`intent`, `ok`, `escalate`) is the same question-type machinery. |
| `scripts/health.py` | Run-health diagnostics for long jobs. |
| `scripts/run_with_heartbeat.py` | Heartbeat wrapper for long jobs; terminal record written in `finally`. |
| `TOOLS.md`, `docs/BOOTLOOPS.md` | Tooling and the shared BootLoops substrate. |

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
| 1. Pin System One checkpoint | **CHOICE MADE; PIN INCOMPLETE** | `docs/PHASE_I_PIN.md` — `convaiinnovations/laya`, English root, Apache-2.0, 421M. **The revision hash + per-file sha256 are not yet recorded**, so §12 item 4 is not satisfied and the pre-registration may not be sealed. `config/pin.json` is written when the first download completes. |
| 2. English intent items + gold | **SPEC WRITTEN, NOT BUILT** | `docs/ITEM_BANK_SPEC.md`; four approval points left open for the researcher (domain scope, option counts, bank size, who labels gold). |
| 3. `N_en` noise generator | **IN PROGRESS (delegated)** | Classes fixed (QWERTY-adjacent substitution, transposition, deletion, insertion); λ rates pending a readability calibration (O1). |
| 4. `predict → JSONL` | **IN PROGRESS (delegated)** | Schema is the protocol's §3.5. The runner must reach Laya, not the superseded pin. |
| 5–6. Fit τ\*, test H1.1–H1.3 | **BLOCKED** | N pending a pilot measurement of the discordance rate and the clean SilentError baseline (O2); the pilot needs the pinned revision and the item bank. |
| 7. Freeze all artefacts | **NOT STARTED** | — |

**Two pin-time calibrations are outstanding and belong before the seal** (`docs/PHASE_I_PIN.md`):
a temperature refit per (question type, option count) — the checkpoint ships over-confident — and a
decision on whether `noul` is used directly or via the documented two-option-`choice` workaround.
Both are decided on dev and frozen; neither may be revisited after the confirmatory results are seen.

The Phase I pre-registration is drafted at `docs/PHASE_I_PREREGISTRATION.md`: **nine of the twelve
§12 items are FIXED NOW**, and three are **PENDING** because the protocol's own sequencing requires a
measurement first (λ rates from a readability calibration; N from a pilot discordance rate; the item
bank). Nothing PENDING may be guessed later and called pre-registered — each must be frozen by an
amendment filed **before** the confirmatory run, naming the measurement that set it.

**Nothing in this repository is cited as evidence for any claim in the protocol.** The protocol carries
its own pre-registration (§12) and its own artefact freeze (§4.6).
