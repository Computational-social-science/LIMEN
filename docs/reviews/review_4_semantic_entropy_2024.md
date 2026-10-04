# Review record 4 — semantic entropy: the paper already makes our distinction

**Instrument:** `docs/CRITICAL_REVIEW_PROTOCOL.md`, six questions.
**Source:** `references/paper.md` of `semantic-entropy-paper` (Nature 2024; Kuhn, Gal, Farrar & Gal).
**Produced on the free route** (`nvidia/nemotron-3-ultra-550b-a55b:free`); the load-bearing quotations
were re-checked against the source before this record was written.
**Verdict: WELL-SCOPED — and its own theory already implies our claim.**

---

## 1. Why this verdict is the most useful result so far

The other three reviews found **overreaches** — places where a result valid inside a scope was
described in a way that leaves it. This one found the opposite, and the opposite is more valuable to
this programme:

> **The canonical detector of hallucination by semantic entropy explicitly declines to cover our case,
> and explicitly says that merging our case with genuine fabrication is unhelpful.**

So the paper is **not** a counter-example to the construct claim. It is **independent support for it**,
from the side of the literature least likely to be motivated toward our conclusion.

**This does not weaken the programme's contribution — it relocates it.** The contribution is no longer
"published work conflates the two constructs". It is:

> **A published framework states the distinction in its own theory, and nobody has tested whether the
> framework's *implementation* honours it at that boundary.**

That is a narrower claim, and a much more defensible one — it is falsifiable, and it does not require
anyone to have erred.

## 2. The paper's own words

**Line 161 — it names the merging and rejects it:**

> "We distinguish this from cases in which a similar 'symptom' is caused by the following different
> mechanisms: when LLMs are consistently wrong as a result of being trained on erroneous data such as
> common misconceptions; when the LLM 'lies' in pursuit of a reward; or **systematic failures of
> reasoning or generalization**. We believe that **combining these distinct mechanisms in the broad
> category hallucination is unhelpful.** Our method makes progress on a portion of the problem …
> However, **it does not guarantee factuality because it does not help when LLM outputs are
> systematically bad.**"

**Line 265 — it states the exclusion as a limit on its own method:**

> "Our method **explicitly does not directly address situations in which LLMs are confidently wrong
> because they have been trained with objectives that systematically produce dangerous behaviour, cause
> systematic reasoning errors or are systematically misleading the user.** We believe that these
> represent different underlying mechanisms — despite similar 'symptoms' — and need to be handled
> separately."

**Both quotations verified by literal search against `paper.md`.** The string `systematic` occurs 3
times in the source; both substantive uses are the passages above.

## 3. What the framework therefore predicts about our case

Our object is a model that **consistently** expands an abbreviation to an **attested but unintended**
sense. Under this paper's taxonomy:

| | |
|---|---|
| Consistency across samples | **high** — the model does not vary with the seed |
| Therefore semantic entropy | **low** |
| Therefore the detector's verdict | **not a confabulation** |
| By the paper's own classification | a **systematic** error — "similar 'symptom', different mechanism" |

**So the framework predicts our case is NOT what it detects.** That is the prediction we can test, and
it is the opposite of what a reader who knows only the abstract would expect.

## 4. The gap, stated at the correct size

**Not** a flaw in the paper's logic — its logic is correct and it says so.

**The untested thing is the boundary condition of the implementation.** Two specific, untested
possibilities, both of which the paper's prose leaves open:

1. **Over-sensitive clustering** — the bidirectional-entailment clustering merges two meanings that are
   genuinely distinct. The paper discusses this failure mode and motivates its method against it.
2. **Under-sensitive clustering with respect to *annotator-relevant* distinctions** — the clustering
   treats two expansions as equivalent *because they are lexically similar*, while an annotator treats
   them as different because they are *different attested senses*. **The paper does not test this
   direction at all.** It is the direction our case occupies.

The second is the programme's entry. **It is a gap in the evidence, not in the theory** — and stating it
that way is what keeps the claim alive.

## 5. Honest limits of this record

1. **The conversion is `unreviewed`.** `verify` reports `all_sources_agent_reviewed: false`; the 31 pages
   were extracted but not reviewed page by page. A spot scan found no gross extraction damage, but
   **figures and complex tables may be mis-transcribed**, and the paper's quantitative claims (AUROC
   values, the Table 1 taxonomy) are exactly where that risk lives. Anything used quantitatively from
   this copy must be re-checked against the PDF. The two quotations central to this record are ordinary
   body prose and are not exposed to that risk.
2. **The clustering-quality criticism is recorded but not adjudicated.** The reviewer notes that
   clustering quality is measured only at the entailment-classification level, with no adjusted Rand
   index against human meaning clusters, and that transitivity failures are admitted. **Those are the
   reviewer's readings**, and given point 1 they deserve a check against the PDF before they are used.
3. **This is a reading of one paper's text, not a measurement.** Nothing here shows the framework
   *behaves* as its theory says at our boundary. That is the pending experiment, and it needs the sense
   inventory (`docs/CORPUS_LOCATION_STATUS.md`).
4. **One paper is not a literature.** This result is strong because the paper is canonical, not because
   it is representative. The survey question — *do detectors generally adopt this boundary, or does
   semantic entropy happen to?* — remains open and is Phase II literature work.