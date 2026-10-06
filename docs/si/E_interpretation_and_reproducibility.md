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
