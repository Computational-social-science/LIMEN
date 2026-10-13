# The unavoidability premise: what it needs, what it has, and what is still open

**The programme rests on the premise that human keyboard-input noise reaches the model in the LLM era.** A
foundational premise that is only asserted is a logical suspension, so this file decomposes it, states the
evidence type each part needs, and records where the evidence is missing. **Written after an audit that found
five suspensions, two of which were introduced by an earlier draft of the very experiment meant to resolve them.**

---

## 1. The premise, decomposed

**The premise as it was stated — "human keyboard-input noise is unavoidable in the LLM era" — mixes four claims
of different kinds, and only one of them is testable today.**

| | Claim | Kind of evidence required | Status |
|---|---|---|---|
| **P1** | Human keyboard input contains errors | **measurement** | **ESTABLISHED** — Birkbeck 36,133; CSCD-NS 15,143; JWTD 242,885 |
| **P2** | Those errors reach the model | **architectural fact** | **ESTABLISHED** — an LLM chat path passes the raw text through; there is no correction layer between the user and the model |
| **P3** | The LLM-era input stack does not remove them | **measurement** | **PARTLY** — see §3 |
| **P4** | They will continue to | **forecast, not measurement** | **NOT TESTABLE TODAY** |

**The consequence, which is the point of this file.** **P4 cannot be "strongly confirmed" by any experiment run
now**, and dressing a forecast as a measurement is the failure mode this programme's rules exist to prevent. **But
the premise does not need P4**, because its strongest form is present-tense: **the noise that reaches the model is
real and its detectability is script-dependent** — P1 plus P2 plus P3, all measurable now.

## 2. The five suspensions the audit found, and their repairs

**S1 — the proposed survival experiment is CIRCULAR on the logographic arm.** CSCD-NS records errors **that an
input method produced**; feeding them back into an input method to ask whether it would remove them asks a
question whose answer is fixed by construction. **REPAIRED: the experiment is deleted.** The Chinese question is
not "would an IME remove this" but **"is this error detectable from the glyph stream"** — which the measured
**81.4 % same-romanisation share already answers**.

**S2 — the experiment measured MITIGATION, not unavoidability.** "Could hypothetical automation remove it" is not
"does it reach the model". **REPAIRED: deleted; P2 is stated as the architectural fact it is.**

**S3 — "the current LLM correction layer" is undefined and does not exist on the path being studied.** In an LLM
chat interface the user's raw text goes to the model. **REPAIRED: P2 reclassified from an experiment to an
architectural fact.**

**S4 — the claimed link to H2.2 was unsupported.** H2.2 concerns the **model's own confidence gate**, a
behavioural property; a correction-layer survival rate says nothing about it. **REPAIRED: the link is withdrawn.
H2.2 is tested only by measuring the gate.**

**S5 — the English arm's corpus PREDATES the LLM era, so the English evidence did not match the premise's
tense.** Birkbeck is a corpus of 1980s–90s children's misspellings. **This was not previously flagged.**
**REPAIRED: see §3.**

## 3. S5's repair: an LLM-era corpus covering all three channels

**GitHub Typo Corpus** (Hagiwara & Mita, LREC 2020; `mhagiwara/github-typo-corpus`) — **more than 350,000 edits
and 65 million characters across 15+ languages, harvested from GitHub commits from 2018 onward**, i.e. **inside
the LLM era**.

**And it covers the programme's three channels**: the authors provide the typo-specific keys `prob_typo`,
`is_typo` and `ppl` **for English (`eng`), Simplified Chinese (`cmn-hans`) and Japanese (`jpn`)** — "the three
largest languages in the dataset". **So it supplies a second, independent, contemporary observed corpus for every
arm of the programme**, not merely a repair for the English one.

**Two limitations that travel with it, stated rather than discovered later.**

1. **Its licence is not clean.** The project states that "the copyright and license terms of the individual
   commits and texts contained in the dataset follow the terms of the repositories they belong to" — **so the
   corpus is not redistributable as a unit**, and any use must respect the underlying repositories' terms. It is
   usable for measurement; it is not usable as a redistributed artefact.
2. **Its register is software commits**, not conversational input. **It is closer in time to the LLM era than
   Birkbeck is, and further in register from chat.** That is a real trade and it is why the corpus enters as a
   **cross-check on the error's morphology** rather than as a drop-in replacement for the channel's corpus.

## 4. What the cross-check can and cannot decide

**What it decides**: whether the **morphology** of English typing errors — the distribution over substitution,
insertion, deletion and transposition, and the non-word versus real-word split — **has changed between the
pre-LLM-era corpus and a 2018-onward one.** If it has not, the mechanism is era-independent and only the rate
could have moved, which is exactly what P3 needs to be defensible.

**What it cannot decide**: the current rate under LLM-assisted input on a current device. **No corpus measures
that, and the premise does not require it** once the mechanism is shown to be stable and the architectural fact
P2 holds.

## 5. The premise, in its defensible present-tense form

> **Text that people type carries errors (P1, measured); those errors reach the model without an intervening
> filter (P2, architectural); and the share of them that is detectable from the input alone is a function of the
> script — measured at 93.6 % loud in English and 81.4 % trace-free in Chinese (P3, measured here).**

**P4 — that this persists — is a forecast. It is stated as one, with its basis, and it is not used as evidence.**
**The programme's motivation does not depend on it**: a study of how confidence-gated behaviour degrades under
script-dependent noise is about the mechanism the measurements above establish, and it is worth doing whether the
rate rises, holds or falls.
