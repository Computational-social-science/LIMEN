# C2 — the `noul` primitive's validity, measured

**Question.** The protocol's Q0 asks `ok` and `escalate` as `noul` questions. The instrument's card
warns that `noul` can *"follow its option labels instead of the state"*, returning a confident "no" for
clearly positive input, and documents a workaround: ask the same question as a two-option `choice` with
neutral keys. **Does either method measure the state?**

**Why this is inside the pipeline's remit.** If the primitive does not measure what the protocol's §3.1
wire format says it measures, every number computed from it is void. That is measurement **validity**;
it is not instrument **quality**, and it is therefore not the tuning this programme forbids
(`docs/INSTRUMENT_POSTURE.md`).

**Script:** `measurement/c2_noul_validity.py` · **Record:** `measurement/c2_noul_validity.json` ·
**Instrument:** pinned `55cf4c4e…`, one model load, each probe asked in both forms on **byte-identical
state text** so any difference is the primitive and not the input.

---

## Result

Twelve probes whose intended answers are not in doubt (6 unambiguous-and-actionable, 6
missing-the-information), asked the same question — *"Is the request clear enough to act on?"* — two
ways.

| Method | mean p(true), actionable probes | mean p(true), vague probes | separation | accuracy @ 0.5 |
|---|---|---|---|---|
| **`noul`** (as the protocol specifies) | 0.5145 | 0.4379 | **+0.0766** | **0.5000** |
| **workaround** (two-option `choice`, neutral A/B) | 0.5752 | 0.7116 | **−0.1365** | **0.3333** |

**Neither method separates the two sets.**

- **`noul` scores exactly chance** — 6 of 12 correct, separation 0.077. It is not measuring the
  distinction the question names.
- **The documented workaround does worse than chance and in the wrong direction**: it rates the **vague**
  probes *higher* on "clear enough to act on" than the unambiguous ones (−0.1365 separation, 0.333
  accuracy). A method that inverts the ordering is not a repair for a method that is merely flat.

**Individual cases, which are harder to dismiss than a summary statistic:**

| Probe | State (abridged) | `noul` p(true) | workaround p(A) |
|---|---|---|---|
| `pos_04` | *"production service is returning errors for every request since 09:15… Please escalate this now"* | **0.1725** | **0.2979** (argmax **B** = lacks information) |
| `neg_06` | *"Things are not as they should be. Let me know."* | 0.2098 | **0.8077** |
| `neg_03` | *"I have a problem. Please advise."* | 0.2475 | **0.7418** |

**The card's warning is confirmed in kind**: an unambiguous, urgent, self-contained request was scored
as *not* actionable by both methods. And the two methods **disagree with each other** on identical
input by up to **0.60** (`neg_06`: 0.21 vs 0.81), which is a conflict, not merely noise.

## What this means for Phase I

**The two affected questions are `ok` and `escalate`.** Both are `noul`. **Their measurements cannot be
trusted at the pinned revision.**

**The primary endpoint is NOT affected.** `Accuracy` and `SilentError@τ` both require gold, and gold
exists only for `intent`; `Coverage@ε` gates on `intent`'s confidence. **`intent` is a `choice`
question**, and it behaves: an independent replay reproduced the pilot's clean accuracy **to the item**
(104/120, difference +0.0000), and the smoke test showed sensible separation with `c` from 0.33 on a
deliberately vague item to 0.99 on an obvious one. **H1.1 and H1.2 stand on `intent` and are unaffected
by this finding.**

**So the finding is bounded and it is actionable:** the confirmatory bank should either **drop `ok` and
`escalate`**, or **carry them as `choice` questions with symmetric, semantically-named options whose
answer is checkable**, or **keep them and report them as invalid** — and the choice must be made now,
before the bank is built, because it changes the bank's shape.

**A recommendation, marked as a recommendation.** Drop them. They contribute nothing to H1.1–H1.3, and
carrying a question whose primitive is known not to measure its construct adds a liability without
adding an endpoint. If a deferral-flavoured question is wanted later, it belongs as a `choice` with
options like `answer` / `ask for more information`, which is checkable against gold and uses the
primitive that demonstrably works.

## Honest limits — and they are substantial

1. **The labels are the author's judgment.** "Is this clear enough to act on?" was answered by me for
   twelve probes. If my ground truth is wrong, the measured separation is wrong. **This is the load-
   bearing weakness of the test.** It is partly mitigated by the **cross-method disagreement**, which
   does not depend on my labels at all: on identical input the two procedures returned answers differing
   by up to 0.60, and a procedure that disagrees with its own alternative cannot be measurement-stable
   regardless of whose labels are used.
2. **Twelve probes is a validity screen, not a calibration.** It is enough to reject a primitive that
   scores at chance; it is not enough to characterise the failure surface, and no effort should be spent
   characterising it — under the admission test, a component that fails is **replaced, not repaired**,
   and here the *question* is what gets replaced.
3. **One question was tested** (`ok`). `escalate` was not run. The card's warning is about the `noul`
   primitive, not about one question, so the finding is expected to generalise — but **that is an
   inference, and it is labelled one.**
4. **The workaround was implemented as documented** (two-option `choice`, neutral keys, meaning in the
   criteria). A different phrasing might do better. **Testing further phrasings would be instrument
   tuning, which this programme does not do**; the correct response to a failing component is to stop
   using it.
