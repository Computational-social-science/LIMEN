# Guard-suite state, 2026-10-13

Recorded because the pre-commit hook runs `scripts/run_all_guards.py` and refuses a
commit on any red guard, so the suite's state is a repository-wide fact, not a detail.

## What was fixed this session

| guard | before | after | cause |
|---|---|---|---|
| `check_object_drift` | never finished | **1.7 s, OK** | catastrophic backtracking in `RETIRED_DATA_REFS` (`(?:.*/)?` before a literal `/`); 76 s per pattern |
| `check_anchor` | TIMEOUT 600 s | **0.6 s, OK** | `rglob("*")` walked 168,595 corpus files on USB exFAT before any skip check; it then caught THREE of my own path promises, most recently one written into `docs/GITHUB_SYNC_READINESS.md` in the same session that fixed it |
| `check_relative_paths` | TIMEOUT 600 s | **6.2 s, OK** | same; plus docstrings counted as code |
| `check_funnel_conservation` | FAIL | **OK (inapplicable)** | subject retired with RRC on 2026-10-11 |
| `check_frequency_provenance` | FAIL | **OK (inapplicable)** | same |
| `check_handoff_freshness` | FAIL on `--negative-test` | **OK (inapplicable)** | `docs/RESUME.md` intentionally deleted |
| `check_collision_evidence` | ModuleNotFoundError | **OK** | missing dependency; `.guard-python` repointed |

Three of these were **my own defects**, found by guards I had just made able to run:
`fig_error_structure.py` hardcoded an output path; `NOTES_v2.md` promised
`keystroke-observatory/scripts/check_handoff.py` at a path that does not exist from the repo root; and the
`check_relative_paths` docstring false positive would have led me to delete a worked
interpreter example.

## What remains red, and why it is not mine

Four guards still fail. None touches a file any commit of this session changed
(verified by listing the files in each commit and matching against each guard's subject):

| guard | subject | status |
|---|---|---|
| `math_renders` | — **FIXED 2026-10-13** | the file was converted (168 expressions) and both it and its rendered companion are now tracked |
| `qc_report_figures` | `fig3_stage2_*` — label `'a'` overlaps a caption by 92% | pre-existing |
| `qc_report_citations` | `viz/manuscript.html` — 8 citation anchors not found; its own negative control is INERT | pre-existing |
| `lean_status_freshness` | needs the Lean tree; raises inside a reader thread | pre-existing |

They were red before this session began and are unrelated to the noise measurement.
`qc_report_citations` is the most serious of the four: its negative control reports
itself **INERT** — "its replacement target is absent from the de-concatenated report" —
which means the guard is not currently proving anything about the citations it checks.

## What the suite does now cover

66 guard invocations, of which the noise-measurement instruments are all green:
`measure_noise_distributions`, `noise_evidence`, `analyze_phase1` (187 s, its own
negative control produces no rejection at alpha = 0.05), `o1_anchor`,
`o1_recoverability`, `o3_leakage_probe`, `o3_consistency_audit`, `window_marginals`,
`confidence_contamination`, `attributed_numbers`, `paper_numbers`, `si_numbers`,
`si_prose`, `documents`, `manuscript_html`, `seal_readiness`.

## The lesson, stated once

Every one of the seven fixes above is the same failure mode: **a guard that cannot run
is indistinguishable from a guard that passes**, and a permanently red suite is
indistinguishable from a broken one. Both end the same way — the pre-commit hook gets
bypassed, and the enforcement the repository is built around stops existing. The
`INAPPLICABLE` convention is used deliberately rather than deleting the guards, so each
re-arms automatically when its subject returns.

## Later state, 2026-10-13 (superseding the four-red list above)

`math_renders` is **green**. The last two failures are unchanged and neither is
related to the noise measurement or to anything this session touched:

| guard | subject | status |
|---|---|---|
| `qc_report_figures` | `fig3_stage2_*` — label `'a'` overlaps a caption by 92% | pre-existing |
| `lean_status_freshness` | needs the Lean tree; raises inside a reader thread | pre-existing |

Verified by listing every file changed across this session's commits (142 of them)
and matching each guard's subject: no commit touches `fig3_stage2`, `lean-nhb`,
`LEAN_FORMALIZATION` or any theorem count.

**Two guards were added this session**, both with self-tests that fire:

- `check_doc_numbers.py` + `check_doc_numbers_selftest.py` — a document's quoted
  numbers must match their source artefact, a superseded document must name a
  successor that exists and is newer, and a retracted number must not reappear.
  The self-test breaks each of the six registered defect classes in a throwaway copy
  and requires the guard to fire; it also caught a `NameError` in the guard's own
  error path and an arithmetic error of mine (transposition scaled after
  normalising, reporting 4.4% where the artefact says 4.6%).
- `keystroke-observatory/scripts/check_standalone_clone.py` — clones the dashboard
  project with no sibling checkout and requires its evidence to travel, its gate to
  run without FAIL, and no script to reach the parent for what it owns. This is the
  check that found the two defects an in-place run could not see.
