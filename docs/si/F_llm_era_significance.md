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
