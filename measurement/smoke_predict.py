#!/usr/bin/env python
"""smoke_predict.py -- pinned-Laya smoke test for the Phase I wire format.

WHAT THIS PROVES
    The programme pins one English-capable System One artefact (protocol 3.2), now
    `convaiinnovations/laya` -- the English root checkpoint (Apache-2.0). This script
    is the minimal end-to-end check that the pin runs locally on this machine, and
    that the `state x typed questions -> probabilities` interface returns per-question
    probabilities for new hand-written English items in the protocol's wire format
    (3.1), with the frozen confidence rule (3.3) computed from those probabilities.

WHAT THIS IS NOT
    Not a protocol result: no typo noise (lambda = 0), no gold labels, no accuracy.
    Nothing is trained, fine-tuned, or temperature-refit. The checkpoint is used
    exactly as shipped -- including the per-(question type, option count) temperature
    map its own `rl_agent_config.json` carries and the package applies; this script
    neither changes nor fits any temperature.

PIN
    Revision: the package's own reviewed commit SHA for `convaiinnovations/laya`
    (laya 0.3.26, `laya/revisions.py: PINNED_REVISIONS`):
        55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851
    Override with --revision (e.g. --revision main to follow the default branch).

RUN (this host reaches HuggingFace only through hf-mirror.com; no API key anywhere)
    unset PYTHONPATH
    export HF_ENDPOINT=https://hf-mirror.com
    C:/Python314/python.exe E:/2026-AI4S/autoresearch/measurement/smoke_predict.py

    The first run downloads the checkpoint into the HuggingFace cache (~808 MB);
    every run after that is offline. `unset PYTHONPATH` is defensive: if the shell
    exports another venv on PYTHONPATH, its packages shadow this interpreter's
    site-packages and `import transformers` fails (measured on this host).
"""
from __future__ import annotations

import argparse
import json
import sys

REVIEWED_SHA = "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"

# --- The Phase I Q0 (protocol 3.1): one choice + two noul questions -------------
# `intent` is `choice` with caller-defined option keys and criteria. `ok` and
# `escalate` are `noul` with the frozen instructions from 3.1; the wire format
# shows no criteria for them, and the package resolves each noul as its own fixed
# false:/true: option pair (the pair the model card's label-following caveat #156
# concerns).
INTENT_CRITERIA = {
    "billing": "payments, invoices, charges, refunds",
    "access": "sign-in, passwords, permissions, account access",
    "urgency": "an outage or a deadline that needs immediate action",
    "info": "a general-information request that needs no account action",
}


def q0() -> dict:
    """The frozen Q0 question set, in the protocol's wire format."""
    return {
        "intent": {"type": "choice",
                   "instructions": "Which category should this request be routed to?",
                   "criteria": dict(INTENT_CRITERIA)},
        "ok": {"type": "noul",
               "instructions": "Is the request clear enough to act on?"},
        "escalate": {"type": "noul",
                     "instructions": "Should a human handle this?"},
    }


# --- Hand-written English items (clean text, lambda = 0) ------------------------
# Domain: short service / routing intents (billing, access, urgency, info), per
# protocol 4.3. "Reading" is the author's plain-language reading of the item, kept
# only to interpret the noul answers in the report; it is NOT a gold label and no
# accuracy is computed from it.
ITEMS = [
    {
        "item_id": "smoke_en_01",
        "state": ("Hi, I was charged twice for my subscription this month. Both charges "
                  "are on the same card and the second one was not authorized. Please "
                  "refund the duplicate charge."),
        "reading": {"intent": "billing", "ok": "true", "escalate": "false"},
    },
    {
        "item_id": "smoke_en_02",
        "state": ("I changed phones last week and now I cannot sign in to my account. "
                  "The password reset email never arrives, and I need access restored "
                  "before my team's review tomorrow morning."),
        "reading": {"intent": "access", "ok": "true", "escalate": "either"},
    },
    {
        "item_id": "smoke_en_03",
        "state": ("Something is wrong with my account. Please look into it and let me "
                  "know what you find. Thanks."),
        "reading": {"intent": "ambiguous (access or info)", "ok": "false",
                    "escalate": "plausibly true"},
    },
]


def frozen_confidence(mode: str, probs) -> float:
    """Protocol 3.3, computed from the returned probabilities alone.

    choice: c = max_j p_j
    noul:   c = max(p, 1-p), with p = P(true)
    """
    if mode == "choice":
        return max(probs)
    p = probs[1]
    return max(p, 1.0 - p)


def main() -> int:
    ap = argparse.ArgumentParser(description="Pinned-Laya smoke test for the Phase I "
                                             "wire format (3.1), English only.")
    ap.add_argument("--revision", default=REVIEWED_SHA,
                    help="Hub revision to pin (default: the package's reviewed SHA "
                         "for convaiinnovations/laya).")
    ap.add_argument("--device", default=None,
                    help="'cuda', 'cpu', or omit for automatic selection.")
    args = ap.parse_args()

    import torch
    import laya
    from huggingface_hub import constants as hub_constants
    from laya import Router

    print("=" * 78)
    print("Pinned-Laya smoke test -- Phase I wire format (3.1), English only")
    print("=" * 78)
    print(f"python       : {sys.version.split()[0]}")
    print(f"laya         : {laya.__version__}")
    print(f"torch        : {torch.__version__}  cuda_available={torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"gpu          : {torch.cuda.get_device_name(0)}")
    print(f"hf endpoint  : {hub_constants.ENDPOINT}")
    print(f"revision pin : {args.revision}")

    router = Router(device=args.device, revision=args.revision)
    agent = router.load("english")          # builds/downloads the pinned checkpoint
    print(f"checkpoint   : repo={agent.model_id!r} subfolder={agent.subfolder!r}")
    print(f"resolved rev : {getattr(agent, 'revision', None)}")
    print(f"device used  : {agent.device}")
    print()

    for item in ITEMS:
        result = router.predict(item["state"], q0())
        routing = result.get("routing", {})
        print("-" * 78)
        print(f"item {item['item_id']}")
        print(f"  routing : model={routing.get('model')!r}  repo={routing.get('repo')!r}")
        print(f"            reason={routing.get('reason')!r}")
        print(f"  state   : {item['state']}")
        answers = result.get("answers", {})
        for qid in ("intent", "ok", "escalate"):
            ans = answers[qid]
            if ans.get("type") == "choice":
                probs = list(ans["probabilities"].values())
                c = frozen_confidence("choice", probs)
                pretty = "  ".join(f"{k}={v:.4f}" for k, v in ans["probabilities"].items())
                print(f"  {qid:9s}[choice] p = {pretty}")
                print(f"           argmax={ans['choice']!r}   "
                      f"c = max_j p_j = {c:.4f}   "
                      f"(model answer_confidence={ans.get('answer_confidence')})")
            else:
                p_true = float(ans["noul"])
                c = frozen_confidence("noul", (1.0 - p_true, p_true))
                print(f"  {qid:9s}[noul]   p(true)={p_true:.4f}  p(false)={1.0 - p_true:.4f}   "
                      f"c = max(p,1-p) = {c:.4f}   "
                      f"(model confidence={ans.get('confidence')})")
        usage = result.get("usage")
        if usage:
            print(f"  usage   : {json.dumps(usage, ensure_ascii=False)}")
        print()

    print("=" * 78)
    print("smoke test complete -- the probabilities above are the pinned checkpoint's "
          "own outputs; the only transformation applied is the one its shipped "
          "config carries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
