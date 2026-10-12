"""Proposition A, model side: are the two error processes separable in LOSS?

WHY THIS EXPERIMENT
The corpus measurement (docs/PARADIGM_TYPING_AS_REGULATED_PROCESS.md) shows human
residual error is two processes with different governing variables:
  * GEOMETRY-indexed  -- adjacent-key substitution. Rate is FLAT across word
    length (0.98x from length 2 to 12).
  * STRUCTURE-indexed -- deletion and insertion. Rate SCALES with word length
    (2.5x and 4.9x).
The programme's generator N_en implements the geometry process and gives it 60% of
the weight; the structure process, 61.3% of measured residual error, has none.

The Shannon note's Proposition A asks whether physical and cognitive noise are
separable. This measures the MODEL half: inject each family at a MATCHED
token-damage rate and compare loss. If loss tracks damage rate regardless of
family, the two-process structure in human data does not propagate to model loss
and N_en's mis-weighting is harmless. If the structure family costs more at
matched damage, the generator's weights are a first-order error.

DESIGN -- everything is reused from the existing harness, nothing is rebuilt:
  * the pinned instrument: convaiinnovations/laya @ 55cf4c4e, via `Router`, the
    same construction measurement/run_phase1.py uses
  * the item bank: measurement/item_bank.jsonl (932 items)
  * the geometry family: measurement/typo_noise.py's own "adj" and "trans" classes
  * the structure family: this script's deletion/insertion, which MOVE TOKEN
    BOUNDARIES (a deleted space merges two words; an inserted space splits one),
    because that is the mechanism the corpus measurement implicates

MATCHED DAMAGE is enforced on the quantity that matters -- the number of
whitespace-delimited TOKENS whose surface form differs from the clean text --
not on the edit count. That is the control the note asks for: "performance
differences at matched damage rate are then attributable to edit structure".

Usage:
  python measurement/prop_a_injection.py --n-items 120 --rate 0.08
"""
from __future__ import annotations

import argparse, hashlib, json, pathlib, random, sys, time
from collections import Counter

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "measurement"))

REVIEWED_SHA = "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851"
QUESTIONS = ["intent"]
QWERTY_ROWS = ("qwertyuiop", "asdfghjkl", "zxcvbnm")
ADJ = {}
for row in QWERTY_ROWS:
    for i, ch in enumerate(row):
        ADJ.setdefault(ch, set())
        if i: ADJ[ch].add(row[i - 1])
        if i + 1 < len(row): ADJ[ch].add(row[i + 1])


def tokens_of(text: str) -> list[str]:
    return text.split()


def damaged_tokens(clean: str, noisy: str) -> int:
    """How many clean tokens are no longer intact in the noisy text.

    Positional comparison is WRONG here and a first version used it: inserting one
    space splits a token, which shifts every later token by one, and the count then
    reports ~all of them (measured: 1 edit -> 1 damaged, 2 edits -> 14 damaged on a
    14-token sentence). That is an alignment artefact, not damage, and it made the
    matched-damage control meaningless.

    The right question is per clean token: does that token still appear, unbroken,
    in the noisy text? A token survives if it occurs as a substring bounded by
    non-letters on both sides. Damage is then 1 minus the surviving fraction,
    scaled to a token count. This is stable under insertions and deletions, which
    is exactly what the structure family does.
    """
    a = tokens_of(clean)
    if not a:
        return 0
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    low = noisy.lower()
    intact = 0
    for w in a:
        wl = w.lower()
        start = 0
        found = False
        while True:
            i = low.find(wl, start)
            if i < 0:
                break
            before = low[i - 1] if i > 0 else " "
            after = low[i + len(wl)] if i + len(wl) < len(low) else " "
            if before not in letters and after not in letters:
                found = True
                break
            start = i + 1
        if found:
            intact += 1
    return len(a) - intact


def inject_geometry(text: str, n_edits: int, rng: random.Random) -> str:
    """Adjacent-key substitution and transposition only (N_en's own classes)."""
    chars = list(text)
    letters = [i for i, c in enumerate(chars) if c.isalpha()]
    rng.shuffle(letters)
    applied = 0
    for i in letters:
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


def inject_structure(text: str, n_edits: int, rng: random.Random) -> str:
    """Deletion and insertion, INCLUDING at whitespace, so boundaries can move."""
    chars = list(text)
    applied = 0
    guard = 0
    while applied < n_edits and guard < n_edits * 40:
        guard += 1
        if not chars: break
        i = rng.randrange(len(chars))
        if rng.random() < 0.5:
            if len(chars) <= 1: continue
            del chars[i]
        else:
            ins = " " if rng.random() < 0.25 else rng.choice("abcdefghijklmnopqrstuvwxyz")
            chars.insert(i, ins)
        applied += 1
    return "".join(chars)


def calibrate(text: str, family: str, target_tokens: int, rng: random.Random) -> tuple[str, int]:
    """Find the edit count that damages `target_tokens` tokens, then return it.

    Binary search on edit count, because the mapping from edits to damaged tokens
    differs by family -- that difference is exactly what must be controlled away.
    """
    # The damage curve is monotone but NOT linear (structure: 3 edits -> 3 tokens,
    # 4 edits -> 9, because one deletion can merge two tokens and change both
    # surfaces). A binary search over edit counts is therefore unreliable -- a first
    # version returned damage 1 when the target was 4. Instead, scan edit counts
    # upward and stop at the FIRST count whose damage reaches the target, keeping
    # the closest hit seen. This is O(target) injector calls, which is cheap next to
    # a model forward pass, and it guarantees the matched-damage control is real.
    best, best_d, best_err = None, None, None
    for n in range(0, max(8, target_tokens * 8)):
        noisy = inject_geometry(text, n, rng) if family == "geometry" else inject_structure(text, n, rng)
        d = damaged_tokens(text, noisy)
        err = abs(d - target_tokens)
        if best_err is None or err < best_err:
            best, best_d, best_err = noisy, d, err
        if d >= target_tokens:
            break
    return best, best_d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-items", type=int, default=120)
    ap.add_argument("--rate", type=float, default=0.08,
                    help="target damaged-token RATE (fraction of tokens)")
    ap.add_argument("--device", default=None)
    ap.add_argument("--revision", default=REVIEWED_SHA)
    ap.add_argument("--out", default=str(REPO / "measurement" / "out" / "prop_a_injection.jsonl"))
    ap.add_argument("--seed", type=int, default=20261012)
    args = ap.parse_args()

    bank = [json.loads(l) for l in (REPO / "measurement" / "item_bank.jsonl")
            .read_text(encoding="utf-8").splitlines() if l.strip()]
    # dev items only: the confirmatory split is not to be touched
    bank = [b for b in bank if b.get("split") == "dev"] or bank
    rng = random.Random(args.seed)
    items = rng.sample(bank, min(args.n_items, len(bank)))
    print(f"items: {len(items)} (from the bank's dev split)")

    import torch, laya
    from laya import Router
    print(f"laya {laya.__version__} | torch {torch.__version__} | cuda {torch.cuda.is_available()}")
    router = Router(device=args.device, revision=args.revision)
    agent = router.load("english")
    print(f"checkpoint : {agent.model_id!r} rev={getattr(agent,'revision',None)}")
    print(f"device     : {agent.device}\n")

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rows = []
    with out_path.open("w", encoding="utf-8", newline="\n") as fh:
        for k, item in enumerate(items, 1):
            state = item["state"]
            q0 = {"intent": json.loads(item["intent"].replace("'", '"'))} \
                 if isinstance(item["intent"], str) else {"intent": item["intent"]}
            gold = item.get("intent_gold")
            n_tok = len(tokens_of(state))
            target = max(1, round(args.rate * n_tok))

            for arm in ["clean", "geometry", "structure"]:
                if arm == "clean":
                    noisy, dmg = state, 0
                else:
                    noisy, dmg = calibrate(state, arm, target, random.Random(f"{item['item_id']}|{arm}|{args.seed}"))
                try:
                    res = router.predict(noisy, q0)
                    ans = (res.get("answers") or {}).get("intent")
                    probs = (res.get("probabilities") or {}).get("intent") or {}
                except Exception as e:
                    fh.write(json.dumps({"item_id": item["item_id"], "arm": arm,
                                         "status": "failure", "error": f"{type(e).__name__}: {e}"},
                                        ensure_ascii=False) + "\n")
                    continue
                chosen = ans if isinstance(ans, str) else (ans or {}).get("choice") if isinstance(ans, dict) else None
                correct = (chosen == gold)
                p_correct = float(probs.get(gold, 0.0)) if probs else None
                row = {"item_id": item["item_id"], "domain": item.get("domain"),
                       "arm": arm, "rate_target": args.rate,
                       "tokens": n_tok, "tokens_damaged": dmg,
                       "damage_rate": dmg / max(n_tok, 1),
                       "chosen": chosen, "gold": gold, "correct": bool(correct),
                       "p_gold": p_correct, "state_hash": hashlib.sha256(noisy.encode()).hexdigest()[:16]}
                rows.append(row)
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            if k % 20 == 0:
                print(f"  {k}/{len(items)}  {time.time()-t0:.0f}s", flush=True)

    # ---- summary ----
    ok = [r for r in rows if "correct" in r]
    print(f"\nrows: {len(ok)} usable of {len(rows)}")
    by = {}
    for arm in ["clean", "geometry", "structure"]:
        sub = [r for r in ok if r["arm"] == arm]
        if not sub: continue
        acc = sum(r["correct"] for r in sub) / len(sub)
        dmg = sum(r["damage_rate"] for r in sub) / len(sub)
        by[arm] = {"n": len(sub), "accuracy": acc, "mean_damage_rate": dmg}
        print(f"  {arm:10} n={len(sub):4}  acc={acc:.4f}  mean damaged-token rate={dmg:.4f}")
    if "geometry" in by and "structure" in by:
        print(f"\n  MATCHED DAMAGE: geometry {by['geometry']['mean_damage_rate']:.4f} vs "
              f"structure {by['structure']['mean_damage_rate']:.4f}")
        dg = by["clean"]["accuracy"] - by["geometry"]["accuracy"]
        ds = by["clean"]["accuracy"] - by["structure"]["accuracy"]
        print(f"  loss vs clean : geometry {dg:+.4f}   structure {ds:+.4f}")
        print(f"  structure - geometry = {ds-dg:+.4f}")
        print("  -> if this is ~0, loss tracks damage and the two processes are NOT separable in loss;")
        print("     if clearly >0, the structure family costs more at matched damage.")
    print(f"\nwrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
