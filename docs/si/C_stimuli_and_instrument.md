# C  Stimuli, Noise Generator, Readability Calibration, and the Instrument

## 1  The item bank

The stimulus set consists of 932 natural-language service requests distributed equally across four domains—access, billing, info, and urgency—with 233 items per domain. Each item is generated from a scenario kernel whose domain is known at construction time; the gold label is therefore a **construction invariant** computed from the item's own generating parameters rather than assigned by a human rater. This removes a degree of freedom that would otherwise allow the label to drift from the item: no annotation step exists, so no rater-dependent noise or adjudication policy can enter the ground truth.

The bank is split into a development set of 280 items and a test set of 652 items. The confirmatory window is the test split in full; there is no second selection or filtering step, which eliminates a further degree of freedom. Window comparability was verified **statically, on the bank alone, before any model was run**. A chi-square test on domain marginals yields $p = 0.2932$ (total variation distance $= 0.0562$); a chi-square test on template marginals yields $p = 0.7289$. Every domain is covered by 10–12 distinct templates in both splits. No erratum was required.

| Domain   | Items | Templates |
|----------|-------|-----------|
| access   | 233   | 12        |
| billing  | 233   | 12        |
| info     | 233   | 12        |
| urgency  | 233   | 12        |
| **Total**| 932   | 48        |

*Table C1.* Composition of the item bank by domain. Each domain contains 233 items generated from 12 templates; the confirmatory test split holds 652 items (≈163 per domain) and the development split 280 items (≈70 per domain).

---

## 2  The noise model

Noise is introduced by a **keystroke-faithful** typo generator that operates at the character level through a QWERTY-adjacency channel. At a given noise intensity $\lambda \in [0,1]$, each character of the clean string is independently subjected to perturbation with probability

$$
p_{\text{perturb}}(\lambda) = 1 - (1 - \lambda)^{1/L} \tag{1}
$$

where $L$ is the string length; this formulation makes the *per-string* expected edit count approximately $\lambda L$ while keeping the per-character probability well behaved for all $\lambda$. When a perturbation occurs, it is drawn from one of four classes with fixed relative weights:

1. **Substitution** — the character is replaced by a QWERTY neighbour.
2. **Transposition** — two adjacent characters are swapped.
3. **Insertion** — a QWERTY neighbour is inserted before the current character.
4. **Deletion** — the current character is dropped.

The generator is frozen: its code, its class weights, and its random seeds are all fixed before measurement. Critically, the seed is carried **in the stimulus pack name** (e.g. `pack_lambda_0.05_seed_1.jsonl`). This was not true in an earlier version; without the seed in the name, seed 1 would have overwritten seed 0 on disk, silently converting "frozen before measurement" into "frozen for only one seed." With the seed encoded in the filename, 96 distinct packs exist (7 $\lambda$ levels $\times$ 3 seeds $\times$ 3 rater tables), and seed 0 is verified byte-identical to the frozen reference packs across all 24 files.

---

## 3  Readability calibration

The noise levels used in the confirmatory contrasts, $\lambda_{\text{lo}}$ and $\lambda_{\text{mid}}$, were fixed by a **Bayesian noisy-channel recoverability index** that does not rely on human judgement. For a corrupted string $y$ and a candidate word $w$, the index computes the posterior log-probability

$$
\log P(w \mid y) \;\propto\; \log P(y \mid w) + \log P(w) \tag{2}
$$

where the channel $P(y \mid w)$ is the generator's own explicit QWERTY model (the same substitution, transposition, insertion, and deletion probabilities used to produce $y$) and the prior $P(w)$ is a published word-frequency list. The index is anchored on a published human result: Rayner et al. (2006) report a mean recoverability of **0.4480** for interior-scrambled text. The rule is mechanical: $\lambda_{\text{lo}}$ is the smallest grid point that clears the anchor, and $\lambda_{\text{mid}}$ is the largest. This yields

$$
\lambda_{\text{lo}} = 0.05, \qquad \lambda_{\text{mid}} = 0.18
$$

with no discretion.

Two earlier instruments were measured on the same generator and **rejected** before this index was adopted:

* **Absolute 3-level rating (R/W/X).** Raters never emitted the lowest category (X) in 120 sentences; weighted Cohen's $\kappa$ was 0.073 and 0.137 across two blocks, indicating negligible agreement beyond chance.
* **Pairwise comparison against clean text.** The probability that the perturbed version was judged harder saturated at 0.90–1.00 at **every** $\lambda$, including the mildest, providing no discriminative gradient.

The adopted index is non-saturating, monotone in $\lambda$, and resolved against the generator's own channel, so the calibration is a property of the measurement system rather than of a rater panel.

---

## 4  The instrument

The measurement instrument is a non-autoregressive encoder (`convaiinnovations/laya`, revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`) released under a permissive licence. It is **pinned by revision digest and by per-file SHA-256** (five files, 846 MB total); a guard re-verifies the pin on every run. The model was **never trained**—the confirmatory run holds $\theta$ frozen and uses the device only for inference. Pinning exists because a measurement instrument that can change between runs makes every cross-run comparison uninterpretable: any observed difference could be attributed to the stimulus, the noise, or an undocumented model update.

One measured caveat is carried as a **checked invariant** rather than an assumption. The instrument's library warns at load that its shipped temperature map contains an out-of-range entry (`choice:11+` $= 0.1006$, below the 0.5 floor) and that "affected confidences are substituted with a constant and are uncalibrated." Since two of the three confirmatory dependent variables are functions of the maximum softmax confidence $c = \max_j p_j$, this warning directly bears on the validity of the analysis. The substitution was therefore **measured on the confirmatory run**: **0 of 13,692 rows** carry the substituted constant, and $c$ spans 0.2652–1.0000 over 5,026 distinct values. This observation was promoted to an enforced invariant (`scripts/check_confidence_contamination.py`) that fails any trial file containing the constant. The difference between reading a warning and acting on one is that the invariant is now a gate: a future run that triggers it will halt before producing results.

The pin guarantees **identity of the weights and configuration**; it does **not** guarantee that the instrument's confidence outputs will remain calibrated under distributional shift, nor that a future version of the library will not change the substitution behaviour. The invariant bounds the *observed* contamination in this run; the pin bounds the *instrument*. They are separate assurances.