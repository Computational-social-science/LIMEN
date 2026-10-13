# RESEARCH STATE — goal, theoretical basis, methodology, results

**This document is the programme's consolidated statement of what it is trying to establish, on what basis,
by what method, and what has actually been established.** It is written to be read top to bottom; every number
in it traces to an artifact in this repository, and every claim says which artifact.

**Authority, stated so this file cannot silently become a rival source.** Where this file and the
**protocol** disagree about the *objective*, the protocol wins
(`protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md`). Where this file and **another document**
disagree about a *fact* — what exists, what is pinned, what is blocked — `CURRENT_OBJECT.md` wins, because its
claims are checked against the repository by `scripts/check_anchor.py`. **This file is the one place that states
the four layers together**, so that a reader does not have to reconstruct the programme from six documents that
were last edited on six different days. When a layer changes, it is changed here first and the consequences are
carried outward.

**Last global revision: 2026-10-08**, after the Phase II noise-channel measurements, the ablation that refuted
the anchor transplant, and the adoption of a published operational scale for the English arm.

---

## 1. Research goal

**The goal is a falsifiable claim about where the load falls, and it is anchored on a mechanism rather than on
a list of script names.** The three classical layers it is derived from are stated in
**`docs/THEORETICAL_ANCHOR.md`** — information theory (L1), orthographic depth and grain size (L2), context and
surprisal (L3) — and every design decision downstream is derived from them there.

> **The division of labour between word form and context in recovering noisy text is set by the orthographic
> DEPTH of the script, not by the model: as depth rises, form's contribution falls and context's rises.**

The reasoning is short and it comes from measurements rather than from a preference. **In an alphabetic script,
word form that has been disrupted is still recoverable from itself** — the letters are a permutation of the
intended ones, and re-ordering them is a computation over the form. **In a logographic script it is not**: a
committed character carries no structural cue pointing at the intended one — `惟` and `唯` are unrelated shapes
that happen to sound alike — so **form cannot in principle recover it and only context can**. The prediction that
follows is specific and checkable: **the published finding that context contributes little should not replicate
in a logographic channel**, because the noise that channel produces is unrecoverable from form alone.

**The primary contrast is therefore English against Chinese — alphabetic against logographic — and it needs
nothing else.** Everything beyond it is generality rather than requirement, which is a deliberate change from the
earlier framing of this goal: see §5.2 for why the contested middle channel was moved out of the primary claim.

### 1.1 What the goal is measured on, and why that is not incidental

**Every channel's evidence is a corpus of observed human errors.** The claim is about what humans do to text when
they type it, so a simulation of that would be evidence about the simulator. **The same standard was applied to
the rejected alternatives**, named with the reason so a later session with a bigger machine cannot reopen them on
the strength of sample size.

| Channel | Dataset | What it is | Measured |
|---|---|---|---|
| English | **Birkbeck Spelling Error Corpus** (Mitton) | native-speaker misspellings | 6,136 words, 36,133 misspellings |
| Chinese | **CSCD-NS** (Hu, Meng & Zhou, ACL 2024) | 40,000 sentences of real Sina Weibo posts, MIT | 17,671 character substitutions, 1.953 % per character, 0 length mismatches |
| Japanese | **JWTD** (Tanaka et al., ACL 2020 SRW) | kanji-conversion pairs, CC-BY-SA 3.0 | 515,328 train / 8,542 test; kanji-conversion 45.7 % of train |

**A morphological resource is not a substitute for an error corpus, and the difference is the whole study.**
UniMorph, Universal Dependencies and WASPI are authoritative and **contain no errors at all** — their error rate is
identically zero. Substituting them for the corpora above would replace the distribution of observed input errors,
which is the object, with a resource in which that distribution does not exist. **Where such resources are the
right instrument is the descriptive layer** — grounding the statement that a script is non-concatenative, for
instance — **and that is where they are used.**

| Phase | Channels | Status |
|---|---|---|
| **I** | English, standard Latin orthography | **COMPLETE** — all three pre-registered hypotheses confirmed |
| **II** | English (alphabetic), Japanese (syllabic), Chinese (logographic) | **Preparatory** — channels derived, datasets acquired and measured, levels frozen; no model run |

### 1.1 What Phase II is for, stated against the literature rather than against a gap we assert

**Wang, Gu, Wei, Gao, Song & Chen (ACL 2025 Findings), "Word Form Matters: LLMs' Semantic Reconstruction under
Typoglycemia"** establishes that LLMs reconstruct scrambled words mainly from **word form**, with **context
contributing little**, and that attention **reallocates toward form** rather than toward context as scrambling
rises. It states its own boundary:

> "our analysis is limited to English, and it remains uncertain whether morphologically rich languages exhibit
> similar dependencies on word form. Future work could explore broader model architectures, diverse
> perturbation types, and **cross-linguistic analyses**."

**Phase II is that cross-linguistic analysis, and it tests something sharper than morphology.** In an alphabetic
script, "form" is a letter string whose *order* must be recovered. **In a logographic script there is no interior
to reorder: the character's form carries the meaning directly.** So the question "does the system rely on form or
on context" is not the same question in the two scripts, and the paper's instrument does not cross the boundary —
its `SemRecScore` compares a word's token representation against the last subword token of a scrambled sequence,
which presupposes a word with an interior and a tokenizer that fragments it. **A Chinese character has no
interior to scramble and Chinese tokenization is character-level**, so the instrument has no definition there.
Phase II's dependent variables are behavioural, which is why they do transfer.

**Adopted as a level-setting device, not as a premise.** Nothing here asserts that paper's conclusions. The
programme's standing rule is that a published mechanism is a *candidate to test*, not a basis to build on.

---

## 2. Theoretical basis

### 2.1 The frame, and its three classical layers

Human–model language interaction is treated as a **structurally biased coupled control system**: writing systems
and input noise are normal disturbances rather than exceptions, and the control law — confidence-gated action —
is directly observable. **The design is derived from three classical layers, set out in full in
`docs/THEORETICAL_ANCHOR.md`:**

- **L1 — Shannon (1948, 1951).** A writing system is a **code**, and redundancy is what absorbs noise. Shannon's
  measured entropy for printed English (~1 bit/character, ~75 % redundancy) is the classical quantification of
  how much a text can lose. **It is why the manipulation is an operational noise RATE**, and why there are three
  dependent variables rather than an accuracy figure.
- **L2 — Katz & Frost (1992), Frost (2005), Ziegler & Goswami (2005).** **Orthographic depth / grain size** is
  the axis that determines the smallest unit a reader can use to reach meaning, and therefore whether context is
  needed. **It is the independent variable, replacing the descriptive script taxonomy** — a taxonomy says what a
  script looks like, depth says what a reader can do with it, and only the latter makes a directional prediction.
  *The theory is contested (a 2017 study reports no cross-linguistic grain-size difference) and its measurement
  is a live 2025 debate, so it is carried as a theory under test and depth is measured, not asserted.*
- **L3 — Miller & Selfridge (1950); Hale (2001); Levy (2008).** Context's contribution is quantified as
  **surprisal reduction**, which is what turns "the model uses context" into a measurable quantity.

**Why the goal stopped moving.** It had been stated against a descriptive list, and a list has no mechanism: any
language can be argued into one. **Depth has a mechanism and a metric, so coverage is derived from the axis
rather than negotiated, and the goal is fixed.**

**Where the framing exceeds what those sources support, the manuscript says so** — the capacity form is used as a
form and not asserted as an instance; the rate-distortion frontier is treated as a frontier and not as a theorem.
**And Rayner et al. (2006) is an anchor stimulus, not a theoretical layer** — it supplies a human-validated point
on the manipulation axis, and §2.2 records what its index value can and cannot be compared to.

### 2.2 The recoverability index, and what it is now known to be

The index is a **noisy-channel posterior**: the mass on the intended word under `P(committed | intended) ·
P(intended)`, with the channel being the noise process itself and the prior being the language's own lexical
frequency. It exists to fix noise levels at points where the manipulation is neither trivially easy nor
impossible — non-saturating levels, so that a null result means something.

**Three properties of it were measured this round, and they changed its role in the programme.**

**It is a property of a triple, not of a stimulus.** Re-scoring the Phase I anchor with the Phase II estimator
on *identical* stimuli — same pack file, same `rayner_scramble`, same seed — moves the value from **0.4480,
measured under this index by Phase I's own construction**, to **0.8799, measured under this index by the Phase II
construction**. **0.4480 is a value this project measured, not a number published in Rayner et al. (2006)**; the
citation names the stimulus condition the index was pointed at. A 0.43 gap between two readings of one condition is a scale change, not a numerical difference.

**The anchor cannot be moved onto the corpus channels' scale, and the ablation says why.** With the channel term
set to a constant — the posterior then driven by the prior alone — the same stimuli score **0.9472**, so the
channel's entire contribution is **−0.0673**. **The channel is inert for this stimulus class, and the 0.8799
mostly measures the prior.** The reason is a mismatch of process: the corpus channels model **substitution**,
Rayner's manipulation is a **permutation**, and a substitution channel has no statistics for a permutation. **An
anchor value therefore calibrates the pair (condition, channel) and never the condition alone.**

**Consequently the index does not set levels.** Swept against the corruption rate, it does not vary monotonically
with severity on any channel — Chinese and English are flat across the whole range, and Japanese's rise is a
composition effect (higher rates admit rarer intended forms whose confusion partners are less shared). Across the
published Scramble Ratio ladder its reading is **0.9995–1.0000**, with the ablation at 0.985–1.000, so the
channel never contributes more than **+0.0144**. **An instrument whose reading moves with the model of noise
loaded, rather than with how hard the stimulus was corrupted, cannot set a level.**

**What it is for.** It characterises each channel — one procedure applied to three independently collected
corpora — and it is reported as a descriptive result in §4.3.

### 2.3 Three principles adopted this round, each tied to a measurement

1. **Instrument unity.** Two implementations of one index that differ in channel source or candidate
   construction do not share a scale, even when both are called "the index". A table placing their outputs side
   by side implies a shared scale that does not exist. **The failure was committed here and caught by review**,
   and it is why §4.3 carries no anchor row.
2. **Process coverage.** Before a channel is used to interpret a stimulus, the stimulus class must belong to the
   process the channel models. Where it does not, the correct conclusion is "this channel does not cover this
   manipulation" — not "the channel gives a low score".
3. **Operational levels.** Where a published manipulation magnitude counts the physical property directly, it is
   superior to any index-derived level because it is invariant to the noise model.

---

## 3. Methodology

### 3.1 Channels, derived from the depth axis rather than chosen

**Coverage is derived from L2.** The arms must **span the measured depth axis**, each must have an **observed
error corpus**, and **only one variable may move between adjacent arms**. The earlier derivation — from the
descriptive three-class taxonomy of Li, Huang, Yao & Hyönä (2022, *Nature Reviews Psychology*) — was replaced
because a descriptive class carries no mechanism, which is what allowed the coverage to be renegotiated on every
reading. **`docs/THEORETICAL_ANCHOR.md` carries the table and the measurement that moved Japanese out of the
primary contrast** (its corpus exercises kanji, i.e. the deep end of the same axis as Chinese).

**One arm is genuinely open**: a **shallow-orthography observed error corpus** (Turkish, Finnish or Spanish). No
other arm lacks one, and no constructed corpus may substitute, because the study is about the error distribution
itself. **Until it is found the primary contrast is English against Chinese** — enough to test the direction of
the prediction, not its shape.

### 3.2 Datasets — observed human behaviour, in all three

**Every channel's primary evidence is a corpus of observed human errors. No simulated data enters a claim or a
success criterion.** Declared with an explicit `provenance` field and enforced by
`scripts/check_dataset_provenance.py`.

| Channel | Dataset | What it is | Measured |
|---|---|---|---|
| English | **Birkbeck Spelling Error Corpus** (Mitton) | native-speaker misspellings | 6,136 words, 36,133 misspellings |
| Japanese | **JWTD** (Tanaka et al., ACL 2020 SRW) | kanji-conversion pairs, CC-BY-SA 3.0 | 515,328 train / 8,542 test; kanji-conversion 45.7 % of train |
| Chinese | **CSCD-NS** (Hu, Meng & Zhou, ACL 2024) | 40,000 sentences of real Sina Weibo posts, MIT | 17,671 character substitutions, 1.953 % per character, 0 length mismatches |

**The rejected alternative is recorded so a later session with a bigger machine does not reopen it on the
strength of sample size**: LCSTS-IME-2M, 2,000,000+ sentences built by *simulating* an input method, was rejected
because the study would then be measuring the simulator's assumptions.

### 3.3 Levels — frozen, and all operational

**Every level is a count of corrupted units, so none passes through a channel.** Source of truth:
`config/phase2_levels.json`, written by `scripts/phase2_recoverability.py --levels`.

| Arm | Levels | Why this source |
|---|---|---|
| **English** | **SR ∈ {0, 0.25, 0.5, 0.75, 1.0}** | published Scramble Ratio (Wang et al., ACL 2025); **SR = 1 is the Rayner et al. (2006) interior-scrambled condition**, so continuity with the Phase I anchor is preserved |
| **Japanese** | **rate ∈ {0.02, 0.05, 0.10, 0.20}** | supplied by the experimenter, never read off the corpus; shape from JWTD's directed `pre → post` spectrum |
| **Chinese** | **rate ∈ {0.005, 0.02, 0.05, 0.10}** | supplied; **brackets the 0.0196 per-character rate the corpus attains**; shape from CSCD-NS's conditional spectrum |

### 3.4 Three per-channel constraints, recorded before the implementation

Written down first because each is a property one channel has and a general-purpose implementation would paper
over, and each would otherwise be discovered after the levels had been computed.

1. **Chinese — the inventory is usable, the rate is not.** CSCD-NS carries an error in **~46 % of sentences in
   every split** (0.4596 / 0.4628 / 0.4606) because a spelling-check dataset is assembled to contain errors. The
   corpus supplies the substitution inventory and its relative spectrum, and no rate at all. An implementation
   that treats "share of substitutions" as "probability of corruption" describes the annotators' sampling plan.
2. **English — there is no frequency spectrum to sample.** Birkbeck's 36,133 misspellings are 36,133 **distinct**
   pairs, so the corpus records **types, not rates**. Nothing can be sampled from a shape that does not exist.
3. **Japanese — the corruption is not injective, and it is directional.** **15.9 % of wrong forms (3,308 of
   20,853) are the wrong form of more than one correct word**, so a wrong-to-right dict lookup mis-attributes
   them. And the direction is counterintuitive: `製作 → 制作` is **4.49 → 4.86** and `入場 → 入城` is **4.26 →
   2.70** in published frequency — **the committed form tends to be the MORE frequent member**, consistent with
   an input method proposing candidates by frequency.

### 3.5 The estimator

**Exact paired permutation**, with Holm correction, and direction enforced as part of the hypothesis so that
opposite-direction movement is excluded from the family rather than counted as support. Phase I's estimator is
inherited unchanged.

### 3.6 Guards

**49 guard runs**, each required to fail on an injected defect, aggregated by `scripts/run_all_guards.py` under a
mutex; a `pre-commit` hook makes a red suite and a commit mechanically incompatible. **The guard suite earned its
place three times this round**: `check_attributed_numbers` caught this project repeating the Rayner attribution
error it had already corrected once; the noise-evidence guard caught a second producer's numbers being quoted
without a check; and a negative control caught **our own control mis-identifying what failure looks like** —
which is the same class of error as a check that cannot fail.

---

## 4. Results

### 4.1 Phase I — COMPLETE, all three hypotheses confirmed

**13,692 conditions, 0 failures, 366.5 s.** All three pre-registered hypotheses rejected under Holm with **zero
direction violations**.

| Hypothesis | p | Threshold | Effect |
|---|---|---|---|
| H1.1 | **4.42e-36** | 0.0167 | b = 71 / c = 307 |
| H1.2′ | **2.00e-04** | 0.0500 | AUC **0.6014 → 0.7601**, **+0.1587**, 1,956 units |
| H1.3 | **5.00e-05** | 0.0250 | **−0.2904**, CI [0.2679, 0.3154] |

**The premise the original H1.2 assumed was refuted, and the refutation stands.** Print-error noise costs ~12 pp
accuracy and ~29 pp coverage, **but the confidence gate is MORE discriminative under noise, not less**: 93.6 % of
noise-induced errors fall below the gate against 71.4 % when clean. **The errors are loud, not silent.** H1.2 was
replaced by H1.2′ — "gate discriminability RISES" — after four independent probes on dev, and the replacement
reuses §4.5 within the same Holm family with thresholds unchanged. **Option (a) `CondErr` was proposed, measured,
and withdrawn by its own author as statistically flat.**

### 4.2 Lean formalisation — 27 theorems, 0 sorry, 0 axioms

The formalisation lives in the **sibling repository** `lean-nhb` (next to this one; override with
`$NHB_LEAN_ROOT`), 591 lines over `lean-nhb: NHB/PhaseI/*.lean` — 23 theorems in the core file and 4 in the
scale-free file. **The formalisation is a feedbacker, not an appendix**: it
refuted a §6 direction, proved the §B1 tie-break optimal, and found the budget collapse (ε = 0.05 with N < 20
closes every minimum-acceptable gate). Verified only by the kernel (`#print axioms`), with guards carrying
negative controls.

### 4.3 Phase II — the three channels characterised

**One procedure, three independently collected corpora, three corruption units, three writing systems. Nothing
in the construction enforces the order.**

| Channel | mean posterior | median | intended is MAP | mean candidates | saturated to one |
|---|---|---|---|---|---|
| English (Birkbeck) | **0.3513** | 0.0000 | 0.3517 | 29.99 | 0.000 |
| Japanese (JWTD) | **0.3062** | 0.0538 | 0.3500 | 123.91 | 0.000 |
| Chinese (CSCD-NS) | **0.2718** | 0.0563 | 0.2783 | 106.13 | 0.000 |

**Recoverability falls from alphabetic to syllabic to logographic.** These are **channel properties, measured on
the noisy channel alone, and they are not Phase II results** — no model has been run. **No anchor row appears
above**, for the reason given in §2.2.

### 4.4 Negative results, recorded first-class

**Four degeneracies were found by running the instrument rather than by reasoning about it. Each produced
numbers that looked like results.**

1. **The edit-radius candidate set explodes on a logographic script.** Measured over a 40,000-word vocabulary:
   **20,257 candidates for Japanese, 30,290 for Chinese**, so the posterior on any one word is ~1/N and the
   reading is 0.00035 / 0.00149 with an MAP hit rate near zero. **This is not a bug — it is the script
   difference stated numerically.** Orthographic distance is informative in an alphabetic script and carries
   nothing in a logographic one, where any two-character word is within two edits of a very large number of
   others.
2. **A pair-level channel saturates the index at one.** With the channel fitted on 80 % of pairs and scored on
   the rest, **0 of 600 scored pairs in every channel had their pair attested in the fitting set**, so the
   candidate set reduced to the intended form alone and the posterior was 1.0 by construction. The readings
   (0.9865 / 0.8610 / 0.5143) were **mostly self-fulfilling and are recorded as such**.
3. **The compositional fix, and its own second-order degradation.** Fitting the channel at the **character** level
   and composing it position-wise — the unit that generalises — removes both degeneracies. Letting the
   substitution frontier **recurse**, however, inflated the candidate set again to **2,400 (Japanese) / 1,100
   (Chinese)**. Bounded at **one substituted position** it is **11.8–13.3 / 4.6–5.3**, with no pair saturating.
4. **The anchor transplant, refuted by ablation.** §2.2. Reported beside the number it refutes, so the number
   cannot be quoted without the diagnostic.

**A dependency gap was also found and closed.** `wordfreq.zipf_frequency` for Japanese raised
`ModuleNotFoundError: No module named 'MeCab'` — the package was installed but its tokenizer was not, so **the
Japanese arm of the index could not have run at all**. This is the "dependency that disappeared" failure: it
surfaces as a crash far from its cause, on a path nobody had exercised yet. **A well-intentioned installation of
the legacy `mecab` package then shadowed the working `mecab-python3` and broke it again**; diagnosed, the shadow
removed, and the working pair verified.

---

## 5. What is genuinely open, and what the deliverables are

### 5.1 Open, stated as open rather than as a plan

1. **No model has been run under any Phase II channel.** Everything in §4.3 is a property of the noise process.
2. **The primary contrast has not been run.** English against Chinese is the claim; nothing in §4 measures it.
3. **The Phase II pre-registration has not been re-synced** to the frozen levels (§3.3) or to the goal as
   restated (§1). It is the document that has to be right before a confirmatory run.
4. **The protocol is at v1.24 and `CURRENT_OBJECT.md` still says v1.1.**
5. **The Japanese rate grid is a choice, not an anchor** — Chinese brackets an observed per-character rate,
   Japanese has no comparable per-token figure because its 45.7 % is a share of TRAIN RECORDS by category.
6. **The channel-characterisation table (§4.3) is not yet in the manuscript.**

### 5.2 The middle channel, and a correction to this programme's own labelling

**Measured, and it changes a design label rather than a result.** JWTD's kanji-conversion channel is **73.5 %
pure kanji**, its dominant unit is a **two-character compound (70.9 % of events)**, and **43.2 % of its committed
single characters are also attested committed characters in the Chinese channel** — because kanji *are* Han
characters. **So the Japanese channel as operationalised exercises the logographic system, not the syllabic one
its label claims.** The programme described this arm as syllabic because the taxonomy it derives coverage from
(Li, Huang, Yao & Hyönä, 2022) has a syllabic class, and kana is that class; the corpus it uses to instantiate the
arm is a kanji corpus.

**Two things are true at once and both are recorded.** The two channels are **not identical** — the corruption
unit differs, two-character compounds against single characters — **but they are not two different writing
systems either, and the difference between them is not the difference the label asserts.** That is why §1's
primary contrast is English against Chinese: **it is the contrast the data supports**, and it does not depend on
the contested arm.

**The arm is not discarded, it is re-scoped.** It becomes a **generality check inside the logographic system** —
does the script effect survive a change of corruption unit? — and a **syllabic channel is added only if an
observed kana error corpus is found**, because a constructed one would fail the standard every other channel met.

### 5.3 The deliverables, ordered so that each is independently useful

**The principle applied is that one body of work should yield more than one finding, and that the intermediate
artefacts should be usable by someone who does not run the study.**

| # | Deliverable | Why it stands alone |
|---|---|---|
| **D1** | **The script-dependence verdict** — the primary result: whether the form/context finding replicates in a logographic channel | This is the contribution, and it is a test of a published ACL 2025 conclusion against observed data from a script that conclusion excluded |
| **D2** | **A cross-script level-setting procedure** — operational levels, per-channel shape from the corpus, no channel-dependent instrument | Genuinely absent from the toolkits this field uses: §2.2 shows why the obvious instrument cannot do it, and the three degeneracies in §4.4 are the evidence. Useful to anyone comparing noise across scripts |
| **D3** | **The channel characterisation** (§4.3) — one procedure, three independent corpora, monotone ordering, saturation 0 | A descriptive result about three real error processes, with the instrument's limits stated |
| **D4** | **Generality checks** — Arabic (root-pattern, non-concatenative) and, if a corpus exists, kana | These convert "we tested three scripts" into "the effect is where the script says it should be" |
| **D5** | **The scale × script interaction**, if the run admits it | Wang et al. report a 70B anomaly their own design cannot explain; the same manipulation across scripts at two model sizes is a question the paper leaves open |

**D1 and D2 are the two that must not be lost**, because D1 is the claim and D2 is what makes a second study
possible. D3 and D4 are earned by the same runs. D5 is cheap only if models are already deployed, and is dropped
without loss if they are not.

### 5.4 What would falsify the restated goal

**Stated because a goal that cannot fail is not a goal.** The claim in §1 fails if, **in the Chinese channel,
context contributes as little as it does in English** — that is, if the logographic arm shows the same
form-dominant, context-independent profile. **That outcome is informative and would be reported as the result**:
it would mean the reliance on form is a property of the model shared across scripts, and that the recoverability
argument in §1 is wrong about what a logographic channel can carry.
