# docpipe — the rules a document pipeline has to satisfy, and why

This directory is the reusable part of the pipeline that produced the LIMEN Phase I manuscript and its
supplementary information. It exists because **eleven defects reached deliverable documents in a single
session and every one of them was invisible in the artefact** — the file opened, looked right, and was wrong.

Every rule below was paid for. The "incident" line is not decoration: it is the reason the rule is stated the
way it is, and a rule whose reason is forgotten gets reverted by the next person who finds it inconvenient.

---

## 1. Verify the artefact, not the intent

**Rule.** Every generated document gets a post-build check that DERIVES its expectations from the source
(how many mathematics spans it declares, how many figures it references) and asserts them against the produced
file (native equation count, residual delimiters, embedded media, resolvable references).

**Incident.** A DOCX shipped with every equation and **not one figure**. The markdown carried
`![Figure N](figures/x.png)`, the HTML resolved it, and the DOCX builder skipped it in silence. The build
reported success throughout, because it was asked whether the script ran rather than what the file contained.

**Enforced by.** `scripts/check_documents.py` — and it is in the guard suite, so no document can be committed
unverified.

## 2. A renderer must have its fonts, or it substitutes

**Rule.** Assert that each renderer's font directory is populated, counted against a floor.

**Incident.** The variables were not italic, and no build said anything. MathJax's CHTML output does not
italicise with CSS — it reaches for a dedicated font — and the font directory was absent, so the browser
substituted and the italic distinction disappeared. The same substitution affected every symbol. **A missing
font is not an error, it is a substitution, and the page still looks like a page.**

**Enforced by.** `scripts/check_documents.py`, plus check C4 in `scripts/check_manuscript_html.py` — two
independent places, deliberately.

## 3. Key a cache by content, not by position

**Rule.** Cache keys are the expression or the source text. A stale entry must become ABSENT, so it falls back
and is reported, rather than silently wrong.

**Incident.** The TeX→OMML map was keyed by the expression's POSITION. Lookup found the span's current index
and used it against a map harvested earlier, so after any edit span *i* received the mathematics of whatever
used to sit at *i* — and the build reported success because an entry existed at that key.

**Enforced by.** `scripts/build_si_docx.py` and `docpipe/render.py`, which key by the expression's own TeX.

## 4. One producer per output

**Rule.** Every output artefact, and every SECTION of a shared artefact, has exactly one writer. A second
script that could write it delegates instead, or does not write at all.

**Incident, four times in one session.** Two builders wrote the same DOCX path and the one that ran last
silently won, so an equation-native document could be replaced by one carrying raw source. Concurrent commit
processes shared one message file and deleted each other's. A guard's own negative-control probe raced
`git add`. And the Stage 2 figure script rewrote a shared caption file from its own three figures, deleting
four captions belonging to another builder.

**Enforced by.** Merge-not-replace in `scripts/build_stage2_figures.py` (it reports "3 own + 4 preserved"), and
a unique message path per commit.

## 5. A failure that cannot reach the thing that acts is not a check

**Rule.** Never pipe a command whose exit code gates something. Capture it.

**Incident.** The guard suite was invoked as `run_all_guards.py | tail -3 && git commit`. A pipeline reports the
LAST command's status, so a RED suite printed its failures and the `&&` still fired. Only the pre-commit hook,
running the suite itself, prevented a red-suite commit.

**Corollary, same session.** A `py_compile` check passed a script whose `import re` was missing — a syntax
check cannot see a name that does not exist. **Verification is the script RUNNING.**

**Enforced by.** `.githooks/pre-commit`, and the habit of `cmd > out.txt 2>&1; rc=$?`.

## 6. A guard that encodes a design must fail when the design changes

**Rule.** Do not treat a guard failure caused by a deliberate change as a nuisance to be silenced. Update the
check and say why, or the change goes unexamined.

**Incident.** Unifying the maths renderers removed KaTeX, and check C4 — which asserted the page references
three KaTeX files — turned red. **That was the check working**: it forced the replacement to be argued, and C4
now asserts MathJax *and* the font directory, which is stronger than what it replaced.

**Enforced by.** `scripts/check_manuscript_html.py`.

## 7. A figure that has not been measured is not a figure that passed

**Rule.** Run a programmatic layout audit over EVERY figure generator: text overlap, text outside the canvas,
labels escaping their panel, font sizes outside the journal band.

**Incident.** The audit covered one generator, so four later figures were never measured. Extending it found
the proof-dependency graph had its labels overlapping in dozens of places, and that all the newer figures were
saved with a tight bounding box while the audit measures against the saved canvas.

**Corollary.** A crash that produces a clean count is a false pass. The audit printed zero collisions once
because the generator had died before the figure was captured; **the exit code, not the count, was what said
so.**

**Enforced by.** `scripts/qc_stage2_figures.py`, which now iterates all generators and runs inside the guard
suite.

---

## The shape of the pipeline

```
source markdown ──┬─> HTML   (renderer + assets)     ─┐
                  ├─> PDF    (same engine)            ├─> verify the ARTEFACT
                  └─> DOCX   (TeX→MathML→OMML)        ─┘   (counts derived from the source)
figures ─────────────> layout audit ──────────────────┘
```

Two rules govern the whole thing and they are the two most expensive lessons here: **derive expectations from
the source and assert them against the product**, and **make sure the failure can reach the thing that acts.**
