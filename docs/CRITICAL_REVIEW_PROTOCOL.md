# Critical-review protocol — how the paper-agents are to be used

**Owner's correction (2026-10-04), recorded verbatim in intent:**

> *Not every conclusion or mechanism in SCIENCE/NATURE literature holds. Treating the polysemy of an
> abbreviation as LLM hallucination is precisely a conclusion we want to challenge — and exactly the
> kind of SCIENTIFIC GAP we are after, for critical review.*

**This document corrects the posture taken when the paper library was set up.** The previous framing —
published work as an authoritative *reference frame* to be adopted — is wrong. Published work is the
**set of claims under review**. The library's purpose is to make each claim **answerable to a test**,
not to supply our premises.

---

## 1. What changes, stated as a table

| | Wrong frame (superseded) | Correct frame |
|---|---|---|
| Status of a published claim | authority to align with | **a claimant** |
| Meaning of a pre-emption | "we may not claim novelty" | **"we are obliged to engage — and the engagement is where the contribution is"** |
| Kind of gap sought | coverage gap ("nobody measured X") | **construct / taxonomic gap ("the published X is mis-specified, and here is the measurement that shows it")** |
| Role of the paper-agents | reference frames | **instruments for interrogating claims** |
| Failure mode to avoid | under-engaging (ignoring prior work) | **deferring** — adopting a construct because it is published |

**This does not relax rigour; it relocates it.** We still cite prior work, concede what it establishes,
and pre-empt what it pre-empts. What we refuse is the inference *published ⇒ correct*.

## 2. The worked example, because it is the programme's own object

**The claim to be reviewed.** A family of high-profile results operationalises *hallucination* as an
unreliable or ungrounded output — e.g. by measuring semantic inconsistency across sampled answers and
treating low consistency as the hallmark of fabrication.

**Why it does not hold here.** When a model expands the abbreviation `LLM` to *Master of Laws*, it is
not fabricating. It is resolving an **abbreviated, polysemous input** by selecting a lexicalised
reading — and it does so **consistently**, which is the opposite of the inconsistency the hallucination
construct keys on. Two distinct failures are being merged:

1. **fabrication** — an output with no support in the input or the world;
2. **a legitimate reading that disagrees with the annotator's intent** — the model and the label simply
   resolved the same abbreviation differently.

**These are different constructs with different signatures.** A framework that scores (2) as (1) is
**mis-specified on exactly this class of input**, and the mis-specification is measurable: consistent
polysemous resolutions should be *high* on the hallucination instrument's own statistic while being
*correct* on a lexicalisation instrument. That divergence is the finding.

**Note the direction of the test.** We are not claiming the hallucination literature is wrong in
general. We are claiming it has a **scope condition** it does not state, and that our regime sits
outside that scope. That is a bounded, falsifiable, publishable claim — and it is the kind of claim
NHB exists for.

## 3. The instrument: six questions per paper, in this order

Every paper-agent in the library is interrogated with the same six questions. The output is a short
review record, not a summary.

1. **THE CLAIM.** In one sentence, what does the paper assert? Quote it.
2. **THE MECHANISM.** What is the proposed causal or statistical mechanism? Is it a law, a regularity,
   a correlation, or a definition in disguise?
3. **THE OPERATIONALISATION.** What exactly is measured, on what inputs, with what labels — and
   **whose judgment do the labels encode?** (A label is an annotator's decision, not ground truth.)
4. **THE SCOPE.** Under what conditions was it validated? Name the population, the item class, the
   language, the model class, and the regime. **The scope is where over-extension happens.**
5. **THE OVERREACH.** Where is the construct applied **beyond** that scope without a test — especially
   where two distinct constructs are merged because they share a surface signature? *(This is the
   question the programme exists to ask.)*
6. **OUR ENTRY.** Which of our measurements would **separate** the merged constructs, and what would
   the paper's framework predict that we can falsify? If none exists, say so: the paper is then a
   reference frame after all, and should be labelled one.

**Discrimination check.** A paper that survives all six as well-scoped is **not** a gap. Recording that
honestly is part of the instrument: if every paper turns out to be well-scoped, then our gap is
elsewhere, and we must find it rather than manufacture one.

## 4. What this does to the two documents that were written under the wrong posture

| Document | Correction |
|---|---|
| `docs/GAP_VERDICT.md` | Its pre-emption list stands as **fact** (those mechanisms are published). Its **conclusion** is amended: pre-emption is not a bar to novelty, it is the **obligation to engage**. The surviving claim is therefore not merely "a narrower interaction" — it is **the construct-validity challenge**, whose first act is showing where a published construct's signature and its target come apart. |
| `docs/PAPER_AGENT_LIBRARY.md` | §3 ("what the agents are for") is superseded by §3 of this document. The library's purpose is **interrogation**, and a converted agent that is never interrogated has produced nothing. |

**Both corrections are recorded rather than silently overwritten**, because the wrong posture was
articulated in an earlier commit and a reader of that commit must be able to see why it was abandoned.

## 5. Consequence for the three dispatched conversions

They remain exactly as valuable — **more so**. Their outputs are not premises to import; they are the
**objects** the six-question instrument is applied to. If a conversion completes, the next action is not
"read it as background" but "run the instrument and record the review".

## 6. The standing rule this establishes

> **A published result enters this programme in one of two roles, and the role must be declared:
> an *instrument* (a tool or method we use, e.g. a calibration procedure) or a *claimant* (an assertion
> we are testing). It is never an authority.** Where a paper is cited for a mechanism, the citation
> carries the scope condition; where it is cited for a method, it carries the provenance.

**Drift signal.** Any live document that imports a published *conclusion* into this programme's
premises without declaring it a claimant, or that treats a venue as evidence of correctness, is drift
against this rule.
