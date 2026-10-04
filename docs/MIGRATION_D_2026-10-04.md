# Migration record — project moved from D: to E: (2026-10-04)

**Performed:** 2026-10-04, by the agent, at the programme owner's direction.
**What moved:** the entire `autoresearch` repository.
**From:** `D:/2026-AI4S/autoresearch`
**To:** `E:/2026-AI4S/autoresearch`

## Why

`D:` was at **98 % capacity (7.2 TB of 7.3 TB, 177 GB free)**. `E:` had **2.8 TB free**. Any
corpus-scale work — which the sense inventory now requires — cannot run on `D:`. The move was made
with a **copy → verify → remove** sequence, never `mv`, so a mid-flight failure could not leave both
copies broken.

## Verification, before the source was removed

| Check | Source | Target | |
|---|---|---|---|
| Files | 1309 | 1309 | ✓ |
| Bytes | 128,894,291 | 128,894,291 | ✓ |
| `git rev-parse HEAD` | `c895d7a5…` | `c895d7a5…` | ✓ |
| Commit count | 52 | 52 | ✓ |
| Dirty files | 0 | 0 | ✓ |
| Drift guard | — | `OK: no drift across 24 live files` | ✓ |

The copy includes `.git` (3.3 MB, full history) and the untracked `.p2a-work/` conversion trees
(121 MB), so a resumed conversion and any `git` operation behave identically.

## Absolute-path references — classified, not silently rewritten

The standing convention is that **scripts use relative paths and the project is path-portable**. A
scan found 13 absolute references. They were classified, because "the project moved" and "history
happened at a path" are different things:

**Fixed (live paths — these would have broken):**

| File | What | Now |
|---|---|---|
| `config/pin.json` | `workdir` | `E:/2026-AI4S/autoresearch/measurement` |
| `measurement/smoke_predict.py` | runner docstring | `E:/2026-AI4S/…` |

**Left as written (historical records — rewriting them would falsify what happened):**

| File | Refs | Why it stays |
|---|---|---|
| `measurement/pilot_results.json` | 1 | It records where a **completed** run read its input. That was `D:`, and that is a fact about the run. |
| `docs/PREDICT_SMOKE_TEST.md` | 4 | A report of a run made at `D:`. The report is an artefact of that moment. |

**Not touched (still valid — they point OUTSIDE the moved project):** references to
`D:/2026-AI4S/nhb-llm-mistranslation/` (the `paper2agent` engine, still on `D:`) and
`D:/2026-AI4S/AGENTS.md` (the workspace file, still on `D:`). Neither moved, so neither reference is
stale.

## What a future reader should know

1. **A `D:/2026-AI4S/autoresearch/…` path in this repository is a historical address.** It resolves to
   nothing. Do not "repair" it in the two record files above; the address is the datum.
2. **The live project is `E:/2026-AI4S/autoresearch`.** Any new script must use **relative** paths, so
   that the next move costs nothing.
3. **`D:` remains at 98 %.** It is not a working target. Corpus work goes to `E:`.
