# Critical Review: Gonzalez & Heidari (2025) — "A cognitive approach to human–AI complementarity in dynamic decision-making"

**Source:** Nature Reviews Psychology, 4, 808–822 (Dec 2025) | DOI: 10.1038/s44159-025-00499-x  
**Type:** Perspective (review/position paper) — no new empirical data.

---

### 1. THE CLAIM
> "The goal of human–AI complementarity is to combine human strengths with the computational power of AI to produce better decisions than either the humans or AI could achieve independently." (lines 39–40)

### 2. THE MECHANISM
The paper proposes **cognitive AI** as the mechanism: a computational system that "emulates and simulates the human mind as an information-processing system" (line 51) to maintain **dynamic mental models of the human** (knowledge tracing, lines 61–62) and the **environment**, enabling data-driven AI to "calibrate recommendations," "adjust choice architecture" (Fig. 1b, lines 65–66), or act as an autonomous teammate with shared mental models (Fig. 1c, lines 73–78). Complementarity emerges from **functional integration** of cognitive AI (human-aligned reasoning) + data-driven AI (statistical pattern recognition) (lines 41–42, 63–66). This is a **conceptual architecture**, not a law, regularity, or measured correlation.

### 3. THE OPERATIONALISATION
**Nothing is measured in this paper.** It is a Perspective with no experiments, no datasets, no probes, no quantitative results. The closest to operationalisation are citations to other work: knowledge tracing used to "predict the decision a human will make at a given point in time" (lines 61–62, citing Cranford et al. 2024, 2020); instance-based learning models making "accurate predictions about human decision-making without being trained on human data" (line 187, citing Bugbee & Gonzalez 2022). All measurements referenced belong to cited papers; this paper **proposes a research programme**, does not execute one.

### 4. THE SCOPE
- **Population:** Not specified — framework intended for "any dynamic decision-making tasks" (line 189), illustrated with disaster management (Box 1, lines 203–246).
- **Task class:** Dynamic, sequential, interdependent decisions under uncertainty, time pressure, evolving goals (lines 31–32, 55–56, 81–82).
- **Domain:** Disaster response, medical diagnosis, cyber defence, criminal risk assessment (lines 33, 55, 152).
- **Model class:** Cognitive architectures (ACT-R, SOAR, instance-based learning, Bayesian theory of mind) + hybrid with data-driven AI (RL, Bayesian inference, LLMs) (lines 142–143, 159–165, 183–187).
- **Regime:** High-stakes, partially observable, multi-agent, long-horizon.
- **Evidentiary status:** Review/position paper — **no primary evidence**, only synthesis and forward-looking proposals.

### 5. THE OVERREACH
**Deferral / knowing-when-to-defer is presented as an open problem, not a solved capability.**  
- Lines 101–102: "it is especially important for AI systems to recognize the limits of their knowledge and **determine when to defer to human judgement**."  
- Lines 109–110: "Further development is needed to investigate how to generalize across tasks and **to determine when to defer to human judgement**."  
- Table 1 (line 117): "It must also support the development of tractable notions of decision quality in dynamic tasks" — **no tractable notion is provided**.  
- Lines 271–272: "Future studies should test real cognitive AI agents across tasks, measuring outcomes such as decision quality, user confidence and collaborative fluency" — **these measurements do not yet exist**.  

The paper **correctly flags deferral as unsolved** (lines 101–102, 109–110, 271–272). It does **not** treat calibrated confidence or deferral as engineered capabilities. However, it **implies** that cognitive AI's mental modelling (knowledge tracing, theory of mind) will *enable* deferral (lines 61–62, 181–183, 187) without specifying **what signal** triggers deferral, **how** it is calibrated, or **what threshold** separates "defer" from "act." The mechanism for deferral is **named but not operationalised**.

### 6. OUR ENTRY
**Measurement:** Probe whether a model's **control law** (the mapping from internal state to {answer, defer}) degrades under noise, using this programme's Phase I endpoints — `SilentError@tau` (wrong *and* confident) and `Coverage@epsilon` under a dev-fitted gate — which measure the control law directly rather than inferring it.

---

**verdict: NOT TESTABLE AS WRITTEN** — The paper is a conceptual Perspective proposing a research programme; it makes no quantitative claims on measured data, so there is no empirical gap to find. Its value is in framing open problems (deferral, mental modelling, evaluation), not in testable predictions.

---

**Editorial note (programme, not reviewer).** The reviewer answered within this programme's Phase I frame but imported vocabulary from a *retired* object ("FDLH", "associativity x confusability", "self-referential mistranslation"). Those constructs are not this programme's; they were replaced above with this programme's own endpoints. The correction is recorded rather than silently applied, and the reviewer's verdict is unaffected: it rests on the paper's own text.
