# Resume here

**Updated 2026-10-08.** Working tree clean, everything pushed.
`local = origin` at `36594ae`. 45 guards green. Nothing depends on an unlogged conversation.

> **Transport note, kept because it recurs and the diagnosis is the useful part.** Pushes failed eleven times
> across this session — `Connection was reset`, then `Failed to connect to github.com port 443` — while
> `api.github.com` and `github.com` both answered **HTTP 200 at the same moment**. Each time the same command
> went through unchanged on a later attempt, including the one immediately after this note was written.
> **On this host the git transport path is the flaky part, not the network. When the API answers, retry;
> do not investigate credentials, and do not conclude the commit is lost.**
>
> **Do not pre-write an "unpushed" warning into this note again.** It was written three times tonight and was
> stale three times within minutes — the push succeeds on the attempt after the note is committed. State the
> commit and let the first action be a push; a note that announces a failure it then outlives is itself the
> stale-claim defect this file exists to avoid.

## Where the work lives

| | |
|---|---|
| main repository | `Computational-social-science/LIMEN` (public) — local `E:/2026-AI4S/autoresearch`, branch `main` |
| formalization | `Computational-social-science/LIMEN-lean` (private) — local `E:/2026-AI4S/lean-nhb`, branch `main` |
| authority for the object | `CURRENT_OBJECT.md` |
| protocol | `protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md` (**v1.24**, sha256 pinned) |
| pre-run evidence | `docs/PHASE_I_DEV_PRERUN_RESULTS.md` (§1–§10) |
| Lean status | `docs/LEAN_FORMALIZATION_STATUS.md` |
| the HTML deliverable | `viz/manuscript.html` |
| the reference audit | `docs/REFERENCE_AUDIT.md` |
| Phase II, drafted | `docs/PHASE_II_PREREGISTRATION.md` |

Both repositories were verified at the start of this session: LIMEN `main` = `0a2e662`, LIMEN-lean
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

1. ~~**The protocol's attribution is imprecise and HELD OPEN deliberately.**~~ **DONE 2026-10-07 — protocol
   v1.24.** The protocol now states that the anchor is a **published human *manipulation* measured under this
   index**, not a number quoted from the paper, and `config/anchor.json` was re-pinned through
   `repin_anchor.py` (sha256 `81dcbad6…` → `724fb00f…`). The same session found and fixed the copy at
   `viz/protocol.md`, which had drifted out of sync with the protocol. **Closed; recorded here rather than
   deleted, because the entry stayed open long enough to send a session after work already finished.**
2. **`System One` / `JEV-Ecosystem` are still undecided** in the protocol's vocabulary. Same decision shape as
   (1): renaming means a version bump and a re-pin, with `PHASE_I_PREREGISTRATION.md` and `CURRENT_OBJECT.md`
   kept coherent.
3. **Phase II's second channel `s_1` is now derived, and the dataset choice remains.** §5 of
   `docs/PHASE_II_PREREGISTRATION.md` fixes the criteria and records a mechanism-based tie-breaker: a
   **segmentation-or-conversion** channel would *test* the Phase I mechanism (unremarkable surface, wrong
   answer → predicted silent), while a **substitution-style** channel would merely illustrate it.
   **COVERAGE IS SETTLED (2026-10-08), ON A SOURCE RATHER THAN BY PREFERENCE.** The programme owner directed
   that the coverage be decided from the literature first, and pointed at
   `Refs/2022-NRP_Universal and specific reading mechanisms across different writing systems.pdf`
   (Li, Huang, Yao & Hyönä, *Nature Reviews Psychology* **1**, 133–144; DOI `10.1038/s44159-022-00022-6`). That
   review defines the categories by how graphemes map to speech — alphabetic / syllabic / logographic — so one
   channel per category gives **English · Japanese · Chinese**, and it states that findings from alphabetic
   scripts "cannot necessarily be extended to other writing systems" and that the comparison "should be [made]
   within the same study". **The review is now queryable as an agent**:
   `universal-reading-mechanisms-paper` (installed, verified, recorded in `docs/PAPER_AGENT_LIBRARY.md` §6).
   **DATASETS ARE NOW SETTLED (2026-10-08), BY THE OBSERVED-BEHAVIOUR RULE.** The programme owner directed that
   where a real human behavioural dataset exists it is the one to use, and made that a global rule; it is
   recorded as rule 17 of `global-research-project-rules`, and the project-side declaration is
   `config/datasets.json` with `scripts/check_dataset_provenance.py` reading it (a declaration nothing reads is
   a comment). Each channel's primary is `observed`: **English — Birkbeck Spelling Error Corpus** (real
   native-speaker errors; scope caveat recorded that it includes children and very poor spellers, so the
   distribution is usable but the rate must not be quoted as typical); **Japanese — JWTD** (real Wikipedia
   revision history; the paper states it is publicly available); **Chinese — CSCD-NS** (40,000 sentences from
   REAL Sina Weibo posts by official media accounts, MIT, ACL 2024, pp. 146–159). **The rejected alternative
   matters as much as the choice:** `LCSTS-IME-2M` sits in the *same repository* as CSCD-NS, is ~50× larger and
   far tidier, and is constructed by **simulating** pinyin IME input — it would measure the simulator's
   assumptions, which is the quantity under study. **Remaining:** confirm the three datasets actually download
   (Birkbeck and JWTD by URL; CSCD-NS from the drive link the repository documents, its data not being in the
   repo because of the host's LFS quota), **then** file the amendment. Evidence so far is in
   `docs/PHASE_II_S1_CHANNEL_EVIDENCE.md`.
4. ~~**The superseded SI generator is a live hazard, contained but not removed.**~~ **It no longer exists in
   this repository: deleted 2026-10-08.** It was the generator whose inline prose made the SI read like an
   engineering log — the reason the assembler exists — and it still defaulted to the assembler's own output
   path. Contained by a flag is not removed; `check_output_collisions.py` names this exact class. Deletion was
   reported by three guards before the commit landed (two path promises in this file, and the collision map),
   which is the behaviour wanted from them.

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
"$PY" -B scripts/run_all_guards.py                       # 45 guards, each with a negative control
```

**The superseded generator that used to sit beside the assembler was deleted on 2026-10-08.** It defaulted to
the assembler's own output path, and `check_output_collisions.py` declares the assembler its sole producer —
a script that is not the producer must not carry the producer's path, and confinement by a flag is not
removal. Git history keeps the file.

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

## Open items carried from the 2026-10-05 shutdown (three of four now closed)

**Kept as a list rather than deleted, because two of its entries are the evidence that this file goes stale
when its items are executed and it is not updated.** Item 1 and item 3 were done and the entries stayed open.

1. ~~**Run the confirmatory analysis**, then fill the Stage 1 manuscript skeleton with real numbers.~~
   **DONE 2026-10-05** — the run produced 13,692 records, and the manuscript's numbers were filled from it.
2. **Decide the visibility of `LIMEN-lean`.** It was created **private** because it was created on
   instruction to protect against loss, and publishing a new repository is not a decision to take on
   someone else's behalf. One click in repository settings flips it. **STILL OPEN.**
3. ~~**A guard for the recurring ordering mistake.**~~ **DONE** — `scripts/check_step_order.py` asserts that
   no transient artefact is staged and that the protocol's version, digest and byte count agree, and it runs
   in the suite with a negative control.
4. **`R6/`** is untracked and holds the user's reference materials. Classified as toolbox by the tool
   boundary rule; left alone deliberately. **STILL OPEN (deliberately).**

## Two habits worth keeping, both learned the hard way today

- **Convert a number into the quantity the decision depends on before acting on it.** Twice a plausible
  figure reversed a conclusion once its units were fixed: an equivalence margin that was a confidence
  interval rather than a powered bound, and a power ratio computed against a measured effect rather than the
  pre-registered target.
- **Verify an estimator with controls before pre-registering it.** A key collision silently collapsed a
  dataset to two observations while the script still printed a p-value, and a positive control that shifted
  a whole arm was inert because a within-arm AUC is invariant to a monotone transform — both were caught by
  controls, not by reading the code.
