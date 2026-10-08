# Second Channel (s₁) Candidate Assessment for LIMEN Phase II

**Protocol constraints (PHASE_II_PREREGISTRATION.md §5, protocol §5.3):**
- (i) Parallel intentions constructible under one prompt template with constructive labels
- (ii) Noise process buildable **faithfully** from channel's own input ecology (NOT English typos on transliteration)
- (iii) Instrument pinned at revision reading the channel
- **Forbidden:** English typo operations on transliterated text
- **Mechanism tie-breaker:** Segmentation/conversion channel (wrong but ordinary word) > substitution channel (implausible surface)

**Pinned instrument:** `convaiinnovations/laya` @ `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851` (root = English); ships `multilingual/` subfolder (mmBERT-base, 322M, 256k vocab, 100+ langs, Apache-2.0). Revision is **immutable commit SHA**, not branch.

---

## Ranked Candidates

| Rank | Candidate | Conversion vs Substitution | Evidence Quality (DOI/arXiv) | Faithful Noise Feasibility | Instrument Requirement |
|------|-----------|----------------------------|------------------------------|----------------------------|------------------------|
| **1** | **Japanese (kana→kanji IME conversion)** | **CONVERSION-STYLE** — Homophone conversion yields *wrong but ordinary word* (e.g., 機械学習 → 機会学習, both valid words, meaning flipped). JWTD "kanji-conversion" category: typo shares reading, 0 shared chars, **real word**. Mibayashi & Ohshima (2026) Homophone Conversion typo: 回答/解答, 対象/対照, 機械/器械/機会 — **all ordinary words**. | **High.** JWTD: Tanaka et al. (2020) ACL SRW, **DOI: 10.18653/v1/2020.acl-srw.31** — 500k+ typo-correction pairs from Wikipedia revisions, 4 categories incl. *kanji-conversion*. Mibayashi & Ohshima (2026) arXiv:2610.01241v1 — 5 typo categories, benchmarks on JMMLU/JCommonsenseQA/JamC-QA, 11 models. Hagiwara & Mita (2020) LREC — GitHub multilingual typo corpus incl. Japanese. | **(a) Parallel intentions: YES.** Template: multiple-choice QA (JMMLU style). Examples: Q: "機械学習の定義は？" (def of machine learning) vs "機会学習の定義は？" (def of opportunity learning) — same template, different kanji, both valid. (b) **Corpus: YES.** JWTD (public, 500k+ pairs) + GitHub typo corpus. Kanji-conversion subset directly usable. (c) **Model: PINNED laya-multilingual reads Japanese.** mmBERT-base (Gemma-2 tokenizer) covers 1833 langs incl. Japanese; laya-multilingual model card reports XNLI Japanese 0.731 (vs English-only 0.521). Pin: `convaiinnovations/laya`@55cf4c4, subfolder=`multilingual`. |
| **2** | **Chinese (Pinyin IME homophone selection)** | **CONVERSION-STYLE** — Wrong homophone yields *valid Chinese word/phrase* (e.g., 参加 sanka → 酸化 sanka "oxidation"; 妈 ma → 吗 ma question particle). Microsoft (2000) typing model: real-user Pinyin errors cause **conversion to wrong but valid characters**. Chen & Lee (2000) Table 3.1: actual input error rate 20.84% vs perfect 6.82% — **tripling** due to IME propagation. | **High.** Chen & Lee (2000) Microsoft Research, **ACL 2000** (DOI via ACL Anthology) — 100 users, 8h each, statistical typing model trained on real errors. READIN benchmark (cited in arXiv:2610.01241v1 §2.3) — Chinese pinyin input mistakes + speech errors. CHIME (Li et al., IJCAI 2011) — error-tolerant Pinyin IME. | **(a) Parallel intentions: YES.** Template: multiple-choice. Example: Q: "参加の意味は？" (meaning of participation) vs "酸化の意味は？" (meaning of oxidation) — same Pinyin `sanka`, both valid words. (b) **Corpus: PARTIAL.** READIN benchmark exists (pinyin input mistakes) but not fully public; CHIME data not obviously released. Microsoft typing corpus (100 users) not public. Would need to synthesize from JWTD-style Wikipedia revisions for Chinese (exists but less documented). (c) **Model: PINNED laya-multilingual reads Chinese.** Model card lists Chinese (zh); XNLI Chinese covered. Same pin as Japanese. |
| **3** | **Korean (Hangul spacing / IME composition)** | **SEGMENTATION-STYLE (conversion-adjacent)** — Spacing errors: `이옷은` → `이 옷은` ("this clothing" vs "this is clothing") — **both valid readings, meaning flips**. Kor-Native corpus (Yoon et al. 2023): word spacing (WS) is **dominant error for native speakers** (Fig 1). KAGAS WS category: 100% annotator agreement. Jamo-level composition errors also produce valid but wrong syllables. | **High.** Yoon et al. (2023) arXiv:2210.14389v3 — **Kor-Native (17,559 pairs), Kor-Learner (28,426), Kor-Lang8 (109,559)** — all public (NIKL license for research). KAGAS auto-annotation toolkit. Lee (2014) cited: only ~20% natives fully master spacing rules. ACM CHI 2010 user study (Ilinkin et al.) — total error rate 4.8–5.9% on mobile IMEs. | **(a) Parallel intentions: YES.** Template: QA. Example: "이옷은 더러워요" (this-clothing is-dirty) vs "이 옷은 더러워요" (this clothing is-dirty) — spacing flips subject. Or particle errors: `하와이에서` vs `하와이에` (KAGAS PART category). (b) **Corpus: YES.** Kor-Union (155k+ pairs) public via GitHub/NAIST/Korpus. WS edits directly extractable. (c) **Model: PINNED laya-multilingual reads Korean.** Model card: Korean accuracy 0.110→0.490 (English→multilingual). mmBERT-base covers Hangul. Same pin. |
| **4** | **Thai (no word delimiters → segmentation ambiguity)** | **SEGMENTATION-STYLE** — Wrong segmentation yields *valid but different word sequence* (e.g., `กินข้าว` "eat rice" vs `กิน ข้าว` "eat rice" — same here but compound ambiguities: `นักเรียน` "student" vs `นัก เรียน` "study Nak"). Nakwijit & Purver (2022): 32.4% sentences have misspellings; **vowel substitution, tone modification, consonant deviation** dominate — mostly **intentional** (86.4%), some create valid words. Unintentional typos (106 in test) include keyboard-proximity errors yielding non-words. | **Medium-High.** Nakwijit & Purver (2022) **LREC, DOI via ACL Anthology 2022.lrec-1.24** — 3000 sentences, 1484 misspellings, 728 unique types, 5 annotators, intentional/unintentional split. Wisesight Sentiment corpus (base) public. Haruechaiyasak & Kongthon (2013) 4 intentional classes. Lertpiya et al. (2020) neural correction pipeline. | **(a) Parallel intentions: UNCERTAIN.** No explicit word boundaries → "same template" hard to define. Could use character-level classification template, but constructive gold-label rule (§5) assumes word-level intentions. Segmentation ambiguities are **not IME-mediated** in the protocol's sense — they're script-inherent, not input-method errors. (b) **Corpus: YES for misspellings** (Wisesight + Nakwijit annotations), **NO for segmentation errors** as digital-input ecology — no published corpus of *user-committed* segmentation errors from IME/keyboard. (c) **Model: PINNED laya-multilingual reads Thai.** mmBERT-base covers Thai (explicitly listed). Model card: 51 langs incl. Thai. Same pin. |
| **5** | **Arabic (undotted / undiacritized forms)** | **SUBSTITUTION-STYLE (primarily)** — Missing diacritics/dots yields **homographs** (same skeleton, different meaning): `سعب` (sa'b "difficult") vs `شعب` (sha'b "people") — **both valid words**, but the *digital input error* is **omission**, not conversion. Al-Kokoschka (2020): dots sometimes **forgotten in handwriting/social media** to bypass filters. Diacritization systems (Tashkeela, etc.) treat restoration as *recovery*, not *conversion error*. Error typology (Springer 2020): "replacement error" = valid wrong word (24.18%), "non-existence error" = non-word (11.27%). | **Medium.** Tashkeela corpus (large public diacritized Arabic). Diacritization benchmarks: DER/WER metrics. arXiv:2111.09791 — **undotted Arabic adversarial effect on Transformers** (dots removed post-hoc, not IME errors). Darwish et al. (2017) Tashkeela. Alqahtani et al. (2019) survey. | **(a) Parallel intentions: YES.** Template: diacritization disambiguation. Example: `كتاب` (kitāb "book") vs `كُتِبَ` (kutiba "was written") — same undotted form, diacritics flip meaning. (b) **Corpus: NO for *digital input* errors.** Tashkeela = *correct* diacritized text. No published corpus of **user-typed undotted/undiacritized errors** from IME/keyboard. Diacritics omitted *by convention* (97%+ words), not by error. "Dotless Arabic" (arXiv:2111.09791) is synthetic adversarial, not natural error ecology. (c) **Model: PINNED laya-multilingual reads Arabic.** Model card: Arabic 0.110→0.400. mmBERT-base covers Arabic. Same pin. |

---

## Single Best Non-Latin Candidate

**Japanese (kana→kanji IME conversion)**

### Strongest Argument FOR
- **Conversion-style errors are native to the IME ecology** (kanji-conversion = wrong candidate selected from homophone list) — **exactly the mechanism Phase I predicts should be *quiet* (H2.4)**.
- **Public, large-scale, faithful corpus exists** (JWTD: 500k+ pairs, kanji-conversion category explicitly identified, DOI: 10.18653/v1/2020.acl-srw.31).
- **Pinned instrument already reads it** — `laya-multilingual` subfolder at same revision, Apache-2.0, XNLI Japanese 0.731.
- **Parallel intentions trivial** via existing JMMLU/JCommonsenseQA benchmarks (already used in Mibayashi & Ohshima 2026).

### Strongest Argument AGAINST (must be stated)
> **The Homophone Conversion typo in Mibayashi & Ohshima (2026) had *negligible* accuracy impact (avg Δ = −0.004, some models *no degradation*).** If the noise process is too easy for the model, the cross-channel contrast (H2.2–H2.4) may lack statistical power — the "quiet" signature may be *too quiet* to detect a frontier/discrimination gap. Calibration (§6) would need to push λ_mid to near-saturation to elicit measurable discordance, risking ceiling/floor effects. **This is a power/design risk, not a validity defect** — but it must be acknowledged in the pre-registration amendment.

---

## Uncertain Claims (explicitly marked)

| Claim | Uncertainty |
|-------|-------------|
| Korean spacing errors are "conversion-style" | They are **segmentation errors**, not IME candidate-selection errors. Protocol §5.3 permits "IME-mediated input ecology such as conversion errors" — spacing is **composition/spacing**, not conversion. May not satisfy (ii) as written. |
| Thai segmentation ambiguities qualify as "digital input confusions" | Protocol §5.3: "non-Latin script with documented digital input confusions". Thai has **no IME** — segmentation is script-inherent, not input-method-mediated. **Likely disqualified** on (ii). |
| Arabic undotted forms are a "digital input error ecology" | Diacritics/dots are **omitted by convention** (97%+), not by typing error. arXiv:2111.09791 shows adversarial effect of *synthetic* dot-removal, not natural user errors. **No corpus of user-committed omission errors exists.** |
| Chinese READIN benchmark is publicly obtainable | Cited in arXiv:2610.01241v1 §2.3 but **link/availability unverified**. Microsoft typing corpus (Chen & Lee 2000) not public. |
| laya-multilingual's per-language calibration holds at Phase I temperature map | Temperature map shipped with PINNED revision has **one out-of-range entry** (choice:11+ = 0.1006, clamped to 0.5 with warning). Multilingual subfolder may have **different calibration**; not verified. |
| JWTD kanji-conversion subset size sufficient for calibration | JWTD = 500k+ total pairs; **kanji-conversion subset size not reported** in paper. May be small fraction. |

---

## Recommendation

**Proceed with Japanese (kana→kanji IME conversion) as s₁.**

- Pin: `convaiinnovations/laya`@`55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`, subfolder=`multilingual`
- Noise process: JWTD kanji-conversion pairs → estimate per-homophone-set confusion rates → build λ_lo/λ_mid via recoverability index (§6)
- Parallel intentions: JMMLU 4-choice template, homophone-swapped distractors
- Pre-registration amendment: record Japanese choice, cite JWTD + Mibayashi & Ohshima (2026) + laya-multilingual model card
- Power procedure (§9): measure π_d on dev items *after* noise calibration, then set N