# Phase II Second Channel Audit: English Autocorrect / Homophone-Conversion Errors

**Prepared for:** LIMEN project — Registered Report Phase II channel selection (s₁)
**Date:** 2026-10-08
**Status:** Decisive literature-and-evidence review; feeds a frozen amendment before data collection

---

## 1. Frozen Criteria (Quoted Verbatim)

From **PHASE_II_PREREGISTRATION.md §5** and **NHB_Orthographic_Channels_JEV_Research_Protocol.md §5.3**:

> **Required:**
> - (i) parallel intentions can be constructed under the same template, with constructive labels;
> - (ii) the noise process can be built **faithfully** from that channel's own input ecology;
> - (iii) the instrument can be pinned at a revision that reads the channel.
>
> **Forbidden:** implementing $\mathcal{N}_{s_1}$ as English typo operations applied to transliterated text. That would make the noise an artefact of the transliteration and the contrast a statement about it.

From **PHASE_II_PREREGISTRATION.md §5 (mechanism prediction):**
> A **segmentation or conversion channel** — an IME that commits to a wrong but perfectly ordinary word, a script without word delimiters where the wrong segmentation is still readable — produces **a surprising surface and a wrong answer**, which is the model-side signature. **If the choice is free, choosing a channel of the second kind makes the experiment test the mechanism rather than illustrate it.**

---

## 2. Shortlist of Candidate Noise Processes for English Conversion-Style Errors

| # | Candidate | Primary Source(s) | Empirical Evidence for Realism | Error Type | Real-Word? |
|---|-----------|-------------------|--------------------------------|------------|------------|
| **A** | **Mobile/desktop autocorrect homophone substitution** (its↔it's, their↔there↔they're, your↔you're, to↔too↔two) | Carlson & Fette (2007) — ICMLA; Jones & Martin (1997) — ANLP; Muylle et al. (2026) — *J. Mem. Lang.* 146:104703; Kukich (1992) survey | **Carlson & Fette (2007):** Empirical confusion-set counts from Google 1T n-grams: its/it's (2,158), their/there/they're (5,576), your/you're (734), lead/led (264), weather/whether (361). **Jones & Martin (1997):** Corpus counts: it's/its (1,577/391), you're/your (734/220), their/there/they're (4,176). **Muylle et al. (2026):** Controlled typing experiments (N=124); homophone substitution errors = ~25% of misspellings in final texts (Connors & Lunsford 1992; Lastres López & Manalastas 2018). **Kukich (1992):** 25–40% of all spelling errors are real-word errors. | **Real-word substitution** (valid English word swapped for another valid English word; phonologically identical, orthographically distinct) | **YES** — every substitution yields a valid dictionary word |
| **B** | **Autocorrect-induced real-word errors ("atomic typos")** — dictionary-based corrector replaces a non-word typo with a *wrong but valid* word | Shah & de Melo (2020) — LREC 2020 (arXiv:2005.01158); Hirst & Budanitsky (2005) | **Shah & de Melo (2020):** "many such errors are now *caused* by autocorrection software"; they induce real-word errors by running a dictionary corrector (Enchant) on character-level corruptions and *forcing* the top incorrect suggestion. **Twitter Typo Corpus (Aramaki 2010):** 39,171 typo→correction pairs; error distribution: substitution 15,000, insertion 9,000, deletion 9,500, replication 3,000, transposition 2,500. Real-word errors induced via corrector are a *downstream* product of this pipeline, not directly observed in the corpus. | **Real-word substitution** (but mediated by a corrector; the *surface* error is a valid word) | **YES** — by construction (corrector only proposes dictionary words) |
| **C** | **GitHub Typo Corpus (Hagiwara & Mita, 2020)** — 350k+ edits from GitHub commits, including "spell" edits (misspellings) and "grammatical" edits | Hagiwara & Mita (2020) — LREC (arXiv:1911.12893) | **350k edits, 65M chars, 15+ languages.** Human annotation of 200 English edits: categories include "Spell" (misspellings) and "Grammatical" (which may include homophone confusions). However, the corpus is **commit-based** (developer text), not mobile/autocorrect ecology. No published breakdown of homophone vs. non-word within "Spell" edits. | Mixed: mostly **non-word** typos (dokument→document); some real-word grammatical edits | **PARTIAL** — only the "Grammatical" subset; no published rate for homophone-specific edits |
| **D** | **MulTypo (Zhao et al., 2025)** — keyboard-layout-aware typo generator (replacement, insertion, deletion, transposition) | Zhao et al. (2025) — ACL 2025 (arXiv:2510.09536) | **Explicitly models QWERTY adjacency + 10-finger typing.** Validated via human naturalness judgments (superior to naive baseline). **Does not model homophone/autocorrect conversions** — only character-level keyboard slips. | **Non-word** (character-level edits producing implausible strings) | **NO** — by design (keyboard-adjacent substitutions produce non-words) |
| **E** | **Japanese IME/Homophone Conversion (arXiv:2610.01241)** — predefined homophone sets (回答/解答, 対象/対照, etc.) | arXiv:2610.01241 (2024) | **11 Japanese LLMs × 3 benchmarks.** Homophone Conversion: 10% of candidate instances replaced. **Avg accuracy drop = 0.004** (negligible). Predefined sets are small (5–6 pairs) and language-specific. | **Real-word substitution** (kanji conversion errors) | **YES** — but **Japanese-only**; no English analogue published |

---

## 3. Evaluation Against Frozen Criteria

| Criterion | Candidate A (Autocorrect homophone substitution) | Candidate B (Autocorrect-induced via corrector) | Candidate C (GitHub Typo Corpus) |
|-----------|---------------------------------------------------|--------------------------------------------------|----------------------------------|
| **(i) Parallel intentions under same template, constructive labels** | **YES** — English intent templates (Phase I) can be reused; gold labels are constructive (the intended word is known by construction). Homophone pairs are predefined. | **YES** — same as A; the corruption is applied to the clean English item. | **YES** — but the noise is not channel-specific; it's a mix of developer typos. |
| **(ii) Faithful noise process from channel's own input ecology** | **PARTIAL** — Strong empirical *inventories* (Carlson & Fette, Jones & Martin, Muylle et al.) document *which* homophones are confused and *relative frequencies*. **Gap:** No published **per-keystroke or per-word error rate** for autocorrect-specific homophone substitutions in mobile/desktop ecology. Muylle et al. measure *typing* homophone errors (dictation/QA), not *autocorrect* errors. | **WEAK** — The "error replacement" step (Enchant forced confusion) is a **synthetic proxy**, not a faithful model of autocorrect behavior. Shah & de Melo admit this is induced, not observed. | **NO** — GitHub commits reflect *developer* editing (code + docs), not mobile autocorrect ecology. No evidence this ecology matches the target channel. |
| **(iii) Instrument pinned for the channel** | **YES** — Phase I instrument (Laya English root, pinned at 55cf4c4e) reads English; no multilingual router needed. | **YES** — same as A. | **YES** — same as A. |
| **Forbidden construction?** | **NO** — This is *not* "English typo ops on transliterated text." It is a **conversion-style channel** (wrong but ordinary word committed by an IME-like process), which the protocol *predicts* will produce *silent* errors (H2.4 direction). | **BORDERLINE** — The character-level corruption step *is* English typo ops; the corrector step adds conversion. The *composite* may be argued to inherit the forbidden character. | **NO** — but fails (ii) decisively. |

---

## 4. Best Candidate: **Candidate A — Autocorrect Homophone Substitution**

### 4.1 Why it is the best fit
- **Mechanism alignment:** It is a **conversion channel** (IME-like): the user intends word *w*, the autocorrect commits *w'* (a valid, frequent word, phonologically identical). This matches the protocol's predicted *segmentation-or-conversion* signature (errors *silent*, AUC *decreases* or stays flat, conditional error *rises*).
- **Empirical inventory exists:** Carlson & Fette (2007) and Jones & Martin (1997) provide **published confusion-set counts** from large-scale corpora (Google 1T, Brown corpus). Muylle et al. (2026) provide **controlled experimental evidence** that homophone interference is real, syntactic-category-independent, and ~25% of final-text misspellings.
- **Real-word by definition:** Every substitution is a valid English word — the core design requirement for "silent" errors.
- **English instrument compatible:** No multilingual router needed; Phase I pin works.

### 4.2 Critical Gap: **No published autocorrect-specific error rate**
- The literature documents **human typing/production** homophone errors (Muylle et al.), **corpus confusion frequencies** (Carlson & Fette), and **spell-checker correction targets** (Jones & Martin).
- **No paper reports:** "In mobile autocorrect usage, X% of homophone tokens are incorrectly converted to Y." The LDC 2023 claim cited in blog posts ("there outnumbers their 4.7:1 in uncurated web text") is **unverified** — no DOI, no paper.
- **Calibration route:** Phase II pre-registration §6 requires either (a) human pilot recoverability or (b) documented per-channel empirical error rates. **We have neither for autocorrect homophone conversion.** A human pilot would be required.

---

## 5. Proposed Construction Recipe (Auditable, Reproducible)

If the project accepts the gap and proceeds with a human pilot for calibration, the following recipe implements Candidate A faithfully:

### 5.1 Substitution Pairs (Drawn from Carlson & Fette 2007 + Jones & Martin 1997)
| Confusion Set | Members | Relative Corpus Frequency (Carlson & Fette) | Directionality |
|---------------|---------|---------------------------------------------|----------------|
| **there/their/they're** | there, their, they're | 5,576 (combined) | there > their > they' |
| **your/you're** | your, you're | 734 (your) / 220 (you're) | your > you're |
| **its/it's** | its, it's | 2,158 (combined) | it's > its (in web text) |
| **to/too/two** | to, too, two | Not directly counted; high frequency | to ≫ too > two |
| **affect/effect** | affect, effect | Not in top tables; common in literature | — |
| **lose/loose** | lose, loose | — | — |
| **weather/whether** | weather, whether | 361 | — |
| **lead/led** | lead, led | 264 | — |
| **cite/sight/site** | cite, sight, site | — | — |
| **role/roll** | role, roll | — | — |

**Selection rule:** Use the **top 10 confusion sets** from Carlson & Fette (2007) Table 1 (or the 18 sets from Jones & Martin 1997) that are **heterographic homophones** (different spelling, same pronunciation). Exclude same-spelling pairs.

### 5.2 Rate Control
- **Per-token substitution probability `p_homophone`** — calibrated via human pilot (recoverability index) per Phase II §6 route (a).
- **Directionality:** Sample the *substituted* word from the confusion set with probabilities proportional to **corpus frequency of the *wrong* word** (mimicking autocorrect's bias toward higher-frequency forms). E.g., for intended `their`, substitute `there` with prob ∝ freq(`there`), `they're` with prob ∝ freq(`they're`).
- **Context independence (baseline):** Apply per-token independently. *Advanced:* condition on preceding POS (e.g., `their` before noun vs. `there` after preposition) using a lightweight tagger — but this adds complexity; document as a design choice.

### 5.3 Reproducibility
- **Deterministic generator:** `noise(item_id, λ, seed) → corrupted_text`
- **Seed policy:** Same as Phase I — frozen seeds {0,1,2} carried in pack name.
- **Configuration pinned:** JSON config specifying confusion sets, relative frequencies, `p_homophone` per λ level (lo/mid), and POS-conditioning flag.
- **Version control:** Generator code + config + confusion-set CSV committed to repo; SHA-256 recorded in pre-registration amendment.

### 5.4 Calibration (Per Phase II §6)
- **Route (a) Human Pilot:** Recruit N≥20 native English speakers; present clean vs. corrupted items; measure **recoverability index** = noisy-channel posterior mass on intended word (same index as Phase I, anchored at Rayner et al. 2006 interior-scrambled = 0.4480).
- **Target:** Select `λ_lo`, `λ_mid` such that recoverability spans a non-saturating range (cf. Phase I separation 6.07 pooled seed SD).
- **Report:** Anchor value used, per-level recoverability, pilot N, demographics.

---

## 6. Comparison Against Forbidden Construction

| Aspect | Forbidden: "English typo ops on transliterated text" | Candidate A: Autocorrect Homophone Substitution |
|--------|------------------------------------------------------|--------------------------------------------------|
| **Noise primitive** | Character-level: adjacent-key sub, transpose, del, ins | **Word-level: whole-word substitution** from a confusion set |
| **Surface form** | Implausible string (non-word or low-probability) | **Perfectly ordinary, high-frequency word** |
| **Ecology** | Keyboard adjacency (physical) | **Autocorrect/IME commitment (linguistic conversion)** |
| **Error "loudness"** | **Loud** — surface form improbable under intended meaning (Phase I result) | **Predicted silent** — surface form unsurprising, meaning wrong (protocol §5 mechanism) |
| **Channel type** | Substitution-style (Phase I) | **Segmentation/conversion-style (Phase II target)** |
| **Protocol status** | **Explicitly forbidden** | **Matches the "second kind" the protocol favors** |

**Verdict:** Candidate A is **genuinely different in kind**. The forbidden construction applies *character-level typo operations* to a transliterated string, producing *orthographic noise*. Candidate A applies *lexical conversion* (whole-word substitution by a conversion engine), producing *semantic noise with intact orthography*. This is exactly the contrast the protocol designed Phase II to test.

---

## 7. Published Work Using Homophone/Autocorrect Noise in LLM Evaluation

| Work | Noise Type | Models / Tasks | Results | Source |
|------|------------|----------------|---------|--------|
| **cx0/llm-typos (GitHub)** | Homophone substitution (8 pairs: its/it's, cite/sight, hole/whole, role/roll, soul/sole, steal/steel, tail/tale, waist/waste) | Claude-3 Opus/Sonnet/Haiku; retrieval task (preceding/following word) | Homophones degrade retrieval; Opus more robust than Sonnet/Haiku. No aggregate accuracy reported. | GitHub repo (no DOI/arXiv) — **unsupported for formal citation** |
| **Healthcare LLM robustness (PMC12923095, 2024)** | Homophone substitution (10–30% of words) + typographical errors + redaction | GPT, BlueBERT, Llama; sentiment, medical condition classification, QA | Homophones & typos: **mild, similar effects** (most conditions stable/improved); Redaction: **largest degradation**, only catastrophic drops. Homophone most affected QA tasks. | **PMC12923095** — PMID/ID verifiable |
| **Japanese LLM robustness (arXiv:2610.01241)** | Homophone Conversion (10% of candidates; 5 predefined sets) + IME Conversion + char-level typos | 11 Japanese LLMs (Swallow, ELYZA, llm-jp, Sarashina); JMMLU, JCommonsenseQA, JamC-QA | **Homophone Conversion: avg accuracy drop 0.004** (negligible). Character Transposition/Replacement: consistent degradation. | **arXiv:2610.01241** — verifiable |
| **Shah & de Melo (2020) "Correcting the Autocorrect"** | Induced real-word errors via dictionary corrector (Enchant) on character-corrupted text | BERT, RoBERTa, etc.; error detection/correction on food/movie reviews | Generated datasets enable context-aware correction; models improve on induced errors. **Noise is synthetic proxy, not observed autocorrect errors.** | **LREC 2020, arXiv:2005.01158** — DOI verifiable |
| **MulTypo (Zhao et al., 2025)** | Keyboard-layout typos only (replace/insert/delete/transpose) — **NO homophone/autocorrect** | 18 LLMs (Gemma, Qwen, OLMo); 5 tasks × 12 languages | Typos consistently degrade performance; instruction tuning increases brittleness. **Does not test homophone conversion.** | **ACL 2025, arXiv:2510.09536** — DOI verifiable |

**Key finding:** **No published work evaluates English LLMs under a faithful autocorrect-homophone noise process.** The Japanese study (arXiv:2610.01241) is the closest but uses a tiny predefined set and finds negligible impact. The healthcare study uses homophone substitution but at high rates (10–30%) without ecological grounding.

---

## 8. Unsupported Claims (Marked Explicitly)

| Claim | Status | Reason |
|-------|--------|--------|
| "Autocorrect homophone error rate is X% in mobile typing" | **UNSUPPORTED** | No peer-reviewed source with DOI/arXiv reports this. Blog posts cite "LDC 2023 analysis" — no such publication found. |
| "GitHub Typo Corpus contains Y% homophone edits" | **UNSUPPORTED** | Paper reports "Spell" vs "Grammatical" categories but no homophone-specific breakdown. |
| "Muylle et al. (2026) measures autocorrect errors" | **UNSUPPORTED** | Measures *typing production* errors (dictation/QA), not autocorrect substitutions. |
| "Shah & de Melo's induced errors match real autocorrect errors" | **UNSUPPORTED** | Authors explicitly induce errors via corrector; they do not claim ecological validity for the *autocorrect* step. |
| "MulTypo can generate homophone errors" | **FALSE** | MulTypo only does character-level keyboard typos (replace/insert/delete/transpose). |

---

## 9. Recommendation

**Candidate A (Autocorrect Homophone Substitution) is the only scientifically defensible option** among English conversion-style channels, **provided**:

1. **A human pilot is run** to calibrate `λ_lo`/`λ_mid` via recoverability index (Phase II §6 route a), because **no published autocorrect-specific error rate exists**.
2. **The confusion sets and directionality probabilities are drawn from Carlson & Fette (2007) and Jones & Martin (1997)** — the only published, corpus-grounded inventories.
3. **The generator is implemented as a word-level substitution process** (not character-level), with deterministic seeding, pinned config, and version control — making it auditable and distinct from the forbidden construction.

**If the project cannot run a human pilot**, Candidate A **fails criterion (ii)** (no faithful rate from channel's own ecology) and should not be selected. In that case, the project must choose a non-Latin script or IME-mediated channel with documented input-ecology error rates (e.g., Japanese IME conversion, Chinese Pinyin conversion, Arabic diacritic dropout) where published rates exist.

---

## 10. References (Verifiable)

- Carlson, A. & Fette, I. (2007). *Memory-Based Context-Sensitive Spelling Correction at Web Scale*. ICMLA 2007. DOI: 10.1109/ICMLA.2007.34
- Jones, M.P. & Martin, J.H. (1997). *Contextual Spelling Correction Using Latent Semantic Analysis*. ANLP 1997. DOI: 10.3115/974557.974582
- Muylle, M., Pinet, S., Nozari, N. (2026). *On idle idols and ugly icons: Investigating lexical selection in typing through homophones*. Journal of Memory and Language, 146, 104703. DOI: 10.1016/j.jml.2025.104703
- Shah, K. & de Melo, G. (2020). *Correcting the Autocorrect: Context-Aware Typographical Error Correction via Training Data Augmentation*. LREC 2020. arXiv:2005.01158
- Hagiwara, M. & Mita, M. (2020). *GitHub Typo Corpus: A Large-Scale Multilingual Dataset of Misspellings and Grammatical Errors*. LREC 2020. arXiv:1911.12893
- Zhao, R., Liu, Y., Schütze, H., Hedderich, M.A. (2025). *Evaluating Robustness of Large Language Models Against Multilingual Typographical Errors*. ACL 2025. arXiv:2510.09536
- Aramaki, E. (2010). *Twitter Typo Corpus*. http://luululu.com/tweet/ (no DOI)
- Kukich, K. (1992). *Techniques for automatically correcting words in text*. ACM Comput. Surv. 24(4). DOI: 10.1145/146370.146380
- Mitton, R. (1996). *Spellchecking by computer*. In: *Spellchecking and the Computer*. (Cited in Hirst & Budanitsky 2005)
- Hirst, G. & Budanitsky, A. (2005). *Correcting real-word spelling errors: Restoring the semantic distance*. (arXiv:cs/0505053)
- **Japanese LLM robustness:** arXiv:2610.01241 (2024)
- **Healthcare LLM robustness:** PMC12923095 (2024)

---

*End of audit. This document is a decision input; it does not modify repository files.*