# PREDICT smoke test — the pinned Laya checkpoint answers new English items in the §3.1 wire format

**Status:** measured on this machine, 2026-10-04. **Pin:** `convaiinnovations/laya` (English root
checkpoint), revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`.
**Runner:** `D:/2026-AI4S/autoresearch/measurement/smoke_predict.py` (prints; writes no files).
**Scope:** instrument check only. No protocol result: no typo noise (λ = 0), no gold labels, no
accuracy, no training, no temperature refit, no API key. The earlier local 0.8B artefact is
superseded (see `docs/JEV_TOOLBOX_SELECTION.md`); nothing here concerns it.

---

## 1. What was established

1. The pinned checkpoint **downloads and runs locally** on this machine (Windows, git-bash,
   RTX 4070 12 GB) with **no API key and no network at inference time**.
2. `Router().predict(state, questions)` answers **new hand-written English items** in the
   protocol's wire format (§3.1: `intent` choice with per-option criteria, `ok` noul,
   `escalate` noul) and returns **per-question probabilities**.
3. The **frozen confidence rule (§3.3)** was computed here from those probabilities:
   choice `c = max_j p_j`; noul `c = max(p, 1−p)`. The model's own `answer_confidence` /
   `confidence` fields coincide with them to 4 dp on all 9 questions.
4. After the first download the path is **fully offline**: a rerun under `HF_HUB_OFFLINE=1`
   reproduced every number below, byte-identical, in **7 s wall** (load + model build + 9
   questions on the GPU).

## 2. The exact working command

```bash
cd /d/2026-AI4S/autoresearch/measurement
unset PYTHONPATH
export HF_ENDPOINT=https://hf-mirror.com
/c/Python314/python.exe smoke_predict.py
```

* **Environment variables needed:** `HF_ENDPOINT=https://hf-mirror.com` (required — see §7).
  `PYTHONPATH` must be unset/empty (see §7). Nothing else: no API key, no token, no
  `LAYA_REVISION` (the revision is pinned inside the runner; `--revision` overrides it).
* Also verified: runnable from any working directory via the absolute script path
  (`C:/Python314/python.exe D:/2026-AI4S/autoresearch/measurement/smoke_predict.py` → exit 0).
* Offline re-run (evidence that inference is local): prefix `export HF_HUB_OFFLINE=1`.
* First run: ~14 s of downloads from the mirror; every later run is offline.
* Interpreter: `C:/Python314/python.exe` (Python 3.14.5, torch 2.13.0+cu126, CUDA on the
  RTX 4070). It is the host's general-purpose Python with a CUDA-enabled torch; the other
  ordinary installs (Python 3.11/3.12/3.13, miniconda) have no torch or CPU-only builds, and
  the agent runtime's private venv is not an instrument environment.

## 3. Install route that worked

```bash
C:/Python314/python.exe -m pip install -U laya
```

* **laya 0.3.26** from PyPI (pypi.org is reachable directly from this host; the wheel is
  312 KB, pure Python). The machine already had laya 0.3.20 in the user site; the `-U`
  upgrade to 0.3.26 is what the runs above used.
* All dependencies were already satisfied on this host, so nothing else was installed or
  changed: torch 2.13.0+cu126, transformers 5.3.0, safetensors 0.7.0, huggingface_hub 1.33.0,
  numpy 2.4.1. Install location:
  `C:\Users\Administrator\AppData\Roaming\Python\Python314\site-packages`.
* No `[extra]` was needed (no `serve`, `fast`, `onnx`, …).

## 4. The checkpoint the pin resolves to (model version / revision downloaded)

| Field | Value |
|---|---|
| Repo | `convaiinnovations/laya` — root = the English checkpoint (ModernBERT-large, 421 M, 512 ctx, Apache-2.0) |
| **Revision downloaded** | **`55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`** — the package's own reviewed commit SHA (`laya/revisions.py: PINNED_REVISIONS`, laya 0.3.26; `LAYA_REVISION=reviewed` resolves to the same SHA) |
| Mirror `main` HEAD at survey | `7b928d828b7b0e022f929d9bd2e44165aa270148` (mirror API, last modified 2026-10-03T18:00:07Z) — `main` can move; that is why the explicit reviewed SHA is requested |
| HF endpoint that worked | **`https://hf-mirror.com`** (`huggingface.co` times out from this host — measured, 15 s curl timeout; the mirror answers; `huggingface_hub` picks the endpoint up from `HF_ENDPOINT`, verified in-process) |
| Files downloaded (5) | `model.safetensors` 842,609,210 B, sha256 `891102d372688fc2a094dac56a384bc537b87c63f21f9f3dac0be2b7cbc8d86c` · `rl_agent_config.json` 745 B · `encoder/config.json` 2,083 B · `tokenizer/tokenizer.json` 3,583,228 B · `tokenizer/tokenizer_config.json` 308 B |
| Cache location | `C:\Users\Administrator\.cache\huggingface\hub\models--convaiinnovations--laya\snapshots\55cf4c4e...\` |

The runner prints the resolved revision it actually loaded (`resolved rev` line below), so
the revision in use is stated by the run itself, not inferred.

## 5. The items (hand-written, English, clean text — λ = 0)

The frozen Q0 of §3.1 is asked of every item:
`intent` = choice, instructions *“Which category should this request be routed to?”*, criteria
`{billing: "payments, invoices, charges, refunds", access: "sign-in, passwords, permissions,
account access", urgency: "an outage or a deadline that needs immediate action", info: "a
general-information request that needs no account action"}`; `ok` = noul, *“Is the request
clear enough to act on?”*; `escalate` = noul, *“Should a human handle this?”*.

| id | state |
|---|---|
| `smoke_en_01` | Hi, I was charged twice for my subscription this month. Both charges are on the same card and the second one was not authorized. Please refund the duplicate charge. |
| `smoke_en_02` | I changed phones last week and now I cannot sign in to my account. The password reset email never arrives, and I need access restored before my team's review tomorrow morning. |
| `smoke_en_03` | Something is wrong with my account. Please look into it and let me know what you find. Thanks. |

Items 01–02 are written to be clearly actionable; item 03 is deliberately vague (the
`ok` / `escalate` contrast case). The author's readings are kept in the runner for
interpretation only — they are not gold labels and nothing is scored.

## 6. Observed probabilities and confidences (real output)

Combined output of the first successful run (tqdm progress rewrites collapsed to one line;
the two warnings the package emitted are kept in place, labelled `[stderr]`; the
`choice:11+` warning is explained in §7 — it does not apply to any question here):

```text
==============================================================================
Pinned-Laya smoke test -- Phase I wire format (3.1), English only
==============================================================================
python       : 3.14.5
laya         : 0.3.26
torch        : 2.13.0+cu126  cuda_available=True
gpu          : NVIDIA GeForce RTX 4070
hf endpoint  : https://hf-mirror.com
revision pin : 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851
Fetching 5 files: 100%|##########| 5/5 [00:14<00:00, 2.97s/it]
[stderr] The `reference_compile` argument is deprecated and will be removed in `transformers v5.2.0`
[stderr] RuntimeWarning: laya: this checkpoint ships invalid temperatures or values outside [0.5, 5];
         using choice:11+=0.10058280825614929 -> 0.5. Treat confidence from the affected entries as uncalibrated.
checkpoint   : repo='convaiinnovations/laya' subfolder=None
resolved rev : 55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851
device used  : cuda

------------------------------------------------------------------------------
item smoke_en_01
  routing : model='english'  repo='convaiinnovations/laya'
            reason='English Latin text'
  state   : Hi, I was charged twice for my subscription this month. Both charges are on the same card and the second one was not authorized. Please refund the duplicate charge.
  intent   [choice] p = billing=0.9589  access=0.0077  urgency=0.0215  info=0.0119
           argmax='billing'   c = max_j p_j = 0.9589   (model answer_confidence=0.9589)
  ok       [noul]   p(true)=0.7628  p(false)=0.2372   c = max(p,1-p) = 0.7628   (model confidence=0.7628)
  escalate [noul]   p(true)=0.1217  p(false)=0.8783   c = max(p,1-p) = 0.8783   (model confidence=0.8783)
  usage   : {"input_tokens": 233, "output_tokens": 0, "state_tokens": 33, "state_tokens_dropped": 0, "truncated": false, "truncated_questions": []}

------------------------------------------------------------------------------
item smoke_en_02
  routing : model='english'  repo='convaiinnovations/laya'
            reason='English Latin text'
  state   : I changed phones last week and now I cannot sign in to my account. The password reset email never arrives, and I need access restored before my team's review tomorrow morning.
  intent   [choice] p = billing=0.0629  access=0.6756  urgency=0.1978  info=0.0637
           argmax='access'   c = max_j p_j = 0.6756   (model answer_confidence=0.6756)
  ok       [noul]   p(true)=0.4336  p(false)=0.5664   c = max(p,1-p) = 0.5664   (model confidence=0.5664)
  escalate [noul]   p(true)=0.0302  p(false)=0.9698   c = max(p,1-p) = 0.9698   (model confidence=0.9698)
  usage   : {"input_tokens": 239, "output_tokens": 0, "state_tokens": 35, "state_tokens_dropped": 0, "truncated": false, "truncated_questions": []}

------------------------------------------------------------------------------
item smoke_en_03
  routing : model='english'  repo='convaiinnovations/laya'
            reason='English Latin text'
  state   : Something is wrong with my account. Please look into it and let me know what you find. Thanks.
  intent   [choice] p = billing=0.2835  access=0.1057  urgency=0.3346  info=0.2762
           argmax='urgency'   c = max_j p_j = 0.3346   (model answer_confidence=0.3346)
  ok       [noul]   p(true)=0.5662  p(false)=0.4338   c = max(p,1-p) = 0.5662   (model confidence=0.5662)
  escalate [noul]   p(true)=0.0642  p(false)=0.9358   c = max(p,1-p) = 0.9358   (model confidence=0.9358)
  usage   : {"input_tokens": 197, "output_tokens": 0, "state_tokens": 21, "state_tokens_dropped": 0, "truncated": false, "truncated_questions": []}

==============================================================================
smoke test complete -- the probabilities above are the pinned checkpoint's own outputs; the only transformation applied is the one its shipped config carries.
```

Condensed table (c computed here per §3.3; the noul argmax column is the implied yes/no):

| item | question | probabilities | argmax | c |
|---|---|---|---|---|
| 01 | intent | billing 0.9589 / access 0.0077 / urgency 0.0215 / info 0.0119 | billing | 0.9589 |
| 01 | ok | p(true)=0.7628 | true | 0.7628 |
| 01 | escalate | p(true)=0.1217 | false | 0.8783 |
| 02 | intent | billing 0.0629 / access 0.6756 / urgency 0.1978 / info 0.0637 | access | 0.6756 |
| 02 | ok | p(true)=0.4336 | false | 0.5664 |
| 02 | escalate | p(true)=0.0302 | false | 0.9698 |
| 03 | intent | billing 0.2835 / access 0.1057 / urgency 0.3346 / info 0.2762 | urgency | 0.3346 |
| 03 | ok | p(true)=0.5662 | true | 0.5662 |
| 03 | escalate | p(true)=0.0642 | false | 0.9358 |

Notes on precision and provenance:

* All probabilities are **as returned by the interface** — the package emits them rounded to
  4 decimal places; the `c` values are computed from those returned values, exactly as a
  caller would. The model's own confidence fields reproduce the same numbers.
* Two back-to-back offline reruns (`HF_HUB_OFFLINE=1`) produced **byte-identical stdout**
  (clean `diff`; the stderr warnings repeat identically too).
* Probabilities are **post-shipped-calibration**: the checkpoint's own `rl_agent_config.json`
  carries a `temperature_by_options` map and the loader applies it. For the question shapes
  used here the applied temperatures are `choice:3-5 → 1.7601518630981445` (the 4-option
  `intent`) and `noul:2 → 1.983399510383606`. No temperature was refit, changed, or added by
  this test — this is the artefact exactly as shipped.
* `usage` confirms no state truncation on any item (`truncated: false`) and no collapsed
  option spans (`usage["options"]` absent, which the package emits only when the head budget
  collapses options).

## 7. Workarounds and obstacles (what was needed, what was hit)

1. **`unset PYTHONPATH` — needed, and the failure was reproduced exactly.** With the agent
   runtime's venv on `PYTHONPATH`, `import transformers` under `C:/Python314/python.exe`
   dies with
   `ImportError: cannot import name '_regex' from partially initialized module 'regex'`
   (the foreign venv's compiled extension shadows this interpreter's packages). With
   `PYTHONPATH` unset, transformers 5.3.0 + tokenizers 0.22.2 import cleanly. In the shell
   used for the runs `PYTHONPATH` was empty, so the `unset` is precautionary here — but the
   agent runtime on this host puts a foreign venv on `PYTHONPATH` in some tool invocations,
   and that situation reproduced this exact failure, so it stays part of the recorded
   command.
2. **`HF_ENDPOINT=https://hf-mirror.com` — required for the first download.** Measured:
   `huggingface.co` times out (15 s), `hf-mirror.com` serves the API and the five files. The
   runner's header prints the endpoint actually in use. After the download, `HF_HUB_OFFLINE=1`
   reruns complete with no network.
3. **Nothing else was needed.** No OOM (the 0.4 B model on a 12 GB card), no TensorFlow
   deadlock (tensorflow is not installed, so the model card's `USE_TF=0` tip did not apply),
   no modification of any downloaded file (verified: the cached `tokenizer_config.json` is
   byte-identical to the hub original at the pinned revision, md5 `807aa7cea721625dc8728ac062871ce3`),
   no temperature refit, no API key.
4. Two non-blocking stderr warnings, reported for completeness: (a) the loader clamps one
   shipped temperature entry that is outside the package's accepted [0.5, 5] range —
   `choice:11+ = 0.1005828...` → `0.5`, warned as “Treat confidence from the affected entries
   as uncalibrated”. No question in this test has 11+ options, so nothing observed here is
   affected. (b) A transformers deprecation notice that `reference_compile` will be removed
   (laya sets it) — cosmetic under transformers 5.3.0.

## 8. Do the two noul questions track the state or the label pair?

The model card warns that `noul` “can follow its option labels instead of the state” (issue
#156) and instructs to check it on your own data. Raw values only; nothing was refit. Both
noul questions were asked of all three states, so the check has two contrast cases
(items 01/02 clearly actionable; item 03 deliberately vague).

**`ok` — “Is the request clear enough to act on?”.** p(true) = **0.7628 / 0.4336 / 0.5662**.
The values are not stuck: the state moves them, and the two extremes differ. But the ordering
does **not** follow the author's reading — the most concretely actionable item (`smoke_en_02`:
locked out, reset mail missing, deadline) is the only one leaning *no*, while the deliberately
vague item 03 leans slightly *yes*. Two of the three are weak positives (c = 0.57–0.76). At
n = 3 this is an observation, not a finding: `ok` looks state-sensitive but not obviously
state-*tracking*, and it should be checked on the dev bank before either form is frozen (the
selection doc already schedules exactly this as an instrument-calibration item).

**`escalate` — “Should a human handle this?”.** p(true) = **0.1217 / 0.0302 / 0.0642** — a
confident *no* on all three items (c = 0.88–0.97), including item 03, where escalation is a
plausible reading. Three materially different states, nearly the same answer each time: this
is the closest thing to the card's label-pair pattern seen in this smoke test. Three items
cannot distinguish “genuinely no” from “the `false:`/`true:` pair pulled toward no”, so the
honest statement is: on this first look `escalate` did not track these states, its values on
this domain should be treated as suspect, and the dev-side check the card prescribes is
required before it is used as a primary or secondary endpoint.

The two noul questions behaviour is **not identical** (one varies with the state, one does
not), so if there is a label-pair artefact here it is question-specific rather than one global
“no” bias. Both raw patterns are reported as observed; no refit was applied (per instruction).

## 9. What this is not, and limitations

* Not a protocol result and not evidence for any hypothesis: three items, clean text only
  (λ = 0), no noise process, no gold labels, no accuracy, no gate. These items are interface
  evidence, not part of the Phase I confirmatory item bank.
* The `noul` behaviour in §8 is a three-item look at a known weak point, on the root
  checkpoint the selection document already flags as weak zero-shot (0.362 on typed
  decisions); nothing above should change the pre-registered plan.
* The probabilities carry the checkpoint's shipped per-type temperatures (§6); if the
  programme later fits its own calibration on dev — a pre-registered instrument step — those
  numbers will differ from the ones above, and this document records the shipped-artefact
  baseline it will be compared against.

## 10. Files

* Runner: `D:/2026-AI4S/autoresearch/measurement/smoke_predict.py` — prints only; writes no
  files; the only state it creates is the HuggingFace cache entry described in §4.
* This report: `D:/2026-AI4S/autoresearch/docs/PREDICT_SMOKE_TEST.md`.
