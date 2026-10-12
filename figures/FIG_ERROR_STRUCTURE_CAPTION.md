# Figure caption — typing error is two processes, not one noise channel

**Figure 1 | Human typing error is a regulated two-process system, and synthetic
noise models the minority process.** Analysis of **300,000 transcribed sentences**
from **20,000 participants** in the 136M Keystrokes corpus (Dhakal, Feit,
Kristensson & Oulasvirta, *CHI 2018*). Because the corpus logs every keystroke
including backspace, errors **repaired by the typist** are separable from errors
that **survive into the final text** — a distinction unavailable to any analysis
of residual strings alone.

**a**, Composition of surviving errors, one event per error. Deletion and
insertion together account for 61.3%, case 16.5%, and the two keyboard-geometry
classes (adjacent-key substitution, transposition) only 13.6%.

**b**, The programme's synthetic noise generator `N_en` against measurement.
`N_en` assigns fixed weights of adjacent 35%, transposition 25%, deletion 20%,
insertion 20% and has **no case class**. It over-weights by 3–4× exactly the two
geometry-indexed classes and under-weights the two structure-indexed classes,
while omitting case — the third-largest measured class — entirely. The generator
is therefore not a neutral noise model but a model of one specific process.

**c**, The discriminating test. A motor process is blind to word structure, so its
per-character rate must be flat across word length; a planning process operates on
chunks, so its rate must scale with length. Adjacent-key substitution is **flat
(0.98× from length 2 to 12)**, whereas deletion rises 2.5× and insertion 4.9×.
The two families are **double-dissociated**.

**d**, The dissociation at population level, with the participant — not the
character — as the unit of inference. Long/short word error-rate ratios:
adjacent 1.07 (95% CI 1.02–1.13), deletion 1.79 (1.73–1.86), insertion 2.83
(2.73–2.93); 2,000 participant-cluster bootstrap replicates, n = 20,000. The
effect is not an aggregation artefact: it reproduces in both halves of a
split by error burden and in every decile with informative participants.

**e**, Word-first position is not an elevated-error position. Case errors — largely
a capitalisation convention (82.1% occur at sentence-initial position) rather than
a typing slip — dominate the word-first cell. With case excluded, word-first
(3.5 per 1,000 characters) is **below** word-middle (5.9). A previously reported
3.7× word-initial effect was retracted as a counter artefact. Truncated
transcriptions excluded; all classes attributed to positions under one convention.

**f**, The final text is the residual of a control loop, not its output.
2.61 errors per sentence are repaired by backspace against 0.44 that survive
(5.9×), and 63.6% of sentences contain at least one backspace. Correction latency
from the preceding keystroke is tightly unimodal (median 450 ms; 81% within
200–750 ms), consistent with a single fast automatic monitor rather than a
deliberate lexical check.

---

## Statistics and definitions

- **Source**: 136M Keystrokes corpus, 168,593 participant files; a random sample
  of 20,000 files (seed 20261012) was analysed, each contributing 15 sentences.
- **Unit of analysis**: the transcribed sentence `(participant_id,
  test_section_id)`; for **d** the participant.
- **WPM, IKI, error definitions**: follow the source paper's Performance
  Measures (p. 4). Uncorrected error rate = `Levenshtein(presented, transcribed)
  ÷ max(len)`.
- **Class definitions**: adjacent-key = substitution between keys adjacent on
  QWERTY; transposition = adjacent character swap; case = same letter, different
  case; deletion / insertion from alignment; "other" is a residual bin and is not
  given a mechanistic reading.
- **Transposition detection**: `difflib` has no transposition class and reports
  93.4–100% of single transpositions as an insertion **plus** a deletion of the
  same character. A dedicated detector recovers 96.5–100% of synthetic
  transpositions with 0% false positives on different-character pairs. Counted as
  **one event** here; counting two opcodes instead would raise transposition to
  8.8% and lower deletion/insertion correspondingly.
- **Truncation control**: 2.99% of sections have `USER_INPUT` as a strict prefix
  of `SENTENCE`. These are excluded from **e** and from all position analyses;
  they accounted for 24.7% of the raw word-last elevation.
- **No error bars** are shown in **a**, **b**, **c**, **e** and **f**: with
  n = 300,000 sentences the confidence intervals are narrower than the plotted
  symbol and would imply a precision the sampling design does not support.
  Panel **d** shows participant-cluster bootstrap intervals, which do carry
  inferential meaning.

## Caveats and retractions

1. **Retracted**: the word-initial vs word-internal contrast (previously reported
   as 8.82 vs 2.40 per 1,000, a 3.7× effect) was a **counter artefact** — the
   counter incremented only in the `replace` branch, omitting 93,760 of 138,893
   errors. Under full attribution the ratio is 1.48×, and **0.43×** excluding case.
2. **Revised**: earlier position figures silently excluded insertions from the
   numerator. Panel **e** uses one consistent all-class convention.
3. **Revised**: the sentence-position profile is a **J-shape, not a U-shape** — the
   apparent left arm was case errors (78.9% of decile 0), and the final bucket is
   not a decile (19.9% of characters). Excluding case, the first bucket is 2.89
   per 1,000, *below* the middle.
4. **Revised**: "word-last" is better described as **end-of-sentence**.
   Sentence-final words are 13.3% of word-last exposure but 44.2% of word-last
   errors (37.77 vs 7.32 per 1,000, a 5.2× ratio).
5. **Open**: whether the two processes are separable **in model loss** is not
   addressed here. That requires injection at matched token-damage rate, not a
   corpus measurement.
6. **Open**: the mechanism behind the deletion/insertion scaling with word length
   is unresolved between a motor account (missed or doubled keystroke) and a
   planning account (chunk boundary).
7. **Not addressed**: generalisation beyond English, and beyond this corpus's 15
   fixed sentences and self-selected participants.

## Verification

All numbers were independently recomputed by a separate adversarial verification
pass (`docs/ERROR_STRUCTURE_VERIFICATION.md`), which reproduced every class count,
position cell and decile exactly (0 mismatches), confirmed the transposition
detector against its own generator (100% recovery, 0% false positives), and
attacked the double dissociation under interior-only normalisation and within
every sentence decile without breaking it. Five of six originally reported
numbers required restatement; those restatements are applied in this figure.

## Data and code

- `figures/fig_error_structure.py` — this figure, reproducible from the JSON inputs
- `scripts/trans_aware.py` — transposition-aware classification (with self-test)
- `scripts/per_participant.py` — participant-level dataset
- `scripts/h1_vs_h2.py` — the double-dissociation test
- `scripts/decisive_tests.py` — truncation control and correction latency
- `docs/PARADIGM_TYPING_AS_REGULATED_PROCESS.md` — full analysis
