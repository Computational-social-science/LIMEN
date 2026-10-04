# JEV Toolbox Selection — the pipeline is instrumentation, not an object of study

**Decision (2026-10-04).** The JEV link in this programme is **instrumentation**. Choosing it is not a
research question and is not to be optimised. The selection criterion is the one the programme owner
set: **the best option in the current JEV ecosystem that is (a) free of academic controversy and
(b) openly accessible** — then it is used as a toolbox and left alone.

**Selected: `convaiinnovations/laya` (the English root checkpoint). Apache-2.0, Convai Innovations.**
Runtime: `pip install laya`.

---

## Why the criterion had to be stated this way

The retired programme (R1, archived) treated its stack as an object: it reproduced a training loop,
measured per-step cost, and argued about kernel stacks and optimiser choices. **None of that is
science about the live object.** The live object is the orthographic-channels protocol; its instrument
should be the best available one and should not consume the programme's attention.

Two consequences follow, and both are recorded here so they are not re-litigated:

1. **The instrument's internals are not a target.** If Laya is slow or awkward we do not optimise it;
   we report the constraint and, if it blocks a measurement, we say so.
2. **The instrument must be pinnable and stable.** A pre-registered protocol needs a fixed artefact.
   The selection below is therefore recorded with a version and a licence, not as "the best model".

## Evidence against the two criteria

### (a) Free of academic controversy

The ecosystem's flagship, TypeSafe's hosted **Jev**, is **closed, hosted, and waitlisted**, and its
published claims are being independently audited — for example `jev-baselines-eval` ran a
**pre-registered** comparison (Banking77 n=208, CLINC150 zero-shot n=200) and reported that Jev is
~2× faster than a nano-class LLM **rather than the 40–200× its marketing suggested**, and that **its
confidence is not better calibrated than an LLM's**. A second pre-registered study in the same
repository found that under authority-framed prompt injection **Jev's confidence ranks hijacked
decisions *above* resisted ones** (AUROC 0.261 [0.190, 0.336]).

**None of that is a criticism of the work — it is a reason not to build a calibration study on top of
a component whose calibration is itself under audit.** The protocol's central instrument is the
confidence value; it must come from something whose probability semantics are not in dispute.

**Laya's advantage is that it states its own limits before anyone else has to.** From its model card,
verbatim:

- *"**Ships over-confident:** Refitting one temperature per (question type, option count) moves mean
  ECE **0.466 → 0.081** (`laya`) and **0.314 → 0.106** (`laya-multilingual`). Do this on your own data
  before trusting the probabilities."*
- *"`noul` can follow its option labels instead of the state … returning a confident "no" for clearly
  positive input (#156). **Check `noul` answers on your own data.**"*
- *"The English checkpoint collapses on non-Latin scripts (Khmer scores **0.000 accuracy at 0.952
  confidence**). Because the model stays confident while being wrong, confidence gating cannot save
  you."*
- *"`action.act_probability` carries no usable signal yet … Gate on `confidence` instead."*
- *"Ordinal `score` questions are the weakest primitive (SST-5 0.372)."*
- *"Treat Laya as a fast base to specialise, not as a zero-shot decision engine."*

**The third of those is not only a caveat — it is a published, independently reproducible instance of
exactly the phenomenon this protocol measures** (a confidently wrong answer surviving a confidence
gate). It is cited as motivation, not as evidence, because the protocol must earn its own result.

### (b) Openly accessible

| | |
|---|---|
| Licence | **Apache 2.0** (code and weights) |
| Install | `pip install laya` — Python 3.10+; extras `[serve]`, `[mcp]`, `[langchain]`, `[onnx]`, `[fast]` |
| Weights | HuggingFace `convaiinnovations/laya` (hub repo holds the family) |
| Sizes | English root **421M** (ModernBERT-large, 512 ctx) · multilingual **322M** (mmBERT-base, 1024/up to 8192) · typed-decisions **421M** (1024) |
| Hardware | 39.5 ms / question on a **T4**; comfortably inside a 12 GB consumer GPU, and CPU-capable |
| Standing | **30.2k stars, 2.6k forks, 1,281 commits**, commits same-day; 134 finetunes, 58 quantizations, 59 Spaces |
| Local-only | The confirmatory path needs **no API and no key** |

## The decisive fit: the protocol's wire format *is* Laya's API

Protocol §3.1 defines the interface as `state` + typed `questions` → probabilities per question id,
with `choice`, `noul` and per-option `criteria`. That is Laya's native call shape:

```python
from laya import Router
router = Router()
result = router.predict(state, {
    "intent":   {"type": "choice", "instructions": "...", "criteria": {...}},
    "ok":       {"type": "noul",   "instructions": "Is the request clear enough to act on?"},
    "escalate": {"type": "noul",   "instructions": "Should a human handle this?"},
})
result["answers"]["intent"]["choice"]
result["answers"]["ok"]["noul"]
result["routing"]["model"]
```

The protocol's §3.2 named "English **Laya** root" as a candidate before this survey was run. The
survey does not contradict that; it supplies the evidence for it.

## Pin within the family: the English **root**, not the typed-decisions fine-tune

The hub repo offers three checkpoints. Phase I pins **`convaiinnovations/laya`** — the English root —
and the reasons are load-bearing:

1. **Protocol §3.2 says so** ("pin **one** English-capable System One artefact"), and §12 item 1 fixes
   Phase I to English with no script factor.
2. **Contamination avoidance.** `laya-typed-decisions` is fine-tuned on *"the four typed-decisions
   workflows"*. If the Phase I item bank overlaps those workflows, a high score would measure
   memorisation of the fine-tune, not behaviour. The root checkpoint has no such exposure.
3. **The multilingual checkpoint and its router are the natural Phase II instrument** (100+ languages,
   script detection in <0.5 ms). Holding the root for Phase I and the multilingual for Phase II keeps
   the family constant across the two phases instead of changing instrument mid-programme.

**Known cost of this choice, stated now:** the root is weak zero-shot on typed decisions (the card
reports **0.362** where the fine-tune reaches **0.766**). Phase I therefore risks low clean accuracy.
That is a **power** problem, and it is handled downstream, not by switching checkpoints after seeing
results: if the pilot's clean accuracy is too close to chance for the design to detect a 5-point
drop, that is recorded as a limitation of the pin and Phase I reports it — the checkpoint is not
swapped mid-phase.

## Instrument calibration this pin requires (belongs to the pin, not to the test)

Laya ships over-confident. Under the admission test of `docs/INSTRUMENT_POSTURE.md`, **that is a
disclosed property of an ADMITTED component — not a calibration task.** Nothing here is tuned.

| Item | Status | Why |
|---|---|---|
| **Temperature refit per (question type, option count)** | **DROPPED** | Card: mean ECE 0.466 → 0.081 after refit. **Not performed.** The research question is about *this* instrument's control law, and `c` enters that law; refitting `c` on our dev data would substitute a different instrument. The **shipped** ECE is reported as the instrument's real property; the vendor's after-refit figure is quoted as the vendor's. |
| **`noul` sanity check** | **OPEN — measurement validity, not tuning** | Card: `noul` can follow its option labels and answer a confident "no" on clearly positive input (#156), with a documented workaround (ask as a two-option `choice` with neutral keys). **If the primitive does not measure what §3.1 says, every number from it is void** — which is why this one stays. Decided by measurement on dev, then frozen. |

**The temperature refit was previously scheduled here as instrument setup. That was the wrong posture
and is withdrawn** (`docs/INSTRUMENT_POSTURE.md`): this programme judges a tool on three criteria —
usable, scientific, reproducible — and then uses it as shipped. It does not improve it.

## What this decision retires

- **The earlier Phase I pin (a locally held 0.8B release from the retired ecosystem) is superseded.**
  It was chosen when the criterion was "the only checkpoint on this machine". Under the owner's
  criterion — best *openly accessible, uncontroversial* option in the current ecosystem — a local
  artefact of the retired programme is not in the running. `docs/PHASE_I_PIN.md` is rewritten to the
  Laya pin.
- **The retired programme's harness, calibration scripts and environment are not part of the
  instrument.** They stay archived as a record.

## Sources (all checked 2026-10-04)

- `cobanov/awesome-jev` — curated, source-backed ecosystem list (495★, CC0)
- `rupeshpoojary9/awesome-open-system-one` — **open-only** list; source of the candidate set
- `convaiinnovations/laya` (HuggingFace model card) and `NandhaKishorM/laya` (GitHub, Apache-2.0)
- `ickma2311/jev-baselines-eval` — pre-registered independent evaluations (MIT)
- `AbdelStark/jev-benchmarks`, `fstandhartinger/jevbench` — probability-aware open benchmarks
- `typesafe.ai` launch post and `docs.typesafe.ai` — the category's own definitions

**No number above is used as evidence for a protocol hypothesis.** They establish that the instrument
is open, maintained, and honest about its limits.
