# Lean 4 formalization — status, honestly

**Project:** `E:/2026-AI4S/lean-nhb` (absolute path is deliberate: a relative link breaks when the
drives differ). **Toolchain:** `leanprover/lean4:v4.34.1`, Lean core only, **no Mathlib** — so the
artifact rebuilds offline in seconds with zero dependency resolution.

## STATUS: INCOMPLETE. It does not compile. No theorem is machine-verified.

```
source files          : 1  (NHB/PhaseI/Core.lean, 168 lines)
errors remaining      : 3      <- MEASURED 2026-10-04, not estimated
sorry / admit / axiom : 0      <- this is the part that must never be compromised
theorems machine-checked: 0
```

**Nothing in this project may be cited as evidence.** The reasoning that informed Amendment 2 §B1 was
done on paper and by measurement, not by this artifact.

## A correction to the previous version of this file

The earlier version of this record said **9 errors** and that the remedy was **`lake add mathlib`**.
Both claims were wrong, and wrong in the direction that would have led to a bad decision — adding a
dependency cycle to fix a problem that dependency does not have.

Measured on 2026-10-04:

- **3 errors, not 9.** Every one is a type or proof-script error in an otherwise coherent file.
- **Mathlib is not the remedy.** None of the three failures is a missing lemma. The statements are all
  provable in core; what failed was how the proofs were written.
- **One earlier failure was in the build configuration, not the mathematics.** `lakefile.toml` declared
  `globs = ["NHB", "vf.PhaseI.*"]` pointing at a module that does not exist, so the build failed before
  reaching any theorem. Corrected to `globs = ["NHB"]`, and the empty `vf/` and `probe/` directories
  were removed.

**An inaccurate status file is worse than an absent one**, because it is read as a decision input: this
one would have had someone spend a dependency-resolution cycle on what was a proof script.

## What the formalization is FOR

The protocol §4.4 fits `tau*` to produce `Coverage@eps` without saying which threshold is reported when
several meet the budget. The mathematics needed to close that is small and entirely definitional:

1. `Risk(tau)` and `Coverage(tau)` are monotone non-increasing in tau;
2. the admissible set `{tau : Risk(tau) <= eps}` is upward closed, hence an admissible tau is **never
   unique**;
3. a canonical threshold exists (one above every confidence admits nothing, so its Risk is 0);
4. **the least admissible threshold maximises coverage among admissible thresholds** — so the tie-break
   in Amendment 2 §B1 has a defensible optimum, and the understatement from any other choice is bounded
   by monotonicity rather than by luck;
5. an empty dev set is degenerate: every tau is admissible and coverage is 0 at all of them.

**Point 4 is the substantive one.** It is why the tie-break was declared rather than left open.

The file states all five, plus the identity that `SilentError@tau` and the accepted-error rate are the
same count — the one quantity, not two, that the noisy-channel framing (`P_e`) and the protocol's
estimand both name. **The statements are correct; only the proofs are incomplete.**

## Why it is not finished — stated as a process failure, not a technical one

**The obstacle is one tactic's normalised form, and it was met with eight guesses.**

The guards in `Risk` are `decide` applications, so `by_cases` branches on an *equality to true* rather
than on a proposition, and `simp` normalises a guard before matching a hypothesis against it. The
correct sequence was **measured early, in a standalone file**:

```
simp only [decide_eq_true_eq, Bool.and_eq_true]   -- normalises the guard to a Prop conjunction
```

That experiment succeeded. The eight iterations that followed each guessed a different tactic form
against the real file instead of writing three-line experiments, and **two of them introduced errors
rather than removing them** — a `Bool.and_eq_true.mp` projection that does not exist in Lean 4.34.1, and
a bare `show` whose pattern does not match the goal.

**The failure mode is the project's own: an artefact edited until the tool stops complaining, with the
tool's exit status treated as the objective.** It is the same shape as every "the build exited 0 and the
page was wrong" defect in this project's history, and it is why the work was handed to a subagent under
an explicit instruction to work in a throwaway file and to write a minimal example before guessing.

**Adding Mathlib would not have prevented this.** A larger lemma set would have made it easier to stop
and guess, because there would always be another name to reach for.

## The three remaining failures, stated so they can be finished

| Where | Failure |
|---|---|
| `risk_mono`, cons branch | after `by_cases` on the normalised guard and `ite_true`, the goal is arithmetic that `omega` cannot close |
| `top_admissible` | `Nat.le_add_right` is instantiated against thresholds `max a.c (maxC rest) + 1` and `maxC rest + 1`; the monotonicity step needs `maxC rest + 1 <= max a.c (maxC rest) + 1` stated explicitly, and the head `if` resolved first |
| `empty_dev_is_degenerate` | `Nat.le_trans` yields `Risk tau [] = 0` where `Risk tau [] <= 0` is required |

All three are proof-script defects. **None requires changing a theorem statement**, and changing one to
get a green build would destroy the reason to formalize anything.

## The discipline that matters more than the theorem count

Four defects were found during this attempt, and they are the reason to keep the project at all:

1. **A `sorry` was written into a draft file.** It was detected by a tree-wide scan and the file was
   deleted rather than patched, because Lean compiles a file containing `sorry` into a usable `.olean` —
   a proof checker that goes green on a `sorry` is precisely the failure it exists to prevent.
2. **`Nat.find` was assumed present.** It lives in Mathlib/Std, not core. The assumption was wrong and
   the design changed.
3. **`Bool` and `Prop` were mixed** (`!o.correct` in a position expecting a proposition), producing a
   cascade of errors whose first message pointed nowhere near the cause.
4. **The status file itself was wrong** — 9 errors against a measured 3, and a remedy aimed at the wrong
   layer. Recorded here rather than quietly edited, because the error was in a record meant to guide a
   decision.

**None of these is a mathematical problem, and all four would have shipped silently under a weaker
workflow.** That is the argument for machine-checking this file at all — and equally the argument
against claiming its results before it compiles.