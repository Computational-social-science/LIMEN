# Lean 4 formalization — status, honestly

**Project:** `E:/2026-AI4S/lean-nhb` (absolute path is deliberate: a relative link breaks when the
drives differ). **Toolchain:** `leanprover/lean4:v4.34.1`, Lean core only, **no Mathlib** — so the
artifact rebuilds offline in seconds with zero dependency resolution.

## STATUS: INCOMPLETE. It does not compile. No theorem is machine-verified.

```
errors remaining: 9
sorry / admit / axiom: 0      <- this is the part that must never be compromised
theorems machine-checked: 0
```

**Nothing in this project should be cited as evidence.** The reasoning that informed Amendment 2 §B1
was done on paper and by measurement, not by this artifact.

## What the formalization was FOR

The protocol §4.4 fits `tau*` to produce `Coverage@eps` without saying which threshold is reported when
several meet the budget. The mathematics needed to close that is small and entirely definitional:

1. `Risk(τ)` and `Coverage(τ)` are monotone non-increasing in τ;
2. the admissible set `{τ : Risk(τ) ≤ ε}` is upward closed, hence an admissible τ is **never unique**;
3. a canonical threshold exists (one above every confidence admits nothing, so its Risk is 0);
4. **the least admissible threshold maximises coverage among admissible thresholds** — so the tie-break
   in Amendment 2 §B1 has a defensible optimum, and the understatement from any other choice is
   bounded by monotonicity rather than by luck;
5. an empty dev set is degenerate: every τ is admissible and coverage is 0 at all of them.

**Point 4 is the substantive one.** It is why the tie-break was declared rather than left open.

## Why it did not finish

**The obstacle is tooling friction, not mathematical difficulty.** Most of the remaining errors are
`omega` failing on goals containing `decide`, plus case-split hygiene in Lean core without Mathlib's
lemma set. Three drafts were attempted, each restructuring the definitions to reduce the friction —
the final one routes every conditional over `Nat` so that `if` compiles to code and no
`Classical.propDecidable` is needed.

**A fourth attempt was started and abandoned.** The agent stopped after three attempts on one file, per
the `lean-formalizing-empirical-claims` rule, and the project was left in this state rather than
iterated further at the owner's token cost.

## The fix, if this is resumed

**Allow Mathlib.** `lake add mathlib` is a single dependency, and it supplies `Nat.find`,
`List.filter_le`-style lemmas and case-split automation — which is where every remaining error lives.
**The expected outcome is that most of the statements above collapse to one or two lines each.**

The alternative is to keep core-only and ship a **partial** proof containing only what core can
discharge, with the rest listed explicitly as unproved. That is honest but weaker, and the weak version
proves little that the specification does not already state.

## The discipline that matters more than the theorem count

Three defects were found and fixed during this attempt, and they are the reason to keep the project at
all:

1. **A `sorry` was written into a draft file.** It was detected by a tree-wide scan and the file was
   deleted rather than patched, because Lean compiles a file containing `sorry` into a usable `.olean`
   — a proof checker that goes green on a `sorry` is precisely the failure it exists to prevent.
2. **`Nat.find` was assumed present.** It lives in Mathlib/Std, not core. The assumption was wrong and
   the design changed.
3. **`Bool` and `Prop` were mixed** (`!o.correct` in a position expecting a proposition), producing a
   cascade of errors whose first message pointed nowhere near the cause.

**None of these is a mathematical problem, and all three would have shipped silently under a weaker
workflow.** That is the argument for machine-checking this file at all — and also the argument against
claiming its results before it compiles.