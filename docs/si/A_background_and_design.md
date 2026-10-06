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
