# The scientific spine this study was missing

*Written after a review that asked three questions and was right on all three. It is kept in the repository
because the answers are the part of the record that is most easily lost.*

---

## 0. The diagnosis, stated as measurements rather than as apology

The review asked why the documents do not hold the title, why the formalization produced no findings, and why
the prose is empty of substance. Each is measurable in the documents themselves.

**The title's central term does not appear in the study.** `participant`: 0. `user`: 0. `human reader`: 0. The
title promises *structure in human–model interaction*; the experiment has no human in it. The one human result
it uses — Rayner et al. (2006) — is a **calibration anchor**, not a measurement made here.

**The body names two works, and neither is domain content.** Holm (1979) and McNemar (1947): both are
statistical machinery. The six works in the reference list are cited *at* the reader, not engaged.

**There is no gap.** `gap`: 0. `contradict`: 0. `inconsist`: 0. `unresolved`: 0. `remains unclear`: 0. The
document never says what the field believes, what is missing, or what would change if this study is right.

### The mechanism that produced it

**The work was executed first and claimed last.** A harness was built, guarded, and rendered; a protocol was
inherited from an earlier object and its title carried forward; and at no point was the title **audited against
what the study can support**. Execution-first is not laziness — every individual artefact is careful — but it
places the claim downstream of the machinery, where it inherits whatever the machinery happens to do. The
empty fields above are not three defects. They are one defect seen from three sides: **no one ever had to
write down what would have to be true for the title to be earned.**

A second mechanism compounds it. **The formalization was filed as quality control.** Twenty-seven kernel-checked
theorems appear in the record as corrections to a protocol and as evidence for a design choice — as
*infrastructure*. Several of them are not that. They are statements about the field's measurement practice, and
they were never promoted.

---

## 1. The title, earned rather than asserted

*"Orthographic channels and input noise as structural disturbances in human–model interaction."*

For this to be true rather than decorative, three things must hold, and each can be written down and checked.

**(i) The disturbance must be structural — a property of the interface, not of either party.** It is. Typing
errors are produced by the human's keyboard, not by the model, and they are not authored deliberately: they are
what the channel does. The model receives them as data and cannot distinguish them from intent. So a typed
request is a **noisy channel** in the technical sense — an intended symbol destroyed by the medium between the
parties — and the noise is a property of the *pairing*, which is why it is a structural disturbance and not a
model defect or a user defect.

**(ii) The human must be in the loop in a way that can be located.** The human appears at exactly two points,
and both are the parts of the design an earlier draft left implicit:

- **At the input**, as the origin of the disturbance. This is what the channel models, and it is why the noise
  generator is *keystroke-faithful* rather than uniformly random: a channel model that does not respect the
  medium's actual error structure is not a model of that channel.
- **At the output**, as the **consumer of the deferral**. A deferral is not a null result — it is work returned
  to the human, and its cost is human time. This is the sense in which coverage is a *human-facing* dependent
  variable, and it is the reason the study's central finding (damage lands in coverage, not in committed
  correctness) is a statement about the interaction rather than about a classifier.

**(iii) The interaction must be the unit of analysis, not an afterthought.** The gate is the interface: it is
where the model's self-assessment is converted into an action that the human experiences. Studying the gate
*is* studying the interaction — but only if the deferral is priced as the human cost it is, and only if the
noise is the human's noise. Both are now explicit.

**What this does not license.** It does not license the word "interaction" as a substitute for human data. This
study measures **the model-side half** of the interface under a **human-derived** disturbance. A claim about
how humans *respond* to a rising deferral rate is a different study, and the obvious next one.

---

## 2. The gap, with the literature named

Two mature literatures do not meet.

**The first measures the damage and stops at the aggregate.** Typo-robustness work is well developed: MulTypo
(arXiv:2510.09536) evaluates 18 open-source models across five tasks and finds that typos consistently degrade
performance, more so in generative and reasoning tasks, with instruction tuning improving clean-input scores
while potentially increasing brittleness. Its own framing of the gap is that "most benchmarks assume clean
input". What it reports is **aggregate degradation on a held-out set** — which is what it sets out to report.

**The second models the policy and assumes clean input.** Selective prediction is equally well developed:
"Entropy Alone is Insufficient for Safe Selective Prediction in LLMs" (arXiv:2603.21172) argues that uncertainty
methods must be evaluated inside the wider abstention policy and against the risk–coverage trade-off, because a
method that looks good in isolation can produce unreliable abstention at low target error rates. It evaluates on
TriviaQA, BioASQ and MedicalQA — **all clean**. Lee & See's account of trust in automation, and Parasuraman &
Riley's **misuse / disuse / abuse** taxonomy that it builds on, are the human-factors frame for what a changing
deferral rate does to an operator — and neither is brought to bear on corrupted input.

**The intersection is empty.** No study measures how the *input channel* moves a *selective-prediction policy's*
risk–coverage frontier, and no study prices the result as a human-facing cost.

That intersection is not a corner of the field. It is where deployment actually lives: a human types, a model
answers or defers, and a human receives whichever happened. The literatures are complete on either side of the
interface and silent at it.

**The question this study answers, then, is not "does noise hurt" — that is settled — but:**

> *When a confidence gate sits between a noisy human input and a human consumer, does input corruption move the
> gate's decision boundary, and in which direction does the damage land?*

with the answer, on this instrument: **the gate gets sharper, and the damage lands on what the system declines
to answer rather than on what it commits to.**

---

## 3. The formalization, read as findings rather than as corrections

The Lean development was treated as infrastructure until the review asked what it had discovered. Four of its
results are not corrections. They are statements about how the field measures this, and each was kernel-checked.

**F-L1. The standard silent-error question is ill-posed as usually stated.** (`risk_mono`; the refuted protocol
wording preserved as `protocol_said_nondecreasing_is_FALSE`.) The silent-error count at a fixed threshold is
**non-increasing** in that threshold. It follows that **no confidence-deflating manipulation can make a
fixed-threshold silent-error rate rise** — the trials leave the accepted set before they can be counted, so the
feared quantity is monotone in the safe direction *by construction*. The literature's premise — that noise
pushes errors *past* a gate calibrated on clean text — is therefore not a hypothesis that a rate can test. It
has to be posed as a **conditional** quantity or as a **discrimination** question, and the study's replacement
hypothesis is exactly the second. **This is a finding about the field's practice: a widely stated worry is
measurably unfalsifiable in the form it is usually stated.**

**F-L2. A gate's discriminability is a property of the model's ordering, not of its calibration.**
(`winsAux_map_of_strictMono`, with `#print axioms` reporting dependence on no axioms.) The ordered-pair count
is invariant under **any** strictly increasing map of the confidence scale. The selective-prediction literature
worries about calibration — whether the numbers are probabilities. This theorem says the **ordering** question
and the **calibration** question are genuinely separate, and that a policy can be evaluated on the first while
the second is in doubt. It is also what allowed the study to proceed on an instrument whose own vendor warns its
confidences are uncalibrated: measured, rescaling the whole arm moves a threshold quantity by **43.6 points**
and the discrimination statistic by **exactly 0.000**.

**F-L3. Two quantities the family treated as distinct measurements are one measurement.**
(`cond_error_complements_cond_accuracy`.) Conditional error among admitted trials and conditional accuracy
among admitted trials sum to one. Any study that reports both as separate evidence has counted one thing twice —
a multiplicity error that no correction procedure can repair, because it corrupts the family rather than the
p-value. Naming which quantities are functions of which is prior to controlling the family-wise error rate.

**F-L4. A risk budget can silently define the estimator out of existence.** (`budget_collapses_to_zero_on_small_dev`,
`empty_dev_is_degenerate`, `clean_pins_at_floor`.) Under a budget $\varepsilon$, at any $N$ with
$\lfloor \varepsilon N \rfloor = 0$ there is no error the budget tolerates, so the minimum admissible threshold
is the all-reject point and the fitted quantity is a **design constant, not an estimate**. At the conventional
$\varepsilon = 0.05$ this bites below $N = 20$. A threshold fitted on a small development split can therefore
report a number the data never determined, without any warning appearing in the output.

**What the four have in common.** Each says that a quantity the field reports is not measuring what its name
suggests — the silent-error rate (it is a criterion-dependent count), the calibration (the ordering is what a
policy reads), the family (two of its members are complements), the fitted threshold (it can be a constant).
That is a coherent contribution and it is *methodological*, which is why it was invisible while it was filed as
"the formalization corrected the protocol".

---

## 4. What would falsify the spine

The gap is empirical, not rhetorical, so it has to be able to fail.

- **If a confidence gate's discriminability fell under noise on other instruments**, the criterion-shift reading
  would not generalise and this would be one instrument's behaviour. The direction is the finding, so it must be
  re-established per instrument.
- **If meaning-corrupting noise deflated nothing** — a plausible substitution, a homophone — then the mechanism
  proposed here predicts an **opposite** outcome: errors would not announce themselves and the rise would
  disappear. That is a testable prediction, and it is the next experiment rather than a caveat.
- **If human operators responded to a falling coverage rate by overriding the gate**, the interaction claim
  would break in the direction F.3 predicts is the benign one — and would have to be measured with humans,
  which this study does not do.
