# Supplementary information

**LIMEN Phase I — orthographic channels and input noise as structural disturbances in human–model interaction**

*Supplementary information provided by the authors; not edited.*

---

## Contents

**A.** Background and design
**B.** Formal framework
**C.** Stimuli, noise model and instrument
**D.** Analysis, power and results
**E.** Interpretation, limitations and reproduction
**F.** Pre-registration: the frozen checklist
**G.** References

---

## A. Background and design

### A.1 Background

Typed decision-making is now routine where a language model is asked a question whose answer must be trusted without inspection: a classifier routes a request, a gate admits or defers, a system acts. The surface form of such a request is produced by a human on a keyboard, and keyboards produce errors. The question this study asks is not whether typographic noise degrades performance — that is settled — but **how the degradation distributes itself across a confidence gate**, because that distribution is what determines whether an operator can see the damage.

A widely repeated premise holds that the dangerous failure is the *silent* one: that noise pushes wrong answers *past* a confidence threshold, so they arrive wearing the same confidence as correct ones and are never caught. If that premise is true, then a gate calibrated on clean text is a liability under noise, and the risk calculus for every deployed gate changes. If it is false — if the errors noise causes arrive *below* the gate — then the gate continues to filter them, and the damage lands somewhere quite different: in the answers the system declines to give.

The distinction matters because the two failures call for opposite remedies. Silent errors demand *recalibration*: a stricter threshold, a different confidence estimator, or abstention that does not rely on confidence at all. Loud errors demand *coverage*: the model is not wrong more often in the answers it commits to, it simply commits less often, and the remedy is throughput — more attempts, a retrieval step, a reprompt — not a different threshold. Treating one as the other wastes the remedy and leaves the real failure in place.

### A.2 The question, stated so that it can fail

> Does keystroke-faithful typographic noise, applied to a typed-decision task, change **the error rate among the trials a confidence gate admits**?

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

> **This proposition refuted the protocol.** The protocol originally asserted the *opposite* — that raising the threshold could only increase the silent-error count. The kernel proved otherwise, and the refutation is preserved in the development as `protocol_said_nondecreasing_is_FALSE` so that the error is visible rather than quietly corrected. The direction matters because it is the formal reason the original H1.2 could not hold: **a fixed-threshold silent-error rate cannot rise under a manipulation that deflates confidence**, since deflation moves trials out of the accepted set entirely.

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

The index is anchored on a **published human result** rather than on a threshold chosen for convenience: Rayner and colleagues' interior-scrambled condition (2006), whose readers recovered the intended word 0.4480 of the time — the harsher of the two variants they report, and therefore a floor for human tolerance. The levels are then determined by rule: **$\lambda_{\mathrm{lo}} = 0.05$** is the smallest grid point whose mean recoverability clears the anchor, and **$\lambda_{\mathrm{mid}} = 0.18$** is the largest point that still clears it. The margin at $\lambda_{\mathrm{lo}}$ is $+0.0728$.

Two earlier instruments were measured and **rejected**, and the reason is quantitative. An **absolute three-level rating** (recoverable / workable / not recoverable) never emitted its lowest category in 120 sentences and reached weighted κ of only 0.073 and 0.137 against a 0.60 floor: it could not express what it was for. **Pairwise comparison against clean text** saturated the other way — the probability that a perturbed sentence was judged harder was 0.90–1.00 at *every* level including the mildest, so it detected the presence of corruption but not its degree. Neither failure is a rater failure; both are instrument failures, and the anchored index is used precisely because it is monotone over the range that matters.

### C.4 The instrument

The instrument is a non-autoregressive encoder under a permissive licence, **pinned by revision digest and by per-file SHA-256**, with an integrity guard that re-verifies the pin on every run. It was never trained: the study measures a fixed device, and holding parameters frozen is what makes a contrast between noise levels a statement about the manipulation rather than about the model's drift. What the pin does **not** guarantee is that the instrument's confidence is calibrated — the library warns, unprompted, that the checkpoint ships temperatures outside its valid range and that affected confidences are substituted with a constant and are uncalibrated. Two of the three dependent variables are functions of confidence, so the warning was bounded by measurement rather than trusted: on the confirmatory run **0 of 13,692 rows carry the substituted constant**, and the confidence values span 0.2652–1.0000 over 5,026 distinct values. Because a single sample cannot make a guarantee, the observation is now carried as a **checked invariant** that fails on any trial file containing the constant. Reading a warning is not the same as acting on one.

# Appendix D — Analysis, Power and Results

## 1 Estimators

The design is paired at the **unit** level: a unit is an item crossed with a seed, and it carries exactly one clean and one noisy observation, each with its own confidence $c$ and correctness $y$. Let $u = 1, \dots, n$ enumerate the units, and let a signed statistic be any function $T$ of the paired sample.

**Definition (exact paired permutation test).** Under the null that the manipulation does not change the joint distribution of $(c, y)$ within a unit, the two arm labels are exchangeable, so the permutation distribution of $T$ is generated by independently swapping each unit's two observations:

$$
T^* \;=\; T\Bigl(\{(X_u^{(\sigma_u)}, Y_u^{(\sigma_u)})\}_{u=1}^n\Bigr), \qquad \sigma_u \overset{\text{i.i.d.}}{\sim} \mathrm{Bernoulli}(0.5),
\tag{1}
$$

where $(X_u^{(1)}, Y_u^{(1)}) = (X_u, Y_u)$ and $(X_u^{(0)}, Y_u^{(0)}) = (Y_u, X_u)$. The two-sided $p$-value is

$$
p \;=\; \frac{1 + \sum_{m=1}^{M} \mathbb{1}\{|T^*_m| \ge |T_{\mathrm{obs}}|\}}{M + 1},
\tag{2}
$$

with $T^*_m$ drawn from the permutation distribution and $M = 2^n$ (the exact enumeration) in our case.

This test is **exact** under the exchangeability assumption. Within each unit, the assignment of the two observations to arms is exchangeable under the null: $(X_u, Y_u) \stackrel{d}{=} (Y_u, X_u)$ for all $u$, and units are mutually independent. Nothing else is assumed. The test requires no distributional form and no asymptotics; it is the limiting case of a random-intercept model carrying only the item effect. The $+1$ corrections in both numerator and denominator are the standard correction that makes the reported $p$ a valid test rather than a lower bound.

**Definition (the discrimination estimand).** With $C$ the confidences of correct trials and $E$ those of incorrect trials *within one arm*,

$$
\mathrm{AUC}(\lambda) \;=\; \frac{1}{|C| \cdot |E|} \sum_{c \in C} \sum_{e \in E} \mathbb{1}(c > e) + \tfrac{1}{2}\,\mathbb{1}(c = e),
\tag{3}
$$

and the tested contrast is $T = \mathrm{AUC}(\lambda_{\mathrm{mid}}) - \mathrm{AUC}(0)$. Because $\mathrm{AUC}$ is a within-unit rank statistic, the same exchangeability argument licenses the exact paired permutation for $T$, and no second inferential framework is introduced. The one-sided alternative for H1.2′ is that $T > 0$: the gate's discriminability rises under noise.

**One estimand is deliberately excluded from the family.** The conditional error among admitted trials, $\mathrm{CondErr}@\tau = \Pr(y = 0 \mid c \ge \tau)$, has a denominator that **changes with the condition** — the admitted set is 121 items clean against 61 under noise, with an intersection of only 51 — so the within-item pairing that the permutation test relies on does not exist for it. It is reported in §D.4 and is **not** a member of the confirmatory family. Naming an estimator the code does not implement is how a pre-registration and an analysis drift apart without anyone noticing.

## 2 The family and direction enforcement

The confirmatory family comprises exactly three hypotheses, corrected by the Holm sequentially rejective procedure at family-wise $\alpha = 0.05$: the smallest $p$-value is compared against $0.05/3 = 0.0167$, the next against $0.05/2 = 0.0250$, and the last against $0.05$. Holm requires no independence assumption among the tests and is uniformly more powerful than Bonferroni.

The three hypotheses and their predicted directions are:

- **H1.1**: accuracy falls at $\lambda_{\mathrm{mid}} = 0.18$ (exact McNemar on paired discordant pairs, with deferred trials counted as errors);
- **H1.2′**: within-arm AUC contrast rises (gate discriminability increases);
- **H1.3**: coverage at $\varepsilon = 0.05$ falls.

**Direction is part of the hypothesis.** Each hypothesis carries its predicted sign, and the Holm input is the two-sided $p$-value **only when the observed movement agrees with the predicted direction**. A two-sided $p$-value is blind to direction: it reports the magnitude of deviation from the null, and a large effect in the *opposite* direction is indistinguishable from support under a naive reading. Under the direction rule, such a movement is recorded as a **direction violation** — a finding in its own right — and is **never counted as evidence** for the hypothesis.

This rule is not a technicality; it is what converted a genuine result into a correction. The original fixed-threshold silent-error hypothesis moved significantly in the *opposite* direction: silent error fell rather than rose. Without the direction rule, the two-sided $p$-value of $5.00 \times 10^{-5}$ would have been entered into Holm as support for a hypothesis that the data had actually refuted. The direction rule correctly classified it as a refutation, which motivated the replacement hypothesis H1.2′.

## 3 Power

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

## 4 Results

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

### 4.1 What the pre-run predicted

| Predicted on dev, before the seal | Confirmatory outcome |
|---|---|
| $\pi_d \approx 0.2036$ | 0.19 ($b + c = 378$ over 1,956 units) |
| Minimum detectable effect 5.41 points | Accuracy contrast ≈ 12.1 points |
| H1.2′ contrast ≈ $+0.1201$ | **$+0.1587$** |
| The original H1.2 falls | **$-0.0266$** |
| No confidence contamination | **0 of 13,692 rows** |

Both prediction classes held. The replacement hypothesis replicated, and the refuted hypothesis reproduced its refutation exactly.

### 4.2 Scientific significance

For this manipulation the silent-error premise **fails, and it fails in a specific way**. Typo noise costs about twelve accuracy points and twenty-nine coverage points, yet the gate's discriminability *rises* — from 0.601 to 0.760 — and the share of errors the gate rejects rises from 61.4 % to 93.5 %. The damage therefore concentrates in **what the model declines to answer**, not in what it confidently gets wrong. Two consequences follow. First, confidence remains a usable control signal under orthographic noise, so the common remedy for a feared silent-error problem — recalibrating or replacing the gate — addresses a failure that does not occur here. Second, the real failure is a **coverage** failure rather than a correctness one, and coverage is remedied by throughput rather than by thresholds.

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

## E2. Figures

**Figure 1. The three pre-registered hypotheses across the noise grid.**

![Figure 1](figures/fig1_stage2_hypotheses.png)

**Typo noise costs accuracy and coverage while making the confidence gate MORE discriminative, not less.** Each panel is one pre-registered hypothesis, tested with the exact paired permutation of the protocol and Holm-corrected across the three-hypothesis family; all three were confirmed with no direction violations. (a) Accuracy falls by 12.1 percentage points from lambda = 0 to lambda_mid (H1.1, p = 4.4e-36). (b) The within-arm AUC between correct and incorrect trials RISES from 0.601 to 0.760 (H1.2', p = 2.0e-04) -- the gate separates right from wrong more sharply under noise. (c) Coverage at tau = 0.9 falls by 23.7 points (H1.3, p = 5.0e-05), so far fewer trials are answered at all. All panels use the **test split** of the pre-registered window: 652 items x 3 frozen noise seeds = 13,692 trial records from the pinned instrument, 0 failures. The confidence rule is `answer if c >= tau else defer`. Dashed vertical lines mark the two calibrated noise levels, lambda_lo = 0.05 and lambda_mid = 0.18. Every plotted value is read from `data/processed/stage2_lambda_summary.csv`, which `scripts/build_stage2_figures.py` derives from `measurement/out/confirm_trials.jsonl`. No point is interpolated or modelled.

**Figure 2. Where the errors go: the gate rejects most of what noise breaks.**

![Figure 2](figures/fig2_stage2_error_destination.png)

**The errors noise creates arrive below the gate: they are loud, not silent.** Panel (a) decomposes every error at each noise level into the share the gate rejects and the share it admits. Under noise the rejected share rises from 61.4% to 93.5%, so the gate catches most of what noise breaks. Panel (b) shows the two error measures diverging: the conditional error among admitted trials is flat (0.092 to 0.070), while the all-trial silent error FALLS (0.041 to 0.015). A fixed-threshold silent-error rate cannot rise under a manipulation that deflates confidence, which is why the original H1.2 was refuted and replaced by H1.2'. All panels use the **test split** of the pre-registered window: 652 items x 3 frozen noise seeds = 13,692 trial records from the pinned instrument, 0 failures. The confidence rule is `answer if c >= tau else defer`. Dashed vertical lines mark the two calibrated noise levels, lambda_lo = 0.05 and lambda_mid = 0.18. Every plotted value is read from `data/processed/stage2_lambda_summary.csv`, which `scripts/build_stage2_figures.py` derives from `measurement/out/confirm_trials.jsonl`. No point is interpolated or modelled.

**Figure 3. Why the gate separates better under noise.**

![Figure 3](figures/fig3_stage2_gate_separation.png)

**The gate does not merely shift down with noise -- it separates correct from incorrect trials more sharply.** Median confidence for correct and for incorrect trials, at the clean level (left) and at lambda_mid (right); the double arrow is the separation between them. Correct-trial confidence falls from 0.888 to 0.783, but incorrect-trial confidence falls more than twice as far, from 0.784 to 0.549. The separation therefore widens from +0.103 to +0.234, and the corresponding within-arm AUC rises from 0.601 to 0.760. The estimand reads only the ORDER of confidences, so it is invariant to any monotone rescaling of the instrument's confidence scale -- machine-checked in the formalization repository. All panels use the **test split** of the pre-registered window: 652 items x 3 frozen noise seeds = 13,692 trial records from the pinned instrument, 0 failures. The confidence rule is `answer if c >= tau else defer`. Dashed vertical lines mark the two calibrated noise levels, lambda_lo = 0.05 and lambda_mid = 0.18. Every plotted value is read from `data/processed/stage2_lambda_summary.csv`, which `scripts/build_stage2_figures.py` derives from `measurement/out/confirm_trials.jsonl`. No point is interpolated or modelled.


## F. Pre-registration: the frozen checklist

The values below are read from the protocol's own checklist rather than restated, so this table cannot claim a frozen value the protocol does not carry.

| Item | Requirement | State |
|---|---|---|


## G. References

**Provenance of this list.** Every entry was taken from a source rather than from memory: the works in J.1 are recorded verbatim in this project's own files (the amendment and validation documents that used them), and the two canonical methods references in J.2 were each verified against a published record at the time of writing, with their identifiers given so a reader can check them. No entry here was written from recollection.

### G.1 Cited works

Brill, E., & Moore, R. C. (2000). An improved error model for noisy channel spelling correction. *Proceedings of the 38th Annual Meeting of the Association for Computational Linguistics*, 286–293. *(error model for the recoverability index)*

Jurafsky, D., & Martin, J. H. *Speech and Language Processing* (3rd ed. draft), appendix B, “Spelling Correction and the Noisy Channel”. *(standard statement of the channel formulation)*

Kernighan, M. D., Church, K. W., & Gale, W. A. (1990). A spelling correction program based on a noisy channel model. *Proceedings of the 13th International Conference on Computational Linguistics (COLING)*, 205–210. *(the channel model used by the recoverability index)*

Rayner, K., White, S. J., Johnson, R. L., & Liversedge, S. P. (2006). Raeding wrods with jubmled lettres: There is a cost. *Psychological Science*, 17(3), 192–193. *(the human readability anchor; the interior-scrambled variant at 0.4480 is the floor against which `λ_lo` and `λ_mid` are selected)*

### G.2 Methods references, verified against a published record

Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics*, 6(2), 65–70. doi:10.2307/4615733. *(the family-wise correction applied to the three-hypothesis family)*

McNemar, Q. (1947). Note on the sampling error of the difference between correlated proportions or percentages. *Psychometrika*, 12(2), 153–157. doi:10.1007/BF02295996. *(the paired test the power calculation is built on)*

### J.3 Software, instrument and data

The measurement instrument is an openly licensed, non-autoregressive encoder pinned by revision digest and by per-file SHA-256; the pin is re-verified on every run, and the model was never trained. The exact revision and the licence are recorded in the project's pin configuration and in the protocol's instrument section, and are the authoritative statement of what was measured.

Formalization is carried out in **Lean 4** (core-only, no external mathematical library), with every theorem checked at the kernel level. Figures are produced with **matplotlib**; the PDF deliverables are rendered by a headless Chromium print of the HTML sources, so the raster and vector editions come from one layout engine.

### J.4 Data and code availability

The pre-registration record, the analysis code, the stimulus generator, the item bank, the guard suite and the formalization are released together. The confirmatory trial record is regenerated by one command from the pinned instrument over the pre-built test bank; the per-level summary used by every figure and by Table H1 is derived from it by script, so no reported number depends on a hand-entered value.
