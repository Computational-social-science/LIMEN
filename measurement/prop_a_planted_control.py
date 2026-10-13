"""PLANTED-TRUTH CONTROL for the Proposition A injection harness.

WHY THIS EXISTS -- the gap it closes
The harness reported "geometry-indexed and structure-indexed noise are not
separable in loss". That is a NULL result from an instrument that has never been
shown able to detect a difference. Per the BootLoops `planted-truth` skill: "a
checker that has never fired is untested", and a null from such an instrument is
not evidence of absence. My own summary said as much in its limits section and
then still drew the conclusion.

THE PLANT
Same harness, same items, same matched damaged-token rate, same endpoints. The
only change is WHERE the damage falls:

  geometry_content   damage only CONTENT words (the words that carry the intent)
  geometry_function  damage only FUNCTION words (stopwords: the, a, in, was...)

Both arms are geometry-family edits, so the edit MECHANISM is identical and the
family is not the variable. Only the linguistic locus differs. For an intent
classifier the content words are the signal, so content damage MUST cost more.

A KNOWN answer, written down before the run:
  prediction -- accuracy(content) < accuracy(function), and coverage(content) <
                coverage(function), at matched damage rate.

If the harness detects this, it can detect a difference at matched damage, and the
geometry-vs-structure null becomes meaningful. If it does NOT detect it, the
harness is underpowered for this design and the earlier null must be withdrawn
rather than reported.
"""
from __future__ import annotations

import argparse, ast, hashlib, json, pathlib, random, sys, time

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "measurement"))

from prop_a_injection import (TAUS, tokens_of, damaged_tokens, QWERTY_ROWS, ADJ)  # noqa: E402

PINNED_REVISION = "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"

# A closed-class stopword list. Function words are the complement within a token.
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "than", "so", "because",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "into", "about",
    "is", "am", "are", "was", "were", "be", "been", "being", "do", "does", "did",
    "have", "has", "had", "will", "would", "can", "could", "should", "may",
    "might", "must", "i", "you", "he", "she", "it", "we", "they", "me", "him",
    "her", "us", "them", "my", "your", "his", "its", "our", "their", "this",
    "that", "these", "those", "there", "here", "not", "no", "as", "up", "out",
    "please", "still", "again", "just", "very", "too", "also", "when", "where",
    "why", "how", "what", "which", "who", "whom", "any", "some", "all", "each",
}

def is_function_word(w: str) -> bool:
    return w.lower().strip(".,!?;:'\"") in STOPWORDS

def token_indices(text: str, want_function: bool) -> list[int]:
    out = []
    for i, w in enumerate(tokens_of(text)):
        if is_function_word(w) == want_function:
            out.append(i)
    return out

def inject_geometry_targeted(text: str, n_edits: int, rng: random.Random,
                             allowed: set[int]) -> str:
    """Geometry-family edits (adjacent-key / transposition) restricted to tokens."""
    toks = tokens_of(text)
    # character ranges of the allowed tokens
    spans, off = [], 0
    for i, w in enumerate(toks):
        s = text.find(w, off); off = s + len(w)
        if i in allowed:
            spans.append((s, s + len(w)))
    if not spans:
        return text
    chars = list(text)
    positions = [i for (a, b) in spans for i in range(a, b) if chars[i].isalpha()]
    rng.shuffle(positions)
    applied = 0
    for i in positions:
        if applied >= n_edits: break
        c = chars[i]
        if rng.random() < 0.6:
            nbrs = sorted(ADJ.get(c.lower(), ()))
            if not nbrs: continue
            rep = rng.choice(nbrs)
            chars[i] = rep.upper() if c.isupper() else rep
        else:
            j = i + 1
            if j >= len(chars) or not chars[j].isalpha() or chars[j] == c: continue
            chars[i], chars[j] = chars[j], chars[i]
        applied += 1
    return "".join(chars)

def calibrate_targeted(text: str, n_edits_target: int, allowed: set[int],
                       rng: random.Random):
    """Monotone scan to the first edit count reaching the target damage."""
    best, best_d, best_err = None, None, None
    for n in range(0, max(8, n_edits_target * 8)):
        noisy = inject_geometry_targeted(text, n, rng, allowed)
        d = damaged_tokens(text, noisy)
        err = abs(d - n_edits_target)
        if best_err is None or err < best_err:
            best, best_d, best_err = noisy, d, err
        if d >= n_edits_target:
            break
    return best, best_d

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-items", type=int, default=150)
    ap.add_argument("--rate", type=float, default=0.30)
    ap.add_argument("--device", default=None)
    ap.add_argument("--revision", default=PINNED_REVISION)
    ap.add_argument("--seed", type=int, default=20261013)
    ap.add_argument("--out", default=str(REPO / "measurement" / "out" / "prop_a_planted.jsonl"))
    args = ap.parse_args()

    bank = [json.loads(l) for l in (REPO / "measurement" / "item_bank.jsonl")
            .read_text(encoding="utf-8").splitlines() if l.strip()]
    bank = [b for b in bank if b.get("split") == "dev"] or bank
    rng = random.Random(args.seed)
    items = rng.sample(bank, min(args.n_items, len(bank)))
    print(f"items: {len(items)} (dev split)")
    print("PLANT: content-word damage vs function-word damage, same mechanism,")
    print("       matched damaged-token rate. Prediction written before the run:")
    print("       accuracy(content) < accuracy(function).\n")

    import torch, laya
    from laya import Router
    print(f"laya {laya.__version__} | torch {torch.__version__} | cuda {torch.cuda.is_available()}")
    router = Router(device=args.device, revision=args.revision)
    agent = router.load("english")
    print(f"device : {agent.device}\n")

    out_path = pathlib.Path(args.out); out_path.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time(); rows = []
    ARMS = ["clean", "content", "function"]
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
            target = max(1, round(args.rate * n_tok))

            content_idx = set(token_indices(state, want_function=False))
            func_idx = set(token_indices(state, want_function=True))

            for arm in ARMS:
                if arm == "clean":
                    noisy, dmg = state, 0
                elif arm == "content":
                    noisy, dmg = calibrate_targeted(
                        state, target, content_idx, random.Random(f"{item['item_id']}|c|{args.seed}"))
                else:
                    noisy, dmg = calibrate_targeted(
                        state, target, func_idx, random.Random(f"{item['item_id']}|f|{args.seed}"))
                try:
                    res = router.predict(noisy, q0)
                    ans_obj = (res.get("answers") or {}).get("intent") or {}
                    chosen = ans_obj.get("choice")
                    probs = ans_obj.get("probabilities") or {}
                except Exception as e:
                    fh.write(json.dumps({"item_id": item["item_id"], "arm": arm,
                                         "status": "failure", "error": f"{type(e).__name__}: {e}"},
                                        ensure_ascii=False) + "\n")
                    continue
                correct = (chosen == gold)
                c = max(probs.values()) if probs else None
                silent = {str(t): (1 if (not correct and c is not None and c >= t) else 0) for t in TAUS}
                action = {str(t): ("answer" if (c is not None and c >= t) else "defer") for t in TAUS}
                row = {"item_id": item["item_id"], "arm": arm, "rate_target": args.rate,
                       "tokens": n_tok, "tokens_damaged": dmg,
                       "damage_rate": dmg / max(n_tok, 1),
                       "n_content_tokens": len(content_idx), "n_function_tokens": len(func_idx),
                       "chosen": chosen, "gold": gold, "correct": bool(correct),
                       "c": c, "silent_error": silent, "action": action,
                       "state_hash": hashlib.sha256(noisy.encode()).hexdigest()[:16]}
                rows.append(row)
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            if k % 30 == 0:
                print(f"  {k}/{len(items)}  {time.time()-t0:.0f}s", flush=True)

    ok = [r for r in rows if "correct" in r]
    print(f"\nrows: {len(ok)} usable of {len(rows)}")
    for arm in ARMS:
        sub = [r for r in ok if r["arm"] == arm]
        if not sub: continue
        acc = sum(r["correct"] for r in sub)/len(sub)
        dmg = sum(r["damage_rate"] for r in sub)/len(sub)
        cov = sum(1 for r in sub if r["action"]["0.8"] == "answer")/len(sub)
        print(f"  {arm:10} n={len(sub):4}  acc={acc:.4f}  cov@0.8={cov:.4f}  damage={dmg:.4f}")
    print(f"\nwrote {out_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
