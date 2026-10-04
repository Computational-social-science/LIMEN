#!/usr/bin/env python
"""run_phase1.py -- the Phase I `predict -> JSONL` confirmatory runner.

WHAT THIS IS
    The batch path from the pinned instrument to the protocol's section 3.5 trial record.
    One row per (item, lambda, noise_seed, question_id). This is the mechanical piece the
    confirmatory run needs; it is deliberately kept separate from analysis, so the record is
    written before anything reads it.

CONTRACT
    - The noise is `typo_noise(state, item_id, lam, seed)` verbatim: a pure function of
      (item_id, lam, seed), so a re-run reproduces the same text and the same op list.
    - The confidence rule is the protocol's section 3.3, computed from the returned
      probabilities alone: choice -> c = max_j p_j ; noul -> c = max(p, 1-p).
    - `error` is defined ONLY where the bank carries gold. The `ok` and `escalate` questions
      have no gold in this bank, so their `error` is null rather than 0 -- writing 0 there
      would silently claim they were answered correctly.
    - `silent_error[t]` = 1 iff the answer is wrong AND confident, i.e. error == 1 and c >= t.
    - `action[t]` = the gate: "answer" if c >= t else "defer".
    - Every attempted trial is recorded, including failures (pre-registration item 10).
      A failed call writes a row with status="failure" and the error text; it is never
      silently dropped, and it never counts as a correct answer.

RESUME
    Re-running with the same --out skips any (item_id, lambda, noise_seed, question_id) already
    present. Interrupting and re-running is therefore safe and cheap. This matters: a
    confirmatory run that cannot resume is a run that gets lost.

RUN (this host reaches HuggingFace only through hf-mirror.com; no API key anywhere)
    unset PYTHONPATH
    export HF_ENDPOINT=https://hf-mirror.com
    python measurement/run_phase1.py \
        --bank measurement/pilot_items.jsonl \
        --out  measurement/trials_smoke.jsonl \
        --lambdas 0 0.05 --seeds 0 --limit 5
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from typo_noise import typo_noise, realised_edit_rate  # noqa: E402

# The package's own reviewed revision; see config/pin_laya.json.
PINNED_REVISION = "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"
TAUS = (0.80, 0.90)
QUESTIONS = ("intent", "ok", "escalate")


def frozen_confidence(mode: str, probs) -> float:
    """Protocol 3.3. choice: max_j p_j. noul: max(p, 1-p) with p = P(true)."""
    if mode == "choice":
        return max(probs)
    p = probs[1]
    return max(p, 1.0 - p)


def q0_of(item: dict) -> dict:
    """Rebuild the frozen Q0 from the bank entry, so the bank is the only source of items."""
    q = {}
    for qid in QUESTIONS:
        spec = item.get(qid)
        if not spec:
            continue
        entry = {"type": spec["type"], "instructions": spec["instructions"]}
        if spec.get("criteria"):
            entry["criteria"] = spec["criteria"]
        q[qid] = entry
    return q


def load_bank(path: pathlib.Path) -> list:
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def done_keys(out: pathlib.Path) -> set:
    """(item_id, lambda, noise_seed, question_id) already recorded, for resume."""
    if not out.is_file():
        return set()
    keys = set()
    for ln in out.read_text(encoding="utf-8", errors="replace").splitlines():
        if not ln.strip():
            continue
        try:
            r = json.loads(ln)
        except Exception:
            continue
        keys.add((r.get("item_id"), r.get("lambda"), r.get("noise_seed"), r.get("question_id")))
    return keys


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase I predict -> JSONL runner.")
    ap.add_argument("--bank", required=True, help="item bank JSONL (gold locked, see ITEM_BANK_SPEC)")
    ap.add_argument("--out", required=True, help="trial record JSONL (appended; used for resume)")
    ap.add_argument("--lambdas", nargs="+", type=float, default=[0.0, 0.05, 0.12],
                    help="noise intensities. Confirmatory values come from O1; these defaults are the pilot's.")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0])
    ap.add_argument("--revision", default=PINNED_REVISION)
    ap.add_argument("--device", default=None, help="'cuda', 'cpu', or omit for automatic")
    ap.add_argument("--limit", type=int, default=0, help="first N items only (0 = all)")
    args = ap.parse_args()

    bank_path = pathlib.Path(args.bank)
    out_path = pathlib.Path(args.out)
    bank = load_bank(bank_path)
    if args.limit:
        bank = bank[: args.limit]
    done = done_keys(out_path)

    planned = len(bank) * len(args.lambdas) * len(args.seeds) * len(QUESTIONS)
    print("=" * 78)
    print("Phase I predict -> JSONL")
    print("=" * 78)
    print(f"bank        : {bank_path}  ({len(bank)} items)")
    print(f"out         : {out_path}  ({len(done)} rows already recorded)")
    print(f"lambdas     : {args.lambdas}")
    print(f"seeds       : {args.seeds}")
    print(f"revision    : {args.revision}")
    print(f"planned rows: {planned}")
    print()

    import torch
    import laya
    from laya import Router

    print(f"laya {laya.__version__} | torch {torch.__version__} | cuda {torch.cuda.is_available()}")
    router = Router(device=args.device, revision=args.revision)
    agent = router.load("english")
    print(f"checkpoint  : repo={agent.model_id!r} subfolder={agent.subfolder!r}")
    print(f"resolved rev: {getattr(agent, 'revision', None)}")
    print(f"device      : {agent.device}")
    print()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    n_written = n_skipped = n_failed = 0
    t0 = time.time()

    with out_path.open("a", encoding="utf-8", newline="\n") as fh:
        for item in bank:
            item_id = item["item_id"]
            q0 = q0_of(item)
            gold = item.get("intent_gold")

            for lam in args.lambdas:
                for seed in args.seeds:
                    pending = [q for q in QUESTIONS
                               if q in q0 and (item_id, lam, seed, q) not in done]
                    if not pending:
                        n_skipped += 1
                        continue

                    # --- noise: pure function of (item_id, lam, seed) -----------------
                    try:
                        noisy, ops = typo_noise(item["state"], item_id, lam, seed)
                    except Exception as e:                       # generator failure
                        for qid in pending:
                            fh.write(json.dumps({
                                "phase": "I", "item_id": item_id, "lambda": lam,
                                "noise_seed": seed, "question_id": qid,
                                "status": "failure", "stage": "noise",
                                "error": f"{type(e).__name__}: {e}",
                            }, ensure_ascii=False) + "\n")
                            n_failed += 1
                        fh.flush()
                        continue

                    state_hash = hashlib.sha256(noisy.encode("utf-8")).hexdigest()
                    rr = realised_edit_rate(item["state"], ops)

                    # --- one model call, reused for every question --------------------
                    try:
                        result = router.predict(noisy, q0)
                        answers = result.get("answers", {})
                    except Exception as e:                       # model failure
                        for qid in pending:
                            fh.write(json.dumps({
                                "phase": "I", "item_id": item_id, "lambda": lam,
                                "noise_seed": seed, "question_id": qid,
                                "state_hash": state_hash, "status": "failure",
                                "stage": "predict", "error": f"{type(e).__name__}: {e}",
                            }, ensure_ascii=False) + "\n")
                            n_failed += 1
                        fh.flush()
                        continue

                    for qid in pending:
                        ans = answers.get(qid)
                        if ans is None:
                            fh.write(json.dumps({
                                "phase": "I", "item_id": item_id, "lambda": lam,
                                "noise_seed": seed, "question_id": qid,
                                "state_hash": state_hash, "status": "failure",
                                "stage": "answer_missing", "error": "question absent from result",
                            }, ensure_ascii=False) + "\n")
                            n_failed += 1
                            continue

                        mode = q0[qid]["type"]
                        if mode == "choice":
                            p_map = dict(ans["probabilities"])
                            probs = list(p_map.values())
                            argmax = ans["choice"]
                        else:
                            p_true = float(ans["noul"])
                            p_map = {"true": p_true, "false": 1.0 - p_true}
                            probs = [1.0 - p_true, p_true]
                            argmax = None            # noul has no argmax over the bank's options

                        c = frozen_confidence(mode, probs)

                        # error is only defined where gold exists
                        if qid == "intent" and gold is not None:
                            err = 0 if argmax == gold else 1
                        else:
                            err = None

                        row = {
                            "phase": "I",
                            "item_id": item_id,
                            "script": "en_latin",
                            "lambda": lam,
                            "typo_ops": ops,
                            "realised_edit_rate": rr,
                            "noise_seed": seed,
                            "state_hash": state_hash,
                            "model_id": f"{getattr(agent, 'model_id', 'convaiinnovations/laya')}@{args.revision[:12]}",
                            "question_id": qid,
                            "question_type": mode,
                            "p": p_map,
                            "c": c,
                            "argmax": argmax,
                            "gold": gold if qid == "intent" else None,
                            "error": err,
                            "silent_error": {str(t): (1 if (err == 1 and c >= t) else 0) if err is not None else None
                                             for t in TAUS},
                            "action": {str(t): ("answer" if c >= t else "defer") for t in TAUS},
                            "status": "ok",
                        }
                        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                        n_written += 1
                    fh.flush()

                    if n_written and n_written % 25 == 0:
                        el = time.time() - t0
                        print(f"  {n_written:6d} rows written  ({el:.0f}s, {n_written/el:.1f} rows/s)")

    print()
    print(f"  rows written : {n_written}")
    print(f"  conditions skipped (already present): {n_skipped}")
    print(f"  failures recorded: {n_failed}")
    print(f"  elapsed      : {time.time() - t0:.1f}s")
    print(f"  record       : {out_path}  ({out_path.stat().st_size} B)" if out_path.is_file() else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
