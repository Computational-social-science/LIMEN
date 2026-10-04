# Orthographic Channels and Input Noise as Structural Disturbances in Human–Model Interaction

> **A pre-registered, phased protocol integrating System One / JEV-ecosystem tooling.**
> Version 1.1 — English typos first, then cross-script expansion.

**Read `CURRENT_OBJECT.md` before doing anything here.** It is the single authority on the live
object, the retirements, and the drift signals. This file only introduces the object.

---

## The question

Human–model language interaction is a **structurally biased coupled control system**, and writing
systems and input noise are **normal disturbances**, not exceptions. Typed decision models make the
**control law** — confidence-gated action — directly observable and programmable.

The programme therefore asks, in order:

1. **Phase I.** Under English orthography, is keyboard-faithful typo noise a material disturbance of
   a typed-decision model's **understanding and control** — not merely a generation nuisance?
2. **Phase II.** For matched intentions and comparable noise intensity, do the laws of
   \((p, c, a)\) differ across orthographic channels beyond sampling error?

The long-run target is cross-script structural bias. It is **not** claimed in Phase I.

## Why the phasing is not a convenience

Noise processes, gold labels and power calculations are **channel-specific**. Equating noise across
scripts by "same edit rate as English" is explicitly forbidden (§5.2 of the protocol). Phase II's
pre-registration is filed **only after** Phase I instruments are frozen, and Phase I is never
re-opened to hunt interactions once Phase II results exist.

## What is measured

Plain accuracy is not the endpoint. The protocol's estimands are the **control law's**:

| Quantity | Definition |
|---|---|
| \(\mathrm{Acc}(\lambda)\) | share of test items answered correctly, against noise intensity \(\lambda\) |
| \(\mathrm{SilentError@}\tau(\lambda)\) | share that are **wrong and confident** — \(c \ge \tau\) on a wrong answer |
| \(\mathrm{Coverage@}\varepsilon(\lambda)\) | share answered while holding accepted-item error at \(\le \varepsilon\) |

with the frozen confidence rule (choice: \(c = \max_j p_j\); noul: \(c = \max(p, 1-p)\)) and the gate
\(g_\tau\): answer when \(c \ge \tau\), otherwise defer. \(\tau \in \{0.80, 0.90\}\) is pre-registered;
the \(\tau^\star\) used for coverage is fitted **on dev only**.

## The interface

A typed decision model — one forward pass, a distribution over the options of a typed question about
a document, and no generated text:

```text
state:     <English text, clean or typo-perturbed>
questions: {
  intent:   { type: "choice", instructions: "...", criteria: { ... } },
  ok:       { type: "noul",   instructions: "Is the request clear enough to act on?" },
  escalate: { type: "noul",   instructions: "Should a human handle this?" }
}
→ probs, conf per question id
```

## What Phase I does not do

The protocol names its own non-goals, and they bind this repository:

- no confirmatory fine-tuning or QLoRA — the confirmatory arms **freeze θ**;
- no paid API on the confirmatory path; local inference only;
- no writing-system claim from English evidence;
- no universal \(\lambda\) across languages without justification;
- no leaderboard maximisation.

## Where things are

| Path | What |
|---|---|
| `CURRENT_OBJECT.md` | **The authority.** Live object, retirements, drift signals. |
| `protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md` | The protocol in full (v1.1). |
| `docs/` | Working notes for the live object. |
| `measurement/`, `scripts/`, `config/`, `paths.py` | Live instruments carried over from earlier work; `CURRENT_OBJECT.md` names each one's role. |
| `archive/` | Retired objects, kept as records. **Not targets.** |

## Status

**Not yet started.** The protocol is a draft for staged pre-registration. As of 2026-10-04 there is no
pinned checkpoint with a recorded commit and SHA256, no item bank, no `N_en` typo generator, no JSONL
and no analysis. The work ahead is §13 of the protocol.

## Licence and provenance

Code MIT. The protocol is this repository's own work. Where the programme integrates JEV-ecosystem
tooling it reuses interfaces and public data, and claims none of that ecosystem's work as its own;
each reused artefact is named where it is used. No number from generated text may enter a claim —
every external number carries a source.
