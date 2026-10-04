# Arm 0 audit: what it cost, and where the cost went

Recorded 2026-10-03, after the observation that arm 0's 18 hours is not a minimal cost and that the
result resting on it may not be sound. Both halves of that observation are correct, and this file
records what was checked, what was excluded, and what remains unexplained.

## What arm 0 cost

| | RSI-Jev v1.0 (2B, H100) | Arm 0 (0.6B, RTX 4070) | ratio |
|---|---|---|---|
| `steps` | 1,500 | 1,500 | 1 |
| `batch_size` | 16 | 16 | 1 |
| `n_train_cases` | 6,277 | 6,277 | **1 — identical** |
| `train_seconds` | **908** (15.1 min) | **62,741** (17.4 h) | **69×** |
| `final_loss` | 0.6075 | 0.6626 | — |
| `tower_keys` | 319 | 309 | (different architectures) |

Per-step: theirs **0.605 s**, ours **41.8 s**.

The 69× is against a model **3.3× smaller**. Accounting for it: an H100 runs bf16 GEMMs at roughly
10–11× an RTX 4070, and the model is 3.3× smaller, so the explained ratio is about **3.3×**. The
unexplained factor is about **21×**.

`nvidia-smi` reports 100 % GPU utilisation for this run. That reading is not evidence of throughput:
it means a kernel was resident during the sampling window, and a stream of small kernels reports
100 % just as a saturated GEMM does. The arithmetic says otherwise — 4,496 tokens per step through
a 0.6B model is ~1.6e13 FLOPs, which over 41.8 s is **~390 GFLOPS, or 0.43 % of the card's bf16
peak**.

## What was excluded (four hypotheses, each falsified by measurement, not argument)

1. **The per-step encode.** `encode_question` + `collate` for a batch of 16 measures **0.005 s**, i.e.
   0.01 % of the step. Measured directly, at 0.5 ms per question.
2. **A tower pass per option.** `encode.py` lays the state and every option into **one** sequence,
   with `option_index` pointing at the last token of each option's block. One tower pass per example,
   not one per option.
3. **Padding waste.** `EncodeConfig.max_length` is 2048, which invited the hypothesis that each batch
   is padded to it. Measured: `collate` pads to the batch maximum. A 16-example batch of
   239/219/216/235/207/218/230/199/190/202/155/268/269/276/281/139 tokens collates to **(16, 281)**
   — a fill factor of **1.00×**, no waste.
4. **The recipe.** The spec is field-for-field identical to the published `meta.json` on every
   load-bearing key (`lr_base 5e-06`, `lr_head 0.0001`, `steps`, `batch_size`, `freeze_base=False`,
   `freeze_embeddings=True`, `option_order='shuffled'`, `grad_checkpointing`, `min_trainable_tower`),
   with one recorded deviation (`eval_batch_size` 32→8). `scripts/check_arm0_spec.py`: 83/83.

`torch 2.13.0+cu126` on SM 8.9 is what the run used and what is installed; the README's "torch 2.10"
is stale, the run's own record is not.

## What was checked on the result side, and holds

The metric is computed correctly. Pooled top-1 over `typed_decisions` test, n = 2,000
(600 `choice` + 600 `noul` + 800 `score`):

- arm 0, canonical: (0.5600×600 + 0.6367×600 + 0.5463×800) / 2000 = **0.5775** ✓
- zero-shot control, canonical: (0.3767×600 + 0.5567×600 + 0.3063×800) / 2000 = **0.4025** ✓

Both reproduce the figures the records report, from the records themselves.

## The remaining hypothesis, and it has this project's own measurement behind it

Per-step time grows with run length:

| run | steps | s/step |
|---|---|---|
| 1-step probe | 1 | 2 |
| 3-step probe | 3 | 9 |
| heartbeat test | 5 | 47 |
| **arm 0** | **1,500** | **42** |

A one-step run is **20× faster per step** than a long run of the same code, weights and batch.

`scripts/check_arm0_spec.py` already records the mechanism, from a measurement made for a different
purpose: at `eval_batch_size: 32` the run "sits at 11,583 / 12,282 MiB = **94%** and spend over 61
minutes on the evaluation that 8 finishes in 15.6, **because at 94% of capacity the allocator
thrashes**."

Arm 0 peaked at **11,807 / 12,282 MiB = 96 %**.

So the hypothesis is that arm 0 spent its 18 hours in the allocator-thrashing regime, and that the
21× is fragmentation at the edge of VRAM rather than arithmetic. It is testable at a fraction of
arm 0's cost: the heartbeat driver records per-step seconds, so a 100-step run shows where and how
the per-step time degrades, and a second 100-step run under
`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` is the control.

## What this means for the objective

The pre-registered predictions are P1–P5. Scored against measurements this project already had,
without a new run: **P1 confirmed, P4 confirmed, P5 not supported** (the order gap closed rather
than opened), **P3 supported at 0.8B by the source's own record**. Only **P2** — where the plateau
sits — needs arms.

P2 needs a noise floor to interpret an arm's effect size, and the source supplies its own. Their
per-seed sd is quoted at 0.011–0.016, and their "difference of two 3-seed means has an sd of about
0.010". Back-deriving: per-seed sd = 0.010 × √3 = **0.0173**. Decomposing that against our
evaluation's sampling error at n = 2,000, `sqrt(p(1-p)/n)` = **0.0106**, leaves a **training-seed sd
of 0.0137** — larger than the evaluation noise, so it cannot be ignored.

Consequences for any arm we run:

| seeds per arm | sd of the arm-mean | sd of a two-arm difference | gate +0.020 in σ |
|---|---|---|---|
| 1 | 0.0173 | 0.0245 | **0.82** |
| 3 | 0.0100 | 0.0141 | **1.41** |
| 5 | 0.0077 | 0.0110 | 1.83 |

The source's own 3-seed gate is a **σ≈1.4** test. They say so themselves: "The bar was above the
resolution … the run was not powered to find what it was looking for." An arm therefore costs
**three** trainings, and at arm 0's measured 17.4 h that is **52 h per arm**.

**The 21× is therefore on the critical path: while it stands, P2 cannot be settled at any acceptable
cost, and no arm should be launched.** Two candidate arms had been sketched before this audit; both
are withdrawn pending it.
