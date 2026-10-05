#!/usr/bin/env python
"""o1_recoverability.py -- O1's readability criterion from a mature formula, not from a judge.

WHY THIS REPLACES THE RATER FOR THE `lo` CRITERION
    The validated LLM rater saturated on exactly the comparison `lo` needs. Measured on all eight grid
    points: P(perturbed called harder than its own clean version) = 0.900-1.000, including at the mildest
    rate, with position-A flat at ~0.5. The question "which of these two is harder" is answered by noticing
    that one of them contains typos, at any dose. It measures DETECTION of corruption, not DEGREE.

    So the criterion needs a quantity that is about recovery rather than detection, and it needs to be
    computable. That quantity is the posterior probability that a reader recovers the intended word from
    the surface form, and it has a textbook formulation.

THE FORMULA, AND WHERE IT COMES FROM
    The Bayesian noisy channel. Kernighan, Church & Gale (1990) for spelling correction; Brill & Moore
    (2000) for the error model; the standard statement is Jurafsky & Martin, *Speech and Language
    Processing*, appendix B ("Spelling Correction and the Noisy Channel"):

        w_hat = argmax_w  P(surface | w) . P(w)

    P(surface | w) is the CHANNEL - how likely the intended word w is to be typed as `surface`. P(w) is the
    PRIOR - how likely w is a word at all. Both are estimable here without any human labelling:
    the channel from this project's own frozen generator, and the prior from published lexical norms.

    The quantity §12 asks about is not the argmax but the POSTERIOR MASS ON THE TRUTH:

        r(w | surface) = P(surface | w) . P(w)  /  sum_w' P(surface | w') . P(w')

    r near 1 means the reader is led to the intended word; r near 0 means the surface form points
    somewhere else. That is what "the intended content is recoverable" means operationally, and unlike a
    judge it does not saturate on presence-of-typos: at low dose r stays near 1 because the corrupted form
    still points at the truth.

WHY THE PRIOR COMES FROM PUBLISHED NORMS
    `wordfreq` aggregates published lexical frequency resources (SUBTLEX, Leeds, and others) and exposes
    Zipf frequencies. Using it rather than counting our own corpus keeps the prior independent of the
    stimulus material: a prior counted from the same texts being rated would make easy words easy by
    construction.

WHY THE CHANNEL COMES FROM THE GENERATOR
    The generator is the manipulation. Its error model is the correct P(surface | w) for this study - not a
    generic typo model. It is *measured* here rather than assumed: the script samples the frozen generator
    over a vocabulary, aligns intended against surface with a DP aligner, and tallies the confusion counts.
    So the channel is an estimate with a sample size attached, not a guess with a citation attached.

WHAT THIS SCRIPT DOES NOT DO
    It does not decide the `lo` threshold. It computes the index and reports its behaviour across the grid;
    the threshold is a protocol decision and is recorded as one.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import re
import statistics
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MEASUREMENT = REPO_ROOT / "measurement"
sys.path.insert(0, str(MEASUREMENT))

VALIDATION = MEASUREMENT / "o1_validation"
CHANNEL_FILE = VALIDATION / "channel.json"

# Pre-registered constants. Changing any of these changes the instrument.
MAX_CANDIDATE_EDITS = 2      # candidates within this many edits of the surface form
SMOOTH = 0.05                # add-k smoothing on the channel, so an unseen op is unlikely not impossible
UNSEEN_LOG = -12.0           # log-probability floor for a character operation the sample never produced
ZIPF_FLOOR = 1.0             # words rarer than this Zipf band are outside the candidate vocabulary
GRID = (0.05, 0.06, 0.07, 0.08, 0.12, 0.14, 0.16, 0.18)

# WHICH FROZEN SEED'S STIMULI THE INDEX READS. The packs carry the seed in their filename because without
# it the second seed overwrites the first; the anchor was measured on seed 0 and keeps reading seed 0.
# A different seed is a different instrument run, and must be reported as such rather than averaged in.
PACK_SEED = 0

# THE PUBLISHED ANCHOR, as a named constant so it can be guarded rather than retyped in prose.
# Rayner, White, Johnson & Liversedge (2006), "Raeding wrods with jubmled lettres: There is a cost",
# Psychological Science 17(3): first and last letter of each word fixed, the interior rearranged; readers
# answered comprehension questions with high accuracy and read ~11% slower. This is the MEASURED value of
# that condition under this index (interior-scrambled variant, the harsher of the two), and it is what
# `lo` has to clear. A published number that only ever appears in a document is a number that drifts.
RAYNER_ANCHOR_MEAN_R = 0.4480
RAYNER_ANCHOR_CITATION = ("Rayner, White, Johnson & Liversedge (2006), Psychological Science 17(3), "
                          "interior-scrambled variant")


def zipf(word: str) -> float:
    """Published lexical frequency, via the `wordfreq` aggregation of SUBTLEX/Leeds and others."""
    import wordfreq
    return wordfreq.zipf_frequency(word, "en")


def prior(word: str) -> float:
    """P(w) up to a constant. Zipf is log10 per billion, so 10**(z-9) is a per-billion rate."""
    z = zipf(word)
    return 0.0 if z < ZIPF_FLOOR else 10.0 ** (z - 9.0)


def load_vocabulary(limit: int = 20000, min_zipf: float = 2.5) -> list[str]:
    """A candidate vocabulary of common English words, filtered by published frequency."""
    import wordfreq
    words = [w for w in wordfreq.top_n_list("en", limit * 2) if w.isalpha() and len(w) >= 2]
    words = [w for w in words if zipf(w) >= min_zipf]
    return words[:limit]


# ---------------------------------------------------------------------------------------------
# The channel, MEASURED from the frozen generator.
# ---------------------------------------------------------------------------------------------
def _align(a: str, b: str, sub: dict, ins: dict, dele: dict) -> list[tuple[str, str]]:
    """Weighted DP alignment of intended `a` against observed `b`, returning character pairs.

    Returns a list of (intended_char_or_empty, observed_char_or_empty). Empty on the left is an insertion
    relative to the intended word; empty on the right is a deletion.
    """
    n, m = len(a), len(b)
    NEG = -1e18
    dp = [[NEG] * (m + 1) for _ in range(n + 1)]
    bk = [[None] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            if i == 0 and j == 0:
                continue
            best, arg = NEG, None
            if i and dp[i - 1][j] + dele.get((a[i - 1],), -12.0) > best:
                best, arg = dp[i - 1][j] + dele.get((a[i - 1],), -12.0), ("del", i - 1, j)
            if j and dp[i][j - 1] + ins.get((b[j - 1],), -12.0) > best:
                best, arg = dp[i][j - 1] + ins.get((b[j - 1],), -12.0), ("ins", i, j - 1)
            if i and j and dp[i - 1][j - 1] + sub.get((a[i - 1], b[j - 1]), -12.0) > best:
                best, arg = dp[i - 1][j - 1] + sub.get((a[i - 1], b[j - 1]), -12.0), ("sub", i - 1, j - 1)
            dp[i][j], bk[i][j] = best, arg
    out, i, j = [], n, m
    while i or j:
        kind, pi, pj = bk[i][j]
        if kind == "sub":
            out.append((a[pi], b[pj])); i, j = pi, pj
        elif kind == "del":
            out.append((a[pi], "")); i = pi
        else:
            out.append(("", b[pj])); j = pj
    return out[::-1]


def build_channel(sample_words: int = 4000, lam: float = 0.12, seed: int = 0) -> dict:
    """Estimate the character confusion channel by sampling the frozen generator.

    Log-probabilities are stored because the downstream product of many character probabilities
    underflows to zero in float64 well before a 12-character word is finished.
    """
    from typo_noise import typo_noise
    vocab = load_vocabulary(sample_words)
    sub_c: collections.Counter = collections.Counter()
    ins_c: collections.Counter = collections.Counter()
    del_c: collections.Counter = collections.Counter()
    sub_b: collections.Counter = collections.Counter()
    ins_b: collections.Counter = collections.Counter()
    del_b: collections.Counter = collections.Counter()
    n_pairs = 0
    for k, w in enumerate(vocab):
        surf, _ops = typo_noise(w, f"chan-{k}", lam, seed)
        surf = re.sub(r"\s+", "", surf)
        if surf == w:
            continue
        n_pairs += 1
        for a_ch, b_ch in _align(w, surf, {}, {}, {}):   # uniform alignment just to find the pairs
            if a_ch and b_ch:
                sub_c[(a_ch, b_ch)] += 1; sub_b[a_ch] += 1
            elif a_ch:
                del_c[(a_ch,)] += 1; del_b[a_ch] += 1
            else:
                ins_c[(b_ch,)] += 1; ins_b["*"] += 1
    # Each class gets its own denominator, and they are NOT interchangeable:
    #   substitution  P(observe b | intended a) = count(a->b) / count(intended a)
    #   deletion      P(drop a)                  = count(a dropped) / count(intended a)
    #   insertion     P(emit b)                  = count(b emitted) / TOTAL insertions
    # An earlier version divided the insertion count by the count of the emitted character, which is not a
    # probability at all - it silently produced values above one for common letters.
    alpha = SMOOTH
    n_ins_total = sum(ins_c.values()) + 1
    sub_den = {a: sum(v for (x, _), v in sub_c.items() if x == a) for a in {x for x, _ in sub_c}}
    del_den = {a: v for (a,), v in del_c.items()}
    ins_v = len(ins_c) + 1

    sub = {(a, b): math.log((c + alpha) / (sub_den[a] + alpha * (len(sub_den) + 1)))
           for (a, b), c in sub_c.items()}
    ins = {(b,): math.log((c + alpha) / (n_ins_total + alpha * ins_v))
           for (b,), c in ins_c.items()}
    dele = {(a,): math.log((c + alpha) / (del_den[a] + alpha * 2))
            for (a,), c in del_c.items()}
    return {"sub": sub, "ins": ins, "del": dele, "n_pairs": n_pairs,
            "lam_sampled": lam, "vocab_sampled": len(vocab),
            "counts": {"sub": len(sub_c), "ins": len(ins_c), "del": len(del_c)}}


def save_channel(ch: dict) -> None:
    def enc(d):
        return {"|".join(k): v for k, v in d.items()}
    VALIDATION.mkdir(parents=True, exist_ok=True)
    CHANNEL_FILE.write_text(json.dumps(
        {"sub": enc(ch["sub"]), "ins": enc(ch["ins"]), "del": enc(ch["del"]),
         "n_pairs": ch["n_pairs"], "lam_sampled": ch["lam_sampled"],
         "vocab_sampled": ch["vocab_sampled"], "counts": ch["counts"]}, indent=2), encoding="utf-8")


def load_channel() -> dict:
    if not CHANNEL_FILE.exists():
        raise SystemExit(f"no channel at {CHANNEL_FILE}; run --build-channel first")
    raw = json.loads(CHANNEL_FILE.read_text(encoding="utf-8"))
    return {"sub": {tuple(k.split("|")): v for k, v in raw["sub"].items()},
            "ins": {tuple(k.split("|")): v for k, v in raw["ins"].items()},
            "del": {tuple(k.split("|")): v for k, v in raw["del"].items()},
            **{k: raw[k] for k in ("n_pairs", "lam_sampled", "vocab_sampled", "counts")}}


def channel_logprob(ch: dict, surface: str, intended: str) -> float:
    """log P(surface | intended), via the DP alignment under the estimated channel.

    Every character pair gets a value: a pair never seen in the channel sample falls back to the smoothed
    floor rather than to None. The first version of this line wrote the fallback with `or -12.0` inside a
    conditional expression, which binds as `X if c else (Y or -12.0)` - so an unknown SUBSTITUTION returned
    None and the sum raised. A missing branch is exactly where a probability model must not be silent.
    """
    pairs = _align(intended, surface, ch["sub"], ch["ins"], ch["del"])
    total = 0.0
    for a, b in pairs:
        if a and b:
            total += ch["sub"].get((a, b), UNSEEN_LOG)
        elif a:
            total += ch["del"].get((a,), UNSEEN_LOG)
        else:
            total += ch["ins"].get((b,), UNSEEN_LOG)
    return total


def damerau_leq(a: str, b: str, k: int) -> bool:
    """True if the optimal-string-alignment distance between a and b is at most k."""
    if abs(len(a) - len(b)) > k:
        return False
    prev2: list[int] = []
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            if i > 1 and j > 1 and ca == b[j - 2] and a[i - 2] == cb:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        prev2, prev = prev, cur
        if min(cur) > k:
            return False
    return prev[len(b)] <= k


def recoverability(surface: str, intended: str, ch: dict, vocab: list[str]) -> dict:
    """Posterior mass on the intended word, over candidates within MAX_CANDIDATE_EDITS of the surface."""
    cands = [w for w in vocab if damerau_leq(w, surface, MAX_CANDIDATE_EDITS)]
    if intended in cands:
        pass
    else:
        cands.append(intended)
    if not cands:
        return {"r": 0.0, "map": None, "n_cand": 0, "rank": None}
    scores = []
    for w in cands:
        lp = channel_logprob(ch, surface, w) + math.log(max(prior(w), 1e-12))
        scores.append((lp, w))
    mx = max(s for s, _ in scores)
    ws = sum(math.exp(s - mx) for s, _ in scores)
    by_word = {w: math.exp(s - mx) / ws for s, w in scores}
    order = sorted(scores, reverse=True)
    rank = next((i + 1 for i, (_, w) in enumerate(order) if w == intended), None)
    return {"r": by_word.get(intended, 0.0), "map": order[0][1], "n_cand": len(cands), "rank": rank}


def rayner_scramble(word: str, rng) -> str:
    """Rayner et al. (2006) 'Raeding wrods with jubmled lettres': first and last letter fixed, the
    interior rearranged. The paper's own example is `characters -> chatrecras`, `sentence -> sencetne`,
    `have -> hvae`. For len <= 3 the word is unchanged, which is what the constraint implies."""
    if len(word) <= 3:
        return word
    mid = list(word[1:-1])
    rng.shuffle(mid)
    return word[0] + "".join(mid) + word[-1]


def rayner_transpose(word: str) -> str:
    """The adjacent-pair variant of the same manipulation: swap interior letter pairs, first/last fixed."""
    if len(word) <= 3:
        return word
    m = list(word[1:-1])
    for i in range(0, len(m) - 1, 2):
        m[i], m[i + 1] = m[i + 1], m[i]
    return word[0] + "".join(m) + word[-1]


def content_words(s: str) -> list[str]:
    return [w for w in re.findall(r"[A-Za-z][A-Za-z'-]*", s) if len(w) >= 3]


def item_index(clean: str, perturbed: str, ch: dict, vocab: list[str]) -> dict:
    """Two indices, because they answer different halves and neither is redundant.

    `recovered`  = share of content words whose MAP reading under the channel IS the intended word.
                   This is the "did the reader get there" quantity and is what `lo` needs.
    `mean_r`     = mean posterior mass on the truth. Continuous, so it still discriminates when
                   `recovered` is saturated at 1.0.
    """
    # Pair the clean words with their corrupted counterparts by ORDER, which is what typo_noise preserves:
    # it edits characters inside tokens and never reorders or drops words (its own self-tests assert the
    # whitespace structure).
    cw = content_words(clean)
    pw = re.findall(r"\S+", perturbed)
    pairs = []
    for i, w in enumerate(cw):
        surf = None
        for tok in pw:
            if damerau_leq(w.lower(), re.sub(r"[^a-z'-]", "", tok.lower()), MAX_CANDIDATE_EDITS):
                surf = re.sub(r"[^a-z'-]", "", tok.lower())
                break
        if surf:
            pairs.append((w.lower(), surf))
    if not pairs:
        return {"recovered": float("nan"), "mean_r": float("nan"), "n": 0}
    rs = [recoverability(s, w, ch, vocab) for w, s in pairs]
    hit = sum(1 for x, (w, _) in zip(rs, pairs) if x["map"] == w)
    return {"recovered": hit / len(rs),
            "mean_r": statistics.mean(x["r"] for x in rs),
            "n": len(rs), "per_word": [x["r"] for x in rs]}


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--build-channel", action="store_true")
    ap.add_argument("--demo", type=int, metavar="N", help="show per-item indices on N grid points")
    ap.add_argument("--seed-variance", action="store_true",
                    help="recoverability across the generator's frozen seeds {0,1,2}, and the gap/SD ratio")
    ap.add_argument("--anchor", action="store_true",
                    help="measure the published human condition (Rayner 2006) with the same index")
    ap.add_argument("--self-test", action="store_true",
                    help="known-answer controls: channel and distance primitives")
    args = ap.parse_args()

    if args.self_test:
        fails = []
        if not damerau_leq("access", "acess", 1):
            fails.append("one deletion not detected")
        if damerau_leq("access", "access", 1) is not True:
            fails.append("identical strings reported as distant")
        if not damerau_leq("recieve", "receive", 2):
            fails.append("transposition not detected within 2")
        if damerau_leq("access", "completely", 2):
            fails.append("distant strings reported as near")
        pairs = _align("access", "acess", {}, {}, {})
        if [a for a, _ in pairs if a] != list("access"):
            fails.append(f"alignment dropped intended characters: {pairs}")
        if fails:
            print("  [FAIL] self-test:")
            for f in fails:
                print("      -", f)
            return 1
        print("  [OK] self-test: distance and alignment answer known cases correctly")
        return 0

    if args.build_channel:
        ch = build_channel()
        save_channel(ch)
        print(f"  channel estimated from the frozen generator: {ch['n_pairs']} corrupted words, "
              f"{ch['counts']} distinct character operations -> {CHANNEL_FILE}")
        return 0

    if args.seed_variance:
        import csv
        from typo_noise import typo_noise
        ch = load_channel()
        vocab = load_vocabulary(20000)
        pack = sorted((REPO_ROOT / "measurement" / "o1_packs").glob("o1_*_lam005_seed0_raterA.csv"))
        rows = list(csv.DictReader([l for l in pack[0].read_text(encoding="utf-8").splitlines()
                                    if not l.startswith("#")]))[:60]
        print("  SEED VARIANCE: the generator's own frozen seeds are {0,1,2}. The recoverability range")
        print("  across the ladder is ~5% relative, so the seed spread decides whether that range is")
        print("  signal or noise. Regenerated from the clean text at each (lambda, seed).")
        print()
        print("  lambda   seed=0   seed=1   seed=2     mean      SD")
        out = {}
        for lam in (0.05, 0.12, 0.18):
            vals = []
            for seed in (0, 1, 2):
                ix = []
                for k, r in enumerate(rows):
                    pert, _ = typo_noise(r["clean"], f"sv-{k}", lam, seed)
                    ix.append(item_index(r["clean"], pert, ch, vocab))
                vals.append(statistics.mean(x["mean_r"] for x in ix if x["n"]))
            mu = statistics.mean(vals)
            sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
            out[str(lam)] = {"per_seed": vals, "mean": mu, "sd": sd}
            print(f"  {lam:<7} {vals[0]:8.4f} {vals[1]:8.4f} {vals[2]:8.4f}  {mu:7.4f}  {sd:.4f}")
            # seed 0 must reproduce the pack the index was first computed on
        lo_mu, mid_mu = out["0.05"]["mean"], out["0.18"]["mean"]
        pooled = statistics.mean([out["0.05"]["sd"], out["0.18"]["sd"]])
        gap = lo_mu - mid_mu
        print()
        print(f"  lo(0.05) - mid(0.18) gap = {gap:.4f}   pooled seed SD = {pooled:.4f}"
              f"   gap / SD = {gap / pooled:.2f}")
        print(f"  anchor floor (Rayner 2006, scrambled) = 0.4480")
        print(f"  lo clears the anchor by {lo_mu - 0.4480:+.4f}; mid clears it by {mid_mu - 0.4480:+.4f}")
        if gap / pooled < 2.0:
            print("\n  [FINDING] the ladder's range is within about two seed standard deviations, so the")
            print("            lo-to-mid separation is NOT resolved against generator noise. Widening the")
            print("            edit classes is therefore required before the ladder can be calibrated, and")
            print("            this measurement is the acceptance margin that change has to beat.")
        else:
            print("\n  [OK] the separation exceeds twice the seed SD, so it is resolved against generator")
            print("       noise; the ladder's range is small but real.")
        (VALIDATION / "seed_variance.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
        return 0

    if args.anchor:
        import csv
        import random
        rng = random.Random(0)
        ch = load_channel()
        vocab = load_vocabulary(20000)
        pack = sorted((REPO_ROOT / "measurement" / "o1_packs").glob("o1_*_lam005_seed0_raterA.csv"))
        rows = list(csv.DictReader([l for l in pack[0].read_text(encoding="utf-8").splitlines()
                                    if not l.startswith("#")]))[:60]
        print("  ANCHOR: the published human condition, measured with the same index")
        print("  Rayner et al. (2006) - first and last letter fixed, interior rearranged - readers")
        print("  answered comprehension questions with high accuracy and read ~11% slower. So a")
        print("  condition at THAT level of disruption is one humans demonstrably handle.")
        print()
        for label, fn in (("interior scrambled", rayner_scramble),
                          ("interior adjacent transposed", rayner_transpose)):
            idx = []
            for r in rows:
                if fn is rayner_scramble:
                    pert = " ".join(rayner_scramble(w, rng) if len(w) > 3 else w
                                    for w in re.findall(r"\S+", r["clean"]))
                else:
                    pert = " ".join(rayner_transpose(w) if len(w) > 3 else w
                                    for w in re.findall(r"\S+", r["clean"]))
                idx.append(item_index(r["clean"], pert, ch, vocab))
            mr = statistics.mean(x["mean_r"] for x in idx if x["n"])
            rec = statistics.mean(x["recovered"] for x in idx if x["n"])
            print(f"    {label:30s} mean_r = {mr:.3f}   recovered = {rec:.3f}")
        measured = {}
        for label, fn in (("scrambled", rayner_scramble), ("transposed", rayner_transpose)):
            idx = []
            for r in rows:
                if fn is rayner_scramble:
                    pert = " ".join(rayner_scramble(w, rng) if len(w) > 3 else w
                                    for w in re.findall(r"\S+", r["clean"]))
                else:
                    pert = " ".join(rayner_transpose(w) if len(w) > 3 else w
                                    for w in re.findall(r"\S+", r["clean"]))
                idx.append(item_index(r["clean"], pert, ch, vocab))
            measured[label] = statistics.mean(x["mean_r"] for x in idx if x["n"])
        grid_mr = {}
        print()
        print("    grid for comparison (frozen generator):")
        for lam in GRID:
            pk = sorted((REPO_ROOT / "measurement" / "o1_packs")
                        .glob(f"o1_*_lam{int(round(lam * 100)):03d}_seed{PACK_SEED}_raterA.csv"))
            if not pk:
                continue
            rr = list(csv.DictReader([l for l in pk[0].read_text(encoding="utf-8").splitlines()
                                      if not l.startswith("#")]))[:60]
            ix = [item_index(x["clean"], x["perturbed"], ch, vocab) for x in rr]
            grid_mr[lam] = statistics.mean(x["mean_r"] for x in ix if x["n"])
            print(f"      lambda={lam:<5} mean_r = {grid_mr[lam]:.3f}")
        lo = min(GRID)
        clears = [l for l in sorted(GRID) if grid_mr.get(l, 0.0) >= RAYNER_ANCHOR_MEAN_R]
        payload = {"anchor_mean_r": RAYNER_ANCHOR_MEAN_R, "anchor_citation": RAYNER_ANCHOR_CITATION,
                   "rayne_conditions_measured": measured, "grid_mean_r": {str(k): v for k, v in grid_mr.items()},
                   "lambda_lo_by_anchor": clears[0] if clears else None,
                   "lambda_mid_by_anchor": clears[-1] if clears else None,
                   "lo_clears_anchor": bool(clears and clears[0] == lo),
                   "margin_at_lo": (grid_mr.get(lo, 0.0) - RAYNER_ANCHOR_MEAN_R)}
        (VALIDATION / "anchor.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print()
        print(f"    anchor floor = {RAYNER_ANCHOR_MEAN_R:.4f} ({RAYNER_ANCHOR_CITATION})")
        print(f"    smallest grid point clearing it = lambda {clears[0] if clears else None}"
              f"   margin at lo = {payload['margin_at_lo']:+.4f}")
        print(f"    largest  grid point clearing it = lambda {clears[-1] if clears else None}"
              f"   (the most stressed point still inside human tolerance)")
        print(f"    written to {VALIDATION / 'anchor.json'}")
        return 0 if payload["lo_clears_anchor"] else 1

    if args.demo:
        import csv
        ch = load_channel()
        vocab = load_vocabulary(20000)
        print(f"  vocabulary {len(vocab)} words (Zipf >= 2.5, published norms)")
        print(f"  channel from {ch['n_pairs']} sampled words at lambda={ch['lam_sampled']}")
        print()
        print("  lambda   recovered   mean_r   n_items")
        for lam in sorted(GRID)[: args.demo]:
            pack = sorted((REPO_ROOT / "measurement" / "o1_packs")
                          .glob(f"o1_*_lam{int(round(lam * 100)):03d}_seed{PACK_SEED}_raterA.csv"))
            if not pack:
                continue
            rows = list(csv.DictReader([l for l in pack[0].read_text(encoding="utf-8").splitlines()
                                        if not l.startswith("#")]))
            idx = [item_index(r["clean"], r["perturbed"], ch, vocab) for r in rows[:60]]
            rec = statistics.mean(x["recovered"] for x in idx if x["n"])
            mr = statistics.mean(x["mean_r"] for x in idx if x["n"])
            print(f"  {lam:<7} {rec:9.3f}  {mr:7.3f}   {sum(1 for x in idx if x['n'])}")
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())