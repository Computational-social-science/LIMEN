# Phase I — Amendment 2 (filed before the confirmatory run)

**Filed:** 2026-10-04 · **Governing:** `protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md` v1.1
· **Amends:** `docs/PHASE_I_PREREGISTRATION.md`, `docs/PHASE_I_AMENDMENT_1.md`,
`docs/PHASE_I_ERRATUM_1_PI_D.md`, `docs/PREDICT_JSONL_RUNNER.md`, `docs/INSTRUMENT_POSTURE.md`

**Everything here is decided BEFORE the confirmatory run and before any confirmatory data exists.** Four
open questions are closed, and the reason each is closed is recorded so that a reader can reconstruct
the choice rather than infer it. **This is the last amendment before the seal.**

---

## B1 — DECLARED. The τ\* tie-break

### The defect

Protocol §4.4 fits `tau*` on dev to produce `Coverage@eps` and does not say **which** threshold is
reported when several meet the budget. **An admissible threshold is never unique.** Risk is monotone
non-increasing in τ — a stricter gate cannot accept more errors — so if τ meets the budget then every
τ′ ≥ τ meets it too. The admissible set is upward closed and therefore typically an interval with no
distinguished element.

**This was not hypothetical.** Amendment 1 §A3 hit precisely this situation: the pilot's clean
`SilentError@0.9` was **0/120**, so `Risk(τ) = 0` across the grid and **every** τ was admissible.

### The decision

**`tau*` := the LEAST admissible threshold.** Equivalently: the loosest gate whose accepted-error rate
fits ε.

**Why this choice and not another.** It is the only convention under which `Coverage@ε` is **maximised**
among admissible thresholds, so the reported coverage is the best coverage the budget permits — and the
gap between any other admissible choice and this one is **bounded by monotonicity**, not by luck. It is
also the least committal: it is the threshold closest to answering, so it reports the most behaviour.

### The mathematical content is now machine-checked

The `lean-nhb` project builds clean: **22 theorems, zero errors, zero `sorry`**, and every one of the
twelve is verified by Lean's own kernel via `#print axioms` (`scripts/check_lean_axioms.py`), which
fails on `sorryAx` — the axiom Lean substitutes for a proof it could not find. A grep for the literal
word would not do: it proves a string is absent, not that a theorem is proved.

**What is proved, and what is not.** Two results carry this rule:

| Result | Statement |
|---|---|
| `admissible_mono` | the admissible set `{tau : Risk(tau) <= eps}` is upward closed — so an admissible threshold is **never unique**, which is why a tie-break must be declared at all |
| `least_admissible_maximises_coverage` | among admissible thresholds, the **least** one maximises `Coverage@eps` |

**The second is the substantive one**, because it is what makes the rule *optimal* rather than merely
conventional. Getting it right required a correction that is worth recording: a first attempt took
`a <= b` as a hypothesis and left both `Admissible` hypotheses **unused** — Lean reported them as
warnings. That version was true but was not the claim: it said any threshold dominates any smaller
one, an ordering that holds for every pair whether or not either is admissible, and so said nothing
about admissibility. In the theorem above the ordering is **derived** from least-admissibility, which
is the only way the budget can do any work at all.

**One limit, stated rather than glossed.** `least_admissible_is_at_least_as_good` shows the guarantee
is a maximum, **not a strict maximum**: a stricter threshold can admit exactly as much when no
observation's confidence lies between the two. The rule must therefore be reported as "maximises
coverage among admissible thresholds", never as "maximises it strictly".

**What is NOT proved, and cannot be.** Nothing here says noise changes any of these quantities. Every
theorem follows from the protocol's definitions alone — a finite sample of (confidence, correct)
pairs, the confidence rule, and the gate. The empirical claim that orthographic noise moves the
rate–error curve is carried as a **named premise** in the manuscript, not as something a theorem can
establish. A formalization that asserted it would be proving the result by fiat.

**Authority for this section:** `docs/LEAN_FORMALIZATION_STATUS.md`. The tie-break rule itself is
unchanged by the formalization; what changed is that its justification is now machine-checked rather
than asserted.

### The zero-floor case is separately flagged, because it destroys the estimate's meaning

If `Risk(τ) = 0` for every τ in the grid, then **every τ is admissible and `tau*` is not identified by
the criterion at all.** In that situation:

1. `tau*` is reported as the least admissible threshold **together with** the flag
   `risk_identifiable: false`;
2. `Coverage@eps` for that condition is **not reported as an endpoint value** — it is reported as
   **undefined, with the reason** ("the gate accepts no errors at any threshold, so the budget does not
   select a threshold");
3. the one-sided 95 % **upper bound** on the noisy silent-error rate is reported instead, which is what
   Amendment 1 §A3 already committed to.

**A `Coverage@eps` of zero in this situation is a statement about the dev set, not about the model.**
It must never be read as "the model was perfectly selective."

---

## B2 — DECIDED. How `realised_edit_rate` enters the analysis

### The defect

`λ` is a **target mean** number of edits per character, not an achieved rate. Over the 1080-row
replay (`measurement/trials_pilot_replay.jsonl`):

| λ label | mean realised | median | min | max | SD |
|---|---|---|---|---|---|
| 0.00 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.05 | 0.0502 | 0.0473 | **0.0000** | 0.1310 | 0.0258 |
| 0.12 | 0.1148 | 0.1142 | 0.0339 | 0.2278 | 0.0355 |

The generator's mean is **calibrated** (+0.4 %, −4.4 %); the real feature is the **spread**. At λ = 0.05 an
item can receive **zero** edits, making that "noisy" trial **byte-identical** to its clean counterpart.

### The decision

**All three, not a choice between them:**

1. **The realised-rate distribution per λ is reported** alongside every λ effect.
2. **`realised_edit_rate` enters as a covariate**, with `λ` retained as the assigned factor — so the
   λ effect is estimated at the intended rate rather than at whatever was achieved on average.
3. **The share of trials with zero ops is reported per λ as its own quantity.** Those trials are
   **controls by accident** and must be visible, because at λ = 0.05 they are not a negligible minority.

**Decided before the run**, so it cannot be selected after seeing which choice gives the cleaner result.

---

## B3 — DECIDED. π_d is defined in the analysis code, not left implicit

**Per Erratum 1**, which found the pilot's figure had counted *relabels* — items wrong on both sides of
a pair — as discordant.

**The binding definition, to be implemented as code and cited in the analysis:**

> π_d is the proportion of items whose **binary outcome differs** between the two conditions being
> compared, i.e. (correct→wrong) + (wrong→correct), over the number of paired items.

**Every item-level breakdown reported alongside π_d must separate all four categories** — correct→wrong,
wrong→correct, relabel, unchanged — because collapsing them is exactly how the error arose.

**N is unchanged at `N_test = 652`, `bank = 932`.** Erratum 1 established that the π_d over-count pushed
N **upwards**, so the frozen value is conservative; the corrected π_d is 22/120 = 0.1833, requiring 574.

---

## B4 — DECIDED. `ok` and `escalate` are DROPPED from the confirmatory bank

### The basis

C2 measured the `noul` primitive's validity at the pinned revision (`docs/C2_NOUL_VALIDITY.md`):

| Method | separation | accuracy @ 0.5 |
|---|---|---|
| `noul` (as the protocol specifies) | +0.0766 | **0.5000** — exactly chance |
| the documented two-option workaround | **−0.1365** | 0.3333 — worse than chance, **inverted** |

On identical input the two methods disagree by up to **0.60**. A procedure that disagrees with its own
documented alternative is not measurement-stable regardless of whose labels are used.

### The decision

**The confirmatory bank carries `intent` only.** `ok` and `escalate` are not asked.

**Consequences, stated so they cannot be discovered later:**

- This is a **deviation from protocol §3.1**, which specifies a three-question Q0. It is disclosed here
  rather than presented as compliance.
- **The primary endpoints are unaffected.** `Accuracy` and `SilentError@τ` require gold, and gold exists
  only for `intent`; `Coverage@ε` gates on `intent`'s confidence. **H1.1 and H1.2 stand on `intent`.**
- `SilentError` and `Coverage` are therefore computed over **`intent` only**, and the manuscript says so.
- If a deferral-flavoured question is wanted later, it must be a **`choice`** with options such as
  `answer` / `ask for more information`, which is checkable against gold and uses the primitive that
  demonstrably works. That would be a **new** endpoint, added by a later amendment, never a substitution
  made after seeing results.

---

## What remains OPEN, and therefore what still blocks the seal

| Item | State | Needs |
|---|---|---|
| **O1** — λ levels | **OPEN** | The readability calibration must state **who reads** and **what counts as readable** before the ladder is scored. |
| **O3** — item bank content | **OPEN** | The content space is short of the 932 the frozen N requires (`docs/O3_BANK_DECISION.md`), and the resolution trades external validity against a frozen N. |
| **§12 item 4** — instrument pin | **FIXED** | Complete and verified; no longer blocking. |

**A4(3) — whether to weaken the `criteria` field — is resolved as RETAINED.** The protocol's §3.1 wire
format specifies per-option criteria; weakening them would change what the headline endpoint measures
and would invalidate the frozen N. The threat this creates is real and is documented rather than
removed: **0.8667 clean accuracy against the model card's 0.362**, likeliest because `criteria` names
each option's decision rule (`docs/REGISTERED_REPORT_STAGE1.md` §5.1). **Mitigation committed: a
template-confound probe measures whether accuracy depends on which template an item came from.** If it
does, the endpoint is partly lexical and the manuscript must say so.

---

## The seal condition

The pre-registration may be sealed when **O1 and O3 are frozen**. **No confirmatory data may be
collected before the seal**, and this amendment does not seal it.