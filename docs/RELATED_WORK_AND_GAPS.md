# Related work as PK objects — what is reused, and what is put under test

**The principle this file applies.** A related work is not background. Its **open resources and methods are
reusable**, and reusing them converts the work into one of two things: a **foundation** the programme builds on,
or a **claim the programme can overturn**. Anything that is neither is decoration, and decoration does not fill a
gap. **Every row below names a resource and a claim, and says which of the two roles it will play.**

**Ordered by how much each one costs to reuse and how much it settles.**

---

## PK-1 — MulTypo: does a simulated error distribution buy what an observed one buys?

| | |
|---|---|
| **Work** | Zhao, Liu, Altinger, Schütze & Hedderich (arXiv 2510.09536, Oct 2025), *Evaluating Robustness of LLMs Against Multilingual Typographical Errors* |
| **Resource** | **`github.com/cisnlp/multypo`** — verified to exist. A multilingual typo **generator** driven by language-specific keyboard layouts, plus evaluation across 18 open models and 5 tasks |
| **Its claim** | Typos degrade performance; robustness is **language-dependent**, with **high-resource languages more robust than low-resource ones** |
| **What it does not do** | **Its errors are generated, not observed** — and, as the full paper shows, **its realism was validated by human evaluation** (§3.2), which this row's first version wrongly implied had not happened |
| **Role** | **FOUNDATION for the realism protocol; a measured MECHANISM BOUNDARY at the deep end of the depth axis** |

**The experiment, run rather than proposed, and the result is a mechanism boundary.**

`pip install multypo` was run on the project's interpreter. **The package is MIT-licensed, installs cleanly, and
`get_supported_languages()` returns exactly the twelve segmental scripts** — German, English, French, Greek,
Russian, Arabic, Hindi, Armenian, Georgian, Hebrew, Bengali, Tamil. **No logographic language, no syllabic one.**

**Its extension point is `register_keyboard_layout(keyboard_rows, left_keys, right_keys, ignoring_set)`, so the
question is not whether the authors chose to include Chinese but whether the mechanism can express Chinese at
all.** Registering a pinyin keyboard succeeds, and the generator then runs — and this is what it produces:

```
input   我惟独喜欢这一个
output  我独喜欢这一个          ← the character 惟 was DELETED
```

**That is a backspace, not the error the corpus records.** The observed Chinese substitutions are
`惟→唯 · 作→做 · 在→再 · 那→哪 · 做→作 · 象→像 · 带→戴 · 收→受` — **every one of them a homophone.**

**So the boundary was quantified, giving the generator the strongest sympathetic reading available** — that the
characters' pinyin be compared, rather than the characters themselves:

| CSCD-NS observed character substitutions | 15,139 |
|---|---|
| **whose typed PINYIN is identical** | **12,334 — 81.4 %** |
| whose pinyin differs | 2,805 — 18.5 % |

**For 81.4 % of the observed Chinese errors, the keystrokes were correct.** The pinyin was typed exactly, and
**the error happened entirely inside the input method's candidate selection.** A generator whose operations are
replacement, insertion, deletion and transposition **defined on a key string cannot produce a single one of them**
— not because coverage is low, but because **there is no keystroke to corrupt**. **The mechanism is unreachable
from the mechanism's side, and that is a measurement rather than an argument.**

**What the parity correction does to this row.** The first version of this section framed the difference as
"they simulated, we observed", implying a standard the competitor had not met. **Reading the full paper refuted
that**: MultiTypo **validates its realism through human evaluation** (§3.2), with 15 sentences per language rated
for naturalness and significant improvements over a naive baseline in nine of twelve languages. **The authors did
the validation the framing assumed they had skipped.** The defensible contrast is therefore not evidence quality
but **reach**: an error process whose locus is candidate selection, not key adjacency.

**And their realism protocol is reusable.** Adopting their human-evaluation design lets the programme show that
its observed corpora are rated more natural than a simulated baseline **on the competitor's own instrument** —
converting the evidence standard from a principle into a measurement taken on a shared scale.

**A convergence worth recording.** MultiTypo operates at a **user-defined typo rate `τ ∈ [0,1]`** — operational and
channel-free. **The programme reached the same principle independently, through a different route** (sections 6.5
and 6.7 of `docs/PHASE_II_NOISE_EVIDENCE.md`), and then went further by **measuring why an index cannot supply
that rate**. Two independent arrivals at the same design rule is evidence the rule is right.

## PK-2 — Multilingual calibration: is it resource, or is it depth?

| | |
|---|---|
| **Work** | Zhou, Zhang, Hu, Li, Collier, Vulić & Korhonen (arXiv 2510.03136, Oct 2025), *Beyond the Final Layer: Intermediate Representations for Better Multilingual Calibration* |
| **Resource** | **LACE** (Language-Aware Confidence Ensemble) — a **training-free** per-language layer ensemble; study spans 6 model families and 100+ languages |
| **Its claim** | Non-English languages are **systematically worse calibrated**, diagnosed as a consequence of **English-centric training**; late-intermediate layers are better calibrated than the final layer |
| **What it does not do** | **Measures calibration on clean input**, and **its explanatory axis is resource/language, not depth of the writing system** |
| **Role** | **FOUNDATION for the method, OVERTURN for the explanation** |

**The experiment, in two halves.**

1. **Reuse LACE as a reference calibration method** and ask whether a layer ensemble that fixes *clean-input*
   miscalibration also fixes **noise-induced** miscalibration. **If it does not, that is a published method with a
   measured boundary** — a useful and honest result about someone else's tool.
2. **Test depth against resource as competing predictors.** If **orthographic depth predicts degradation after
   resource is controlled for**, then "English-centric training" is an incomplete explanation and the programme
   has refined a Nature-family-level claim. **The two variables are separable in this design** because the depth
   axis and the resource axis do not coincide: English is the highest-resource language *and* one of the deepest
   alphabetic ones, while Chinese is high-resource *and* logographic.

## PK-3 — "Word form dominates": true of scripts, or true of English?

| | |
|---|---|
| **Works** | Wang et al. (ACL 2025 Findings), *Word Form Matters*; Zhang et al. (arXiv 2509.06996), *Visible Yet Unreadable* |
| **Resource** | **`github.com/Aurora-cx/TypoLLM`** — verified to exist; the **SR/CI scales** (already adopted as the English level source); **`SemRecScore`**; and, from *Visible Yet Unreadable*, **cross-script stimuli-generation code, prompts and evaluation protocols** for Chinese logographs against English alphabetic words |
| **Their claims** | Wang et al.: LLMs rely on **word form**, context contributes **little**, attention reallocates to form as scrambling rises — **established in English only**, with a stated 70B anomaly. Zhang et al.: VLMs **under-rely on compositional priors** needed for robust literacy, across Chinese and English |
| **What they do not do** | **Neither tests a script in which word form carries no recoverable cue**, and the second is a **vision** study |
| **Role** | **FOUNDATION for stimuli and scales, OVERTURN for the scope of the claim** |

**The experiment.** **`SemRecScore` is adopted as a second, representational dependent variable in the English
arm** — where it is defined — so the programme's behavioural result can be read against theirs directly, and any
divergence is attributable to the arm rather than to a different measurement. In the **logographic arm the metric
has no definition** (a character has no interior to scramble, and Chinese tokenization is character-level), so the
behavioural variables carry that arm alone — **and that asymmetry is itself part of the result**: it is the
instrument's boundary, reported as a finding rather than hidden as a limitation.

**Both of their mechanisms predict the opposite of what the depth account predicts for a logographic script.**
That is what makes the test informative rather than confirmatory.

## PK-4 — The framing, adopted rather than re-invented

| | |
|---|---|
| **Work** | Steyvers, Teo, Mackert & Smyth (2024, *Nature Machine Intelligence*), *What large language models know and what people think they know* |
| **Resource** | The **calibration gap** and **discrimination gap** constructs |
| **Role** | **FOUNDATION — terminology and measures adopted verbatim** |

**Why adopt rather than define anew.** A Nature-family venue has already given these quantities their names and
their operationalisations. **Inventing a parallel vocabulary for the same idea would make the work look novel and
read as unfamiliar**, which is the opposite of what a registered report needs. The programme's confidence-gate
variables are reported as calibration-gap-type and discrimination-gap-type measures against that framing.

## PK-5 — The human anchor and the cross-script taxonomy

| | |
|---|---|
| **Works** | Rayner, White, Johnson & Liversedge (2006), *Psychological Science*; Li, Huang, Yao & Hyönä (2022, *Nature Reviews Psychology*) |
| **Role** | **FOUNDATION.** Rayner supplies the human-validated point on the manipulation axis (its index value is measured under this project's index and cannot be compared across channels — see `docs/PHASE_II_NOISE_EVIDENCE.md` §6.5). Li et al. supplies the cross-script mechanism review, already converted into the `universal-reading-mechanisms-paper` skill |

---

## What the programme does NOT claim

**Stated so the positioning cannot be read as more than it is.**

- **Not** that cross-script typo robustness is unstudied. **MulTypo studies it**, across 18 models and 5 tasks.
- **Not** that models are uncalibrated across languages. **Zhou et al. established that**, at scale.
- **Not** that scrambling semantics are unstudied. **Wang et al. established them** for English.

**What is claimed is narrower and checkable**: those works establish their results **through a simulated error
process, on clean input, or in a single script** — and **none of them tests whether the explanatory axis is the
depth of the writing system rather than the language or its resource level.** The programme's contribution is the
**substitution of observed error data at operational levels for a simulation**, and **depth for resource as the
axis** — with PK-1 supplying the measurement that decides whether the first substitution was necessary.
