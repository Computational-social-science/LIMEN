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
# THIS PROJECT'S OWN external-data FIRST. Resolving the parent's copy meant this
# read a sibling tree that is not ours; the project's own copy is the complete one.
EXTERNAL = next(
    (p for p in (REPO_ROOT / "external-data", REPO_ROOT.parent / "external-data")
     if p.is_dir()),
    REPO_ROOT / "external-data")

# THE INDEX'S OWN CONSTANTS ARE IMPORTED, NOT RESTATED. Two implementations of one index that can drift apart
# is two instruments; the anchor is only meaningful if every arm uses the same edit radius and the same floor.
from o1_recoverability import MAX_CANDIDATE_EDITS, ZIPF_FLOOR, RAYNER_ANCHOR_MEAN_R  # noqa: E402

# How many pairs to evaluate. All of them is the honest aim; this bounds the runtime on the Japanese
# inventory, which is the largest. The value used is reported with every result.
DEFAULT_PAIR_LIMIT = 6000

# THE LEVEL GRIDS. Both are OPERATIONAL - they are counts of corrupted units, so neither passes through a
# channel, which is the property section 6.5 showed an index-derived level cannot have.
#
# LEVEL_GRID is the rate at which intended forms are corrupted, for the two channels whose corruption is a
# substitution. It deliberately spans a wide range because the whole point of the sweep is to find where the
# index stops discriminating, rather than to assume where that is.
LEVEL_GRID = (0.02, 0.05, 0.10, 0.20, 0.35, 0.50, 0.75, 1.00)

# SR_LADDER is the published Scramble Ratio scale (section 6.6). It is not swept: the levels ARE these five
# points, and SR = 1 is the Rayner et al. (2006) interior-scrambled condition.
SR_LADDER = (0.0, 0.25, 0.5, 0.75, 1.0)

# THE FROZEN LEVELS. Single source of truth: the pre-registration cites these, no document retypes them.
# Every one is OPERATIONAL - a count of corrupted units - so none passes through a channel. Sections 6.5-6.7
# record the measurements that forced that: an index-derived level inherits the identity of whichever noise
# model is loaded, and swept against the rate the index does not vary monotonically with severity on any
# channel. The English ladder is published; the two rate grids are supplied, with the Chinese one bracketing
# the 0.0196 per-character rate CSCD-NS actually attains.
FROZEN_LEVELS = {
    "en": {
        "levels": [0.0, 0.25, 0.5, 0.75, 1.0],
        "axis": "Scramble Ratio (fraction of interior letters scrambled, first and last fixed)",
        "level_source": "operational; Wang et al. (ACL 2025 Findings). SR = 1 is the Rayner et al. (2006) "
                        "interior-scrambled condition",
        "shape_source": "none estimated - the manipulation is the shape",
        "index_usable": False,
        "index_note": "mean posterior is 0.9995-1.0000 across the ladder and the ablated channel control is "
                      "0.985-1.000, so the channel contributes at most +0.0144 (section 6.5, 6.7)",
    },
    "ja": {
        "levels": [0.02, 0.05, 0.10, 0.20],
        "axis": "fraction of intended forms corrupted",
        "level_source": "supplied by the experimenter; never read off the corpus",
        "shape_source": "JWTD directed pre -> post kanji-conversion spectrum",
        "anchor_note": "no per-token rate is available: JWTD's 45.7 % is a share of TRAIN RECORDS by category, "
                       "a property of corpus assembly rather than a per-token rate; the grid is bracketed by "
                       "the Chinese one and stated as a choice",
    },
    "zh": {
        "levels": [0.005, 0.02, 0.05, 0.10],
        "axis": "fraction of intended forms corrupted",
        "level_source": "supplied by the experimenter; never read off the corpus",
        "shape_source": "CSCD-NS conditional substitution spectrum",
        "anchor_note": "brackets the 0.0196 per-character rate the corpus attains (1.953 % of characters per "
                       "sentence, section 4), with points below and above it",
    },
}


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


def index_over_pairs(pairs, lang: str, vocab: list[str], limit: int, channel: str = "composed",
                     fit_pairs=None, label: str = "", ablate_channel: bool = False) -> dict:
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
    if fit_pairs is not None:
        # THE ANCHOR CASE. The stimuli being scored are not the corpus the channel is fitted on, so there is
        # no leakage to split away: fitting on the whole corpus and scoring every stimulus is the correct
        # design, and it is what makes the anchor row and the three channel rows ONE instrument rather than
        # four numbers produced by two different procedures. Section 6.5 records why that distinction matters.
        fit, test, split_mode = fit_pairs, pairs, "channel fitted on a separate corpus; every stimulus scored"
    else:
        cut = max(1, int(len(pairs) * 0.8))
        fit, test, split_mode = pairs[:cut], pairs[cut:] or pairs[-1:], "pairs split 80/20; channel fitted on the training portion"

    # ── fit the compositional channel: aligned character pairs, weighted by the pair's count
    fitted: _c.Counter = _c.Counter()
    intended_unit_totals: _c.Counter = _c.Counter()
    n_aligned = 0
    for committed, intended, count in fit:
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
        # NEGATIVE CONTROL FOR "IS THE CHANNEL DOING ANY WORK". With the channel ablated to a constant, the
        # posterior is driven by the prior alone; if the index barely moves, the channel term is inert for
        # this stimulus class and the number says nothing about the channel. Section 6.5 uses this to test
        # whether a corpus-fitted substitution channel can price a PERMUTATION, which is a different process
        # from the one it was fitted on.
        if ablate_channel:
            return 0.0
        num = fitted.get((cu, iu), 0) + SMOOTH_K
        den = intended_unit_totals.get(iu, 0) + SMOOTH_K * V
        return math.log(num / den)

    def channel_logprob(committed: str, intended: str) -> float:
        """Compositional: the sum over aligned positions. Length mismatch is not scored here - those pairs
        are excluded at fit time and reported, rather than silently zeroed."""
        if len(committed) != len(intended):
            return float("-inf")
        return sum(unit_logprob(cu, iu) for cu, iu in zip(committed, intended))

    def candidates_of(committed: str, cap: int = 4000, max_positions: int = 1) -> list[str]:
        """Every form a reader could plausibly be reading: substitute, at up to `max_positions` positions, a
        unit the channel maps to that position's committed unit.

        WHY THE DEPTH IS BOUNDED AND REPORTED RATHER THAN LEFT TO RECURSE. The first version let the
        substitution frontier expand transitively — substitute a unit, then substitute the result again, and so
        on. On a two-character Japanese word that turns a handful of single-position alternatives into
        thousands, because each substituted form generates its own alternatives; measured over the injected
        sample the candidate set averaged 2,400 for Japanese and 1,100 for Chinese, which dilutes the posterior
        for a reason that has nothing to do with the corruption being harder.

        One position is also what the channel says. P(committed | intended) is fitted from pairs that differ at
        the position being counted, so a form two substitutions away is not a reading the channel proposed — it
        is a reading of a reading. Bounding at one position keeps the candidate set the channel's own.
        """
        out = {committed}
        positions = range(min(max_positions, len(committed)))
        frontier = [(committed, 0)] if max_positions <= 0 else None
        if max_positions <= 0:
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
        for i in positions:
            for alt in from_unit.get(committed[i], ()):
                if alt == committed[i]:
                    continue
                out.add(committed[:i] + alt + committed[i + 1:])
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
        "channel_fitted_on": f"aligned character pairs from {n_aligned} pairs in the fitting corpus",
        "split_mode": split_mode,
        "channel_units_parameterised": len(fitted),
        "pairs_fitted": len(fit),
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


def anchor_pairs(docs: int = 60) -> list[tuple[str, str, int]]:
    """The Rayner interior-scramble scored as (committed, intended) WORD pairs.

    SAME STIMULI, SAME PERTURBATION as Phase I's `--anchor`: the first 60 rows of the same pack file, the
    same `rayner_scramble`, the same seed. What changes is the estimator that scores them, which is the point
    - see section 6.5. Only words longer than three characters are included, because those are the ones the
    manipulation actually touches; including the untouched short words would dilute the anchor with pairs no
    manipulation was applied to.
    """
    import csv
    import random
    import re
    from o1_recoverability import rayner_scramble

    pack = sorted((REPO_ROOT / "measurement" / "o1_packs").glob("o1_*_lam005_seed0_raterA.csv"))
    if not pack:
        return []
    rows = [ln for ln in pack[0].read_text(encoding="utf-8").splitlines() if not ln.startswith("#")]
    rng = random.Random(0)
    out: list[tuple[str, str, int]] = []
    for r in list(csv.DictReader(rows))[:docs]:
        for w in re.findall(r"\S+", r.get("clean", "")):
            if len(w) > 3:
                out.append((rayner_scramble(w, rng), w, 1))
    return out


def injection_spectrum(pairs) -> dict[str, list[tuple[str, float]]]:
    """The empirical conditional distribution P(committed | intended), straight from the corpus.

    THE SHAPE COMES FROM THE CORPUS AND ONLY THE SHAPE DOES. Section 6.1 records that the Chinese corpus
    carries an error in ~46 % of sentences because that is how it was assembled, so its SHARE of substitutions
    is a property of the annotation plan and not a rate. What is usable is which committed form goes with which
    intended form, and in what proportion relative to one another. This function returns exactly that and never
    normalises it into a per-token probability."""
    by_intended: dict[str, list[tuple[str, float]]] = {}
    for committed, intended, count in pairs:
        c, w = committed.strip(), intended.strip()
        if not c or not w:
            continue
        by_intended.setdefault(w, []).append((c, int(count)))
    for w, opts in by_intended.items():
        tot = sum(n for _, n in opts)
        by_intended[w] = sorted(((c, n / tot) for c, n in opts), key=lambda t: -t[1])
    return by_intended


def inject_at_rate(pairs, lam: float, rng) -> list[tuple[str, str, int]]:
    """Corrupt the intended forms at rate lam, drawing each committed form from the empirical spectrum.

    THIS IS THE NOISE-INJECTION THE LEVEL SEARCH USED TO IMPLICITLY ASSUME, made explicit. lam is supplied by
    the caller - it is never read off the corpus - which is what lets the rate and the shape come from different
    places. For a language whose corruption is a character substitution the pair is a character; for Japanese it
    is a kanji word, and the sample is drawn in the DIRECTION the corpus records, because section 6.3 measured
    that 15.9 % of wrong forms are the wrong form of more than one correct word, so a wrong-to-right lookup
    would mis-attribute them.
    """
    spec = injection_spectrum(pairs)
    out: list[tuple[str, str, int]] = []
    for intended, opts in spec.items():
        if rng.random() < lam:
            r = rng.random()
            acc = 0.0
            chosen = opts[0][0]
            for c, p in opts:
                acc += p
                if r <= acc:
                    chosen = c
                    break
            if chosen != intended:
                out.append((chosen, intended, 1))
    return out


def inject_sr(text_words: list[str], sr: float, rng) -> list[tuple[str, str, int]]:
    """Rayner-style interior scramble at Scramble Ratio sr: first and last letter fixed.

    SR IS OPERATIONAL - it counts characters, so it passes through no channel. That is why the English arm's
    levels come from it (section 6.6) after section 6.5 showed an index-derived level would inherit the
    channel's identity. For sr = 1 every interior character is rearranged, which is the Rayner et al. (2006)
    interior-scrambled condition."""
    out: list[tuple[str, str, int]] = []
    for w in text_words:
        if len(w) < 4:
            continue
        interior = list(w[1:-1])
        k = int(round(sr * len(interior)))
        if k <= 0:
            continue
        idx = list(range(len(interior)))
        rng.shuffle(idx)
        chosen_pos = sorted(idx[:k])
        # permute the chosen positions among themselves
        vals = [interior[i] for i in chosen_pos]
        rng.shuffle(vals)
        for pos, v in zip(chosen_pos, vals):
            interior[pos] = v
        cand = w[0] + "".join(interior) + w[-1]
        if cand != w:
            out.append((cand, w, 1))
    return out


def english_stimulus_words(limit: int = 1200) -> list[str]:
    """Words for the SR ladder: the same pack rows Phase I's anchor used, so the ladder is built on the same
    stimuli the anchor was."""
    import csv
    import re

    pack = sorted((REPO_ROOT / "measurement" / "o1_packs").glob("o1_*_lam005_seed0_raterA.csv"))
    if not pack:
        return []
    rows = [ln for ln in pack[0].read_text(encoding="utf-8").splitlines() if not ln.startswith("#")]
    words: list[str] = []
    for r in list(csv.DictReader(rows))[:60]:
        for w in re.findall(r"[A-Za-z]+", r.get("clean", "")):
            if len(w) > 3:
                words.append(w.lower())
        if len(words) >= limit:
            break
    return words[:limit]


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--channel", choices=sorted(CHANNELS), default=None, help="one channel (default: all)")
    ap.add_argument("--limit", type=int, default=DEFAULT_PAIR_LIMIT,
                    help="pairs to evaluate per channel (reported with every result)")
    ap.add_argument("--anchor", action="store_true",
                    help="also score the Rayner interior-scramble with THIS estimator, so the anchor row and "
                         "the channel rows come from one instrument (section 6.5)")
    ap.add_argument("--ablate-channel", action="store_true",
                    help="NEGATIVE CONTROL: set the channel term to a constant, so the posterior is driven by "
                         "the prior alone. If the index does not move, the channel is inert for these stimuli.")
    ap.add_argument("--levels", action="store_true",
                    help="sweep the corruption rate per channel and report the index curve the operational "
                         "levels are read off (section 6.7)")
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

    if args.levels:
        import random as _random
        print("=" * 78)
        print("LEVEL CURVES - the index as a function of the corruption rate")
        print("=" * 78)
        print("  The channel is fitted on the REAL corpus and the injected sample is scored with it, so what")
        print("  the curve measures is the intrinsic ambiguity of that corpus's own corruption process -")
        print("  which is the quantity a level is read off. The rate is supplied here and never read off the")
        print("  corpus (section 6.1); only the SHAPE is.")
        print()
        levels_out: dict = {}
        for name in names:
            cfg = CHANNELS[name]
            src = cfg["pairs"](None)
            if not src:
                continue
            vocab = top_vocabulary(cfg["lang"])
            curve = []
            print(f"  {cfg['label']}")
            print(f"    {'rate':>6}  {'mean_post':>10}  {'median':>8}  {'MAP':>6}  {'cands':>8}  {'sat':>6}")
            for lam in LEVEL_GRID:
                rng = _random.Random(20261008)
                inj = inject_at_rate(src, lam, rng)
                if len(inj) < 20:
                    print(f"    {lam:>6.2f}  (only {len(inj)} injected pairs - too few to score)")
                    curve.append({"rate": lam, "n_injected": len(inj)})
                    continue
                res = index_over_pairs(inj, cfg["lang"], vocab, args.limit, fit_pairs=src)
                curve.append({
                    "rate": lam, "n_injected": len(inj),
                    "mean_posterior": res.get("mean_posterior_on_intended"),
                    "median_posterior": res.get("median_posterior_on_intended"),
                    "map_share": res.get("share_where_intended_is_MAP"),
                    "mean_candidates": res.get("mean_candidates"),
                    "saturated_share": res.get("share_of_scored_pairs_that_saturated_to_one_candidate"),
                })
                print(f"    {lam:>6.2f}  {res['mean_posterior_on_intended']:>10.4f}  "
                      f"{res['median_posterior_on_intended']:>8.4f}  {res['share_where_intended_is_MAP']:>6.3f}  "
                      f"{res['mean_candidates']:>8.2f}  "
                      f"{res['share_of_scored_pairs_that_saturated_to_one_candidate']:>6.3f}")
            levels_out[name] = {"label": cfg["label"], "curve": curve}
            print()

        # The English arm's levels are NOT read off a curve: section 6.5 shows a substitution channel is inert
        # for a permutation, so any curve here would be reporting the prior. The ladder is the published
        # operational scale instead, and the curve is reported beside it only to document that fact.
        words = english_stimulus_words()
        if words:
            en_src = CHANNELS["en"]["pairs"](None)
            en_vocab = top_vocabulary("en")
            print("  English (alphabetic; the published SR ladder, with the index reported beside it)")
            print(f"    {'SR':>6}  {'mean_post':>10}  {'cands':>8}   note")
            sr_curve = []
            for sr in SR_LADDER:
                rng = _random.Random(20261008)
                inj = inject_sr(words, sr, rng)
                if len(inj) < 20:
                    print(f"    {sr:>6.2f}  (only {len(inj)} injected pairs)")
                    sr_curve.append({"sr": sr, "n_injected": len(inj)})
                    continue
                res = index_over_pairs(inj, "en", en_vocab, args.limit, fit_pairs=en_src)
                abl = index_over_pairs(inj, "en", en_vocab, args.limit, fit_pairs=en_src, ablate_channel=True)
                sr_curve.append({
                    "sr": sr, "n_injected": len(inj),
                    "mean_posterior": res.get("mean_posterior_on_intended"),
                    "mean_candidates": res.get("mean_candidates"),
                    "channel_ablated": abl.get("mean_posterior_on_intended"),
                })
                print(f"    {sr:>6.2f}  {res['mean_posterior_on_intended']:>10.4f}  "
                      f"{res['mean_candidates']:>8.2f}   ablated {abl['mean_posterior_on_intended']:.4f}  "
                      f"(channel contributes {res['mean_posterior_on_intended'] - abl['mean_posterior_on_intended']:+.4f})")
            levels_out["en_sr_ladder"] = {
                "label": "English (alphabetic; published SR ladder)",
                "curve": sr_curve,
                "level_source": "operational - Wang et al. (ACL 2025 Findings) Scramble Ratio; SR=1 is the "
                                "Rayner et al. (2006) interior-scrambled condition",
                "why_not_index_derived": "section 6.5: the substitution channel is inert for a permutation, so "
                                         "the ablated column is shown beside every row",
            }
            print()
        out["level_curves"] = levels_out
        out["FROZEN_LEVELS"] = FROZEN_LEVELS

    if args.anchor:
        print("=" * 78)
        print("Rayner et al. (2006) interior-scrambled, scored by THIS estimator")
        print("=" * 78)
        ap_pairs = anchor_pairs(60)
        if not ap_pairs:
            print("  no stimuli found under measurement/o1_packs")
        else:
            en_fit = CHANNELS["en"]["pairs"](None)      # the whole English source corpus
            en_vocab = top_vocabulary("en")
            res = index_over_pairs(ap_pairs, "en", en_vocab, args.limit, fit_pairs=en_fit,
                                   ablate_channel=args.ablate_channel)
            if not args.ablate_channel:
                abl = index_over_pairs(ap_pairs, "en", en_vocab, args.limit, fit_pairs=en_fit,
                                       ablate_channel=True)
                res["NEGATIVE_CONTROL_channel_ablated_to_a_constant"] = abl["mean_posterior_on_intended"]
                res["channel_term_contribution"] = round(
                    res["mean_posterior_on_intended"] - abl["mean_posterior_on_intended"], 6)
            # The continuity check that a single-instrument design makes possible: the value this project
            # previously reported for this condition, produced by Phase I's own word-level construction.
            res["phase1_value_under_its_own_construction"] = RAYNER_ANCHOR_MEAN_R
            res["stimuli"] = f"{len(ap_pairs)} word pairs from the first 60 pack rows, seed 0"
            out["anchor_rayner_interior_scrambled"] = res
            for k, v in res.items():
                print(f"  {k:<52}: {v}")
        print()

    print(f"  ANCHOR for this index (Phase I construction, measured): {RAYNER_ANCHOR_MEAN_R}")
    if args.json:
        out_path = args.json if args.json.is_absolute() else (REPO_ROOT / args.json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
