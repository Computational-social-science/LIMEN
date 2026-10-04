# Cost ledger

Time and compute are this project's largest cost, and until now nothing recorded them as a cost.
This file is that record. Every entry is a measurement taken from the artefacts a run left behind,
not an estimate, and every entry names what the spend bought. A spend that bought nothing is
recorded as such rather than omitted.

The rule this file exists to enforce: **no GPU time without a stated question that the run answers,
and no second run until the first one's answer is in hand.**

## Spent

| what | wall | GPU (train) | what it bought |
|---|---|---|---|
| **arm 0** | **18 h 07 m** | **17.43 h** | the v1.0 recipe's number at 0.6B: pooled top-1 0.5775 against a 0.4025 zero-shot anchor. One seed. |
| arm 0's evaluation | 38 min | — | 21,792 scored decisions; the source of 0.5775 and of the order-gap reading |
| arm 0's one-off | ~26 min | — | model + corpus + both evaluation targets loaded |
| 1-step probe | ~8 min | 2 s | that the pipeline completes a step, and that the spec's case count (6,277) matches the source's |
| 3-step probe | ~10 min | 27 s | a first per-step time; also the run the project later ruled invalid for contention |
| 30-step probe | ~1.2 h | ~3207 s | that the loss falls and crosses the frozen control on two targets |
| heartbeat test, training | 7 min | 236 s | that the heartbeat's step counter agrees with the harness's own report — the check that caught a wrapper bug that would have crashed instantly and left a signature indistinguishable from a stalled job |
| heartbeat test, evaluation | **40 min, killed** | — | **nothing.** A 5-step model's evaluation numbers are not a result. Killed once the reading was worthless and it was holding the card; the criterion it was meant to satisfy is already demonstrated at full scale by arm 0's 21,792 records |
| eval_batch_size measurement | 61 min + 15.6 min | — | that 32 does not OOM but sits at 94 % of VRAM, where the allocator thrashes |
| probe attempt 1 (`_probe_ckpt_cost`) | 15 min waiting, 0 run | — | **nothing.** Its design was wrong: 3 steps cannot see a degradation that is a function of step number. Withdrawn before it ran |
| probe attempt 2 (MSYS paths) | ~2 min | — | **nothing.** Failed on a path-translation bug. Recorded because a fast failure is still a spend |

**Total GPU-train time to date: about 24.4 h**, of which **17.4 h is arm 0**. Excluding arm 0, every
other measurement above together cost under 1.5 h of training — the diagnostic short runs are cheap,
and the expensive object is the one full arm.

## The number that makes this urgent

Arm 0's per-step time is **41.8 s**. The source's is **0.605 s** for the same 1,500 steps at 2B on an
H100. The 69× is against a model 3.3× smaller, and hardware plus size explain about 3.3× of it, so
**~21× is unexplained** — see `arm0_audit.md`.

That 21× is not a performance detail, it is the project's feasibility bound:

| | at 41.8 s/step | at 4.2 s/step (10× better) |
|---|---|---|
| one training | 17.4 h | 1.7 h |
| one arm (3 seeds, the source's design) | **52 h** | **5.2 h** |
| 8 arms | 17 days | 1.7 days |

P2 is the only pre-registered prediction that still needs arms, and it needs at least one arm. At the
measured cost, one arm is over two days of a single GPU.

## Scheduled next, and nothing else

| what | expected | the question it answers |
|---|---|---|
| step-curve probe, 2 × 100 steps | 25 min – 2 h | where the per-step time degrades, and whether `expandable_segments:True` removes it |

Nothing is queued behind it. The two candidate arms sketched before the audit are **withdrawn**: at
52 h each they were not affordable, and launching either would have been the same mistake as arm 0
in a new place.

## Not to repeat

- **A probe must span the regime it is testing.** The withdrawn 3-step probe could not have detected
  a step-number-dependent effect no matter what the cause was; it would have returned "no difference"
  for every hypothesis.
- **Pass native paths to native programs.** MSYS path conversion is disabled on this host, so
  `/e/...` reaches python.exe as `\e\...`. Cost of learning it the second time: ~2 min.
- **An evaluation of a model that is not a result is not worth 40 minutes.** The heartbeat's
  evaluation was kept alive past its usefulness and then killed; the decision should have been made
  when the heartbeat's own criterion passed.
