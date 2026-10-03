#!/usr/bin/env python
"""
calibrate_against_release.py -- evaluate the source's own released checkpoint with OUR harness,
against the number they published for it.

WHY THIS EXISTS, AND WHY IT COMES BEFORE ANY EXPERIMENT
    This project changed the backbone before checking that its pipeline reproduces a known answer.
    The source published `typed_decisions` 0.6525 at 2B and 0.6175 at 0.8B, with the checkpoints and
    a verify.json carrying the exact per-target figures. Those are free calibration targets. They were
    never used, so a defect anywhere in the encode path, the readout, the metric or the harness would
    have surfaced as "the 0.6B scores 0.5775" and looked like a result.

    This runs THEIR weights through OUR code and compares. A match makes every number this project
    has produced comparable; a mismatch finds the defect for the cost of one evaluation instead of
    another seventeen hours.

WHAT IS HELD FIXED, AND WHY THAT MATTERS
    The loader below mirrors the checkpoint's own `code/load_release.py` operation for operation --
    read meta.json, load the base, load the tower with strict=False and reject any missing key that
    is not the embedding, build ArchConfig from the spec, load the scorer, move the scorer back to
    fp32, set eval mode. The ONE change is that the base weights come from a local directory rather
    than from `meta["base_model"]`, which is a Hub id and would otherwise be re-downloaded.

    The evaluator is `rsijev.evaluate.predict` and the metric is the same pooled top-1 the records
    use, computed the same way: for each question, the option whose probability is highest, compared
    against `gold_label`. Nothing here is reimplemented.

WHAT THE ANSWER MEANS
    Their verify.json reports agreement_with_record = 1.0, so their checkpoint, their score and their
    published number are mutually consistent. Therefore our harness must reproduce

        typed_decisions/canonical   0.6175   (n=2000)
        typed_decisions/reversed    0.6210   (n=2000)
        mmlu_pro_1k/canonical       0.2690   (n=1000)

    A deviation is a defect in our evaluation path, and it is a defect that would have been
    invisible without this run.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from paths import published_release, require, v1_env  # noqa: E402

# The published targets, read from the checkpoint's own verify.json rather than typed here. A
# target copied by hand is one that can silently disagree with the artefact it names.
def published_targets(ckpt: pathlib.Path) -> dict:
    v = ckpt / "verify.json"
    if not v.is_file():
        return {}
    d = json.loads(v.read_text(encoding="utf-8"))
    return {k: {kk: vv for kk, vv in val.items()}
            for k, val in (d.get("verify") or {}).items()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--ckpt", required=True, help="the released checkpoint directory")
    ap.add_argument("--base", required=True, help="local directory holding the base weights")
    ap.add_argument("--batch-size", type=int, default=8,
                    help="their spec says 32; 8 is this host's measured point before the allocator "
                         "thrashes. The metric does not depend on it, and the run records which was used.")
    ap.add_argument("--out", default=None, help="write the calibration JSON here")
    a = ap.parse_args()

    ckpt = pathlib.Path(a.ckpt)
    base = pathlib.Path(a.base)
    if not (ckpt / "meta.json").is_file():
        raise SystemExit(f"[fatal] no meta.json in {ckpt}")
    if not (base / "config.json").is_file():
        raise SystemExit(f"[fatal] no config.json in {base} -- is that a model directory?")

    env = require(v1_env(), "the v1.0 code environment")
    sys.path.insert(0, str(env))
    sys.path.insert(0, str(env / "scripts"))

    import torch
    from safetensors.torch import load_file
    from transformers import AutoTokenizer
    from rsijev.arch import ArchConfig, DecisionModel
    from rsijev.contract import gold_label
    from rsijev.encode import EncodeConfig
    from rsijev.evaluate import predict
    from rsijev.targets import load_mmlu_pro_1k, load_typed_decisions

    meta = json.loads((ckpt / "meta.json").read_text(encoding="utf-8"))
    spec = meta["spec"]
    print(f"[calibrate] checkpoint : {ckpt}")
    print(f"[calibrate] meta base  : {meta['base_model']}  (loaded from {base})")
    print(f"[calibrate] their run  : train_seconds {meta['train_seconds']} "
          f"final_loss {meta['final_loss']:.6f} n_train_cases {meta['n_train_cases']}")
    print(f"[calibrate] environment: {env}")

    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(str(base))

    # WHICH CLASS, AND WHY IT IS NOT AutoModelForCausalLM
    #   The base config declares `architectures: ['Qwen3_5ForConditionalGeneration']` and carries no
    #   top-level `vocab_size` -- it lives in `text_config`. AutoModelForCausalLM resolves to
    #   Qwen3_5ForCausalLM, which hands the TOP-LEVEL config to Qwen3_5TextModel, and that reads
    #   config.vocab_size. Measured 2026-10-03: AttributeError: 'Qwen3_5Config' object has no
    #   attribute 'vocab_size'. The checkpoint's own load_release.py uses AutoModelForCausalLM and
    #   works in the source's stack (transformers <5.18); it does not in ours (5.3.0).
    #
    #   The tower inside the multimodal wrapper is `model.language_model`: it holds 320 keys and the
    #   checkpoint carries 319, the difference being the frozen embed_tokens. Measured, not assumed.
    from transformers import Qwen3_5ForConditionalGeneration
    lm = Qwen3_5ForConditionalGeneration.from_pretrained(str(base), dtype=torch.float32)
    tower = lm.model.language_model
    missing, unexpected = tower.load_state_dict(load_file(str(ckpt / "tower.safetensors")),
                                                strict=False)
    bad = [k for k in missing if "embed_tokens" not in k]
    if bad or unexpected:
        raise SystemExit(f"[fatal] checkpoint does not match the base: "
                         f"missing {bad[:5]}, unexpected {list(unexpected)[:5]}")
    print(f"[calibrate] tower = model.language_model, {len(missing)} key(s) from the base "
          f"({', '.join(missing[:2]) or 'none'})")

    cfg = getattr(lm.config, "text_config", None) or lm.config
    arch = ArchConfig(readout=spec["readout"], readout_layer=spec["readout_layer"],
                      max_options=spec["max_options"], freeze_base=True,
                      option_pool=spec["option_pool"], residual=spec["residual"],
                      logit_cap=spec.get("logit_cap"),
                      head_input_norm=spec.get("head_input_norm", False),
                      **dict(spec.get("arch_extra") or {}))
    model = DecisionModel(tower, cfg.hidden_size, arch).to("cuda")
    model.scorer.load_state_dict(load_file(str(ckpt / "scorer.safetensors")))
    model.scorer.to(torch.float32)          # never follows the tower down (their own note)
    model.eval()
    print(f"[calibrate] model built in {time.time()-t0:.0f}s")

    targets = {"typed_decisions": load_typed_decisions("test"),
               "mmlu_pro_1k": load_mmlu_pro_1k()}
    want = published_targets(ckpt)

    result = {"ckpt": str(ckpt), "base": str(base), "batch_size": a.batch_size,
              "their_run": {k: meta[k] for k in ("train_seconds", "final_loss", "n_train_cases",
                                                 "tower_keys", "tapped_layer",
                                                 "linear_attn_kernel")},
              "targets": {}}

    print(f"\n[calibrate] evaluating (batch {a.batch_size}) ...")
    for tname, cases in targets.items():
        orders = ["canonical", "reversed"] if tname == "typed_decisions" else ["canonical"]
        for order in orders:
            t1 = time.time()
            e = EncodeConfig(layout=spec["layout"], option_pool=spec["option_pool"],
                             option_order=order)
            preds = predict(model, tok, cases, e, max_options=spec["max_options"],
                            device="cuda", batch_size=a.batch_size)
            hits = n = 0
            for c, q, p in preds:
                pred = q.options[max(range(len(p.probs)), key=p.probs.__getitem__)]
                hits += int(pred == gold_label(q, c.gold[q.key]))
                n += 1
            got = round(hits / n, 4)
            key = f"{tname}/{order}"
            exp = (want.get(key) or {}).get("pooled_top1")
            delta = None if exp is None else round(got - exp, 4)
            result["targets"][key] = {"ours": got, "theirs": exp, "delta": delta, "n": n,
                                      "seconds": round(time.time() - t1, 1)}
            flag = "" if delta in (None, 0.0) else ("  <-- DEVIATION" if abs(delta) > 0.0005 else "")
            print(f"  {key:26} ours {got:.4f}   theirs {exp if exp is not None else 'n/a'}"
                  f"   delta {delta if delta is not None else 'n/a'}{flag}"
                  f"   (n={n}, {time.time()-t1:.0f}s)")

    exact = [k for k, v in result["targets"].items() if v["delta"] == 0.0]
    off = [k for k, v in result["targets"].items() if v["delta"] not in (None, 0.0)]
    print(f"\n[calibrate] exact matches: {len(exact)}/{len(result['targets'])}"
          + (f"   deviations: {off}" if off else ""))
    if not off:
        print("            => the evaluation path reproduces the source's published numbers exactly.")
    else:
        print("            => the evaluation path does NOT reproduce them. This is a defect in our")
        print("               path, and it would have been invisible without this run.")

    if a.out:
        pathlib.Path(a.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"\n[calibrate] wrote {a.out}")
    return 0 if not off else 1


if __name__ == "__main__":
    raise SystemExit(main())
