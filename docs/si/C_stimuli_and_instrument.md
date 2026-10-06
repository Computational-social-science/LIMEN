## C. Stimuli, noise model and instrument

### C.1 The item bank

The stimuli are typed decision tasks in a service-request register, drawn from a bank of **932 items** spanning four domains — access, billing, information and urgency — with **233 items in each domain**. The bank is split into a development set of **280 items** and a test set of **652 items**; the confirmatory window is the test set *in full*, with no second selection step, which removes a degree of freedom a post hoc window would otherwise introduce.

| Domain | Dev | Test | Total |
|---|---|---|---|
| access | 65 | 168 | 233 |
| billing | 64 | 169 | 233 |
| information | 81 | 152 | 233 |
| urgency | 70 | 163 | 233 |
| **Total** | **280** | **652** | **932** |

An item carries a state description, a set of caller-defined options, and a gold label. **The gold label is constructive rather than annotated**: it is computed from the item's own construction, so the label cannot drift from the item and no rater's judgement enters the target. That matters more than it sounds. An annotated gold label is a measurement of a second process, and under noise the interesting question is precisely whether the *model* is robust — not whether annotators agree about what a corrupted item means. Deriving the label removes the annotator from the causal path entirely.

Because the two splits must be comparable for a dev-calibrated threshold to transfer, comparability was checked **statically, on the bank alone, before any model was run**. Domain marginals do not differ (χ² p = 0.2932, total variation 0.0562), template marginals do not differ (χ² p = 0.7289), and every domain is covered by 10–12 templates in both splits (45 templates in dev, 47 in test). No erratum was required. The check reports rather than corrects: had the marginals differed, the response is an erratum written *before* the run, because re-weighting after seeing outcomes is a design change made on the data.

### C.2 The noise model

Noise is applied at the level of characters, and it is **keystroke-faithful** rather than uniformly random. For a text of length $L$ and a noise level $\lambda$, each character is perturbed independently with probability

$$p_{\mathrm{pert}}(\lambda) \;=\; \min\bigl(1,\; \lambda\bigr),$$

and a perturbed character is realised as one of **four classes** with weights fixed by a QWERTY-adjacency channel: **substitution** (a neighbouring key), **transposition** (the adjacent character), **insertion** (a neighbouring key), and **deletion**. The class weights are part of the frozen generator, so the noise is reproducible and is *not* tuned per item.

Two aspects of the generator were fixed only after a failure. First, the generator's seed is carried **in the stimulus pack name**. Originally it was not, which meant that regenerating at seed 1 silently overwrote seed 0 — converting "frozen before measurement" into "frozen for exactly one seed" without any error surfacing. With the seed in the name, 96 packs exist (grid × seeds × rater tables) and seed 0 reproduces the original packs **byte-for-byte, 24 of 24 files**. Second, the clean condition is verified to be *identical across seeds*: at $\lambda = 0$ the generator has nothing to perturb, so a clean cell that moved with the seed would mean the generator was disturbing something at zero noise and every comparison would have been against a moving baseline.

### C.3 Readability calibration

The two operating levels were fixed by a **non-saturating recoverability index** rather than by human judgement. For a corrupted surface form, the index is the posterior mass the noisy channel places on the intended word:

$$\mathcal{R}(s) \;=\; \frac{\exp\bigl(\log P(s \mid w^{\star}) + \log P(w^{\star})\bigr)}{\sum_{w} \exp\bigl(\log P(s \mid w) + \log P(w)\bigr)},$$

with the channel the generator's own QWERTY model and the prior a published word-frequency list. Values are reported as the mean over items.

The index is anchored on a **published human result** rather than on a threshold chosen for convenience: Rayner and colleagues' interior-scrambled condition (2006), whose readers recovered the intended word 0.4480 of the time — the harsher of the two variants they report, and therefore a floor for human tolerance. The levels are then determined by rule: **$\lambda_{\mathrm{lo}} = 0.05$** is the smallest grid point whose mean recoverability clears the anchor, and **$\lambda_{\mathrm{mid}} = 0.18$** is the largest point that still clears it. The margin at $\lambda_{\mathrm{lo}}$ is $+0.0728$.

Two earlier instruments were measured and **rejected**, and the reason is quantitative. An **absolute three-level rating** (recoverable / workable / not recoverable) never emitted its lowest category in 120 sentences and reached weighted κ of only 0.073 and 0.137 against a 0.60 floor: it could not express what it was for. **Pairwise comparison against clean text** saturated the other way — the probability that a perturbed sentence was judged harder was 0.90–1.00 at *every* level including the mildest, so it detected the presence of corruption but not its degree. Neither failure is a rater failure; both are instrument failures, and the anchored index is used precisely because it is monotone over the range that matters.

### C.4 The instrument

The instrument is a non-autoregressive encoder under a permissive licence, **pinned by revision digest and by per-file SHA-256**, with an integrity guard that re-verifies the pin on every run. It was never trained: the study measures a fixed device, and holding parameters frozen is what makes a contrast between noise levels a statement about the manipulation rather than about the model's drift. What the pin does **not** guarantee is that the instrument's confidence is calibrated — the library warns, unprompted, that the checkpoint ships temperatures outside its valid range and that affected confidences are substituted with a constant and are uncalibrated. Two of the three dependent variables are functions of confidence, so the warning was bounded by measurement rather than trusted: on the confirmatory run **0 of 13,692 rows carry the substituted constant**, and the confidence values span 0.2652–1.0000 over 5,026 distinct values. Because a single sample cannot make a guarantee, the observation is now carried as a **checked invariant** that fails on any trial file containing the constant. Reading a warning is not the same as acting on one.
