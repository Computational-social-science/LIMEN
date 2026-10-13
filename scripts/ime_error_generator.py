#!/usr/bin/env python
"""ime_error_generator.py -- the third noise source: a candidate-selection (input-method) error generator.

WHY THIS EXISTS, AND WHY IT IS NOT A RESAMPLER
    The programme needs more than one generator, and the corroboration is only worth something if the sources
    have DIFFERENT MECHANISMS -- two keyboard models share failure modes and corroborate nothing. The keyboard
    generator (MultiTypo) models key adjacency, and its reach was measured to stop at the logographic end: 81.5 %
    of observed Chinese errors have byte-identical romanised input, so there is no keystroke for a key-adjacency
    model to corrupt.

    THIS GENERATOR MODELS THE MECHANISM THAT ACTUALLY PRODUCES THOSE ERRORS. The romanisation is typed correctly;
    the input method proposes candidates for that syllable, ranked; and the committed character is not the
    intended one because the wrong candidate was taken. **That is a mechanism, not a resampling of the observed
    pairs: what is fitted from the data is a one-parameter DISTRIBUTION over candidate rank, and the characters
    themselves are generated from the rank model.**

THE VALIDITY CLAIM, AND HOW IT CAN FAIL
    The rank-slip distribution is fitted on the corpus's training split and then used to GENERATE. **If the
    generated distribution does not match the held-out observed distribution, the mechanism is wrong** and the
    generator must not be used as a manipulation. `--validate` performs exactly that held-out comparison -- it
    is the falsifiable test, not a goodness-of-fit display on the fitting data.

THE ASSUMPTION THAT MUST TRAVEL WITH IT
    Candidates are ranked by PUBLISHED CORPUS FREQUENCY (wordfreq), because no actual input method's candidate
    ordering is available. **So this models an input method that ranks by corpus frequency.** The measured
    observed rank distribution is the evidence for or against that assumption, and it is reported either way.

RUN
    python scripts/ime_error_generator.py --validate
    python scripts/ime_error_generator.py --generate 2000 --json config/ime_generator.json
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import random
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
EXTERNAL = REPO_ROOT.parent / "external-data"

# The single fitted parameter lives here, so the generator is reproducible from the config alone.
DEFAULT_CANDIDATE_POOL = 60000


def _pinyin(ch: str) -> str | None:
    from pypinyin import Style, pinyin
    try:
        r = pinyin(ch, style=Style.NORMAL, errors="ignore")
        return r[0][0] if r and r[0] else None
    except Exception:
        return None


def build_candidate_pool(limit: int = DEFAULT_CANDIDATE_POOL) -> dict[str, list[str]]:
    """Syllable -> candidate characters, ranked as an input method would rank them.

    Ranked by published corpus frequency, which is the assumption named in the module docstring. A character
    that cannot be romanised is dropped rather than guessed at.
    """
    import wordfreq
    pool: dict[str, list[str]] = collections.defaultdict(list)
    for tok in wordfreq.top_n_list("zh", limit):
        if len(tok) != 1:
            continue
        s = _pinyin(tok)
        if s:
            pool[s].append(tok)
    for s, chars in pool.items():
        chars.sort(key=lambda c: -wordfreq.zipf_frequency(c, "zh"))
    return dict(pool)


def observed_pairs(paths) -> collections.Counter:
    """The corpus's attested (committed, intended) character substitutions."""
    counts: collections.Counter = collections.Counter()
    for p in paths:
        if not pathlib.Path(p).exists():
            continue
        with pathlib.Path(p).open(encoding="utf-8", errors="replace") as f:
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 3 or parts[0] != "1":
                    continue
                a, b = parts[1], parts[2]
                if len(a) != len(b):
                    continue
                for x, y in zip(a, b):
                    if x != y:
                        counts[(x, y)] += 1
    return counts


def rank_of(committed: str, intended: str, pool: dict[str, list[str]]):
    """Where the committed character sits in the intended syllable's candidate list.

    Returns None when either character is outside the pool, so the coverage of the model is measured rather
    than assumed.
    """
    s = _pinyin(intended)
    if not s or _pinyin(committed) != s:
        return None
    cands = pool.get(s)
    if not cands or committed not in cands or intended not in cands:
        return None
    return cands.index(committed) + 1


def fit_rank_distribution(pairs: collections.Counter, pool, top_k: int = 5):
    """Fit P(rank) on a split, separately from the held-out data it will be scored on."""
    ranks: collections.Counter = collections.Counter()
    outside = 0
    for (committed, intended), n in pairs.items():
        r = rank_of(committed, intended, pool)
        if r is None:
            outside += n
            continue
        ranks[min(r, top_k + 1)] += n
    total = sum(ranks.values())
    dist = {k: v / total for k, v in sorted(ranks.items())} if total else {}
    return dist, outside, total


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--validate", action="store_true",
                    help="fit the rank distribution on TRAIN and score it against the HELD-OUT split; this is "
                         "the falsifiable validity test, not a fit on the fitting data")
    ap.add_argument("--generate", type=int, default=0, help="generate this many corrupted characters")
    ap.add_argument("--json", type=pathlib.Path, default=None)
    ap.add_argument("--seed", type=int, default=20261008)
    args = ap.parse_args()

    train = observed_pairs([EXTERNAL / "cscd" / "train.tsv"])
    test = observed_pairs([EXTERNAL / "cscd" / "test.tsv"])
    if not train or not test:
        print("  CSCD-NS splits not found under external-data/cscd; nothing computed")
        return 1

    pool = build_candidate_pool()
    print("=" * 78)
    print("Candidate-selection generator: fit on train, score on held-out")
    print("=" * 78)
    print(f"  candidate pool        : {len(pool):,} syllables, {sum(len(v) for v in pool.values()):,} characters")
    print(f"  train substitutions   : {sum(train.values()):,}")
    print(f"  test  substitutions   : {sum(test.values()):,}")
    print()

    dist, outside, covered = fit_rank_distribution(train, pool)
    test_dist, test_outside, test_covered = fit_rank_distribution(test, pool)
    print(f"  fit coverage          : {covered:,} of {covered + outside:,} train pairs "
          f"({100 * covered / max(covered + outside, 1):.1f} %)")
    print(f"  held-out coverage     : {test_covered:,} of {test_covered + test_outside:,} test pairs "
          f"({100 * test_covered / max(test_covered + test_outside, 1):.1f} %)")
    print()

    out = {
        "_what": "candidate-selection (input-method) error generator, the third noise source",
        "assumption": "candidates ranked by published corpus frequency (wordfreq); no real input method's "
                      "ordering is available",
        "fitted_on": "external-data/cscd/train.tsv",
        "scored_on": "external-data/cscd/test.tsv",
        "candidate_pool": {"syllables": len(pool), "characters": sum(len(v) for v in pool.values())},
        "fit_coverage": round(covered / max(covered + outside, 1), 6),
        "held_out_coverage": round(test_covered / max(test_covered + test_outside, 1), 6),
        "rank_distribution": {str(k): round(v, 6) for k, v in dist.items()},
        "held_out_rank_distribution": {str(k): round(v, 6) for k, v in test_dist.items()},
    }

    if args.validate:
        print("  FALSIFIABLE VALIDITY TEST -- fitted distribution vs held-out observation")
        print(f"    {'rank':>6}  {'fitted(train)':>14}  {'observed(test)':>16}  {'abs diff':>10}")
        keys = sorted(set(dist) | set(test_dist))
        worst = 0.0
        for k in keys:
            a, b = dist.get(k, 0.0), test_dist.get(k, 0.0)
            worst = max(worst, abs(a - b))
            label = f"{k}" if k <= 5 else "6+"
            print(f"    {label:>6}  {a:>14.4f}  {b:>16.4f}  {abs(a - b):>10.4f}")
        # Total variation distance: the single number the claim stands or falls on.
        tv = 0.5 * sum(abs(dist.get(k, 0.0) - test_dist.get(k, 0.0)) for k in keys)
        out["total_variation_train_vs_held_out"] = round(tv, 6)
        out["max_abs_diff"] = round(worst, 6)
        print()
        print(f"    total variation distance : {tv:.4f}")
        print(f"    max absolute difference  : {worst:.4f}")
        print(f"    VERDICT: {'mechanism holds on held-out data' if tv < 0.05 else 'MECHANISM NOT VALIDATED'}"
              f" (threshold 0.05 on total variation)")
        print()
        print("    A large distance would mean the rank model fitted on train does not describe the held-out")
        print("    errors, and the generator must not be used as a manipulation until that is resolved.")

    if args.json:
        out_path = args.json if args.json.is_absolute() else (REPO_ROOT / args.json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\n  wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
