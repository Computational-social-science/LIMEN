#!/usr/bin/env python
"""o1_auto_indices.py -- the automatic readability measures, recorded alongside the human panel.

WHY THIS IS NOT THE DECISION
    The protocol says items must be human-readable, so a human panel decides. This produces the SECONDARY
    columns Amendment 3 section 5 promises: automatic indices that let a human judgement be related to a
    quantity. A script that guessed a category would be the same failure as a hand-written figure, only
    with a plausible-looking provenance attached - so nothing here produces a category.

WHAT IS MEASURED, AND WHY EACH INDEX IS HERE

  WER            word error rate against the clean text: the fraction of words that are wrong. It is the
                 standard measure and it is dominated by insertions and deletions, which a reader repairs
                 silently - so it moves with lambda even when reading does not get harder.

  word_recoverability
                 THE INDEX THIS PROJECT ACTUALLY WANTS. The fraction of content words that survive
                 within edit distance 1 of their original. A reader recovers a damaged word from its
                 neighbours; when the WORD ITSELF is destroyed, more of the sentence has to be carried by
                 context, and that is the load the programme calls a disturbance. This is the closest
                 proxy available for "how much of this sentence still exists", and it is cheap.

  char_lost      fraction of original characters not present in the perturbed string at all. A blunt
                 measure, included because it is the one nobody can argue about the definition of.

  sentence_recoverability
                 fraction of SENTENCES whose word-recoverability is above a stated cut. A lambda that
                 leaves 90 % of words intact but destroys every sentence is a different design point
                 from one that damages words evenly, and the mean cannot tell them apart.

NO MODEL, NO DOWNLOAD
    Every index here is computed from the item and its corruption. Nothing is loaded, so the numbers are
    reproducible offline and cannot drift with a checkpoint - which matters, because a readability index
    that changes when the language model changes is not a property of the text.

NEGATIVE CONTROL
    Six constructed cases: identical text must score 0 everywhere, a one-letter change must score
    correctly, a word destroyed beyond repair must lower recoverability, and every index must be
    MONOTONE under additional edits. An index that can go UP under more damage is not measuring damage.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "measurement"))
import typo_noise as tn                                   # noqa: E402
sys.path.insert(0, str(ROOT / "scripts"))
import o1_calibration as o1                               # noqa: E402

BANK = ROOT / "measurement/item_bank.jsonl"
WORD = re.compile(r"[A-Za-z']+")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def edit_distance(a, b, cap=4):
    """Levenshtein with an early exit once the distance exceeds `cap`.

    The cap is what makes this affordable over a whole bank: once the distance is known to exceed the
    threshold that matters for recoverability, the exact value is irrelevant and the rest of the row
    cannot change the answer.
    """
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if abs(la - lb) > cap:
        return cap + 1
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        best = cur[0]
        for j in range(1, lb + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1,
                         prev[j - 1] + (0 if a[i - 1] == b[j - 1] else 1))
            if cur[j] < best:
                best = cur[j]
        if best > cap:
            return cap + 1
        prev = cur
    return prev[lb]


def words(s):
    return [w.lower() for w in WORD.findall(s)]


def indices(clean, perturbed):
    wc, wp = words(clean), words(perturbed)
    out = {}

    # word error rate against the clean text (Levenshtein over the word sequences)
    out["wer"] = (edit_distance(wc, wp, cap=8) / len(wc)) if wc else 0.0

    # word recoverability: is each original content word still present, within edit distance 1?
    pool = collections.Counter(wp)
    ok = 0
    for w in wc:
        if pool.get(w, 0) > 0:
            ok += 1
            continue
        hit = False
        for cand, n in pool.items():
            if n > 0 and abs(len(cand) - len(w)) <= 1 and edit_distance(w, cand, cap=1) <= 1:
                hit = True
                break
        if hit:
            ok += 1
        elif pool.get(w, 0):
            ok += 1
    out["word_recoverability"] = (ok / len(wc)) if wc else 1.0

    # characters lost entirely
    have = collections.Counter(perturbed)
    out["char_lost"] = (sum(1 for ch in clean if have.get(ch, 0) <= 0) / len(clean)) if clean else 0.0

    # sentence recoverability: share of sentences whose word recoverability is >= 0.8
    sents = [s for s in SENTENCE_SPLIT.split(clean) if s.strip()]
    good = 0
    for s in sents:
        ws = words(s)
        if not ws:
            good += 1
            continue
        p = collections.Counter(words(perturbed))
        hit = 0
        for w in ws:
            if p.get(w, 0) or any(p.get(c, 0) and abs(len(c) - len(w)) <= 1
                                 and edit_distance(w, c, cap=1) <= 1 for c in p):
                hit += 1
        if hit / len(ws) >= 0.8:
            good += 1
    out["sentence_recoverability"] = (good / len(sents)) if sents else 1.0
    out["n_words"] = len(wc)
    return out


KEYS = ("wer", "word_recoverability", "char_lost", "sentence_recoverability")


def measure_level(lam, seed=0, n=o1.N_PER_LEVEL):
    items = o1.build_sheet(lam, seed, n=n)
    rows = []
    for it in items:
        d = indices(it["clean"], it["perturbed"])
        d["lambda_target"] = lam
        d["realised_edit_rate"] = it["realised_edit_rate"]
        d["item_id"] = it["item_id"]
        rows.append(d)
    return rows


def negative_test():
    CLEAN = ("Please restore write access this afternoon. "
             "The account for our onboarding group is locked.")
    cases = []

    def near(a, b, tol=1e-9):
        return abs(a - b) <= tol

    # The control asserts what a DAMAGE index must do, which is not the same as what it must equal.
    # Two earlier versions of these assertions were wrong and the index was right: one demanded that
    # identical text score word_recoverability 0 (it must score 1 - nothing was lost), and one
    # demanded that "access" -> "acces" lower recoverability (edit distance 1 is inside the stated
    # recovery threshold, so it must NOT). A control that asserts the wrong physics hides a real
    # regression instead of catching one.
    i0 = indices(CLEAN, CLEAN)
    cases.append(("identical text: no damage at all",
                  near(i0["wer"], 0.0) and near(i0["char_lost"], 0.0)
                  and near(i0["word_recoverability"], 1.0)
                  and near(i0["sentence_recoverability"], 1.0)))

    # Distance 1 is INSIDE the recovery threshold by definition, so recoverability must hold and only
    # WER may rise. Asserting both is what pins the threshold at 1 instead of leaving it floating.
    i1 = indices(CLEAN, CLEAN.replace("access", "acces"))
    cases.append(("distance-1 damage raises WER but stays recoverable",
                  i1["wer"] > i0["wer"] and near(i1["word_recoverability"], 1.0)))

    # Distance beyond the threshold must lower it.
    i2 = indices("restore access", "qqqqqqq wwwwwww")
    # WER is a RATIO, so its ceiling is 1.0 - every word wrong is not "more than every word wrong".
    # An earlier assertion demanded wer > 1.0 and therefore could never have passed, on a metric that was
    # behaving exactly as defined.
    cases.append(("damage beyond distance 1 lowers recoverability and maxes WER",
                  i2["word_recoverability"] == 0.0 and near(i2["wer"], 1.0)))

    # monotonicity under ADDITIONAL damage - the property that makes it a damage index
    base = CLEAN
    steps, prev_wer = [], None
    for lam in (0.0, 0.05, 0.12, 0.25):
        txt = ", ".join(tn.typo_noise(base, "probe_item", lam, 0)[0] for _ in range(1))
        w = indices(base, txt)["wer"]
        if prev_wer is not None:
            steps.append(w >= prev_wer - 1e-9)
        prev_wer = w
    cases.append(("WER is monotone non-decreasing in lambda", all(steps)))

    recs = []
    for lam in (0.0, 0.05, 0.12, 0.25):
        recs.append(indices(base, tn.typo_noise(base, "probe_item", lam, 0)[0]))
    mono = all(recs[i + 1]["word_recoverability"] <= recs[i]["word_recoverability"] + 1e-9
               for i in range(len(recs) - 1))
    cases.append(("word recoverability is monotone non-increasing in lambda", mono))

    cases.append(("every index is in range", all(
        0.0 <= i[k] <= 1.0 for i in recs for k in KEYS)))

    ok = 0
    for label, good in cases:
        ok += good
        print(f"  [{'OK' if good else 'MISS'}] {label}")
    print(f"\n  {ok}/{len(cases)} negative controls fired")
    return 0 if ok == len(cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Automatic readability indices for the O1 ladder.")
    ap.add_argument("--negative-test", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--json-out", type=pathlib.Path,
                    default=ROOT / "measurement/o1_auto_indices.json")
    args = ap.parse_args()
    if args.negative_test:
        return negative_test()

    levels = [("lo", o1.LO_GRID), ("mid", o1.MID_GRID)]
    out = {"seed": args.seed, "n_per_level": o1.N_PER_LEVEL, "levels": []}
    print(f"  {'role':<5} {'lam':>6} {'WER':>8} {'wordRec':>9} {'charLost':>9} {'sentRec':>8} {'editRate':>9}")
    for role, grid in levels:
        for lam in grid:
            rows = measure_level(lam, args.seed)
            agg = {k: round(statistics.mean(r[k] for r in rows), 4) for k in KEYS}
            agg["realised_edit_rate"] = round(
                statistics.mean(r["realised_edit_rate"] for r in rows), 4)
            out["levels"].append(dict(role=role, lambda_target=lam, **agg))
            print(f"  {role:<5} {lam:>6} {agg['wer']:>8.4f} {agg['word_recoverability']:>9.4f} "
                  f"{agg['char_lost']:>9.4f} {agg['sentence_recoverability']:>8.4f} "
                  f"{agg['realised_edit_rate']:>9.4f}")

    args.json_out.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"\n  written : {args.json_out.relative_to(ROOT)}")
    print("\n  These are the SECONDARY columns of Amendment 3 section 5. They do not decide the level;")
    print("  the human panel does. Their purpose is to let a human judgement be related to a quantity,")
    print("  and to catch a level at which the text is broken rather than merely hard.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
