# Scientific-gap verdict — Phase I, checked against the live literature

**Verdict: the programme is NOT YET on a clean gap.** Two of the mechanisms this protocol relies on
are pre-empted in the published record, and the orthographic-channel space is occupied. This document
names each pre-emption with its quote, states what survives, and prescribes the re-scoping the Stage 1
needs before it claims anything.

**Method.** Mechanism-level pre-emption search (the rule in the `claim-novelty-audit` skill: search the
*structural position*, not the topic), run 2026-10-04 via the `arxiv` MCP (**queries match
title/abstract/metadata, not full text — a stated coverage limit**). Retrieval worked; the
`semantic-scholar` MCP was **rate-limited** (E3001, retry_after 60 s) and contributed nothing, so this
audit is **arXiv-only** and does not cover OpenReview, proceedings, or blogs.

---

## 1. Mechanism slot: "confidently wrong bypasses abstention" — **PRE-EMPTED**

Our `SilentError@τ` is the share of items that are wrong **and** confident. That is not a new
construct, and its motivation is already published almost verbatim.

| Source | Quote | Slot it occupies |
|---|---|---|
| **arXiv:2608.09768** — *ReliableNet: A Chance-Constrained Approach to Trustworthy Classification in Deep Learning* (2026-08-10) | *"A prediction that is both confident and wrong is a critical reliability failure because it can bypass abstention and human review precisely when the model is mistaken."* | The exact motivation of `SilentError@τ` |
| **arXiv:2603.21172** — *Entropy Alone is Insufficient for Safe Selective Prediction in LLMs* (2026-03-22) | studies uncertainty signals *"in the context of the wider selective prediction"* setup | Confidence-as-gate, evaluated |
| **arXiv:2509.01455** — *Trusted Uncertainty in LLMs: A Unified Framework for Confidence Calibration and Risk-Controlled Refusal* (2025-09-01) | *"Deployed language models must decide not only what to answer but also when not to answer."* | The answer/defer control law itself |
| **arXiv:2508.07556** — *Uncertainty-Driven Reliability: Selective Prediction and Trustworthy Deployment in Modern ML* (2025-08-11) | a thesis on *"selective prediction — where models abstain when confident"* | The whole frame, as established literature |
| **arXiv:2502.19110** — *Conformal Linguistic Calibration* (2025-02-26) | abstention and linguistic calibration traded off | Calibrated abstention |

**Consequence.** The protocol's §3.3 confidence rule, §3.4 gate and the `SilentError`/`Coverage` pair are
**instrumentation drawn from an established literature, not contributions**. The Stage 1 must present
them as inherited, cited, and re-measured — never as the novelty.

## 2. Mechanism slot: "gating magnifies disparity across groups" — **PRE-EMPTED, and by a canonical paper**

Our Phase II hypothesis H2.3 is a **coverage disparity across channels**, and H2.1 a script × noise
interaction.

| Source | Quote | Slot it occupies |
|---|---|---|
| **arXiv:2010.14134** — *Selective Classification Can Magnify Disparities Across Groups* (Jones, Sagawa, Koh, Kumar, Liang; 2020) | *"selective classification can improve average accuracies … [but] we find that it can **magnify disparities across groups**"* | The mechanism behind any coverage-disparity claim we were going to make |
| **arXiv:2607.24875** — *FinAbstain* (2026-07-27) | LLMs *"may express high confidence when evidence is sparse, stale, or contradictory"* | Confidence/evidence mismatch as a measured failure |

**Consequence.** "Gating helps the average and hurts a subgroup" is **2020 work, and well cited**. Our
Phase II cannot claim to discover that abstention creates disparity. What it can still ask is narrower,
and the narrowing is where the surviving claim lives (§4).

## 3. Mechanism slot: "writing system as a systematic structural cost" — **OCCUPIED**

This is the one that most directly threatens the programme's framing, because our thesis calls the
orthographic channel a *structural* variable.

| Source | Quote | Slot |
|---|---|---|
| **arXiv:2602.11174** — *The Script Tax: Measuring Tokenization-Driven Efficiency and Latency Disparities in Multilingual Language Models* (2026-01-19) | *"their tokenizers can impose **systematic costs on certain writing systems**. We quantify this **script tax** by comparing two orthographic variants with identical linguistic content."* | Script as a systematic cost, with a controlled orthographic-variant design — **the closest published analogue to our Phase II** |
| **arXiv:2606.20770** — *Beyond 'One Language, One Script': Quantifying Orthographic Bias in Multilingual VLMs with PuMVR* (2026-06-18) | *"we operate under a flawed assumption: that one language corresponds to a single writing system"* | "Orthographic bias", quantified |
| **arXiv:2605.31363** — *The Latin Substrate: How Language Models Represent and Mediate Script Choice* (2026-05-29) | how models *"internally mediate"* script choice | Mechanism of script handling |
| **arXiv:2508.21206** — *Enhancing Robustness of AR LMs against Orthographic Attacks via Pixel-based Approach* (2025-08-28) | *"input text is perturbed with characters from multilingual alphabets, leading to substantial performance degradation"* | Orthographic perturbation of LM input — **the noise side of our design** |
| **arXiv:2409.15452** — *CUTE: Measuring LLMs' Understanding of Their Tokens* (2024-09-23) | models *"process [tokens] as atomic units without direct access to individual characters"*, raising *"to what extent can LLMs learn orthograph[y]"* | The representational reason the channel could matter |
| **arXiv:2502.19669** — *Investigating Neurons and Heads in transformer-based LLMs for Typographical Errors* (2025-02-27) | *"how LLMs encode inputs with typos"* | The English-typo mechanism of our Phase I |
| **arXiv:2609.35475** — *Spontaneous Context Restoration: How Language Models Recover from Corrupted Inputs* (2026-09-28) | models *"sometimes produce correct outputs even when their inputs are corrupted by deletion, replacement, or misspelling"* | The recovery phenomenon that would make H1.2 fail — published one week ago |

**Consequence.** "English typo noise degrades LLM accuracy" (our H1.1) is **not a contribution**. Nor is
"scripts carry systematic costs". Both are published, in the same 2025–2026 window.

## 4. What survives — and it is an interaction, not a main effect

> **Surviving claim.** Prior work measures a channel's *static* cost (script tax, orthographic bias) and
> separately shows that *gating* magnifies *static* group disparities. **Nobody has asked whether the
> perturbation regime changes the channel ORDERING of a gated decision system — whether added noise
> re-ranks the channels' coverage, rather than merely lowering everyone's.**

**Sharpened by the classical frame (`docs/THEORETICAL_FOUNDATIONS.md`, §C-3).** Each (channel, λ) pair
defines a **rate–error curve** — coverage against residual error, which is exactly what the protocol's
`Coverage@ε` / `SilentError@τ` pair samples. The claim above then has a geometric name:

- **parallel shift** — noise lowers every channel's curve by a similar amount and the ordering is
  preserved; channel differences are static, and noise is a scalar tax on top of them;
- **crossing** — noise changes which channel sits higher; channel differences are **regime-dependent**,
  and any static channel ranking is invalid outside the regime it was measured in.

**The programme claims crossing, and crossing is falsifiable on the fitted curves.** This is stronger
than the earlier phrasing because it is a criterion, not a direction: two curves can be compared without
needing a significant interaction to be located first.

That is a **two-factor interaction** (channel × noise) on a **control-law** estimand, in a
**generation-free typed-decision** subject, on a **pre-registered** locked split. Interactions are
where pre-emption is least likely and where the statistical design earns its keep: a main-effect design
cannot see it, which is exactly why it is still open.

**Three supporting differences, each weaker than the interaction and to be presented as such:**
1. **Subject class.** The script-tax and orthographic-bias work studies encoders and VLMs; ours studies
   a **typed-decision control system** whose output is consumed by application code.
2. **Estimand.** They measure accuracy, latency and bias; ours measures the **control law** — the
   coverage/error trade under a pre-registered gate.
3. **Noise as an instrument, not a nuisance.** `2508.21206` treats orthographic perturbation as an
   attack to be defended against; here it is the **independent variable**, with a channel-specific
   generator that the protocol explicitly forbids equating across scripts.

## 5. Consequences for the programme — the honest list

> **⚠️ POSTURE CORRECTED 2026-10-04.** The list below was written under the assumption that a
> pre-emption bars novelty. The programme owner corrected that: **published ≠ correct**, and
> challenging a published conclusion is itself the gap sought. Pre-emption is therefore **not a bar to
> novelty but the obligation to engage** — and the engagement is where the contribution lives. The
> pre-emptions in §1–§3 stand as **fact**; what changes is that they are **claimants to be tested**,
> not authorities to defer to. Full corrected posture and the six-question review instrument:
> `docs/CRITICAL_REVIEW_PROTOCOL.md`. The most concrete instance: treating an abbreviation's polysemy
> as hallucination merges **fabrication** with **a legitimate reading that disagrees with the
> annotator's intent** — two constructs with different signatures, measurably separable, and merged in
> the published operationalisation.

1. **Phase I, as written, is not a gap.** Its own text already concedes this (*"necessary infrastructure
   science … not a diluted substitute for Phase II"*). The Stage 1 must **state that plainly**, cite the
   pre-emptions above, and present Phase I as **instrument validation for the interaction test** —
   not as a standalone contribution.
2. **The Stage 1 title and abstract must lead with the interaction**, not with "noise degrades
   performance".
3. **H1.1 must be demoted explicitly** in the manuscript text as previously argued on other grounds: it
   is pre-empted *and* it is not the control-law claim.
4. **A pre-emption paragraph is now mandatory** in §1 of `docs/REGISTERED_REPORT_STAGE1.md`, naming
   `2010.14134` and `2602.11174` by id with their quotes. A reviewer who knows the field will raise both;
   raising them first is a credibility asset (the audit skill's own rule).
5. **The `2609.35475` finding (spontaneous context restoration) must be handled**: if corrupted inputs
   are sometimes repaired, H1.2 can fail for an interesting reason, and the protocol's *"H1.1 supported,
   H1.2 not"* branch anticipated exactly that. That branch now has a mechanistic citation.
6. **Coverage is arXiv-only.** Before submission, the same mechanism queries must run against
   OpenReview and the venue proceedings — the stated blind spot — and the `semantic-scholar` MCP
   (rate-limited today) should be retried for citation-graph coverage.

## 6. Toolbox status, for the record

| Toolbox | Status at 2026-10-04 |
|---|---|
| **`arxiv` MCP** | **WORKING** — 7 queries, all returned real records with ids, dates and abstracts |
| **`semantic-scholar` MCP** | **RATE-LIMITED** — E3001, `retry_after` 60 s, 4/4 attempts failed. Verified present, not usable this session |
| **`paper2agent` toolbox** | **DEPLOYED** at `D:/2026-AI4S/nhb-llm-mistranslation/paper2agent_repo` (14 MB, 111 files, repo + scripts + skills) with prior output in `paper2agent_work` (383 MB, 1,845 files: documents, notes, renders, a paper draft and reviews). Not exercised in this session |
| Hermes MCP `lwow` | configured, not exercised |
| BootLoops / Lean 4 / understand-anything | present on disk, not exercised |

**No claim in this document rests on a toolbox's say-so.** Every pre-emption above carries an arXiv id
retrieved by a call made here, on 2026-10-04.
