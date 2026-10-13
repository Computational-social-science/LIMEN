# THEORETICAL ANCHOR — the three layers the design is derived from

**This file exists because the programme's goal moved too often, and the reason was structural rather than
procedural.** The goal had been stated against a **descriptive taxonomy** — alphabetic, syllabic, logographic —
and a list of categories is not a mechanism. Any language can be argued into a list, so every new reading of the
literature could argue for a different coverage, and the goal moved with it.

**A mechanism does not move.** This file states the three classical layers the design is derived from, and every
design decision downstream — which languages, which corpora, which levels, which models — is derived from them
rather than chosen. **Where a decision is still a choice, it says so.** Nothing here is adjusted to fit a result;
if a result conflicts with this file, the conflict is reported.

---

## L1 — Information theory: a writing system is a code, and redundancy is what absorbs noise

**Shannon (1948)**, *A Mathematical Theory of Communication*, and **Shannon (1951)**, *Prediction and Entropy of
Printed English*. Shannon's n-gram experiments put the entropy of English at roughly **1 bit per character**
against a ceiling of about 4.7, i.e. **roughly three-quarters of written English is redundant**. Two consequences
follow, and both bind the design.

**A noisy channel and a code are the two halves of one problem.** The question "how much disruption can text
tolerate" is a question about **redundancy consumption**, and it is only well-posed at a stated noise level. **This
is why the levels are operational rates rather than index readings**: the theory needs a rate, and section 6.5 of
`docs/PHASE_II_NOISE_EVIDENCE.md` shows the index cannot supply one.

**And it fixes what the dependent variable must be.** The quantity of interest is not "does it fail" but **how
much redundancy must be consumed before the intended message stops being recoverable**, which is why the
programme carries three dependent variables (accuracy, silent error, coverage) instead of one accuracy figure.

---

## L2 — Orthographic depth and grain size: the axis that replaces the taxonomy

**Katz & Frost (1992)**, the orthographic depth hypothesis; **Frost (2005)**; **Ziegler & Goswami (2005)**, the
psycholinguistic grain size theory. A recent review of cross-script variation names these as **the two dominant
theoretical frameworks** for describing cross-script diversity, alongside the descriptive typologies
(*Writing System Variation and Its Consequences for Reading and Dyslexia*, 2017).

**The mechanism.** A script's depth is how consistently its written units map onto its spoken units. **This
determines the smallest unit a reader can use to get from print to meaning.** In a **shallow** script the mapping
is near-regular, so a reader can work at a small grain — grapheme to phoneme — and reach the word without help.
In a **deep** script that route fails often enough to be unreliable, so the reader must **recruit larger units and
the surrounding context**.

**This is the form/context question, with a thirty-year-old theoretical basis, and it is the reason this
programme's independent variable is depth rather than script class.** The descriptive taxonomy says *what a script
looks like*; depth says **what a reader can do with it, and why** — so it makes a directional prediction, and a
taxonomy does not.

**Where the theory is contested, and it is.** A 2017 study reported **no** cross-linguistic difference in
preferred grain size for one well-known effect (*German and English Bodies: No Evidence for Cross-Linguistic
Differences in Preferred Orthographic Grain Size*). **The programme therefore treats grain size as a theory under
test, not as a premise** — which is the standing rule that a published mechanism is a candidate, not a basis.

**And the metric is a live debate, which is an opportunity rather than an obstacle.** How to *measure* depth has
no agreed answer: a 2025 review in *Psychonomic Bulletin & Review* asks directly *"How we should measure
orthographic depth: Or should we?"*, and a May 2025 preprint proposes a **script-agnostic** measure grounded in
algorithmic information theory (*Orthographic transparency as compressibility*). **So depth cannot be asserted from
a textbook table — it has to be measured, and the measurement is contested.** The programme measures it and
reports which instrument it used.

**One asymmetry that matters and is easy to miss.** Reading and spelling are **not symmetrically transparent**
(*Does a truly symmetrically transparent orthography exist? Spelling is more difficult than reading*, 2022). **The
programme's corpora are production errors — what a person typed — so every claim here is about the production
direction**, and a reading-side result is not evidence about it.

---

## L3 — Context and surprise: making "context contributes" a measurable quantity

**Miller & Selfridge (1950)**, *Verbal context and the recall of meaningful material*: intelligibility depends on
contextual order — fifth-order approximations are recallable, lower orders are not. **Hale (2001)** and **Levy
(2008)** turn this into a quantity: processing cost tracks **surprisal**, `−log P(word | context)`, so the
contribution of context is **the reduction in surprisal it provides**.

**This is what makes the programme's central contrast a measurement rather than a comparison of means.** "The
model relies on form rather than context" becomes: **how much does the available context reduce the cost of
recovering the intended form, and does that reduction scale with the script's depth?**

---

## What is derived from the three layers, and what is still a choice

### Language coverage — derived

**The requirement is set by L2**: the languages must **span the measured depth axis**, each must have an
**observed error corpus** (the standard the programme applies everywhere), and **only one variable may move
between adjacent points**.

| Point on the depth axis | Language | Script | Corpus | Status |
|---|---|---|---|---|
| **shallow alphabetic** | Turkish, Finnish or Spanish | alphabetic | **not yet identified** | **open — see §D1 below** |
| **deep alphabetic** | English | alphabetic | Birkbeck Spelling Error Corpus | acquired, measured |
| **logographic** | Chinese | morphemic | CSCD-NS | acquired, measured |
| *(optional, second axis)* | Arabic | consonantal, non-concatenative | QALB (2M+ words, manually corrected) | identified, availability to verify |

**Japanese moves out of the primary contrast.** Measured: JWTD's kanji-conversion channel is **73.5 % pure
kanji**, dominated by **two-character compounds (70.9 %)**, and shares **43.2 %** of its committed single
characters with the Chinese channel, because kanji *are* Han characters. **It therefore sits on the deep end of
the same axis as Chinese, not at a separate point on it**, and it is retained as a **within-depth generality
check** (does the effect survive a change of corruption unit) rather than as a distinct script class.

**What is still a choice, stated as a choice**: which shallow language. The three candidates differ in corpus
availability rather than in depth, so the choice will be made by **which observed error corpus exists**, and that
is the next thing to determine.

### Levels — derived

**L1 requires a noise rate**; **§6.1 of the noise-evidence document requires that the rate not be read off a
corpus that was assembled to contain errors**. Both bind, and together they produce the operational grids already
frozen in `config/phase2_levels.json`.

### Models — derived criterion, choice within it

**Criteria the theory imposes**: open weights (the result must be reproducible), **more than one scale** (L2's
prediction should hold across capacity, and a scale interaction is a live open question — Wang et al. report a 70B
anomaly their own design cannot explain), and **differing script exposure**, because a model's training mix is a
candidate explanation for the very effect under test. **The last criterion turns what is usually a nuisance into a
variable.**

**Choice within the criteria**: the comparison set used by the recent cross-script literature — **Qwen (CJK-heavy)
and Llama (English-heavy)**, with Mistral and Gemma as available alternatives. **The specific versions are not
frozen here**, because they will be chosen when the run is built and must be recorded with their weights' digests;
what is frozen is the criterion.

---

## D1 — The mainline methodology, settled

**This section replaces an earlier draft of itself.** The design had been: one observed corpus per script, and the
shallow arm blocked because no shallow-orthography observed error corpus could be found. **That blocker is
dissolved, and the structure that dissolves it is better than the one it replaces.**

### D1.1 The generator is the mainline, and the reason is comparability

**`MultiTypo`** (Liu, Zhao, Altinger, Schütze & Hedderich, ACL 2026; arXiv 2510.09536) is a **keyboard-aware
multilingual typo generator**, MIT-licensed, `pip install multypo`, with an operational typo rate
**`τ ∈ [0,1]`**, and it **validates its realism against human ratings** (§3.2 of that paper — 15 sentences per
language judged for naturalness, significantly above a naive baseline in nine of twelve languages).

**Three properties make it the right mainline, and the third is the one that matters most.**

1. **Its rate is operational and built in.** The observed corpora have no rate at all — CSCD-NS's 46 % is a
   construction artefact (§6.1) — so the programme had to supply one. **The generator does not have that problem.**
2. **It is fixed-seed and reproducible**, with no licensing or access dependence.
3. **Its twelve languages already span the depth axis**: English (deep) through French, German and Greek
   (intermediate) to Russian, Hindi, Bengali and Tamil (shallow), plus Arabic and Hebrew (abjad) and the
   Armenian and Georgian scripts. **A three-corpus design compared three teams' annotation schemes as much as it
   compared three scripts; a single generator applies one mechanism across the whole range.**

**And the generator reached the same design rule independently.** Its `τ` is an operational, channel-free noise
rate. The programme arrived at that principle through sections 6.5–6.7 of the noise-evidence document and then
went further by measuring *why* an index cannot supply such a rate. **Two independent arrivals at one rule is
evidence the rule is right.**

### D1.2 The boundary, measured rather than argued

**`get_supported_languages()` returns exactly twelve languages and every one is segmental. There is no
logographic and no syllabic language in the set, and the reason is mechanical rather than editorial.** The
extension point is `register_keyboard_layout(keyboard_rows, left_keys, right_keys, ignoring_set)` — that is,
**key adjacency and hand assignment**. Registering a pinyin keyboard succeeds; the generator then runs and
produces this:

```
input   我惟独喜欢这一个
output  我独喜欢这一个              ← the character 惟 was deleted
```

**A backspace is not the error the corpus records.** Measured over CSCD-NS, giving the generator the strongest
sympathetic reading — comparing the characters' *pinyin* rather than the characters:

| CSCD-NS observed character substitutions | 15,139 |
|---|---|
| **whose typed pinyin is identical** | **12,334 — 81.4 %** |
| whose pinyin differs | 2,805 — 18.5 % |

**For 81.4 % of the observed Chinese errors the keystrokes were correct.** The pinyin was typed exactly and the
error happened inside the input method's candidate selection. **A mechanism defined on key adjacency cannot
generate a single one of them — not because coverage is low, but because there is no keystroke to corrupt.**

**So the boundary is not "the generator is incomplete". It is that the locus of the error moves, and it moves
exactly where L2 says the reading route changes.** In a shallow alphabetic script a reader reaches the word
through small-grain decoding, and a key is the unit that can be mistyped. **In a logographic script the small-grain
route does not exist, the composing unit is the candidate, and the keyboard is no longer where the noise lives.**
**The generator's coverage boundary and the theory's mechanism boundary are the same boundary.**

### D1.3 What each source is for

| Role | Source | Why it holds that role |
|---|---|---|
| **Mainline** | **MultiTypo**, twelve languages, operational τ, fixed seeds | **One mechanism across the depth range** — the only way the cross-script contrast is internally valid |
| **Validity criterion** | **Birkbeck** (English), **QALB** (Arabic) | Where a language has both, ask whether the generator reproduces the **observed** distribution. **This is a stronger role for the observed data than being one point on a curve** |
| **The arm the generator cannot reach** | **CSCD-NS** (Chinese) | §D1.2. **Here the observed corpus is not auxiliary — it is the only instrument that exists** |
| **A finding, not a discrepancy** | the disagreement itself | The measured 81.4 % boundary is a result about a class of generators, reported as one |

### D1.4 The evidence standard, and its exact boundary

**The standing rule is that a study of what people actually do uses observed behaviour, never a simulation of it.
The rule is not repealed here and does not need to be, because it is not the rule this design would break.**

**The distinction is what the claim is about.** A simulated corpus may not be the primary evidence for **a claim
about human behaviour** — that is the failure the rule exists to prevent, and it is why LCSTS-IME-2M was rejected
for the Chinese channel. **The claim here is about how a MODEL behaves under noise.** The generator supplies the
**manipulation**, not the object of study, and **its realism is validated against observed human data** — which is
what makes using it an instrument rather than an assumption.

**The rule that survives, restated so it cannot be read as a loophole**: *observed behaviour is required for any
claim about human behaviour, and is required as the validation criterion for a generated manipulation used in a
claim about anything else.* **Both halves are enforced here — the second by the English and Arabic arms.**

### D1.5 What remains genuinely open

- **A shallow-orthography observed corpus is still wanted, and it is no longer on the critical path.** The
  generator covers the shallow range; an observed corpus there would upgrade that span from *generated and
  validated elsewhere* to *observed directly*.
- **Depth must be measured, not asserted.** The twelve generator languages span the axis by construction but
  their **positions on it have not been measured**, and the 2025 metric that would measure them is itself under
  debate (`docs/RELATED_WORK_AND_GAPS.md`). **Measuring the twelve is a prerequisite for the axis claim, and it
  is a contribution to the metric debate in its own right.**
