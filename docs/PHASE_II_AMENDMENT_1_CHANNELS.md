# Phase II — Amendment 1 (filed before any Phase II data)

**Filed:** 2026-10-08 · **Governing:** `protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md` v1.24
· **Amends:** `docs/PHASE_II_PREREGISTRATION.md` §5 (channel selection), §5.5/§12 (artifact change),
§6 (noise equivalence), §9 (power)

**Everything here is decided BEFORE any Phase II data exists.** The pre-registration fixed the *criteria* for the
second channel and left the *choice* open pending evidence. This amendment records the choice and the evidence
that determines it. It supersedes nothing else in `PHASE_II_PREREGISTRATION.md`.

---

## A1 — The coverage is DERIVED, not chosen

§5 permitted three kinds of channel: a non-Latin script with documented digital-input confusions, a distinct
orthographic standard within a language family, or an IME-mediated ecology. That clause says which channels are
*admissible*. It does not say which channels a study *must* cover, and picking from a menu of admissibles is a
taste decision wearing a criteria costume.

The coverage is instead read off a source. **Li, Huang, Yao & Hyönä (2022), *Nature Reviews Psychology* 1,
133–144, DOI `10.1038/s44159-022-00022-6`** classifies writing systems by **how graphemes map to speech** into
exactly three categories — alphabetic (phoneme), syllabic (syllable), logographic (morpheme) — and argues that
findings from one cannot be assumed to transfer to another. So one channel per category is not a selection; it
is what the taxonomy leaves.

| # | Channel | Category | Script facts that matter here |
|---|---|---|---|
| 1 | **English** | alphabetic | spaced; phonology is recoverable from the form |
| 2 | **Japanese** | syllabic | kana is syllabic; the kanji inside it is logographic — Japanese is the mixed case, classified by the review under syllabic |
| 3 | **Chinese** | logographic | unspaced; a character maps to a morpheme and **the form does not indicate its own pronunciation** |

**The review supplies the justification in its own voice**, and it is the reason this is worth doing at all:
conclusions obtained from studies of alphabetic scripts *"cannot necessarily be extended to other writing
systems"*; *"no model to date has been systematically tested in different writing systems"*; and the comparison
*"should be [made] within the same study"*.

**The mechanism that must differ, also from the review (Table 1).** Alphabetic: *"Phonology can be easily
extracted from form"* → the phonological and direct-semantic routes are **cascaded** and used together.
Logographic: *"Form does not indicate phonology"* → the **direct semantic route is used primarily** and the
phonologically mediated route *"plays a minimal part for adult readers"*. **This is the loop the Phase I
mechanism predicts on**: a channel whose correct reading does not travel through the surface form should behave
differently from one whose reading does.

**What the amendment does NOT claim.** The review is a reading-mechanism review. It says nothing about language
models, input methods or noise, and it does not license any prediction about a model's confidence gate. Every
such link below is this project's inference, stated as one.

---

## A2 — The instrument, and the artifact change this amendment commits to

**Criterion (iii) was tested, not assumed.** `config/pin_laya.json` pins `convaiinnovations/laya` at immutable
revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`, variant *root (English)*. Tokenising fixed probes with that
revision's own tokenizer:

| script | tokens/char | how it encodes |
|---|---:|---|
| English | **0.273** | word-level |
| German / French / Spanish | 0.364 / 0.379 / 0.415 | subword, Latin |
| Arabic | 0.762 | UTF-8 byte fallback |
| Thai | 1.107 | UTF-8 byte fallback |
| Korean | 1.583 | UTF-8 byte fallback |
| **Japanese** | **1.619** | UTF-8 byte fallback |
| **Chinese** | **2.071** | UTF-8 byte fallback |

The vocabulary is 50,368 tokens of byte-level BPE with **no CJK, Hangul, Arabic, Devanagari or Thai tokens at
all**. **The pinned root instrument cannot read either non-Latin channel, so criterion (iii) fails for both at
the current pin.**

**DECISION — re-pin to the multilingual artifact.** The same revision ships a second artifact in its
`multilingual/` subtree with **its own weights (`model.safetensors`, 643,835,514 B), its own tokenizer
(34,363,188 B against the root's 3,583,228 B) and its own encoder config**. Because the pin fixes **per-file
SHA-256**, that is a **different instrument**, not a subdirectory of the existing one. Recorded separately in
`config/pin_laya_multilingual.json` (5 files, 678,201,636 B, every digest recomputed from the bytes); both pins
are verified by `scripts/check_pin_integrity.py`, which now discovers every `config/pin_laya*.json` rather than
naming one file.

**And it was RUN, not merely recorded.** `measurement/smoke_predict_multilingual.py`:

- **resolved revision** `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`, subfolder `multilingual`;
- the router's own reason for the non-Latin items: *"non-Latin script (kana, 100% of letters); the English
  checkpoint cannot read it"* — and the same for `han`;
- seven items routed, three English (control) and four non-Latin.

**The English sensitivity run is NOT optional and this is why.** Under the multilingual artifact the three
English control items gave `c` of **0.9589, 0.6756, 0.3346**, while the four non-Latin items gave **0.9430,
0.9917, 0.9950, 0.9986**. Two item sets of unmatched difficulty and a gloss that is not a gold label mean this
is **not a cross-channel result** — it is a demonstration that the artifact changes English behaviour, which is
precisely the confound §5.5/§12 attach a sensitivity run to. **All English cells are re-run under the
multilingual artifact, and any cross-channel contrast is computed within that artifact.**

---

## A3 — The datasets, and the rule that chose them

Each channel's noise process is built from a **corpus of observed human behaviour**. This is not a preference:
the programme's global rule 17 requires it, on the ground that a simulation of an error distribution is evidence
about the simulator, and a study fed simulated errors reports a clean result about a population that does not
exist while internal consistency never reveals it. `config/datasets.json` declares every dataset with a
`provenance` of `observed` or `simulated`, and `scripts/check_dataset_provenance.py` reads it.

**All measurements below are from `config/data_manifest.json`, regenerated from the bytes on disk by
`scripts/build_data_manifest.py` and checked by the guard suite.**

| Channel | Primary | Kind of observed behaviour | Measured |
|---|---|---|---|
| English | **Birkbeck Spelling Error Corpus** | real native-speaker spelling errors, compiled and distributed by Roger Mitton | **6,136 words / 36,133 misspellings** — *exactly* the compiler's published counts |
| Japanese | **JWTD** (Tanaka, Murawaki, Kawahara & Kurohashi, ACL 2020 SRW, `10.18653/v1/2020.acl-srw.31`) | real Wikipedia revision history | **515,328 train + 8,542 test pairs**; licence **CC-BY-SA 3.0** |
| Chinese | **CSCD-NS** (Hu, Meng & Zhou, ACL 2024 long paper 10, pp. 146–159) | **real posts by official media accounts on Sina Weibo** | **40,000 rows**, split 30,000 / 5,000 / 5,000; licence **MIT** |

**A question this amendment CLOSES with a measurement.** The evidence document
(`docs/PHASE_II_S1_CHANNEL_EVIDENCE.md`) recorded that the JWTD paper does not report the size of its
kanji-conversion subset and that it *"may be a small fraction"*. Measured: **kanji-conversion is 235,490 pairs —
45.7 % of the training set, the LARGEST of the four categories.** The concern was unfounded, and it is now
settled by counting rather than by inference.

**Why the Japanese channel is the one that TESTS the mechanism.** JWTD's kanji-conversion category is a
**conversion** channel: the committed form is a different but **ordinary** word sharing the reading —
`入場 → 入城`, `固体 → 個体`. That is the "surprising surface, wrong answer" signature that the Phase II
pre-registration predicts will be **quiet**, against Phase I's substitution errors which were **loud**. The same
property holds for Chinese, verified by inspecting labelled examples: `说到 → 说道`, `惟一 → 唯一`,
`共通 → 共同`, `渡假村 → 度假村`, `不在 → 不再` — ordinary words for ordinary words.

### A3.1 The rejected alternative, recorded so it is not re-opened

`LCSTS-IME-2M` **sits in the same repository as CSCD-NS**, is **~50× larger** (2,000,000+ samples), uniformly
formatted and trivially loadable — and is **constructed by simulating pinyin IME input**. It is rejected as
primary evidence by rule 17: it would measure the simulator's assumptions about IME errors, which is the
quantity under study. **A later session with a bigger machine must not re-open this on the strength of sample
size.** It may be used for pipeline bring-up and power analysis, labelled as simulated at every point of use.

Also recorded and not selected: SIGHAN 2013/2014/2015 (observed, retained as a cross-check candidate because
its source-distribution documentation is thinner); the GitHub Typo Corpus, LEMON and Readin (licence not
established as open, and their source ecologies are not this channel's — developer commits, multi-domain text,
and controlled re-entry respectively).

### A3.2 Three scope caveats, stated so no rate is quoted as natural

1. **Birkbeck** includes, in the compiler's own words, *"the efforts of young children and extremely poor
   spellers being subjected to spelling tests way beyond their ability"*. The error **distribution** is usable;
   the error **rate** is not an adult typist's.
2. **CSCD-NS** carries an annotated error in **~46 % of sentences in every split** (measured: 0.4596 train,
   0.4628 dev, 0.4606 test). That is a property of how a spelling-check corpus is assembled, **not** a natural
   error rate. The error **types** are observed behaviour; the **rate** is a construction artefact.
3. **JWTD's test set is crowdsource-filtered and therefore less noisy** than its training set, which makes the
   test set the better source for a noise model even though it is **60× smaller**. Which split supplies
   $\mathcal{N}_{s_1}$ is fixed in the noise-equivalence step (§6), not here.

---

## A4 — What this amendment fixes, and what it deliberately leaves open

**Fixed here, before any data:** the coverage (three channels, one per writing-system category); the instrument
change and the obligation to re-run English under it; the three primary datasets and their provenance class; the
rejected alternative and its reason; and the three scope caveats.

**NOT fixed, and not to be inferred from this document:** the form of $\mathcal{N}_{s_1}$ per channel (which
substitutions, at what rate, drawn from which subset) — that is §6's noise-equivalence step, and for Chinese it
must be built from CSCD-NS's observed error **types** rather than from its construction **rate**; the value of
$\lambda$ and the calibration ladder; the number of items and the power procedure; and the ordering of the
channels. **None of these may be set by a script written before the noise-equivalence argument is made.**

**One acquisition fact, recorded because it is not visible from the files.** The Chinese corpus could not be
fetched from this machine at all: `drive.google.com` answered **HTTP 000** after a 22 s timeout, and the
documented alternative is Baidu Netdisk, which needs an account and a client. **The programme owner downloaded
it by hand.** The correct response to that blocker was to record it, not to substitute the simulated dataset
sitting beside it in the same repository.
