# Six-Question Critical Review: Kuhn et al. (2024), "Detecting hallucinations in large language models using semantic entropy", *Nature* 630, 625–630.

---

## 1. THE CLAIM

> "We focus on a subset of hallucinations which we call 'confabulations' for which LLMs fluently make claims that are both wrong and arbitrary—by which we mean that the answer is sensitive to irrelevant details such as random seed." (lines 161–163)

> "It does not guarantee factuality because it does not help when LLM outputs are systematically bad." (lines 164–165)

**Claim:** Semantic entropy detects *confabulations* (arbitrary, seed-sensitive errors) by measuring uncertainty over *meanings* via bidirectional-entailment clustering, improving QA accuracy by refusing high-entropy answers.

---

## 2. THE MECHANISM

**Computed:** Sample *M*=10 generations (line 397); cluster by bidirectional entailment (GPT-3.5/DeBERTa, lines 455–467, 539–540); sum length-normalized token probabilities per cluster (Eq. 5, lines 413–425); SE = −∑ *P*(*C*_i|**x**) log *P*(*C*_i|**x**).

**Rationale:** "The model will be uncertain about generations for which its output is going to be arbitrary" (lines 373–374). This is an **empirical regularity** (AUROC/AURAC), not a theorem. The paper disclaims: "Our method explicitly does not directly address situations in which LLMs are confidently wrong because they have been trained with objectives that systematically produce dangerous behaviour… these represent different underlying mechanisms" (lines 265–267).

**Measures vs. assumes:**
- **Measures:** Dispersion of the model's *own* sampled meanings under seed variation.
- **Assumes:** (a) Bidirectional entailment ≈ semantic equivalence (lines 405–407); (b) Judge LLM entailment ≈ human meaning-equivalence (human–GPT-4 ≈ human–human, lines 197–198); (c) Seed variation reflects internal uncertainty (line 397); (d) Target = *arbitrary* errors, not *systematic* (lines 162, 265–267).

---

## 3. THE OPERATIONALISATION

| Element | Operationalisation | Whose Judgment |
|---------|-------------------|----------------|
| **Inputs** | TriviaQA, SQuAD, BioASQ, NQ-Open, SVAMP; FactualBio (lines 437–439, 501–502) | Dataset authors |
| **Generations** | *M*=10, temp=1, nucleus *p*=0.9, top-*K*=50 (line 397) | Model's sampling |
| **Clusters** | Bidirectional entailment via GPT-3.5 (sentence) or DeBERTa "non-defeating" (paragraph) (lines 455–467, 539–540) | Judge LLM |
| **Correctness** | GPT-4: "does the proposed answer mean the same as the expected answer?" (lines 488–493) | GPT-4 (vs. 2 humans: 92–93% agreement, line 2378) |
| **Metrics** | AUROC, AURAC, rejection accuracy (lines 479–484) | Derived from GPT-4 labels |

**Clustering quality:** Supplementary Note 2 reports entailment-classification agreement (human–human 87%, human–GPT-4 87%, human–GPT-3.5 83%, lines 1967–1991), but **no direct clustering-quality metric** (e.g., ARI vs. human clusters). The paper admits: "semantic equivalence is fuzzy… assumptions behind our equivalence classes do not hold in practice" (lines 712–713, 2065–2068).

---

## 4. THE SCOPE

**Models:** LLaMA 2 Chat (7B/13B/70B), Falcon Instruct (7B/40B), Mistral Instruct (7B); GPT-4 for paragraph (lines 189, 443).  
**Tasks:** Free-form QA (trivia, RC, biomedical, natural Q, math) + biography generation (lines 187–188).  
**Language:** English only.  
**Regime:** Context-free (line 441); temp=1; *M*=10.

**Explicit assumptions:** (1) Uncertainty ⇔ arbitrariness (lines 373–374); (2) Bidirectional entailment ≈ equivalence (line 405); (3) Judge LLM reliable (lines 197–198); (4) Temp=1 sampling faithful (line 397); (5) Target = *arbitrary* errors (lines 162, 265–267); (6) Reference answers ≈ truth (line 491); (7) Length normalization appropriate (lines 385–386: "little theoretical justification"); (8) Discrete SE approximates probabilistic SE (line 429).

---

## 5. THE OVERREACH

**Does it distinguish "confidently fabricated" from "confidently resolved ambiguity differently from annotator"?** **No.** It explicitly excludes systematic errors:

> "We distinguish this from cases… when LLMs are consistently wrong as a result of being trained on erroneous data… or systematic failures of reasoning" (lines 161–164)

> "Our method explicitly does not directly address situations in which LLMs are confidently wrong because they have been trained with objectives that systematically produce dangerous behaviour… these represent different underlying mechanisms" (lines 265–267)

The only ambiguity discussion (Table 1 row 4, lines 230–231, 240–242) shows SE *erroneously high* when clustering is *too sensitive* (distinguishing "1 October 1998" from "1998"). The **opposite failure**—clustering *insensitive* to a distinction the annotator cares about (e.g., abbreviation sense)—is **never tested**. This is an untested scope boundary.

---

## 6. OUR ENTRY

**Abbreviation case:** Model consistently expands `LLM` → "Large Language Model" (dominant sense); annotator intended "Local Linear Model" (attested but rarer). Model is highly self-consistent → low SE.

**Framework prediction:** **NOT a confabulation.** Low SE ⇔ "the LLM is confident about the meaning" (line 176) ⇔ "not a confabulation" (Table 1, rows 1, 3). Generations cluster together → SE ≈ 0 → detector outputs "not confabulation."

**Confirming measurement:** Run SE pipeline on abbreviation-expansion prompts where (a) model is highly self-consistent (low SE) and (b) expansion disagrees with annotator's intended sense but is corpus-attested. If detector says "not confabulation" while annotator says "incorrect," scope claim confirmed.

**Falsifying result:** If SE is *high* on such cases (clusterer splits consistent generations), *or* if paper had tested this class and found low-SE incorrect answers as false negatives (it did not). The paper's theory **implies our claim**; our contribution is to **test a published framework's scope boundary**, not contradict it.

---

## Verdict

**verdict: WELL-SCOPED — and its own theory already implies our claim.**

The paper explicitly targets *confabulations* (arbitrary, seed-sensitive errors) and disclaims *systematic* errors (lines 161–164, 265–267). Our abbreviation case—consistent expansion to an attested but unintended sense—is a *systematic* error by the paper's taxonomy, hence **outside its claimed scope**. The framework *predicts* low SE → "not a confabulation." The gap is not in the paper's logic but in the **untested boundary**: no experiment probes whether low-SE systematic disagreements with annotators are falsely cleared. Our programme tests this boundary.