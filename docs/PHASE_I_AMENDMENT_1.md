# Phase I — Amendment 1 (one-time, filed before the confirmatory run)

**Filed:** 2026-10-04 · **Governing document:** `protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md`
v1.1 · **Amends:** `docs/PHASE_I_PREREGISTRATION.md`

**The one-time rule.** The pre-registration's own terms permit each PENDING item to be frozen **once**,
by an amendment filed before the confirmatory run, **naming the measurement that set it**. This is that
amendment. It also carries one **correction**, which is a different act and is labelled as such: an
entry the pre-registration marked `FIXED NOW` was **wrong**, and a wrong fixed entry is more dangerous
than a pending one, because a pending entry announces itself and a wrong one does not.

Nothing here may be revised again after the confirmatory run begins.

---

## A1 — CORRECTION. The pinned instrument (§12 item 4) was the RETIRED checkpoint

**What the pre-registration said.** §12 item 4, status `FIXED NOW`:
`E:/2026-AI4S/calib/rsi_jev_v1_0_08b`; tower sha256 `60f8ea11…cff67`, scorer sha256 `22cb924e…11a06`,
directory manifest sha256 `f9dcc09b…b6675d2`.

**Why it is wrong.** That checkpoint belongs to the **RSI-Jev** object, which was retired by
`CURRENT_OBJECT.md`, and its artefacts were archived. The live Phase I instrument is a different model
entirely. The entry was not stale-by-omission; it affirmatively asserted the retired pin as frozen.

**Corrected entry.**

| | |
|---|---|
| Model | `convaiinnovations/laya` — English root |
| Hub revision used | `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851` (immutable commit sha; `main` is **not** the pin) |
| Licence | Apache-2.0 |
| Parameters / architecture | 421 M, ModernBERT-large encoder, non-autoregressive |
| Install | `pip install laya` |
| Status | **COMPLETE · VERIFIED AGAINST DISK** — all 5 files present with matching per-file SHA256 (846.20 MB total) |
| Authority | `docs/PHASE_I_PIN.md` · `config/pin_laya.json` |

**Status change, closed 2026-10-04.** This row previously read **CHOICE MADE · PIN INCOMPLETE**, with
confirmatory `predict → JSONL` recorded as **blocked** on the missing digests. The download has since
completed and the pin is no longer a claim but a **measurement**: every one of the five files was
re-hashed from disk and matched `config/pin_laya.json` byte for byte (846,195,574 B total;
`model.safetensors` = `891102d372688fc2…`). `scripts/check_pin_integrity.py` re-runs that comparison
and fails loudly on any drift, including the case where the snapshot is missing altogether.

**So the block is lifted.** What remains open for §12 item 4 is nothing about the instrument; the
remaining Phase I blocks are the O1 λ-calibration decisions, which are about the stimulus, not the tool.

**Disclosure.** This correction changes which artefact the programme runs on. It is disclosed here
rather than silently edited, because the previous pin appears in an earlier committed version of the
pre-registration and a reader of that commit must be able to see why it was replaced. The
**pilots already run** were executed on the Laya pin, not on the retired checkpoint — so the measurements
in A2 are consistent with the corrected entry, not with the wrong one.

---

## A2 — O2 RESOLVED. N_item is now frozen at the measurement that set it

**Measured inputs** (GPU pilot, pinned Laya English root, λ ∈ {0, 0.05, 0.12}, `noise_seed = 0`,
120 items, 360 trials, 0 failures; `measurement/pilot_results.json`, sha256 `f7373c79…`):

> **⚠️ ERRATUM — read `docs/PHASE_I_ERRATUM_1_PI_D.md` before using π_d from this table.**
> The π_d below was **over-counted** by including items that were wrong on **both** sides of the pair
> (so-called "relabels": the argmax moved to another non-gold option, leaving the binary outcome
> unchanged). **The McNemar-correct value is π_d = 22/120 = 0.1833**, requiring `N_test = 574`.
> **The frozen `N_test = 652` is nevertheless KEPT**, because in this formula a larger π_d demands a
> larger N, so the over-count pushed N **upwards** — the error is conservative, not under-powering.
> Found by an independent replay of the pilot through `measurement/run_phase1.py`, which reproduced the
> clean accuracy to the item (104/120, difference +0.0000) and the raw flip counts exactly.

| Quantity | Measured | Interval |
|---|---|---|
| π_d, clean → mid | **0.2083** (25/120) | Wilson 95% [0.145, 0.289] |
| π_d, clean → lo | 0.0833 (10/120) | — |
| clean accuracy (`intent`) | 0.8667 (104/120) | [0.794, 0.916] |
| clean SilentError@0.9 | **0.0000** (0/120) | upper 95% ≈ 0.025 |
| accuracy drop, clean → mid | 8.33 pp | — |

**Derivation, using the pre-registration's OWN formula.** Before trusting the result, the formula was
re-implemented from scratch and checked against the table already printed in the pre-registration
(§O2). It **reproduces that table exactly** — 0.06→186, 0.08→249, 0.10→312, 0.12→375, 0.15→469,
0.20→626 — so the number below is computed with the document's own convention, not a substitute.

```
N = ( z(1-α/2)·√π_d  +  z(power)·√(π_d − δ²) )² / δ²      α = 0.05 two-sided, power = 0.80, δ = 0.05
π_d = 0.2083  →  N = 651.71  →  N_test = 652
item bank  =  652 / 0.70  = 931.4  →  **932 items**  (30 % dev / 70 % test, split by item_id)
```

**Self-consistency check, and it holds:** at N = 652 the minimum detectable effect at 80 % power is
**5.01 pp** — the δ the design was built around. At the pilot's N = 120 the MDE is **11.67 pp**, which is
why the observed 8.33-pp drop was **not** significant at pilot size. That is stated so the pilot is not
later narrated as a finding.

**Frozen values.**

| Item | Frozen value |
|---|---|
| N_test | **652 items** |
| Item bank (with dev) | **932 items** |
| Dev / test share | 30 % / 70 %, split by `item_id` |
| δ (detectable mid-vs-clean error increase) | **5 absolute pp** |
| α, power | 0.05 two-sided, 0.80 |
| β (test) | McNemar, item as the unit |

---

## A3 — The τ = 0.90 endpoint has a ZERO FLOOR. This was analysed, and it is an advantage — NOT a blocker

**The observation.** Clean `SilentError@0.9` measured **0/120**. The pre-registration's SilentError
power table starts at a baseline of 0.02 and does not cover a baseline of 0. There is therefore no row
that applies, and N cannot be read off that table.

**The analysis.** With a clean baseline of exactly 0, the paired McNemar structure has only one
non-empty cell: an item can produce a silent error under noise but not under clean, never the reverse.
So the paired test **degenerates to a one-sided one-sample test** on the noisy count, and the question
becomes: how many items are needed to see a rise at all?

| Assumed true rise | N for 80 % power |
|---|---|
| 0.02 | 80 |
| 0.05 | 32 |
| 0.10 | 16 |

**Consequence for the frozen N.** At N = 652, an assumed true rise of only 0.02 yields an expected
**13.0** silent errors, and the probability of observing none is ≈ 0.0000. **The endpoint is therefore
well-powered, not untestable**, and the N of 652 — which was driven entirely by the accuracy endpoint —
is more than sufficient. **An earlier concern that τ = 0.90 might sit above where any errors live is
withdrawn here as incorrect.**

**What is still pre-committed, because a zero floor invites a specific abuse.** If the clean baseline is
0 and the noisy conditions also yield 0, the result is a **null with an informative bound**, and it is
reported as exactly that — the upper confidence bound on the rise, not a claim of absence. A null at
this endpoint may not be narrated as evidence that noise is harmless. The reported statistic is the
one-sided 95 % upper bound on the noisy silent-error rate.

**τ is not changed.** τ ∈ {0.80, 0.90} is protocol text (§12 item 7) and both values are reported
everywhere. `SilentError@0.8` carried signal in the pilot (2/120) while `@0.9` did not; reporting both is
therefore informative rather than redundant. A change of τ would be a change of the confirmatory
hypothesis, not of an instrument setting, and is not made here.

---

## A4 — RECORDED, NOT RESOLVED. Three measurements that change what the items measure

The pilot surfaced three facts that bear on **construct validity** — whether the `intent` endpoint
measures the understanding the claim is about. They are recorded here so that a later reader cannot
find them unmentioned. **The decision on the third is explicitly deferred to the programme owner.**

1. **Clean accuracy 0.8667 against the model card's claimed 0.362 for this checkpoint** — a 24-point
   gap; the measured value also exceeds the card's fine-tuned figure (0.766). The likeliest cause:
   the protocol's own §3.1 `criteria` field names each option's decision rule, which makes the
   intent task easy. The field is protocol-conformant. High accuracy **helps** power and **weakens**
   construct clarity — it must not be reported as evidence the instrument is strong.
2. **Gold was agent-assigned with no human pass.** If the same agent wrote items and assigned labels,
   items may be self-answering. `docs/ITEM_BANK_SPEC.md` already carries "gold labeller" as an open
   approval point; this measurement raises its priority.
3. **`criteria` retention — decision PENDING, owner's call.** Two options: **(a)** retain — conformant,
   easier, better-powered, weaker construct; **(b)** weaken to option names only — harder, cleaner
   construct, but requires **re-piloting to re-measure π_d, which would in turn re-open A2.**

**Why this is not resolved here.** Option (b) invalidates the N frozen in A2, and re-piloting is a new
measurement with its own cost. Choosing (a) or (b) is a scientific-judgement call with a deadline
attached, and it is the owner's. Whichever is chosen must be recorded **before** the confirmatory run,
because it determines what the headline endpoint means.

---

## A5 — What remains OPEN after this amendment

> **Posture correction (2026-10-04).** An earlier version of this table listed a temperature refit as
> **mandatory**. That was instrument *optimisation*, which this programme's rule forbids: the object of
> study is the **shipped** instrument's control law, and refitting `c` would measure a different one.
> The refit is **dropped**; the shipped map is **disclosed** instead. Full ruling:
> `docs/INSTRUMENT_POSTURE.md`.

| Item | State |
|---|---|
| **O1** — λ levels (§4.2) | **OPEN.** Needs the readability calibration: who reads, and what counts as readable, must be stated before the ladder is scored. |
| **O3** — item bank (§4.3) | **OPEN.** Four design approvals outstanding in `docs/ITEM_BANK_SPEC.md` (domain scope, option counts, bank size, gold labeller). Bank size is now **bound by A2 at 932**. |
| **§12 item 4** — model pin | **INCOMPLETE** (revision hash + per-file digests pending download; blocks confirmatory prediction). |
| **C2 -- the `noul` primitive** | **OPEN.** The pilot applied the shipped temperatures as-is and flagged that `escalate` noul is strongly confident-no. The remaining question is whether `noul` follows **the state or its labels** -- measurement validity, decided on dev. **C1 (a temperature refit) is DROPPED as instrument optimisation**; the instrument is used as shipped and its properties disclosed (`docs/INSTRUMENT_POSTURE.md`). |

**This amendment does not seal the pre-registration.** Sealing requires A4(3) to be decided, O1 and O3
to be frozen, and the pin to be completed. Until then the confirmatory run may not start.
