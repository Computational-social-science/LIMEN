# Phase II — the empirical noise evidence for §6

**Prepared 2026-10-08.** This document supplies `PHASE_II_PREREGISTRATION.md` §6 with what it asked for and
nothing more. §6 permits levels to be equated by either **(a) a human pilot** or **(b) documented per-channel
empirical error rates from an external source**, and forbids equating them by "the same edit rate as English".
It does not permit the noise process to be invented, so every distribution below is **measured from an observed
corpus** — the three primaries fixed by `docs/PHASE_II_AMENDMENT_1_CHANNELS.md`, declared with their provenance
in `config/datasets.json` and measured from the bytes by `scripts/build_data_manifest.py`.

**Every number here is reproducible from the corpora on disk.** No figure was recalled, and the scripts that
produce them are named at the point of use.

---

## 1. What was measured, and why these three quantities

A faithful $\mathcal{N}_{s}$ needs three things that a corpus can supply and that intuition cannot:

1. **the unit of corruption** — what changes, so the process edits the right object;
2. **the inventory** — which corruptions are real, so the process draws from attested forms rather than from a
   generator's imagination;
3. **the frequency spectrum** — how the mass is distributed, so the process samples the shape and not merely
   the support. **A process that samples uniformly over an attested inventory is still unfaithful** if the real
   distribution is concentrated, which is exactly what the measurements below show it to be.

---

## 2. English — the alphabetic channel

**Source:** Birkbeck Spelling Error Corpus (`missp.dat`), 6,136 correct words as `$word` headers, each followed
by its misspellings.

| quantity | measured |
|---|---|
| correct words | **6,136** |
| misspelling tokens | **36,133** |
| **distinct** (`word → misspelling`) pairs | **36,133** |
| error forms per word (mean) | **5.89** |

**The finding that matters: every one of the 36,133 pairs is distinct.** There is no frequency spectrum to
sample from, because the corpus records **types, not rates** — no misspelling recurs as a countable event.

**Consequence for §6, and it is a limit rather than a result.** Birkbeck can supply the **unit** and the
**inventory** for the English channel, and cannot supply the **rate**. This is the same conclusion the earlier
audit reached from the literature (`docs/PHASE_II_S1_CHANNEL_EVIDENCE.md`: no published autocorrect error rate
exists), now confirmed by measuring the corpus itself: **the English channel's level cannot be equated by route
(b) from this corpus.** Phase I did not need it to be — its levels came from a published human anchor under a
recoverability index — and Phase II must use the same index rather than pretend a rate is available.

**What the inventory does show about the English channel's character.** The words with the most distinct error
forms are long, low-frequency, orthographically irregular items — `miscellaneous` (226 forms), `magnificent`
(185), `beautiful` (179), `enthusiasm` (167), `especially` (156), `prejudice` (154), `conscientious` (152).
**These are non-word corruptions of improbable surfaces.** That is Phase I's class, and it is the class the
pre-registration contrasts the other two channels against.

---

## 3. Japanese — the syllabic channel, kanji-conversion

**Source:** JWTD, the `kanji-conversion` category, both splits. Corruption unit is the **word**, taken from each
record's `diffs` field.

| quantity | measured |
|---|---|
| confusion-pair tokens | **246,014** |
| **distinct** pairs | **26,089** |
| diffs per sentence (mean / max) | **1.031 / 5** |
| pairs occurring ≥ 2 times | 12,536 (48.0 % of pairs, **94.5 % of mass**) |
| pairs occurring ≥ 50 times | 744 (2.9 % of pairs, 59.3 % of mass) |
| pairs occurring ≥ 1000 times | **17 (0.1 % of pairs, 14.9 % of mass**) |

**The distribution is sharply concentrated, so uniform sampling over the inventory would be unfaithful.** The
seventeen most frequent pairs alone carry 14.9 % of all mass, while **52.0 % of the inventory (13,553 of 26,089
pairs) occurs exactly once**. The most frequent pairs are `製作 → 制作` (6,957; 2.83 %), `勤め → 務め` (3,963),
`始めて → 初めて` (3,461), `制作 → 製作` (2,509), `運行 → 運航` (2,491).

**And the pairs are what the channel selection rests on: ordinary word for ordinary word, confused by reading.**
`製作/制作`, `勤め/務め`, `始めて/初めて`, `開放/解放`, `再開/再会`, `召還/召喚`, `自信/自身`, `競争/競走`,
`受賞/受章`, `回答/解答`, `内臓/内蔵`. **A reader who knows the reading cannot tell which was meant from the
surface alone** — the surface is unremarkable and the reading is wrong.

**A structural property that the noise process must handle: the corruption is not injective.** **15.9 % of wrong
forms (3,308 of 20,853) are the wrong form of more than one correct word.** A process that assumes
`wrong → correct` is a function will silently mis-attribute those cases; it must sample the direction the corpus
actually records (the corpus gives `pre → post`, both attested).

---

## 4. Chinese — the logographic channel

**Source:** CSCD-NS, labelled sentences (`label == 1`) in train and test. Corruption unit is the **character**.

| quantity | measured |
|---|---|
| error-bearing sentences | **16,092** |
| character substitutions | **17,671** |
| **distinct** pairs | **5,290** |
| substitutions per sentence (mean) | **1.098** |
| character substitution rate over aligned characters | **1.953 %** |
| length-mismatched sentence pairs | **0** |
| pairs occurring ≥ 2 times | 1,894 (35.8 % of pairs, **80.8 % of mass**) |
| pairs occurring ≥ 50 times | 39 (0.7 % of pairs, 24.8 % of mass) |

**Zero length mismatches is a useful structural fact**: in this corpus the corruption is a pure aligned
substitution, so a character-level noise process can be applied position-for-position without an alignment step
— and any length change in a generated corpus would be a sign the process had drifted from the data.

**The substitution inventory is a homophone inventory**, which is the property the channel is chosen for:
`惟 → 唯` (wéi), `作 → 做` (zuò), `在 → 再` (zài), `那 → 哪` (nà / nǎ), `象 → 像` (xiàng), `带 → 戴` (dài),
`收 → 受` (shōu / shòu), `与 → 于` (yǔ / yú), `力 → 利` (lì), `应 → 映` (yìng), `己 → 已` (jǐ / yǐ),
`须 → 需` (xū), `的 → 地` (de). **Ordinary character for ordinary character, distinguishable by reading and not
by form.** Note the mutual pairs (`作/做`, `在/再`, `与/于`) — as in Japanese, **direction is attested data and
must be taken from the corpus rather than assumed symmetric**.

---

## 5. The contrast this evidence establishes

| channel | category | corrupts | the corrupted form is | predicted signature |
|---|---|---|---|---|
| English | alphabetic | a word | **not a word** (improbable surface) | Phase I measured it: errors are **loud** |
| Japanese | syllabic | a kanji word | **an ordinary word** | quiet |
| Chinese | logographic | a character | **an ordinary character** | quiet |

**This is the pre-registration's mechanism given a measurable form.** The Phase I mechanism says channel-side
noise is loud when the surface is improbable under the intended meaning. The English inventory is improbable
surfaces; the Japanese and Chinese inventories are ordinary forms whose *reading* is wrong. §5's mechanism
prediction — that a conversion channel produces "a surprising surface and a wrong answer" — is therefore not an
assumption imported from the literature but a property of the corpora, measured.

---

## 6. Three constraints the index implementation must honour

**Written before the implementation, deliberately.** Each of these is a property of one channel that a
general-purpose implementation would silently paper over, and each would be discovered only after the levels
had been computed — at which point the fix means recomputing everything. They are recorded here because they
are DESIGN constraints, and a design constraint written into code is a design constraint learned too late.

### 6.1 Chinese: the inventory is usable, the rate is not

CSCD-NS carries an annotated error in **~46 % of sentences in every split** (0.4596 train / 0.4628 dev /
0.4606 test), because a spelling-check dataset is assembled to contain errors. **So the corpus supplies the
substitution inventory and its relative spectrum, and supplies no rate at all.** The Chinese level must
therefore be **supplied by the experimenter and never read off the corpus**, and the spectrum must never be
normalised into a per-character probability. *(Section 6.7 fixes those supplied rates and section 6.5/6.7
record why the level is operational rather than read off the index: an index-derived level inherits the
channel's identity, and measured across the rate grid the index does not vary monotonically with severity.)* An implementation that treats "share of substitutions in the corpus" as
"probability a character is corrupted" will produce levels that describe the annotators' sampling plan.

**This is the only one of the three channels where inventory and rate come from different places**, and it is
the one where conflating them is most tempting, because the spectrum is right there and is already normalised.

### 6.2 English: there is no frequency spectrum to sample

Birkbeck's 36,133 misspellings are **36,133 distinct pairs** — no error form recurs, so the corpus records
**types, not rates**. There is nothing to sample a shape from. The English inventory is usable for what it is
(a list of attested non-word corruptions) and cannot supply a frequency spectrum, which means the English
channel's noise shape cannot be estimated from this corpus by frequency at all. **Phase I did not need it and neither does Phase II** — the
English arm's levels come from the published Scramble Ratio ladder (section 6.6), which is operational and
estimates no shape at all, so nothing has to be invented to fill the gap.

### 6.3 Japanese: the corruption is not injective, and it is directional

Two structural properties, both measured, both of which a naive implementation gets wrong:

- **Not injective.** **15.9 % of wrong forms (3,308 of 20,853) are the wrong form of more than one correct
  word.** An implementation that stores `wrong → correct` as a dict, or that samples by first choosing a wrong
  form and then looking up its correction, will silently mis-attribute those 3,308 cases. The corpus records
  `pre → post` and **both directions are attested data**; the process must sample the direction the corpus
  records.
- **Directional, and the direction is not the one an error model usually assumes.** Checking the highest-mass
  pairs against published frequency (`wordfreq`, Japanese): `製作 → 制作` is **4.49 → 4.86**, `入場 → 入城` is
  **4.26 → 2.70**. **The committed form tends to be the MORE frequent member of the pair** — consistent with an
  input method proposing candidates by frequency, and inconsistent with a model that corrupts toward rarer
  forms. An implementation that assumed errors move toward lower-probability forms would get the prior term
  backwards, and the prior term is one of the two factors the index is built from.

**A dependency this exposed, recorded because a frozen instrument depends on it.** The index's prior comes from
`wordfreq` (`scripts/o1_recoverability.py`, `zipf()`), and on this host `wordfreq.zipf_frequency` for Japanese
raises `ModuleNotFoundError: No module named 'MeCab'` — the package is installed but its Japanese tokenizer was
not, so **the Japanese arm of the index could not have run at all** until `mecab-python3` and `ipadic` were
added. **English and Chinese arm worked without it** (measured). This is the "dependency that disappeared"
failure the global rules describe: it surfaces as a crash far from its cause, on a code path nobody had
exercised yet. Recorded so a rebuilt environment is a known one.

### 6.4 The Phase I index does not transfer to the non-alphabetic channels as constructed

**Two measured degeneracies, found by running it rather than by reasoning about it.** Both are recorded because
each one produced numbers that look like results and are not.

**(a) The edit-radius candidate set explodes, and that is the script difference stated numerically.** The first
implementation took candidates to be every vocabulary word within `MAX_CANDIDATE_EDITS` (= 2, the Phase I
constant) of the committed form. Measured over a 40,000-word vocabulary: **mean 20,257 candidates for Japanese
and 30,290 for Chinese**, giving a mean posterior of 0.00035 and 0.00149 with an MAP hit rate near zero. This is
not a bug. In an alphabetic script orthographic distance is informative — few words are within two edits of any
given string — and in a logographic one **any two-character word is within two edits of a very large number of
other words**. The index's discriminating power comes from the channel term `P(committed | intended)`; the edit
radius was standing in for a channel and providing none.

**(b) Once the channel supplies the candidates, a held-out PAIR has no channel mass and the index saturates at
one.** With the channel fitted on 80 % of the pairs and scored on the remaining 20 %, **the number of held-out
pairs whose (committed, intended) pair was also attested in the fitting set was 0 in all three channels** — the
split is over the pair inventory, so every scored pair is a pair the channel has never seen. The candidate set
then reduces to the intended form alone and the posterior is 1.0 by construction. The measured means —
**0.9865 English, 0.8610 Japanese, 0.5143 Chinese** — are therefore mostly self-fulfilling and **must not be
reported as channel indices**.

**What this requires, stated as the next piece of work rather than as a limitation.** The channel must
**generalise compositionally**: for the Chinese channel, a character-level channel
`P(committed_character | intended_character)` fitted on the training portion gives mass to a held-out pair
because it is built from characters both of whose behaviours the training portion observed. The same applies to
Japanese at the kanji level. Then the candidate set for an unseen surface is the set of forms the composed
channel can produce, which is small and principled — and the index measures something. **The Phase I index is
unchanged in form; what changes is that its channel must be estimated at a unit that generalises, and for a
logographic script that unit is the character.**

**Resolved, and the resolution is the result.** The channel was refitted at the character level, composed
position-wise into a word score, so that a held-out pair receives channel mass from characters whose behaviour
the training portion observed even though the pair itself was not seen. Both degeneracies disappear, and the
saturation diagnostic that would have hidden them is reported with every run:

| Channel | mean posterior | median | intended is MAP | mean candidates | saturated to one |
|---|---|---|---|---|---|
| English (Birkbeck) | **0.3513** | 0.0000 | 0.3517 | 29.99 | 0.000 |
| Japanese (JWTD) | **0.3062** | 0.0538 | 0.3500 | 123.91 | 0.000 |
| Chinese (CSCD-NS) | **0.2718** | 0.0563 | 0.2783 | 106.13 | 0.000 |

**These three rows ARE comparable to one another** — one procedure applied to each language's own attested
error process. **An anchor row is deliberately absent**: section 6.5 shows, by ablation, that the human-validated
anchor cannot be moved onto this scale, and that the English arm therefore keeps Phase I's own construction
instead.

**Read against Phase I's own English construction, where the anchor is measured under this index (0.4480), the
ordering across these three rows is monotone and in the direction the taxonomy predicts**: recoverability falls
from alphabetic to syllabic to logographic (0.3513 > 0.3062 > 0.2718). **What makes this more than a coincidence
of three numbers is that it emerges from three independently collected corpora, three different corruption units
(within-word, kanji word, character), and three writing systems** — nothing in the construction enforces the
order.

**Two limits that must travel with these numbers.** First, the **English arm is not the same construct as
Phase I's**: Phase I scored English words against a typo channel over a vocabulary, giving the 0.4480 anchor
measured under this index;
this table scores Birkbeck's attested misspellings against a character channel fitted from the corpus itself, so
the English figure is comparable to the other two columns and not to the anchor row. Second, the **Japanese
channel generalises least** — only **7.7 %** of held-out committed forms were themselves seen (Chinese: 59.8 %,
because characters repeat far more than two-character kanji words) — so its column rests more heavily on
composition than the Chinese one does; **saturation is nevertheless 0.000 in both**, which is the property that
matters, because a saturated pair contributes a manufactured 1.0.

**These are channel properties, measured on the noisy channel alone, and they are what section 6's level-setting
argument needs. They are not Phase II results**: no model has been run, and the pre-registration's hypotheses
are about the instrument, not about the channel.

### 6.5 The anchor cannot be moved onto the channel scale, and the attempt proves why

**The section 6.4 table compared four rows that were not measured by one instrument**, and the check that
settles it is an ablation rather than an argument.

Phase I's anchor value (0.4480, measured under this index) was produced by **Phase I's own channel** — a typo model built from perturbed
English words, scoring word-level candidates from a frequency vocabulary. The three channel columns were
produced by **a character channel fitted from each corpus**, scoring candidates generated compositionally. Two
differences: the channel's source and the candidate construction.

**Re-scoring the anchor with the estimator the three columns use, on the same stimuli and the same perturbation
(the same pack file, the same `rayner_scramble`, the same seed), gives 0.8799 against the 0.4480 that Phase I
measured under its own construction.** The
gap is 0.43, which is far too large to be a technical difference between two implementations of one estimator.

**So the ablation was run to find out what the 0.8799 measures.** With the channel term set to a constant — the
posterior then driven by the prior alone — the same stimuli score **0.9472**, so the channel's entire
contribution is **−0.0673**. **The channel is close to inert for this stimulus class, and what the 0.8799
mostly measures is the prior.**

**The reason is a mismatch of process, and it is the substantive point.** The corpus channels model
**substitution** — what a reader commits instead of the intended form. Rayner's manipulation is a
**permutation** — the same letters, re-ordered. **A substitution channel has no statistics for a permutation,
and no amount of re-scoring will give it any.** The index is a property of the triple (stimulus, channel,
prior); changing the channel changes the value even for identical stimuli, so **an anchor value calibrates the
pair (condition, channel) and never the condition alone.**

**Three consequences, and they are design decisions rather than code changes.**

1. **The English arm keeps Phase I's own construction.** It is the only arm for which a human-validated anchor
   exists, it is continuous with Phase I, and re-using the validated instrument is the project's rule.
2. **The Chinese and Japanese arms are set by a criterion intrinsic to each channel**, because **no
   human-validated anchor exists for either** and manufacturing one from the Alphabetic anchor would import
   exactly the error this section documents.
3. **The three channel columns remain comparable to one another** — the same procedure applied to each
   language's own attested error process, which is a legitimate cross-language comparison. **The anchor row is
   removed from that table**, because its presence implied a scale it does not share.

**Recorded as the negative control it is.** The ablation is wired into `scripts/phase2_recoverability.py`
(`--ablate-channel`) and reported beside every anchor run, so a future reader cannot quote the anchor number
without the diagnostic that shows what it is made of.

### 6.6 The English arm's levels come from a published operational scale, not from an index

Section 6.5 left the English arm's level-setting open: the human-validated anchor cannot be moved onto the
corpus channels' scale, so a level derived from the index would inherit that problem.

**Wang, Gu, Wei, Gao, Song & Chen (ACL 2025 Findings, "Word Form Matters: LLMs' Semantic Reconstruction under
Typoglycemia") supplies the instrument that removes the problem instead of working around it.** It defines

> **Scramble Ratio (SR) = N_scrambled / N_candidate**, the fraction of a word's interior characters that have
> been scrambled, with five levels **SR ∈ {0, 0.25, 0.5, 0.75, 1}**, and a second axis **Context Integrity (CI)
> ∈ {0, 0.25, 0.5, 0.75, 1}**, over SQuAD stimuli restricted to words of at least ten characters with the first
> and last letters fixed.

**SR is operational: it counts characters, so it passes through no channel at all.** That is exactly the
property section 6.5 shows the index cannot supply, and it means the English arm's levels can be set by a
published, reproducible manipulation magnitude rather than by a quantity whose value depends on which model of
noise happens to be loaded. **Rayner et al. (2006)'s interior-scrambled condition is the SR = 1 end of this
ladder**, so adopting SR also preserves continuity with the Phase I anchor instead of discarding it.

**And the same paper states the gap Phase II fills, in its own Limitations section:**

> "our analysis is limited to English, and it remains uncertain whether morphologically rich languages exhibit
> similar dependencies on word form. Future work could explore broader model architectures, diverse
> perturbation types, and cross-linguistic analyses."

**Its central finding — that LLMs rely on word form and barely on context, with attention reallocating to form
rather than to context as scrambling rises — is established in an alphabetic script only.** Phase II's three
channels are the cross-linguistic test, and they test something sharper than morphology: **whether a reliance on
"word form" survives when form is a different object entirely**, a character whose shape carries meaning rather
than a letter string whose order must be recovered.

**Two limits, stated because they bound what can be borrowed.**

1. **The paper's instrument does not cross scripts.** `SemRecScore` is the cosine similarity between the original
   word's token representation and the last subword token of the scrambled sequence; it presupposes a word with
   an interior whose order can be perturbed and a tokenizer that fragments it. **A Chinese character has no
   interior to scramble and Chinese tokenization is character-level**, so the instrument has no definition
   there. Phase II's dependent variables are behavioural (accuracy, silent error, coverage), not representational,
   which is why they do transfer.
2. **SR and CI are adopted as a level-setting device, not as a hypothesis.** Nothing in this section asserts the
   paper's conclusions; **the project's rule is that a published mechanism is a candidate to test, not a premise
   to build on**, and the paper's own limitation says its finding has not been checked outside English — which is
   the check Phase II runs.

### 6.7 The frozen levels, and why the index is not what sets them

**Both level grids are operational.** Each is a count of corrupted units, so neither passes through a channel —
the property section 6.5 shows an index-derived level cannot have. This section records the measurement that
forced the conclusion rather than assuming it.

**The index was swept against the corruption rate, per channel, with the channel fitted on the real corpus and
the injected sample scored by it.** The candidate set is bounded at one substituted position, because letting
the substitution frontier recurse inflated it to 2,400 candidates for Japanese and 1,100 for Chinese — the same
degeneracy as 6.4(a) arriving through a different door, and diluting the posterior for a reason unrelated to
the corruption being harder. Bounded, the candidate sets are **11.8–13.3 (Japanese), 4.6–5.3 (Chinese),
24.9–25.6 (English)**, and no pair saturates at any rate.

| Channel | rate 0.02 | 0.20 | 0.50 | 1.00 | shape |
|---|---|---|---|---|---|
| Japanese | 0.318 | 0.344 | 0.425 | **0.461** | rises |
| Chinese | 0.347 | 0.354 | 0.367 | **0.367** | flat |
| English | 0.407 | 0.336 | 0.337 | **0.349** | flat |

**What the curves say, and it is not what a level-setting index would need to say.** The index does not vary
monotonically with the corruption rate on **any** channel. Chinese and English are flat across the whole range.
Japanese rises, and the rise is a **composition effect rather than a severity effect**: the rate selects a
nested subset of intended forms in descending order of their attested pair count, so the forms added at higher
rates are rarer ones whose confusion partners are less shared — measurably easier to identify, which is the
opposite of what more corruption should do. **An instrument whose reading moves with which forms were sampled
rather than with how hard they were corrupted cannot set a level.**

**On the permutation arm the index is not merely flat but uninformative.** Across the published SR ladder the
mean posterior is **0.9995–1.0000**, and with the channel ablated to a constant it is 0.985–1.000, so the
channel's entire contribution never exceeds **+0.0144**. **This is section 6.5's prediction, independently
reproduced at five scrambling levels**: a substitution channel carries no statistics for a permutation.
**That measurement is why the English arm's levels are the published ladder and not an index reading.**

**The frozen levels.**

| Arm | Levels | Source of the level | Source of the shape |
|---|---|---|---|
| **English** | **SR ∈ {0, 0.25, 0.5, 0.75, 1.0}** | Wang et al. (ACL 2025 Findings) Scramble Ratio; **SR = 1 is Rayner et al. (2006)** | the scramble itself — no shape is estimated |
| **Japanese** | **rate ∈ {0.02, 0.05, 0.10, 0.20}** | supplied here, **never read off the corpus** | JWTD's directed `pre → post` spectrum |
| **Chinese** | **rate ∈ {0.005, 0.02, 0.05, 0.10}** | supplied here; **brackets the 0.0196 per-character rate the corpus attains** | CSCD-NS's conditional substitution spectrum |

**The Chinese grid is anchored by the corpus's own measured rate rather than centred arbitrarily** — 1.953 % of
characters per sentence (section 4) sits inside the grid, with two points below and one above. **Japanese has no
comparable per-token figure to anchor to**: its 45.7 % is the share of TRAIN RECORDS whose category is
kanji-conversion, which is a property of how the corpus was assembled and not a per-token rate, so its grid is
bracketed by the Chinese one and stated as a choice.

**What the index is for, now that it is not setting levels.** It characterises each channel — the 0.3513 /
0.3062 / 0.2718 table in section 6.4, saturation 0.000, one procedure applied to three independently collected
corpora. **That is a descriptive result about the three error processes, and it is reported as one.**

---

## 7. What §6 still needs, and what this document does not decide

**Supplied here:** the unit, the inventory and the frequency spectrum for the Japanese and Chinese channels;
the unit and inventory for English, with the measured reason its rate is unavailable; the structural properties
(non-injective corruption in Japanese, pure aligned substitution in Chinese, mutually-directed pairs in both).

**NOT decided here, and not to be inferred from this document:**

- **the level-setting itself.** §6 requires recoverability of the intended word under the channel's own noise,
  computed with Phase I's index (the noisy-channel posterior mass on the intended word, with the channel being
  the generator's own model) and anchored at the value this project **measured** for the Rayner et al. (2006)
  interior-scrambled condition — **0.4480, a value measured under this index rather than quoted from the
  paper**. Which corpus subset supplies the noise, how the per-pair mass is normalised into a per-token rate,
  and what the ladder of levels is, are all open;
- **the English level**, which on this evidence cannot come from route (b);
- **whether the Chinese rate may be used at all.** CSCD-NS's ~46 % error-bearing share is an artefact of corpus
  construction (§A3.2 of the amendment), so **its inventory supplies the noise and its prevalence does not** —
  the rate must be set by the index, not read off the corpus;
- **the item count, the power procedure, and the channel ordering.**

**A trap this document is written to prevent.** The three corpora have very different sizes — 6,136 English
words, 246,014 Japanese pairs, 17,671 Chinese substitutions — and it is tempting to equate levels by matching
those numbers. §6 forbids exactly that: **equating by edit rate is the route it rules out**, and the three
channels' units are not commensurable in the first place (a word, a kanji word, a character). The index is what
makes the levels comparable; the counts are what make the noise faithful, and the two jobs must not be
conflated.
