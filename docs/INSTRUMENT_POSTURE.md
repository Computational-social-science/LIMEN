# Instrument admission — three criteria, and then the question is closed

**Ruling, 2026-10-04, on the programme owner's instruction:** *we only judge whether a given JEV tool is
**usable**, **scientific**, and **reproducible** — that is all.*

A JEV-ecosystem component is **one tool on one link of the pipeline**. It is not a research object, not
something to improve, and not something whose properties the programme is responsible for fixing.

---

## The admission test

A component may enter the pipeline **if and only if** all three hold. Each is a yes/no, and each is
answered with evidence, not with an impression.

| # | Criterion | The question | The evidence that answers it |
|---|---|---|---|
| **1** | **Usable** | Does it run on this host and return the interface the protocol needs — `state × questions → probabilities`? | An actual run, at the pinned revision, returning per-option probabilities. Not a model card, not a README. |
| **2** | **Scientific** | Is it a legitimate instrument for this question? | An open licence; a documented interface; provenance free of academic controversy (the protocol's own §3.2 criterion). |
| **3** | **Reproducible** | Does the same input give the same output, here and elsewhere? | An **immutable** revision (a commit, never a branch); recorded per-file digests; and a perturbation generator that is a pure function of its declared inputs. |

**Failing any one rejects the component — and the response is to choose a different component, not to
repair the one that failed.**

**Passing all three ADMITS it, and admission means: use it exactly as shipped.** Its limitations are
**disclosed** in the manuscript, never removed. A disclosed limitation is a property of the instrument
and therefore of the result; a removed one is an unlogged substitution of the object of study.

## What admission explicitly does NOT authorise

- **Tuning.** No temperature refit, no recalibration, no threshold adjustment, no configuration edit.
- **Defect repair.** An out-of-range value, a load-time warning, an odd default: if the component still
  passes the three criteria, the oddity is **documented and lived with**.
- **Validation as an end in itself.** "How good is this model?" is not a question this programme asks.
- **Checkpoint substitution** once the pre-registration is sealed.

**Drift signal.** Any live document that schedules a *change* to an admitted component — before or
during the confirmatory run — is drift. Documenting a property is not drift; changing one is.

## The verdict on the pinned component

**`convaiinnovations/laya`, root (English) variant — ADMITTED.** All three criteria met, with evidence:

| Criterion | Evidence | |
|---|---|---|
| **Usable** | `measurement/smoke_predict.py` returned per-option probabilities for 3 items on CUDA at revision `55cf4c4e…` with `truncated: false`; then `measurement/run_phase1.py` produced **1080 rows in 10 s with 0 failures** (≈107 rows/s). | ✓ |
| **Scientific** | Apache-2.0; documented interface (`choice` / `noul` / `score`); published model card; no academic controversy attached. | ✓ |
| **Reproducible** | Immutable revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`; per-file sha256 for all 5 files in `config/pin_laya.json`; the noise generator is a pure function of `(item_id, λ, seed)`. An independent replay reproduced the pilot's clean accuracy **to the item** (104/120, difference +0.0000). | ✓ |

**The tool question is CLOSED.** No further work is scheduled on it — including the investigations that
were previously scheduled here and are now withdrawn (a temperature refit; treating the shipped map's
out-of-range entry as a defect).

### Properties disclosed, not fixed

Recorded once, here and in the manuscript's instrument subsection, so that no reader mistakes them for
defects in our runs:

1. **It ships over-confident** — the card reports mean ECE 0.466, and 0.081 after a refit **we do not
   perform**. We report the **shipped** figure as the instrument's real property; the refitted figure is
   quoted as the vendor's, never adopted as ours.
2. **The shipped temperature map contains one out-of-range entry** (`choice:11+` = 0.1006). The package
   clamps it to 0.5 at load and warns that affected entries are uncalibrated. **Phase I uses 2–4 options,
   so the entries exercised are `choice:2` and `choice:3-5`, both in range — the invalid entry is
   unreachable by this design.** The load-time warning is **expected** and will appear in every run log.
3. **`noul` may follow its option labels rather than the state.** This is the one item that stays open,
   and it stays for a reason that is **not** tuning: if the primitive does not measure what the protocol's
   §3.1 wire format says it measures, every number computed from it is void. **Measurement validity is
   inside the pipeline's remit; instrument quality is not.** The choice between direct `noul` and the
   documented two-option-`choice` workaround is decided on dev and frozen before the run.
