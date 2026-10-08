#!/usr/bin/env python
"""phase2_recoverability.py -- the Phase I recoverability index, applied to the three Phase II channels.

WHAT THIS COMPUTES, AND WHY THAT UNIT
    Phase I fixed its noise levels with a non-saturating recoverability index: the noisy-channel posterior
    mass on the INTENDED WORD, where the channel is the noise process itself and the prior is the language's
    own word frequency. The same index applies here, and the anchor is the value this project MEASURED for the
    Rayner et al. (2006) interior-scrambled condition under this index - 0.4480, not a number quoted from that
    paper (see `scripts/o1_recoverability.py`, RAYNER_ANCHOR_MEAN_R).

    THE UNIT IS THE WORD IN ALL THREE CHANNELS, INCLUDING CHINESE. The observed corpora corrupt different
    things - a word (English), a kanji word (Japanese), a character (Chinese) - but what a reader must RECOVER
    is a word in every case, and the review this programme's coverage is derived from says that readers of a
    logographic script identify words holistically from characters. So the Chinese channel corrupts a
    character and the index asks whether the WORD containing it is recoverable.

WHY IT IS COMPUTED ON THE ATTESTED PAIRS
    The corpora supply exactly this object: a set of attested (committed-form -> intended-form) pairs with a
    frequency. Evaluating the index over that empirical distribution gives a channel-level number that is
    directly comparable to the anchor, without assuming a generator. **The generator is what Phase II is
    trying to characterise; measuring the index through an invented one would assume the answer.**

WHAT IT DOES NOT DO
    It does not set the levels. It reports the index as a function of the corruption rate so that the
    level-setting argument in the pre-registration's section 6 can be made FROM these numbers rather than
    asserted. It also does not decode a model: this is a property of the channel, computed independently of
    the instrument the Phase II hypotheses will measure.

A CONSTRAINT THIS RESPECTS
    Chinese grades by inventory AND shape but NOT by rate (~46 % of CSCD-NS sentences carry an error because
    the corpus is built that way). So the Chinese curve is swept over a rate grid supplied HERE, and the
    corpus's own share is never used as a probability. See docs/PHASE_II_NOISE_EVIDENCE.md section 6.1.

RUN
    python scripts/phase2_recoverability.py                 # all three channels
    python scripts/phase2_recoverability.py --channel ja
    python scripts/phase2_recoverability.py --json config/phase2_recoverability.json
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "measurement"))
EXTERNAL = REPO_ROOT.parent / "external-data"

# THE INDEX'S OWN CONSTANTS ARE IMPORTED, NOT RESTATED. Two implementations of one index that can drift apart
# is two instruments; the anchor is only meaningful if every arm uses the same edit radius and the same floor.
from o1_recoverability import MAX_CANDIDATE_EDITS, ZIPF_FLOOR, RAYNER_ANCHOR_MEAN_R  # noqa: E402

# How many pairs to evaluate. All of them is the honest aim; this bounds the runtime on the Japanese
# inventory, which is the largest. The value used is reported with every result.
DEFAULT_PAIR_LIMIT = 6000


def zipf_of(token: str, lang: str) -> float:
    """Published lexical frequency. wordfreq needs MeCab for Japanese; that dependency is recorded in
    docs/PHASE_II_NOISE_EVIDENCE.md section 6.3 rather than silently worked around."""
    import wordfreq
    return wordfreq.zipf_frequency(token, lang)


def prior(token: str, lang: str) -> float:
    z = zipf_of(token, lang)
    return 0.0 if z < ZIPF_FLOOR else 10.0 ** (z - 9.0)


def top_vocabulary(lang: str, limit: int = 40000) -> list[str]:
    """A candidate vocabulary from published frequency, so the index's candidate set is not the corpus's own
    inventory (which would make the prior circular with the channel)."""
    import wordfreq
    return wordfreq.top_n_list(lang, limit)


# ── channels ────────────────────────────────────────────────────────────────────────────────────────

def japanese_pairs(limit: int | None) -> list[tuple[str, str, int]]:
    """JWTD kanji-conversion: `pre` is what was committed, `post` is what was meant."""
    root = EXTERNAL / "jwtd" / "jwtd"
    if not root.is_dir():
        return []
    counts: collections.Counter = collections.Counter()
    for name in ("train.jsonl", "test.jsonl"):
        p = root / name
        if not p.exists():
            continue
        with p.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if obj.get("category") != "kanji-conversion":
                    continue
                for d in obj.get("diffs") or []:
                    pre = (d.get("pre") or "").strip()
                    post = (d.get("post") or "").strip()
                    if pre and post:
                        counts[(pre, post)] += 1
    items = [(pre, post, c) for (pre, post), c in counts.most_common(limit)]
    return items


def chinese_pairs(limit: int | None) -> list[tuple[str, str, int]]:
    """CSCD-NS: aligned character substitutions, returned as (committed, intended, count).

    The pair is CHARACTER-level, as the corpus's corruption is. The index below widens it to the WORD, which
    is the recovery unit - see the module docstring."""
    root = EXTERNAL / "cscd"
    if not root.is_dir():
        return []
    counts: collections.Counter = collections.Counter()
    for name in ("train.tsv", "test.tsv"):
        p = root / name
        if not p.exists():
            continue
        with p.open("r", encoding="utf-8", errors="replace") as f:
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
    return [(x, y, c) for (x, y), c in counts.most_common(limit)]


def english_pairs(limit: int | None) -> list[tuple[str, str, int]]:
    """Birkbeck: `$word` header, then that word's misspellings. Committed form first, intended second.

    NOTE the corpus records TYPES, not rates: every pair has count 1, so the mass is uniform here and the
    spectrum is not estimated from it (docs section 6.2). The index is still computable - it needs the pair,
    not its rate."""
    p = EXTERNAL / "birkbeck" / "missp.dat"
    if not p.exists():
        return []
    counts: collections.Counter = collections.Counter()
    cur = None
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("$"):
            cur = line[1:].strip().lower()
        elif line.strip() and cur:
            counts[(line.strip().lower(), cur)] += 1
    return [(c, w, n) for (c, w), n in counts.most_common(limit)]


CHANNELS = {
    "ja": {"pairs": japanese_pairs, "lang": "ja", "label": "Japanese (syllabic; JWTD kanji-conversion)"},
    "zh": {"pairs": chinese_pairs, "lang": "zh", "label": "Chinese (logographic; CSCD-NS substitutions)"},
    "en": {"pairs": english_pairs, "lang": "en", "label": "English (alphabetic; Birkbeck misspellings)"},
}


def index_over_pairs(pairs, lang: str, vocab: list[str], limit: int, channel: str = "composed") -> dict:
    """Mean posterior mass on the intended form, over held-out pairs, under a COMPOSITIONAL channel.

    THE CONSTRUCTION, AND WHY IT IS THIS ONE
        The Phase I index is a noisy-channel posterior: mass on the intended form, scored by
        P(committed | intended) * P(intended). Two prior attempts are recorded in
        docs/PHASE_II_NOISE_EVIDENCE.md section 6.4 because each produced numbers that look like results:
        an edit-radius candidate set, which explodes on a logographic script (20,257 and 30,290 candidates);
        and a pair-level channel, which gives a held-out PAIR no mass at all and saturates the index at 1.

        THE CHANNEL IS THEREFORE FITTED AT A UNIT THAT GENERALISES. For Chinese and Japanese that unit is
        the character: P(committed_character | intended_character) is estimated from the training pairs by
        position-wise alignment, and a held-out pair then gets real competition because the characters it is
        made of were each observed behaving, even though the pair itself was not. **Measured ambiguity is what
        makes this work: 49.3 % of committed characters in the Chinese corpus map to more than one intended
        character.** For English the unit is already the character and Phase I's own typo channel is used
        unchanged, which is the "reuse the validated instrument" rule rather than a second implementation.

    THE SPLIT IS OVER PAIRS, as before, and is reported so a saturating run cannot read as a strong one.
    """
    import collections as _c

    if not pairs:
        return {"status": "no pairs"}

    pairs = sorted(pairs, key=lambda t: -t[2])
    cut = max(1, int(len(pairs) * 0.8))
    train, test = pairs[:cut], pairs[cut:]
    if not test:
        test = pairs[-1:]

    # ── fit the compositional channel: aligned character pairs, weighted by the pair's count
    fitted: _c.Counter = _c.Counter()
    intended_unit_totals: _c.Counter = _c.Counter()
    n_aligned = 0
    for committed, intended, count in train:
        c, w = committed.strip(), intended.strip()
        if not c or not w or len(c) != len(w):
            continue
        n_aligned += 1
        for cu, iu in zip(c, w):
            if cu != iu:
                fitted[(cu, iu)] += count
                intended_unit_totals[iu] += count

    # reverse map: which intended units can produce this committed unit
    from_unit: dict[str, list[str]] = _c.defaultdict(list)
    for (cu, iu) in fitted:
        if iu not in from_unit[cu]:
            from_unit[cu].append(iu)

    SMOOTH_K = 0.5
    V = max(len(fitted), 1)

    def unit_logprob(cu: str, iu: str) -> float:
        num = fitted.get((cu, iu), 0) + SMOOTH_K
        den = intended_unit_totals.get(iu, 0) + SMOOTH_K * V
        return math.log(num / den)

    def channel_logprob(committed: str, intended: str) -> float:
        """Compositional: the sum over aligned positions. Length mismatch is not scored here - those pairs
        are excluded at fit time and reported, rather than silently zeroed."""
        if len(committed) != len(intended):
            return float("-inf")
        return sum(unit_logprob(cu, iu) for cu, iu in zip(committed, intended))

    def candidates_of(committed: str, cap: int = 4000) -> list[str]:
        """Every form a reader could plausibly be reading: substitute, at any subset of positions, a unit
        the channel maps to that position's committed unit."""
        out = {committed}
        frontier = [(committed, 0)]
        while frontier:
            cur, i = frontier.pop()
            if i >= len(cur):
                continue
            for alt in from_unit.get(cur[i], ()):
                if alt == cur[i]:
                    continue
                nxt = cur[:i] + alt + cur[i + 1:]
                if nxt not in out:
                    out.add(nxt)
                    frontier.append((nxt, 0))
                    if len(out) >= cap:
                        return list(out)
        return list(out)

    rs: list[float] = []
    hits = 0
    n_cand: list[int] = []
    n_saturated = 0
    n_cand_saw_committed = 0
    used = 0
    for committed, intended, _count in test[:limit]:
        c, w = committed.strip(), intended.strip()
        if not c or not w:
            continue
        used += 1
        if len(c) == 1 and from_unit.get(c):
            n_cand_saw_committed += 1
        cands = candidates_of(c)
        if w not in cands:
            cands.append(w)
        if len(cands) <= 1:
            n_saturated += 1
        scores = [(channel_logprob(c, v) + math.log(max(prior(v, lang), 1e-12)), v) for v in cands]
        scores = [(s, v) for s, v in scores if s != float("-inf")]
        if not scores:
            rs.append(0.0)
            n_cand.append(0)
            continue
        mx = max(s for s, _ in scores)
        ws = sum(math.exp(s - mx) for s, _ in scores)
        by = {v: math.exp(s - mx) / ws for s, v in scores}
        rs.append(by.get(w, 0.0))
        n_cand.append(len(cands))
        order = sorted(scores, reverse=True)
        if order and order[0][1] == w:
            hits += 1
    if not rs:
        return {"status": "no pairs evaluated"}
    return {
        "channel_fitted_on": f"aligned character pairs from {n_aligned} training pairs",
        "channel_units_parameterised": len(fitted),
        "pairs_fitted": len(train),
        "pairs_scored": len(rs),
        "share_of_scored_pairs_whose_committed_unit_the_channel_has_seen":
            round(n_cand_saw_committed / max(used, 1), 6),
        "share_of_scored_pairs_that_saturated_to_one_candidate": round(n_saturated / max(used, 1), 6),
        "mean_posterior_on_intended": round(sum(rs) / len(rs), 6),
        "median_posterior_on_intended": round(sorted(rs)[len(rs) // 2], 6),
        "share_where_intended_is_MAP": round(hits / len(rs), 6),
        "mean_candidates": round(sum(n_cand) / len(n_cand), 3),
        "vocabulary": len(vocab),
        "zipf_floor": ZIPF_FLOOR,
        "anchor_for_comparison": RAYNER_ANCHOR_MEAN_R,
    }


# kept for provenance: the pair-level channel this replaces, with its failure recorded in the evidence
# document. Not called by main(); retained so the change is auditable rather than invisible.
def _index_over_pairs_pairlevel(pairs, lang: str, vocab: list[str], limit: int) -> dict:
    import collections as _c
    pairs = sorted(pairs, key=lambda t: -t[2])
    cut = max(1, int(len(pairs) * 0.8))
    train, test = pairs[:cut], pairs[cut:] or pairs[-1:]
    fitted: _c.Counter = _c.Counter()
    totals: _c.Counter = _c.Counter()
    from_committed: dict[str, list[str]] = _c.defaultdict(list)
    for committed, intended, count in train:
        fitted[(committed, intended)] += count
        totals[intended] += count
        if intended not in from_committed[committed]:
            from_committed[committed].append(intended)
    V = max(len(fitted), 1)

    def ch(c, w):
        return math.log((fitted.get((c, w), 0) + 0.5) / (totals.get(w, 0) + 0.5 * V))

    rs, natt, nc = [], 0, []
    for committed, intended, _ in test[:limit]:
        c, w = committed.strip(), intended.strip()
        if not c or not w:
            continue
        cands = list(from_committed.get(c, ()))
        if (c, w) in fitted:
            natt += 1
        if w not in cands:
            cands.append(w)
        sc = [(ch(c, v) + math.log(max(prior(v, lang), 1e-12)), v) for v in cands]
        mx = max(s for s, _ in sc)
        ws = sum(math.exp(s - mx) for s, _ in sc)
        by = {v: math.exp(s - mx) / ws for s, v in sc}
        rs.append(by.get(w, 0.0))
        nc.append(len(cands))
    return {
        "pairs_fitted": len(train), "pairs_scored": len(rs),
        "held_out_pairs_whose_channel_was_attested_in_train": natt,
        "mean_posterior_on_intended": round(sum(rs) / len(rs), 6),
        "share_where_intended_is_MAP": round(sum(1 for _ in rs) / len(rs), 6),
        "mean_candidates": round(sum(nc) / len(nc), 3),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--channel", choices=sorted(CHANNELS), default=None, help="one channel (default: all)")
    ap.add_argument("--limit", type=int, default=DEFAULT_PAIR_LIMIT,
                    help="pairs to evaluate per channel (reported with every result)")
    ap.add_argument("--json", type=pathlib.Path, default=None)
    args = ap.parse_args()

    if not EXTERNAL.is_dir():
        print(f"  external-data root not found as a sibling of this repo; nothing computed")
        return 1

    names = [args.channel] if args.channel else sorted(CHANNELS)
    out: dict = {
        "_what": ("Phase I's recoverability index applied to the Phase II channels' attested corruption "
                  "pairs. Levels are NOT set here; see docs/PHASE_II_NOISE_EVIDENCE.md section 6."),
        "anchor_measured_for_this_index": RAYNER_ANCHOR_MEAN_R,
        "anchor_citation": "Rayner, White, Johnson & Liversedge (2006), interior-scrambled condition",
        "pair_limit": args.limit,
        "channels": {},
    }

    for name in names:
        cfg = CHANNELS[name]
        print("=" * 78)
        print(cfg["label"])
        print("=" * 78)
        pairs = cfg["pairs"](args.limit)
        if not pairs:
            print("  no pairs on disk")
            out["channels"][name] = {"status": "no pairs on disk"}
            continue
        vocab = top_vocabulary(cfg["lang"])
        res = index_over_pairs(pairs, cfg["lang"], vocab, args.limit)
        out["channels"][name] = {"label": cfg["label"], "language": cfg["lang"], **res}
        for k, v in res.items():
            print(f"  {k:<34}: {v}")
        print(f"  most frequent pair                            : "
              f"{pairs[0][0]} -> {pairs[0][1]}  (count {pairs[0][2]})")
        print()

    print(f"  ANCHOR for this index (Phase I, measured): {RAYNER_ANCHOR_MEAN_R}")
    if args.json:
        out_path = args.json if args.json.is_absolute() else (REPO_ROOT / args.json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
