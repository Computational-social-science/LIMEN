# Phase II Corpus Rebuild — Top-Level Design (Pending Phase I Seal)

**Status:** design only, **pending Phase I seal**. Nothing here has been built. This design exists for the Phase II corpus that will replace the retired Root Recovery Corpus (RRC v2.0.0, retired 2026-10-11 as an invalid measurement instrument). The post-mortem is `docs/POSTMORTEM_RRC_VALIDITY.md`; the evidence is `archive/rrc-v2.0.0-INVALID/`.

**Why a document and not a script.** The previous build had 83 passing guards and no acceptance criterion. The failure was not in the code — it was that no one had written down, *before* building, what would make an item valid. So the first artifact of a rebuild is the criterion, frozen, with its own controls. Everything below is ordered by that principle.

**Phase dependency.** This design is for **Phase II** (§5 of the Protocol). Per the Protocol (§0.2, §5.1), Phase II pre-registration is filed **only after** Phase I instruments are frozen and pilot-stable. The Phase I seal is blocked only by the operational pre-run; once the seal is applied, Phase II pre-registration can be filed and this design becomes actionable.

**A note on authorship.** This design is written by the same agent that built the corpus it replaces. That is a known independence defect, and §5.4 is the structural answer to it: the role that gates the pipeline is specified to be a *different* process with a *different* premise, and the specific question it must answer is named so its answer can be checked.

---

## 1. The scientific question the corpus must support

State it before the construction, in one falsifiable sentence, because every construction rule below
is derived from it:

> **Given an observed corrupted form, can a reader recover the intended root by knowing which errors
> actually occur — and does that ability vary with the writing system's orthographic depth?**

Two consequences follow immediately, and both are load-bearing:

1. **The task must be decidable only with channel knowledge.** If surface similarity between the
   candidate and the observation decides it, the item measures string distance. This is what killed
   the previous corpus.
2. **Difficulty must be a property of the item, not of the reader's search.** It is the confidence gap
   between candidate roots under the measured channel — not a character-similarity margin.

## 2. What a valid item is

An item is a tuple `(S, {R_1..R_k}, answer)` where `S` is an observed form read out of a real corpus of
human error, and every `R_i` is a **candidate intended form**.

**Validity is a property of the candidate SET, and it has three conditions, all necessary:**

| # | condition | why |
|---|---|---|
| V1 | **Each `R_i` has non-negligible `P(S \| R_i)` under the measured channel.** | Every option must be a plausible *source of the observation*. This is the condition the previous corpus violated by drawing decoys from the answer's surface neighbourhood. |
| V2 | **Exactly one `R_i` has a channel probability that is not negligible OR has no decision could be trivially made.** | If two are plausible the item is ambiguous and must be **discarded, not kept as "hard"**. |
| V3 | **The channel probabilities are separated enough to define a margin.** | An item whose candidates all have similar `P(S\|R_i)` has no difficulty signal, which is what `margin_defined = false` was reporting on 52.7–100 % of the previous corpus. |

**The construction direction is the whole design.** Generate candidates by *reading the observation
backwards through the channel*:

```
For each observed S:
    C(S) = { R : P(S | R) >= tau_channel }        # the observation's plausible histories
    if |C(S)| < 2:      discard                   # nothing to discriminate (V2)
    answer = argmax_R P(S | R)
    decoys = C(S) \ {answer}, ranked by P(S | R)  # NOT by string similarity to anything
```

**Forbidden, and stated as a prohibition because it is the exact error that was made:** a decoy may
never be selected by its similarity to `S` or to the answer. Selection is by channel probability only.

## 3. The acceptance gate (frozen before the first item is built)

`planted-truth` step 0 requires the controls to exist before the real data opens. For this corpus the
gate is **one number**, and it is chosen now, before any new item exists:

> **A channel-blind heuristic must score within the chance band of the task.**

Operationalised, with the thresholds set here and not afterwards:

| control | requirement | measured how |
|---|---|---|
| **G-trivial** | Levenshtein, longest-common-prefix, length and substring picks each land **inside [chance, chance + 0.10]** | `audit_item_validity.py` on the new corpus |
| **G-plant** | On items constructed so the answer is *deliberately not* the surface-nearest candidate, the same heuristics score **at chance exactly**, and a channel-aware resolver recovers **≥ 0.95** | synthetic planted set, built by construction, answer written first |
| **G-null** | Two candidates with identical channel probability produce an item that is **rejected**, not scored | injected-ambiguity fixture |
| **G-percell** | No cell may pass while another fails; the gate is per (arm, layer) | the audit's cell table |

**Refusal to move a threshold is part of the gate.** If a control fails, the construction changes; the
threshold does not. `acceptance-gate` calls the alternative "threshold drift", and the previous corpus
died of it in prose form.

**Every number the corpus will ever support is reported in the same table as these floors.** A result
stated against "chance 0.25" without the trivial-heuristic floor beside it is not reportable.

## 4. The pipeline, with gates

Seven stages, each ending in a handoff that the Critical Agent must clear. A gate that is not cleared
stops the pipeline; there is no "proceed with a note".

| stage | produces | gate (Critical Agent verifies) |
|---|---|---|
| **S1 sources** | candidate corpora of *observed* errors, with provenance and licence | every source is observed human error, not synthesised; licence permits the use; the corpus is the object, not a proxy |
| **S2 channel** | `P(observed \| intended)` estimated from the sources | the estimate is measured, not assumed; its uncertainty is carried forward; a **null channel** (uniform errors) is rejected by the same estimator |
| **S3 candidates** | for each `S`, the set `C(S)` | V1 holds for every option; **no option was selected by similarity to `S` or to the answer** (this is the specific check the previous build lacked) |
| **S4 assembly** | items with exactly one answer, multiple plausible decoys | V2 and V3 hold; ambiguous items are discarded, and the discard count is reported |
| **S5 validity gate** | the audit table | **§3 in full.** This gate is the accept gate; S6 does not begin without it |
| **S6 measurement** | instrument results | the instrument is the *native* model, the prompt form is validated (a pilot showing the instrument can read the choices at all), and the trivial floors are printed beside every accuracy |
| **S7 reporting** | the manuscript / report | every claim traces to a number; every number carries its control; no narrative history of earlier drafts |

**S2 before S3 is not negotiable.** The channel is what makes candidates generatable from the
observation. Building decoys before the channel is measured is how the previous corpus ended up
selecting them by surface form — there was no other criterion available.

## 5. The multi-agent environment

### 5.1 Roles, with hard constraints

Adopted from the Driver-Harness separation already used in this project, extended so that verification
is continuous rather than terminal:

| role | responsibility | may NOT |
|---|---|---|
| **Orchestrator** | dispatch stages, hold the plan, own the pipeline state | read raw source data; clear its own gate |
| **Constructor** | build S1–S4 artifacts | grade its own output; write the Critical Agent's report |
| **Critical Agent** | clear or block **every handoff** (S1→S7) | modify any artifact; be overridden by the Orchestrator |
| **Independent Auditor** | re-derive §2's construction rule from the spec alone, then compare to what was built | see the constructor's implementation before writing its derivation |

### 5.2 The Critical Agent — specification

The Critical Agent is not a reviewer that comments at the end. It is a **gate**, and it is the role the
previous pipeline lacked. Its specification:

1. **Its checklist is frozen before S1** and is the §3 gate plus the §4 per-stage criteria. It may not
   add a criterion after seeing an artifact, and may not relax one.
2. **It reports per gate: `CLEARED` or `BLOCKED`**, with the measured evidence attached — a count, a
   table, a number. An adjective is not a verdict.
3. **A `BLOCKED` escalates to the user.** The Orchestrator has no override. (The previous pipeline's
   failure mode was exactly an override: an alarm fired, a plausible story was written, and the run
   continued with the alarm recorded as a "limitation".)
4. **It must refuse explanations of the form "the check is oversensitive."** If a control fires, the
   root cause is found or the pipeline stops. This clause exists because it is the specific behaviour
   that let nine days of work proceed on an invalid instrument.
5. **It audits the *right property*.** The previous build's 83 guards were each verified bidirectional
   and all checked plumbing. The Critical Agent's gates are anchored on §2's validity conditions and
   §3's acceptance numbers — not on conservation, purity, or style. **A guard count is not evidence.**
6. **It has its own negative control.** Before it gates anything real, a deliberately defective
   handoff is fed to it — a candidate set whose decoys were selected by surface similarity, which is
   the exact defect being guarded against — and the Critical Agent must **BLOCK** it. Until it has
   been watched to block, it is a hope, not a gate. This mirrors `planted-truth` step 5: *a control's
   first demonstrated failure is its birth certificate.*
7. **It runs on a different premise.** For the S3 gate it receives the construction rule and the
   artifact, **not** the constructor's rationale. For the S5 gate it re-runs the trivial heuristics
   itself rather than reading the constructor's audit output.

### 5.3 Independence bookkeeping

`independence-bookkeeping` asks what each check shares with the thing it checks. Declared here, before
building:

- The **channel estimate (S2)** and the **item construction (S3–S4)** share the same estimated
  `P(S|R)`. That is intended — S3 must be generated from S2 — and it means S5 cannot use the channel
  to grade itself. **S5's controls are consequently channel-blind heuristics and a planted set, neither
  of which uses the channel.** This is the disjointness that makes S5 meaningful.
- The **planted set (G-plant)** is written by construction — the answer is authored first, then data
  produced from it — never regenerated from the pipeline being tested.
- The **Independent Auditor** may not read the constructor's code before writing its own derivation of
  §2. A derivation that agrees because it was read is not independent.

### 5.4 The known independence defect, and its mitigation

The agent writing this design also built the retired corpus, and would be the natural Constructor. **The
Critical Agent must therefore not be that agent**, and the S5 gate must be computed by code the
Constructor did not write. Where a genuinely different process is unavailable, the fallback is to run
the Critical Agent with a **different model and a different framing** (adversarial convergence: N
independent attempts, M refuters, keep only claims that survive), and to record the residual
shared-premise risk explicitly rather than claim independence that does not exist.

### 5.5 Execution substrate

Fan-out runs as a **plan-in-code workflow**: the deterministic assembly (S1–S3, per-source, per-arm)
is a script; only the irreducibly-judgmental gates fan out to subagents. Per `dynamic-workflow`:
- `delegate_task` runs **inside the parent turn** and is discarded on interruption — fine for
  minutes-long gates, wrong for a multi-day build. A durable build needs the SQLite kanban swarm.
- Atomicity is required in every gate report: "cell `zh/L2c` fails G-trivial at `edit = 0.41`", never
  "the corpus looks weak".

## 6. Stop conditions

The pipeline halts — not annotates, halts — when any of these holds. Each is a restatement of a
specific failure of the previous build:

1. **Any §3 control fails.** (`threshold drift`)
2. **Undefined difficulty exceeds 5 % of items in any cell.** (`margin_defined = false` on 52.7–100 % was reported as a limitation and the build continued)
3. **A decoy's selection cannot be traced to a channel probability.** (the exact construction error)
4. **A gate report contains an adjective where a number is required.**
5. **The Critical Agent cannot be shown to block a known-defective handoff.**
6. **A measurement is taken before S5 is cleared.** (measurements were run and reported on a corpus with no validity audit)

## 7. Open questions, to be settled before S1

These are for the user, not for the agent to assume:

1. **Scope.** Is this rebuild part of the live object, or a standalone methodological artifact? The
   answer determines whether it inherits the previous object's claims.
2. **Target size.** The channel-conditioned construction will yield far fewer items than 100,838 —
   plausibly two orders of magnitude fewer, because V2 discards every observation with a unique
   plausible history. **Is a smaller, valid corpus acceptable, or does the design need a different
   task form to reach scale?** This is the single largest risk to the plan.
3. **Writing systems.** The previous six arms were not comparable (only L4 was shared) and one
   observation appeared in two layers. Which systems can be supported by *measured* channels, and does
   the comparison require a channel that exists in all of them?
4. **Which instrument**, and whether the prompt form is validated before the build rather than after.
