"""Estimate a character-substitution channel P(observed | intended) from an observed corpus.

ORDER IS THE POINT. This script runs the planted-truth battery BEFORE it touches a real corpus, and
refuses to report a real estimate until that battery passes. The previous attempt at this project built
its items before any channel existed, which left surface similarity as the only available criterion and
turned the corpus into a string-matching test. The synthesis being followed states the rule directly:
*no exponent before the likelihood*. A likelihood that has never recovered a known answer is not a
likelihood, it is a fit.

The battery, in order:

  1. PLANT.  Build a substitution matrix from keyboard geometry (a known ground truth), generate
     synthetic (intended, observed) word pairs from it, and push them through the SAME extraction and
     estimation path used on real data. Require the planted matrix back inside the reported intervals.
  2. NULL.   Generate pairs from a uniform channel and require the estimator to FAIL to distinguish it
     from uniform. Then generate pairs from the planted channel and require it to distinguish them
     decisively. A test that rejects everything, or nothing, is not a test.
  3. ONLY THEN estimate on a real corpus, and label which layer the source can actually carry.

WHICH LAYER A SOURCE CARRIES is stated, not assumed. A word-level correction corpus mixes physical
(keyboard) and cognitive (spelling) errors and cannot separate them; estimating from one measures the
mixture. Per the synthesis, that conflation is the error to avoid, so the source's layer is reported as
a named limitation rather than left implicit.

    python scripts/channel_estimate.py                 # full battery, then the real corpus
    python scripts/channel_estimate.py --battery-only   # validation only, no real data
"""

import difflib
import json
import math
import pathlib
import random
import sys
from collections import Counter, defaultdict

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed" / "channel_estimate.json"
#  The plant must come back at least this well before any real corpus is read. Set from the
#  requirement, not from a result: the estimator claims to recover a channel, so it must recover
#  one. A run that scored 52.4 % would have passed a verdict that only checked the null test.
RECOVERY_MIN = 0.90

QWERTY_ROWS = ["`1234567890-=", "qwertyuiop[]\\", "asdfghjkl;'", "zxcvbnm,./"]


def qwerty_neighbours():
    """(row, col) neighbours on a QWERTY layout, offsets only -- no linguistic knowledge at all."""
    pos = {}
    for r, row in enumerate(QWERTY_ROWS):
        for c, ch in enumerate(row):
            pos[ch] = (r, c)
    nb = defaultdict(set)
    for ch, (r, c) in pos.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                q = (r + dr, c + dc)
                for other, o in pos.items():
                    if o == q:
                        nb[ch].add(other)
    return pos, nb


def planted_matrix(pos, nb, p_nb=0.60, p_ident=0.30, p_uniform=None):
    """A known ground truth: mostly correct, sometimes an adjacent key, sometimes a far key.

    This is the answer the estimator must recover. It is written down FIRST, before any data exists,
    which is what makes the recovery meaningful.
    """
    alpha = sorted(pos)
    far = 1.0 - p_nb - p_ident
    if p_uniform is None:
        p_uniform = far / max(1, len(alpha) - 1 - max(len(nb[c]) for c in alpha) // 1)
    M = {}
    for i in alpha:
        row = {}
        nbi = nb[i]
        row[i] = p_ident
        share = p_nb / max(1, len(nbi))
        for j in nbi:
            row[j] = share
        others = [j for j in alpha if j != i and j not in nbi]
        if others and far > 0:
            for j in others:
                row[j] = far / len(others)
        s = sum(row.values())
        M[i] = {k: v / s for k, v in row.items()}
    return M


def sample_from(M, word, rng):
    out = []
    for ch in word:
        row = M.get(ch) or M.get(ch.lower())
        if not row:
            out.append(ch)
            continue
        keys = list(row)
        wts = [row[k] for k in keys]
        out.append(rng.choices(keys, weights=wts, k=1)[0])
    return "".join(out)


def align_pairs(intended, observed):
    """Character substitutions from a word pair. Only replace-ops count; indels are a different channel
    (insert/delete) and mixing them here would repeat the conflation this project exists to avoid."""
    sm = difflib.SequenceMatcher(a=intended, b=observed, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                out.append((intended[i1 + k], observed[j1 + k]))
    return out


def counts_from_pairs(pairs):
    c = Counter()
    for intended, observed in pairs:
        for src, dst in align_pairs(intended, observed):
            c[(src, dst)] += 1
    return c


def estimate(counts, alpha, z=1.96):
    """Per-intended MLE with a Wilson interval on each conditional. N is the row total, which is the
    denominator the conditional actually has."""
    rowtot = Counter()
    for (i, _), n in counts.items():
        rowtot[i] += n
    est = {}
    for i in alpha:
        N = rowtot.get(i, 0)
        if N == 0:
            continue
        cells = {}
        for (a, b), n in counts.items():
            if a != i:
                continue
            p = n / N
            den = 1 + z * z / N
            ctr = (p + z * z / (2 * N)) / den
            half = z * math.sqrt(max(0.0, p * (1 - p) / N + z * z / (4 * N * N))) / den
            cells[b] = {"p": p, "n": n, "lo": max(0.0, ctr - half), "hi": min(1.0, ctr + half)}
        est[i] = {"N": N, "cells": cells}
    return est


def llr(counts, model, alpha):
    """Log-likelihood ratio of `model` against the uniform channel, on the observed counts.

    Uniform here means: given an intended character, every OTHER character equally likely -- the channel
    that carries no keyboard information. Both models must assign mass to every cell that occurs.
    """
    ll_m = ll_u = 0.0
    for (i, o), n in counts.items():
        pm = (model.get(i, {}).get("cells", {}).get(o, {}).get("p")
              if "cells" in model.get(i, {}) else None)
        if pm is None:
            pm = model.get(i, {}).get(o)
        if not pm:
            pm = 1e-12
        others = max(1, len(alpha) - 1)
        pu = 1.0 / others if o != i else 1e-9
        ll_m += n * math.log(pm)
        ll_u += n * math.log(pu)
    return ll_m - ll_u, ll_m, ll_u


def recover_check(est, truth, pairs_n):
    """Did the estimator recover the planted matrix, inside its own intervals?"""
    covered = total = 0
    worst = []
    for i, row in truth.items():
        e = est.get(i)
        if not e:
            continue
        for j, p_true in row.items():
            if p_true < 1e-9:
                continue
            got = e["cells"].get(j)
            total += 1
            if got and got["lo"] <= p_true <= got["hi"]:
                covered += 1
            elif got:
                worst.append((abs(got["p"] - p_true), i, j, p_true, got["p"], got["lo"], got["hi"]))
    worst.sort(reverse=True)
    return covered, total, worst[:4]


def read_correct_words(path, limit=None):
    """The CLEAN forms only -- `$`-prefixed lines.

    Base words for the planted fixture must be clean. Feeding this file's bare lines takes the
    MISSPELLINGS as if they were clean input: their character distribution IS the distortion under
    test, so the fixture becomes part of the effect it is meant to bound. A first run did exactly that
    and the plant's recovery fell to 34.9 % while the estimator was working correctly -- a contaminated
    fixture, not a broken estimator.
    """
    words = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            w = line.rstrip("\n").strip()
            if not w.startswith("$"):
                continue
            w = w[1:].strip()
            if w.isalpha() and 2 <= len(w) <= 14:
                words.append(w.lower())
            if limit and len(words) >= limit:
                break
    return words


def read_pairs(path, limit=None):
    """(intended, observed) pairs from a `$correct` / misspelling-lines block structure."""
    pairs = []
    cur = None
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            w = line.rstrip("\n").strip()
            if not w:
                continue
            if w.startswith("$"):
                cur = w[1:].strip()
            elif cur:
                if w.isalpha() and 2 <= len(w) <= 18 and cur.isalpha():
                    pairs.append((cur.lower(), w.lower()))
            if limit and len(pairs) >= limit:
                break
    return pairs


def main():
    battery_only = "--battery-only" in sys.argv
    rng = random.Random(20261011)
    pos, nb = qwerty_neighbours()
    alpha = sorted(pos)
    print("  alphabet: %d characters from the QWERTY layout" % len(alpha))

    # ---- 1. PLANT ---------------------------------------------------------------
    truth = planted_matrix(pos, nb)
    recovery_rate = 0.0
    word_src = pathlib.Path(r"E:/2026-AI4S/external-data/birkbeck/missp.dat")
    base_words = read_correct_words(word_src, limit=4000) if word_src.exists() else []
    if not base_words:
        base_words = ["the", "model", "channel", "keyboard", "estimate", "corpus", "signal"]
    print("  planting: %d base words, sampled through a known QWERTY-derived matrix" % len(base_words))

    for n_pairs in (2000, 20000):
        pairs = [(w, sample_from(truth, w, rng)) for w in rng.choices(base_words, k=n_pairs)]
        cnt = counts_from_pairs(pairs)
        est = estimate(cnt, alpha)
        cov, tot, worst = recover_check(est, truth, n_pairs)
        recovery_rate = cov / max(1, tot)
        print("    planted n=%6d -> substitutions=%6d  truth inside CI: %d/%d = %.1f%%"
              % (n_pairs, sum(cnt.values()), cov, tot, 100 * cov / max(1, tot)))
        for w in worst:
            print("       worst miss: %r->%r true=%.4f est=%.4f CI=[%.4f,%.4f]"
                  % (w[1], w[2], w[3], w[4], w[5], w[6]))

    # ---- 2. NULL ----------------------------------------------------------------
    print()
    print("  null test: the SAME estimator must not distinguish a uniform channel from uniform")
    uni = {}
    others = max(1, len(alpha) - 1)
    for i in alpha:
        uni[i] = {j: (1.0 / others if j != i else 1e-9) for j in alpha}
    pairs_u = [(w, sample_from(uni, w, rng)) for w in rng.choices(base_words, k=20000)]
    cnt_u = counts_from_pairs(pairs_u)
    est_u = estimate(cnt_u, alpha)
    llr_u, m_u, u_u = llr(cnt_u, est_u, alpha)
    pairs_p = [(w, sample_from(truth, w, rng)) for w in rng.choices(base_words, k=20000)]
    cnt_p = counts_from_pairs(pairs_p)
    est_p = estimate(cnt_p, alpha)
    llr_p, m_p, u_p = llr(cnt_p, est_p, alpha)
    print("    uniform channel  -> LLR vs uniform = %12.1f   (per-obs %.3f)  [must be ~0]"
          % (llr_u, llr_u / max(1, sum(cnt_u.values()))))
    print("    planted channel  -> LLR vs uniform = %12.1f   (per-obs %.3f)  [must be large]"
          % (llr_p, llr_p / max(1, sum(cnt_p.values()))))
    verdict = ("PASS" if abs(llr_u / max(1, sum(cnt_u.values()))) < 0.05
               and llr_p / max(1, sum(cnt_p.values())) > 0.05 else "FAIL")
    print("    battery: %s" % verdict)
    #  THE RECOVERY CRITERION BELONGS IN THE VERDICT. A first version of this check reported PASS on
    #  the strength of the null test alone while the plant was recovering 52.4 % of the planted
    #  matrix -- a gate that passed a run its own docstring said must fail. The verdict is computed
    #  from BOTH, and a failing recovery now stops the run before any real corpus is read.
    if verdict == "PASS" and recovery_rate < RECOVERY_MIN:
        print("  [STOP] the plant's matrix was recovered at %.1f %% (below the %.0f %% floor), so the"
              % (100 * recovery_rate, 100 * RECOVERY_MIN))
        print("         extraction path does not invert a known channel. The per-cell estimates are")
        print("         not trustworthy yet and no real corpus will be read.")
        print("         The null test passing does not substitute: distinguishing structure from noise")
        print("         is weaker than recovering the structure's parameters.")
        return 1
    if verdict == "FAIL":
        print("  [STOP] the estimator cannot tell a real channel from none; no real data will be used.")
        return 1

    if battery_only:
        print()
        print("  --battery-only: real corpus not touched.")
        return 0

    # ---- 3. REAL CORPUS ---------------------------------------------------------
    print()
    print("  real corpus. LAYER LABEL IS PART OF THE RESULT: a word-level correction corpus carries")
    print("  physical and cognitive errors TOGETHER and cannot separate them, so this estimates the")
    print("  MIXTURE, not the keyboard channel alone.")
    pairs = read_pairs(word_src)
    print("    source: %s -- %d (intended, observed) pairs" % (word_src.name, len(pairs)))
    if len(pairs) < 200:
        print("  [STOP] too few real pairs to estimate a channel; refusing to report a number.")
        return 1
    cnt = counts_from_pairs(pairs)
    est = estimate(cnt, alpha)
    llr_r, _, _ = llr(cnt, est, alpha)
    print("    substitutions extracted : %d" % sum(cnt.values()))
    print("    LLR vs uniform channel  : %.1f  (per-obs %.4f)" % (llr_r, llr_r / max(1, sum(cnt.values()))))
    top = sorted(((n, a, b) for (a, b), n in cnt.items()), reverse=True)[:12]
    print()
    print("    top %d substitutions  intended -> observed   (count, per-intended share):" % len(top))
    for n, a, b in top:
        p = est.get(a, {}).get("cells", {}).get(b, {})
        print("      %r -> %r   n=%5d   p=%.4f  CI95=[%.4f, %.4f]"
              % (a, b, n, p.get("p", float("nan")), p.get("lo", float("nan")), p.get("hi", float("nan"))))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "source": str(word_src).replace(chr(92), "/"),
        "layer_limitation": ("word-level correction corpus: physical (keyboard) and cognitive "
                             "(spelling) errors are carried TOGETHER and cannot be separated here"),
        "pairs": len(pairs), "substitutions": sum(cnt.values()),
        "llr_vs_uniform": llr_r,
        "estimate": {i: {"N": est[i]["N"],
                         "cells": {k: v for k, v in sorted(est[i]["cells"].items(),
                                                           key=lambda x: -x[1]["n"])[:12]}}
                     for i in est},
    }, indent=2), encoding="utf-8")
    print()
    print("    wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
