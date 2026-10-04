# Instrument ledger — what each retired instrument did, and where it went

**Purpose.** `CURRENT_OBJECT.md` used to list nine instruments as "kept — and why". None of them
existed: the R1 archival moved them all. This ledger exists so that a retired instrument is described
**once**, in the past tense, with its location — instead of being promised in the present tense by a
document that cannot keep the promise.

**Rule.** An instrument is added here when it is archived. An instrument is listed in
`CURRENT_OBJECT.md`'s live table only after its path has been verified to exist.

## Retired with R1 (2026-10-04)

All under `archive/R1_jevrsi_loop_objective_2026-10-04/`. These served the retired loop objective; none
is an input to the current protocol.

| Instrument | What it did | Where it is |
|---|---|---|
| `paths.py`, `config/paths.json` | Path single-source-of-truth and environment precedence for the loop workspace | `archive/.../root/paths.json` |
| `scripts/calibrate_against_release.py` | Loaded a pinned System One checkpoint and compared it to a published record | `archive/.../scripts/calibrate_against_release.py` |
| `measurement/report_from_items.py` | Recovered metrics from a trial record | `archive/.../measurement/report_from_items.py` |
| `measurement/build_synth_split.py` | Built typed-question splits over `choice` / `noul` / `score` | `archive/.../measurement/build_synth_split.py` |
| `scripts/health.py` | Run-health diagnostics for long jobs | `archive/.../scripts/health.py` |
| `scripts/run_with_heartbeat.py` | Heartbeat wrapper for long jobs | `archive/.../scripts/run_with_heartbeat.py` |
| `TOOLS.md`, `docs/BOOTLOOPS.md` | Tooling notes and the shared BootLoops substrate | `archive/.../docs/BOOTLOOPS.md` |

**Note on the shared substrates.** BootLoops and Lean 4 are **global installations**, not artefacts of
this repository: BootLoops lives at `E:/2026-AI4S/bootloops` and Lean 4 at `~/.elan`. Archiving the
repository's notes about them did not retire either installation, and both remain available.

## Replacements built for the current protocol

| Instrument | What it does |
|---|---|
| `measurement/typo_noise.py` | The noise process `N_en`, a pure function of `(item_id, λ, seed)` |
| `measurement/run_phase1.py` | The `predict → JSONL` runner, resumable, failures recorded |
| `measurement/smoke_predict.py` | The end-to-end check that the pinned checkpoint runs locally |
| `measurement/c2_noul_validity.py` | The `noul` primitive's measurement-validity check |
| `scripts/build_item_bank.py` | The deterministic item-bank builder |
| `scripts/check_anchor.py` | Verifies the anchor, version coherence, authority claims and dead references |
