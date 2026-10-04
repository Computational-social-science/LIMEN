# Phase I — Pinned System One Artefact

**Status:** pinned 2026-10-04. **Revises an earlier pin**, archived at
`archive/superseded_by_toolbox_selection_2026-10-04/PIN_superseded_rsijev_08b.md`. The first pin was a
locally held 0.8B release from the retired ecosystem, chosen when the criterion was "the only
checkpoint on this machine". Under the programme owner's criterion — **the best *openly accessible,
uncontroversial* option in the current JEV ecosystem, used as a toolbox** — a local artefact of the
retired programme is not in the running. Selection reasoning and evidence:
`docs/JEV_TOOLBOX_SELECTION.md`.

**Protocol requirement:** §3.2 ("pin **one** English-capable System One artefact"), §12 item 4
("Model ID + commit + SHA256").

---

## The pinned artefact

| Field | Value |
|---|---|
| Model | **`convaiinnovations/laya`** — the English root checkpoint of the Laya family |
| Publisher | Convai Innovations |
| Licence | **Apache 2.0** (code and weights) |
| Architecture | ModernBERT-large encoder, non-autoregressive |
| Parameters | 421M |
| Context | 512 tokens |
| Primitives | `choice` (with per-option `criteria`), `noul`, `score` |
| Install | `pip install laya` (Python 3.10+) |
| Weights | HuggingFace `convaiinnovations/laya` |
| Confirmatory path | **Local only. No API, no key.** |

**Pinned revision — NOT YET RECORDED, so this pin is INCOMPLETE.** §12 item 4 requires commit +
SHA256. The exact HuggingFace revision hash, the sha256 of every downloaded weight file, and the
resolved `laya` package version go into `config/pin.json` when the first download completes. Until
that file exists this document records a *choice*, not a *pin*, and the pre-registration may not be
sealed.

## The family, and why Phase I takes the root

The hub repo holds three checkpoints:

| Checkpoint | Backbone | Params | Context | Best at |
|---|---|---|---|---|
| **`convaiinnovations/laya`** (root) | ModernBERT-large | 421M | 512 | English text, guardrails, email triage |
| `convaiinnovations/laya-multilingual` | mmBERT-base | 322M | 1024 (up to 8192) | 100+ languages, ~2.2× faster |
| `convaiinnovations/laya-typed-decisions` | ModernBERT-large | 421M | 1024 | the four typed-decisions workflows |

**Phase I pins the root**, for three load-bearing reasons:

1. §3.2 says to pin **one English-capable** artefact, and §12 item 1 fixes Phase I to English with no
   script factor.
2. **Contamination avoidance.** `laya-typed-decisions` is fine-tuned on four typed-decision workflows.
   If the Phase I item bank overlapped them, a high score would measure memorisation of the fine-tune,
   not behaviour. The root has no such exposure.
3. **Phase II keeps the same family.** The multilingual checkpoint plus Laya's `Router` (script
   detection in <0.5 ms) is the natural Phase II instrument, so the instrument family stays constant
   across phases instead of changing mid-programme.

**Known cost, stated before the run.** The root is weak zero-shot on typed decisions — the model card
reports **0.362** where the fine-tune reaches **0.766**. Phase I therefore risks low clean accuracy.
That is a **power** problem, and it is handled downstream by measurement, **not** by swapping
checkpoints after seeing results: if the pilot's clean accuracy is too near chance for the design to
detect a five-point drop, that is recorded as a limitation of the pin and Phase I reports it.

## Why the protocol's interface is this model's API

Protocol §3.1: `state` + typed `questions` → probabilities per question id, with `choice`, `noul` and
per-option `criteria`. Laya's native call shape is the same, which is why the protocol's §3.2 named
"English **Laya** root" before this survey existed:

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

## Instrument calibration this pin requires — belongs to the pin, not to the test

The model card discloses two defects that bear directly on the protocol's instrument. **Both are
calibrated on dev only, before the pre-registration is sealed; their data is excluded from the
confirmatory test set; neither may be revisited after the confirmatory results are seen.**

**C1 — temperature refit.** The card states the model *"ships over-confident"* and that *"refitting one
temperature per (question type, option count) moves mean ECE 0.466 → 0.081"* on this checkpoint. The
gate `g_τ` and the `SilentError@τ` estimand both consume `c`; an uncalibrated `c` would make the
control-law measurement an artefact of the model's optimism. The refit is instrument setup.
**The protocol's §3.3 confidence *rule* is unchanged** (`c = max_j p_j` for choice, `c = max(p, 1-p)`
for noul); what changes is the distribution the rule is applied to, declared and frozen here.

**C2 — `noul` sanity.** The card warns that `noul` *"can follow its option labels instead of the
state"*, returning a confident "no" for clearly positive input (upstream issue #156), and documents a
workaround: ask the same question as a two-option `choice` with neutral keys. Phase I uses `noul` for
`ok` and `escalate`. **Changing the primitive changes what is measured**, so this is decided on dev by
measurement and frozen in the pre-run amendment.

## What this pin does NOT establish

- It is not evidence for any protocol hypothesis. It fixes the instrument; it says nothing about noise.
- It is **not** a comparability claim against any other model, hosted or local. Numbers from other
  systems may share a table and are never averaged or differenced.
- Its behaviour on this programme's item domain (§4.3 short service / routing intents) is
  **unmeasured**. The item bank is new; this checkpoint has never been scored on it.
- **No vendor figure on this page is evidence for a hypothesis.** The card's numbers are quoted to
  justify instrument setup. They are re-measured here or not used.

## Running the pin

```bash
pip install laya                            # Python 3.10+
export HF_ENDPOINT=https://hf-mirror.com    # this host reaches HuggingFace only via hf-mirror
# If the transformers import fails: a PYTHONPATH holding an unrelated venv can shadow site-packages
# on this host. Unset PYTHONPATH and retry before concluding anything about the environment.
```

**No training is involved and none is permitted on the confirmatory path** (protocol §8).

## What the revised pin retires, and what it does not

The earlier pin — `E:/2026-AI4S/calib/rsi_jev_v1_0_08b` and its code environment `E:/2026-AI4S/v1_env`
— is **superseded as the Phase I instrument**. Its measurements remain valid as a record of that
artefact: it was scored on this machine and reproduced its own published record to within one question
in 2,000, and the R1 archive holds that evidence. It is simply no longer what Phase I runs on.
