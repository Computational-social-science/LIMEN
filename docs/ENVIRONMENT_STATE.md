# Environment state, 2026-10-13: Python 3.15.0 and BootLoops

Recorded because both change what the repository can resolve implicitly, and the
`CURRENT_OBJECT.md` rule applies: **a declaration in a document is not an available
tool; a call that returns is.** Both were checked by calling them.

---

## 1. Python 3.15.0 is now the `py` launcher default

| resolver | resolves to | has the project's stack? |
|---|---|---|
| `py` (launcher, now marked `*`) | **3.15.0** | **no** |
| `python` on PATH | 3.14.5 (`C:\Python314`) | no |
| `.guard-python` (explicit) | Hermes 3.14.7 | **yes** |
| `sys.executable` inside any repo script | whatever started it | inherits |

**3.15.0 is at `C:\Users\Administrator\AppData\Local\Python\pythoncore-3.15-64\python.exe`.**
It carries `pandas 3.0.6`, `numpy 2.5.4`, `pyarrow 26.0.0` — and **none** of
`torch`, `transformers`, `laya`, `matplotlib`, `rapidfuzz`, `pypinyin`, `scipy`.

**This is the exact failure mode BootLoops' own config records**: *"BATTERIES.json
hardcodes `python3`, which resolved to the system interpreter with no dependencies"*
→ 15 failures. The mechanism is silent: the interpreter runs, the import fails
later, and the error names the module rather than the resolver.

**Why the repository is not broken by it.** Every subprocess in
`scripts/` and `measurement/` uses `sys.executable` (verified across 12 call sites),
so a script inherits the interpreter that started it and never re-resolves. The
guard suite is pinned by `.guard-python`, which names the Hermes 3.14.7 path
explicitly. So the change is **latent, not active**.

**The one live exposure.** `py` and bare `python` now both resolve to an interpreter
without the project's dependencies. Anything that hardcodes `python3` — the pattern
BootLoops was bitten by — would break. Nothing in this repository does, but the
`external-data` tooling and any future script are the risk surface.

**Recommendation:** leave `.guard-python` pointing at Hermes 3.14.7. Do **not**
"upgrade" the project to 3.15: the pinned instrument (`laya @ 55cf4c4e`) needs
`torch`/`transformers`, which 3.15 does not have, and the whole point of the pin is
that the instrument does not move. 3.15 is available and unused, which is the
correct state for it here.

## 2. BootLoops is installed and its skills are the useful part

| | |
|---|---|
| root | `E:\2026-AI4S\bootloops` (toolkit, 52 packages under `tools/`, 12 skills under `skills/`) |
| shared config | `C:\Users\Administrator\.bootloops\config.json` |
| skills installed | `C:\Users\Administrator\AppData\Local\hermes\skills\bootloops\` — 13 directories |
| runs on | **WSL Ubuntu only**, by its own declaration |

**The platform limit is real and stated by the toolkit itself**: *"NOT Windows:
`signal.SIGALRM` and the `resource` module do not exist there, and
`run_selftests.py` itself dies decoding the local code page."* WSL is present
(`Ubuntu`, stopped; `docker-desktop`, running), so the toolkit is reachable there —
but it was **not** invoked, because nothing in the current bottleneck needs it.

**The skills, however, are plain `SKILL.md` documents and they apply directly.**
Thirteen of them, of which four bear on the work in this repository:

- **`planted-truth`** — synthetic-truth controls. *Applied this session*: it
  falsified two claims I had made about Proposition A
  (`docs/PLANTED_TRUTH_CONTROL.md`).
- **`acceptance-gate`** — what "done" means. *"A result is done when it has survived
  a check that could have failed, run by a route that could not have known the
  answer."* Directly relevant to the Phase I seal.
- **`independence-bookkeeping`** — the one-way contamination rule and the reference
  ledger. Relevant to whether the confirmatory analysis and its checks share code.
- **`referee-sim`**, **`ref-check`**, **`prose-lint`**, **`reading-contract`**,
  **`timing-discipline`**, **`tool-stewardship`** — not yet examined in this session.

**Note on visibility.** These skills live under the **Hermes** skill tree. This
session's DSH catalog does **not** list a `bootloops` category, so they are not
auto-loaded here. They are readable as files, and that is how `planted-truth` was
applied. Treating them as "installed and available" would repeat the error the
config file itself warns about.

## 3. What was NOT done, and why

- **BootLoops was not activated.** Its toolkit is physics/loop-integral tooling
  (`abacus`, `kira-stack`, `popcorn`, `seedling`) with no bearing on typing-error
  measurement, and its own config says Windows cannot run it. Invoking it would be
  the "toolbox is not contamination, but a toolbox report is not evidence" error in
  reverse: using a tool because it is present rather than because it answers a
  question the programme has.
- **The project was not moved to 3.15.** The pinned instrument must not move.
- **No dependency was installed.** The correct fix for a missing dependency is to
  point at the interpreter that has it (`.guard-python`), not to duplicate the
  environment — a mistake made and corrected earlier in this session.
