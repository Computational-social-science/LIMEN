# ERROR_STRUCTURE_VERIFICATION.md

**Adversarial verification of the "surviving errors are not a single motor process" claim.**
Verifier: `err-verifier` (task-5). Date: 2026-10-12.
Scripts: `E:\2026-AI4S\wb-diag\ev_*.py`. Raw data: `C:\keystroke-corpus\files` (168,593 files).
Sample: 20,000 files, seed 20261012, 300,000 sentences — the same sample as the measurement under test.

**Bottom line.** Every published number reproduces **exactly** — I get 0 mismatches on all 5 class
counts, all 15 `cls_by_pos` cells, all 10 decile counts, all 3 `case_by_pos` cells and both
`prev_err` cells. So the arithmetic is clean. But three of the six claims are stated in a
**numerator convention that silently drops insertions**, and one of those drops is the entire
basis of claim 4. The headline position effect **survives the truncation test** (-25%), and the
H1/H2 double dissociation **survives every attack I could construct**.

---

## 1. Verdict table

| # | Claim | Verdict | What actually happened |
|---|-------|---------|------------------------|
| 1 | Class mix 37.0 / 30.5 / 15.7 / 8.6 / 8.2 | **CONFIRMED as computed — REFUTED as interpreted** | Reproduces to the digit (37.02 / 30.49 / 15.73 / 8.57 / 8.19). But 100% of transpositions are counted as one insertion **plus** one deletion (section 5). Deletion and insertion are both inflated. |
| 2 | Word-first case 74.2%; middle/last deletion 58.6% / 67.6% | **PARTIALLY REFUTED** | Reproduces exactly **only** if insertions are removed from the numerator. With all errors: 62.4% / 41.9% / 43.2%. The published figures use a different denominator from claim 1 without saying so. |
| 3 | Per-position rate 10.23 / 5.55 / 14.64 | **PARTIALLY REFUTED** | Reproduces exactly, same convention. Including insertions: 12.17 / 8.15 / 23.70. The published 14.64 **drops 36.8% of word-last errors** (19,631 insertions). |
| 4 | Word-initial 8.82 vs internal 2.40 (3.7x) | **REFUTED** | The 3.7x is an artefact of a counter fed only by `replace` opcodes. Full attribution: 10.48 vs 7.10 = **1.48x**. Excluding case errors: **0.43x** — word-initial is *lower*. |
| 5 | U-shape: 13.58 / ~5 / 13.16 | **PARTIALLY REFUTED** | Reproduces exactly, but bucket 9 is not a decile (19.9% of all characters) and bucket 0 is 78.9% case errors. Excluding case, decile 0 = 2.89 — **below** the middle. It is a J-shape, not a U. |
| 6 | 2.615 backspaces vs 0.463 surviving errors/sentence; 63.6% | **CONFIRMED (numbers) / REFUTED (comparison)** | All three reproduce exactly. But backspaces are keystrokes and surviving errors are aligned edits; one transposition scores 2. Under the published convention the numerator is 0.322/sentence, so the ratio is 8.1:1, not 5.65:1. |
| A | Truncation kills the position effect | **REFUTED — the effect survives** | 16.66% of word-last and 17.11% of decile-9 errors are prefix-truncation. Removing them: last 14.64 -> **11.02** (-24.7%), decile 9 13.16 -> **9.62** (-26.9%). Both survive. |
| B | Denominator correct; len-1 words double-counted | **CONFIRMED / not double-counted** | Rates are per character-exposure and correct. len-1 words are counted **once, as `first` only** — never `last`. So `last` *excludes* 4.74% of words. Under-counted, not double-counted. |
| C | Case errors are a modelling decision | **CONFIRMED** | 82.1% of all case errors are sentence-initial (k=0). Drop them and word-first falls from 10.23 to **2.64** vs middle 5.05 — word-first is *below* middle. |
| D | Alignment artefact inflates ins/del | **CONFIRMED, near-total** | 11/11 adjacent transpositions -> `insert`+`delete`. My 40k generator: 98.26% `insert,delete`, 1.74% `delete,insert`, **0% clean**. Detector verified: 100% recovery, 0% FP on different-character pairs. |
| E | Space handling inflates the boundary effect | **CONFIRMED, 6.9% of errors** | 9,512 errors (6.85%) are anchored on space characters and are dropped from `cls_by_pos` entirely. So `cls_by_pos` totals != `cls` totals by exactly 9,512. |

---

## 2. Centrepiece — the truncation test (confound A)

### 2.1 Method

A truncated transcription registers as a run of deletions at the end of the target. I classified a
section as truncated iff `USER_INPUT` is a non-empty **strict prefix** of `SENTENCE`. I also
computed two independent detectors: a trailing `delete` opcode whose `a1` reaches `len(target)`,
and `under_typed` = (printable keystrokes < `len(target)`), which catches truncation even when the
participant backspaced over the gap.

### 2.2 How much truncation is there?

| Quantity | Count | Share of 300,000 sections |
|---|---|---|
| Exact match (`USER_INPUT == SENTENCE`) | 216,383 | 72.13% |
| **Strict prefix (truncated)** | **8,978** | **2.99%** |
| Trailing `delete` reaching target end | 15,296 | 5.10% |
| Under-typed (printable strokes < len target) | 18,526 | 6.18% |
| Under-typed **and** zero backspaces | 16,273 | 5.42% |
| Zero backspaces | 109,198 | 36.40% |

Truncation is **short**: of the 8,978 prefix-truncated sections, 8,856 (98.6%) are missing exactly
one character and each contributes exactly 1.000 errors on average — i.e. they are almost all a
single dropped final character (overwhelmingly the final `.` or `?`). Only 66 sections are missing
6+ characters.

### 2.3 Concentration of the artefact

| Position | All errors | From prefix-truncated sections | Share |
|---|---|---|---|
| first | 28,770 | 87 | 0.30% |
| middle | 47,226 | 412 | 0.87% |
| **last** | **53,385** | **8,893** | **16.66%** |

| Decile | All errors | From prefix-truncated | Share |
|---|---|---|---|
| 0-7 | 73,882 | 1 | 0.00% |
| 8 | 8,981 | 71 | 0.79% |
| **9** | **55,557** | **9,505** | **17.11%** |

The artefact is concentrated **exactly** where the claim is elevated — 17% of the elevation comes
from 3% of the sentences. That is the strongest form of the confound.

### 2.4 Does the elevation survive? Yes.

Position profile, **published convention** (insertions excluded, `ref_cls_by_pos`):

| Subset | first | middle | last | last/first |
|---|---|---|---|---|
| ALL (as published) | 10.23 | 5.55 | **14.64** | 1.43 |
| **EXCL prefix-truncated** | 10.50 | 5.65 | **11.02** | **1.05** |
| EXCL under-typed | 8.85 | 4.44 | 11.44 | 1.29 |

Position profile, **all 5 classes** (internally consistent):

| Subset | first | middle | last | last/first |
|---|---|---|---|---|
| ALL | 12.17 | 8.15 | 23.70 | 1.95 |
| EXCL prefix-truncated | 12.50 | 8.34 | 20.35 | 1.63 |
| EXCL under-typed | 10.73 | 6.91 | 20.76 | 1.94 |

Decile profile (`ref_dec_err`, published convention):

| Subset | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| ALL | 13.58 | 5.49 | 5.56 | 4.82 | 5.05 | 5.09 | 5.17 | 5.39 | 5.57 | **13.16** |
| **EXCL prefix-trunc** | 14.00 | 5.66 | 5.73 | 4.97 | 5.20 | 5.25 | 5.33 | 5.56 | 5.68 | **9.62** |

**Verdict: the last-position and decile-9 elevations survive truncation removal.** Word-last falls
14.64 -> 11.02 (-24.7%) and decile 9 falls 13.16 -> 9.62 (-26.9%); the middle deciles rise ~3.1%
because the denominator loses the truncated characters. These match the Lead's figures exactly.
The effect is real, but **a quarter of its published magnitude was truncation.**

### 2.5 The mechanism is the *sentence-final word*, not "word-last"

Splitting the word-last category by exposure (truncation excluded, insertions excluded):

| Category | Exposure | Errors | Rate /1000 |
|---|---|---|---|
| first | 2,294,329 | 24,263 | 10.58 |
| middle | 5,614,439 | 32,689 | 5.82 |
| **sentence-final word end** | **291,022** | **10,992** | **37.77** |
| mid-sentence word end | 1,894,814 | 13,869 | 7.32 |

Sentence-final words are **13.3%** of "last" exposure but **44.2%** of "last" errors — a **5.2x**
rate ratio against mid-sentence word ends. The "word-last" effect is almost entirely an
**end-of-sentence** effect. This is a real and reportable phenomenon, but "word-last position" is
the wrong label for it.

---

## 3. Alignment artefact (confound D) — quantified

### 3.1 Raw `difflib` behaviour

`difflib.SequenceMatcher` has no transposition class. For `"the quick brown fox"` -> `"the qucik brown fox"`:

```
insert   t[6:6]=''   p[6:7]='c'
delete   t[7:8]='c'  p[8:8]=''
```

An insertion of a character and a deletion of **the same character**, separated by one equal block.

### 3.2 Incidence

| Generator | n | `insert,delete` | `delete,insert` | clean |
|---|---|---|---|---|
| Exhaustive adjacent swaps, 12-letter alphabet | 11 | 11 (100%) | 0 | 0% |
| My random generator (40,000 edits, mixed word lengths) | 7,402 | 98.26% | 1.74% | **0%** |

The artefact is **near-total**, confirming the Lead. My clean 0% (vs the Lead's 3.9%) is because my
generator skips swaps of identical adjacent characters, where the "edit" is a no-op; those are not
real transpositions and should not be counted either way.

### 3.3 Verifying the Lead's detector

`scripts/trans_aware.py`, run against **my own** generator (different RNG, different word list,
lengths 2-14):

| True edit | n | Recovered as intended |
|---|---|---|
| transposition | 7,402 | **100.00%** |
| substitution | 7,645 | 98.63% |
| deletion | 7,648 | 100.00% |
| insertion | 7,813 | 100.00% |
| double-letter typo | 7,695 | 100.00% |

**100% transposition recovery — the Lead's 96.5% is conservative, not optimistic. The detector has
no recovery bug.** (The 1.37% "substitution" misses are substitutions that happen to land on an
adjacent key, which is a labelling choice, not an error.)

### 3.4 False positives

| Case | Result | Correct? |
|---|---|---|
| Genuine ins+del, **different** characters, 20,000 randomised pairs | 0% called transposition | yes |
| Genuine ins+del, **same** character, 9,691 randomised pairs | 99.6% called transposition | see below |
| Double-letter typo `the cat sat` -> `the catt sat` | `ins_align` 1 | yes, not swallowed |
| Double-letter on existing double `letter` -> `letterr` | `ins_align` 1 | yes |
| Triple letter `letter` -> `letterrr` | `ins_align` 2 | yes |
| Two separate insertions | `ins_align` 2 | yes |
| Two separate deletions | `del_align` 3 | yes |
| `the quick brown fox` -> `thex quick brown fo` (genuine ins at 3, genuine del at 18) | `transposition` 2 | **false positive** |

**One genuine false-positive mode exists**: when a participant coincidentally inserts and deletes the
*same character* at different places, the detector merges them. This is unavoidable for any
observationally-based classifier — a same-character insert+delete at distance 3 is *indistinguishable*
from a transposition of distance 3. It is a **definitional limit, not a bug**. The practical bound is
that it can only affect pairs where the moved character is identical.

### 3.5 Corrected class mix

Transposition-aware, 300,000 sentences, transposition counted as 2 units per event (the Lead's
counter convention):

| Class | Count | Share | Published |
|---|---|---|---|
| deletion | 45,330 | **32.64%** | 37.0% |
| insertion | 36,254 | **26.10%** | 30.5% |
| case | 21,854 | 15.73% | 15.7% |
| transposition | 12,172 | **8.76%** | — (invisible) |
| adjacent | 11,903 | 8.57% | 8.6% |
| other substitution | 11,376 | 8.19% | 8.2% |

This reconciles with the Lead's corrected mix (32.6 / 26.0 / 15.8 / 8.9 / 8.6 / 8.2) to within
0.15 pp. Indel share 67.5% -> **58.7%**.

**Caveat for the figure**: transposition is counted as **2 units** because it consumed two
opcodes. Every other class is one error per unit. If transposition is counted as **one event**
(6,086 events), the mix is deletion 34.13%, insertion 27.30%, case 16.46%, **transposition 4.58%**,
adjacent 8.96%, other 8.57%. The 8.9% figure is an artefact of double-counting. **Report 8.9% only
with the "2 opcodes per event" convention stated, or use 4.6%.**

---

## 4. The other confounds

### 4.1 Denominator (B) — correct per character; len-1 words under-counted

- `first` exposure = **2,364,492 = exactly the number of words**. Correct per-character, not per-word.
- `last` exposure = **2,252,488 = words - len-1 words** (2,364,492 - 112,004). Correct.
- **len-1 words (4.74% of words) are counted once, as `first` only. They are never `last`.**
  They are **not double-counted** — the opposite. The `last` category systematically *excludes*
  1-character words, biasing it toward longer words.

Word-length composition and rates expose this:

| Position | len 1 | len 2 | len 3 | len 4+ |
|---|---|---|---|---|
| first (share of exposure) | 4.7% | 17.9% | 19.7% | 57.7% |
| last (share of exposure) | **0.0%** | 18.8% | 20.6% | 60.6% |
| **first rate /1000** | **31.36** | 10.14 | 10.75 | 11.70 |
| **last rate /1000** | — | 8.41 | 12.66 | **32.21** |

The word-first "elevation" is driven by 1-character words (31.36/1000 — and 4.7% of that is case
errors on sentence-initial "I" and "A"). The word-last elevation is driven by long words
(32.21/1000 at len 4+). **Both position effects are word-length composition effects as much as
position effects.**

### 4.2 Case (C) — confirmed, and it kills the word-first story

- 21,854 case errors = 15.73% of all errors.
- **82.1% (17,941) are at `k == 0`, the sentence-initial character.** All of those are word-first.
- Case errors by position: first 17,941 / middle 2,871 / last 1,042.

Removing case errors from the published convention:

| Position | With case | **Without case** |
|---|---|---|
| first | 10.23 | **2.64** |
| middle | 5.55 | **5.05** |
| last | 14.64 | 14.17 |

**Word-first is *below* word-middle once capitalisation is excluded** (2.64 vs 5.05). I confirm the
Lead's case-convention kill (Lead: 2.68 vs 5.14; the 0.04 difference is the insertion convention —
the Lead's figure includes insertions, mine excludes them; both point the same way). The word-first
"error elevation" is **capitalisation convention, not typing error.**

Class mix with case removed: deletion 43.9%, insertion 36.2%, adjacent 10.2%, other 9.7%.

### 4.3 Space handling (E) — 6.85% of errors are silently dropped from the position analysis

- 9,512 errors are anchored on a **space character**: 5,062 deletions (9.8% of all deletions),
  4,166 insertions (9.8% of all insertions), 284 other substitutions.
- These get `pos = None` and are therefore **excluded from `cls_by_pos`** but retained in `cls` and
  `dec_err`. That is why `cls_by_pos` sums to 129,381 against `cls` 138,893 — a **6.85% discrepancy**.
- Space deletions merge two words; they are attributed to no word at all. So the "boundary effect"
  cannot be read off `cls_by_pos`.

`prev_err` (the claim-4 counter) is worse than that: it is incremented **only inside the `replace`
branch**, so it omits *every* pure deletion and *every* pure insertion — 93,760 of 138,893 errors.
That is the mechanism of the claim-4 failure:

| Attribution | word-initial | word-internal | ratio |
|---|---|---|---|
| Script's `prev_err` (replace branch only) | **8.82** | **2.40** | **3.67x** (published) |
| Full consistent attribution | 10.48 | 7.10 | 1.48x |
| Full, excluding case errors | 2.90 | 6.71 | **0.43x** |

### 4.4 Decile definition (claim 5) — bucket 9 is not a decile

The script uses `dec = max(1, n // 10)` then `min(9, k // dec)`. For a 45-character sentence
`dec = 4`, so bucket 9 absorbs `k = 36..44` **plus everything past 40** — in practice bucket 9 holds
**19.9% of all characters** (2,483,098 of 12,473,692) versus 8.9% for each of buckets 0-8. The
"last decile" is twice the size of every other bucket.

Two further facts about the "U":

- Bucket 0 is **78.9% case errors**. Excluding case, the decile profile becomes
  2.89 / 4.62 / 4.95 / 4.23 / 4.53 / 4.34 / 4.54 / 4.51 / 4.69 / **12.51**.
  **The left arm of the "U" disappears entirely.** Decile 0 is *below* the middle.
- The right arm is real (12.51 even without case) and is the same sentence-final effect as 2.5.

**The U-shape is a J-shape: flat middle, no start elevation once capitalisation is excluded, and a
genuine end-of-sentence spike.**

---

## 5. H1/H2 double dissociation — attacked, survives

Claim: adjacent-key substitution rate is **flat** across word length while deletion and insertion
**scale** with it. Design: case excluded, prefix-truncated sections excluded (291,022 sentences).

### 5.1 Replication of the Lead's exposure table

My exposure matches `h1h2.json` **exactly** for lengths 1-11. Length 12 differs because I bucket
`12+` (278,187 chars) and the Lead used exactly 12 (159,288). Conclusion unaffected: adjacent is
1.291 at len 11, 1.086 at len 12+, and the Lead's 1.136 at exactly 12.

### 5.2 The dissociation, and its bootstrap

| Class | len 2 | len 12 | ratio | 95% CI (per-participant bootstrap) |
|---|---|---|---|---|
| adjacent | 1.164 | 1.086 | **0.93x** | **[0.82, 1.06]** |
| deletion | 2.084 | 5.428 | **2.60x** | [2.39, 2.85] |
| insertion | 1.239 | 4.583 | **3.70x** | [3.30, 4.16] |

Bootstrapped over **participants** (2,000 resamples of 20,000 files), not characters. The adjacent
ratio's CI **contains 1.0**; deletion and insertion CIs are far from it. Monotonicity holds at every
intermediate length for deletion (2.08, 2.47, 2.46, 2.87, 3.77, 4.43, 5.43) and insertion
(1.24, 1.95, 2.02, 3.74, 4.31, 4.44, 4.58).

### 5.3 Attack 1 — is it just boundary dilution? No.

Normalising on **interior characters only** (dropping word-first and word-last from both numerator
and denominator), len 3 -> len 12:

| Class | ratio | 95% CI |
|---|---|---|
| adjacent | **0.98x** | [0.82, 1.16] |
| deletion | 2.04x | [1.84, 2.26] |
| insertion | 3.57x | [3.03, 4.24] |

Adjacent remains flat with only interior characters. The flatness is **not** an artefact of long
words diluting boundaries. Excluding only word-first gives the same picture (adjacent 0.91x,
deletion 2.57x, insertion 4.83x).

### 5.4 Attack 2 — is it a sentence-position effect? No.

Holding decile fixed, adjacent is flat across word-length groups within every decile:

| decile | len <= 4 | 5-7 | 8+ |
|---|---|---|---|
| 0 | 0.957 | 0.794 | 0.789 |
| 4 | 1.002 | 0.937 | 1.045 |
| 8 | 1.119 | 1.029 | 1.001 |

Deletion and insertion scale monotonically with word length **within every decile** (e.g. decile 4
deletion: 2.66 / 2.59 / 3.34; decile 8 insertion: 1.66 / 1.69 / 2.85). The word-length effect is
not a sentence-position effect.

### 5.5 Attack 3 — does the transposition artefact create the scaling? No, it strengthens it.

With my own transposition-aware classifier, **transposition itself scales with word length**
(interior-only, len 3 -> len 12: **2.24x**, CI [1.87, 2.70]) — like deletion and insertion, unlike
adjacent. So the artefact inflates deletion and insertion, but removing it does not remove the
scaling. **Transposition behaves as a word-structure-indexed class, not as a motor slip** — which
is an additional argument for the two-process reading, not against it.

### 5.6 Verdict on the dissociation

**The double dissociation survives.** Adjacent-key is flat (0.93x, CI contains 1.0) and stays flat
under interior-only normalisation (0.98x) and within every sentence decile; deletion, insertion
**and transposition** scale with word length under all three controls and under participant-level
bootstrap. I could not break it.

**Residual caveats** (weaken, do not kill):

1. The `adjacent` class is defined by a hand-built QWERTY adjacency set (8.57% of errors). The
   flatness is only as good as that model.
2. Word length correlates with word **frequency and type**; the scaling in deletion/insertion is
   consistent with word-level planning but not uniquely diagnostic of it.
3. Adjacent at len-1 is 0.516/1000, about half the plateau. The flatness is a len >= 2 phenomenon.

---

## 6. What survives and what does not

### Safe to publish in a figure

| Number | Value | Basis |
|---|---|---|
| **Truncation prevalence** | 2.99% of sections are strict prefixes; 98.6% of those are missing exactly 1 char | 2.2 |
| **Position effect after truncation control** | last **11.02** vs first 10.50 vs middle 5.65 /1000 (published convention); or 20.35 / 12.50 / 8.34 with all classes | 2.4 |
| **Decile-9 effect after truncation control** | **9.62** vs middle ~5.5 /1000 | 2.4 |
| **Sentence-final word effect** | 37.77 vs 7.32 /1000 = **5.2x**; 13.3% of exposure, 44.2% of errors | 2.5 |
| **Case-convention kill** | word-first 2.64 vs middle 5.05 /1000 excluding case errors | 4.2 |
| **H1/H2 dissociation** | adjacent 0.93x [0.82, 1.06]; deletion 2.60x [2.39, 2.85]; insertion 3.70x [3.30, 4.16] | 5.2 |
| **Interior-only dissociation** | adjacent 0.98x [0.82, 1.16]; deletion 2.04x; insertion 3.57x | 5.3 |
| **Transposition artefact** | 98.26% of transpositions -> `insert`+`delete`; detector recovery 100% | 3.2-3.3 |
| **Corrected class mix** | deletion 32.64%, insertion 26.10%, case 15.73%, transposition 8.76% (2 units/event), adjacent 8.57%, other 8.19% | 3.5 |
| **Backspace prevalence** | 2.615/sentence; 63.60% of sentences contain >=1 backspace | 1 claim 6 |

### Must be dropped or restated

| Number | Problem | Restatement |
|---|---|---|
| **10.23 / 5.55 / 14.64** | numerator silently excludes insertions; 14.64 drops 36.8% of last-position errors | Use 12.17 / 8.15 / 23.70 (all classes) or state the exclusion |
| **74.2% / 58.6% / 67.6%** | same convention, and inconsistent with the 37.0%/30.5% in claim 1 | 62.4% / 41.9% / 43.2% with all classes, or state the exclusion |
| **8.82 vs 2.40 (3.7x)** | `prev_err` is fed by the `replace` branch only — omits 93,760 of 138,893 errors | 10.48 vs 7.10 (1.48x); **0.43x** excluding case |
| **U-shape / 13.58 at decile 0** | bucket 0 is 78.9% case errors; excluding case it is 2.89 — *below* the middle | "J-shape": flat middle, no start elevation, end spike at 12.51 |
| **"decile 9"** | bucket 9 holds 19.9% of characters, not 10% | Use exact deciles, or call it "final fifth" |
| **"word-last position"** | the effect is the *sentence-final word* (5.2x vs mid-sentence word ends) | Relabel as end-of-sentence |
| **transposition 8.9%** | counts 2 units per event; every other class counts 1 | 8.9% with the convention stated, or **4.58%** as events |
| **0.463 surviving errors/sentence vs 2.615 backspaces** | backspaces are keystrokes, errors are aligned edits; 1 transposition = 2 errors | 0.322/sentence under the published convention -> 8.1:1, not 5.65:1 |
| **word-first "elevation"** | driven by 1-char words (31.36/1000) and capitalisation | Report word-length composition alongside |

### Figure panels that must be re-checked

`figure-maker` was told to mark the at-risk panels pending verification. My verdict on each:

- **Per-position rate panel (10.23/5.55/14.64)** — at risk on two counts (numerator convention and
  the sentence-final confound). **Rebuild** from 2.4/2.5, or annotate the exclusion.
- **Class-mix-by-position panel (74.2/58.6/67.6)** — **rebuild** with a stated, consistent
  numerator. Currently inconsistent with the headline class mix.
- **Decile/U-shape panel** — **rebuild**. The left arm is not there once case is excluded, and
  bucket 9 is twice the size of the others.
- **Word-initial vs internal 3.7x panel** — **drop**. It is a counter artefact plus capitalisation.
- **H1/H2 word-length dissociation panel** — **safe**. Survives truncation, interior-only
  normalisation, decile control and participant bootstrap.
- **Truncation-control panel** — **safe and should be shown**; it is a genuine robustness check.

---

## 7. Independent-recomputation note

I recomputed from the raw corpus rather than the JSON, using the same sample seed so that
discrepancies are attributable to method, not sampling. My faithful replication
(`ev_main3.py`, `ref_*` counters) reproduces `error_structure2.json` with **0 mismatches** across
all five class counts, all fifteen `cls_by_pos` cells, all ten `dec_err` buckets, all three
`case_by_pos` cells and both `prev_err` cells.

**Additional data quirks found (not in the task brief):**

1. **Scientific-notation numeric fields.** 8 of 3,000 sampled files contain values like
   `1.477579e+12` in `PRESS_TIME`/`RELEASE_TIME`/`KEYSTROKE_ID`. With
   `on_bad_lines='skip'`, pandas silently **drops** those rows. Measured impact is negligible
   (~1 row per file, ~0.004% of rows) but it is a silent data-loss path in both the script under
   test and `trans_aware.py`.
2. **Blank `LETTER` with VK-only `KEYCODE`.** In some files `LETTER` is empty and only the
   `KEYCODE` (Windows virtual-key code, e.g. `72` = 'H') carries the character: 1,365,002 rows
   (9.4%) are blank-`LETTER`, in 31,109 of 300,000 sections. **A keystroke-replay reconstruction of
   `USER_INPUT` is therefore impossible for ~10% of sections** — my first replay attempt matched
   only 68% of sections. This does not affect the script under test (which reads `USER_INPUT`
   directly), but it rules out any replay-based verification.
3. **Parse quirks confirmed and handled:** 18 split rows (literal newline inside `LETTER`) and
   29 ten-field rows in 14.6M physical lines across the sample; all retained, 0 dropped.

---

## 8. Confidence

| Finding | Confidence |
|---|---|
| Exact replication of the published counters | **Very high** — 0 mismatches, deterministic |
| Truncation is 2.99% and supplies 17% of the last-position/decile-9 elevation | **Very high** |
| Position effect **survives** truncation removal | **High** — survives 3 independent exclusion definitions |
| Claim 4 (3.7x) is a counter artefact | **Very high** — mechanism identified and reproduced |
| Case-convention kill of word-first | **Very high** |
| U-shape left arm is case errors | **High** |
| Transposition artefact near-total; detector correct | **High** — 100% recovery, 0% FP on different-char pairs |
| H1/H2 double dissociation survives | **High** — survives interior-only, decile control, participant bootstrap |

**Net assessment.** The headline *qualitative* claim — surviving errors are not a single motor
process — is **supported**, and its strongest evidence (the H1/H2 double dissociation) survives
every attack I could build. But **five of the six specific published numbers need restatement**:
three because the numerator silently excludes insertions, one because the counter only sees
`replace` opcodes, and one because the "decile" is not a decile. A quarter of the published
position effect was truncation. None of this overturns the conclusion; all of it changes the
numbers that go in the figure.

---

## 9. Reproduction commands

```
$PY = C:\Users\Administrator\AppData\Local\hermes\tools\python-3.14.7+20260901-win32-x64\python.exe

& $PY E:\2026-AI4S\wb-diag\ev_scan.py    400  20261012   # parse quirks, replay feasibility
& $PY E:\2026-AI4S\wb-diag\ev_main3.py   20000 20261012  # faithful replication + both conventions
& $PY E:\2026-AI4S\wb-diag\ev_main4.py   20000 20261012  # per-decile per-class + bootstrap inputs
& $PY E:\2026-AI4S\wb-diag\ev_h1h2.py    20000 20261012  # H1/H2 word-length, transposition-aware
& $PY E:\2026-AI4S\wb-diag\ev_lastword.py                 # sentence-final vs mid-sentence word end
& $PY E:\2026-AI4S\wb-diag\ev_trans_mix.py                # corrected class mix
& $PY E:\2026-AI4S\wb-diag\ev_align.py                    # difflib transposition signature
& $PY E:\2026-AI4S\wb-diag\ev_trans.py                    # detector recovery + false positives
& $PY E:\2026-AI4S\wb-diag\ev_final.py                    # verdict tables
& $PY E:\2026-AI4S\wb-diag\ev_dec.py                      # decile profile + bootstrap
& $PY E:\2026-AI4S\wb-diag\ev_h1h2_report2.py             # interior-only + participant bootstrap
```

All scripts are read-only with respect to the corpus and write only under `E:\2026-AI4S\wb-diag\`.
`scripts/error_structure2.py` was read but **not modified**.
