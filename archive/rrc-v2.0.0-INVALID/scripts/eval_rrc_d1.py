"""Run d1-3B natively over RRC and measure the two falsifiers that need model output.

What this measures
------------------
The technical report defines three falsifiers (scripts/falsifiers.py). Two need a model:

  F1  on the ranked layers (margin defined), does the model's confidence separate its correct
      from its incorrect answers beyond what the margin already predicts?
  F2  on the reading channel (margin identically zero, section 2.4 of the report), does accuracy
      at frequency rank 1 differ from accuracy at rank n? If it does not, the channel's own
      ordering carries no difficulty and the layer is uninformative rather than hard.

This script produces the per-item records those two tests read. It does not compute the tests'
verdicts; it writes the rows and a summary, so the analysis can be re-run without re-running the
model.

The instrument
--------------
`LiquidAI/d1-3B` loaded natively (not the GGUF, not through a server), because the decision
readout is a property of the checkpoint: the model exposes no `option_codes` attribute, so the
interface comes from the two modules shipped inside the checkpoint directory itself -- its prompt
module (the `Choice` question form) and its runner module (the `SystemOne` readout).
They are imported as a package from the resolved checkpoint path (see `resolve_model`), not from
this repository, and they use relative imports, which is why they cannot be imported by path
alone. The state is the observed corrupted form and the candidates are the question's criteria,
which is the placement those two modules expect.

Note on the readout and tokenization: the probabilities come from the option CODE tokens (A, B,
C ...), not from the candidate strings. A multi-token candidate therefore cannot corrupt the
readout -- which matters here, because a single Han character may or may not be one token and the
comparison across scripts would otherwise be confounded by tokenization rather than by script.

No absolute paths: the model directory comes from `--model`, else `FDLH_D1_MODEL`, else
`$HERMES_HOME/models/d1-3b-native`, else `~/.cache/fdlh/d1-3b-native`; an unresolvable path is a
loud failure rather than a silent fallback.
"""
import argparse
import collections
import json
import math
import os
import pathlib
import random
import statistics
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[1]
RRC_DIR = REPO / "data" / "rrc"
MANIFEST = REPO / "config" / "rrc.json"
OUT = REPO / "measurement" / "out"
SEED = 20261010

# The layers whose candidates are RANKED against the state, and which therefore carry a margin.
# This mirrors the tuple inside build_rrc's build_arm; a guard (check_ranked_layers_agree.py
# equivalent, in run_all_guards) compares the two, because one quantity implemented in two places
# that can drift is two instruments (rule 19) -- and a mismatch here would silently move items
# between the margin-sampled and flat-sampled paths.
RANKED_LAYERS = ("L2", "L3del", "L3")


def resolve_model(explicit: str | None) -> pathlib.Path:
    """The checkpoint directory, or a loud failure."""
    cands = []
    if explicit:
        cands.append(pathlib.Path(explicit))
    if os.environ.get("FDLH_D1_MODEL"):
        cands.append(pathlib.Path(os.environ["FDLH_D1_MODEL"]))
    if os.environ.get("HERMES_HOME"):
        cands.append(pathlib.Path(os.environ["HERMES_HOME"]) / "models" / "d1-3b-native")
    cands.append(pathlib.Path.home() / ".cache" / "fdlh" / "d1-3b-native")
    for c in cands:
        if (c / "config.json").exists() and (c / "model.safetensors").exists():
            return c
    raise SystemExit(
        "  [FAIL] no d1-3B checkpoint found. Looked in:\n    "
        + "\n    ".join(str(c) for c in cands)
        + "\n  Pass --model, or set FDLH_D1_MODEL. Refusing to substitute a different model: "
          "the measurement is of this instrument."
    )


def wilson(k: int, n: int, z: float = 1.96) -> tuple:
    """Wilson score interval for a binomial proportion.

    Used instead of the normal approximation because the interesting cells here are small and
    near zero -- the reading channel's rank-1 accuracy was 3 % of 31 items -- where the normal
    interval runs below 0 and reports a negative lower bound for a proportion.
    """
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def sample_items(arms: list[str], per_layer: int, rng: random.Random,
                 per_rank: int = 0, by_state: int = 0, per_margin: int = 0) -> list[dict]:
    """Items sampled per arm and layer, so a small arm is not swamped by a large one.

    `per_rank` and `per_margin` are the same idea applied to each channel's own difficulty
    quantity, and they exist for the same reason: neither quantity is uniformly distributed, so a
    flat sample is dense where the corpus happens to be dense and thin at the ends — which is
    exactly where the interesting behaviour is. On the reading channel, rank 1 is ~20 % of the layer
    and the tail single digits. On the ranked layers the margin is likewise concentrated, so a flat
    quartile split of the SAMPLE is not a balanced split of the QUANTITY.

    Applying the balanced scheme to one channel and not the other would make the two curves
    incomparable — one measured at a quota per difficulty level, the other following the corpus —
    and §5.11's cross-channel claim rests on comparing them. Both are therefore available, and the
    figure and the report name which scheme produced each curve.
    """
    out = []
    for arm in arms:
        p = RRC_DIR / f"{arm}.jsonl"
        if not p.exists():
            print("  [WARN] arm file absent, skipped: %s" % p.name)
            continue
        rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

        if by_state:
            groups: dict = collections.defaultdict(list)
            for it in rows:
                groups[(it["state"], it["root"])].append(it)
            # only states that carry more than one layer can support a comparison; keep those,
            # and prefer the ones with the most layers so a state contributes its full stack
            multi = {k: v for k, v in groups.items() if len({x["layer"] for x in v}) > 1}
            keys = sorted(multi)[:]
            rng.shuffle(keys)
            take = min(by_state, len(keys))
            # counted over THIS arm's items, not over the running total: an earlier version
            # printed the accumulated list, so every arm appeared to hold every earlier arm's
            # layers and rrc-ru showed 1,949 items from a 302-item file.
            added = []
            for k in keys[:take]:
                added += multi[k]
            out += added
            layers = collections.Counter(x["layer"] for x in added)
            print("  %-13s %6d states, %4d multi-layer, %4d sampled -> %4d items  layers=%s"
                  % (arm, len(groups), len(multi), take, len(added), dict(sorted(layers.items()))))
            continue

        buckets: dict = collections.defaultdict(list)
        for it in rows:
            buckets[it["layer"]].append(it)
        for layer, lrows in sorted(buckets.items()):
            if layer == "L2c" and per_rank:
                by_rank: dict = collections.defaultdict(list)
                norank = []
                for it in lrows:
                    r = (it.get("difficulty") or {}).get("group_rank")
                    (by_rank[r] if r else norank).append(it)
                picked = []
                for r in sorted(k for k in by_rank if isinstance(k, int)):
                    take = min(per_rank, len(by_rank[r]))
                    picked += rng.sample(by_rank[r], take)
                if norank:
                    picked += rng.sample(norank, min(per_rank, len(norank)))
                out += picked
                dist = {r: sum(1 for x in picked
                               if (x.get("difficulty") or {}).get("group_rank") == r)
                        for r in sorted(set(list(by_rank) + [None]),
                                        key=lambda k: (k is None, k if k is not None else 0))}
                print("  %-13s %-7s %6d available, %4d sampled  rank-dist=%s"
                      % (arm, layer, len(lrows), len(picked),
                         {k: v for k, v in dist.items() if v}))
            elif per_margin and layer in RANKED_LAYERS:
                # equal-population deciles of the margin, then a quota from each, so the curve is
                # measured at the same density across the whole range instead of where the corpus
                # happens to sit. Deciles rather than fixed margin widths because the margin's
                # usable range is channel-dependent.
                with_m = [it for it in lrows if (it.get("difficulty") or {}).get("margin") is not None]
                if len(with_m) < 40:
                    take = min(per_layer, len(lrows))
                    out += rng.sample(lrows, take)
                    print("  %-13s %-7s %6d available, %4d sampled (flat: <40 with a margin)"
                          % (arm, layer, len(lrows), take))
                    continue
                with_m.sort(key=lambda it: it["difficulty"]["margin"])
                n = len(with_m)
                step = max(1, n // 10)
                picked = []
                for i in range(0, n, step):
                    chunk = with_m[i:i + step]
                    if chunk:
                        picked += rng.sample(chunk, min(per_margin, len(chunk)))
                out += picked
                ms = sorted(it["difficulty"]["margin"] for it in picked)
                print("  %-13s %-7s %6d available, %4d sampled  margin-dist=%d deciles "
                      "[%.3f .. %.3f]"
                      % (arm, layer, len(lrows), len(picked), len(range(0, n, step)),
                         ms[0] if ms else 0, ms[-1] if ms else 0))
            else:
                take = min(per_layer, len(lrows))
                out += rng.sample(lrows, take)
                print("  %-13s %-7s %6d available, %4d sampled"
                      % (arm, layer, len(lrows), take))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--model", default=None)
    ap.add_argument("--per-layer", type=int, default=200)
    ap.add_argument("--arms", default="")
    ap.add_argument("--batch-log", type=int, default=50)
    ap.add_argument("--per-rank", type=int, default=0,
                    help=("quota per group_rank value on the reading channel (L2c); 0 = use "
                          "--per-layer flat sampling. Use this to make the ends of the rank "
                          "distribution measurable in their own right."))
    ap.add_argument("--out-tag", default="",
                    help=("suffix for the output filenames, so a second sampling scheme does not "
                          "overwrite the first run's rows. Empty keeps the original names."))
    ap.add_argument("--by-state", type=int, default=0,
                    help=("sample STATES, taking every layer built from each, so layered items "
                          "are paired by construction; the unit for comparing layers. 0 = sample "
                          "items independently per layer (the unit for comparing arms)."))
    ap.add_argument("--per-margin", type=int, default=0,
                    help=("quota per margin decile on the ranked layers (L2/L3del/L3), the "
                          "analogue of --per-rank for the ranked channel. Use both so the two "
                          "channels' curves are measured under the same scheme; 0 = flat."))
    args = ap.parse_args()

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

    man = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    all_arms = list(man.get("arms") or {})
    arms = [a for a in (args.arms.split(",") if args.arms else all_arms) if a]
    if not arms:
        print("  [FAIL] no arms; run scripts/build_rrc.py first")
        return 1

    mdir = resolve_model(args.model)
    print("  instrument : %s" % mdir)

    rng = random.Random(SEED)
    items = sample_items(arms, args.per_layer, rng, per_rank=args.per_rank,
                         by_state=args.by_state, per_margin=args.per_margin)
    if not items:
        print("  [FAIL] no items sampled")
        return 1
    print("  total items: %d" % len(items))

    import torch
    from transformers import AutoModel, AutoTokenizer

    # The checkpoint's runner module uses a relative import (`from .api import SystemOneApi`), so
    # the checkpoint directory must be imported AS A PACKAGE. Adding it to sys.path is not
    # enough -- a relative import needs a parent package, and `d1-3b-native` is not a valid
    # module name either. The directory is therefore registered under an alias with its own
    # search location, which is what makes the relative imports inside it resolve.
    import importlib.util
    pkg = "_d1_native_pkg"
    spec = importlib.util.spec_from_file_location(
        pkg, str(mdir / "__init__.py"),
        submodule_search_locations=[str(mdir)],
    )
    if spec is None:
        raise SystemExit("  [FAIL] could not register the checkpoint as a package: %s" % mdir)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[pkg] = mod
    init = mdir / "__init__.py"
    if not init.exists():
        init.write_text("", encoding="utf-8")
    spec.loader.exec_module(mod)

    prompt_mod = importlib.import_module(pkg + ".prompt")
    runner_mod = importlib.import_module(pkg + ".runner")
    Choice = prompt_mod.Choice
    SystemOne = runner_mod.SystemOne

    tok = AutoTokenizer.from_pretrained(str(mdir), trust_remote_code=True)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    model = AutoModel.from_pretrained(str(mdir), trust_remote_code=True,
                                      dtype=torch.bfloat16, device_map="cuda")
    s1 = SystemOne(model=model, tokenizer=tok)
    print("  loaded     : %s  VRAM %.2f GB" % (type(model).__name__,
                                               torch.cuda.memory_allocated() / 1e9))

    OUT.mkdir(parents=True, exist_ok=True)
    rows_path = OUT / ("rrc_d1_rows%s.jsonl" % args.out_tag)
    rows_path.write_text("", encoding="utf-8")

    t0 = time.time()
    done = 0
    # Requests are batched, not sent one at a time. The runner's own `run` packs every
    # single-question, image-free request into trees up to its token budget, so sending one
    # request per call defeats that packing entirely: each call becomes a chunk of one row and
    # the forward pass is paid per item. Measured on the first full run, throughput was ~15 items/s
    # on short states and ~0.16 items/s on long ones -- a factor of ~90 between arms. Batching
    # restores the packing the runner was written to do, and a failing batch falls back to
    # one-at-a-time so a single bad item cannot take the run down with it.
    REQ_BATCH = 128
    batch_ok = True

    def build_req(it):
        """One `(state, [question], images)` request for an item."""
        return (it["state"], [Choice(
            instructions=("An observed form is shown. Exactly one of the candidates is the form "
                          "that was originally intended. Report the probability of each."),
            criteria={c: None for c in it["candidates"]},
        )], [])

    with open(rows_path, "w", encoding="utf-8") as fh:
        for start in range(0, len(items), REQ_BATCH):
            batch = items[start:start + REQ_BATCH]
            if not batch_ok:
                # The packing path needs flash-attention, which this build does not have, and it
                # fails the same way every time. Retrying it per batch would print the same warning
                # thirty-odd times and pay a failed forward pass each time, so the first failure
                # turns batching off for the rest of the run rather than being rediscovered.
                results = []
                for it in batch:
                    try:
                        results.append(s1.run([build_req(it)])[0])
                    except Exception as exc:  # noqa: BLE001
                        print("  [WARN] %s failed: %s: %s"
                              % (it["item_id"], type(exc).__name__, exc), flush=True)
                        results.append(None)
            else:
                reqs = [build_req(it) for it in batch]
                try:
                    results = s1.run(reqs)
                except Exception as exc:  # noqa: BLE001
                    print("  [WARN] batched run of %d failed (%s: %s); batching off for the rest "
                          "of the run" % (len(batch), type(exc).__name__, exc), flush=True)
                    batch_ok = False
                    results = []
                    for it, rq in zip(batch, reqs):
                        try:
                            results.append(s1.run([rq])[0])
                        except Exception as exc2:  # noqa: BLE001
                            print("  [WARN] %s failed: %s: %s"
                                  % (it["item_id"], type(exc2).__name__, exc2), flush=True)
                            results.append(None)

            for it, res in zip(batch, results):
                if res is None:
                    continue
                cands = it["candidates"]
                probs = res[0][0]
                ntok = res[1]
                if len(probs) != len(cands):
                    print("  [WARN] %s returned %d probs for %d candidates"
                          % (it["item_id"], len(probs), len(cands)), flush=True)
                    continue
                pick = max(range(len(cands)), key=lambda i: probs[i])
                dif = it.get("difficulty") or {}
                fh.write(json.dumps({
                    "item_id": it["item_id"],
                    "arm": it["arm"],
                    "layer": it["layer"],
                    "language": it.get("language"),
                    # `state` and `candidates` are stored so a row is self-contained: the paired
                    # layer test matches two layers by their shared state, and recovering that by
                    # re-reading the corpus would make the analysis depend on a file that can be
                    # rebuilt while the rows are fixed.
                    "state": it["state"],
                    "candidates": cands,
                    "picked": cands[pick],
                    "root": it["root"],
                    "correct": cands[pick] == it["root"],
                    "p_max": round(max(probs), 6),
                    "p_root": (round(probs[cands.index(it["root"])], 6)
                               if it["root"] in cands else None),
                    "margin": dif.get("margin"),
                    "margin_defined": dif.get("margin_defined"),
                    "group_size": dif.get("group_size"),
                    "group_rank": dif.get("group_rank"),
                    "group_rank_source": dif.get("group_rank_source"),
                    "n_options": len(cands),
                    "prompt_tokens": ntok,
                }, ensure_ascii=False) + "\n")
                done += 1
            if done and (done % args.batch_log < REQ_BATCH):
                el = time.time() - t0
                print("  %5d/%d  %.1fs  (%.2f items/s)" % (done, len(items), el, done / el),
                      flush=True)

    rows = [json.loads(l) for l in rows_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    elapsed = time.time() - t0
    print()
    print("  evaluated %d items in %.1fs" % (len(rows), elapsed))
    if not rows:
        print("  [FAIL] no rows")
        return 1

    # Throughput is reported because it is not constant and a reader planning a replication
    # needs to know that: measured, the same script ran at ~21 items/s early in a run and under
    # 1 items/s late in one, with a failed fast path responsible for part of it (see
    # scripts/eval_rrc_d1.py's batching note). Rates are per arm and layer so a slow arm cannot
    # be mistaken for a slow script, and the fastest and slowest deciles are kept because the
    # mean hides exactly the effect worth reporting.
    rate = {"items": len(rows), "elapsed_s": round(elapsed, 1),
            "items_per_s": round(len(rows) / elapsed, 2) if elapsed else None}

    # ---- summary
    by = collections.defaultdict(list)
    for r in rows:
        by[(r["arm"], r["layer"])].append(r)

    summary = {"n_rows": len(rows), "instrument": str(mdir), "seed": SEED,
               "per_layer_cap": args.per_layer, "by_arm_layer": {},
               "sampling": ("by_state" if args.by_state else
                            "per_rank+per_margin" if (args.per_rank and args.per_margin) else
                            ("per_rank" if args.per_rank else
                             ("per_margin" if args.per_margin else "per_layer"))),
               "by_state": args.by_state, "per_rank": args.per_rank,
               "per_margin": args.per_margin,
               "out_tag": args.out_tag, "rate": rate}
    print()
    print("  accuracy by arm and layer (chance = 1/K)")
    for (arm, layer), rs in sorted(by.items()):
        n = len(rs)
        acc = sum(1 for r in rs if r["correct"]) / n
        chance = 1 / rs[0]["n_options"]
        se = (chance * (1 - chance) / n) ** 0.5
        z = (acc - chance) / se if se else float("nan")
        pmax = statistics.median(r["p_max"] for r in rs)
        pr = [r["p_root"] for r in rs if r["p_root"] is not None]
        summary["by_arm_layer"]["%s|%s" % (arm, layer)] = {
            "n": n, "acc": round(acc, 4), "chance": round(chance, 4),
            "z_vs_chance": round(z, 2), "p_max_median": round(pmax, 4),
            "p_root_median": round(statistics.median(pr), 4) if pr else None,
        }
        print("    %-13s %-7s n=%4d  acc=%.4f  chance=%.4f  z=%+6.2f  p_max med=%.3f"
              % (arm, layer, n, acc, chance, z, pmax))

    # ---- F2: the reading channel's rank effect.
    #
    # Stated as a curve over the rank, not as a two-point contrast. Rank 1 against "rank > median"
    # is a comparison whose two sides are not the same kind of thing -- one value against a
    # heterogeneous remainder -- and it is sensitive to the median splitting a tied value. The
    # curve reports each rank value with its own count and interval, so a reader can see whether
    # the quantity is monotone, flat, or reversed, rather than being told it is one of the three.
    f2 = []
    for (arm, layer), rs in sorted(by.items()):
        if layer != "L2c":
            continue
        with_rank = [r for r in rs if r["group_rank"]]
        if len(with_rank) < 20:
            continue
        curve = []
        for rk in sorted({r["group_rank"] for r in with_rank}):
            sub = [r for r in with_rank if r["group_rank"] == rk]
            k = sum(1 for r in sub if r["correct"])
            lo, hi = wilson(k, len(sub))
            curve.append({"rank": rk, "n": len(sub), "acc": round(k / len(sub), 4),
                          "ci95": [round(lo, 4), round(hi, 4)]})
        first = [r for r in with_rank if r["group_rank"] == 1]
        rest = [r for r in with_rank if r["group_rank"] > 1]
        k1 = sum(1 for r in first if r["correct"])
        k2 = sum(1 for r in rest if r["correct"])
        lo1, hi1 = wilson(k1, len(first))
        lo2, hi2 = wilson(k2, len(rest))
        # a two-proportion z, so the contrast carries a test and not only two numbers. The
        # hypothesis is rank-1 >= rest (the frequent root is easier); a positive z supports it.
        p1 = k1 / len(first) if first else 0.0
        p2 = k2 / len(rest) if rest else 0.0
        n1, n2 = len(first), len(rest)
        pp = (k1 + k2) / (n1 + n2) if (n1 + n2) else 0.0
        se = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2)) if n1 and n2 and 0 < pp < 1 else None
        z = ((p1 - p2) / se) if se else None
        entry = {
            "arm": arm,
            "n_with_rank": len(with_rank),
            "curve": curve,
            "rank_1_n": n1, "rank_1_acc": round(p1, 4), "rank_1_ci95": [round(lo1, 4), round(hi1, 4)],
            "rank_gt1_n": n2, "rank_gt1_acc": round(p2, 4),
            "rank_gt1_ci95": [round(lo2, 4), round(hi2, 4)],
            "z_rank1_minus_rest": None if z is None else round(z, 3),
            "direction": ("rank-1 easier" if z is not None and z > 1.96 else
                          "rank-1 harder" if z is not None and z < -1.96 else
                          "no separation at 0.05"),
            "rank_source": (next((r.get("group_rank_source") for r in with_rank
                                  if r.get("group_rank_source")), None)),
        }
        f2.append(entry)
        print()
        print("  F2 %s  (rank source: %s, n=%d)" % (arm, entry["rank_source"], len(with_rank)))
        for c in curve[:6]:
            print("      rank %-3d n=%4d  acc=%.4f  95%%CI[%.3f,%.3f]"
                  % (c["rank"], c["n"], c["acc"], c["ci95"][0], c["ci95"][1]))
        if len(curve) > 6:
            print("      ... %d more rank values" % (len(curve) - 6))
        print("      rank-1 %.4f [%.3f,%.3f] n=%d  vs  rank>1 %.4f [%.3f,%.3f] n=%d  z=%s  -> %s"
              % (p1, lo1, hi1, n1, p2, lo2, hi2, n2,
                 "n/a" if z is None else "%+.2f" % z, entry["direction"]))
    summary["f2_rank_effect"] = f2

    sp = OUT / ("rrc_d1_summary%s.json" % args.out_tag)
    sp.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print()
    print("  wrote %s" % rows_path)
    print("  wrote %s" % sp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
