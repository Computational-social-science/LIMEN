#!/usr/bin/env python
"""smoke_predict_multilingual.py -- smoke test for the MULTILINGUAL Laya artifact.

WHY THIS EXISTS
    `config/pin_laya.json` pins the ROOT checkpoint of `convaiinnovations/laya`, which is
    English at the tokenizer level: measured with the pinned revision's own tokenizer, its
    50,368-token vocabulary contains no CJK, Hangul, Arabic, Devanagari or Thai tokens, and
    those scripts fall back to UTF-8 bytes (Chinese 2.07 tokens/character, Japanese 1.62,
    against English 0.27). `smoke_predict.py` therefore proves the pin runs, but for the
    ROOT only, and it hardcodes `router.load("english")`.

    A Phase II channel in a non-Latin script needs an instrument that READS that script.
    This revision ships a second artifact in its `multilingual/` subtree: separate weights
    (`model.safetensors`, 643,835,514 B), a 34,363,188 B tokenizer and its own encoder
    config. Because the pin fixes PER-FILE SHA-256, that is a DIFFERENT INSTRUMENT rather
    than a subdirectory of the existing one -- so it gets its own pin
    (`config/pin_laya_multilingual.json`) and its own smoke test, which is this file.

WHAT THIS PROVES, AND WHAT IT DOES NOT
    Proves: the multilingual artifact runs locally from the pinned revision through the
    same `state x typed questions -> probabilities` interface, that the router selects it,
    and that it returns per-question probabilities for Japanese and Chinese items as well
    as English. That is the evidence criterion (iii) of Phase II pre-registration section 5
    asks for -- "the instrument can be pinned at a revision that reads the channel".

    Does NOT prove: any Phase II result. There is no noise (lambda = 0), no gold label and
    no accuracy. The English items are here as the SENSITIVITY CONTROL that sections 5.5
    and 12 require when an artifact changes: the same items the root pin answers, run
    under the new artifact, so that a later cross-artifact difference is attributable to
    the channel rather than to the artifact.

RUN (this host reaches HuggingFace only through hf-mirror.com; no API key anywhere)
    unset PYTHONPATH
    export HF_ENDPOINT=https://hf-mirror.com
    python measurement/smoke_predict_multilingual.py

    `unset PYTHONPATH` is defensive and load-bearing: if the shell exports another venv on
    PYTHONPATH its packages shadow this interpreter's site-packages and `import transformers`
    fails (measured on this host).
"""
from __future__ import annotations

import argparse
import json
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# The wire format, the frozen confidence rule and the Q0 question set are SINGLE-SOURCE
# here: this script imports them rather than restating them, so the two smoke tests cannot
# drift apart in what they measure.
from smoke_predict import ITEMS as ENGLISH_ITEMS, frozen_confidence, q0  # noqa: E402

REVIEWED_SHA = "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"

# --- Hand-written items in the two non-Latin scripts --------------------------------
# Same domain and same Q0 questions as the English items, so the three languages are
# PARALLEL by construction rather than merely similar. Each `reading` is the author's
# plain-language gloss, kept to interpret the noul answers; it is NOT a gold label and no
# accuracy is computed from it. lambda = 0 throughout (no noise is applied anywhere).
NON_LATIN_ITEMS = [
    {
        "item_id": "smoke_ja_01",
        "script": "Japanese",
        "state": ("今月、サブスクリプションの料金が二重に請求されました。同じカードで二回引き落とされており、"
                  "二回目は承認していません。重複した請求を返金してください。"),
        "reading": "billing / duplicate charge / refund requested",
    },
    {
        "item_id": "smoke_ja_02",
        "script": "Japanese",
        "state": ("先週スマートフォンを変えてからアカウントにサインインできません。パスワード再設定のメールが"
                  "届かず、明日の朝のチームレビューまでにアクセスを復旧する必要があります。"),
        "reading": "access / cannot sign in / urgent deadline",
    },
    {
        "item_id": "smoke_zh_01",
        "script": "Chinese",
        "state": "这个月我的订阅被重复扣款了两次。两笔都扣在同一张卡上，第二笔我并没有授权。请退还重复的扣款。",
        "reading": "billing / duplicate charge / refund requested",
    },
    {
        "item_id": "smoke_zh_02",
        "script": "Chinese",
        "state": "我上周换了手机，现在无法登录我的账户。密码重置邮件一直没有收到，而我需要在明天早上团队评审之前恢复访问。",
        "reading": "access / cannot sign in / urgent deadline",
    },
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Pinned-Laya smoke test for the MULTILINGUAL "
                                             "artifact, across English, Japanese and Chinese.")
    ap.add_argument("--revision", default=REVIEWED_SHA,
                    help="Hub revision to pin (default: the reviewed SHA shared with the root pin).")
    ap.add_argument("--device", default=None, help="'cuda', 'cpu', or omit for automatic selection.")
    ap.add_argument("--variant", default="multilingual",
                    help="Router variant to exercise (default: multilingual).")
    args = ap.parse_args()

    import torch
    import laya
    from huggingface_hub import constants as hub_constants
    from laya import Router

    print("=" * 78)
    print(f"Pinned-Laya smoke test -- {args.variant} artifact, English / Japanese / Chinese")
    print("=" * 78)
    print(f"python       : {sys.version.split()[0]}")
    print(f"laya         : {laya.__version__}")
    print(f"torch        : {torch.__version__}  cuda_available={torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"gpu          : {torch.cuda.get_device_name(0)}")
    print(f"hf endpoint  : {hub_constants.ENDPOINT}")
    print(f"revision pin : {args.revision}")
    print(f"variant      : {args.variant}")
    print()

    router = Router(device=args.device, revision=args.revision)
    agent = router.load(args.variant)      # builds/downloads the pinned artifact
    print(f"checkpoint   : repo={agent.model_id!r} subfolder={agent.subfolder!r}")
    print(f"resolved rev : {getattr(agent, 'revision', None)}")
    print(f"device used  : {agent.device}")
    print()

    routed_models: set[str] = set()
    for item in ENGLISH_ITEMS + NON_LATIN_ITEMS:
        result = router.predict(item["state"], q0())
        routing = result.get("routing", {}) or {}
        routed_models.add(str(routing.get("model")))
        print("-" * 78)
        print(f"item {item['item_id']}   script={item.get('script', 'English')}")
        print(f"  routing : model={routing.get('model')!r}  repo={routing.get('repo')!r}")
        print(f"            reason={routing.get('reason')!r}")
        if "reading" in item:
            print(f"  reading : {item['reading']}   (author's gloss, NOT a gold label)")
        print(f"  state   : {item['state']}")
        answers = result.get("answers", {})
        for qid in ("intent", "ok", "escalate"):
            ans = answers.get(qid)
            if not ans:
                print(f"  {qid:9s} -- absent from the response")
                continue
            if ans.get("type") == "choice":
                probs = list(ans["probabilities"].values())
                c = frozen_confidence("choice", probs)
                pretty = "  ".join(f"{k}={v:.4f}" for k, v in ans["probabilities"].items())
                print(f"  {qid:9s}[choice] p = {pretty}")
                print(f"           argmax={ans.get('choice')!r}   c = max_j p_j = {c:.4f}")
            else:
                p_true = float(ans["noul"])
                c = frozen_confidence("noul", (1.0 - p_true, p_true))
                print(f"  {qid:9s}[noul]   p(true)={p_true:.4f}  p(false)={1.0 - p_true:.4f}   "
                      f"c = max(p,1-p) = {c:.4f}")
        print()

    print("=" * 78)
    print("SUMMARY")
    print(f"  variant exercised : {args.variant}")
    print(f"  resolved revision : {getattr(agent, 'revision', None)}")
    print(f"  routers observed  : {sorted(routed_models)}")
    reads_non_latin = any(m == args.variant for m in routed_models)
    print(f"  non-Latin items answered by the {args.variant} router: {reads_non_latin}")
    print()
    if reads_non_latin:
        print("  PASS - the pinned multilingual artifact runs locally and answers Japanese and")
        print("         Chinese items through the frozen wire format. Criterion (iii) of Phase II")
        print("         section 5 is satisfied for a non-Latin channel, subject to the English")
        print("         sensitivity comparison the pre-registration requires for a new artifact.")
        return 0
    print("  FAIL - the non-Latin items were not routed to the multilingual artifact, so this")
    print("         run does not show that the pin reads the channel. Nothing is concluded.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
