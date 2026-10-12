# Position paper: what the project's scientific objective is

**Status:** positioning analysis. **Phase I confirmatory run complete (2026-10-05).** The scale question
(`docs/DATASET_REBUILD_DESIGN.md` §7.2) is downstream; Phase II pre-registration is the next step
once the Phase I seal is finalised.

**Companion documents:** `docs/POSTMORTEM_RRC_VALIDITY.md` (why the previous corpus was retired),
`docs/DATASET_REBUILD_DESIGN.md` (Phase II corpus design, pending Phase I seal).

**Source of the criteria used below:** *From Neural Scaling to Interaction Channels* — a synthesis of
the Shannon Scaling Law and a keyboard-bounded program on human–LLM noise. Its §11 gives a dependency
order, and its §9 gives admission rules for what counts as a result. Both are used here as the
standard the project is positioned against.

---

## 1. What the retired corpus actually was

An audit of the arms in `archive/rrc-v2.0.0-INVALID/` shows they were never six scripts. They were
**five error-generating mechanisms**, and they happen to span exactly the distinctions the synthesis
demands be kept apart:

| arm | source recorded in provenance | mechanism |
|---|---|---|
| `rrc-en-word` | Birkbeck `missp.dat` | word-level misspelling — a **spelling model**, not a keyboard |
| `rrc-en` | GitHub Typo Corpus, prose `.md`/`.rst` | typographical error in running English text |
| `rrc-ru` | GitHub Typo Corpus, Cyrillic lines | typographical error under a **ЙЦУКЕН** layout |
| `rrc-zh` | CSCD `all.tsv` (IME errors) | **input-method error**: keys → pinyin → wrong candidate |
| `rrc-zh-gh` | GitHub Typo Corpus, Han lines | Chinese text produced through an **IME** |
| `rrc-ja` | JWTD `test.jsonl` | **kana/kanji conversion** — an IME-shaped two-stage channel |

Mapped onto the synthesis's own vocabulary:

| RRC arm | its §7.2 layer | its §9.1 kind |
|---|---|---|
| `rrc-en-word` | cognitive | process noise |
| `rrc-en`, `rrc-ru` | **physical** (keyboard geometry) | observation noise |
| `rrc-zh`, `rrc-zh-gh`, `rrc-ja` | contextual / phonetic | semantic compression, intention ambiguity |

**The corpus therefore named as "script" and "language" what were in fact channel mechanisms.** That
is a conflation of three different axes, and the synthesis forbids it twice — §9.1 ("split what the
notes currently bundle as interaction noise") and §7.2 ("physical, cognitive, and contextual layers are
not the same random variable").

### 1.1 The consequence that was never diagnosed

The IME arms were the largest failure in the audit (`rrc-zh`: `edit = 22.8 %`, below chance;
`all decoys at similarity zero` on 89.8 % of items). The reason is now exact:

An IME error such as `可服用度` for `可复用度` preserves **the keystrokes and the pinyin exactly** and
differs only in the **selected character**. The discriminating variable in that channel is *phonetic*;
the surface variable is not. **The corpus scored candidates by character-level surface similarity — a
function blind to the very variable along which its own channel discriminates.** Zero similarity
everywhere was not a bug in the scoring; it was the scoring asking the wrong question of a channel it
had never characterised.

For the physical arms the same error ran the other way: a surface-similarity scorer *is* approximately
the right function for a keyboard channel, which is why `rrc-en` reached `edit = 99.7 %`. **One corpus,
two channel types, one scoring function: it was correct for one and blind for the other, and nothing in
the build could tell them apart.**

## 2. The category error

The synthesis's §11 opens with:

> **1. Fix the measurement model on the keyboard** (adjacency matrix, timing proxy, operational
> definition of contextual ambiguity). **No exponent before the likelihood.**

The retired corpus was built **items first**. Candidates were assembled and scored before any
`P(observation | intended)` existed for any arm. With no channel estimate there was nothing to draw
candidates from, so the only available criterion was surface similarity — and that is the mechanism by
which the corpus became a string-matching test.

**This is §11's step-4 trap displaced one level down.** The synthesis warns that writing the term into
the formula before the term is identified turns the program into a rename. The same move at the item
level — building the instrument before the channel is identified — turns it into a string-matching
benchmark. **The error is one of ORDER, and it was made twice for the same reason: the step that feels
like production was started before the step that makes production meaningful.**

## 3. Three positionings

| | Objective | Needs | Its result is | Admission (§9) |
|---|---|---|---|---|
| **A. Benchmark** | measure a model's ability at root recovery | valid items, and **scale** for comparative power | a ranking of models or scripts | fails until items are channel-generated (§2) |
| **B. Measurement model** | **what is the channel?** estimate `P(observation \| intended)` per mechanism | observed error corpora and an estimation procedure | a likelihood with its uncertainty, per mechanism | admits B directly; no scale requirement |
| **C. Separability / floor** | do the mechanisms' damages add (Prop. A); is there a residual scale does not buy (Prop. C) | B, plus an intervention at matched damage rate | additivity or interaction; a residual curve | needs randomisation (§9.4), not scale |

**D. SSL extension** (Proposition 1 / §11 step 4) is deliberately excluded from the table: §11 places it
after A and B, and states that the answer is allowed to be *do not add it*. Positioning there now would
reproduce the trap.

## 4. Recommendation

**Position the project at B, with C as its first scientific use, and D held open and expected to be
answered "no" or "not yet".**

Grounds:

1. **B is where the synthesis says to start** (§11 step 1), and it is the only one that is not
   downstream of an unbuilt instrument.
2. **B is what the project has already partially done and never noticed it had.** The IME
   characterisation produced earlier — 420 homophone groups, the largest holding 364 characters, a
   median homophone-group frequency rank of 3–4, `group_rank` as the true difficulty variable — **is a
   channel measurement.** It was reported as a feature of a corpus and buried inside a benchmark whose
   headline numbers are now withdrawn. Under B it is a result.
3. **B does not depend on SSL being right.** If SSL's ansatz is later displaced, a measured keyboard
   channel remains a measured channel. A benchmark built on a disputed ansatz inherits the dispute.
4. **C is the first genuinely falsifiable use of B**, and §9.4 already specifies its design
   (randomised injection at matched damage rate) — so it can be admitted without inventing criteria.
5. **D's expected answer is negative**, and a program positioned so that its headline result is
   allowed to be "the three-term denominator suffices" is a program that cannot be embarrassed by its
   own outcome.

**Stated as one sentence, for the record:**

> The project builds the **keyboard-and-IME channel's measurement model** — an estimated
> `P(observation | intended)` per error mechanism, with its separating variables named — and uses it to
> test whether those mechanisms' damages are separable, holding the SSL-extension question open and
> expecting the answer to be that no fourth term is yet earned.

**What this positioning forbids**, none of which is a matter of taste:

- Naming arms after scripts or languages. Arms are **mechanisms**.
- Scoring candidates for an IME channel with a surface-similarity function.
- Reporting any model accuracy before the channel for that arm is estimated and the trivial floor is
  printed beside it.
- Claiming generality beyond the mechanisms actually measured (§7.6: one modality cannot define a
  spectrum).

## 5. The scale question, resolved

`DATASET_REBUILD_DESIGN.md` §7.2 asked whether a much smaller corpus is acceptable, given that the
channel-conditioned construction discards every observation with a single plausible history, and
estimated the loss at up to two orders of magnitude.

**Under positioning B the question dissolves.** Identification does not scale with `n`; it scales with
the number of **mechanisms** and the **identifiability of their parameters**. A benchmark wants 100,838
items because it compares systems and needs statistical power. A measurement model wants enough
observations per mechanism to estimate that mechanism's parameters with a stated interval — a
requirement set by the estimator, not by a target count.

| | benchmark | measurement model |
|---|---|---|
| wants | items | observations per mechanism |
| its `n` is | statistical power | precision of an estimate |
| a 2-order reduction is | fatal | expected |

**So the shrinkage is not a cost of the rebuild; it is the signature of the objective having changed.**
The corpus that should have existed was never the large one.

## 6. What this changes in the rebuild design

`DATASET_REBUILD_DESIGN.md` stands, with three amendments:

1. **§1's scientific question is rewritten** to ask what the channels are and whether their damages
   separate, not what a model can do with them. The model becomes an *instrument applied to a measured
   channel*, not the object of study.
2. **§2's validity conditions acquire a per-mechanism parameter** — the channel against which `P(S|R_i)`
   is computed is the arm's own estimated channel, so an IME arm is scored phonetically and a keyboard
   arm geometrically. A single scoring function across arms is now a **stated defect**, not an
   implementation detail.
3. **§7's open question 2 is answered**: smaller is correct. Question 3 (which writing systems) is
   replaced by **which mechanisms**, and the answer must be one the estimator can identify.

## 7. Next step — Phase II pre-registration

**Phase I is complete.** The physical mechanism channel `P(observation | intended)` for English keyboard typos was estimated in the dev pre-run, yielding `π_d = 0.2036` and a calibrated noise generator `N_en`. The confirmatory run (2026-10-05) confirmed all three hypotheses.

> **The channel ESTIMATE was re-measured on 2026-10-12 and the earlier one is retired.** The first estimator classified residual errors without a transposition class, and `difflib` reports a single adjacent swap as an insert plus a delete of the same character (93-100% of cases, measured), so every transposition was scored as one insertion AND one deletion. The superseded artefacts are in `archive/keystroke_channel_SUPERSEDED_2026-10-12/` with the evidence in its `WHY_RETIRED.md`; the replacement is `scripts/trans_aware.py` and `figures/fig_error_structure.*`, verified in `docs/ERROR_STRUCTURE_VERIFICATION.md`. **The replacement reaches a stronger conclusion:** the deletion/insertion mass is not one process but two, double-dissociated by word length (`docs/PARADIGM_TYPING_AS_REGULATED_PROCESS.md`). `π_d` and `N_en` are unaffected by this correction, which concerns the composition of the channel, not the Phase I estimand.

**The next step is Phase II pre-registration**, which requires the Phase I seal first. Per the Protocol (§0.2, §5.1), Phase II pre-registration is filed **only after** Phase I instruments are frozen and pilot-stable. The seal is blocked only by the operational pre-run (pinned-instrument end-to-end dev run); once that runs, the seal is applied and Phase II pre-registration can be filed.

Phase II pre-registration must specify:
1. **Channel `s_1` selection** (one non-Latin/non-Latin script with documented input confusions, annotators, and a faithful `N_{s_1}` generator)
2. **Channel-specific `λ` levels** (not equated by "same edit rate as English" — equivalence justified by human pilot difficulty or documented empirical error rates)
3. **Phase II hypotheses** (H2.1 script×noise interaction, H2.2 SilentError contrast, H2.3 Coverage disparity)
4. **Power calculations** derived from Phase I measured effect sizes (π_d = 0.2036, accuracy contrast ≈ 12 points)

The admission rules (§9) apply: separability (Proposition A), exponent/threshold (Proposition B), precoding (Proposition C) must be satisfied before any SSL extension (Proposition 1) is considered. The answer to Proposition 1 is allowed to be "do not add it."
