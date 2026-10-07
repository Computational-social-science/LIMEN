# Supplementary information

**LIMEN Phase I — orthographic channels and input noise as structural disturbances in human–model interaction in the age of large language models**

*Supplementary information provided by the authors; not edited.*

**The result in one sentence.** Typing errors cost a language model accuracy and coverage, yet the confidence gate that decides whether to answer becomes *sharper* under them — the errors arrive below the gate rather than above it — so in the age of language models the damage from the input channel lands on what the system declines to answer, not on what it commits to.

---

## Contents

**A.** Background and design
**B.** Formal framework
**C.** Stimuli, noise model and instrument
**D.** Analysis, power and results
**E.** Interpretation, limitations and reproduction
**F.** Significance in the age of large language models
**G.** Significance across disciplines
**H.** Pre-registration: the frozen checklist
**I.** References

---

## Thesis, gap and contribution

*This section states what the study claims, against whom, and what the formalization contributes as science. It precedes the appendices because everything in them is an elaboration of it.*

### T.1 The title, earned rather than asserted

*"Orthographic channels and input noise as structural disturbances in human–model interaction."*

For this to be true rather than decorative, three things must hold, and each can be written down and checked.

**(i) The disturbance must be structural — a property of the interface, not of either party.** It is. Typing errors are produced by the human's keyboard, not by the model, and they are not authored deliberately: they are what the channel does. The model receives them as data and cannot distinguish them from intent. So a typed request is a **noisy channel** in the technical sense — an intended symbol destroyed by the medium between the parties — and the noise is a property of the *pairing*, which is why it is a structural disturbance and not a model defect or a user defect.

**(ii) The human must be in the loop in a way that can be located.** The human appears at exactly two points, and both are the parts of the design an earlier draft left implicit:

- **At the input**, as the origin of the disturbance. This is what the channel models, and it is why the noise
generator is *keystroke-faithful* rather than uniformly random: a channel model that does not respect the medium's actual error structure is not a model of that channel.
- **At the output**, as the **consumer of the deferral**. A deferral is not a null result — it is work returned
to the human, and its cost is human time. This is the sense in which coverage is a *human-facing* dependent variable, and it is the reason the study's central finding (damage lands in coverage, not in committed correctness) is a statement about the interaction rather than about a classifier.

**(iii) The interaction must be the unit of analysis, not an afterthought.** The gate is the interface: it is where the model's self-assessment is converted into an action that the human experiences. Studying the gate *is* studying the interaction — but only if the deferral is priced as the human cost it is, and only if the noise is the human's noise. Both are now explicit.

**What this does not license.** It does not license the word "interaction" as a substitute for human data. This study measures **the model-side half** of the interface under a **human-derived** disturbance. A claim about how humans *respond* to a rising deferral rate is a different study, and the obvious next one.

---

### T.2 The gap, with the literature named

Two mature literatures do not meet.

**The first measures the damage and stops at the aggregate.** Typo-robustness work is well developed: MulTypo (arXiv:2510.09536) evaluates 18 open-source models across five tasks and finds that typos consistently degrade performance, more so in generative and reasoning tasks, with instruction tuning improving clean-input scores while potentially increasing brittleness. Its own framing of the gap is that "most benchmarks assume clean input". What it reports is **aggregate degradation on a held-out set** — which is what it sets out to report.

**The second models the policy and assumes clean input.** Selective prediction is equally well developed: "Entropy Alone is Insufficient for Safe Selective Prediction in LLMs" (arXiv:2603.21172) argues that uncertainty methods must be evaluated inside the wider abstention policy and against the risk–coverage trade-off, because a method that looks good in isolation can produce unreliable abstention at low target error rates. It evaluates on TriviaQA, BioASQ and MedicalQA — **all clean**. Lee & See's account of trust in automation, and Parasuraman & Riley's **misuse / disuse / abuse** taxonomy that it builds on, are the human-factors frame for what a changing deferral rate does to an operator — and neither is brought to bear on corrupted input.

**The intersection is empty.** No study measures how the *input channel* moves a *selective-prediction policy's* risk–coverage frontier, and no study prices the result as a human-facing cost.

That intersection is not a corner of the field. It is where deployment actually lives: a human types, a model answers or defers, and a human receives whichever happened. The literatures are complete on either side of the interface and silent at it.

**The question this study answers, then, is not "does noise hurt" — that is settled — but:**

> *When a confidence gate sits between a noisy human input and a human consumer, does input corruption move the
> gate's decision boundary, and in which direction does the damage land?*

with the answer, on this instrument: **the gate gets sharper, and the damage lands on what the system declines to answer rather than on what it commits to.**

---

### T.3 The formalization, read as findings rather than as corrections

The Lean development was treated as infrastructure until the review asked what it had discovered. Four of its results are not corrections. They are statements about how the field measures this, and each was kernel-checked.

**F-L1. The standard silent-error question is ill-posed as usually stated.** (`risk_mono`; the refuted protocol wording preserved as `protocol_said_nondecreasing_is_FALSE`.) The silent-error count at a fixed threshold is **non-increasing** in that threshold. It follows that **no confidence-deflating manipulation can make a fixed-threshold silent-error rate rise** — the trials leave the accepted set before they can be counted, so the feared quantity is monotone in the safe direction *by construction*. The literature's premise — that noise pushes errors *past* a gate calibrated on clean text — is therefore not a hypothesis that a rate can test. It has to be posed as a **conditional** quantity or as a **discrimination** question, and the study's replacement hypothesis is exactly the second. **This is a finding about the field's practice: a widely stated worry is measurably unfalsifiable in the form it is usually stated.**

**F-L2. A gate's discriminability is a property of the model's ordering, not of its calibration.** (`winsAux_map_of_strictMono`, with `#print axioms` reporting dependence on no axioms.) The ordered-pair count is invariant under **any** strictly increasing map of the confidence scale. The selective-prediction literature worries about calibration — whether the numbers are probabilities. This theorem says the **ordering** question and the **calibration** question are genuinely separate, and that a policy can be evaluated on the first while the second is in doubt. It is also what allowed the study to proceed on an instrument whose own vendor warns its confidences are uncalibrated: measured, rescaling the whole arm moves a threshold quantity by **43.6 points** and the discrimination statistic by **exactly 0.000**.

**F-L3. Two quantities the family treated as distinct measurements are one measurement.** (`cond_error_complements_cond_accuracy`.) Conditional error among admitted trials and conditional accuracy among admitted trials sum to one. Any study that reports both as separate evidence has counted one thing twice — a multiplicity error that no correction procedure can repair, because it corrupts the family rather than the p-value. Naming which quantities are functions of which is prior to controlling the family-wise error rate.

**F-L4. A risk budget can silently define the estimator out of existence.** (`budget_collapses_to_zero_on_small_dev`, `empty_dev_is_degenerate`, `clean_pins_at_floor`.) Under a budget $\varepsilon$, at any $N$ with $\lfloor \varepsilon N \rfloor = 0$ there is no error the budget tolerates, so the minimum admissible threshold is the all-reject point and the fitted quantity is a **design constant, not an estimate**. At the conventional $\varepsilon = 0.05$ this bites below $N = 20$. A threshold fitted on a small development split can therefore report a number the data never determined, without any warning appearing in the output.

**What the four have in common.** Each says that a quantity the field reports is not measuring what its name suggests — the silent-error rate (it is a criterion-dependent count), the calibration (the ordering is what a policy reads), the family (two of its members are complements), the fitted threshold (it can be a constant). That is a coherent contribution and it is *methodological*, which is why it was invisible while it was filed as "the formalization corrected the protocol".

---

### T.4 What would falsify this

The gap is empirical, not rhetorical, so it has to be able to fail.

- **If a confidence gate's discriminability fell under noise on other instruments**, the criterion-shift reading
would not generalise and this would be one instrument's behaviour. The direction is the finding, so it must be re-established per instrument.
- **If meaning-corrupting noise deflated nothing** — a plausible substitution, a homophone — then the mechanism
proposed here predicts an **opposite** outcome: errors would not announce themselves and the rise would disappear. That is a testable prediction, and it is the next experiment rather than a caveat.
- **If human operators responded to a falling coverage rate by overriding the gate**, the interaction claim
would break in the direction F.3 predicts is the benign one — and would have to be measured with humans, which this study does not do.

---

## A. Background and design

### A.1 Background

Typed decision-making is now routine where a language model is asked a question whose answer must be trusted without inspection: a classifier routes a request, a gate admits or defers, a system acts. The surface form of such a request is produced by a human on a keyboard, and keyboards produce errors. The question this study asks is not whether typographic noise degrades performance — that is settled — but **how the degradation distributes itself across a confidence gate**, because that distribution is what determines whether an operator can see the damage.

A widely repeated premise holds that the dangerous failure is the *silent* one: that noise pushes wrong answers *past* a confidence threshold, so they arrive wearing the same confidence as correct ones and are never caught. If that premise is true, then a gate calibrated on clean text is a liability under noise, and the risk calculus for every deployed gate changes. If it is false — if the errors noise causes arrive *below* the gate — then the gate continues to filter them, and the damage lands somewhere quite different: in the answers the system declines to give.

The distinction matters because the two failures call for opposite remedies. Silent errors demand *recalibration*: a stricter threshold, a different confidence estimator, or abstention that does not rely on confidence at all. Loud errors demand *coverage*: the model is not wrong more often in the answers it commits to, it simply commits less often, and the remedy is throughput — more attempts, a retrieval step, a reprompt — not a different threshold. Treating one as the other wastes the remedy and leaves the real failure in place.

### A.2 The question, stated so that it can fail

*‹Does keystroke-faithful typographic noise, applied to a typed-decision task, change **the error rate among the trials a confidence gate admits**?›*

The question is deliberately about a conditional quantity rather than an overall one. An overall error rate must rise when noise is applied, because some correct answers become wrong; that is arithmetic, not a finding. Whether the *admitted* error rate rises is an empirical question about the joint behaviour of confidence and correctness, and it can go either way. It is falsifiable, it is measurable on a frozen instrument, and its answer decides which remedy applies.

### A.3 Pre-registered hypotheses

Let $\lambda \in \{0, 0.03, 0.05, 0.08, 0.12, 0.18, 0.25\}$ index the noise level, with $\lambda_{\mathrm{lo}} = 0.05$ and $\lambda_{\mathrm{mid}} = 0.18$ fixed by calibration (§C.3). Each trial carries a confidence $c$ and a correctness indicator; the gate admits a trial when $c \ge \tau$. The three pre-registered hypotheses are:

$$\text{H1.1:}\quad \mathrm{Acc}(\lambda_{\mathrm{mid}}) < \mathrm{Acc}(0) \qquad\text{(accuracy falls)}$$

$$\text{H1.2}^{\prime}\text{:}\quad \mathrm{AUC}(\lambda_{\mathrm{mid}}) > \mathrm{AUC}(0) \qquad\text{(the gate's discriminability rises)}$$

$$\text{H1.3:}\quad \mathrm{Cov}_{\varepsilon}(\lambda_{\mathrm{mid}}) < \mathrm{Cov}_{\varepsilon}(0) \qquad\text{(coverage falls)}$$

where $\mathrm{AUC}(\lambda)$ is the within-arm probability that a randomly chosen correct trial carries higher confidence than a randomly chosen incorrect one, and $\mathrm{Cov}_\varepsilon$ is the fraction of trials the gate admits at the calibrated threshold. H1.3 is the hypothesis that speaks to the premise's consequence, and H1.2′ is the hypothesis that speaks to its mechanism.

**One hypothesis was replaced before the confirmatory run, and the record should say so on its first page.** The original H1.2 asserted that the fixed-threshold silent error *rises* with noise. A pre-registered pre-run on the development split refuted it in four independent formulations, and the mechanism is one the protocol had already proved: noise deflates confidence, so fewer trials clear the gate at all, and the admitted-and-wrong share falls with them. A fixed-threshold silent-error rate *cannot* rise under a confidence-deflating manipulation. H1.2′ replaces it, and the replacement was made **before any confirmatory data existed**. §E.4 reports what the pre-run predicted and whether each prediction held.

### A.4 Design

The design is within-item: every item appears at every noise level under every frozen seed, so every contrast is paired on the item, and item difficulty — which is large and unmodelled — cancels exactly rather than being estimated. The confirmatory window is the 652-item test split of a 932-item bank, used in full; there is no second selection step, which removes a degree of freedom that a post hoc window would introduce. The instrument was pinned by revision digest and per-file SHA-256 and never trained: the study measures a fixed device rather than tracking a moving one. Analysis was fixed in advance as an exact paired permutation test with Holm correction across the three-hypothesis family and with each hypothesis's *direction* enforced, so that a significant movement the wrong way is recorded as a violation and never counted as support.

## B. Formal framework

This appendix states the protocol's machinery as mathematics. Everything here is formalized in Lean 4, core-only, with every theorem checked at the kernel level; the formal names are given so that each proposition can be located in the development. Nothing in this appendix is empirical: **no theorem can settle whether noise changes any of these quantities, and that is the empirical claim of the study (§B.5).**

### B.1 Definitions

A **trial** is a pair $o = (c, y) \in \mathcal{O}$ where $c \in \mathbb{N}$ is the reported confidence on a fixed integer scale and $y \in \{0,1\}$ indicates correctness against the item's constructive gold label. A **sample** is a finite list $T = [o_1, \dots, o_n]$.

**Definition 1 (the gate).** For a threshold $\tau$, the gate admits $o$ iff $c \ge \tau$:

$$\mathrm{Adm}_\tau(o) \;=\; [\,c \,\ge\, \tau\,].$$

**Definition 2 (accepted set, coverage).** With $|\cdot|$ the list length,

$$\mathrm{Accepted}_\tau(T) \;=\; \sum_{o \in T} \mathrm{Adm}_\tau(o), \qquad \mathrm{Cov}_\tau(T) \;=\; \frac{\mathrm{Accepted}_\tau(T)}{|T|}.$$

**Definition 3 (silent error and conditional error).** The silent error counts trials that are *both* admitted and wrong; the conditional error is its rate among admitted trials:

$$\mathrm{Risk}_\tau(T) \;=\; \sum_{o \in T} \bigl[\mathrm{Adm}_\tau(o) \wedge \lnot y_o\bigr], \qquad \mathrm{CondErr}_\tau(T) \;=\; \frac{\mathrm{Risk}_\tau(T)}{\mathrm{Accepted}_\tau(T)}.$$

The distinction between $\mathrm{Risk}_\tau$ (a count over the whole sample) and $\mathrm{CondErr}_\tau$ (a ratio whose denominator moves with $\tau$) is not cosmetic; it decides which estimator is available (§B.4).

**Definition 4 (discrimination).** For samples of correct and incorrect confidences $C = [c : (c,1) \in T]$ and $E = [c : (c,0) \in T]$, the ordered-pair count and the associated AUC are

$$W(C, E) \;=\; \sum_{c \in C} \#\{\,e \in E : e < c\,\}, \qquad \mathrm{AUC}(T) \;=\; \frac{W(C,E)}{|C| \cdot |E|}.$$

### B.2 What is assumed, and what is only defined

Two things are **assumed**, and they are the only assumptions.

**(A1) Exchangeability.** Within a unit (an item crossed with a seed), the two arm labels are exchangeable under the null that the manipulation does not change the joint distribution of $(c, y)$. This is what licenses an exact permutation distribution rather than an asymptotic one.

**(A2) Monotone confidence encoding.** If a collection of confidences is transformed by any strictly increasing map, the *ordering* relations among them are preserved. This is a property of the encoding, not a claim about calibration; §B.4 shows why the distinction matters.

Everything else is a **definition**, including $\mathrm{Adm}$, $\mathrm{Cov}$, $\mathrm{Risk}$, $\mathrm{CondErr}$ and $\mathrm{AUC}$. In particular, no assumption is made that confidence is calibrated, well-ordered, or comparable across arms.

### B.3 Propositions with proof outlines

**Proposition 1 (accepted set is monotone in the threshold).** *For $\tau_1 \le \tau_2$ and any $T$, $\mathrm{Accepted}_{\tau_2}(T) \le \mathrm{Accepted}_{\tau_1}(T)$.* Formal name `accepted_mono`. *Proof.* $c \ge \tau_2$ implies $c \ge \tau_1$ by transitivity, so each indicator is pointwise non-increasing; a sum of pointwise non-increasing indicators is non-increasing. The order relation on thresholds is also characterised as an equivalence, `admissible_iff_limen_le`.

**Proposition 2 (coverage is non-increasing in the threshold).** Formal name `coverage_mono`. *Proof.* Immediate from Proposition 1 after dividing by the positive constant $|T|$; recorded separately because coverage is a dependent variable and the division by a fixed denominator is what makes the `Nat`-arithmetic statement non-trivial in the formalization.

**Proposition 3 (the silent-error count is NON-INCREASING in the threshold).** *For $\tau_1 \le \tau_2$, $\mathrm{Risk}_{\tau_2}(T) \le \mathrm{Risk}_{\tau_1}(T)$.* Formal name `risk_mono`.

*‹**This proposition refuted the protocol.** The protocol originally asserted the *opposite* — that raising the threshold could only increase the silent-error count. The kernel proved otherwise, and the refutation is preserved in the development as `protocol_said_nondecreasing_is_FALSE` so that the error is visible rather than quietly corrected. The direction matters because it is the formal reason the original H1.2 could not hold: **a fixed-threshold silent-error rate cannot rise under a manipulation that deflates confidence**, since deflation moves trials out of the accepted set entirely.›*

*Proof.* By case analysis on whether a trial is bad at the higher threshold. If $c \ge \tau_2$ and $y = 0$ then $c \ge \tau_1$, so the same trial is bad at the lower threshold and contributes no increase; if not, it contributes nothing at either. Induction over the list.

**Proposition 4 (existence and optimality of a least admissible threshold).** *There is a total order in which a least admissible threshold exists (`admissible_exists`, `top_admissible`), and the most lenient admissible threshold maximises coverage (`least_admissible_maximises_coverage`) while admitting at least as many trials as any other admissible choice (`least_admissible_is_at_least_as_good`).* *Proof.* Admissibility is downward closed by Proposition 1, so the admissible set is an initial segment of the threshold order; its maximum is the least restrictive choice, and Proposition 1 gives the coverage comparison.

**Corollary 4.1 (`clean_pins_at_floor`).** *If the clean arm's silent-error count already satisfies the budget at the lowest admissible threshold, the selector returns that floor for every sample size and every budget.* The selection rule therefore reports **a design constant rather than an estimate** whenever the clean arm is at the floor, which is why the dev-fitted threshold cannot be read as a quantity the data discovered.

**Proposition 5 (small-$N$ degeneracy).** *If the error budget is $\varepsilon$ and $N$ is a sample size with $\lfloor \varepsilon N \rfloor = 0$, the minimum admissible threshold is the all-reject threshold.* Formal names `budget_collapses_to_zero_on_small_dev`, `empty_dev_is_degenerate`. *Proof.* The budget admits zero errors; any threshold admitting a wrong trial violates it; by Proposition 3 the count is non-increasing in $\tau$, so the admissible set shrinks to the single all-reject point. At $\varepsilon = 0.05$ this bites below $N = 20$. `the_threshold_below_the_limen_keeps_only_the_error` records the adjacent pathology: one step below the admissible threshold the retained set is precisely the errors.

**Proposition 6 (accuracy is not diagnostic of understanding).** *Two samples can have identical correctness profiles and different confidence profiles, and the gate's reading of them differs.* Formal names `acc_is_not_diagnostic_of_understanding`, `one_movement_three_readings`, `acc_defers_wrong_mono`, `cond_error_complements_cond_accuracy`. *Proof.* Construct two samples agreeing on $y$ and differing in $c$; the gate admits different subsets, so any quantity computed on the admitted set separates them while accuracy — a function of $y$ alone — does not.

**Corollary 6.1 (the conditional quantities are complements).** `CondErr` and the conditional accuracy among admitted trials sum to one, so the two carry the same information and must not both be counted as evidence. This is the declared dependency that the Holm family must respect.

### B.4 The scale-free result, and why it is load-bearing

**Theorem 7 (scale-free discrimination).** *For any $f : \mathbb{N} \to \mathbb{N}$ that is strictly increasing, and any correct and incorrect confidence lists $C$ and $E$,*

$$W\bigl(f(C), f(E)\bigr) \;=\; W(C, E).$$

Formal name `winsAux_map_of_strictMono`. The kernel reports that this theorem **depends on no axioms at all**, which is a stricter bar than the no-`sorry` discipline applied elsewhere.

*Proof outline.* By induction on $C$. For the inductive step it suffices that the inner count is preserved, `countLt_map`: the number of entries of $f(E)$ strictly below $f(c)$ equals the number below $c$. That in turn needs the order-reflecting property of a strictly increasing map on $\mathbb{N}$, `lt_of_map_lt`: from $f(a) < f(b)$ infer $a < b$. This is proved by trichotomy — $a = b$ makes the images equal, and $a > b$ reverses the inequality by strict monotonicity — so the map reflects order as well as preserving it, and the two predicates agree elementwise.

**Why it matters.** H1.2′ is measured by the AUC, and the AUC is this count divided by a constant. The theorem says the estimand **reads only the ordering of confidences and never their values**, so no strictly increasing miscalibration of the instrument's confidence scale can move it. That is not a convenience: the instrument's own library warns that some confidences are substituted with a constant and are uncalibrated, and an estimand that bounds a *rate* at an absolute threshold would rest precisely on the calibration the warning puts in doubt. The theorem is the formal discharge of the claim that H1.2′ is robust to that warning — and it is the reason the replacement hypothesis was chosen over the two alternatives that were measured and rejected.

### B.5 What is not proved

Nothing in this appendix says that noise changes $\mathrm{Acc}$, $\mathrm{Cov}$, $\mathrm{Risk}$ or $\mathrm{AUC}$. Those are statements about a particular instrument on a particular task, and no theorem can settle them; they are the empirical content of the study, tested by the exact permutation procedure of §D.1 and reported in §D.4. What the formalization does is different and narrower: it fixes what the quantities *are*, proves the relationships that hold by definition, and supplies one theorem — Theorem 7 — that a design choice depends on.

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

The index is anchored on a **published human result** rather than on a threshold chosen for convenience: Rayner and colleagues' interior-scrambled condition (2006) — the harsher of the two variants they report — **measured under this index rather than quoted from the paper**: applying the recoverability index to that condition returns 0.4480, and therefore a floor for human tolerance. The levels are then determined by rule: **$\lambda_{\mathrm{lo}} = 0.05$** is the smallest grid point whose mean recoverability clears the anchor, and **$\lambda_{\mathrm{mid}} = 0.18$** is the largest point that still clears it. The margin at $\lambda_{\mathrm{lo}}$ is $+0.0728$.

Two earlier instruments were measured and **rejected**, and the reason is quantitative. An **absolute three-level rating** (recoverable / workable / not recoverable) never emitted its lowest category in 120 sentences and reached weighted κ of only 0.073 and 0.137 against a 0.60 floor: it could not express what it was for. **Pairwise comparison against clean text** saturated the other way — the probability that a perturbed sentence was judged harder was 0.90–1.00 at *every* level including the mildest, so it detected the presence of corruption but not its degree. Neither failure is a rater failure; both are instrument failures, and the anchored index is used precisely because it is monotone over the range that matters.

### C.4 The instrument

The instrument is a non-autoregressive encoder under a permissive licence, **pinned by revision digest and by per-file SHA-256**, with an integrity guard that re-verifies the pin on every run. It was never trained: the study measures a fixed device, and holding parameters frozen is what makes a contrast between noise levels a statement about the manipulation rather than about the model's drift. What the pin does **not** guarantee is that the instrument's confidence is calibrated — the library warns, unprompted, that the checkpoint ships temperatures outside its valid range and that affected confidences are substituted with a constant and are uncalibrated. Two of the three dependent variables are functions of confidence, so the warning was bounded by measurement rather than trusted: on the confirmatory run **0 of 13,692 rows carry the substituted constant**, and the confidence values span 0.2652–1.0000 over 5,026 distinct values. Because a single sample cannot make a guarantee, the observation is now carried as a **checked invariant** that fails on any trial file containing the constant. Reading a warning is not the same as acting on one.

## D. Analysis, power and results
### D.1 Estimators

The design is paired at the **unit** level: a unit is an item crossed with a seed, and it carries exactly one clean and one noisy observation, each with its own confidence $c$ and correctness $y$. Let $u = 1, \dots, n$ enumerate the units, and let a signed statistic be any function $T$ of the paired sample.

**Definition (exact paired permutation test).** Under the null that the manipulation does not change the joint distribution of $(c, y)$ within a unit, the two arm labels are exchangeable, so the permutation distribution of $T$ is generated by independently swapping each unit's two observations:

$$ T^* \;=\; T\Bigl(\{(X_u^{(\sigma_u)}, Y_u^{(\sigma_u)})\}_{u=1}^n\Bigr), \qquad \sigma_u \sim_{\text{i.i.d.}} \mathrm{Bernoulli}(0.5), \tag{1} $$

where $(X_u^{(1)}, Y_u^{(1)}) = (X_u, Y_u)$ and $(X_u^{(0)}, Y_u^{(0)}) = (Y_u, X_u)$. The two-sided $p$-value is

$$ p \;=\; \frac{1 + \sum_{m=1}^{M} \mathbb{1}\{|T^*_m| \ge |T_{\mathrm{obs}}|\}}{M + 1}, \tag{2} $$

with $T^*_m$ drawn from the permutation distribution and $M = 2^n$ (the exact enumeration) in our case.

This test is **exact** under the exchangeability assumption. Within each unit, the assignment of the two observations to arms is exchangeable under the null: $(X_u, Y_u) \stackrel{d}{=} (Y_u, X_u)$ for all $u$, and units are mutually independent. Nothing else is assumed. The test requires no distributional form and no asymptotics; it is the limiting case of a random-intercept model carrying only the item effect. The $+1$ corrections in both numerator and denominator are the standard correction that makes the reported $p$ a valid test rather than a lower bound.

**Definition (the discrimination estimand).** With $C$ the confidences of correct trials and $E$ those of incorrect trials *within one arm*,

$$ \mathrm{AUC}(\lambda) \;=\; \frac{1}{|C| \cdot |E|} \sum_{c \in C} \sum_{e \in E} \mathbb{1}(c > e) + \tfrac{1}{2}\,\mathbb{1}(c = e), \tag{3} $$

and the tested contrast is $T = \mathrm{AUC}(\lambda_{\mathrm{mid}}) - \mathrm{AUC}(0)$. Because $\mathrm{AUC}$ is a within-unit rank statistic, the same exchangeability argument licenses the exact paired permutation for $T$, and no second inferential framework is introduced. The one-sided alternative for H1.2′ is that $T > 0$: the gate's discriminability rises under noise.

**One estimand is deliberately excluded from the family.** The conditional error among admitted trials, $\mathrm{CondErr}@\tau = \Pr(y = 0 \mid c \ge \tau)$, has a denominator that **changes with the condition** — the admitted set is 121 items clean against 61 under noise, with an intersection of only 51 — so the within-item pairing that the permutation test relies on does not exist for it. It is reported in §D.4 and is **not** a member of the confirmatory family. Naming an estimator the code does not implement is how a pre-registration and an analysis drift apart without anyone noticing.

### D.2 The family and direction enforcement

The confirmatory family comprises exactly three hypotheses, corrected by the Holm sequentially rejective procedure at family-wise $\alpha = 0.05$: the smallest $p$-value is compared against $0.05/3 = 0.0167$, the next against $0.05/2 = 0.0250$, and the last against $0.05$. Holm requires no independence assumption among the tests and is uniformly more powerful than Bonferroni.

The three hypotheses and their predicted directions are:

- **H1.1**: accuracy falls at $\lambda_{\mathrm{mid}} = 0.18$ (exact McNemar on paired discordant pairs, with deferred trials counted as errors);
- **H1.2′**: within-arm AUC contrast rises (gate discriminability increases);
- **H1.3**: coverage at $\varepsilon = 0.05$ falls.

**Direction is part of the hypothesis.** Each hypothesis carries its predicted sign, and the Holm input is the two-sided $p$-value **only when the observed movement agrees with the predicted direction**. A two-sided $p$-value is blind to direction: it reports the magnitude of deviation from the null, and a large effect in the *opposite* direction is indistinguishable from support under a naive reading. Under the direction rule, such a movement is recorded as a **direction violation** — a finding in its own right — and is **never counted as evidence** for the hypothesis.

This rule is not a technicality; it is what converted a genuine result into a correction. The original fixed-threshold silent-error hypothesis moved significantly in the *opposite* direction: silent error fell rather than rose. Without the direction rule, the two-sided $p$-value of $5.00 \times 10^{-5}$ would have been entered into Holm as support for a hypothesis that the data had actually refuted. The direction rule correctly classified it as a refutation, which motivated the replacement hypothesis H1.2′.

### D.3 Power

McNemar is a binomial test on the **discordant** pairs, so power depends on $n \cdot \pi_d$ and on the conditional asymmetry $\pi = c/(b + c)$, not on $n$ alone. A design sized on the McNemar structure is insensitive to the total sample size $n$ once the discordant-pair count is fixed.

| Quantity | Value |
|---|---|
| Paired discordance $\pi_d$, measured on dev | **0.2036** (frozen estimate 0.1833) |
| Expected discordant pairs at $n = 652$ | 132.7 |
| Conditional asymmetry measured | 45 with the hypothesis vs 12 against → $\pi = 0.7895$ |
| Holm-adjusted $\alpha$ (three-test family) | 0.0167 |
| **Minimum detectable effect at 80 % power** | **5.41 accuracy points** |
| Effect the design pre-registered | 5.0 points |

The minimum detectable effect — 5.41 points against a pre-registered target of 5.0 — is a match to within a point, so the sample size is sized for exactly the effect the design declared. A first version of this calculation reported the design as *over-powered by 5.11×*, obtained by comparing the MDE against the **measured** effect rather than the pre-registered target; that comparison is misleading because a design is sized for the effect it declares, and a larger observed effect does not render its sizing a defect. Converting $\pi$ into accuracy points reverses the conclusion, and the conversion now lives in the analysis script rather than in a reader's head.

### D.4 Results

The confirmatory run used the test split: **652 items × 7 noise levels × 3 frozen seeds = 13,692 trial records, zero failures**. Table D1 gives every quantity at every noise level, read from the derived per-level summary.

| $\lambda$ | Accuracy | Within-arm AUC | Coverage@0.9 | CondErr@0.9 | Errors rejected (%) |
|---|---|---|---|---|---|
| 0.00 | 0.8926 | 0.6014 | 0.4479 | 0.0925 | 61.4 |
| 0.03 | 0.8834 | 0.6587 | 0.4080 | 0.0764 | 73.2 |
| 0.05 | 0.8707 | 0.6951 | 0.3850 | 0.0730 | 78.3 |
| 0.08 | 0.8574 | 0.7015 | 0.3308 | 0.0742 | 82.8 |
| 0.12 | 0.8246 | 0.7271 | 0.2878 | 0.0817 | 86.6 |
| 0.18 | 0.7720 | 0.7601 | 0.2111 | 0.0702 | 93.5 |
| 0.25 | 0.7025 | 0.7483 | 0.1585 | 0.0710 | 96.2 |

*Table D1.* Seven noise levels, test split, 1,956 trials per level. Source: the derived per-level summary from `data/processed/stage2_lambda_summary.csv`, which the figure pipeline recomputes from the trial record; nothing here is interpolated or modelled.

The within-arm AUC is **not monotone** in the noise level. It rises from 0.6014 at $\lambda = 0$ to 0.7601 at $\lambda_{\mathrm{mid}} = 0.18$, then falls to 0.7483 at $\lambda = 0.25$, so discrimination improves with corruption up to a point and then begins to degrade. The pre-registered contrast is unaffected (it compares $\lambda_{\mathrm{mid}}$ against zero, as fixed in advance), but a reader should not carry away the impression of a monotone trend that the data do not show.

The family. All three hypotheses were rejected under Holm with **no direction violations**:

| Hypothesis | Predicted | raw $p$ | Verdict |
|---|---|---|---|
| H1.1 accuracy falls | falls | 4.42 × 10⁻³⁶ | **rejected — supported** |
| H1.2′ discriminability rises | rises | 2.00 × 10⁻⁴ | **rejected — supported** |
| H1.3 coverage falls | falls | 5.00 × 10⁻⁵ | **rejected — supported** |

H1.1 discordant pairs: $b = 71$, $c = 307$ — more than four items newly wrong for every one newly right. H1.2′ contrast $+0.1587$ over 1,956 units. H1.3 mean coverage fall $0.2904$, 95 % CI $[0.2679, 0.3154]$.

#### D.4.1 What the pre-run predicted

| Predicted on dev, before the seal | Confirmatory outcome |
|---|---|
| $\pi_d \approx 0.2036$ | 0.19 ($b + c = 378$ over 1,956 units) |
| Minimum detectable effect 5.41 points | Accuracy contrast ≈ 12.1 points |
| H1.2′ contrast ≈ $+0.1201$ | **$+0.1587$** |
| The original H1.2 falls | **$-0.0266$** |
| No confidence contamination | **0 of 13,692 rows** |

Both prediction classes held. The replacement hypothesis replicated, and the refuted hypothesis reproduced its refutation exactly.

#### D.4.2 Scientific significance

For this manipulation the silent-error premise **fails, and it fails in a specific way**. Typo noise costs about twelve accuracy points and 23.7 coverage points at the reported threshold (the mean paired fall is 0.2904), yet the gate's discriminability *rises* — from 0.601 to 0.760 — and the share of errors the gate rejects rises from 61.4 % to 93.5 %. The damage therefore concentrates in **what the model declines to answer**, not in what it confidently gets wrong. Two consequences follow. First, confidence remains a usable control signal under orthographic noise, so the common remedy for a feared silent-error problem — recalibrating or replacing the gate — addresses a failure that does not occur here. Second, the real failure is a **coverage** failure rather than a correctness one, and coverage is remedied by throughput rather than by thresholds.

## Figures

**Figure 1. The three pre-registered hypotheses across the noise grid.**

![Figure 1](figures/fig1_stage2_hypotheses.png)

**Typo noise costs accuracy and coverage while making the confidence gate MORE discriminative, not less.** Each panel is one pre-registered hypothesis, tested with the exact paired permutation of the protocol and Holm-corrected across the three-hypothesis family; all three were confirmed with no direction violations. (a) Accuracy falls by 12.1 percentage points from lambda = 0 to lambda_mid (H1.1, p = 4.4e-36). (b) The within-arm AUC between correct and incorrect trials RISES from 0.601 to 0.760 (H1.2', p = 2.0e-04) -- the gate separates right from wrong more sharply under noise. (c) Coverage at tau = 0.9 falls by 23.7 points (H1.3, p = 5.0e-05), so far fewer trials are answered at all. All panels use the **test split** of the pre-registered window: 652 items x 3 frozen noise seeds = 13,692 trial records from the pinned instrument, 0 failures. The confidence rule is `answer if c >= tau else defer`. Dashed vertical lines mark the two calibrated noise levels, lambda_lo = 0.05 and lambda_mid = 0.18. Every plotted value is read from `data/processed/stage2_lambda_summary.csv`, which `scripts/build_stage2_figures.py` derives from `measurement/out/confirm_trials.jsonl`. No point is interpolated or modelled.

**Figure 2. Where the errors go: the gate rejects most of what noise breaks.**

![Figure 2](figures/fig2_stage2_error_destination.png)

**The errors noise creates arrive below the gate: they are loud, not silent.** Panel (a) decomposes every error at each noise level into the share the gate rejects and the share it admits. Under noise the rejected share rises from 61.4% to 93.5%, so the gate catches most of what noise breaks. Panel (b) shows the two error measures diverging: the conditional error among admitted trials is flat (0.092 to 0.070), while the all-trial silent error FALLS (0.041 to 0.015). A fixed-threshold silent-error rate cannot rise under a manipulation that deflates confidence, which is why the original H1.2 was refuted and replaced by H1.2'. All panels use the **test split** of the pre-registered window: 652 items x 3 frozen noise seeds = 13,692 trial records from the pinned instrument, 0 failures. The confidence rule is `answer if c >= tau else defer`. Dashed vertical lines mark the two calibrated noise levels, lambda_lo = 0.05 and lambda_mid = 0.18. Every plotted value is read from `data/processed/stage2_lambda_summary.csv`, which `scripts/build_stage2_figures.py` derives from `measurement/out/confirm_trials.jsonl`. No point is interpolated or modelled.

**Figure 3. Why the gate separates better under noise.**

![Figure 3](figures/fig3_stage2_gate_separation.png)

**The gate does not merely shift down with noise -- it separates correct from incorrect trials more sharply.** Median confidence for correct and for incorrect trials, at the clean level (left) and at lambda_mid (right); the double arrow is the separation between them. Correct-trial confidence falls from 0.888 to 0.783, but incorrect-trial confidence falls more than twice as far, from 0.784 to 0.549. The separation therefore widens from +0.103 to +0.234, and the corresponding within-arm AUC rises from 0.601 to 0.760. The estimand reads only the ORDER of confidences, so it is invariant to any monotone rescaling of the instrument's confidence scale -- machine-checked in the formalization repository. All panels use the **test split** of the pre-registered window: 652 items x 3 frozen noise seeds = 13,692 trial records from the pinned instrument, 0 failures. The confidence rule is `answer if c >= tau else defer`. Dashed vertical lines mark the two calibrated noise levels, lambda_lo = 0.05 and lambda_mid = 0.18. Every plotted value is read from `data/processed/stage2_lambda_summary.csv`, which `scripts/build_stage2_figures.py` derives from `measurement/out/confirm_trials.jsonl`. No point is interpolated or modelled.

**Figure 4. The scale-free property, measured on the confirmatory record.**

![Figure 4](figures/fig4_stage2_scale_free.png)

**The estimand chosen for H1.2′ is invariant under exactly the distortion the instrument's own library warns about, and a threshold quantity is not.** The confirmatory record was rescaled by a family of strictly increasing maps $c \mapsto c^{\gamma}$, $\gamma \in [0.35, 3.00]$ — nineteen transforms applied to all 6,067 confidences of the $\lambda = 0.18$ arm. **(a)** The within-arm AUC does not move: its spread across the entire family is **0.000 × 10⁰**, not merely small, because the statistic reads only the ORDER of confidences and a strictly increasing map cannot change an order. This is the content of the kernel-verified scale-free theorem, measured rather than asserted. **(b)** Under the *same* family, coverage at the fixed threshold $\tau = 0.90$ moves by **43.6 percentage points** (0.054 to 0.489) while accuracy is unchanged at 0.772 — accuracy cannot move, since rescaling confidences cannot reorder correctness. **The contrast is the point:** an estimand that bounds a rate at an absolute threshold inherits the instrument's calibration, and one that reads order does not. The instrument's library states unprompted that this checkpoint's temperatures are invalid and that affected confidences are uncalibrated; H1.2′ was chosen, before the confirmatory run, precisely so that the hypothesis would not rest on the quantity that warning puts in question. n = 6,067 trials at $\lambda = 0.18$, all three frozen seeds pooled. Every plotted number is computed in the figure script from the confirmatory trial record; none is typed in.

**Figure 5. The proof dependency graph, parsed from the kernel source.**

![Figure 5](figures/fig5_stage2_proof_graph.png)

**The 27 machine-checked results form a directed proof structure with 14 independent premises and 15 invocations among them, and the theorem the design rests on sits in a module of its own.** Each node is a theorem in the kernel; arrows point from a proof to the results it invokes. The graph is **parsed from the formalisation's source** — each declaration is sliced up to the next and searched for the names of its siblings — so the arrows are the formalisation's own structure rather than a transcription of how it is described. The four blue nodes are the scale-free module of the sibling formalisation repository; `#print axioms` reports at build time that **none of its theorems depends on any axiom at all**, a stronger bar than the no-`sorry` standard the rest of the kernel is held to. No empirical premise appears anywhere in the graph: every result follows from the protocol's definitions alone, and no theorem here states that noise changes any quantity — that is the empirical claim, and it is settled by the confirmatory run, not by proof.

**Figure 6. The formalisation corrected the protocol, and the corrections were kept.**

![Figure 6](figures/fig6_stage2_corrections.png)

**The formalisation changed the research, and the corrections were kept rather than edited away.** A formalisation that only confirms what was already written is decoration. This one refuted its own protocol's wording: the kernel establishes by `decide` that the silent-error count is **non-increasing** in the threshold, where the protocol had asserted the opposite and built a hypothesis on it. Three further statements were settled the same way — the $\varepsilon = 0.05$ budget rule was shown to give a shut gate for $N < 20$, the accuracy reading was shown not to be diagnostic of understanding, and two readings the family treated as distinct were shown to be **one** quantity. The left column reproduces claims from the record's own corrections table, kept there on the stated grounds that an inaccurate status record is worse than an absent one; the right column gives what was measured or proved, with the italic name of the kernel result that settled it. **The figure's content is parsed from those two documents**, so it cannot assert a correction the repository does not record.

**Figure 7. What the manuscript's claims rest on.**

![Figure 7](figures/fig7_stage2_evidence_chain.png)

**A third of this manuscript's claims rest on a machine-checked proof, and the assumptions are visible as assumptions.** The protocol's provenance table classifies every claim by its authority, and this figure counts that table: **16 claims PROVED** — each naming a theorem the kernel checked, with the table's generator failing if such a theorem does not exist — **6 MEASURED** off the confirmatory or pre-run record, **6 ASSUMED** and carried as assumptions rather than as results, and **6 TO BE TESTED** in Phase II. The count matches the generator's own independent total of 34, which is the property that makes the figure worth drawing: it is derived from the table rather than summarised from it. **No claim about the effect of noise on accuracy, silent error or coverage appears as PROVED** — those are the empirical claims, settled by the confirmatory run and by nothing else, and a figure that blurred that distinction would misrepresent the work it describes.

**Figure 8. The failure-class partition, drawn on the two diagnostics that separate the classes.**

![Figure 8](figures/fig8_stage2_failure_partition.png)

The two failure classes, drawn on the two diagnostics that separate them. **(a)** The measured trajectory across the noise grid, against the share of errors the gate rejects (does the gate *see* the damage?) and the conditional error among admitted trials (does it reach *committed* answers?). The path runs right and slightly down - 61.4 % to 96.2 % rejected, conditional error flat at 9.25 % to 7.02 % - the loud, channel-side region. The **silent, model-side** region is where meaning-corrupting noise is predicted to land, marked hollow because it is a prediction and not a measurement. **(b)** The same two diagnostics against noise level: the rejection share rises monotonically while the conditional error does not. Every plotted value is read from `data/processed/stage2_lambda_summary.csv`; nothing is interpolated or modelled.


## E. Interpretation, limitations and reproduction

### E.1 Interpretation

Taken jointly, the three confirmed hypotheses describe a manipulation whose damage is **visible where it occurs**. Typo noise costs accuracy and coverage, yet the confidence gate separates correct from incorrect trials *more* sharply under noise, and the share of errors arriving below the gate rises from 61.4 % to 93.5 %. The errors are not merely detectable in principle; in this design they are overwhelmingly detected in fact.

**(a) For gated typed decisions.** The common fear is that noise corrupts the input in a way that corrupts the *judgement* while leaving the *reported confidence* intact, so the gate waves through an error it was built to catch. That is not what happens here. Noise deflates confidence along with the answer, and deflation is precisely the signal the gate reads. A gate calibrated on clean text therefore remains a working control under this manipulation — it does not need to be replaced by abstention-on-uncertainty, and the threshold does not need rescaling to remain useful.

**(b) For how the risk is framed.** The framing shifts from a **correctness** failure to a **coverage** failure. Under noise the system is not more often wrong in what it commits to; it commits to far less. At the highest level examined, coverage is 0.16 against 0.45 clean — the model declines roughly two-thirds of the trials it would otherwise have answered. A system whose value depends on answering will fail under such noise, but it fails *observably*: the deferral rate moves before the error rate among committed answers does. Operators monitor the wrong quantity if they monitor only accuracy among answers given.

**(c) Why a null-shaped result is a finding.** "The conditional error does not rise" sounds like an absence. It is not, for two reasons. First, the *direction* is informative and was predicted before the run: an equivalence-shaped claim is a measurement when it is bounded, and here the bound is quantitative — the conditional error moves by −0.0108 against a baseline of 0.0826. Second, the mechanism is identified rather than merely negated: the gate rejects 93.5 % of the errors because the errors carry low confidence, which the scale-free theorem shows cannot be an artefact of the instrument's calibration. A finding that names the mechanism and excludes the obvious confound is a substantive result even when its headline is that something does *not* happen.

**What this does not show.** It does not show that confidence is calibrated, or that it is comparable across models, tasks or noise types. It does not show that any particular deployed gate is safe. And it does not show that the mechanism generalises beyond orthographic noise — noise that corrupts *meaning* rather than *form* could plausibly deflate nothing.

### E.2 Limitations

**Single language and single instrument.** The study is English-only on one frozen encoder. The fixed effect it measures is therefore a property of this pairing, not of "models". A different instrument with a different confidence head could show a different sign, and the direction is the whole finding — so it must be re-established, not assumed. What would not change the interpretation: the identification of *where* the damage lands (coverage rather than committed-answer correctness), because that follows from the gate's construction.

**Synthetic, keystroke-faithful noise.** The generator models the keyboard, not a population of typists: it has no word-level errors, no autocorrect, no systematic homophone substitutions. A real error corpus would test whether human errors are equally self-announcing. What would change: if real typing errors were substantially *more* confusable than the generator's, the AUC might not rise, and the conclusion would weaken accordingly.

**The instrument's confidence is uncalibrated by its own vendor's warning.** This is why the main estimand is scale-free — but scale-freeness protects the *ordering* claims only. The absolute coverage figures do depend on where the fixed threshold sits on a scale the warning puts in question, and a reader should treat the coverage levels as design-relative rather than as calibrated probabilities. The contamination check bounds this: zero of 13,692 rows carry the substituted constant.

**Three hypotheses, one task, one register.** The family is small and the task is word-level decision under a service-request register. The multiplicity correction is honest for the family declared, and says nothing about claims outside it.

### E.3 Relation to prior work

Two bodies of practice bear on this. Work using **model confidence as a control signal** generally assumes that confidence and correctness co-vary in a stable way; this study finds that noise *strengthens* the co-variation rather than eroding it, in the sense that the ordering of correct above incorrect becomes more reliable. That is a favourable result for the practice, and it is instrument- and manipulation-specific. Work on **typographic robustness** typically reports aggregate degradation; the contribution here is not another aggregate number but the *decomposition* of that degradation across a gate, which is what determines whether an operator sees it. The direction of the decomposition is opposite to the common expectation, and that — not the magnitude — is the reportable claim.

### E.4 Reproduction

1. **Protocol and pin.** The frozen protocol is pinned by digest in the repository's anchor record, which also carries its version and byte count; the anchor is what makes a version number identify a content. The instrument is pinned by revision digest plus per-file SHA-256, verified on every run by an integrity guard.
2. **Stimulus bank.** The 652-item test bank is pre-built and stored, produced statically without running any model.
3. **Confirmatory record.** One command regenerates it from the pinned instrument over that bank: the run script, pointed at the pre-built bank with the seven noise levels, three seeds, and the compute device. Projected cost is minutes on a consumer GPU.
4. **Analysis.** The pre-registered analysis script consumes the trial record and emits the family result. The replacement-hypothesis contrast is a separate script with its own positive and negative controls, and the confidence-contamination invariant is a third. All three are run against the record.
5. **Figures and tables.** One script derives the per-level summary from the trial record; the figures read that summary, and the captions are generated from it, so a caption cannot disagree with its figure. The SI's own tables are checked against the same summary by a dedicated checker, which fails if a table cell differs from its source.
6. **Guards and the commit gate.** The full suite runs as one command and each check is exercised on an injected defect that must make it fail. A versioned pre-commit hook runs the suite and **refuses the commit** when it is red, because a rule about ordering that nothing enforces is not a rule.
7. **Formal core.** The machine-checked development accompanies the repository: every theorem kernel-verified, none depending on `sorry`, and the scale-free discrimination theorem reported as depending on **no axioms at all**.

Everything above is released together, so that the record of what was decided, the code that decided it, and the checks that would have caught it being wrong travel as one artefact.

## F. Significance in the age of large language models

The title places this study in a period, and until now nothing in this document said what the period has to do with it. It has a great deal, and the connection is not decorative: **the large language model era is the first in which the primary human-to-machine channel is typing, at scale, and the first in which the machine's decision to answer or decline is a shipped product feature rather than a research technique.** Those are the two conditions this study measures.

### F.1 The typed channel stopped being an edge case

For most of computing, a corrupted character was an input-validation problem. The channel is now the interface. A language model is addressed in natural language typed by a human, dictated into speech recognition, or pasted from a document that was itself scanned or converted; retrieval pipelines feed it text with the same defects, and agent runtimes feed it their own generated text back. Every one of those steps is a noisy channel in the technical sense — an intended symbol destroyed by the medium between two parties — and they compose.

The field already agrees the surface form is decisive, which is why the LLM era is arguing about it. Prompt-lexical-sensitivity work finds that minor lexical changes can trigger disproportionate performance fluctuations and asks for the mechanism at n-gram level (Xie et al. 2026, arXiv:2608.20349); a counter-current argues that part of the reported sensitivity is an evaluation artefact rather than a model property (Hua et al. 2025, arXiv:2509.01790). That disagreement is itself the LLM-era fact: **a field this concerned with how small surface changes move a model has not asked where in the decision those changes land.**

The contribution here is a third position in that argument. The surface form does not merely move a score; it **decomposes the outcome**, and the decomposition is not what the aggregate suggests. On this instrument, the same manipulation that costs 12 accuracy points leaves the gate's discrimination **higher**, because the trials it corrupts lose confidence along with correctness. **A literature reporting aggregate degradation would read that as uniform damage.** It is not uniform, and the direction matters more than the magnitude.

### F.2 The era's dominant safety vocabulary is the silent failure, and the input channel is its inverse

The LLM safety discourse is organised around failures that do not announce themselves: hallucination that reads fluently, agents that keep running and push plausible results to a human, memory and tool semantics drifting over long horizons. A longitudinal taxonomy of a production agent runtime names exactly this — **silent failures** — as the class that matters operationally, because the system continues and the output looks like work (Wu 2026, arXiv:2606.14589).

This study measures a class of failure that is the **opposite**, and it is worth being precise about what that does and does not mean. It does not contradict that taxonomy. It partitions it. **Silent failures arise from the model's own unreliability — memory, tool semantics, narrative coherence. Loud failures arise from the channel.** Here, 93.5 % of the errors noise creates arrive below the gate, against 61.4 % clean: the corrupted trial loses confidence because the surface form is improbable under the intended meaning, and that loss is the signal the gate reads. The errors announce themselves because the *corruption* is what makes them wrong.

The operational consequence is a distinction that decides the remedy, and getting it backwards wastes the remedy entirely. A silent-failure problem calls for monitoring, adversarial testing, and external verification. A loud-failure problem calls for **availability**: the system is not committing to more wrong answers, it is answering far less often, and no amount of recalibration changes that.

### F.3 Abstention became a product feature, so the risk–coverage frontier became a deployment surface

Abstention used to be a classifier technique. In this era it is a feature that is argued about, benchmarked, and trained for: AbstentionBench measures whether reasoning models can decline on underspecified or unanswerable queries on the stated grounds that **knowing when not to answer is as critical as answering correctly** (Kirichenko et al. 2025, arXiv:2506.09038), and a parallel line trains the behaviour directly.

That changes what a coverage number is. In a benchmark, a 29-point coverage fall is a statistic. In a deployment it is a **volume of work returned to humans**: every deferred request becomes a regeneration, a reprompt, a manual answer, or an abandoned session. **The finding of this study is therefore not "accuracy degrades" — which the era already knows — but "under the channel that this era made primary, the abstention feature fires far more often and the damage lands on human time rather than on committed correctness."** That is an operational claim about an LLM-era feature, and it is the reason the deferral is priced as a human cost in §T.1 rather than as a null outcome.

It also reframes what the era's trust problem looks like. In classical automation, disuse meant an operator switching an aid off. In a conversational system, disuse is quieter and continuous: the human edits the prompt, regenerates, or gives up, absorbing the channel's noise as their own labour. The system's self-assessment is behaving correctly — it is the operator's workload that moves.

### F.4 The calibration debate has a precise boundary, and this study locates it

Large language models are overconfident and miscalibrated; it is one of the era's most reliably reproduced findings (Chhikara 2025, arXiv:2502.11028). The usual consequence drawn is that confidence-based control is unsafe until calibration is solved.

The machine-checked result in §B.4 and its measurement in Figure 4 draw the boundary differently, and this is where the LLM era makes the theorem practically load-bearing rather than merely elegant. A threshold policy reads the **ordering** of confidences; calibration is a claim about their **values**. The ordered-pair count is invariant under any strictly increasing rescaling — measured on the confirmatory record as a spread of exactly **0.000** while a threshold quantity moved **43.6 points**. So:

- **Calibration being unsolved does not invalidate an ordering-based policy.** A practitioner can ship a threshold that discriminates while the calibration question is still open, because discrimination is not what the calibration failure damages.
- **And a calibration objection cannot be used to dismiss an ordering result.** The two are separate questions, and this is the era in which that separation is worth stating, because the literature merges them constantly.

### F.5 Agents make the channel recursive, which multiplies a single typo

An agent runtime is a sequence of commit-or-decline decisions: call the tool or do not, act on the result or re-plan, surface an answer or keep working. Each is a gate, and each consumes text that may have come from a human keyboard, an OCR pass, or the model's own previous turn. **The disturbance is therefore structural at every hop, and the hops compose.**

This is the sense in which the LLM era amplifies rather than merely inherits the phenomenon. A mis-typed request in a single-turn system costs one answer. The same request at the head of an agent chain is consumed by every subsequent step, and the model's own output becomes the next step's input channel.

And the era has already identified the evaluative defect this study is built around, in its own terms. ToolFailBench exists because **aggregate benchmark scores hide where tool use fails**, and gives the reason in a sentence that could serve as the motivation for this whole document: *a model that never calls a needed tool and a model that calls the tool but ignores the result can look similar under final task accuracy* (Soni 2026, arXiv:2607.04686). That is precisely the collapse this study avoids by measuring a gate's conditional behaviour rather than an aggregate — and it says that the fix is not a better score, it is a decomposition.

### F.6 What the era should take from this, stated as practice

Four things, in the order a practitioner would use them.

**Report the decomposition, not the aggregate.** Under a channel that the era has made primary, an aggregate score cannot distinguish damage to committed answers from damage to availability, and those two call for opposite remedies. The measurement is cheap: the same trial record, read at the gate.

**Do not recalibrate a gate in response to input noise.** For this manipulation the gate improved, and the failure was availability. The remedy is throughput — retries, a retrieval step, a reprompt — or accepting the deferral cost knowingly.

**Treat confidence-ordering as usable before calibration is solved**, and stop letting the calibration result carry an argument it does not support. The two questions are separable, and the separation is machine-checked here rather than argued.

**Ask which class a failure belongs to before instrumenting for it.** Silent failures need verification and monitoring; loud failures need capacity. A system instrumented for the wrong class of failure will be well defended where it is not attacked.

### F.7 The boundaries, restated for this framing

The era-specific reading inherits every boundary of the study and adds two.

It is measured on **one instrument and one language**, on synthetic but keystroke-faithful noise, with confidence from a non-autoregressive encoder rather than a frontier chat model's sampled generations. The mechanism proposed — that confidence falls when the surface form is improbable under the intended meaning — predicts that it should hold more widely, but prediction is not measurement, and the direction is the finding.

**The loud-failure result is a claim about the input channel, not about LLMs in general**, and the era's own dominant taxonomy is about a different class. Reading §S.2 as a refutation of the silent-failure literature would be a misreading: it is a partition, and the partition is only useful if both sides are measured.

And the human remains, as §T.1 says, present at two points and measured at neither: this study prices the deferral as a human cost without observing a human pay it. **In the era that made human–model turn-taking the dominant interface, that is the measurement most worth making next.**

## G. Significance across disciplines

### G.1 What the result is, stated so that other fields can use it

The manipulation is narrow on purpose: a single frozen encoder, one language, one synthetic but keystroke-faithful noise process, one typed decision task. What generalises is not the magnitude but the **decomposition**, and the decomposition is what other disciplines have a use for.

Type errors cost accuracy and coverage, and the two costs are worth stating separately because they are different quantities that are easy to conflate. Accuracy falls from **0.8926 to 0.7720**, a loss of **12.1 points** ($p = 4.4 \times 10^{-36}$). Coverage at the fixed threshold $\tau = 0.90$ falls from **0.4479 to 0.2111**, a loss of **23.7 points** — while the H1.3 estimand, the **mean paired fall across units**, is **0.2904** with 95 % CI $[0.2679, 0.3154]$ ($p = 5.0 \times 10^{-5}$). The two coverage figures are not the same measurement: one is the level at a threshold in a given condition, the other is the average within-unit change, and a reader who takes either for the other will misstate the result by five points. Both losses are expected. The unexpected part is the third quantity: the confidence gate's **discriminability rises** under the same manipulation — the within-arm AUC between correct and incorrect trials goes from **0.601 to 0.760** ($p = 2.0 \times 10^{-4}$) — and the share of errors arriving below the gate rises from **61.4 % to 93.5 %**. Errors under this corruption are not quieter; they are **louder**, and they are loudest exactly where the model is least reliable.

### G.2 Signal-detection theory: this is a criterion shift, not a sensitivity loss

The AUC is a nonparametric measure of sensitivity — the probability that a randomly chosen correct trial outranks a randomly chosen incorrect one — and it is the ordinal form of $d'$. Reading the three results in those terms gives a clean statement: **noise moves the operating point (the effective criterion, through a downward shift of the confidence distribution) while leaving the underlying separability not merely intact but improved.** The apparent paradox — accuracy collapsing while discrimination sharpens — dissolves once accuracy and coverage are recognised as **criterion-dependent** quantities (they read a fixed threshold in confidence units) and the AUC as **criterion-free**. A field that reports only accuracy under corruption will therefore read a criterion shift as a sensitivity loss, and will misattribute the remedy: it will try to repair discrimination when the discrimination was never the problem.

### G.3 Human factors and automation: the risk moves from misuse to disuse

The automation literature separates **misuse** — accepting the system's output when it is wrong — from **disuse** — declining to use a system that works. The result here is a **dependability-class** statement about which one this manipulation produces. It produces disuse: the system does not commit to more wrong answers, it commits to far fewer answers at all, and it does so *because* its own confidence collapses on exactly the trials it is getting wrong. Read as a trust calibration, that is the well-behaved direction — the system's self-assessment degrades *with* its performance rather than independently of it. The practical consequence runs against the common remedy: an operator worried about silent errors under noisy input would recalibrate or replace the gate, and **for this corruption there is nothing to repair in the gate**. What needs provisioning is throughput, because the failure is availability, not correctness.

### G.4 Safety engineering: fail-safe rather than fail-operational degradation

Coverage is an **availability** property and correctness-among-committed-answers is a **safety** property. Systems are classified by how they degrade: a *fail-safe* system degrades by ceasing to act, a *fail-operational* system degrades by continuing to act while wrong. This manipulation drives the system along the fail-safe path — and it does so without any of the machinery usually needed to guarantee it, because the degradation is produced by the model's own confidence rather than by an external monitor. That is a useful, narrow, and honest claim: **for orthographic noise, the gate is the safety mechanism and it is not defeated by the noise**. Whether the same holds for noise that corrupts *meaning* rather than *form* is an empirical question this study does not answer, and it is the obvious next one.

### G.5 Reading research: confidence tracks a noisy channel

The stimuli are calibrated against a published human result — the interior-scrambled condition of Rayner and colleagues (2006), **measured under this index rather than quoted from the paper** — applying the recoverability index to that condition returns 0.4480 — and the noise generator is a keyboard-adjacency channel in the tradition of noisy-channel spelling correction. The finding that connects these to the model is that **the model's confidence behaves like a noisy-channel posterior**: it falls when the surface form becomes unlikely under the intended word, which is what makes the errors self-announcing. A reader recovers from a typo by detecting that the surface form is improbable; the instrument here appears to do the same thing through its confidence. That is a mechanism-level correspondence, not an analogy, and it is testable: a noise process whose corruptions are *plausible* under the channel should produce errors that are **not** self-announcing, and the AUC should then fail to rise.

### G.6 Methodology: choose estimands that cannot inherit an instrument's calibration

The design decision that made the third result usable was made before the run and is transferable. The instrument's own library warns, unprompted, that this checkpoint's temperatures are invalid and that affected confidences are uncalibrated. An estimand that bounds a rate **at an absolute threshold** inherits that warning; an estimand that reads only the **order** of confidences cannot. Measured on the confirmatory record, this is not a subtlety — rescaling every confidence by a family of strictly increasing maps leaves the AUC with a spread of exactly **0.000** while moving coverage at the fixed threshold by **43.6 percentage points**. The general principle is stated in the formal framework and machine-checked there; its use is not specific to this study. **Wherever a measurement device's calibration is in question, the ordinal estimand is the one that survives the doubt** — and choosing it in advance is what makes the resulting claim robust to a caveat that would otherwise have to be argued away afterwards.

### G.7 What this does not license

Five boundaries, stated because each of them is a way the result could be over-read.

It does **not** show that confidence is calibrated, comparable across models, or comparable across tasks. It shows that the *ordering* is stable under this corruption, which is weaker and is all the claim needs.

It does **not** show that any deployed gate is safe. The gate here is a fixed threshold on a single instrument's confidence; a deployed system's gate is a composition, and composition is where these guarantees are usually lost.

It does **not** show that the direction generalises beyond orthographic noise. Noise that corrupts meaning rather than form — a plausible substitution, a homophone, an adversarial token — is the case where the mechanism identified in §F.5 predicts the opposite result, and predicting the opposite result is the point of identifying a mechanism.

It does **not** show that the model "knows when it is uncertain" in any reflective sense. The measurement is compatible with a purely distributional account of confidence, and nothing here distinguishes the two.

It does **not** establish that silent refusal is a lesser harm than a confident error out of context. That is a judgement about a deployment, and the study's contribution is to establish **which** of the two failure modes this manipulation produces, not which one a given application should prefer.

## H. Pre-registration: the frozen checklist

The values below are read from the protocol's own checklist rather than restated, so this table cannot claim a frozen value the protocol does not carry.

| Item | Requirement | State |
|---|---|---|
| 1 | English only; no script factor in confirmatory tests | **FIXED** |
| 2 | Typo classes and λ rates fixed | **FIXED — λ_lo = 0.05, λ_mid = 0.18** |
| 3 | Generator seed policy | **FIXED** |
| 4 | Model ID + commit + SHA256 | **FIXED** |
| 5 | **$Q_0$ frozen** | **FIXED — as `intent` alone** |
| 6 | Confidence rule frozen | **FIXED** |
| 7 | τ ∈ {0.80, 0.90}, ε = 0.05 | **FIXED** |
| 8 | Dev/test split by item | **FIXED** |
| 9 | Primary endpoints H1.1–H1.3; confirmatory family = exactly these three, Holm, $\alpha=0.05$ | **FIXED** |
| 10 | FAILURES policy | **FIXED** |
| 11 | No confirmatory training | **FIXED** |
| 12 | Cross-script claims reserved for Phase II | **FIXED** |
| — | **Item bank** | **ACCEPTED** (932 items; consistency measured, no human pass) |
| — | **N_item** | **FROZEN: N_test = 652** |


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
