"""Power the family comparison at the dev ceiling: n = 280, not 150.

Also: the previous plant carried only a DIRECTION, so its null could not be
interpreted. This one carries a CALIBRATED effect size -- damage content words at
rate 0.30 vs 0.15 -- so the expected gap is computable and recovery can be
demanded to a stated accuracy, which is what the planted-truth skill requires.

Two runs in one script:
  A. the family comparison at n = 280 (geometry vs structure, matched damage)
  B. the calibrated plant at n = 280 (content 0.30 vs content 0.15)
"""
from __future__ import annotations
import argparse, ast, hashlib, json, pathlib, random, sys, time
from collections import defaultdict

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "measurement"))
from prop_a_injection import TAUS, tokens_of, damaged_tokens  # noqa: E402
from prop_a_planted_control import token_indices, calibrate_targeted  # noqa: E402
from prop_a_injection import inject_geometry, inject_structure, calibrate  # noqa: E402

PINNED = "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"

def run(router, bank, n_items, mode, rate_lo, rate_hi, seed, out_path):
    rng = random.Random(seed)
    items = rng.sample(bank, min(n_items, len(bank)))
    ARMS = (["clean", "geometry", "structure"] if mode == "family"
            else ["clean", "content_lo", "content_hi"])
    rows = []
    t0 = time.time()
    with out_path.open("w", encoding="utf-8", newline="\n") as fh:
        for k, item in enumerate(items, 1):
            state = item["state"]
            spec = item["intent"]
            if isinstance(spec, str):
                try: spec = json.loads(spec)
                except json.JSONDecodeError: spec = ast.literal_eval(spec)
            q0 = {"intent": spec}
            gold = item.get("intent_gold")
            n_tok = len(tokens_of(state))
            content_idx = set(token_indices(state, want_function=False))
            for arm in ARMS:
                try:
                    if arm == "clean":
                        noisy, dmg = state, 0
                    elif mode == "family":
                        tgt = max(1, round(rate_hi * n_tok))
                        noisy, dmg = calibrate(
                            state, arm, tgt,
                            random.Random(f"{item['item_id']}|{arm}|{seed}"))
                    else:
                        rate = rate_lo if arm.endswith("_lo") else rate_hi
                        tgt = max(1, round(rate * n_tok))
                        noisy, dmg = calibrate_targeted(
                            state, tgt, content_idx,
                            random.Random(f"{item['item_id']}|{arm}|{seed}"))
                    res = router.predict(noisy, q0)
                    a = (res.get("answers") or {}).get("intent") or {}
                    chosen = a.get("choice"); probs = a.get("probabilities") or {}
                except Exception as e:
                    fh.write(json.dumps({"item_id": item["item_id"], "arm": arm,
                                         "status": "failure", "error": f"{type(e).__name__}: {e}"}) + "\n")
                    continue
                correct = (chosen == gold)
                c = max(probs.values()) if probs else None
                row = {"item_id": item["item_id"], "arm": arm, "tokens": n_tok,
                       "tokens_damaged": dmg, "damage_rate": dmg / max(n_tok, 1),
                       "correct": bool(correct), "c": c,
                       "silent_error": {str(t): (1 if (not correct and c is not None and c >= t) else 0) for t in TAUS},
                       "action": {str(t): ("answer" if (c is not None and c >= t) else "defer") for t in TAUS},
                       "state_hash": hashlib.sha256(noisy.encode()).hexdigest()[:16]}
                rows.append(row)
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            if k % 40 == 0:
                print(f"    {k}/{len(items)}  {time.time()-t0:.0f}s", flush=True)
    return rows

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-items", type=int, default=280)
    ap.add_argument("--mode", choices=["family","plant"], default="family")
    ap.add_argument("--rate-lo", type=float, default=0.15)
    ap.add_argument("--rate-hi", type=float, default=0.30)
    ap.add_argument("--device", default=None)
    ap.add_argument("--revision", default=PINNED)
    ap.add_argument("--seed", type=int, default=20261013)
    args = ap.parse_args()

    bank = [json.loads(l) for l in (REPO/"measurement"/"item_bank.jsonl")
            .read_text(encoding="utf-8").splitlines() if l.strip()]
    dev = [b for b in bank if b.get("split") == "dev"]
    print(f"dev items available: {len(dev)}  (requested {args.n_items})")
    if args.n_items > len(dev):
        print(f"  REFUSING: {args.n_items} exceeds the dev split's {len(dev)}. The other "
              f"{len(bank)-len(dev)} are the confirmatory window and must not be used.")
        return 2
    import torch, laya
    from laya import Router
    print(f"laya {laya.__version__} | cuda {torch.cuda.is_available()}")
    router = Router(device=args.device, revision=args.revision)
    agent = router.load("english")
    print(f"device : {agent.device}  mode : {args.mode}\n")
    out = REPO/"measurement"/"out"/f"prop_a_powered_{args.mode}.jsonl"
    rows = run(router, dev, args.n_items, args.mode, args.rate_lo, args.rate_hi, args.seed, out)
    ok = [r for r in rows if "correct" in r]
    by = defaultdict(dict)
    for r in ok: by[r["item_id"]][r["arm"]] = r
    items = [k for k,v in by.items() if len(v) == 3]
    print(f"\nrows {len(ok)} | paired items {len(items)}")
    for arm in sorted({r['arm'] for r in ok}):
        sub = [r for r in ok if r["arm"] == arm]
        acc = sum(r["correct"] for r in sub)/len(sub)
        cov = sum(1 for r in sub if r["action"]["0.8"]=="answer")/len(sub)
        dmg = sum(r["damage_rate"] for r in sub)/len(sub)
        print(f"  {arm:12} n={len(sub):4} acc={acc:.4f} cov@0.8={cov:.4f} damage={dmg:.4f}")
    print(f"wrote {out}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
