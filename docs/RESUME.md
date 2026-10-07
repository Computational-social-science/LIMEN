# Resume here

**Updated at shutdown, 2026-10-07.** Working tree clean, everything pushed.
`local = origin = b810849c49fa`. 41 guards green. Nothing depends on an unlogged conversation.

## Where the work lives

| | |
|---|---|
| main repository | `Computational-social-science/LIMEN` (public) — local `E:/2026-AI4S/autoresearch`, branch `main` |
| formalization | `Computational-social-science/LIMEN-lean` (private) — local `E:/2026-AI4S/lean-nhb`, branch `main` |
| authority for the object | `CURRENT_OBJECT.md` |
| protocol | `protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md` (v1.21, sha256 pinned) |
| pre-run evidence | `docs/PHASE_I_DEV_PRERUN_RESULTS.md` (§1–§10) |
| Lean status | `docs/LEAN_FORMALIZATION_STATUS.md` |
| the HTML deliverable | `viz/manuscript.html` |

Both repositories were verified against the GitHub API at shutdown: LIMEN `main` = `34236cc`, LIMEN-lean
`main` = `fea32ab`. Working trees clean.

## STATE: Phase I complete; the manuscript is written and the bibliography is audited

**Confirmatory run: 13,692 records, 0 failures, 366.5 s.** H1.1 p = 4.42e-36 · H1.2′ p = 2.00e-04 ·
H1.3 p = 5.00e-05 — all rejected under Holm, no direction violations.
Results in `docs/PHASE_I_CONFIRMATORY_RESULTS.md`.

**What changed on 2026-10-07.** The manuscript stopped being a summary of the protocol. It now carries its own
definitions and assumptions (the encoder, the instrument, the gate, and the three assumptions the design rests
on); the theoretical frame (Shannon 1948 on capacity, Shannon 1959 on the rate–distortion frontier, Green &
Swets 1966 on criterion versus sensitivity, Wiener 1948 on the disturbance); and Results headings that assert
findings rather than describe process. Four classical references were verified field by field and cited for the
first time. Two guards were added, each from a defect made in this session.

## Do these first

1. **The protocol's attribution is imprecise and HELD OPEN deliberately.** Lines **60** and **949** of
   `protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md` call the Rayner anchor value "the published
   Rayner (2006) anchor". The accurate statement — and the one the corrected prose now uses everywhere else —
   is that **Rayner published the *manipulation* and this project measured *the number* under its own
   recoverability index**. Correcting the protocol changes its sha256, which is a **re-pin with a version
   bump** — a governance act, not a prose fix. `check_attributed_numbers.py` excludes the protocol for this
   reason and prints the exclusion. **Decide: re-pin, or record the wording as accepted.**
2. **`System One` / `JEV-Ecosystem` are still undecided** in the protocol's vocabulary. Same decision shape as
   (1): renaming means a version bump and a re-pin, with `PHASE_I_PREREGISTRATION.md` and `CURRENT_OBJECT.md`
   kept coherent.
3. **Phase II's second channel `s_1` is not chosen.** §5 of `docs/PHASE_II_PREREGISTRATION.md` fixes the
   criteria and records a mechanism-based tie-breaker: a **segmentation-or-conversion** channel would *test* the
   Phase I mechanism (unremarkable surface, wrong answer → predicted silent), while a **substitution-style**
   channel would merely illustrate it. Choosing needs evidence — documented digital-input confusions, parallel
   intentions constructible under the template, and an instrument pinned at a revision that reads the script.
4. **`build_supplementary_information.py` is a live hazard, contained but not removed.** It writes the same path
   as the real assembler and DESTROYED the SI on 2026-10-07 (624 lines → 255). It now refuses to run without an
   explicit override flag. Whether to delete it is a judgement call left open.

## The standing rule this session paid for three times

**A kernel name, a DOI and a number are the same kind of assertion — each promises that something exists as
described.** Today produced one of each: an invented kernel name (`silent_error_count_antitone`, which does not
exist — the real ones are `risk_mono` and `protocol_said_nondecreasing_is_FALSE`); a DOI guessed one character
wrong that resolved to a **different paper in the same journal and issue**; and a number attributed to Rayner
et al. that this project computed. Only the first is mechanically guarded (`scripts/check_lean_citations.py`);
the second is why no identifier is ever constructed from memory; the third is guarded going forward by
`scripts/check_attributed_numbers.py`.

**And both guards had to be narrowed against measurement, not intuition:** the citation guard produced 17 false
positives before its scope was a declared document list, and value-matching for the attribution guard produced
26 collisions for one real finding. **A check that cries wolf gets disabled.**

## Building the documents — the correct order

```bash
cd E:/2026-AI4S/autoresearch
PY="C:/Users/Administrator/AppData/Local/hermes/tools/python-3.14.7+202****0901-win32-x64/python.exe"

# the manuscript
"$PY" -B scripts/build_paper_html.py
"$PY" -B scripts/build_docx.py --src docs/PAPER.md --out viz/manuscript.docx --harvest   # then re-harvest the map
"$PY" -B scripts/build_docx.py --src docs/PAPER.md --out viz/manuscript.docx --build

# the SI - edit docs/si/*.md FIRST, then assemble, then render
"$PY" -B scripts/assemble_supplementary_information.py   # the SOLE producer of the SI markdown
"$PY" -B scripts/build_si_documents.py                   # HTML + DOCX + PDF

# the gate
"$PY" -B scripts/run_all_guards.py                       # 41 guards, each with a negative control
```

**`build_supplementary_information.py` is NOT in that list and must not be.** `check_output_collisions.py`
declares the assembler its sole producer.

## Historical state before the 2026-10-07 work (superseded, kept for the record)

- **Guards: 28 of 28 pass**, each with a negative control that must fail.
- **Protocol v1.21**, evidence chain of 34 claims (15 proved · 6 measured · 6 assumed · 7 to be tested).
- **H1.2 was replaced by H1.2′** after four independent probes refuted the original claim (§7–§9 of the
  pre-run results). H1.2′ — the gate's discriminability rises under noise, measured as the within-arm AUC —
  is directional, **scale-free (machine-checked in LIMEN-lean: `#print axioms` reports no axioms at all)**,
  reuses §4.5's exact paired permutation, and leaves the frozen three-test Holm family and its thresholds
  untouched.
- **Sample size confirmed**: MDE 5.41 accuracy points at 80 % power against the 5.0-point target this design
  pre-registered. `π_d` measured 0.2036 against the frozen 0.1833 (higher, and favourable).
- **Window comparability checked statically**: domain χ² p = 0.2932, template χ² p = 0.7289. No erratum.

## The confirmatory run — DONE, kept for reproduction

**Executed 2026-10-05. All four commands below have been run and their outputs are the results in
`docs/PHASE_I_CONFIRMATORY_RESULTS.md`.** They are kept here because the analyses are re-runnable.

```bash
cd E:/2026-AI4S/autoresearch
PY="C:/Users/Administrator/AppData/Local/hermes/tools/python-3.14.7+20260901-win32-x64/python.exe"

# 1. the confirmatory run - 652 test items x 7 lambdas x 3 seeds = 13,692 conditions, ~7 minutes
HF_ENDPOINT=https://hf-mirror.com "$PY" -B measurement/run_phase1.py \
  --bank measurement/out/confirm_test.jsonl \
  --out  measurement/out/confirm_trials.jsonl \
  --lambdas 0.0 0.03 0.05 0.08 0.12 0.18 0.25 --seeds 0 1 2 --device cuda

# 2. the pre-registered analysis (exact paired permutation, Holm, direction enforced)
"$PY" -B scripts/analyze_phase1.py --trials measurement/out/confirm_trials.jsonl --lam-mid 0.18

# 3. the H1.2' contrast
"$PY" -B scripts/analyze_h12_auc.py --trials measurement/out/confirm_trials.jsonl

# 4. the confidence-contamination invariant on the real run
"$PY" -B scripts/check_confidence_contamination.py measurement/out/confirm_trials.jsonl
```

`measurement/out/` is gitignored; `measurement/out/confirm_test.jsonl` is already built (652 items, test
split only, static — no model was run to create it).

## Open items, in the order they matter

1. **Run the confirmatory analysis above**, then fill the Stage 1 manuscript skeleton with real numbers.
   Section 16 of the protocol already carries the pre-run evidence; the abstract and key-results boxes need
   the confirmatory data and nothing else does.
2. **Decide the visibility of `LIMEN-lean`.** It was created **private** because it was created on
   instruction to protect against loss, and publishing a new repository is not a decision to take on
   someone else's behalf. One click in repository settings flips it.
3. **A guard for the recurring ordering mistake.** Three times in one session two steps were run in the
   wrong order and produced output that looked fine — a commit that included its own transient message file,
   a guard suite run in the same shell invocation as the commit it was supposed to gate, and a derived table
   refreshed between a version bump and its re-pin. A check asserting no transient files are staged and that
   the version field agrees with the content digest would cover the whole class.
4. **`R6/`** is untracked and holds the user's reference materials. Classified as toolbox by the tool
   boundary rule; left alone deliberately.

## Two habits worth keeping, both learned the hard way today

- **Convert a number into the quantity the decision depends on before acting on it.** Twice a plausible
  figure reversed a conclusion once its units were fixed: an equivalence margin that was a confidence
  interval rather than a powered bound, and a power ratio computed against a measured effect rather than the
  pre-registered target.
- **Verify an estimator with controls before pre-registering it.** A key collision silently collapsed a
  dataset to two observations while the script still printed a p-value, and a positive control that shifted
  a whole arm was inert because a within-arm AUC is invariant to a monotone transform — both were caught by
  controls, not by reading the code.
