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

## Status of the live object

**Not yet started.** The protocol is a draft for staged pre-registration (version 1.1). As of
2026-10-04 no Phase I artefact exists: no pinned checkpoint recorded with commit and SHA256, no item
bank, no `N_en` typo generator, no JSONL, no analysis. The work ahead is the protocol's §13 runbook.

**Nothing in this repository is cited as evidence for any claim in the protocol.** The protocol
carries its own pre-registration (§12) and its own artefact freeze (§4.6).
