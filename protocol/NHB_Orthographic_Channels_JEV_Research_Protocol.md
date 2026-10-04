# Orthographic Channels and Input Noise as Structural Disturbances in Human–Model Interaction

## A Pre-Registered, Phased Protocol Integrating System One / JEV-Ecosystem Tooling

**Document type:** Detailed research protocol (*Nature Human Behaviour*–oriented framing)  
**Version:** 1.2 (English typo first, then cross-script / multilingual expansion)  
**Status:** Draft for staged pre-registration  
**Compute envelope:** Single consumer GPU admissible; zero paid API on confirmatory path  
**Primary interface class:** Typed decision models (System One):  
\(\texttt{state} \times \texttt{questions} \mapsto\) distributions over caller-defined options  

> **v1.2 records three decisions that earlier work had already made.** The protocol is the research
> objective, so a change to it may not be made only in a downstream document — if an amendment
> contradicts the protocol, the protocol is what must move. **The three changes are marked
> `v1.2 CHANGE` at the point they apply**, and each names the amendment that motivated it. They are
> the *only* substantive changes from v1.1; nothing else in the design moved.  

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

**Rule:** Phase II pre-registration is filed **only after** Phase I instruments (items, \(\mathcal{N}_{\mathrm{en}}\), logging, gates) are frozen and pilot-stable. Phase I must not be re-opened to “hunt” interactions after seeing Phase II.

---

## 1. Formal system model

### 1.1 Interaction cycle

| Symbol | Domain | Meaning |
|--------|--------|---------|
| \(i\) | intention space | User communicative / task intention |
| \(s \in \mathcal{S}\) | orthographic channels | Phase I: \(s = s_{\mathrm{en}}\) only; Phase II: \(s \in \{s_{\mathrm{en}}, s_{1}, \ldots\}\) |
| \(n \sim \mathcal{N}_s(\lambda)\) | noise process | Channel-specific; Phase I uses \(\mathcal{N}_{\mathrm{en}}\) only |
| \(\lambda \in \{0, \lambda_{\mathrm{lo}}, \lambda_{\mathrm{mid}}\}\) | intensity | Pre-registered rates |
| \(x \in \Sigma^*\) | symbol string | Observed state text |
| \(q \in \mathcal{Q}\) | typed questions | System One choice / noul / (optional) score |
| \(f_\theta\) | decision model | Frozen System One parameters in confirmatory tests |
| \(\mathbf{p}\) | simplex | Option probabilities |
| \(c \in [0,1]\) | confidence | Fixed functional of \(\mathbf{p}\) |
| \(a \in \mathcal{A}\) | action | \(\{\mathrm{answer}, \mathrm{defer}, \mathrm{escalate}, \mathrm{refuse}\}\) |
| \(g_\tau\) | gate | Pre-registered map \((\mathbf{p},c)\mapsto a\) |

**Encoding:**
\[
x = E(i, s, n), \qquad n \sim \mathcal{N}_s(\lambda).
\]

**System One map (JEV-compatible):**
\[
(\mathbf{p}, c) = f_\theta(x, q).
\]

**Control:**
\[
a = g_\tau(\mathbf{p}, c).
\]

**Normal disturbance:** ecologically relevant regime has \(\lambda > 0\); \(\lambda = 0\) is a boundary probe.

**Structural bias (full thesis, Phase II):** for matched \(i\) and comparable \(\lambda\), laws of \((\mathbf{p},c,a)\) differ across \(s\) beyond sampling error.

**Phase I restriction:** \(s\) fixed to English; estimands are functions of \(\lambda\) only (and optional model/router contrasts within English).

---

## 2. Why Phase I anchors on English typos

| Reason | Implication |
|--------|-------------|
| **Process validity** | English keyboard typo models (adjacency, transposition, deletion, insertion) are well-specified and reusable (e.g., MulTypo-style Latin layouts) |
| **Label quality** | Intent gold and inter-annotator agreement are cheapest and most stable in English first |
| **Instrument debug** | JSONL schema, confidence rule, gates \(g_\tau\), and System One wiring are validated before multilingual complexity |
| **Literature bridge** | Connects to existing LLM typo-robustness results while shifting DVs to **SilentError** and **coverage** under System One |
| **Avoid false cross-script claims** | Forbids treating “English typo intensity” as universal \(\lambda\) across scripts |

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
| Training | **Frozen** \(\theta\) in Phase I–II confirmatory arms |
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

- Choice: \(c = \max_j p_j\)  
- Noul: \(c = \max(p,\,1-p)\)  

### 3.4 Primary gate

\[
g_\tau:\quad
a = \begin{cases}
\mathrm{answer}(\arg\max \mathbf{p}) & c \ge \tau \\
\mathrm{defer} & c < \tau
\end{cases}
\]
with \(\tau \in \{0.80,\,0.90\}\) pre-registered; Coverage@\(\varepsilon=0.05\) uses \(\tau^\star\) fit on **dev only**.

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
| Noise \(\lambda\) | \(0\), lo, mid |
| Item | \(N\) English intent scenarios (within-item across \(\lambda\)) |

No script factor in confirmatory Phase I.

### 4.2 English typo process \(\mathcal{N}_{\mathrm{en}}\)

Allowed edit classes (pre-register subset):

1. Adjacent-key substitution (QWERTY)  
2. Character transposition  
3. Deletion  
4. Insertion (adjacent or random from alphabet)  

**Intensity:** target mean edits per token or per character  
- \(\lambda_{\mathrm{lo}}\): e.g. ~5–8% character corruption  
- \(\lambda_{\mathrm{mid}}\): e.g. ~12–18%  

Exact rates fixed in pre-registration after a short calibration so that items remain human-readable at lo and stressed at mid. Generator: deterministic in `(item_id, λ, seed)`.

**Out of scope for Phase I:** OCR noise, ASR noise, full-word substitution, adversarial misspellings aimed at jailbreaks, non-English code-switching.

### 4.3 Stimuli

- Domain: short service / routing intents (billing, access, urgency, info).  
- \(N_{\mathrm{item}}\): set by power for detecting mid vs clean error increase (and SilentError@0.9 increase) of ≥5 absolute points at 80% power.  
- Gold: locked English labels for `intent` (and noul keys if used as primary).  
- Split: ~30% dev / ~70% test by item_id.

### 4.4 Phase I hypotheses

- **H1.1:** \(\mathrm{Acc}(\lambda_{\mathrm{mid}}) < \mathrm{Acc}(0)\) on test.  
- **H1.2:** \(\mathrm{SilentError@}0.9(\lambda_{\mathrm{mid}}) > \mathrm{SilentError@}0.9(0)\).  
- **H1.3:** Under dev-fit \(\tau^\star\) at \(\varepsilon=0.05\), \(\mathrm{Coverage}(\lambda_{\mathrm{mid}}) < \mathrm{Coverage}(0)\) on test **or** error among accepted rises (pre-register which is co-primary).

**Interpretation if supported:** typo noise is a material disturbance of System One **understanding and control**, not merely a generation nuisance.  
**Interpretation if H1.1 holds but H1.2 fails:** errors rise but confidence tracks—control law partially healthy.  
**Phase I does not** establish structural bias across writing systems.

### 4.5 Phase I analysis

- Paired / mixed models with item random intercepts; factor \(\lambda\).  
- Bootstrap CIs on SilentError and Coverage contrasts.  
- Pre-register Holm across H1.1–H1.3 family as defined in the OSF entry.

### 4.6 Phase I deliverables

Frozen: item bank, \(\mathcal{N}_{\mathrm{en}}\), model pin, JSONL, analysis notebook, FAILURES log, short report.

---

## 5. Phase II — Cross-script / multilingual extension

### 5.1 Entry criteria (gates from Phase I)

Phase II begins only if:

1. Phase I pipeline error rate (tooling failures) < pre-set bound;  
2. \(\mathcal{N}_{\mathrm{en}}\) and labels stable under independent re-run;  
3. New pre-registration filed for Phase II hypotheses (no retroactive change to Phase I).

### 5.2 Design

**Factors**

| Factor | Levels |
|--------|--------|
| Channel \(s\) | \(s_{\mathrm{en}}\), \(s_1\) (one primary contrast) |
| Noise \(\lambda\) | \(0\), lo, mid (**channel-specific** generators) |

**Critical rule:** \(\lambda\) levels are **not** equated by “same edit rate as English” alone. Equivalence is justified by (a) human pilot difficulty, or (b) documented empirical error rates per channel, stated in Phase II pre-registration.

### 5.3 Channel \(s_1\) selection criteria

Choose **one** of:

- Non-Latin script with documented digital input confusions; or  
- Same language family but distinct orthographic standard; or  
- IME-mediated input ecology (e.g., conversion errors),

with: (i) ability to build parallel intentions; (ii) annotators; (iii) a **faithful** \(\mathcal{N}_{s_1}\).

**Forbidden:** implementing \(\mathcal{N}_{s_1}\) as “run English typo ops on transliterated text” as the sole noise model.

### 5.4 Phase II hypotheses (full structural thesis)

- **H2.1:** Script × noise interaction on error (mid vs clean deltas larger for \(s_1\) than \(s_{\mathrm{en}}\), or pre-registered directed form).  
- **H2.2:** SilentError@0.9 contrast \((s_1,\lambda_{\mathrm{mid}}) - (s_{\mathrm{en}},\lambda_{\mathrm{mid}}) > 0\).  
- **H2.3:** Coverage@0.05 disparity under the same gating discipline as Phase I.

Optional mechanism arm: router `forced_en` vs `forced_multi` vs `auto` under \(s_1\) inputs.

### 5.5 Models in Phase II

- Keep Phase I pinned model as backbone when possible.  
- If multilingual checkpoint / router is required for \(s_1\), pin it explicitly; report English cells under the **same** artifact for comparability, plus a sensitivity run with Phase I English-only pin on English cells only.

---

## 6. Metrics (both phases)

\[
\mathrm{Acc}(s,\lambda) = 1 - \frac{1}{|\mathcal{T}|}\sum \mathbb{1}\{\hat y \neq y^\star\}
\]

\[
\mathrm{SilentError@}\tau(s,\lambda) = \frac{1}{|\mathcal{T}|}\sum \mathbb{1}\{\hat y \neq y^\star \wedge c \ge \tau\}
\]

\[
\mathrm{Coverage@}\varepsilon(s,\lambda) = \frac{|\{x: c(x)\ge \tau^\star_\varepsilon\}|}{|\mathcal{T}|}
\]

Phase I omits \(s\) (always \(s_{\mathrm{en}}\)).

> **v1.2 CHANGE 3 — the fitting rule for \(\tau^\star\) is stated, including the case where it does not
> exist.**
>
> v1.1 said only "fitted on dev" and never said *which* threshold is reported when several meet the
> budget. **An admissible threshold is never unique:** `Risk(τ)` is monotone non-increasing in τ, so if τ
> meets the budget then every τ′ ≥ τ meets it too. The admissible set is upward closed and typically has
> no distinguished element. **This is not hypothetical** — the pilot's clean `SilentError@0.9` was
> **0/120**, making `Risk(τ) = 0` across the whole grid and *every* τ admissible.
>
> **The rule:** \(\tau^\star_\varepsilon\) is the **least admissible threshold**, i.e. the loosest gate
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
> Authority: `docs/PHASE_I_AMENDMENT_2.md` §B1.

---

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
- Phase II adds \(s_1\) materials under the same discipline.  
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
| Phase I pre-reg + items + \(\mathcal{N}_{\mathrm{en}}\) | 1–3 | Locked English bank |
| Phase I pilot + power | 3–4 | Final \(N\) |
| Phase I confirmatory + report | 4–7 | H1.x results, frozen tooling |
| Phase II design + pre-reg | 7–9 | \(s_1\), \(\mathcal{N}_{s_1}\) |
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
| 5 | **\(Q_0\) frozen** | **FIXED — as `intent` alone** | **v1.2 CHANGE 1.** v1.1 said `(intent, ok, escalate)`; `ok` and `escalate` are **dropped**, since the `noul` primitive measured at chance (`docs/C2_NOUL_VALIDITY.md`). This checklist entry is therefore **amended by the protocol itself**, not by a downstream note. |
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
| Version | **1.2** |
| v1.2 changes | (1) `Q0` is `intent` alone; (2) the pin is decided — Laya English root at `55cf4c4e…`; (3) the `τ*` fitting rule is stated, including when it yields nothing. Nothing else moved from v1.1 |
| Staging | **Phase I English typo → Phase II cross-script** |
| Primary DVs (I) | Acc, SilentError@τ, Coverage@ε vs \(\lambda\), **all over `intent`** |
| Primary DVs (II) | Script × noise interaction; cross-channel SilentError / coverage |
| Tooling | One JEV-compatible System One component, **admitted on three criteria and used as shipped** — not validated, not tuned |
| Thesis | Coupled control under normal orthographic disturbance; structural bias tested only from Phase II |
| Anchor identity | sha256 recorded in `config/anchor.json`, verified by `scripts/check_object_drift.py` |

---

*End of protocol v1.2*
