# From Neural Scaling to Interaction Channels

**A systematic formulation of the Shannon Scaling Law, its limits, and a keyboard-bounded research program on human–LLM noise**

| | |
|---|---|
| **Document type** | Research synthesis and problem formulation |
| **Status** | Reorganization of working notes into a single argument. Not an empirical study. |
| **Epistemic labels** | *Established* (published result) · *Reported* (claim carried from the working notes or a secondary summary, not re-analyzed here) · *Proposition* (open) · *Constraint* (methodological rule) |

---

## Abstract

Neural scaling laws began as empirical power laws relating loss to parameters, data, and compute. Two later results change what those laws can mean. Under strong representation superposition, loss scales inversely with model dimension for geometric reasons that do not depend on the fine structure of the data-frequency distribution. Separately, the Shannon Scaling Law (SSL) models training as transmission over a noisy channel and thereby represents non-monotonic failures—catastrophic overtraining and quantization-induced degradation—that monotonic power laws cannot.

The working notes ask whether noise introduced when humans interact with a deployed model, and in particular when they type an intention on a keyboard, belongs in that same capacity formula. This document argues that the question is well posed only after four distinctions are enforced.

1. Training noise, supervision noise, and deployment-time input noise are different channels. SSL currently formalizes the first. Human-Bounded Intelligence formalizes a floor on the second. Neither result already contains the third.
2. “Interaction noise” is not yet a variable. It becomes one only if its physical, cognitive, and contextual layers are separable, if the resulting term is identifiable in the SSL denominator, and if an intervention changes it without changing the confounders that usually travel with it.
3. The keyboard channel is the narrow object on which those tests can actually be run. QWERTY geometry, keystroke timing, and intent ambiguity are different mechanisms; prompt-level perturbation injection makes the first experimentally assignable.
4. Keyboard noise need not enter SSL as an additive power. Reported token-survival and thinking-budget effects are equally consistent with an erasure channel whose damage can be partly bought back with inference compute. Which functional form is correct is itself a result, not a modeling preference.

Six general propositions and three keyboard propositions are stated below. Six constraints define what would count as solving them. A conditional reading of the scientific stakes follows: a partial, identified solution would found a research program on human–machine channel capacity; a relabeling of existing loss curves would not. The document closes with a structured critique of the SSL paper as a base that cannot be extended by citation alone.

---

## 1. The argument in one page

The notes read as a sequence of topics. They are one argument, nested as follows.

```text
Monotonic scaling laws          describe loss, do not explain it,
                                and cannot represent U-shaped failure
        │
        ├─ Superposition        geometric mechanism for the monotonic regime
        │
        └─ Shannon Scaling Law  information-theoretic mechanism for the
                                non-monotonic regime, with an assumed
                                three-term noise decomposition
                    │
                    │  meets
                    ▼
        Human-Bounded Intelligence
                                human supervision that is not sufficient
                                for a latent target induces a strictly
                                positive error floor
                    │
                    │  the meeting is not yet a formula
                    ▼
        Interaction noise       too broad to be a term: nonstationary,
                                reflexive, multimodal, intention-latent
                    │
                    │  restrict the object
                    ▼
        Keyboard channel        geometrically parameterized, partly
                                observable in timing, randomizable
                    │
                    ▼
        Propositions A–C        separability, scaling exponent, precoding
                    │
                    │  admitted only if
                    ▼
        Six constraints         separable, identifiable, intervenable,
                                extrapolable — and not a new name for an old curve
```

The thesis that this structure supports:

> Do not insert a human-noise term into the Shannon Scaling Law until keyboard-channel noise has been shown to be separable, identifiable, intervenable, and extrapolable. The scientific object is that test, not the enlarged formula.

Everything after this section is a specification of one layer of the diagram.

---

## 2. What neural scaling laws actually state

### 2.1 The empirical core

*Established.* Kaplan et al. (2020) showed that, over a wide operating range, the cross-entropy loss of autoregressive language models falls as a power law in parameter count $N$, dataset size $D$, and training compute. The practical content of that observation is predictability: loss at a larger scale can be forecast from smaller runs, rather than discovered only after the run.

Hoffmann et al. (2022), the Chinchilla study, changed the allocation rule inside that predictability. For a fixed compute budget $C \approx 6ND$, loss is minimized when parameters and tokens are scaled together, not when almost all new compute is spent on parameters. The compute-optimal frontier is a joint $(N, D)$ schedule.

What these laws do **not** state:

- They do not identify a mechanism. A stable exponent is not a cause.
- They are monotonic in the fitted regime. They have no internal degree of freedom that turns further tokens or further parameters into *worse* loss.
- They do not allocate any quantity other than pretraining $N$, $D$, and $C$. Inference-time compute, data redundancy, architectural inductive bias, and human input at deployment are outside the original variables.

### 2.2 Why “larger is better” needed a mechanism

*Established.* Liu, Liu, and Gore (2025; NeurIPS 2025 Best Paper Runner-up) propose representation superposition as a contributor to neural scaling. A model in superposition represents more features than it has dimensions. Features packed into a lower-dimensional space overlap; those geometric overlaps are a source of loss.

Their result splits by regime:

| Regime | When loss follows a power law in dimension |
|---|---|
| Weak superposition | Only if feature frequencies themselves are power-law distributed |
| Strong superposition | Generically. Loss scales inversely with dimension, $L \propto 1/m$, across a broad class of frequency distributions |

Open-weight LLMs, on their measurements, sit in the strong-superposition regime, and the Chinchilla parameter law is consistent with inverse-dimension scaling once parameter count is converted to width. The mechanism is geometric interference, not a fact about any one dataset.

Two limits of this explanation matter later. It accounts for a *monotonic* improvement with dimension. It does not, by itself, produce a U-shaped curve in tokens, quantization, or interaction length. And it is a claim about representation geometry during training and evaluation of the model, not about noise injected by a human at inference time.

The working notes describe this paper as the NeurIPS 2025 Best Paper. The published designation is **Best Paper Runner-up**. The substantive claim is unchanged; the award label should not be inflated.

---

## 3. The Shannon Scaling Law

### 3.1 What monotonic laws cannot say

*Established.* Ouyang et al. (2026; arXiv:2605.23901, accepted at ICML 2026) start from failures that power laws fit only by changing the story after the fact:

- **Catastrophic overtraining.** Additional pretraining can *hurt* downstream supervised fine-tuning.
- **Quantization-induced degradation.** Aggressive post-training quantization can collapse larger models rather than merely shave a constant off their quality.

Both are non-monotonic in a resource that classical scaling treats as beneficial. A law with only a decreasing power plus a floor cannot put a minimum in the interior of the resource axis.

### 3.2 The channel ansatz

*Established as a modeling choice; not derived from a theorem that applies literally to SGD.*

The Shannon–Hartley capacity of a band-limited channel with additive white Gaussian noise is

$$
C = B \log_2 \!\left(1 + \frac{S}{\mathcal{N}}\right),
$$

with bandwidth $B$, signal power $S$, and noise power $\mathcal{N}$. SSL maps the symbols onto training as follows.

| Channel quantity | Training quantity | Parametric form |
|---|---|---|
| Bandwidth $B$ | Parameter count $N$ | $B \propto N^{\alpha}$ |
| Signal power $S$ | Token count $D$ | $S \propto D^{\beta}$ |
| Noise $\mathcal{N}$ | Three fitted contributions | see below |

The three noise contributions, in the paper’s own decomposition, are:

| Term | Name in SSL | Intended content |
|---|---|---|
| $d\, D^{\delta}$ | Data-induced noise | Typos, ambiguity, and contradiction already in the corpus. Sensitivity grows with $D$. |
| $c\, (DN)^{\gamma}$ | Model-interaction noise | Training as a dynamic denoising process: a randomly initialized model is high-noise and low-capacity, and is progressively denoised. The term couples tokens and parameters. |
| $e$ | Irreducible noise | A constant standing in for architectural limits and residual system entropy. Analogous in role, not in derivation, to the irreducible-loss term of Chinchilla-style laws. |

The resulting capacity is

$$
C_{\mathrm{LLM}}(N, D)
  = a N^{\alpha}
    \log_2\!\left(
      1 + \frac{b D^{\beta}}{c\,(DN)^{\gamma} + d\, D^{\delta} + e}
    \right),
\tag{SSL}
$$

with positive fitted constants $a,b,c,d,e,\alpha,\beta,\gamma,\delta$. Test loss is **set** equal to the reciprocal,

$$
\mathcal{L}(N, D) = \frac{1}{C_{\mathrm{LLM}}(N, D)}.
\tag{L}
$$

Equation (L) is an ansatz. The paper proposes it; it does not derive it from a coding theorem or from a learning-theoretic excess-risk bound. The working notes are right to mark this as a heuristic link. Capacity and loss move in opposite directions under (L), so any regime in which the denominator grows faster than the numerator produces a U-shape in $\mathcal{L}$. That qualitative mechanism is the paper’s real contribution. The identification of $\mathcal{L}$ with $1/C$ is a choice of gauge.

A six-parameter simplification, obtained by pruning constants that consistently fit near negligible values, is

$$
C_{\mathrm{Simpl}}
  = a N^{\alpha}
    \log_2\!\left(
      1 + \frac{D^{\beta}}{c\,(DN)^{\gamma} + D^{\delta}}
    \right).
\tag{SSL-s}
$$

The paper reports that (SSL-s) retains nearly the in-sample fit of the nine-parameter form (average $R^2$ about $0.954$ versus about $0.966$).

### 3.3 What the exponents are used to mean

*Established as fitted regularities inside the paper’s experiments, not as universal constants.*

Two comparisons organize the discussion:

1. **Along tokens.** The data-noise exponent exceeds the signal exponent, $\delta > \beta$, across the reported scenarios. Under (SSL) and (L), U-shaped degradation along the token axis is then intrinsic to the fitted noise dynamics, not an extra external shock that must be added by hand.
2. **Along parameters.** The relation between the bandwidth exponent $\alpha$ and the model-noise exponent $\gamma$ crosses with signal-to-noise ratio. In high-SNR regimes (stable pretraining, mild fine-tuning), $\alpha > \gamma$: extra parameters buy more capacity than they import noise. In low-SNR regimes (aggressive fine-tuning step sizes), the inequality flips to $\gamma > \alpha$: making the model larger amplifies the perturbed channel faster than it widens it.

The second comparison is the paper’s account of “scaling hurts.” The first is its account of “training longer hurts.” Neither comparison is a theorem about every architecture or every data distribution. Both are readings of fitted exponents under a specific ansatz.

### 3.4 Empirical scope, stated tightly

*Established.*

| Item | What was actually done |
|---|---|
| Models | Pythia, 160M–12B; OLMo2, 1B–32B |
| Perturbations | Gaussian weight noise (about 10–40 dB); GPTQ quantization (about 2–4 bit); supervised fine-tuning learning rates from $10^{-5}$ to $10^{-3}$ |
| Tasks under SFT | GSM8K (math), SocialIQA (QA), StarCoder (code), in addition to pretraining loss |
| In-sample fit | High $R^2$ on the fitted regimes, including values reported up to about $0.99$ on pretraining and about $0.98$ average under quantization |
| Extrapolation | Fit on Pythia models $\le 6.9$B and $\le 180$B tokens; predict the held-out 12B model out to 307B tokens at pooled $R^2 = 0.847$. Monotonic baselines collapse on the same split |

The extrapolation factor in parameters is about $12/6.9 \approx 1.7$, and the token extrapolation from 180B to 307B is of the same order. That is a real out-of-sample test. It is not a test at frontier scale.

A correction to the working notes: they describe the fit target as WikiText-2 test loss alone, with no downstream check. The paper’s SFT section does evaluate math, QA, and code. The critique that survives is narrower and is stated in Section 8: those tasks are still short, closed evaluations under weight or optimizer perturbations. They are not open-ended generation quality, multi-turn dialogue, or human input noise.

### 3.5 What SSL explains, in one sentence

Under the ansatz (SSL)–(L), performance improves with scale only while signal outruns noise. Past that point, further tokens or further parameters in a noisy regime reduce capacity. Monotonic laws have no such point. That is the increment over Kaplan and Chinchilla.

---

## 4. Scaling is no longer only a story about $N$

The notes place four neighboring lines of work beside SSL. They are not part of the interaction-noise argument. They matter only because they show that “scale the parameters” is already an incomplete design space, so an interaction term would be a further axis, not a decoration of the only axis.

| Line | Claim, as published or as stated in the notes | Status |
|---|---|---|
| Parallel scaling (ParScale; Chen et al., 2025, arXiv:2505.10475) | $P$ diverse, learnable input transformations, parallel forwards, and learned aggregation. $P$ streams behave like an $\mathcal{O}(\log P)$ parameter increase, with up to $22\times$ less memory growth and $6\times$ less latency growth than matching parameter scaling, in the reported comparison. | Established |
| Recursive inference scaling (RINS; Alabdulmohsin and Zhai, 2025, arXiv:2502.07503) | A specific recursive depth, compute-matched, improves asymptotic level and scaling exponent, including a no-regret adapter regime in which the pretrained model is better even if recursion is not used at inference. | Established |
| Data density | High redundancy is reported to slow scaling (sub-scaling). More tokens are not more information. | Reported direction; no single law is adopted here |
| Architecture versus parameters | A position, called in the notes a “second scaling law,” that wisdom depends more on architecture than on parameter count. | A position, not a named theorem in this document |
| Neuroscience | Phenomenological renormalization-group analyses of large neural-population recordings are cited in the notes as evidence of cross-modal scale-free structure, suggesting that biological population codes may obey scaling relations of their own. | Reported direction; not used below |

SSL’s own slogan, once the exponents are taken seriously, is the same shift: prefer signal-to-noise ratio and information density over brute-force scale. ParScale and RINS are existence proofs that some of the relevant “scale” is parallel compute and recursive depth. They do not address a human at a keyboard.

---

## 5. Where human noise would have to enter

### 5.1 Two published objects that are easy to conflate

**Object A — training-channel noise (SSL).**  
Data-induced, model-interaction, and irreducible terms in the denominator of (SSL). All three are stories about how a corpus and an optimizer write a set of weights. None of them is a story about a person typing a prompt after the weights are frozen.

**Object B — supervision-channel insufficiency (Human-Bounded Intelligence).**  
Rodriguez Dominguez (2026, arXiv:2602.23446) argues that if every piece of information about a latent evaluation target $Y^\ast$ passes through a human supervision channel that is not sufficient for $Y^\ast$, then any learner dominated by that channel has a strictly positive excess-risk floor:

$$
\liminf_{n \to \infty} \mathcal{E}^\ast(f_{\hat\theta_n}) \ge \gamma_H > 0.
$$

The floor $\gamma_H$ depends on the channel, not on capacity, sample size, or compute. The paper decomposes the human-side deficit into three structural sources, and obtains the same qualitative bound from six formalisms (operator theory, PAC-Bayes, information theory, causal inference, category theory, and a game-theoretic treatment of reinforcement learning from human feedback):

| Source | Content |
|---|---|
| Annotation noise | The label or demonstration is a noisy function of the intended target |
| Preference distortion | The human’s ranking is not the target ranking |
| Semantic compression | Natural language does not have the bandwidth to pass the target |

Auxiliary non-human signals—retrieval, program execution, tool returns, simulators—can lower or remove the floor when they restore information about $Y^\ast$ that the human channel never carried. The notes call this “folding” the floor. The theorem applies when human supervision is the dominating source of information about $Y^\ast$. It is not a theorem about typos in a user prompt.

### 5.2 The junction, stated without a new symbol

SSL and Human-Bounded Intelligence meet at one question and only one:

> Is there a human contribution, at training time or at deployment time, that leaves a remainder in the SSL denominator which cannot be driven to zero by $N$ and $D$, and is that remainder the same object as $\gamma_H$, the same object as the constant $e$, or a third object?

Until that identity is shown, there are three noise vocabularies in play, not one.

| Vocabulary | When it is injected | What removes it, if anything |
|---|---|---|
| SSL data / model / irreducible | During training, in the corpus or the optimization trajectory | More scale only while SNR rises; $e$ is defined not to be removed |
| HBI supervision floor | Whenever the learning signal about $Y^\ast$ is human and insufficient | Auxiliary channels that carry independent information about $Y^\ast$; not scale |
| Deployment interaction noise | After training, in the human’s input to a frozen or lightly adapted model | Unknown. Candidates: precoding, inference compute, context reset. Not known to be $e$ |

The notes’ “fourth component” is a proposal to add the third row to the first row’s formula. Section 6 is the argument that the proposal is not yet legal. Section 7 is the only slice of the third row that is currently a laboratory object.

### 5.3 Why classical channel assumptions do not transfer for free

Shannon–Hartley, as used to motivate (SSL), assumes a linear channel, additive noise of a fixed distribution, stationarity, and no memory. LLM training already violates these; the paper’s use of the formula is an analogy whose justification is predictive, not axiomatic. Human interaction violates them a second time, and differently:

- The human is nonstationary (fatigue, learning, strategy changes).
- The channel has feedback. The model’s output changes the next human input.
- The “encoder” is strategic, not a fixed conditional distribution $P(x \mid \text{intent})$.
- Intention is latent. The clean symbol is not observed, so noise cannot be defined as a residual against a known symbol without an extra measurement model.

A feedback channel, a nonstationary channel, or a control loop may be the right formalism. A memoryless AWGN formula with one extra positive term is a special case that has to be earned.

---

## 6. Six propositions, and the rule that governs all of them

### 6.1 Layer I — theory

**Proposition 1 (independence).**  
Is deployment-time human interaction noise absorbed by one of SSL’s three terms, or does it require a fourth term? Absorption is the default. A fourth term is permitted only if it makes a prediction that the three-term denominator cannot make.

**Proposition 2 (the floor inside the formula).**  
If a human channel imposes $\gamma_H > 0$, how does that floor appear in (SSL)? The notes’ candidate reading is that some noise contribution in the denominator is bounded below by a positive constant, so $C_{\mathrm{LLM}}$ cannot diverge as $N, D \to \infty$, and therefore $\mathcal{L}$ cannot fall to zero under (L). The open mathematical question is whether that constant is $e$, a piece of $e$, or a distinct lower bound with a different dependence on the supervision channel. A further requirement, easy to miss: the estimated floor must be separated from ordinary Bayes error, estimation error, optimization error, and architectural irreducible error. One positive number fitted to a loss curve is not yet $\gamma_H$.

### 6.2 Layer II — measurement

**Proposition 3 (an interaction exponent).**  
Does human interaction noise accumulate as a power, and does its exponent exceed the exponent of the signal it rides on, in the same sense that $\delta > \beta$ along tokens? If interaction round $T$ plays a role analogous to $D$, (SSL) predicts an interior minimum: past some $T$, more dialogue reduces capacity. Multi-turn error accumulation and “hallucination snowballing” are *reported* phenomena consistent with that shape. They are not yet a measurement of an exponent, and a U-shape is also what user fatigue, rising task difficulty, and a shifting model policy look like. The proposition is about the exponent under controls, not about the existence of some U-shaped plot.

**Proposition 4 (a modality spectrum).**  
Speech, typing, clicking, and selection have different noise laws. Can they be placed on one capacity spectrum by giving each modality its own map from behavior into $(N, D)$ or into a more suitable pair (bandwidth, signal power), so that the theory says which modality to use for which task? This proposition is **not** operationalized by the keyboard restriction in Section 7. It is the reason the restriction is temporary. A spectrum is undefined until at least two modalities have been measured with the same identification strategy.

### 6.3 Layer III — intervention

**Proposition 5 (precoding).**  
Shannon’s theorem says that rates below capacity can be driven to arbitrarily small error by encoding, at the price of encoder complexity. The human-facing analogue is an interaction protocol: structured prompts, intent confirmation, feedback calibration. Does such a protocol reduce effective noise at fixed channel capacity? Human-Bounded Intelligence supplies a sharper prediction than “cleaner prompts help”: auxiliary non-human signals should reduce the floor only insofar as they restore information about the latent target. A prompt format that makes the user more fluent without adding information about $Y^\ast$ need not move $\gamma_H$.

**Proposition 6 (a budget, not a slogan).**  
Treat human supervision as one noisy channel and model scaling as another, under a joint budget. The design question—buy parameters, or buy human feedback—is then a constrained capacity maximization, not a preference. Any optimum is meaningless if it averages over users whose ability, preference, and task distribution are nonstationary. Heterogeneity is part of the proposition, not a robustness check to be added later.

### 6.4 The rule

*Constraint.* The failure mode the notes correctly isolate is circular enlargement of (SSL): define “interaction noise” as whatever made the loss worse, insert a term that fits the worsening, and declare the framework extended. The counter-rule is:

> A term enters (SSL) only after it is separable, identifiable, intervenable, and extrapolable. Otherwise the extension is a rename.

The six constraints in Section 9 are that rule, expanded. Propositions 1–6 are not independent essays. Proposition 1 is illegal until separability holds. Proposition 2 is empty until the floor is estimated against the right baseline. Propositions 5 and 6 are causal claims and require an intervention, not a regression.

---

## 7. The keyboard channel as the laboratory object

### 7.1 Why this boundary is a scientific gain

Restricting attention to “noise introduced when a human types an intention” is not a smaller version of the same problem. It moves the problem onto a channel that already has a geometry, a timing process, and decades of measurement.

Three properties do the work:

| Property | Why it matters for SSL |
|---|---|
| The noise mechanism factors | Physical, cognitive, and contextual layers are not the same random variable. Proposition 1 can be tested on the factorization instead of on a label. |
| One layer is randomly assignable | Adjacent-key substitutions can be injected into a fixed prompt. In natural typing, errors are entangled with fatigue, difficulty, and strategy, so the entanglement cannot be conditioned away by observation alone. |
| Cognitive state has a side channel | Keystroke intervals, pauses, and keystroke count move with load. The mediator is not identical to the final erroneous string. |

Modalities that lack all three—open-ended speech in the wild, in particular—stay outside the first experiment. They are Proposition 4’s problem, addressed only after the keyboard identification strategy exists.

### 7.2 Three layers

**Physical layer.**  
On a QWERTY keyboard the substitution process is not uniform. The probability of striking `s` when aiming at `a` is far larger than the probability of striking `p`, and that fact is fixed by geometry, almost independent of what the typist is trying to say. A key-adjacency matrix parameterizes it. Engines in the class the notes call HIVE generate the standard edit family: neighbor substitution, transposition, deletion, insertion, duplication.

**Cognitive layer.**  
`their` → `thier` can be a stable spelling model or a failure of chunking under load. Keystroke dynamics separate these better than the string does. Difficult tasks are reported to slow typing, lengthen pauses, and increase keystroke count. The notes report a further correlation result: the correlation between inter-key interval and content complexity distinguishes compositional writing ($\rho$ in a range of roughly $0.35$–$0.55$) from mechanical transcription ($\rho < 0.15$). Those coefficients are carried from the working notes; they are not re-estimated here. The logical point does not depend on the exact interval: timing is a measurement of the mediator, and the mediator is not the corrupted token.

**Contextual layer.**  
This layer is not transmission error. It is residual uncertainty over intention given a keystroke sequence. Inside the keyboard boundary it has an operational definition that does not require a general theory of meaning: the number of distinct, plausible intentions compatible with the same keystroke sequence when context is withheld. A language model, in the classical noisy-channel spelling formulation, is exactly the prior that spends that uncertainty:

$$
P(\text{intent} \mid \text{keys})
  \propto
  \underbrace{P(\text{keys} \mid \text{intent})}_{\text{physical and cognitive channel}}
  \;
  \underbrace{P(\text{intent})}_{\text{contextual disambiguation}}.
$$

The product is the right generative picture. It is not yet evidence that the two factors add inside the SSL denominator.

### 7.3 Two functional forms SSL must be willing to lose

*Reported, then turned into a fork.* The notes extract two findings from keyboard-perturbation studies (HIVE and related work):

1. Models absorb a large amount of QWERTY corruption before accuracy falls sharply. The count of damaged tokens, more than the type of edit, tracks the loss.
2. Increasing the model’s thinking budget largely restores the lost performance.

If both findings hold, keyboard noise is a poor candidate for a new additive power $d_{\mathrm{int}} T^{\delta_{\mathrm{int}}}$ dropped into (SSL). Two alternatives have to be carried as live hypotheses.

**Form K1 — additive power.**  
Interaction dose $T$ (edit rate, or round index, or a timing-derived cognitive-load proxy) contributes a term $d_K T^{\delta_K}$ in the denominator. This is the unique form in which Proposition 3 is a direct transcription of $\delta > \beta$. It predicts a smooth U-shape in $T$ and no special role for inference compute except insofar as inference compute is already inside $N$ or $D$, which it is not.

**Form K2 — erasure, with a compute rebate.**  
Each token survives with probability $1 - \pi$, or a prompt fails when the surviving fraction crosses a threshold. Capacity depends on the surviving information, not on an additive noise power. Inference compute $R$ (thinking tokens, reranking, a cleanup pass) buys back part of the erasure. The notes’ “re-pass” observation—that cleaning the instruction before the model sees it has only limited effect—says the rebate is incomplete. Incomplete recovery is informative: a perfect cleanup would have said the channel was invertible by a preprocessor; a partial cleanup says some of the damage is not a surface edit.

Form K2 changes the *optimization* SSL is asked to support. If $R$ substitutes for lost input information, the relevant frontier is not only $(N, D)$ but $(N, D, R)$ at fixed budget, and a cleaner keyboard channel is a substitute for $R$. That is a concrete version of Proposition 6 inside one modality: spend the next unit of budget on parameters, on thinking tokens, or on a precoder (autocomplete, constrained decoding, intent confirmation).

A threshold version of K2 also predicts something K1 does not: little loss over a wide range of edit rates, then a sharp drop. An additive power predicts a smooth curve. The distinction is empirical and does not require new terminology.

### 7.4 What randomization buys

In natural use, a typist’s error is caused by the same factors one would like to hold fixed: task difficulty, load, fatigue, strategy. Conditioning on the observed error does not separate “this edit type hurts the model” from “the state that produced this edit type also changed the task.”

Injection removes that fork for the physical layer. The same prompt set can be randomly assigned to neighbor substitution, transposition, deletion, or a cognitive-style misspelling schedule, at a matched rate of damaged tokens. Performance differences at matched damage rate are then attributable to edit structure. Differences that appear only when damage rate changes, regardless of edit type, support the notes’ claim that token survival, not edit identity, is the carrier of loss.

What randomization does **not** buy: a measurement of natural cognitive noise. Injected misspellings that *look* cognitive are not cognitive. Estimating the cognitive layer requires the timing side channel on real typing, with task difficulty independently controlled. Proposition A below is designed so that these two designs are not collapsed into one “keyboard study.”

### 7.5 Three propositions that can be run

These are the keyboard-sized versions of Propositions 1, 3, and 5. They do not replace Propositions 2, 4, and 6.

**Proposition A (separability; the test for Proposition 1).**  
On a fixed prompt set, measure loss under (i) pure physical noise: random adjacent-key edits at rate $\pi$, and (ii) a cognitive-style schedule whose edit rate matches $\pi$ but whose edit locations follow spelling and chunking patterns, ideally on real keystroke traces with load instrumented. Ask whether the two loss increments add when both are present.

- Additivity supports writing two terms, or one term that depends only on $\pi$.
- A large interaction, especially if timing-derived load changes the effect of a physical edit, argues against a single keyboard scalar in the SSL denominator.
- If matched-$\pi$ physical and cognitive schedules produce the same loss, the notes’ “damaged-token count dominates edit type” claim is confirmed on this slice, and a fourth SSL component indexed by edit type is unnecessary. A component indexed by survival rate may still be necessary.

**Proposition B (exponent or threshold; the test for Proposition 3).**  
Accumulate keyboard damage either within a prompt (rate $\pi$) or across rounds (independent damage each round, context retained). Distinguish three outcomes:

| Outcome | Implication |
|---|---|
| Smooth power in $\pi$ or in round index $T$, with noise exponent above the signal exponent | K1. $T$ can be discussed in the same grammar as $D$, and a U-shape is a prediction, not a surprise. |
| Flat region, then a cliff at a survival threshold | K2. Do not report a power-law exponent as if it were the finding. |
| U-shape that disappears once task difficulty and user policy are controlled | The curve was a confound. SSL gains nothing. |

Round index $T$ is not data volume $D$. Treating them as the same variable is a scale error, even if both happen to enter a logarithm.

**Proposition C (the feasible set of precoding; the test for Proposition 5).**  
Operational precoders on this channel are ordinary: real-time spell correction, autocomplete, keystroke-intent decoding, and a cleanup pass before the LLM. The scientific questions are the boundary, not the existence of a benefit.

- How much of the loss in Proposition B does each precoder remove, at matched residual edit rate?
- Does the residual, after the strongest precoder and a large thinking budget $R$, go to zero? If it does, keyboard noise is not an HBI floor and should not be absorbed into $e$. If a positive residual remains and tracks insufficiency of the typed string for the latent target—not the edit rate—that residual is the first keyboard-sized estimate of a floor that scale and $R$ do not buy.
- Does the precoder impose a cognitive cost that changes the timing process and thus the next round’s noise? That feedback is part of the result. A precoder that lowers edit rate and raises load can increase total loss.

The notes already record that a cleanup pass is not sufficient. Proposition C asks for the curve of residual loss against precoder strength and against $R$, not for another demonstration that spellcheck helps.

### 7.6 What the keyboard program explicitly does not answer

| Left open | Why the keyboard does not close it |
|---|---|
| Proposition 2 in full generality | A keyboard residual is at most the floor of *this* channel. It does not identify $\gamma_H$ for preference data, demonstrations, or RLHF. |
| Proposition 4 | One modality cannot define a spectrum. |
| Proposition 6 in full generality | The budget over $(N, R, \text{precoder})$ under keyboard noise is a special case. It says nothing about the value of human preference labels. |
| Speech, tool use, multi-user strategy | Different observability, different assignment mechanism. |

---

## 8. Critique of the Shannon Scaling Law as a base

The interaction program inherits SSL only where SSL is actually identified. The following limits are properties of the 2026 paper, not of information theory in general. Several of them are already acknowledged, in softer form, by the existence of the six-parameter reduction.

### 8.1 The analogy is stronger than the derivation

- Shannon–Hartley does not apply to a nonlinear, nonstationary, coupled training dynamics. Predictive success does not convert the analogy into a theorem.
- Equation (L) is assumed. A different monotone map from capacity to loss would move the location of every fitted basin.
- The three noise terms are assumed to add and to be separately interpretable. Nothing in the fitting procedure tests that a coupled term was not simply absorbed into $\gamma$, $\delta$, and $e$. “Model-interaction noise” in particular names a dynamic story that the scalar $c(DN)^{\gamma}$ only partially encodes.
- $N^{\alpha}$ and $D^{\beta}$ are inherited from existing scaling practice. They are not implied by coding theory.

Any fourth term added under these conditions inherits an under-identified denominator. That is the formal reason Proposition 1 cannot be settled inside the current fitting pipeline.

### 8.2 The experimental range does not reach the claim one would like to export

- Scale stops at 12B (Pythia) and 32B (OLMo2). The clean extrapolation is a factor of roughly $1.7$ in parameters and a similar factor in tokens, at pooled $R^2 = 0.847$. Useful against monotonic baselines; not a warrant for trillion-parameter or long-horizon forecasts.
- Perturbations are Gaussian weight noise, GPTQ, and SFT learning rate. Learning rate is a particularly impure noise proxy: it moves the optimization path and the task fit together. Distribution shift, data contamination, human input, and multi-turn drift are absent.
- The working notes say that only WikiText-2 loss was fit. That understates the paper. SFT results cover GSM8K, SocialIQA, and StarCoder. The fair residual objection is that these are still compact, closed tasks. They do not measure open-ended generation, reasoning chains as used in deployment, or a human in the loop.
- The full law has nine free parameters and needs variation across both $N$ and $D$ to identify them. The simplified law is evidence that several of those degrees of freedom are weakly used. It is also evidence that the three-term story is only partly resolved by the data: terms that can be pruned are terms the experiments did not pin down. Baseline comparisons include OpenAI-style, Chinchilla-style, and other perturbation-aware laws, but they do not exhaust recent scaling variants, and fit quality is not causal identification.

### 8.3 The paper is silent on the object of Sections 5–7

This is not a complaint that the authors failed to write a different paper. It is a boundary on citation.

- The noise that SSL varies is weight noise, quantization noise, and optimizer noise. It is not typed, spoken, or selected human input.
- There is no multi-turn protocol, no human feedback loop, no intent drift, and no context-reset policy.
- Therefore no result in the paper answers Propositions 1–6. Extending the framework to interaction requires a new channel definition, a new noise measurement, and a new experiment. It cannot be done by reinterpreting $e$.

### 8.4 Deployment phenomena that would change the formula are outside it

Inference-time compute, chain-of-thought, tools, retrieval, and RLHF all change how much information reaches the decision. Under Human-Bounded Intelligence, some of them are exactly the auxiliary channels that move $\gamma_H$. Under Form K2, thinking budget is a rebate on keyboard erasure. SSL as published has neither variable. Quantization in the paper is post-training (GPTQ), not quantization-aware or mixed-precision training. The impact statement’s claim that better laws reduce wasted compute is not accompanied by a decision-level cost analysis. Alignment, fairness, and privacy consequences of a noise model are named, if at all, only generically: a law that tells practitioners when scale still helps can just as easily be read as permission to scale.

---

## 9. What is allowed to count as a solution

These constraints are the notes’ six principles, rewritten as admission rules for a result. A proposition is not “addressed” by a paragraph that respects the rule’s vocabulary. It is addressed by a measurement the rule would admit.

### 9.1 Conceptual operationalization

*Constraint.* Split what the notes currently bundle as interaction noise:

| Kind | Example on the keyboard | What it is not |
|---|---|---|
| Observation noise | A neighbor-key substitution | The typist’s uncertainty about the task |
| Process noise | A load-driven rise in pause time and spelling failure | The resulting string alone |
| Intervention noise | Extra errors caused by the precoder’s own friction | The precoder’s average benefit |
| Intention drift | The target $Y^\ast$ changes between rounds | A noisy encoding of a fixed target |
| Preference distortion | A typed “yes” that is compliance rather than the latent preference | A typo |
| Semantic compression | The intention has no short typing that determines $Y^\ast$ | A transmission error |

No result may define the noise term as “the part of the loss we did not explain.” Additivity has to be tested (Proposition A), not asserted so that the term fits in a denominator.

### 9.2 Theoretical hygiene

*Constraint.*

- A power-law fit is a description. It does not become a mechanism by being written inside a logarithm copied from Shannon–Hartley.
- State the channel assumptions that were used, and state which of stationarity, memorylessness, and one-way transmission was false in the experiment.
- Keep Bayes error, estimation error, optimization error, architectural $e$, and $\gamma_H$ in separate columns. Report the column that moved.
- Prefer the three-term SSL denominator whenever it predicts the new data. A fourth parameter must buy a prediction the nested model misses, on a pre-specified comparison (likelihood ratio or an equivalent model-comparison statistic), not a higher $R^2$ on the fitting sample alone.

### 9.3 Measurement

*Constraint.*

- Intention is latent. Any proxy—reconstructed target, user confirmation, task label—needs a stated relation to $Y^\ast$, and a check that the proxy is not itself a noisier copy of the model’s output.
- Report the signal-to-noise ratio of the *evaluation* channel. SSL’s own lesson is that a noisy benchmark makes scaling predictions look worse than the system under test. Accuracy alone hides that.
- For every exponent: confidence interval, sensitivity to the fitting window, and a pre-registered comparison against a threshold (or other non-power) alternative. Proposition B is lost if only the power law is fit.
- Pre-register interaction studies. Order effects, demand characteristics, and users playing the protocol are the default, not the caveat.

### 9.4 Causality

*Constraint.* A U-shape is not an exponent. Admit a causal claim for Propositions 3, 5, and 6 only under an assignment mechanism: randomized edit injection, randomized precoder, randomized allocation of a supervision budget, or a credible natural experiment. Because the model’s reply changes the human’s next keystroke, the unit of analysis is a feedback system. A static regression of loss on round index estimates a mixture of the channel and the users’ policy.

### 9.5 Scale and extrapolation

*Constraint.*

- $N$, $D$, $T$, wall-clock fatigue, and modality are different axes. An exponent in $T$ does not transfer to $D$ by renaming.
- An exponent is “the” interaction exponent only if it is stable across the tasks, user groups, and keyboards named in the pre-registration. Otherwise it is a local fit, which is still a result, if labeled as local.
- Do not export a laboratory keyboard result to a trillion-parameter model, a week-long conversation, or a production client. State the largest factor actually tested, as Section 3.4 does for SSL itself ($\approx 1.7 \times$).
- An optimal budget that ignores user heterogeneity is an average of different problems.

### 9.6 Ethics and ecological validity

*Constraint.* The human is not a noise source in the moral sense, even when a keystroke is a noise source in the channel sense. Typing carries intention, adaptation, and invention; a model that treats all residual as $\mathcal{N}$ will “correct” away the part of the signal that was never an error. Consent, privacy of keystroke timing, and a ban on protocols that manipulate the typist are admission conditions, not a closing paragraph.

Laboratory injection differs from production typing. Proposition A’s injected arm and its natural-typing arm answer different questions; only the second has ecological claim. Precoders have side effects—cognitive load, changed phrasing, users writing toward the autocorrect—and those side effects are outcomes. A capacity gain that degrades the user’s control of what was meant is not a pure gain on Proposition 5.

### 9.7 Admission table

| Proposition | Minimum evidence that counts | What does not count |
|---|---|---|
| 1 / A | A separability test with a nested comparison against three-term SSL | A new symbol in the denominator |
| 2 | A floor estimated against Bayes, optimization, and architectural baselines, with a stated identity to $e$ or a rejection of that identity | Any positive asymptotic loss |
| 3 / B | A pre-registered distinction between power, threshold, and confounded U-shape | A plot that bends |
| 4 | At least two modalities identified with the same measurement model | A qualitative ranking of “speech is noisier” |
| 5 / C | A randomized precoder curve, including residual loss and user-side cost | A before/after spellcheck demo |
| 6 | A randomized or otherwise identified budget allocation under heterogeneity | An opinion on whether to buy GPUs or annotators |

---

## 10. What would follow if the admission table were met

This section is conditional on Section 9. It is not a claim that the conditions are close to being met.

### 10.1 Scientific content of a real solution

A result that passed the admission table would do four things, and only these four.

1. **Put training scale and interaction scale in one ledger.** Pretraining, fine-tuning, alignment, deployment, and multi-turn use would be comparable as channel-capacity problems only to the extent that each noise term had been identified. The design variable would be the capacity of the closed human–model loop, not $N$ alone.
2. **Force an extension of the channel model, not a metaphor.** The required mathematics is the capacity of a nonstationary feedback channel with a latent semantic input, plus a coding theorem for protocols that try to protect intention, plus a lower bound that separates $\gamma_H$ from $e$. That is an extension of information theory into a regime Shannon–Hartley does not cover. It is not an application of Shannon–Hartley.
3. **Turn three slogans into quantities.** “Can alignment be perfect?”, “Does scale erase human noise?”, and “Must long conversations eventually degrade?” become: is $\gamma_H = 0$ under this supervision channel; does $\partial \mathcal{L} / \partial N$ remove the interaction term or only the terms already in (SSL); does the identified interaction exponent produce an interior minimum in $T$.
4. **Make the unit of analysis a triple.** Source, channel, and destination are optimized together. A model is not intelligent in isolation under this program; a loop is more or less capable.

Connections to the information bottleneck, to cognitive load, and to scale-free structure in neural populations are plausible *after* the keyboard identification exists. They are not consequences of adopting the vocabulary.

### 10.2 Academic consequences, if the results are real

The program would sit across theory venues (NeurIPS, ICML, ICLR), human–computer interaction (CHI, UIST), dialogue (ACL), fairness and accountability (FAccT), and cognitive science. The methodological export is more specific than “interdisciplinarity”: causal identification for closed-loop, nonstationary systems; scaling analysis that refuses to mix axes; SNR reporting for evaluation channels; pre-registration as the default for interactive experiments.

Practical consequences follow only from the same evidence:

| Decision | What a positive result would actually license |
|---|---|
| Benchmarks | Report evaluation-channel noise, not only accuracy |
| Protocols | A quantitative rule for when retaining context destroys more signal than it adds, and a precoder whose residual was measured |
| Budgets | An identified tradeoff between $N$, human feedback, and inference compute, with user heterogeneity in the objective |
| Alignment | An error budget that is allowed to be nonzero, if $\gamma_H > 0$ was actually estimated |
| Governance | An information-theoretic description of what an evaluation measured, which is not by itself a regulatory standard |

### 10.3 Magnitude, without the slogan

The notes rank a complete solution with Shannon’s effect on communication engineering or with statistical mechanics’ effect on thermodynamics, and they mention a Turing-scale prize as the corresponding professional magnitude. Read against Section 9, that ranking is a statement about *kind*, not about proximity.

- Information theory mattered because it separated what rate is achievable from the gadgets of 1948 and gave engineers a bound they could design against. A human–model capacity theorem would matter in the same way: it would say what cannot be bought with scale, and what can be bought with a better channel. It would not, by itself, train a stronger model.
- A complete solution is not the expected outcome. Humans are nonstationary, the loop is reflexive, and intention is unobserved. The realistic product is a program that accumulates partial bounds.
- Partial results already split cleanly, and each is large enough to stand: an identified floor (alignment theory), a precoding bound on a real channel (interaction design), an identified supervision budget (the economics of human feedback).
- A formula with no experiment that meets Section 9 is a relabeling. Its magnitude is approximately zero, regardless of the vocabulary.

The sentence the notes are reaching for, stripped of promotional tone:

> The question “how large can a language model be?” is replaced by “how capable, how reliable, and how interpretable can this human–model channel be, and which resource buys the next increment?”

That replacement is the contribution. It happens only at the rate the admission table is satisfied.

---

## 11. A short research order

The dependency order is stricter than a list of interesting questions.

1. **Fix the measurement model on the keyboard** (Section 7.2): adjacency matrix, timing proxy, operational definition of contextual ambiguity. No exponent before the likelihood.
2. **Run Proposition A** at matched damage rate, injected physical edits versus load-instrumented natural typing. This decides whether a keyboard term is even a single term.
3. **Run Proposition B** against the pre-registered trio {power, threshold, confound}. This decides K1 versus K2 versus “nothing to add.”
4. **Only if A and B identify a term**, write it into a nested extension of (SSL) or (SSL-s) and demand an out-of-sample likelihood gain. This is the earliest moment Proposition 1 can be answered, and the answer is allowed to be “do not add it.”
5. **Run Proposition C** on the term that survived, with residual loss after precoding and after thinking budget $R$. Interpret a nonzero, scale-stable residual as a *candidate* floor (Proposition 2), not as $e$, until the baselines in Section 9.2 are reported.
6. **Leave Propositions 4 and 6** until a second modality survives the same sequence, or until a real supervision budget—not a keyboard precoder—is randomly assigned.

Step 4 is the step the working notes are tempted to do first. It is the step that converts the program back into a rename.

---

## 12. Notation

| Symbol | Meaning |
|---|---|
| $N$ | Parameter count |
| $D$ | Training tokens |
| $C$ | Training compute, in the Chinchilla sense, when so marked |
| $C_{\mathrm{LLM}}$ | SSL capacity, equation (SSL). Not compute. |
| $\mathcal{L}$ | Test loss, tied to capacity only by the ansatz (L) |
| $\alpha, \beta$ | Bandwidth and signal exponents |
| $\gamma, \delta$ | Model-interaction and data-noise exponents |
| $e$ | Irreducible SSL noise term |
| $T$ | Interaction rounds, or another stated interaction dose. Not interchangeable with $D$. |
| $\pi$ | Token damage rate under keyboard perturbation |
| $R$ | Inference-time compute (thinking budget) |
| $Y^\ast$ | Latent evaluation target |
| $\gamma_H$ | Human-Bounded Intelligence floor. Not the SSL exponent $\gamma$. |
| K1, K2 | Additive-power versus erasure-with-rebate models of keyboard noise |

---

## References

1. Kaplan, J., McCandlish, S., Henighan, T., Brown, T. B., Chess, B., Child, R., Gray, S., Radford, A., Wu, J., and Amodei, D. (2020). Scaling laws for neural language models. arXiv:2001.08361.
2. Hoffmann, J., Borgeaud, S., Mensch, A., Buchatskaya, E., Cai, T., Rutherford, E., Casas, D. d. L., Hendricks, L. A., Welbl, J., Clark, A., Hennigan, T., Noland, E., Millican, K., van den Driessche, G., Damoc, B., Guy, A., Osindero, S., Simonyan, K., Elsen, E., Rae, J. W., Vinyals, O., and Sifre, L. (2022). Training compute-optimal large language models. arXiv:2203.15556.
3. Liu, Y., Liu, Z., and Gore, J. (2025). Superposition yields robust neural scaling. arXiv:2505.10465. NeurIPS 2025 Best Paper Runner-up.
4. Ouyang, X., Liu, D., Cai, Y., Liu, J., Yang, Y., Zheng, C., Hartvigsen, T., and Ma, Y. (2026). LLMs as noisy channels: A Shannon perspective on model capacity and scaling laws. arXiv:2605.23901. Accepted at ICML 2026.
5. Chen, M., Hui, B., Cui, Z., Yang, J., Liu, D., Sun, J., Lin, J., and Liu, Z. (2025). Parallel scaling law for language models. arXiv:2505.10475.
6. Alabdulmohsin, I. and Zhai, X. (2025). Recursive inference scaling: A winning path to scalable inference in language and multimodal systems. arXiv:2502.07503.
7. Rodriguez Dominguez, A. (2026). Human supervision as an information bottleneck: A unified theory of error floors in human-guided learning. arXiv:2602.23446.
8. Shannon, C. E. (1948). A mathematical theory of communication. *Bell System Technical Journal*, 27, 379–423, 623–656.

Items in the text marked *reported* that concern keyboard perturbation engines (HIVE), keystroke–load correlations, and thinking-budget recovery are retained as claims of the working notes. They are not given bibliographic entries here, because this synthesis does not re-identify the source experiments. They should be cited from the primary studies before any of Propositions A–C is pre-registered.
