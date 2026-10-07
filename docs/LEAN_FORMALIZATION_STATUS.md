# Lean 4 formalization — status

**Project:** the sibling repository `lean-nhb` (next to this one; override with `$NHB_LEAN_ROOT`). **Toolchain:** `leanprover/lean4:v4.34.1`, Lean core only, **no Mathlib** — so the
artifact rebuilds offline in seconds with zero dependency resolution.

## STATUS: COMPLETE AND MACHINE-VERIFIED

```
source files          : 2  (lean-nhb: NHB/PhaseI/*.lean, 591 lines)
lake build            : Build completed successfully (4 jobs)
errors remaining      : 0      <- MEASURED, not estimated
sorry / admit / axiom : 0      <- grep AND Lean's own #print axioms, see below
theorem count         : 27
theorems machine-checked: 27   <- every one, verified by Lean's kernel
```

**These numbers are generated, not typed.** `scripts/check_lean_status_freshness.py` re-derives every
figure in this block from the Lean source and the build, and fails if any of them disagrees. It exists
because this block said `10` for a full session after two theorems had been added and every other
document had already been updated to `12` — nothing was wrong with the formalisation, and everything was
wrong with the record of it, which is the one artefact a reader actually has to trust.

### The check that matters, and why grep is not it

`grep sorry` proves a string is absent. It does not prove a theorem is proved. A file can be free of
the literal words and still carry an unproven term, and a theorem can close with a tactic that was
never actually given the hypothesis it needed.

So the guard asks **Lean's kernel** instead, via `#print axioms`:

```
$ python scripts/check_lean_axioms.py
OK: 27 theorem(s), none depends on sorryAx; allowed axioms only
    ['Classical.choice', 'Quot.sound', 'propext']
```

`propext`, `Classical.choice` and `Quot.sound` are Lean's three standard axioms; nothing here calls
`Classical`, so its `choice` is not expected. The check forbids exactly one axiom -- `sorryAx`, which is
what Lean substitutes for a proof it could not find.

It also has a negative control, because a guard that has never failed is not a guard:

```
$ python scripts/check_lean_axioms.py --negative-test
  [OK] real file has no sorryAx dependency
  [OK] a sorry-proved theorem is caught
  [OK] real file restored
```

### How this check nearly passed while being broken

Three defects, each of which would have produced a **green light for a file containing `sorry`**:

1. **`LEAN_PATH` unset.** `lake env lean` does not put the project's own build output on the search
   path, so `import NHB.PhaseI.Core` fails and the query returns nothing at all. Absent output is
   indistinguishable from "axiom-free" unless you count the theorems -- which is exactly why the check
   now **raises** on empty output rather than reporting a pass.
2. **The project root was derived, not passed.** Taking `parent.parent` of a file at
   `NHB/PhaseI/Core.lean` yields `NHB/`, not the lean-nhb root, so the path pointed one level too deep.
3. **`lake` instead of `lake.exe`.** Windows `PATH` lookup does not append `PATHEXT`, so `subprocess`
   raised `WinError 2` and the exception was swallowed into an empty result.

**This is the project's recurring failure mode in its purest form: a tool that exits 0 while measuring
nothing.** The defence is the same as everywhere else here -- the check reports how many theorems it
covered, and a negative control that must fail.

## The five results, and what each is FOR

The protocol 4.4 fits `tau*` to produce `Coverage@eps` without saying which threshold is reported when
several meet the budget. The mathematics needed to close that is small and entirely definitional:

1. `Risk(tau)` and `Coverage(tau)` are monotone non-increasing in tau;
2. the admissible set `{tau : Risk(tau) <= eps}` is upward closed, hence an admissible tau is **never
   unique**;
3. a canonical threshold exists (one above every confidence admits nothing, so its Risk is 0);
4. **the least admissible threshold maximises coverage among admissible thresholds** -- so the tie-break
   in Amendment 2 B1 has a defensible optimum, and the understatement from any other choice is bounded
   by monotonicity rather than by luck;
5. an empty dev set is degenerate: every tau is admissible and coverage is 0 at all of them.

**Point 4 is the substantive one.** It is why the tie-break was declared rather than left open.

| Theorem | Statement |
|---|---|
| `accepted_mono` | `a <= b` and the gate admits at `b` implies it admits at `a` |
| `coverage_mono` | `a <= b` implies `Coverage b xs <= Coverage a xs` |
| `risk_mono` | `a <= b` implies `Risk b xs <= Risk a xs` |
| `admissible_mono` | the admissible set is upward closed |
| `mem_maxC` | every observation's confidence is `<= maxC xs` |
| `top_admissible` | `maxC xs + 1` is always admissible |
| `admissible_exists` | hence an admissible threshold always exists |
| `coverage_decreases` | coverage decreases as tau increases |
| `empty_dev_is_degenerate` | an empty dev set admits everything and covers nothing |
| `silent_iff_acceptedAndWrong` | `SilentError@tau` and the accepted-error rate are **one** quantity |
| `least_admissible_maximises_coverage` | the §B1 tie-break rule, proved in full (§B1 below) |
| `least_admissible_is_at_least_as_good` | the guarantee is a maximum, **not** a strict one |
| `protocol_said_nondecreasing_is_FALSE` | the §6 wording "non-decreasing in τ" is **refuted by `decide`** |
| `budget_collapses_to_zero_on_small_dev` | protocol's ε=0.05 gives floor(0.05·N)=0 for N<20; least admissible is a shut gate (Coverage=0); not covered by degeneracy clause |
| `acc_is_not_diagnostic_of_understanding` | Acc falls while conditional accuracy rises on IDENTICAL answer-correctness: §6 eq (7) does not isolate understanding, and H1.1 alone is not diagnostic |
| `acc_defers_wrong_mono` | under defers-as-errors, Acc is non-increasing in τ for a fixed sample |
| `cond_error_complements_cond_accuracy` | H1.3's "error among accepted" and the H1.1 co-report are ONE quantity — the confirmatory family has a declared dependency, not two independent chances |
| `one_movement_three_readings` | one confidence movement drives Acc **down**, CondErr **down**, CondAcc **up**, on identical answer-correctness |
| `clean_pins_at_floor` | with a clean arm at the floor the selector returns a **design constant** for every ε — the clean endpoint of Δτ* is not an estimate |
| `delta_tau_reduces_to_the_noisy_selector` | so Δτ* is one estimate minus a constant, not two estimates |
| `same_diagnostic_from_different_arms` | Δτ*=0 cannot distinguish no disturbance from a tolerance-absorbed one |
| `the_threshold_below_the_limen_keeps_only_the_error` | τ one step below the fitted limen keeps ONLY the error and nothing else — maximally anti-selective pocket just below the limen |

That last row matters for the paper: it makes explicit that the noisy-channel framing's `P_e` and the
protocol's `SilentError@tau` estimand name the same number, not two related ones.

## SCOPE: what is deliberately NOT here

**No empirical premise appears in this file.** Every theorem follows from the protocol's definitions
alone -- a finite sample of (confidence, correct) pairs, the confidence rule, and the gate. In
particular there is **no theorem saying that noise changes any of these quantities**. That is the
empirical claim; it is carried as a named premise in the manuscript, not as something Lean can prove.
A formalization that asserted it would be proving the result by fiat.

## The one structural change, and why it was necessary

`Risk`'s guard is now a named Bool:

```lean
def Bad (tau : Nat) (o : Obs) : Bool := decide (tau <= o.c) && decide (o.correct = false)
```

Definitionally identical to the inline condition. It is named because of a specific and total failure:
inline, `simp`, `rw`, `by_cases` and `omega` all branch on an *unfolded* `decide ... = true`, while a
hypothesis about the same condition is a syntactically different term, so nothing matches and nothing
rewrites. `omega` reported a counterexample containing `g := (if false = true then 1 else 0)` -- a term
it could not evaluate, treated as an arbitrary non-negative integer, which made an unsatisfiable goal
look satisfiable.

**This one line ended eight rounds of guessing.** The earlier version of this file blamed the tactic;
the cause was the guard's shape.

## Corrections to earlier versions of this record

Kept rather than quietly edited, because the errors were in a record meant to guide a decision -- and an
inaccurate status file is worse than an absent one.

| Earlier claim | Measured |
|---|---|
| "9 errors" | 3, then 1, then 0 |
| "the remedy is `lake add mathlib`" | Wrong layer: not one failure was a missing lemma |
| "It does not compile" | It compiles; three subagents and the scratch-file method fixed it |
| "the obstacle is one tactic's normalised form" | It was the guard's *shape*; naming it ended the guessing |

One earlier failure was in the build configuration, not the mathematics: `lakefile.toml` declared
`globs = ["NHB", "vf.PhaseI.*"]` pointing at a module that does not exist, so the build failed before
reaching any theorem. Corrected to `globs = ["NHB"]`.

## Process notes, kept because they are the reusable part

- **Work in a scratch file.** Every successful proof here was found by compiling a three-line
  reproduction with `lean scratch.lean`, then applying the minimal change. Three of the ten theorems
  were fixed by subagents under an explicit instruction to do exactly that, and all three landed
  first try -- after eight of my own direct attempts on the same file had failed.
- **Never hide a failure behind `(try ...)`.** An earlier subagent wrote `dite_true`/`dite_false`, which
  do not exist in any Lean version, and wrapped the damage in `(try ...)` so the error count looked
  unchanged while the file degraded. The grep for `(try ` is now part of the standing discipline.
- **Adding Mathlib would not have prevented this.** A larger lemma set makes it easier to stop and
  guess, because there is always another name to reach for.
- **Verify subagent reports, never relay them.** Two subagents claimed their scratch file was deleted;
  one had left it behind. `ls NHB/PhaseI/` is part of the verification now.
- **Five defects were found in this file** -- a `sorry` written into a draft, an assumed `Nat.find`,
  `Bool`/`Prop` mixed in one position, the wrong error count, and now a guard that measured nothing.
  None was a mathematical problem, and all five would have shipped silently under a weaker workflow.


---

## ScaleFree.lean — the design justification for H1.2′, as a theorem

**Added with the v1.19 replacement of H1.2 by H1.2′.** the formalization repository's PhaseI/ScaleFree module, core-only, no Mathlib.

H1.2′ measures the gate's discriminability as the within-arm AUC and was chosen over an equivalence bound on
a rate **because it is scale-free**. `laya`'s own library warns that this checkpoint's temperatures are invalid
and that affected confidences are uncalibrated, so *"this hypothesis does not depend on the calibration"* has
to be a theorem rather than an argument.

| theorem | statement | `#print axioms` |
|---|---|---|
| `winsAux_map_of_strictMono` | **the ordered-pair count, hence the AUC, is invariant under any strictly increasing rescaling of the confidence scale** | **no axioms** |
| `lt_iff_of_strictMono` | a strictly increasing map on `Nat` reflects order as well as preserving it | — |
| `countLt_map` | the inner count is unchanged by such a map | **no axioms** |

**`#print axioms` reports that none of the three depends on any axiom at all** — stronger than the
no-`sorryAx` bar the Core module is held to, since it rules out every axiom rather than one.

### What the formalization cost, and what it taught

Everything below is a Lean-4-core fact that had to be discovered rather than assumed, and each is the sort of
thing that silently invalidates a proof written from memory:

- **`lemma` is not a command in Lean core.** The keyword is provided by Mathlib. Without it the parser fails
  with *"unexpected identifier; expected 'def', 'theorem', …"* on the line that follows, which points at the
  wrong place. `theorem` is the core keyword.
- **`if_pos` / `if_neg` are deprecated** in this toolchain (`ite_eq_left` / `ite_eq_right` are the current
  names); the old forms still work but warn.
- **A `rw` cannot rewrite a proposition a `Decidable` instance depends on.** Rewriting the condition of an
  `ite` fails with *"motive is not type correct"*, because the instance is an argument of the `ite`. The
  repair is to branch with `by_cases` and close each branch with `ite_eq_left` / `ite_eq_right`, which never
  performs the dependent rewrite.
- **`#print axioms` needs the fully qualified name** outside the namespace that declares the theorem.

**`lean-nhb` is now under version control** (root commit `20c472e`), closing a structural risk that had already
cost a zero-byte truncation of the Core module once. `.lake/` is ignored.
