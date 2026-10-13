# Post-mortem: why RRC v2.0.0 was retired

**Subject.** The Root Recovery Corpus (RRC v2.0.0, 100,838 items across 6 script arms) was retired on
2026-10-11 as an invalid measurement instrument. This document records the mechanism, not the apology:
what was built, the measurement that condemned it, which standing disciplines would have caught it and
at which step, and what changes structurally as a result.

The evidence and the files are in `archive/rrc-v2.0.0-INVALID/`.

---

## 1. The measurement that condemned it

`scripts/audit_item_validity.py` runs four heuristics that carry **no linguistic knowledge of any
kind** — longest common prefix, closest length, substring, and plain Levenshtein distance — and asks
how often each picks the item's designated root.

```
POOLED over 100,838 items (chance = 20 %):
    edit    72.9 %      prefix  63.9 %      length  38.9 %      substr  12.7 %

rrc-en      n=  2337    edit 99.7 %      margin defined 52.7 %
rrc-en-word n= 84001    edit 80.1 %      margin defined 23.4 %
rrc-zh       n= 11590   edit 22.8 %      margin defined  0.0 %
```

**0 of 17 (arm, layer) cells are usable.** The two failure modes are mutually exclusive, and this is
the finding that matters:

| regime | signature | meaning |
|---|---|---|
| solvable | margin defined, `edit` 93–100 % | surface similarity IS the answer |
| unanswerable | margin undefined, `edit` 14–20 % (below chance) | no gradient; the fields point away from the root |

**No cell satisfied both "the item is non-trivial" and "the difficulty is defined".** The corpus did
not contain a subset worth rescuing; it contained none.

## 2. The construction error

A valid multi-candidate item requires **several candidates each of which could plausibly have produced
the observed state**, so that surface similarity cannot discriminate and only knowledge of the error
channel can. Decoys were instead drawn from the **root's** surface neighbourhood, which admits exactly
two outcomes, both useless: decoys far from the state (trivial) or decoys unrelated to the state (no
gradient).

Two items from one source record, `scrapy docs/intro/install.rst`, showing both:

```
rrc-en-L2-00921   'Jessue' -> 'Jessie'
   cands: Jessie, classified, easiest, Access, tries
   margin 0.2  [defined]

rrc-en-L4-01013   same state, same root, same source record
   cands: confirmation, fundamental, Jessie, presenting, maintenance
   margin None [undefined]
```

In the L2 entry the decoys `easiest`, `Access`, `tries` share letters and bigrams with the state and
carry no other relation to it. **The selection optimised for surface overlap — precisely the dimension
a string-distance heuristic reads.**

## 3. Why it was not caught, against the standing disciplines

### 3.1 The one control the claim itself implies was never run — `planted-truth` step 1

The corpus claims that answering an item requires knowledge of the error channel. **That claim defines
its own control**: construct an item whose root is *not* the surface-nearest candidate, then require a
channel-blind heuristic to fail on it. The control was constructible on day one, cost nothing, and
needed no real data. It was never run.

Instead 83 guards verified conservation through the gates, script purity, unit consistency, provenance
and rendering — **every one of which measures the machinery's internal consistency.**

> **Self-consistency mistaken for a control.** The calculation's own diagnostics stay clean orders of
> magnitude past a real failure, because a pipeline that is consistently wrong is still consistent.

This clause is the exact diagnosis. The corpus was verified to agree with itself and never verified
against an independent notion of truth.

### 3.2 The alarm that fired on day one and was explained away — `planted-truth` step 7

`margin_defined` was false on **52.7 %–100 %** of items. This is the corpus stating that its own
difficulty signal is undefined. The responses were: a plausible benign story ("CJK layers have no
defined margin because character-level similarity is zero"), a scope reduction (cross-arm comparison
restricted to L4), and a paragraph in the report filed under *limitations* — followed by proceeding to
measure and to publish conclusions.

> **The explained-away alarm.** A control fires on real data; a plausible story is found; the run
> proceeds. Firing means stop; the story, if true, will survive a root-cause diagnosis.

The limitations paragraph **is** the override record. A fired alarm was downgraded to prose.

### 3.3 The wrong null hypothesis — `acceptance-gate` step 5

Results were reported as "accuracy against chance 0.25" on a five-option task. **0.25 is not the null
when four of five options are decidably unrelated to the observation** — the effective floor is far
higher. The correct null is the strongest trivial baseline, measured at **0.729 pooled and 0.997 on
`rrc-en`**. 0.82 against 0.25 reads as strong; 0.82 against 0.73 reads as nothing.

> **Satisficing.** The first plausible answer is declared final the moment it looks good against a
> baseline the search itself guaranteed.

### 3.4 Fixtures authored by the code under test — `planted-truth` step 4

The decoy-selection rule and the checks that blessed it came from one mind and one premise: *a hard
item is one whose options look alike.* The decoys were therefore selected for surface overlap, and the
verification measured surface-overlap-related plumbing. **The construction and its verification shared
a blind spot, so neither could detect it.** No step in the pipeline held an independent notion of
truth.

### 3.5 Guard count as a quality proxy

83 green guards became the evidence that the corpus was sound. `planted-truth` step 5 requires every
control to be **watched to fail** — that was done, and those guards were genuinely bidirectional. But
bidirectionality proves a check *works*, never that it checks **the property that matters**. The count
was a measure of effort, and it was read as a measure of correctness.

### 3.6 The same class appeared in the reporting layer, unrecognised

During the same period, moving the report's script into `report.js` silently blinded **six** guards;
four passed **vacuously** (one read a 1,210-character MathJax config and found no fields to check).
This is `planted-truth`'s *silent-pass leg*:

> A missing input yields an empty case list, zero failures, and a green banner — "all passed" where the
> denominator was silently zero.

**The failure class was already present in the project and was diagnosed only when it produced visible
breakage, never when it produced silence.** A vacuous pass had no symptom.

## 4. Structural corrections

1. **Freeze a control battery before building.** For any corpus or benchmark: the plants, the
   corruptions, the null tests and the pass criteria are written down and committed **before** the
   first item is constructed. A control designed after the output exists is chosen to pass.

2. **The accept gate for a multi-candidate corpus is a baseline, not a bound.** *A channel-blind
   heuristic must be near chance.* Peak/trough score, confidence interval and per-cell breakdown are
   reported before any model is run. `edit`, `prefix` and `length` floors appear in **the same table**
   as every accuracy the corpus supports.

3. **Undefined difficulty is a stop condition, not a limitation.** Any field whose undefined rate
   exceeds a stated threshold halts construction. A limitation paragraph is not a substitute for a
   stop.

4. **The constructor does not verify.** Decoy validity is re-derived by an independent implementation —
   or by a subagent given the selection rule and nothing else — because a verifier sharing the
   constructor's premise cannot see the constructor's error.

5. **Guard count is not evidence.** Evidence is one control that could have failed and did not, where
   failing would have been meaningful. Coverage is reported as *which property is checked*, never as a
   count of checks.

6. **A guard that cannot look where the thing lives is not a guard.** Any move of code or data requires
   re-auditing every consumer and **showing** it still detects a real defect. Treat a silent pass as a
   defect report against the check.

## 5. What this post-mortem is worth

The negative result is a result. The construction conditions in §2 and §4 are now supported by direct
measurement rather than by argument, and they generalise: **any multi-candidate task built by choosing
distractors from the target's neighbourhood rather than from the observation's plausible histories will
collapse into string matching or into unanswerability.** That is a publishable methodological finding,
and it is the only thing of scientific value this corpus produced.

## 6. What survives

- `scripts/audit_item_validity.py` — the check that condemned it; registered as a standing guard so a
  future corpus is graded before it is used.
- `archive/rrc-v2.0.0-INVALID/` — the corpus, its manifest, the construction code and this record.
- `check_object_drift.py` class D — mechanical refusal of any live reference to the retired corpus.
- The item browser, which is what exposed the defect by showing a real item to a human reader after 83
  guards had passed.

**Retired with the corpus:** every measurement taken on it. The accuracies reported against
`LiquidAI/d1-3B` (0.82–0.93, quoted at the time against chance 0.25) are withdrawn, not qualified. A
knowledge-free heuristic reaches 72.9 %, and 99.7 % on `rrc-en`; those figures cannot be reported as
root-recovery ability.
