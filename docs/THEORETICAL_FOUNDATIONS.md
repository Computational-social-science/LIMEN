# Theoretical foundations — the classical frame, and exactly what it changes

**Owner's directive (2026-10-04):** Shannon's noisy-channel coding theorem and the cybernetics classics
are foundational reference frames for this programme.

**This document does one thing: it maps the protocol's constructs onto that frame one-to-one, states
what the frame *adds*, and states what it does *not* license.** A frame that only decorates an
introduction is worse than none — it invites a reviewer to ask what the theory bought. So every section
ends in a concrete change to the protocol or an explicit refusal to make one.

---

## 1. The frame, stated correctly

**Shannon (1948), noisy-channel coding theorem.** For a channel with capacity `C`, a message `W` is
encoded to `Xⁿ`, transmitted through `p(y|x)`, and decoded to `Ŵ`; error is `P_e = Pr{Ŵ ≠ W}`. If the
rate `R < C`, codes exist making `P_e` arbitrarily small; if `R > C`, no code can — every code has a
positive minimal error that grows with `R`.

**Ashby (1956), law of requisite variety.** Only variety can absorb variety: a regulator must be able
to take at least as many distinguishable states as the disturbance it must counter.

**Conant & Ashby (1970).** *"Every good regulator of a system must be a model of that system."*
*Int. J. Systems Science* **1**: 89–97. **Status, stated properly:** this is a theorem about an optimal
regulator under stated assumptions, not a universal law. The more accurate statement of the conclusion
is that a good regulator must **contain or have access to** a model of the regulated system, and its
generality has been questioned in the literature. The frame is being **revived**, not merely cited
historically — e.g. *A 'good' regulator may provide a world model for intelligent systems*, Phil.
Trans. R. Soc. A **384**: 20250007.

**Wiener (1948).** Control and communication are one subject: a feedback loop carrying information
through a noisy medium.

## 2. The mapping — one row per construct, no hand-waving

| Classical object | Our object | Where it is defined |
|---|---|---|
| Intention `i` | the user's communicative/task intention | protocol §1.1 |
| **Encoder** `E(i, s, n)` | **the user's typing under a writing system `s` and keyboard noise `n`** | protocol §1.1 |
| **Channel** `p(y\|x)` | **the tuple (model `f_θ`, orthographic channel `s`, noise intensity `λ`)** | protocol §1.1, §3.2 |
| **Received sequence** | the model's own state encoding of `x` | `f_θ` |
| **Decoder** `g` | **the gate `g_τ` followed by `argmax`** | protocol §3.4 |
| `P_e` | **`SilentError@τ`** — the decoded answer is wrong *and* the gate let it through | protocol §6 |
| **Rate `R`** | **`Coverage@ε`** — the share of items the gate chooses to answer | protocol §6 |
| **Capacity `C`** | **not directly observable; the rate beyond which `SilentError` cannot be held at ε** | this document |
| Noise `n` | keyboard-faithful typo process `N_s(λ)` | protocol §4.2 |

**The mapping is not decorative — it is close to exact.** `Coverage` and `SilentError` are the
coordinates of a rate-versus-residual-error operating point, and `τ` is the parameter that slides the
system along that curve. **That is what the protocol was measuring without saying so.**

## 3. What the frame adds — four concrete changes

### C-1. The gate becomes a code, and the DV pair gets a derivation

Today the protocol asserts `SilentError@τ` and `Coverage@ε` as chosen metrics. Under the frame they are
**derived**: they are the rate and the residual error of the operating point the gate selects. This
matters because it explains *why* `τ` must be pre-registered and why `τ*` must be fitted **on dev
only**: fitting `τ*` on the test set is choosing the operating point after seeing the curve — which in
coding terms is selecting the code after seeing which messages failed.

**Change:** §6 of the protocol gains one sentence deriving the pair, replacing the current bare
definition. No new measurement.

### C-2. The estimand becomes a curve, not two points

The frame's natural object is the **rate–error curve** of a channel, and the capacity is where that
curve dies. Two pre-registered τ values give two points on it. **Reporting the full curve per channel
costs nothing** (the JSONL already carries `p` per item) and makes the Phase II comparison geometric
rather than pointwise.

**Change:** add `rate_error_curve` as a reporting artefact — for each (channel, λ), the curve over a
grid of τ. **Report-only; no endpoint changes.** This is the single most valuable thing the frame buys,
because it converts a search for two significant differences into a comparison of two functions.

### C-3. 🔑 The surviving gap gets its precise form: parallel or crossing?

The gap audit (`docs/GAP_VERDICT.md`) left one claim standing: *does noise re-rank channels?* The frame
sharpens this beyond what either the protocol or the audit could state:

> **For each orthographic channel `s` and noise level `λ`, the model defines a rate–error curve
> `R_s(λ)`. Two classical possibilities partition the space:**
> - **parallel shift** — noise moves every channel's curve down by a similar amount; the channel
>   *ordering* is preserved. Channel differences are then a static property (consistent with the
>   published "script tax" picture), and noise is a scalar tax on top of it.
> - **crossing / re-ordering** — noise changes which channel sits higher. Channel differences are
>   then **regime-dependent**, and any static channel ranking is invalid outside the regime it was
>   measured in.
>
> **The programme's claim is the second, and it is falsifiable by a crossing test on the fitted curves.**

This is what the frame adds that the literature search could not: a **geometric criterion**. The
literature established static channel costs and static gating disparity; a capacity-ordering analysis
under perturbation is a different question, and "crossing" is the exact name of the answer we are after.

### C-4. Ashby and Conant–Ashby convert two of our hypotheses into *predictions with direction*

- **Requisite variety.** The gate is a regulator whose variety is set by `τ` (a scalar). The disturbance
  has variety set by `λ` and by the channel's input ecology. **Prediction:** the control law should fail
  *more* on the channel with greater disturbance variety — i.e. the interaction in H2.1/H2.3 should be
  *directed*, not merely non-zero. The protocol currently pre-registers H2.1 without a direction; the
  frame supplies one.
- **Conant–Ashby.** A regulator that is a good model of the system it regulates has confidence that
  tracks competence. **`SilentError@τ` is precisely the empirical size of the gap between the
  regulator's model of itself and its actual behaviour.** So our DV is not an ad-hoc reliability metric;
  it is the measured violation of the good-regulator property, and `H1.2` becomes: *does noise degrade
  the regulator's model of itself?* That is a sharper and more citable framing than "confidence does not
  track errors".

**Change:** §1 and §4.4 of the protocol gain the directional form for the Phase II interaction and the
good-regulator framing for H1.2. **Pre-registration is not yet sealed, so a directional hypothesis can
still be filed** — but it must be filed now, not after seeing Phase I.

## 4. What the frame does *not* license — the refusals

1. **It does not supply the empirical content.** Shannon's theorem is about the existence of codes, not
   about what a specific model does. **Nothing about an LLM's typo behaviour follows from it.** The
   frame organises the hypotheses; it cannot be cited as evidence for any of them.
2. **It does not make capacity measurable by definition.** `C` in our setting is not a number we can
   compute from channel properties; it is at best an extrapolated asymptote of a measured curve. **Any
   use of the word "capacity" in the manuscript must be qualified as "effective capacity estimated from
   the observed rate–error curve", or dropped.**
3. **It does not rescue Phase I.** Phase I remains instrument validation for the interaction test. The
   frame makes the *interaction* well-posed; it does not make a main effect novel.
4. **It does not license dropping the empirical pre-emptions.** `docs/GAP_VERDICT.md` stands unchanged:
   the "confidently wrong bypasses abstention" and "gating magnifies disparity" mechanisms are
   published, and the manuscript must concede them regardless of how elegantly the theory is framed.
5. **Requite-variety is a law about what is *possible* for a regulator, not a claim about what this
   model does.** Used as a direction prediction it is fine; used as an explanation it would be
   post-hoc storytelling.

## 5. What this changes in the repo, concretely

| Artefact | Change |
|---|---|
| `protocol/…Protocol.md` | §6 gains the derivation sentence; §1/§4.4 gain the directional Phase II form; a "theoretical frame" subsection is added **in the amendment, not by editing the frozen protocol text** |
| `docs/GAP_VERDICT.md` | the surviving claim is restated as the **parallel-versus-crossing** test (§C-3) — this supersedes the looser "does noise re-rank channels" phrasing |
| `docs/REGISTERED_REPORT_STAGE1.md` | a short theory section with the table of §2; `H1.2` reframed via Conant–Ashby; the full rate–error curve added to the reporting plan |
| `docs/ITEM_BANK_SPEC.md` | unaffected |
| Reporting | new artefact `rate_error_curve` per (channel, λ); report-only |

**One caution on scope.** This frame is *already the protocol's own framing* ("coupled control system",
"normal disturbances" — §0.1). The work here is to make it **load-bearing and quantified** rather than
rhetorical. Where the frame cannot be made load-bearing, it should be cut rather than cited.

## Sources

- Shannon, C. E. (1948). *A Mathematical Theory of Communication*. Bell System Technical Journal
  **27**(3): 379–423. doi:10.1002/j.1538-7305.1948.tb01338.x
- Wiener, N. (1948). *Cybernetics: or Control and Communication in the Animal and the Machine*. MIT Press.
- Ashby, W. R. (1956). *An Introduction to Cybernetics*. Chapman & Hall.
- Conant, R. C., & Ashby, W. R. (1970). *Every good regulator of a system must be a model of that
  system*. International Journal of Systems Science **1**: 89–97.
- Cover, T. M., & Thomas, J. A. (1991). *Elements of Information Theory*. Wiley.
- MacKay, D. J. C. (2003). *Information Theory, Inference, and Learning Algorithms*. CUP. (free online)

**Retrieval note.** The Conant–Ashby attribution and the "contains or has access to" qualification were
verified by retrieval on 2026-10-04, including the Royal Society's 2026 revival
(`Phil. Trans. R. Soc. A` **384**: 20250007). The Shannon statement is from the standard statement of
the theorem. **No claim in this document rests on a secondary summary**; where a source could not be
retrieved it is not cited.
