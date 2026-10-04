# Reference-frame library — Nature/Science-family papers, converted to agents

**Owner's directive (2026-10-04):** convert classic and relevant reference-frame literature — especially
from the Science/Nature family (Nature main, NHB, NMI, and the Nature-affiliated titles) — into
agent-readable skills using the deployed **paper2agent** toolbox, to serve this programme.

**Why this is not decoration.** The programme's theory (`docs/THEORETICAL_FOUNDATIONS.md`) and its gap
(`docs/GAP_VERDICT.md`) both rest on published constructs: uncertainty calibration, the
confidently-wrong failure, and how humans and models complement each other in a decision loop. A
paper-agent makes each of those bodies of work **queryable inside the programme** rather than recalled
from memory.

---

## 1. The engine, and the hard rules that were paid for

**Engine location.** `D:/2026-AI4S/nhb-llm-mistranslation/` — `paper2agent_repo/` (upstream:
`paper_bundle.py` at `paper2agent_repo/skills/paper2agent/paper2skill/scripts/`) plus the **battle-tested
patches** in that project's `scripts/`.

**The rules below come from a documented audit in that project. They are not re-derived here, and they
take precedence over the toolbox's own documentation where the two disagree.**

| Rule | Why |
|---|---|
| **Execute with the Python interpreter, NOT `uv run`** | `uv run` builds an isolated environment without the project's dependencies; the build then fails quietly. *(This contradicts the toolbox's own skill text — the audit wins.)* |
| **Success is an output contract, not a directory** | `SKILL.md` + `references/` with a real `paper.md`. "A directory exists" proves nothing — the first integration declared success while the build stage never ran. |
| **The build stage is mandatory** | prepare / extract / review-aid alone produce no skill. |
| **`patch_paper2agent_windows.py` once per clone** | Upstream compares Windows backslash paths against POSIX literals and flags its own correct output as invalid. |
| **Repair fences at ITEM level only, and only items the builder emits raw** | Criterion: `kind=='code'` AND text starts with a fence AND internally unbalanced. Repairing all unbalanced items injected 7 spurious fence lines into the shipped `paper.md`. |
| **Never repair at page level** | Page-level repair picks the wrong target and appends spurious fences to already-balanced items; this reached a published artefact. |
| **After repair, re-enter with `--build-only`** | Re-running `extract` overwrites the repairs. |
| **Keep one pristine prepare+extract directory as the baseline** | Counting defects in an edited directory undercounts (10 → 6 on the same PDF). |

**Pipeline:** `patch` → `paper_bundle prepare` → `extract` → `review-aid` → review every page →
`adjudicate_fence_repair` → `repair_item_fences` → `locate_dangling_fence` (must report BALANCED) →
`paper2agent_integration --build-only` → `--verify-only`.

**Note on what this tool is.** It builds a **reading package** — it does not execute the paper's
methods, prompts or code. A paper-agent is therefore a *queryable reference*, and any claim drawn from
one still needs its provenance stated.

## 2. Selection — chosen for the reference frame, not for topical resemblance

| # | Source paper (on disk under `D:/2026-AI4S/`) | What it is the reference frame for | Status |
|---|---|---|---|
| 1 | `2026-Nature-Evaluating large language models for accuracy incentivizes hallucinations` | **The closest published analogue to `SilentError@τ`**: accuracy expressed as a target induces confident wrongness. Directly bears on H1.2. | converting |
| 2 | `2026-NMI-Large language models as uncertainty-calibrated optimizers for experimental discovery` | Calibration of a model's own uncertainty — the DV's upstream literature, and the pin's C1 calibration problem. | converting |
| 3 | `2025-NRP-A cognitive approach to human-AI complementarity in dynamic decision-making` | **The coupled-control-system thesis** — how the human–model loop is formalised, and whether anyone measures *when to defer to the other* (which is our gate). | converting |
| 4 | `!2024-Nature-Detecting hallucinations in large language models using semantic entropy` | The canonical uncertainty-estimation method behind "confidently wrong". | queued |
| 5 | `2026-NHB-The shrinking landscape of linguistic diversity in the age of large language models` | **Phase II's channel question** — language/script diversity under LLM pressure, from the target journal. | queued |
| 6 | `2025-Science-Large AI models are cultural and social technologies` | The programme's own meta-position: what class of artefact a model is. | queued |

**Deliberately not selected**, with reasons: the on-disk *agent-engineering* papers (Nature/NMI pieces
on turning papers into agents, agent failure modes, agentic data) are about the **toolchain**, not the
reference frame — converting them would build agents about agents, not serve the science. The
NeurIPS/ICLR/ACL/AAAI/EACL items are outside the requested venue family.

## 3. What the agents are for — the three questions they must answer

Recorded so the library does not become a shelf:

1. **Calibration.** Is the confidently-wrong failure measured the way we intend to measure it, and has
   anyone already run the experiment our H1.2 proposes? (Papers 1, 2, 4)
2. **The loop.** How is the human–model decision loop formalised, and what — if anything — plays the
   role of our gate `g_τ`? (Paper 3)
3. **The channel.** Is there published evidence that the *orthographic/language* channel behaves as a
   structural variable rather than a nuisance? (Paper 5; cf. `docs/GAP_VERDICT.md` §3)

**A converted paper-agent must be interrogated, not merely installed.** An agent that is built and
never queried has produced nothing.

## 4. Retained output contract

Each conversion must satisfy, and be reported with: `SKILL.md` present; `references/` containing
`index.md` and a non-trivial `paper.md`; file count; `paper.md` byte size; and the `--verify-only`
verdict. **A conversion with no evidence of the contract is not counted as done.** Where a conversion
failed, the error text and the failing stage are recorded here rather than the failure being smoothed
over.

## 5. Provenance

The engine is another project's (`nhb-llm-mistranslation`); its audit notes are the source of §1. The
source PDFs live in `D:/2026-AI4S/` and are **not** copied into this repository — this repository's
`archive/` discipline is unaffected, and the converted agents live in the shared skills directory so
that any project can load them.
