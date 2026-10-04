# Orthographic Channels and Input Noise as Structural Disturbances in Human–Model Interaction

## A Pre-Registered, Phased Protocol Integrating System One / JEV-Ecosystem Tooling

**Document type:** Detailed research protocol (*Nature Human Behaviour*–oriented framing)  
**Version:** 1.3 (English typo first, then cross-script / multilingual expansion)  
**Status:** Draft for staged pre-registration  
**Compute envelope:** Single consumer GPU admissible; zero paid API on confirmatory path  
**Primary interface class:** Typed decision models (System One):  
$\texttt{state} \times \texttt{questions} \mapsto$ distributions over caller-defined options  

> **v1.3 names the gate's threshold LIMEN and adds the one estimand that naming makes legible.**
> v1.2 recorded three decisions that earlier work had already made. The protocol is the research
> objective, so a change to it may not be made only in a downstream document — if an amendment
> contradicts the protocol, the protocol is what must move. **Every such change is marked `vN CHANGE`
> at the point it applies**, and each names the document that motivated it, so the protocol's own
> history stays legible.
>
> | Version | Changes | Status |
> |---|---|---|
> | **1.3** | (1) LIMEN named as the gate's threshold (§0.3), with what the name does and does not carry; (2) the **claim** stated directly (§0.4); (3) the **limen-shift diagnostic** $\Delta\tau^\star$ added as a *reported, non-confirmatory* quantity (§4.4a) | additive; **no frozen value moved** |
> | 1.2 | (1) `Q0` is `intent` alone; (2) the pin is decided — Laya English root at `55cf4c4e…`; (3) the `τ*` fitting rule is stated, including when it yields nothing | — |  

---

## 0. Thesis and staging principle

> ## THE GLOBAL ANCHOR
>
> **This protocol is the programme's global anchor.** Every other document in this repository —
> pre-registration, amendments, the item-bank spec, the manuscript, the review records, the dashboards —
> is **subordinate to it** and derives from it.
>
> **What that means mechanically, and how it is enforced:**
>
> 1. **A change to the research objective is a change to THIS file.** If work elsewhere reaches a
>    conclusion that contradicts this protocol, the protocol is what moves — a downstream amendment
>    cannot silently redefine the objective. Every such change is marked `vN CHANGE` at the point it
>    applies and names the document that motivated it, so the protocol's own history stays legible.
> 2. **The objective's identity is checked mechanically.** A guard verifies that this file is present,
>    that its recorded sha256 matches, and that the version in §14 agrees with the version in the
>    header. A file that drifts from the anchor is drift by definition.
> 3. **"What are we working on?" has exactly one answer, and it is §0–§1 of this file.** If any other
>    document's summary of the objective disagrees with §0–§1, this file wins without discussion.
> 4. **What does NOT anchor here, deliberately.** Instruments, toolboxes, run logs and review records are
>    *inputs and outputs* of the programme, not the programme. They are admitted on the three criteria in
>    `docs/INSTRUMENT_POSTURE.md` (usable, scientific, reproducible) and then used as shipped. **The
>    anchor states what is being asked; it does not state how the asking is instrumented.**
>
> **Current anchor identity:** `protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md`,
> version **1.2**. Its sha256 is recorded in `config/anchor.json` and verified by the drift guard.

### 0.1 Thesis

Human–model language interaction is a **structurally biased coupled control system**; writing systems and input noise are **normal disturbances**, not exceptions. System One (JEV-ecosystem) tooling makes the **control law**—confidence-gated action—directly observable and programmable.

### 0.2 Staging principle (methodological)

Cross-script structural bias is the **long-run** scientific target. However, noise processes, gold labels, and power calculations are **channel-specific**. Therefore the programme is deliberately **phased**:

| Phase | Channel scope | Noise scope | Confirmatory claim |
|-------|---------------|-------------|-------------------|
| **I (anchor)** | English, standard Latin orthography only | English **typos** (keyboard-faithful) | Noise is a normal operating disturbance for System One control metrics (error, SilentError, coverage) |
| **II (extension)** | + ≥1 non-English / non-Latin (or distinct input ecology) | **Script-faithful** noise (not Latin rules copied) | Script × noise **interaction** and cross-channel allocational disparity |

**Rule:** Phase II pre-registration is filed **only after** Phase I instruments (items, $\mathcal{N}_{\mathrm{en}}$, logging, gates) are frozen and pilot-stable. Phase I must not be re-opened to “hunt” interactions after seeing Phase II.

---

### 0.3 LIMEN — the gate's threshold, named

**LIMEN** (Latin *limen*, *threshold*) names the threshold inside the confidence gate: the value at which
graded evidence becomes committed action. In this protocol **LIMEN is $\tau$** — the argument of
$g_\tau$ in §3.4.

**The name is mechanical, not metaphorical.** It fixes what the object is: a *decision boundary
instantiated by $g_\tau$*, at which the system stops accumulating evidence and commits. It does not
carry any extra theoretical commitment, and adopting it changes nothing about the mathematics: every
$\tau$ in this protocol was already a number on a scale, and still is.

**Four things the name explicitly does NOT assert**, each of which the measurements could contradict:

1. **That the limen exists at every condition.** The pilot's clean `SilentError@0.9` was **0/120**,
   which makes `Risk(τ) = 0` across the whole grid and *every* threshold admissible — the budget then
   selects nothing, and §6/v1.2 CHANGE 3 already requires `Coverage@ε` to be reported as **undefined with
   a reason** in that case. **A limen that the data cannot identify is a result, not a failure**, and it
   must be reported as such.
2. **That the limen is unique.** Risk is monotone non-increasing in $\tau$, so the admissible set is
   **upward closed** and an admissible threshold is never unique. The tie-break is **declared**
   (least admissible threshold, §6/v1.2 CHANGE 3), not discovered.
3. **That the limen is well calibrated.** It is a threshold on the model's **own** confidence
   $c = \max_j p_j$, which the pinned instrument is documented to ship **over-confident** (card: mean
   ECE 0.466). The limen's *location* is a property of the instrument as shipped; whether that location
   is *epistemically right* is a separate question this protocol does not answer and does not need to.
4. **That the limen is the same for every channel.** §5.2 forbids equating noise across scripts by rate
   alone for the same reason: a limen estimated under one channel's noise process says nothing about
   another's, because both the evidence $c$ and the budget's referent are channel-specific.

**What the name buys.** It makes one thing legible that the earlier notation hid: **the limen is an
estimand, not a setting.** $\tau \in \{0.80, 0.90\}$ are *fixed probes* placed at pre-registered
positions; $\tau^\star_\varepsilon$ is *fitted per condition on dev*. Those are three different
quantities, and prose that says "the threshold" conflates them. Naming the limen forces the question
**"did the limen move?"** — which is answerable (§4.4a), rather than the unanswerable "what is the
threshold?"

### 0.4 The claim, stated directly

**Thesis.** Human–model language interaction is a **structurally biased coupled control system** in which
orthographic channels and input noise are **normal disturbances, not exceptions**.

**Mechanism, in one line.** An intention is not transmitted through a neutral channel. It is encoded
through an orthographic channel $s$ under channel-specific noise $n \sim \mathcal{N}_s(\lambda)$ as
$x = E(i, s, n)$; a **frozen** decision model converts it to graded evidence
$(\mathbf{p}, c) = f_\theta(x, q)$; and a confidence gate $a = g_\tau(\mathbf{p}, c)$ converts
evidence into action. **LIMEN (§0.3) is the limen in $g_\tau$.**

**The research objective.** To test **how $\lambda$ and $s$ shift that gate and the resulting
control metrics** — `Acc`, `SilentError@τ`, `Coverage@ε`.

**Staged test.** **Phase I** fixes $s = s_{\mathrm{en}}$ and treats English keyboard-faithful typo noise
as a normal disturbance. **Phase II** introduces $s_1$ — a non-Latin or otherwise distinct input
ecology — with **script-faithful** noise, and tests script × noise interaction and cross-channel
allocational disparity.

> **A constraint on how this objective may be worded, and why it is stated here.** The objective names
> **both** $\lambda$ and $s$, because the *programme* spans both phases. **No single phase may test
> both.** Phase I estimates functions of $\lambda$ at one channel and may say nothing about $s$
> (§0.2, §5.2, §8); Phase II is the only phase in which $s$ varies. Any sentence of the form "we test
> how $\lambda$ and $s$ shift the limen" is a statement about the programme, **not** a description of
> what Phase I does — and the pre-registration is the place where that distinction is enforced.

**What the programme does not claim.** It does not claim that noise is exceptional, nor that English
typo results establish cross-script fairness. **It claims that orthographic channels and input noise
are structural disturbances of the control loop itself** — of understanding and of the gate, not merely
of text generation.

---

## 1. Formal system model

### 1.1 Interaction cycle

| Symbol | Domain | Meaning |
|--------|--------|---------|
| $i$ | intention space | User communicative / task intention |
| $s \in \mathcal{S}$ | orthographic channels | Phase I: $s = s_{\mathrm{en}}$ only; Phase II: $s \in \{s_{\mathrm{en}}, s_{1}, \ldots\}$ |
| $n \sim \mathcal{N}_s(\lambda)$ | noise process | Channel-specific; Phase I uses $\mathcal{N}_{\mathrm{en}}$ only |
| $\lambda \in \{0, \lambda_{\mathrm{lo}}, \lambda_{\mathrm{mid}}\}$ | intensity | Pre-registered rates |
| $x \in \Sigma^*$ | symbol string | Observed state text |
| $q \in \mathcal{Q}$ | typed questions | System One choice / noul / (optional) score |
| $f_\theta$ | decision model | Frozen System One parameters in confirmatory tests |
| $\mathbf{p}$ | simplex | Option probabilities |
| $c \in [0,1]$ | confidence | Fixed functional of $\mathbf{p}$ |
| $a \in \mathcal{A}$ | action | $\{\mathrm{answer}, \mathrm{defer}, \mathrm{escalate}, \mathrm{refuse}\}$ |
| $g_\tau$ | gate | Pre-registered map $(\mathbf{p},c)\mapsto a$ |

### 1.2 The coupling, as one chain

The three maps above are not three separate facts. **They are one chain, and the chain is the object of
study** — an intention becomes action only by passing all three in order, and a disturbance anywhere
along it changes the action without the user's intervention.

$$
\underbrace{i}_{\text{intention}}
\;\xrightarrow{\;E(\cdot,\,s,\,n \sim \mathcal{N}_s(\lambda))\;}\;
\underbrace{x}_{\text{channel output}}
\;\xrightarrow{\;f_\theta(\cdot,\,q)\;}\;
\underbrace{(\mathbf{p},\,c)}_{\text{graded evidence}}
\;\xrightarrow{\;g_\tau\;}\;
\underbrace{a}_{\text{action}}
$$

The whole programme is this one line. Each of the three maps that follow is a component of it, given its own equation for readability: equation (2) is the first arrow, equation (3) the second, equation (4) the third, and equation (5) expands the last. Reading it left to right, **noise and channel enter only at $E$**, so any difference between two conditions is a difference in $x$ propagating through both downstream stages — which is the formal reason the Phase I design is **within-item** (§4.1).

**Reading the chain, left to right:**

| Stage | What it fixes | What a disturbance does here |
|---|---|---|
| $E(\cdot, s, n)$ | the **channel**: which orthography the intention is encoded through, and at what noise | **This is where input noise acts.** $\lambda$ and $s$ enter here and nowhere else. |
| $f_\theta(\cdot, q)$ | the **instrument**: a frozen decision model turning text into a distribution | Its output $c$ is the model's own confidence, over-confident as shipped (`docs/PHASE_I_PIN.md`) |
| $g_\tau$ | the **gate**: whether evidence becomes action, and which option | **LIMEN is the threshold inside this arrow** (§0.3). It is the only stage this programme manipulates or fits. |

**Why the chain is written as one line rather than three.** Three separate equations invite the reading
that the stages are independently variable. They are not: **a change in $x$ propagates through both
downstream stages**, so $\lambda$ cannot move $\mathrm{Acc}$ without also moving `SilentError@τ` and
`Coverage@ε`. That dependence is the reason the design is **within-item** (§4.1) — every item is its own
control across $\lambda$, precisely because the chain carries the disturbance from end to end.

**The coupling, stated as the hypothesis.** Phase I does not ask "does noise hurt accuracy". It asks
whether a disturbance entering at $E$ **propagates through $f_	heta$ into the gate $g_\tau$** in a way
that changes not only *what* is answered but *whether* the model commits — which is precisely the
separation between H1.1 (accuracy falls) and H1.2 (confidence does not track it).

**Encoding:**
$$
x = E(i, s, n), \qquad n \sim \mathcal{N}_s(\lambda).
$$

where $E(\cdot, s, \cdot)$ is the **channel encoder**: it maps an intention $i$ to an observed symbol string $x$ under orthographic channel $s$ and noise draw $n$, and $\mathcal{N}_s$ is the channel-specific noise process whose intensity is $\lambda$. Phase I admits $s = s_{\mathrm{en}}$ only and uses $\mathcal{N}_{\mathrm{en}}$ (§4.2), so $s$ is a constant here and $\lambda$ is the only free argument. **No other map in this protocol takes $\lambda$ as an argument**, which is what makes the programme's central claim checkable rather than rhetorical.

**System One map (JEV-compatible):**
$$
(\mathbf{p}, c) = f_\theta(x, q).
$$

where $f_\theta$ is the frozen decision model, $q$ the typed question, $\mathbf{p}$ the option probability vector and $c \in [0,1]$ the confidence. In Phase I $\theta$ is **not trained and not tuned**: $f_\theta$ is the pinned instrument (§3.2), so the only thing that varies across conditions in this map is its input $x$. Because $c$ is a **fixed functional of $\mathbf{p}$** (§3.3), the model cannot raise its confidence independently of its evidence — a constraint that H1.2 tests rather than assumes (§4.4).

**Control:**
$$
a = g_\tau(\mathbf{p}, c).
$$

where $g_\tau$ is the pre-registered gate and $a$ the action. Equation (5) expands $g_\tau$ into the rule this line names. This is the only map in the chain whose form the programme manipulates or fits: $\tau$ is a **stimulus parameter** in Phase I (pre-registered at two levels, §3.4) and a **fitted quantity** $\tau^\star_\varepsilon$ in the Phase II analysis (§4.4a).

**Normal disturbance:** ecologically relevant regime has $\lambda > 0$; $\lambda = 0$ is a boundary probe.

**Structural bias (full thesis, Phase II):** for matched $i$ and comparable $\lambda$, laws of $(\mathbf{p},c,a)$ differ across $s$ beyond sampling error.

**Phase I restriction:** $s$ fixed to English; estimands are functions of $\lambda$ only (and optional model/router contrasts within English).

## 2. Why Phase I anchors on English typos

| Reason | Implication |
|--------|-------------|
| **Process validity** | English keyboard typo models (adjacency, transposition, deletion, insertion) are well-specified and reusable (e.g., MulTypo-style Latin layouts) |
| **Label quality** | Intent gold and inter-annotator agreement are cheapest and most stable in English first |
| **Instrument debug** | JSONL schema, confidence rule, gates $g_\tau$, and System One wiring are validated before multilingual complexity |
| **Literature bridge** | Connects to existing LLM typo-robustness results while shifting DVs to **SilentError** and **coverage** under System One |
| **Avoid false cross-script claims** | Forbids treating “English typo intensity” as universal $\lambda$ across scripts |

Phase I **does not** claim to test writing-system bias. It claims: under English orthography, typo noise is a **first-class disturbance of the control loop**.

---

## 3. JEV-ecosystem integration (technical, both phases)

### 3.1 Wire format

```text
state:     <English text, clean or typo-perturbed in Phase I>
questions: {
  intent:   { type: "choice", instructions: "...", criteria: { ... } }
}
→ probs, conf per question id
```

> **v1.2 CHANGE 1 — Q0 is `intent` alone; `ok` and `escalate` are DROPPED from Phase I.**
>
> The v1.1 wire format specified three questions. Measurement at the pinned revision
> (`docs/C2_NOUL_VALIDITY.md`) found the `noul` primitive **scores exactly chance** — 6/12 correct,
> separation +0.077 — and that its documented two-option workaround is **worse than chance and inverted**
> (−0.137 separation, 0.333 accuracy), with the two methods disagreeing by up to **0.60** on identical
> input. A procedure that disagrees with its own documented alternative is not measurement-stable.
>
> **What this changes and what it does not.** `Acc`, `SilentError@τ` and `Coverage@ε` all require gold,
> and gold exists only for `intent`; the gate `g_τ` acts on `intent`'s confidence. **H1.1–H1.3 are
> unaffected.** The cost is that this protocol no longer measures a deferral or escalation judgement.
> **This is a real reduction in scope and is stated as one**, not absorbed silently.
>
> **If a deferral question is wanted later it must be a `choice`** with checkable options
> (`answer` / `ask for more information`), added by a later amendment — never substituted after seeing
> results. Authority: `docs/PHASE_I_AMENDMENT_2.md` §B4.

### 3.2 Pinned stack (confirmatory)

| Item | Specification |
|------|----------------|
| Primary model | **PINNED: the English root of `convaiinnovations/laya`** (Apache-2.0, 421 M, ModernBERT-large, non-autoregressive) |
| Revision | **DECIDED: `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`** — the revision the `laya` package pins. **The Hub's `main` had drifted to `7b928d82…` and is NOT the pin.** |
| Weights | Commit hash + per-file SHA256, recorded in `config/pin_laya.json` (5 files, 846.20 MB) |
| Variant | The **root**, named explicitly: that revision also ships `multilingual/` and `typed-decisions/` subtrees, so "Laya" alone is ambiguous |
| Training | **Frozen** $\theta$ in Phase I–II confirmatory arms |
| API | Local only for confirmatory path |
| Verification | **Executed**, not merely hashed: `measurement/smoke_predict.py` ran on CUDA at that revision and returned per-option probabilities, `truncated: false` |
| Optional contrast | Second checkpoint or one generative forced-choice baseline (secondary) |

> **v1.2 CHANGE 2 — the pin is decided, where v1.1 left it as "pick one and pin".**
> The v1.1 text offered "English Laya root **or** multilingual checkpoint forced on English — pick
> one". The root was pinned, verified by execution, and the multilingual variant was **not** chosen.
> **The instrument is used exactly as shipped** (`docs/INSTRUMENT_POSTURE.md`): a temperature refit was
> considered and **rejected**, because refitting the confidence `c` that enters `g_τ` would substitute a
> different instrument and measure that instead. Authority: `docs/PHASE_I_PIN.md`,
> `docs/PHASE_I_AMENDMENT_1.md` §A1.

**Phase I recommendation:** pin **one** English-capable System One artifact; do not vary router language logic until Phase II.

### 3.3 Confidence rule (frozen)

- Choice: $c = \max_j p_j$  
- Noul: $c = \max(p,\,1-p)$  

### 3.4 Primary gate

**The primary gate, stated as the decision rule it is.** Confidence is a fixed functional of $\mathbf{p}$, so this rule reads one distribution and makes two decisions from it.

$$
g_\tau:\quad
a = \begin{cases}
\mathrm{answer}(\arg\max \mathbf{p}) & c \ge \tau \\
\mathrm{defer} & c < \tau
\end{cases}
$$

where $\mathrm{answer}(\arg\max\mathbf{p})$ commits to the most probable option, $\mathrm{defer}$ abstains, and the single scalar $\tau$ is the threshold applied to $c$. $\tau \in \{0.80, 0.90\}$ is pre-registered; Coverage@$\varepsilon = 0.05$ uses $\tau^\star$ fit on **dev only** (§3.4, §6). Note what this rule does **not** do: it compares no distance from $c$ to $\tau$, so nothing here supports reading the gap as an amount of evidence (§0.3).
with $\tau \in \{0.80,\,0.90\}$ pre-registered; Coverage@$\varepsilon=0.05$ uses $\tau^\star$ fit on **dev only**.

> **What the gate reads, stated exactly, because the LIMEN framing invites a misreading.** The gate makes
> **two separate decisions from one distribution**. It reads **$c$** to decide *whether to commit*, and
> reads **$\arg\max \mathbf{p}$** to decide *which option to commit to*. Because $c = \max_j p_j$ is a
> **fixed function of $\mathbf{p}$** (§3.3), the gate is **not** reading graded evidence as a
> magnitude and comparing it to a boundary — it is applying a **threshold on the top probability**. The
> LIMEN is therefore the boundary of a **decision rule**, not a measurement scale, and nothing in this
> protocol licenses reading a distance from $c$ to $\tau$ as an amount of evidence.
>
> This is why §0.3 says the name is mechanical: it names the boundary that already existed, and
> imports no assumption that the quantity crossing it is commensurate with anything.

### 3.5 JSONL trial record

```json
{
  "phase": "I",
  "item_id": "...",
  "script": "en_latin",
  "lambda": 0,
  "typo_ops": ["adj:recieve→receive", "..."],
  "noise_seed": 0,
  "state_hash": "sha256",
  "model_id": "<pinned>",
  "question_id": "intent",
  "p": {},
  "c": 0.0,
  "argmax": "",
  "gold": "",
  "error": 0,
  "silent_error": {"0.8": 0, "0.9": 0},
  "action": {"0.8": "answer", "0.9": "defer"}
}
```

---

## 4. Phase I — English typo protocol (confirmatory)

### 4.1 Design

**Factors**

| Factor | Levels |
|--------|--------|
| Noise $\lambda$ | $0$, lo, mid |
| Item | $N$ English intent scenarios (within-item across $\lambda$) |

No script factor in confirmatory Phase I.

### 4.2 English typo process $\mathcal{N}_{\mathrm{en}}$

Allowed edit classes (pre-register subset):

1. Adjacent-key substitution (QWERTY)  
2. Character transposition  
3. Deletion  
4. Insertion (adjacent or random from alphabet)  

**Intensity:** target mean edits per token or per character  
- $\lambda_{\mathrm{lo}}$: e.g. ~5–8% character corruption  
- $\lambda_{\mathrm{mid}}$: e.g. ~12–18%  

Exact rates fixed in pre-registration after a short calibration so that items remain human-readable at lo and stressed at mid. Generator: deterministic in `(item_id, λ, seed)`.

**Out of scope for Phase I:** OCR noise, ASR noise, full-word substitution, adversarial misspellings aimed at jailbreaks, non-English code-switching.

### 4.3 Stimuli

- Domain: short service / routing intents (billing, access, urgency, info).  
- $N_{\mathrm{item}}$: set by power for detecting mid vs clean error increase (and SilentError@0.9 increase) of ≥5 absolute points at 80% power.  
- Gold: locked English labels for `intent` (and noul keys if used as primary).  
- Split: ~30% dev / ~70% test by item_id.

### 4.4 Phase I hypotheses

- **H1.1:** $\mathrm{Acc}(\lambda_{\mathrm{mid}}) < \mathrm{Acc}(0)$ on test.  
- **H1.2:** $\mathrm{SilentError@}0.9(\lambda_{\mathrm{mid}}) > \mathrm{SilentError@}0.9(0)$.  
- **H1.3:** Under dev-fit $\tau^\star$ at $\varepsilon=0.05$, $\mathrm{Coverage}(\lambda_{\mathrm{mid}}) < \mathrm{Coverage}(0)$ on test **or** error among accepted rises (pre-register which is co-primary).

**Interpretation if supported:** typo noise is a material disturbance of System One **understanding and control**, not merely a generation nuisance.  
**Interpretation if H1.1 holds but H1.2 fails:** errors rise but confidence tracks—control law partially healthy.  
**Phase I does not** establish structural bias across writing systems.

### 4.5 Phase I analysis

- Paired / mixed models with item random intercepts; factor $\lambda$.  
- Bootstrap CIs on SilentError and Coverage contrasts.  
- Pre-register Holm across H1.1–H1.3 family as defined in the OSF entry.

### 4.6 Phase I deliverables

Frozen: item bank, $\mathcal{N}_{\mathrm{en}}$, model pin, JSONL, analysis notebook, FAILURES log, short report.

### 4.4a The limen-shift diagnostic $\Delta\tau^\star$ — REPORTED, not confirmatory

**Why this exists.** §0.3 argues that naming the threshold makes one question answerable that the earlier
notation could not state cleanly. This is that question.

**The quantity.** For each condition $(\lambda, s)$, fit $\tau^\star_\varepsilon$ on **dev** by the rule
in §6/v1.2 CHANGE 3, then report the shift in that fitted threshold. A single accuracy number cannot
distinguish a threshold that moved from a threshold that never mattered; this does.

$$
\Delta\tau^\star(\lambda) \;=\; \tau^\star_{\varepsilon}\big|_{\lambda_{\mathrm{mid}}} \;-\; \tau^\star_{\varepsilon}\big|_{\lambda=0},
\qquad
\Delta\tau^\star(s_1) \;=\; \tau^\star_{\varepsilon}(s_1) \;-\; \tau^\star_{\varepsilon}(s_{\mathrm{en}}).
$$

where $\Delta\tau^\star(\lambda)$ is the movement of the **fitted gate threshold** between clean and
noisy input, and $\Delta\tau^\star(s_1)$ the same quantity across channels at matched noise. Note what
is differenced: **two estimated thresholds, not two measurements of one thing**, which is why the
status note below makes this diagnostic rather than a test. The second form is **Phase II only**;
Phase I reports the first, at $s = s_{\mathrm{en}}$ alone.

**Status: a diagnostic, NOT a confirmatory endpoint.** This is stated in the protocol because the
temptation to promote it is exactly the failure this design is built to avoid.

- It is **not** in the H1.1–H1.3 family, so **Holm correction as specified in §4.5 does not apply** and it
  is **not** covered by the α = 0.05 confirmatory claim.
- It is reported **with a bootstrap CI** and is interpreted descriptively. A CI excluding 0 is a
  *description of the dev-fitted threshold's behaviour*, **not** a hypothesis test about the population.
- **Why it must stay non-confirmatory.** $\tau^\star$ is a *fitted* quantity on a finite dev set: its
  sampling variability, and the degeneracy when no threshold is admissible, are properties of the
  estimator rather than of the instrument. Promoting it would import the estimator's behaviour into a
  claim about the model.

**The degeneracy is reported, not hidden.** If the budget selects no threshold at either end of the
contrast — the clean-zero-floor case already measured on this instrument — then $\Delta\tau^\star$ is
reported as **undefined with the reason**, and the one-sided 95 % upper bounds on the silent-error rate
at both ends are reported in its place. **A limen that cannot be located is not a limen at zero; it is
an unidentifiable limen**, and the two must never be reported the same way.

**Interpretation boundaries.** A $\Delta\tau^\star < 0$ (the fitted limen tightens under noise) and a
$\Delta\tau^\star > 0$ (it loosens) are **both compatible with the confirmatory hypotheses**, because
H1.2 and H1.3 are stated on `SilentError@τ` and `Coverage@ε` at **fixed** probes, not on the fitted
limen. **This diagnostic therefore cannot rescue or sink H1.1–H1.3, and it is not evidence for or
against the control-law claim on its own.** Its only job is to make the gate's own movement visible.

---

## 5. Phase II — Cross-script / multilingual extension

### 5.1 Entry criteria (gates from Phase I)

Phase II begins only if:

1. Phase I pipeline error rate (tooling failures) < pre-set bound;  
2. $\mathcal{N}_{\mathrm{en}}$ and labels stable under independent re-run;  
3. New pre-registration filed for Phase II hypotheses (no retroactive change to Phase I).

### 5.2 Design

**Factors**

| Factor | Levels |
|--------|--------|
| Channel $s$ | $s_{\mathrm{en}}$, $s_1$ (one primary contrast) |
| Noise $\lambda$ | $0$, lo, mid (**channel-specific** generators) |

**Critical rule:** $\lambda$ levels are **not** equated by “same edit rate as English” alone. Equivalence is justified by (a) human pilot difficulty, or (b) documented empirical error rates per channel, stated in Phase II pre-registration.

### 5.3 Channel $s_1$ selection criteria

Choose **one** of:

- Non-Latin script with documented digital input confusions; or  
- Same language family but distinct orthographic standard; or  
- IME-mediated input ecology (e.g., conversion errors),

with: (i) ability to build parallel intentions; (ii) annotators; (iii) a **faithful** $\mathcal{N}_{s_1}$.

**Forbidden:** implementing $\mathcal{N}_{s_1}$ as “run English typo ops on transliterated text” as the sole noise model.

### 5.4 Phase II hypotheses (full structural thesis)

- **H2.1:** Script × noise interaction on error (mid vs clean deltas larger for $s_1$ than $s_{\mathrm{en}}$, or pre-registered directed form).  
- **H2.2:** SilentError@0.9 contrast $(s_1,\lambda_{\mathrm{mid}}) - (s_{\mathrm{en}},\lambda_{\mathrm{mid}}) > 0$.  
- **H2.3:** Coverage@0.05 disparity under the same gating discipline as Phase I.

Optional mechanism arm: router `forced_en` vs `forced_multi` vs `auto` under $s_1$ inputs.

### 5.5 Models in Phase II

- Keep Phase I pinned model as backbone when possible.  
- If multilingual checkpoint / router is required for $s_1$, pin it explicitly; report English cells under the **same** artifact for comparability, plus a sensitivity run with Phase I English-only pin on English cells only.

---

## 6. Metrics (both phases)

$$
\mathrm{Acc}(s,\lambda) = 1 - \frac{1}{|\mathcal{T}|}\sum \mathbb{1}\{\hat y \neq y^\star\}
$$

**The three dependent variables, defined once.** All three are functions of the same trial set, and they are read as a triple rather than separately.

where $\mathcal{T}$ is the set of trials at that condition and $y^\star$ is the gold label fixed before the run. **Accuracy is necessary and not sufficient**: a model that answers every item with high confidence and is wrong on a quarter of them scores well here and fails the next metric — the failure this programme exists to separate.


$$
\mathrm{SilentError@}\tau(s,\lambda) = \frac{1}{|\mathcal{T}|}\sum \mathbb{1}\{\hat y \neq y^\star \wedge c \ge \tau\}
$$

where $c \ge \tau$ is the gate's own commit condition (equation (5)). **This metric carries the programme's thesis**, because it counts only trials on which the model both committed and was wrong — the subset no accuracy figure can see. It is $P_e$ in the noisy-channel reading of §0.1. Note it is **non-increasing in $\tau$** — a stricter gate cannot admit more errors — and **verified by machine**, not merely argued: `risk_mono` in the `lean-nhb` formalisation proves $a \le b \Rightarrow \mathrm{Risk}\, b \le \mathrm{Risk}\, a$ over the protocol's own definitions (`scripts/check_lean_axioms.py` reports no `sorryAx`). **The direction matters and an earlier draft had it backwards**, saying "non-decreasing": Lean's kernel settles it, and on a two-item sample $\{\{c{=}3, \mathrm{wrong}\}, \{c{=}9, \mathrm{wrong}\}\}$ the count runs $2, 1, 1, 0$ at $\tau = 2, 5, 9, 10$ — falling, not rising. This is also why §3.4 pre-registers $\tau$ rather than choosing it after seeing the curve, and why $\tau^\star_\varepsilon$ must be fit on **dev** only (§4.4a).


$$
\mathrm{Coverage@}\varepsilon(s,\lambda) = \frac{|\{x: c(x)\ge \tau^\star_\varepsilon\}|}{|\mathcal{T}|}
$$

where $\tau^\star_\varepsilon$ is the least threshold whose **dev**-set SilentError is at most $\varepsilon = 0.05$ (least, because the tie-break maximises coverage — Amendment 2, B1). **Coverage is the Rate of the same channel**: the fraction of trials on which the gate transmits at all. Read as a pair, (SilentError, Coverage) traces a rate–error curve — so a claim that noise leaves the curve unchanged becomes testable rather than rhetorical, which is what H1.3 tests.


Phase I omits $s$ (always $s_{\mathrm{en}}$).

> **v1.2 CHANGE 3 — the fitting rule for $\tau^\star$ is stated, including the case where it does not
> exist.**
>
> v1.1 said only "fitted on dev" and never said *which* threshold is reported when several meet the
> budget. **An admissible threshold is never unique:** `Risk(τ)` is monotone non-increasing in τ, so if τ
> meets the budget then every τ′ ≥ τ meets it too. The admissible set is upward closed and typically has
> no distinguished element. **This is not hypothetical** — the pilot's clean `SilentError@0.9` was
> **0/120**, making `Risk(τ) = 0` across the whole grid and *every* τ admissible.
>
> **The rule:** $\tau^\star_\varepsilon$ is the **least admissible threshold**, i.e. the loosest gate
> whose accepted-error rate fits ε. This is the only convention under which `Coverage@ε` is **maximised**
> among admissible thresholds, so the gap from any other choice is bounded by monotonicity rather than by
> luck.
>
> **And the case where the rule yields nothing.** If `Risk(τ) = 0` for every τ in the grid, the budget
> does not select a threshold at all. Then `Coverage@ε` is reported as **undefined, with the reason
> stated**, and the one-sided 95 % upper bound on the noisy silent-error rate is reported instead.
> **A reported `Coverage@ε` of zero in that situation is a fact about the dev set, not about the model,
> and must never be read as "the model was perfectly selective."**
>
> **v1.3 ADDENDUM — the rule's optimality is now machine-checked, and one limit is named.** The
> `lean-nhb` formalisation builds clean (**12 theorems, zero errors, zero `sorry`**, each verified by
> Lean's kernel via `#print axioms`, which fails on `sorryAx`). Two of its results bear directly on this
> rule. `admissible_mono` proves the admissible set is **upward closed**, so an admissible threshold is
> never unique — the premise of the problem this rule solves. `least_admissible_maximises_coverage`
> proves that **among admissible thresholds the least one maximises `Coverage@ε`**, which is what
> licenses calling the rule *optimal* rather than merely conventional.
>
> **The guarantee is a maximum, not a strict maximum.** `least_admissible_is_at_least_as_good` shows
> that a stricter threshold may admit exactly as much when no observation's confidence lies between the
> two. So the rule is to be reported as *"maximises coverage among admissible thresholds"* and **never**
> as *"maximises it strictly"* — the latter is an overclaim the data can refute.
>
> **What the formalisation does NOT establish, and cannot.** Every theorem follows from the definitions
> alone — the gate, the budget, a finite sample. There is **no theorem here saying that noise changes
> any of these quantities**; that is the empirical claim, carried as a named premise in §4.4, not
> something a theorem can prove. The rule itself is unchanged by the formalisation: what changed is that
> its justification is machine-checked rather than asserted.
>
> Authority: `docs/PHASE_I_AMENDMENT_2.md` §B1 · `docs/LEAN_FORMALIZATION_STATUS.md`.

---

---

### 4.4b Lean 反馈环：机器检查改变了协议的三个核心判断

本协议的数学部分不仅被形式化，更在形式化过程中被**修正**。`lean-nhb` 形式化（`E:/2026-AI4S/lean-nhb/NHB/PhaseI/Core.lean`，13 定理，零错误，零 `sorry`，全部经 `check_lean_axioms.py` 经内核 `#print axioms` 验证）不仅是事后存档，它在构建过程中**发现并修正了协议的三个实质性错误**：

| 协议原声称 | Lean 反馈结果 | 协议修正 |
|-----------|---------------|----------|
| §6：`SilentError@τ` 是 "non-decreasing in τ" | `risk_mono` 证明：`Risk` 随 τ **下降**（non-increasing） | §6 改为 non-increasing，引用 `risk_mono`；并在 Core.lean 中保留 `protocol_said_nondecreasing_is_FALSE` 由 `decide` 证伪旧句 |
| §6 "最小可采阈值最大化 coverage" | 首版定理留用了两个 `Admissible` 假设未被用到；Lean 报警告 | 重述为 **IsLeastAdmissible → 推导出顺序**，令排序**从**可采性推导而非假设；`least_admissible_maximises_coverage` 完整成立 |
| §6 未预见：小 dev 集上 budget 崩塌为 0 | `budget_collapses_to_zero_on_small_dev`：N<20 时 floor(0.05·N)=0，最小可采 τ=10 且 Coverage=0（全关门）；紧邻其下的 τ=9 **只保留错误** | §6 增加 degeneracy 条款：budget 为 0 时最小可采阈值可能是"全关门"；§4.4a 增加声明：Δτ* 可能度量的是"门何时完全关"而非选择性 limen 的移动 |

**反馈环也修正了守卫自身的三个缺陷**：(1) `check_lean_status_freshness` 报"检查了 6 项"实则静默跳过 2 项 —— 现无法推导即失败；(2) `LEAN_PATH` 少一层 `lean/`，守卫只是碰巧能用；(3) `depends on axioms: [...]` 正则漏匹配 `does not depend on any axioms`，导致 `decide` 定理（零公理）被误报为未覆盖。

**结果**：协议现在不仅声称其数学是正确的，而且声称其数学**被机器检查过，且在这个过程中被修正过**。形式化不再是附录，而是**修正协议的反馈环**。


## 7. What Phase I contributes to the global thesis

| Global thesis element | Phase I role |
|----------------------|--------------|
| Noise as normal disturbance | **Directly tested** in English |
| Control law (SilentError, coverage) | **Instrumented** via System One |
| Structural bias across scripts | **Not tested** (deferred to Phase II) |
| Feedback / accommodation | Optional later Study C |
| JEV tooling validity | **ADMITTED, not validated** — see below |

Phase I is therefore **necessary infrastructure science** for the control-systems claim, not a diluted substitute for Phase II.

> **On the last row — a wording correction that matters.** v1.1 said JEV tooling validity would be
> **"validated"** under typo stress. That is not what this programme does, and the word implies a
> research output that is not claimed. The programme's rule is a three-criterion **admission test**
> (`docs/INSTRUMENT_POSTURE.md`): **usable**, **scientific**, **reproducible** — each answered with
> evidence, and each passing means **use the component exactly as shipped**.
>
> **Admission is not validation.** A validated instrument would be an object of study, benchmarked and
> improved, which is precisely what this programme forbids: the instrument is one tool on one link of a
> pipeline. **The pilot exercised the instrument under noise; that is an exercise, not a validation.**
> The row is corrected rather than deleted so the change of posture is visible.

---

## 8. Explicit non-goals

| Non-goal | Phase |
|----------|--------|
| Claim writing-system fairness from English typos alone | I |
| Universal typo intensity across languages without justification | II |
| Confirmatory fine-tuning / QLoRA | I–II |
| Paid API dependency | I–II |
| Leaderboard Intelligence maximisation | I–II |
| Equating self-healing spelling with primary endpoints | I–II |

---

## 9. Open science

- **Two pre-registrations:** Phase I; Phase II (after Phase I freeze).  
- Release English typo generator, items (or controlled access), JSONL schema, analysis code.  
- Phase II adds $s_1$ materials under the same discipline.  
- All confirmatory model commits pinned.

---

## 10. Limitations

- Phase I generalises only to English Latin keyboard-like noise.  
- Single System One pin may not represent all JEV-ecosystem models.  
- Parallel Phase II items introduce translation/construction bias; mitigated by adjudication codebook.  
- Gating simulates allocation; not a field deployment RCT.

---

## 11. Timeline (indicative)

| Stage | Months | Output |
|-------|--------|--------|
| Phase I pre-reg + items + $\mathcal{N}_{\mathrm{en}}$ | 1–3 | Locked English bank |
| Phase I pilot + power | 3–4 | Final $N$ |
| Phase I confirmatory + report | 4–7 | H1.x results, frozen tooling |
| Phase II design + pre-reg | 7–9 | $s_1$, $\mathcal{N}_{s_1}$ |
| Phase II data + tests | 9–14 | H2.x results |
| Integrated manuscript | 14–18 | Phased narrative |

---

## 12. Phase I pre-registration checklist

The checklist as the **protocol** states it, with the current state of each item. **The protocol states
the requirement; the state column is maintained by `docs/PHASE_I_PREREGISTRATION.md` and its
amendments.** A protocol item may not be marked satisfied by a downstream document alone.

| # | Protocol requirement | State | Where decided |
|---|---|---|---|
| 1 | English only; no script factor in confirmatory tests | **FIXED** | `docs/PHASE_I_PREREGISTRATION.md` §12 |
| 2 | Typo classes and λ rates fixed | **CLASSES FIXED · λ PENDING** | O1 — needs the readability calibration, which must state *who reads* and *what counts as readable* |
| 3 | Generator seed policy | **FIXED** | pure function of `(item_id, λ, seed)`; `seeds ∈ {0,1,2}` |
| 4 | Model ID + commit + SHA256 | **FIXED** | v1.2 CHANGE 2 — `55cf4c4e…`, `config/pin_laya.json`, verified by execution |
| 5 | **$Q_0$ frozen** | **FIXED — as `intent` alone** | **v1.2 CHANGE 1.** v1.1 said `(intent, ok, escalate)`; `ok` and `escalate` are **dropped**, since the `noul` primitive measured at chance (`docs/C2_NOUL_VALIDITY.md`). This checklist entry is therefore **amended by the protocol itself**, not by a downstream note. |
| 6 | Confidence rule frozen | **FIXED** | §3.3 — `c = max_j p_j` for choice; `c = max(p, 1−p)` for noul |
| 7 | τ ∈ {0.80, 0.90}, ε = 0.05 | **FIXED** | §3.4. **`τ*` fitting rule is now stated by v1.2 CHANGE 3.** |
| 8 | Dev/test split by item | **FIXED** | 30/70 by `item_id` |
| 9 | Primary endpoints H1.1–H1.3 | **FIXED** | §4.4; co-primaries are H1.2 and H1.3 |
| 10 | FAILURES policy | **FIXED** | every attempted trial recorded; failures logged, never dropped |
| 11 | No confirmatory training | **FIXED** | θ frozen; no fine-tuning, no QLoRA, no adapter |
| 12 | Cross-script claims reserved for Phase II | **FIXED** | §0.2, §5.2; §5.1 gates Phase II |
| — | **Item bank** | **BUILT** (932 items, gold a construction invariant) | O3 — human pass still outstanding |
| — | **N_item** | **FROZEN: N_test = 652** | O2, with Erratum 1 — the corrected π_d is 0.1833; 652 is conservative |

**The seal is blocked by exactly two things:** O1 (the λ readability calibration) and O3's human pass.

---

## 13. Minimal Phase I runbook

```text
1. Pin System One checkpoint
2. Build English intent items + gold
3. Generate x(item, λ∈{0,lo,mid}, seed) via N_en
4. predict(state=x, questions=Q0) → JSONL
5. Fit τ* on dev if using Coverage@0.05
6. Test H1.1–H1.3 on locked test
7. Freeze all artifacts before any Phase II work
```

---

## 14. Document control

| Field | Value |
|-------|--------|
| **Role** | **THE PROGRAMME'S GLOBAL ANCHOR.** All other documents are subordinate; see the note at the head of §0 |
| Version | **1.3** |
| v1.3 changes | (1) **LIMEN** named as the gate's threshold (§0.3), with four things the name explicitly does not assert; (2) the **thesis, mechanism, objective and non-claim** stated directly (§0.4), with a constraint on how the objective may be worded per phase; (3) the **limen-shift diagnostic** $\Delta\tau^\star$ added as a **reported, non-confirmatory** quantity (§4.4a); (4) §3.4 states exactly what the gate reads. **Additive only — no frozen value moved and no confirmatory endpoint was added.** |
| v1.2 changes | (1) `Q0` is `intent` alone; (2) the pin is decided — Laya English root at `55cf4c4e…`; (3) the `τ*` fitting rule is stated, including when it yields nothing |
| Staging | **Phase I English typo → Phase II cross-script** |
| Primary DVs (I) | Acc, SilentError@τ, Coverage@ε vs $\lambda$, **all over `intent`** |
| Primary DVs (II) | Script × noise interaction; cross-channel SilentError / coverage |
| Named quantity | **LIMEN** $= \tau$, the argument of $g_\tau$. Fixed probes $\tau \in \{0.80, 0.90\}$; fitted $\tau^\star_\varepsilon$; their shift $\Delta\tau^\star$ is **reported, not confirmatory** |
| Tooling | One JEV-compatible System One component, **admitted on three criteria and used as shipped** — not validated, not tuned |
| Thesis | Coupled control under normal orthographic disturbance; structural bias tested only from Phase II |
| Anchor identity | sha256 recorded in `config/anchor.json`, verified by `scripts/check_anchor.py` |

---

*End of protocol v1.3*
