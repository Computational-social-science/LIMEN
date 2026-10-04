# Review records — the critical-review instrument applied

Four papers from the reference-frame library have been run through the six-question instrument of
`docs/CRITICAL_REVIEW_PROTOCOL.md`. This file is the index; each record is a separate file.

**All four reviews were produced on the free route** (`nvidia/nemotron-3-ultra-550b-a55b:free`), and
the load-bearing quotations are re-checked against the source `paper.md` before any verdict is
recorded — a free model producing grounded work is a result worth stating, but it is a result that has
to be checked, not believed.

| # | Paper | Venue | Conversion quality | Verdict |
|---|---|---|---|---|
| 1 | Evaluating LLMs for accuracy **incentivizes hallucinations** | Nature 2026 | `reviewed_with_limitations` — 23/23 pages reviewed, 25 adjudications | **GAP FOUND** |
| 2 | LLMs as **uncertainty-calibrated optimizers** | NMI 2026 | `reviewed_with_limitations` — 63/63 pages, 21 diagnostics adjudicated | **GAP FOUND** |
| 3 | A cognitive approach to **human–AI complementarity** | NRP 2025 | `reviewed_with_limitations` — 15/15 pages | **NOT TESTABLE AS WRITTEN** |
| 4 | **Detecting hallucinations using semantic entropy** | Nature 2024 | **`unreviewed`** — 31 pages extracted, page-by-page review **not** performed | *pending* |

## The conversion-quality difference is not cosmetic

**Record 4 sits one tier below the other three, and that tier is recorded rather than smoothed over.**

Its `verify` reports `status: "unreviewed"`, `all_sources_agent_reviewed: false`, and the build was run
with `--draft`. A spot scan found **0** bare page numbers, **0** glued table digits, **0** superscript
residue, **0** private-use-area characters and **0** duplicated headings, and all 25 artifact checks
report `matches_source_conversion: true` — so gross extraction damage is unlikely, and the mechanical
layer is sound.

**But the review layer is absent**, and the review layer is where the previous three conversions found
real defects: 25 adjudications in record 1, 21 diagnostics in record 2, column-order repairs and a
rebuilt references section in record 3. **So record 4's figures and complex tables may be mis-transcribed,
and any claim resting on one is marked `[UNVERIFIED: table/figure extraction]` rather than asserted.**

**Why it matters for this programme specifically.** Record 4 is the paper closest to our construct
claim — it is the canonical semantic-entropy detector, and our claim is that such a detector is
mis-specified on inputs with several valid readings. A mis-transcribed number in exactly that paper
would be worse than no paper, so the caveat travels with every use of it rather than living only here.

## The pattern across the three completed records, and why it is not one finding repeated

Records 1 and 2 share a **shape**: a result valid *inside a scope* is described in a way that leaves it,
and in both cases the sentence a reader remembers is the one that overreaches.

But the scopes differ and so do the measurements that would settle them:

- **In record 1 the scope condition is about the INPUT** — one correct answer per prompt. The
  discriminating measurement is lexical: build a sense inventory, ask whether expansions are attested.
- **In record 2 the scope condition is about WHICH OBJECT IS CALIBRATED** — a surrogate, not the model.
  The discriminating measurement is of the model itself.

Collapsing these into "papers overclaim" would discard the only part that matters: that the overreach is
locatable, quotable, and attached to a specific measurement that would settle it.

**Record 3 is the negative control and is worth as much as the other two.** It shows the instrument can
return *no gap* — which is the only reason to trust the two it did return.

## Honest limits

1. **These are readings of text, not measurements.** They establish what each paper says. They do
   **not** establish that any alleged overreach has an empirical consequence. Record 1's falsification
   condition in particular is **untested** until a sense inventory exists
   (`docs/CORPUS_LOCATION_STATUS.md`).
2. **The verdicts are not equally strong.** Record 3 is nearly unappealable; records 1 and 2 rest on a
   reading of framing against scope, which a defender could contest with a passage the reviewer did not
   quote. Quote-level verification reduces that risk without eliminating it.
3. **Record 3's text carried vocabulary from a retired object** and was corrected **in place with the
   correction recorded inside the file** — a correction nobody can see is not a correction.
4. **A free model produced these.** That is why the quotes were checked. The checks passed, which is the
   useful part: the cheap route produced grounded work at zero marginal cost.
