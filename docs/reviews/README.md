# Review records — the critical-review instrument applied

Three papers from the reference-frame library have been run through the six-question instrument of
`docs/CRITICAL_REVIEW_PROTOCOL.md`. This file is the index; each record is a separate file.

**All three reviews were produced on the free route** (`nvidia/nemotron-3-ultra-550b-a55b:free`), and
**all three were verified before being believed**: the load-bearing quotations were re-checked against
the source `paper.md` by literal string search before any verdict was recorded. The verification is
recorded inside each file, including where a check **failed to confirm** something.

| # | Paper | Venue | Verdict | What it turned on |
|---|---|---|---|---|
| 1 | Evaluating LLMs for accuracy **incentivizes hallucinations** | Nature 2026 | **GAP FOUND** | The construct is defined over inputs with a **single correct answer** — the paper says so — and it opens with an **ambiguous abbreviation**, three models returning three different specific expansions, which it calls fabrication. Quoted, with the sidestep at line 26 and the label at line 24. |
| 2 | LLMs as **uncertainty-calibrated optimizers** | NMI 2026 | **GAP FOUND** | Joint GP–LLM training yields a calibrated **GP surrogate** (low NLPD); the paper's framing extends that to the **LLM itself** becoming uncertainty-calibrated. **Nothing in it measures the LLM's own uncertainty** — and the reviewer's key negative claim is corroborated by a search: the string `verbalized` occurs **0 times** in the source. |
| 3 | A cognitive approach to **human–AI complementarity** | NRP 2025 | **NOT TESTABLE AS WRITTEN** | A Perspective: it measures nothing. **The discrimination check did its job** — the hypothesis that deferral is packaged as a solved capability was **not supported**: the paper explicitly flags "determine when to defer" as an open need (verified, 2 occurrences; "further development is needed", 1). The reviewer declined to manufacture a gap. |

## The pattern, and why it is not one finding repeated three times

Reviews 1 and 2 share a **shape**: a result that is valid *inside a scope* is described in a way that
extends it *outside* that scope, and in both cases the extension is the sentence a reader remembers.

But the scopes differ and so do the fixes:

- **In review 1 the scope condition is about the INPUT** — a single correct answer per prompt. The
  discriminating measurement is therefore lexical: build a sense inventory and ask whether the model's
  expansions are attested.
- **In review 2 the scope condition is about WHICH OBJECT IS CALIBRATED** — a surrogate, not the model.
  The discriminating measurement is a property of the model, measured directly (verbalized confidence,
  logits, conformal), not of the fitted surrogate.

**Collapsing these into "papers overclaim" would lose the only part that matters**, which is that the
overreach is locatable, quotable, and in each case attached to a specific measurement that would
settle it.

**Review 3 is the negative control and is worth as much as the other two.** It shows the instrument can
return *no gap* — which is the only reason to trust the two gaps it did return.

## Honest limits

1. **These are readings of text, not measurements.** They establish what each paper says. They do
   **not** establish that any specific alleged overreach has an empirical consequence. Review 1's
   falsification condition in particular is **untested** until a sense inventory exists.
2. **The verdicts are not equally strong.** Review 3's verdict is a statement about the paper's genre
   and is nearly unappealable; reviews 1 and 2 rest on a reading of framing against scope, which a
   defender could contest by pointing to a passage the reviewer did not quote. **The quote-level
   verification reduces that risk without eliminating it.**
3. **Review 3's text carried vocabulary from a retired object** ("FDLH", "associativity ×
   confusability", "self-referential mistranslation") — the reviewer answered in this programme's frame
   but imported a discarded one. Those passages were replaced with this programme's own endpoints and
   **the correction is recorded inside the file**, not silently applied. The verdict is unaffected: it
   rests on the paper's own quoted text.
4. **A free model produced these.** That is why the quotes were checked. It is also worth stating that
   the checks passed — the cheap route produced grounded work at zero marginal cost.
