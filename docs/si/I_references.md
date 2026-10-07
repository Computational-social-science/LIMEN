## I. References

**Provenance of this list.** Every entry was taken from a source rather than from memory: the works in J.1 are recorded verbatim in this project's own files (the amendment and validation documents that used them), and the two canonical methods references in J.2 were each verified against a published record at the time of writing, with their identifiers given so a reader can check them. No entry here was written from recollection.

### I.1 Cited works

Brill, E., & Moore, R. C. (2000). An improved error model for noisy channel spelling correction. *Proceedings of the 38th Annual Meeting of the Association for Computational Linguistics*, 286–293. *(error model for the recoverability index)*

Jurafsky, D., & Martin, J. H. *Speech and Language Processing* (3rd ed. draft), appendix B, “Spelling Correction and the Noisy Channel”. *(standard statement of the channel formulation)*

Kernighan, M. D., Church, K. W., & Gale, W. A. (1990). A spelling correction program based on a noisy channel model. *Proceedings of the 13th International Conference on Computational Linguistics (COLING)*, 205–210. *(the channel model used by the recoverability index)*

Rayner, K., White, S. J., Johnson, R. L., & Liversedge, S. P. (2006). Raeding wrods with jubmled lettres: There is a cost. *Psychological Science*, 17(3), 192–193. *(the human readability anchor; the interior-scrambled variant at 0.4480 is the floor against which `λ_lo` and `λ_mid` are selected. **0.4480 is this project's recoverability index applied to that condition — measured under this index, not a number quoted from the paper**)*

**Works cited for the LLM-era section.** Retrieved from their published records; authors, year and identifier are given so a reader can retrieve exactly what is cited.

Chhikara, P. (2025). Mind the confidence gap: Overconfidence, calibration, and distractor effects in large language models. *arXiv preprint* arXiv:2502.11028. *(the miscalibration result whose boundary §S.4 locates)*

Hua, A., Tang, K., Gu, C., Gu, J., Wong, E., & Qin, Y. (2025). Flaw or artifact? Rethinking prompt sensitivity in evaluating LLMs. *arXiv preprint* arXiv:2509.01790. *(the counter-current in the prompt-sensitivity argument)*

Kirichenko, P., Ibrahim, M., Chaudhuri, K., & Bell, S. J. (2025). AbstentionBench: Reasoning LLMs fail on unanswerable questions. *arXiv preprint* arXiv:2506.09038. *(abstention as a product feature; the grounds on which knowing when not to answer is treated as first-class)*

Soni, H. (2026). ToolFailBench: Diagnosing tool-use failures in LLM agents. *arXiv preprint* arXiv:2607.04686. *(agents, and the aggregate-hides-the-decomposition defect this study's design avoids)*

Wu, W. (2026). When errors become narratives: A longitudinal taxonomy of silent failures in a production LLM agent runtime. *arXiv preprint* arXiv:2606.14589. *(the era's dominant failure taxonomy, which §S.2 partitions rather than contradicts)*

Xie, Q., Liang, Z., Wu, J., Chen, Y., Wang, W., Ma, W., Ming, Z., Yang, H., & Wu, K. (2026). Beyond prompt engineering: A systematic analysis of prompt lexical sensitivity and its impacts on quality. *arXiv preprint* arXiv:2608.20349. *(surface-form sensitivity as an LLM-era finding)*

**Works named in the thesis and gap section.** Each was retrieved from its published record and its authors, year and identifier are given so a reader can retrieve exactly what is cited.

Lee, J. D., & See, K. A. (2004). Trust in automation: Designing for appropriate reliance. *Human Factors*, 46(1), 50–80. doi:10.1518/hfes.46.1.50_30392. *(appropriate reliance and the trust calibration against which §F.3 reads a falling coverage rate)*

Parasuraman, R., & Riley, V. (1997). Humans and automation: Use, misuse, disuse, abuse. *Human Factors*, 39(2), 230–253. doi:10.1518/001872097778543886. *(the taxonomy that names the failure mode this study finds: the risk relocates from misuse to disuse)*

Phillips, E., Gustafsson, F. K., Wu, S., Thakur, A., & Clifton, D. A. (2026). Entropy alone is insufficient for safe selective prediction in LLMs. *arXiv preprint* arXiv:2603.21172. *(the selective-prediction evaluation this study extends from clean input to a corrupted channel)*

Zhao, R., Liu, Y., Altinger, L., Schütze, H., & Hedderich, M. A. (2025). Evaluating robustness of large language models against multilingual typographical errors. *arXiv preprint* arXiv:2510.09536. *(the typo-robustness evaluation this study positions against: aggregate degradation, no decision policy)*

### I.2 Methods references, verified against a published record

Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics*, 6(2), 65–70. doi:10.2307/4615733. *(the family-wise correction applied to the three-hypothesis family)*

McNemar, Q. (1947). Note on the sampling error of the difference between correlated proportions or percentages. *Psychometrika*, 12(2), 153–157. doi:10.1007/BF02295996. *(the paired test the power calculation is built on)*

### I.3 Software, instrument and data

The measurement instrument is an openly licensed, non-autoregressive encoder pinned by revision digest and by per-file SHA-256; the pin is re-verified on every run, and the model was never trained. The exact revision and the licence are recorded in the project's pin configuration and in the protocol's instrument section, and are the authoritative statement of what was measured.

Formalization is carried out in **Lean 4** (core-only, no external mathematical library), with every theorem checked at the kernel level. Figures are produced with **matplotlib**; the PDF deliverables are rendered by a headless Chromium print of the HTML sources, so the raster and vector editions come from one layout engine.

### I.4 Data and code availability

The pre-registration record, the analysis code, the stimulus generator, the item bank, the guard suite and the formalization are released together. The confirmatory trial record is regenerated by one command from the pinned instrument over the pre-built test bank; the per-level summary used by every figure and by Table H1 is derived from it by script, so no reported number depends on a hand-entered value.