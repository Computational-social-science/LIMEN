# Phase II second channel ($s_1$): the evidence, and the decision it supports

**Status: EVIDENCE FOR A DECISION THAT HAS NOT BEEN MADE.** The choice of $s_1$ becomes binding only as an
amendment to `PHASE_II_PREREGISTRATION.md`, recorded before any data. This document assembles what is
verifiable so that the amendment can be written from sources rather than from memory.

**Written 2026-10-08**, after the items below were checked directly. Where a number or a citation is quoted, the
check that confirmed it is named in §4. Where a claim could not be confirmed, it is listed in §5 as
unconfirmed rather than repeated.

---

## 1. The criteria, quoted rather than restated

From `docs/PHASE_II_PREREGISTRATION.md` §5, which fixes them:

> **Required:**
> - (i) parallel intentions can be constructed under the same template, with constructive labels;
> - (ii) the noise process can be built **faithfully** from that channel's own input ecology;
> - (iii) the instrument can be pinned at a revision that reads the channel.
>
> **Forbidden:** implementing $\mathcal{N}_{s_1}$ as English typo operations applied to transliterated text.

And the mechanism tie-breaker, recorded in the same section **before** this evidence was gathered:

> A **segmentation or conversion channel** — an IME that commits to a wrong but perfectly ordinary word, a
> script without word delimiters where the wrong segmentation is still readable — produces **a surprising
> surface and a wrong answer**, which is the model-side signature. **If the choice is free, choosing a channel
> of the second kind makes the experiment test the mechanism rather than illustrate it.**

---

## 2. The instrument constraint is narrower than it looks, and it was measured

Criterion (iii) is the one that most easily disqualifies a candidate, so it was tested rather than assumed.

**The pinned instrument is English-only at the tokenizer level.** `config/pin_laya.json` pins
`convaiinnovations/laya` at immutable revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`, variant
**"root (English)"**. Tokenising fixed probe sentences with that revision's own tokenizer gives:

| script | chars | tokens | tokens/char | how it encodes |
|---|---:|---:|---:|---|
| English | 44 | 12 | **0.273** | word-level |
| German | 55 | 20 | **0.364** | subword, Latin |
| French | 58 | 22 | **0.379** | subword, Latin |
| Spanish | 53 | 22 | **0.415** | subword, Latin |
| Arabic | 42 | 32 | **0.762** | UTF-8 byte fallback |
| Thai | 56 | 62 | **1.107** | UTF-8 byte fallback |
| Korean | 24 | 38 | **1.583** | UTF-8 byte fallback |
| Japanese | 21 | 34 | **1.619** | UTF-8 byte fallback |
| Chinese | 14 | 29 | **2.071** | UTF-8 byte fallback |

Vocabulary is 50,368 tokens of byte-level BPE with **no CJK, Hangul, Arabic, Devanagari or Thai tokens at all**
— non-Latin input is encoded as raw bytes, i.e. as token sequences the model has no learned representation for.
**The pinned root cannot serve any non-Latin channel. Criterion (iii) fails for all of them at the current pin.**

**A language family with a distinct orthography is the only option that needs no new pin** — German, French and
Spanish are Latin-script and encode at 0.36–0.42 tokens/char. That is a real option and is not excluded here.

### 2.1 The multilingual artifact is a *different instrument*, not a subdirectory

`multilingual/` sits at the same commit, which invites the reading that pinning is unchanged. It is not, and the
repository tree at the pinned revision shows why:

| path | bytes | LFS digest |
|---|---:|---|
| `model.safetensors` (root) | 842,609,210 | — (separate file) |
| `multilingual/model.safetensors` | 643,835,514 | `9d628fd971b70038…` |
| `multilingual/tokenizer/tokenizer.json` | 34,363,188 | `609d8f4c067cd395…` |
| `multilingual/encoder/config.json` | 1,938 | — |
| `tokenizer/tokenizer.json` (root) | 3,583,228 | — |

Different weights, a different tokenizer an order of magnitude larger, and a different encoder config. **A pin
that fixes per-file SHA-256 fixes a different instrument when those files change** — which is exactly what
`config/pin_laya.json` does. Adopting the multilingual artifact is therefore **a re-pin under §5.5 and §12, not a
free subfolder**, and it carries the obligation those sections attach to a new artifact (an English sensitivity
run under it). The model card also ships the same weights as a standalone repository,
`convaiinnovations/laya-multilingual`, whose stated backbone is **ModernBERT-large, 395M** — not the
"mmBERT-base, 322M" that appears in one of the drafts this note was built from (§5).

---

## 3. Ranking against the criteria

### 3.1 English autocorrect / homophone conversion — fails (ii)

Mechanically this is the most attractive candidate: the committed output is a **valid, ordinary, high-frequency
English word** (`there` → `their`), which is precisely the "surprising surface, wrong answer" signature, and it
needs no change of instrument.

**It fails criterion (ii).** Confusion *inventories* are published — Carlson & Fette (2007) derive per-pair counts
from Google 1T n-grams; Jones & Martin (1997) give corpus counts — but an inventory is not a rate, and no source
was found reporting what fraction of homophone tokens an autocorrect actually mis-commits. **Building $\mathcal{N}_{s_1}$
from such an inventory would mean choosing the rate ourselves and calling it faithful**, and calibrating it
would require a **human recoverability pilot**. The project has already ruled human-rater agreement out of the
calibration path once, on the grounds that it measures the rater rather than the instrument. A channel whose only
faithful calibration is a human pilot re-introduces exactly what was removed.

*The remaining English candidates are worse, and for stated reasons:* corrector-induced real-word errors
(Shah & de Melo 2020) are explicitly an **induced** proxy, not observed ecology; the GitHub Typo Corpus is
developer commit text and no homophone-specific rate is published from it; MulTypo models **keyboard-adjacent
non-word** errors by construction and so is the substitution class the design wants to contrast against.

### 3.2 Japanese kana→kanji IME conversion — satisfies (i)–(iii), with a measured power risk

**(ii) is satisfied by a real, large, public corpus.** Tanaka, Murawaki, Kawahara & Kurohashi (2020),
*Building a Japanese Typo Dataset from Wikipedia's Revision History*, ACL 2020 SRW, **DOI
10.18653/v1/2020.acl-srw.31**, extracts **over half a million** typo–correction pairs, and states the property
this channel needs in its own words: *"the way people inputting kanji logographs results in typos with drastically
different surface forms from correct ones."* That is a conversion channel: the input method commits a different
kanji that is still an ordinary word.

**(i)** parallel intentions are constructible in the existing multiple-choice template — the pair
`機械学習` / `機会学習` differs by one kanji, shares its reading, and both are ordinary words with different
meanings, so the same item text carries two intentions with constructive labels.

**(iii)** is satisfied **only through a re-pin** to the multilingual artifact (§2.1), with the English
sensitivity run that a new artifact requires.

**The risk is real and it is documented, and it is the strongest argument in this document against the
candidate.** Mibayashi & Ohshima, *Evaluating the Robustness of Japanese LLMs to IME-Related and Typographical
Errors* (arXiv:2610.01241, 2026-10-01), report that *"Character Transposition and Character Replacement typos
consistently reduce accuracy across benchmarks, whereas **IME Conversion, Full-Width Conversion, and Homophone
Conversion have relatively limited impact**."* If conversion noise leaves accuracy essentially unchanged on the
models they tested, then an accuracy-based dependent variable may have almost no events to condition on, and
`SilentError@τ` would be measured on a near-empty cell. **This is a power risk, not a validity defect** — the
§6 recoverability-index calibration exists precisely to place $\lambda$ where the gold answer stops being
recoverable rather than at an assumed rate — but it must be written into the amendment, not discovered later.
The paper evaluated **Japanese LLMs**; the LIMEN instrument is a ~400M decision model, so the effect size need
not transfer, and that is a reason to calibrate rather than to assume.

### 3.3 The other non-Latin candidates

**Chinese (pinyin IME homophone selection)** is conversion-style and would satisfy the tie-breaker, and the
`multilingual/` artifact covers it. It ranks below Japanese for one reason: the corpus situation is worse.
The published error studies (Chen & Lee 2000) rest on a **non-public** 100-user typing corpus, and the READIN
benchmark is cited downstream rather than confirmed obtainable. **(ii) is therefore weaker, not stronger.**

**Korean (spacing/composition)** is a segmentation-flavoured channel with public corpora, but word-spacing is
**not** IME candidate selection; whether it fits §5.3's "IME-mediated input ecology" is a judgement this
document does not settle.

**Thai** has word segmentation ambiguity as a **script property**, not an input-method error — there is no IME
committing a wrong segmentation — and no corpus of user-committed segmentation errors was found. **Likely
disqualified on (ii).**

**Arabic** undotted/undiacritized forms are omitted **by convention** in ordinary writing, not by a typing
error; the published dot-removal results are synthetic adversarial perturbations. **No ecology, so no faithful
noise.**

---

## 4. How each load-bearing fact was checked

| Fact | Check performed |
|---|---|
| Tokenizer byte-fallback behaviour and the tokens/char table | Tokenised fixed probes with the pinned revision's own `tokenizer.json`; raw token IDs inspected |
| `multilingual/` is a separate artifact | Repo file tree fetched at the pinned revision through the mirror API; per-file byte counts and LFS digests compared against the root |
| `laya` model card claims | `README.md` at the pinned revision fetched and read |
| XNLI numbers | Read from that card: **"XNLI, 14 other languages 0.521 → 0.731"** — an aggregate over 14 languages |
| JWTD exists and says what is claimed | DOI resolved through Crossref (title, venue, year, authors) **and** the abstract read at ACL Anthology |
| Mibayashi & Ohshima exists and says what is claimed | `arxiv.org/abs/2610.01241` fetched; title, authors, date and **abstract** read — the "relatively limited impact" sentence is the paper's own |

## 5. Claims that could NOT be confirmed, and are therefore not relied on

- **"The `multilingual/` artifact needs no separate pin."** Appeared in a draft; **contradicted by the file-tree
  check in §2.1** and not repeated here.
- **"XNLI Japanese = 0.731."** Appeared in a draft; the card reports an **aggregate over 14 other languages**.
  Attributing that figure to Japanese alone would be the same defect the project caught once already, when a
  measured anchor was written as a published one.
- **"mmBERT-base, 322M."** Appeared in a draft; the model card says **ModernBERT-large, 395M**. The two cannot
  both be right and the card is the primary source; the architecture is recorded as unresolved.
- **"JWTD has four categories including a kanji-conversion category."** The abstract confirms the kanji-input
  typo class and the corpus size but **not a four-category taxonomy**. Category-level detail must be read from
  the paper before it is quoted.
- **A "LDC 2023" frequency claim** (there : their = 4.7 : 1) that a draft marked unverified: **no DOI, no paper**
  — correctly flagged, and it is not used here.

## 6. What this supports

**A recommendation, not a decision.** On the evidence:

- **English autocorrect fails (ii)** and cannot be made faithful without a human pilot the project has already
  ruled out of this role. It should not be selected.
- **Japanese kana→kanji IME conversion satisfies (i)–(iii)** and is the only candidate whose **(ii) rests on a
  real, large, public corpus** — at the cost of a re-pin to the multilingual artifact and an English sensitivity
  run under it.
- **The power risk is the thing to design against**: the amendment should carry the Mibayashi & Ohshima finding
  explicitly, and §6's recoverability calibration is the mechanism by which the noise is placed where it bites,
  rather than assumed to.

**A Latin-script second channel (German, French or Spanish) is the one option that needs no re-pin**, and it is
recorded here because choosing to re-pin is a cost that should be accepted deliberately rather than by default.

The amendment itself has not been written. That is a governance act on the protocol's own terms, and it belongs
to the project owner.
