# Resume here

**Written before shutdown, 2026-10-05.** Everything below is on disk and pushed; nothing depends on an
unlogged conversation.

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

## State: the seal is unblocked, and the only remaining step is the run

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

## The next step, exactly

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
