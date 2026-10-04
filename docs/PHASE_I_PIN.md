# Phase I — Pinned System One Artefact

**Status:** pinned and independently verified on this machine, 2026-10-04.
**Protocol requirement:** §3.2 ("pin **one** English-capable System One artefact"), §12 checklist item 4
("Model ID + commit + SHA256").

---

## The pinned artefact

```
E:/2026-AI4S/calib/rsi_jev_v1_0_08b
```

| Field | Value |
|---|---|
| Kind | Open System One typed-decision release, v1.0, 0.8B scale |
| Base model | `Qwen/Qwen3.5-0.8B-Base` (recorded in the release's own `meta.json`) |
| Files | 37 |
| Total bytes | 2,022,019,536 |
| **Directory manifest sha256** | `f9dcc09b07a903d9f2c77b85b2d09b41a6cee6d4ac70a8910d0d99357b6675d2` |

**Weights — the load-bearing hashes**

| File | Bytes | sha256 |
|---|---|---|
| `tower.safetensors` | 1,992,487,680 | `60f8ea114a6dc3070be268a1f95973b503bd300b2965555f8acad2d95cfcff67` |
| `scorer.safetensors` | 29,393,884 | `22cb924e0eb9432db467539e18df48ba837a09eee1106b94f04a21b430c11a06` |
| `meta.json` | 1,329 | `2dbae889af349197429e924865abd79a…` |
| `verify.json` | 1,866 | `c99b52a53bb3a170859f8cb8fe92ec54…` |

## Why this artefact

It is the only genuine System One **checkpoint** on this machine. The other local candidates are
backbones without a trained readout (`Qwen3.5-0.8B-Base`, `Qwen3-0.6B`), and the published 2B release
directory (`v1_published/v1_2b`, 31 MB) carries metadata and code but **no weights**.

It also carries what the protocol's Rule-4 placement and §12 checklist ask for: **its own published
record, with an independent reference number.**

## The verification that is already done

The release ships a `verify.json` stating, for each of three evaluations, both the recorded score and
`agreement_with_record`:

| Evaluation | pooled_top1 | n | agreement_with_record |
|---|---|---|---|
| `typed_decisions/canonical` | **0.6175** | 2,000 | **1.0** |
| `typed_decisions/reversed` | **0.6210** | 2,000 | **1.0** |
| `mmlu_pro_1k/canonical` | **0.2690** | 1,000 | **1.0** |

On this machine, our own harness reproduced `typed_decisions/canonical` as **0.6180** against the
recorded 0.6175 — a difference of **one question in 2,000**. That measurement is recorded in
`archive/R1_jevrsi_loop_objective_2026-10-04/` and in the commit history. It is the pin-and-verify
step of §3.2, discharged before any noise is applied.

**The known residual is a kernel-stack difference, and it is measured, not speculated:** the release
was produced with a fused linear-attention kernel; this machine falls back to a torch implementation.
The gap on 2,000 questions is **0.05 pp**. The source's own guidance is that its numbers compare
within one kernel stack — so this pin is compared to itself and to nothing else.

## What "forced on English" means here

The protocol permits "a multilingual checkpoint forced on English" and requires only that one artefact
be pinned (§3.2). This artefact is used on English states only, exactly as pinned. The router-language
question is a Phase II mechanism arm (§5.4) and is not touched in Phase I.

## What this pin does NOT establish

- It is not evidence for any protocol hypothesis. It fixes the instrument; it says nothing yet about
  noise.
- It is not a claim of comparability with any other System One artefact, published or local.
- Its English behaviour on this programme's item domain (§4.3: short service / routing intents) is
  **unmeasured**. Phase I's item bank is new; the pinned artefact has never been scored on it.

## Running the pin

The inference path is the v1.0 code environment that accompanies the release
(`E:/2026-AI4S/v1_env`), whose `predict(state, questions) -> probs, conf` behaviour is what the
protocol's §3.1 wire format expects. **No training is involved and none is permitted on the
confirmatory path** (protocol §8).
