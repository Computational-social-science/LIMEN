# Phase I — Pilot Measurement Report (Laya English pin)

**Status: PILOT. Instrument calibration data — EXCLUDED from the confirmatory test set**
(protocol §4.3 / pre-registration O2; "pilot items … are excluded from the confirmatory test set").

**Governing documents:** protocol `NHB_Orthographic_Channels_JEV_Research_Protocol.md` v1.1 (§3.1–3.4,
§4.1–4.4, §6); pre-registration `PHASE_I_PREREGISTRATION.md` O2; `ITEM_BANK_SPEC.md`; `PHASE_I_PIN.md`.

**Purpose.** Measure the two numbers O2 requires before the pre-registration can be sealed:
the discordance rate **π_d** (clean → mid) and the **clean-baseline `SilentError@0.9`** of the pinned
artefact, on a purpose-built pilot bank. Nothing here tests H1.1–H1.3; no hypothesis claim is made.

---

## 1. What was run

| Field | Value |
|---|---|
| Model | `convaiinnovations/laya` — English root checkpoint (the pinned artefact) |
| Revision | `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851` (the package's reviewed SHA; also the local cache snapshot) |
| Environment | `laya 0.3.26`, `torch 2.13.0+cu126`, Python 3.14.5, NVIDIA GeForce RTX 4070 (CUDA), bf16 autocast per checkpoint config |
| Call path | `Router(device="cuda", revision=<SHA>)` → `agent = router.load("english")` → **`router.predict(state, Q0)` — one state per call** (protocol runbook step 4; the canonical single-call shape) |
| Noise | `measurement/typo_noise.py` (N_en), deterministic in `(item_id, λ, seed)`; **λ ∈ {0, 0.05, 0.12}, seed = 0** |
| Questions | Q0 per §3.1: `intent` (`choice`, per-item 2–4 options + criteria), `ok` (`noul`), `escalate` (`noul`) |
| Confidence rule | §3.3 applied by the analyst to the returned probabilities: choice `c = max_j p_j`; noul `c = max(p, 1−p)` |
| Constraints honoured | No training, no fine-tuning, no temperature refit, no weight modification; local only; no API key; existing files untouched |
| Trials | 120 items × 3 λ = **360 trials, 0 failures, 0 exclusions, 0 truncations** (checked per-trial `usage.truncated`); every trial sits on `routing.model == "english"` |

**Exact commands** (this host reaches HuggingFace only via hf-mirror; `PYTHONPATH` unset defensively;
scripts live outside the repo, in the Hermes scratch dir `…/hermes/cache/scratch/pilot_laya/`):

```bash
unset PYTHONPATH
export HF_ENDPOINT=https://hf-mirror.com
C:/Python314/python.exe …/scratch/pilot_laya/build_bank.py    # writes measurement/pilot_items.jsonl (BEFORE any model call)
C:/Python314/python.exe …/scratch/pilot_laya/score_pilot.py   # 360 trials → scratch/pilot_trials.jsonl
C:/Python314/python.exe …/scratch/pilot_laya/analyze_pilot.py # writes measurement/pilot_results.json
```

Runtime (measured): checkpoint load ≈ 8 s (import + `load("english")`, warm local cache); 360 trials
≈ 10.5 s (≈ 0.03 s/trial). Re-prediction determinism check: 3 (item, λ) pairs
re-run at the end of the session — answers identical in all 3.

**Artefacts.** `measurement/pilot_items.jsonl` (sha256 `21a18e39c0323648e1daea8b0b119f93466107f9f0d8b07c3234fbde42c37e83`,
120 lines) · `measurement/pilot_results.json` (full trial records + metrics + this pilot's O2 inputs).

---

## 2. Item bank construction — and the mandatory disclosure

**Structure (per ITEM_BANK_SPEC.md §1–2).** 120 items; 30 per domain (billing, access, urgency, info);
option counts 40 × two-option / 40 × three-option / 40 × four-option, identical distribution in every
domain; options listed in canonical order so gold position is not fixed; expected chance accuracy
(mean 1/K) = **0.3611**. Fields: `item_id`, `state`, `domain`, `intent`, `intent_gold`, `ok`, `escalate`.

**Construction rules (pilot codebook, applied to every accepted item).** (a) single-cue rule: each state
contains the decisive cue of exactly one domain and no cue of another; (b) urgency items all contain an
explicit escalation request or a stated deadline (spec codebook item 3), usually plus an incident
context; (c) billing/access/info items carry no deadlines; (d) gold = the domain of the decisive cue,
locked in the file **before any model call on the bank**.

**Disclosure (ITEM_BANK_SPEC.md approval point 4 — mandatory).** Gold labels were assigned by an **AI
agent** (Hermes subagent), not by a human annotator. There is **no human pass** for this bank and
therefore **no human inter-annotator agreement statistic**. What stands in its place is a second pass:
(1) an automated single-cue audit over all 120 items — 0 violations; (2) a full manual re-read by the
same agent against the codebook — 2 items were clarified for decisiveness before freeze (one timing
clause, one weak urgency marker), after which the bank was frozen. A human second annotator is
required before any confirmatory use of these items or of this construction method.

**Rejections: 12 candidate items (≈ 9% of the 132 drafted) were rejected for arguable gold** — applied
per spec §4: "ambiguity is a rejection, not a tiebreak". Reasons, in brief:

| # | Candidate (abridged) | Rejected because |
|---|---|---|
| 1 | card charged twice … "before my statement closes on Friday" | billing action + stated deadline; subject rule vs deadline rule both apply |
| 2 | "Where can I download last month's invoice …?" | question about a billing artefact; info vs billing both defensible |
| 3 | cannot sign in because the card expired / account suspended | access failure with billing root cause |
| 4 | site down "including the billing portal, so nobody can pay invoices" | outage + billing actions; urgency vs billing |
| 5 | "Please escalate my refund request …" | escalation of a billing action; urgency vs billing |
| 6 | team locked out "and the project deadline is this Friday" | access action + stated deadline; access vs urgency |
| 7 | reset email "mentions a different account name. Is that normal?" | access defect phrased as a general question; access vs info |
| 8 | "security questionnaire … before the vendor audit next month" | deadline present but no domain owns the work; no decisive cue |
| 9 | "cannot receive email … and our invoices to customers are stuck" | outage + billing artefact; urgency vs billing |
| 10 | "upgrade our plan and bill the difference … today" | billing action + same-day directive; billing vs urgency |
| 11 | refund status + payment policy copy in one request | multi-subject (billing + info) |
| 12 | "login page is extremely slow for everyone today" | availability complaint; access vs urgency (no deadline, no escalation) |

These 12 are recorded so the pilot's gold-selection discipline is inspectable, not asserted.

---

## 3. Measured results (real numbers, 360 trials)

**Headline (question `intent`, item = unit):**

| Metric | clean (λ=0) | lo (λ=0.05) | mid (λ=0.12) |
|---|---|---|---|
| Accuracy | **104/120 = 0.8667** | 102/120 = 0.8500 | **94/120 = 0.7833** |
| 95% Wilson CI | [0.7944, 0.9162] | — | [0.7015, 0.8476] |
| SilentError@0.8 | 2/120 = 0.0167 | 1/120 = 0.0083 | 3/120 = 0.0250 |
| **SilentError@0.9** | **0/120 = 0.0000** | 0/120 = 0.0000 | 1/120 = 0.0083 |
| items answered at c ≥ 0.9 | 50 | 38 | 34 |
| items answered at c ≥ 0.8 | 69 | 58 | 48 |

Chance floor = 0.3611 → **clean accuracy sits +50.6 pp above chance**.

**Δ accuracy:** clean → mid = **−8.33 pp** (0.8667 → 0.7833); clean → lo = −1.67 pp.
(The observed mid-vs-clean drop exceeds the 5-pp effect the design anticipates.)

**π_d (discordance of `intent` argmax):**

| Contrast | π_d | flips (n=120) | right→wrong | wrong→right | wrong→wrong relabel |
|---|---|---|---|---|---|
| **clean → mid** | **25/120 = 0.2083** | 25 | 16 | 6 | 3 |
| clean → lo | 10/120 = 0.0833 | 10 | 6 | 4 | 0 |
| lo → mid | 27/120 = 0.2250 | 27 | — | — | — |

Wilson 95% CI on π_d(clean→mid): **[0.1453, 0.2895]**.

**The two SilentError@0.8 clean cases** were `pilot_access_15` and `pilot_access_19` — both access
items answered "urgency" with c ≥ 0.8. At λ=0 **every one of the 50 items answered at c ≥ 0.9 was
correct** (that is what SilentError@0.9 = 0 means concretely).

**Breakdowns (accuracy / π_d clean→mid):**

| Group | clean | lo | mid | π_d |
|---|---|---|---|---|
| billing (n=30) | 0.9667 | 1.0000 | 0.9000 | 0.1333 |
| urgency (n=30) | 0.9333 | 0.9333 | 0.8667 | 0.1333 |
| info (n=30) | 0.9000 | 0.8333 | 0.8000 | 0.1667 |
| **access (n=30)** | **0.6667** | 0.6333 | 0.5667 | **0.4000** |
| k=2 options (n=40) | 0.9250 | 0.9000 | 0.8500 | 0.1250 |
| k=3 options (n=40) | 0.8000 | 0.8000 | 0.7750 | 0.1750 |
| k=4 options (n=40) | 0.8750 | 0.8500 | 0.7250 | 0.3250 |

The access domain is the pin's weak spot (mostly misrouted to "urgency"), and discordance grows with
option count. Both are descriptive; domain and option count are not hypothesised factors.

**Secondary — `noul` questions (no gold locked; descriptive only).** `ok` (p "clear enough"): mean
0.409 → 0.351 → 0.291 across λ; share c ≥ 0.9 = 0.083/0.150/0.200. `escalate` (p "yes"): mean
0.161/0.161/0.174; share p ≥ 0.5 = 0.042/0.058/0.108, but **share c ≥ 0.9 = 0.45/0.42/0.64** — i.e.
the `escalate` head is frequently very confident, mostly on the "no" side. This bears on pin item C2
(the card's `noul` label-following caveat) but cannot adjudicate it without noul gold; it flags the
dev-stage measurement C2 already schedules.

---

## 4. The two O2 inputs, and the N they imply

**Measured inputs (this pilot):** π_d(clean→mid) = **0.2083**; clean `SilentError@0.9` = **0.0000**
(0/120; exact 95% upper bound by the rule of three ≈ 2.5%).

**Implied test-set N** (pre-registered formulas, verified below against both pre-reg tables):

| Requirement | Formula value | N (ceil) |
|---|---|---|
| McNemar, δ = 5 pp, from measured π_d = 0.2083 | 651.7 | **652** |
| McNemar, from π_d(clean→lo) = 0.0833 (context) | 259.3 | 260 |
| SilentError endpoint, at measured baseline 0.0000 (formula extrapolated below the table floor) | 151.9 | 152 |
| SilentError endpoint, at the table's floor baseline 0.02 (conservative reading) | 268.7 | 269 |
| **max of the two requirements** | **651.7** | **652** |
| **bank size at 70/30** (`⌈max / 0.7⌉`) | — | **932** |

So the pilot points at **≈ 652 test items / ≈ 932 total bank** for 80% power on a 5-pp mid-vs-clean
error increase, driven by the mid-condition discordance rate. The π_d sampling uncertainty matters:
using the CI bounds [0.1453, 0.2895] the implied N spans **[454, 906]** test items — the amendment
should budget with that width in mind, not with the point estimate alone.

**Formula checks against the pre-registration tables** (they reproduce the documents' own numbers;
differences ≤ 3, from rounding in the source tables):

- McNemar table: 0.06→186.0 (pre-reg 186); 0.08→248.8 (249); 0.10→311.6 (312); 0.12→374.4 (375);
  0.15→468.6 (469); 0.20→625.5 (626).
- SilentError table: 0.02→268.7 (266); 0.05→434.4 (432); 0.08→588.9 (587); 0.12→777.3 (775).

**Two pre-registration points the pilot surfaces for the amendment:**

1. **Sentence/table direction.** O2's text says the SilentError requirement *"rises as the clean
   baseline falls"*, but its table shows the requirement **rising with the baseline** (0.02→266 …
   0.12→775), and the table is what the pooled two-proportion formula produces (verified above). The
   sentence and the table point in opposite directions; the table governs interpretation, but the
   inconsistency should be corrected in the sealed text.
2. **Baseline at the floor.** The measured clean baseline is 0/120, below the table's smallest entry
   (0.02). Either reading (formula at 0 → 152; table floor → 269) is *smaller* than the McNemar
   requirement, so the choice does not change the combined N — but the extrapolation should be stated,
   not hidden.

**Is a 5-pp drop detectable at the pilot's size?** Plainly: **No — not at N = 120.** With the measured
π_d = 0.2083, the minimum detectable effect at N = 120 (McNemar, two-sided α = 0.05, 80% power) is
**11.56 pp**, and the achieved power for a 5-pp drop is **0.222**. The pilot was a calibration sample for
setting N, not an N that can carry the test. What the pilot *does* settle is the other half of the
question: clean accuracy is **not** near chance — it is 0.8667 against a 0.3611 chance floor, with the
CI lower bound still ≈ 43 pp above chance, so a 5-pp drop is a meaningful, floor-free effect to
chase; the operative constraint is sample size, not a pin that cannot move.

---

## 5. Instrument notes — where the tool did (and did not) behave as the protocol assumes

1. **Per-option probabilities ARE reachable** (the task's conditional): `answers["intent"]["probabilities"]`
   returns the per-option distribution, rounded by the package to 4 dp; `answers["ok"]["noul"]` /
   `answers["escalate"]["noul"]` return p(true), from which the two-point distribution is exact. The
   frozen §3.3 rule was applied by the analyst to these values; a cross-check against the package's own
   `answer_confidence`/`confidence` fields found 0 discrepancies beyond the 4-dp rounding. The 4-dp
   rounding is the only precision loss and is immaterial here (0 argmax/field contradictions across 360
   trials). A strict reading of §3.5's `p` field needs the *returned* probabilities — they exist.
2. **Single-call vs batched path are not numerically identical.** A batch-of-6 run of the same state
   gave probabilities differing from the single `predict` result in the 4th decimal (bf16 padding
   effects; argmax unchanged). This pilot therefore used the canonical **per-state `router.predict`**
   call for every trial. The confirmatory runbook should either do the same or explicitly pin the batch
   path before the run.
3. **The checkpoint ships a temperature map that the package applies** (choice:2 = 1.9064,
   choice:3–5 = 1.7602, noul:2 = 1.9834 — all softening). All numbers above use the shipped map,
   unmodified. The package also **warned** that the `choice:11+` bucket (not used here; option counts
   are 2–4) is outside its clamp range and was clamped — no effect on this pilot, but any future
   wide-option question should not trust that bucket.
4. **C1 (temperature refit) was NOT performed** (explicitly out of scope for this pilot). The measured
   `c` distribution above is the *unrefit* one; the pin document's scheduled refit will move
   p/c values and must be frozen before confirmatory use. The SilentError@0.9 baseline measured here is
   conditional on the shipped map.
5. **Clean accuracy vs the model card.** The card's 0.362 figure is for the four typed-decisions
   workflows; this bank measures a single 2–4-way routing decision and is not comparable. Item novelty
   against training corpora was **not** audited (no access); a dev-stage contamination cross-check is
   recommended before the confirmatory bank is finalised — this is a stated limitation, not a claim.
6. **Probe precedent.** Tooling-probe states were scored around this run (a `predict` smoke test before
   the bank was authored, a timing probe after scoring finished), some of them thematically similar to
   a few bank items. Inference is stateless (no memory across calls; no training), so there is no
   leakage channel, and pilot items are excluded from the confirmatory set regardless. Noted for
   completeness.
7. **Routing behaved as pinned.** All 360 trials routed to `english` / `convaiinnovations/laya`
   ("English Latin text"); no trial fell to another checkpoint, and no state was truncated at any λ.
8. **Cross-record agreement (concurrent workstream).** Written during this pilot by a parallel
   workstream, the programme's pin record (`config/pin.json`, `docs/PREDICT_SMOKE_TEST.md`) resolves the
   same revision (`55cf4c4e…`), the same package versions, and the same 4-dp probability fact, and
   independently marks C2 (`noul` label-following) as a mandatory pre-confirmatory calibration. No
   conflict with anything recorded here.

---

## 6. FAILURES log

- Failed trials: **0** (nothing to exclude). Truncated states: **0**. Routing anomalies: **0**.
- Construction-time exclusions: the **12 rejected candidates** (§2) and **2 pre-freeze clarifications**;
  both recorded here as required.
- Known external caveats: pilot measured at **seed 0 only**; the confirmatory policy uses seeds
  {0, 1, 2}, and per-item discordance across seeds can only be ≥ the seed-0 figure — the amendment
  should fix the seed structure the McNemar test runs on. Gold is **agent-assigned, single-pass** (§2);
  a human re-annotation pass is required before confirmatory use.

## 7. What this pilot does NOT establish

No hypothesis is tested here; no claim about noise effects, about other checkpoints, or about writing
systems; no external validity beyond this bank, this pin, λ ∈ {0, 0.05, 0.12}, seed 0. Its only outputs
are the O2 design inputs, the instrument notes above, and the frozen pilot record.
