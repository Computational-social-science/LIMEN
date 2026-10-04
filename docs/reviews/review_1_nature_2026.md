# Review record 1 — the 2026 Nature accuracy-incentivized-hallucination paper

**Instrument:** `docs/CRITICAL_REVIEW_PROTOCOL.md` — six questions, claim → mechanism → operationalisation
→ scope → overreach → our entry, with a mandatory discrimination check.
**Source read:** `references/paper.md` (86,025 B) of the built agent
`incentivized-hallucination-paper`.
**Produced by:** a delegated reviewer on the **free** route
(`nvidia/nemotron-3-ultra-550b-a55b:free`) — recorded because it bears on routing, not on the science.
**Reviewer's verdict:** **GAP FOUND**.

---

## 1. Verification — the review was checked before it was believed

A free model produced this review, so its quotes were treated as **claims to be tested**, not evidence.
Every load-bearing quotation was re-checked against the source text by literal string search. **All nine
were found.** The reviewer's line numbers drift by 2–6 lines from the actual file; the **content is
exact**. The drift is recorded rather than smoothed, and the quotations below carry their **verified**
line numbers from the source file, not the reviewer's.

| Load-bearing quotation | In source? |
|---|---|
| "they fabricate specific, confident responses" | **yes** |
| "We side-step these definitional tangles" | **yes** |
| "a single correct answer" | **yes** |
| "a single way to write any given fact" | **yes** |
| "openai/gpt-4.1 via OpenRouter" | **yes** |
| "language-model judges are also found to incorrectly judge answers" | **yes** |
| Theorem 3's singleton-rate bound | **yes** |
| "abstaining is strictly suboptimal" | **yes** |
| "reward unwarranted guessing" (reworded) | **yes** |

**Depth of that verification, stated honestly:** the search proves the *strings exist*. It does **not**
by itself prove each string carries the role the reviewer assigns it. The two that carry the most weight
— §4's Definition 1 and line 26 — were therefore also read **in context** (below), and their role holds.

---

## 2. The six answers, condensed

1. **CLAIM.** Hallucination is "an unintended outcome of training objectives and evaluation incentives
   rather than an inherent LLM deficiency". Not a flaw, an *incentive*.
2. **MECHANISM.** Two, and they are of different kinds. **(i)** A **lower-bound theorem** (Thm 3,
   arbitrary-facts model): with calibrated next-word prediction, the hallucination rate is bounded below
   by the fraction of training facts appearing exactly once. A **proven regularity**, via Good–Turing
   missing mass. **(ii)** A **dominance argument**: under binary accuracy with abstention scored as
   incorrect, guessing dominates abstention — *a definitional consequence of the scoring rule*, not a
   statistical law.
3. **OPERATIONALISATION.** SimpleQA, 4,326 factual questions; **labels assigned by a single model
   judge — `openai/gpt-4.1` via OpenRouter**, not humans and not a consensus. The theoretical bounds use
   analyst-defined valid/error partitions; the synthetic arbitrary-facts model defines ground truth *by
   construction*. **The paper's own text concedes that model judges "incorrectly judge answers".**
4. **SCOPE.** Four frontier proprietary models (Gemini 3 Pro, GPT-5, Grok 4, Claude Opus 4.5) at default
   settings via OpenRouter; **English only**; short-form factual questions with **a single correct
   answer**; one mitigation (a two-generation consistency check); linear abstention-reward rubrics only.
   **Not validated:** open-source models, other languages, multi-hop or ambiguous questions, human
   labels, any other mitigation.
5. **OVERREACH.** The construct is applied as unitary. Three distinct error types share the surface
   label: **approximation** (spelling/counting), **estimation** (singletons), and **polysemy** — and the
   third is precisely the case the framework cannot represent.
6. **OUR ENTRY.** *Attested-sense recovery rate*: for an ambiguous acronym, build a sense inventory from
   corpus evidence, then measure the share of model expansions that **appear in the inventory**.
   Fabrication = expansion ∉ inventory. Polysemy = expansion ∈ inventory but ≠ the annotator's sense.

---

## 3. The gap — stated in the paper's own words

**The paper declares the sidestep (verified, line 26):**

> "defining and measuring hallucination is complicated by issues such as responses that contain multiple
> vague claims. **We side-step these definitional tangles** by analysing an abstract set of errors,
> following learning theory, which applies to binary classification (for example, dog versus cat images)
> **without adjudicating edge cases (for example, images containing both)**."

**Then it opens with one of those edge cases and labels it fabrication (verified, line 24):**

> "All are wrong. They do not abstain, for example, by saying, 'I don't know', or by requesting more
> context, as a reliable human assistant would. **Instead, they fabricate specific, confident
> responses.**"

**And the example is an ambiguous acronym (verified, lines 16–22),** with three models returning three
*different specific* expansions — including one naming a named, exchange-traded financial instrument.

**The gap, in one sentence.** *The paper's construct is defined over inputs with a single correct answer —
it says so — and an ambiguous abbreviation is an input with several; the paper nonetheless uses one as its
opening illustration and calls the model's answers fabrication, without any sense-inventory control that
could separate a fabricated expansion from an attested one.*

**Why this is a scope-condition claim and not an accusation.** We do **not** claim the paper is wrong
about singletons, about next-word-prediction pressure, or about scoring incentives — those results stand
in their own scope. We claim the construct has an **unstated scope condition**, and that the paper's own
text states the condition while using the excluded case as its headline.

**Falsification condition (pre-committed).** The claim dies if, on ambiguous acronyms,
**attested-sense recovery is low** — i.e. model expansions are mostly **absent** from a corpus-built
sense inventory. That would mean the models *are* fabricating, and the paper's label is right for these
items after all. The discriminating measurement is: attested-sense recovery **> 90 %** while
single-answer accuracy on the same items is **< 20 %**.

---

## 4. What this changes for the programme

1. **The gap is no longer a hypothesis about the literature; it is a quoted claim about a specific
   paper.** `docs/GAP_VERDICT.md` framed pre-emption as an obligation to engage. This is the engagement,
   with the source text in hand.
2. **A concrete second instrument is required: a corpus-built sense inventory.** Without it the
   discriminating measurement cannot be computed, and the falsification condition cannot be evaluated.
   This is a new dependency and it is **not** satisfied by anything currently in the repo.
3. **Phase I is unaffected.** Phase I fixes English items with locked gold and measures noise effects on
   error, SilentError and coverage; it does not need the inventory. The inventory is the **bridge from
   Phase I's machinery to the construct claim** and belongs to the paper that makes that claim.
4. **Honest limit.** This review is a *reading* of one paper's text, not a measurement. It establishes
   that the paper says what is quoted. It does **not** establish that any specific PGGB expansion is
   attested — that requires the inventory in (2). Until then the falsification condition is **untested**,
   and this record must not be cited as though the gap were demonstrated empirically.
