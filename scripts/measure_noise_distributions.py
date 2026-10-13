#!/usr/bin/env python
"""measure_noise_distributions.py -- the empirical noise evidence for Phase II section 6.

WHY THIS SCRIPT EXISTS
    `docs/PHASE_II_NOISE_EVIDENCE.md` states that every one of its figures is reproducible from the observed
    corpora on disk. That claim is only true if a script produces them, so this is the script. It reads the
    three primaries fixed by `docs/PHASE_II_AMENDMENT_1_CHANNELS.md`, measures the three quantities a faithful
    noise process needs - the corruption UNIT, the INVENTORY of attested corruptions, and the FREQUENCY
    SPECTRUM over that inventory - and prints them.

    It measures and reports. It does NOT decide anything: the level-setting, the corpus subset used for
    calibration, the ladder of levels, the item count and the power procedure all belong to section 6's
    argument and are explicitly left open by the evidence document.

WHAT IT DELIBERATELY DOES NOT DO
    It does not "clean" the corpora. A substitution whose surface looks odd is still evidence about what people
    wrote, and dropping it would be exactly the silent-subset failure the global rules warn about. Where a
    structural property would break a naive noise process - Japanese kanji-conversion is NOT injective;
    CSCD-NS rows are aligned so a length change would mean the process had drifted - the script measures it and
    says so rather than repairing it.

RUN
    python scripts/measure_noise_distributions.py
    python scripts/measure_noise_distributions.py --json config/noise_evidence.json
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
# THE PROJECT'S OWN external-data COMES FIRST. Resolving the PARENT's copy
# meant this read a sibling tree that happens to hold the same three datasets;
# LIMEN's own copy is the complete one (21.4 GB vs 1.1 GB). A lookup that works
# because two trees overlap is a lookup that breaks when either moves.
EXTERNAL = next(
    (p for p in (REPO_ROOT / "external-data", REPO_ROOT.parent / "external-data")
     if p.is_dir()),
    REPO_ROOT / "external-data")


def _spectrum(counter: collections.Counter, thresholds=(2, 3, 5, 10, 50, 100, 1000)) -> dict:
    """How the mass is distributed over the inventory. The reason uniform sampling is unfaithful."""
    total = sum(counter.values())
    n = len(counter)
    out: dict[str, object] = {"tokens": total, "distinct": n}
    if not total or not n:
        return out
    by_count = collections.Counter(counter.values())
    curve = {}
    for k in thresholds:
        kept_pairs = sum(v for c, v in by_count.items() if c >= k)
        kept_mass = sum(c * v for c, v in by_count.items() if c >= k)
        curve[str(k)] = {"pairs": kept_pairs, "share_of_pairs": round(kept_pairs / n, 4),
                         "share_of_mass": round(kept_mass / total, 4)}
    out["at_least"] = curve
    return out


def english() -> dict:
    """Birkbeck: `$word` header, then that word's misspellings, one per line."""
    path = EXTERNAL / "birkbeck" / "missp.dat"
    if not path.exists():
        return {"status": f"absent at {path.name}"}
    pairs: collections.Counter = collections.Counter()
    per_word: collections.Counter = collections.Counter()
    cur = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("$"):
            cur = line[1:].strip()
        elif line.strip():
            if cur is not None:
                pairs[(cur, line.strip())] += 1
                per_word[cur] += 1
    return {
        "source": "Birkbeck Spelling Error Corpus (missp.dat)",
        "unit": "word",
        "correct_words": len(per_word),
        "spectrum": _spectrum(pairs),
        "error_forms_per_word_mean": round(sum(per_word.values()) / max(len(per_word), 1), 3),
        "most_error_forms": per_word.most_common(12),
        "interpretation": ("Every pair is distinct, so this corpus records TYPES and not RATES: there is no "
                           "frequency spectrum to sample, and the English level cannot be equated by section "
                           "6 route (b) from this corpus."),
    }


def japanese() -> dict:
    """JWTD kanji-conversion: the corruption is a word, recorded in each record's `diffs`."""
    root = EXTERNAL / "jwtd" / "jwtd"
    if not root.is_dir():
        return {"status": "absent"}
    pairs: collections.Counter = collections.Counter()
    per_sentence: list[int] = []
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
                diffs = obj.get("diffs") or []
                per_sentence.append(len(diffs))
                for d in diffs:
                    pre = (d.get("pre") or "").strip()
                    post = (d.get("post") or "").strip()
                    if pre and post:
                        pairs[(pre, post)] += 1
    by_wrong: dict[str, set] = collections.defaultdict(set)
    for (a, _b) in pairs:
        by_wrong[a].add(_b)
    ambiguous = sum(1 for v in by_wrong.values() if len(v) > 1)
    return {
        "source": "JWTD kanji-conversion, train + test",
        "unit": "kanji word",
        "spectrum": _spectrum(pairs),
        "diffs_per_sentence_mean": round(sum(per_sentence) / max(len(per_sentence), 1), 3),
        "diffs_per_sentence_max": max(per_sentence, default=0),
        "most_common_pairs": [[a, b, c] for (a, b), c in pairs.most_common(20)],
        "non_injective": {
            "wrong_forms_with_multiple_correct": ambiguous,
            "wrong_forms": len(by_wrong),
            "share": round(ambiguous / max(len(by_wrong), 1), 4),
            "why_it_matters": ("a noise process assuming wrong -> correct is a function would mis-attribute "
                              "these; the corpus records pre -> post and both directions are attested data"),
        },
    }


def chinese() -> dict:
    """CSCD-NS: `label \\t origin \\t corrected`, label 1 = error-bearing. Corruption is a character."""
    root = EXTERNAL / "cscd"
    if not root.is_dir():
        return {"status": "absent"}
    sub: collections.Counter = collections.Counter()
    sentences = edits = chars = 0
    length_mismatch = 0
    by_origin: dict[str, set] = collections.defaultdict(set)
    for name in ("train.tsv", "test.tsv"):
        p = root / name
        if not p.exists():
            continue
        with p.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 3 or parts[0] != "1":
                    continue
                sentences += 1
                a, b = parts[1], parts[2]
                if len(a) != len(b):
                    length_mismatch += 1
                    continue
                chars += len(a)
                for x, y in zip(a, b):
                    if x != y:
                        edits += 1
                        sub[(x, y)] += 1
                        by_origin[x].add(y)
    ambiguous = sum(1 for v in by_origin.values() if len(v) > 1)
    return {
        "source": "CSCD-NS labelled sentences, train + test",
        "unit": "character",
        "spectrum": _spectrum(sub),
        "error_sentences": sentences,
        "substitutions": edits,
        "substitutions_per_sentence_mean": round(edits / max(sentences, 1), 3),
        "substitution_rate_over_characters": round(edits / max(chars, 1), 6),
        "length_mismatched_rows": length_mismatch,
        "most_common_pairs": [[a, b, c] for (a, b), c in sub.most_common(18)],
        "non_injective": {"origin_characters_with_multiple_substitutes": ambiguous,
                          "origin_characters": len(by_origin)},
        "interpretation": ("zero length mismatches means the corruption is a pure aligned substitution, so a "
                           "character-level process needs no alignment step and any length change it produced "
                           "would be drift from the data"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--json", type=pathlib.Path, default=None, help="also write the measurement here")
    args = ap.parse_args()

    if not EXTERNAL.is_dir():
        print(f"  external-data root not found as a sibling of this repo ({EXTERNAL.name}/); nothing measured")
        return 1

    result = {"_why": ("Measured by scripts/measure_noise_distributions.py from the observed corpora. The "
                       "levels themselves are NOT set here: section 6 requires the recoverability index and "
                       "this script produces the empirical inputs it operates on."),
              "channels": {}}

    for name, fn in (("english", english), ("japanese", japanese), ("chinese", chinese)):
        m = fn()
        result["channels"][name] = m
        print("=" * 78)
        print(f"{name.upper()}")
        print("=" * 78)
        if "status" in m:
            print(f"  {m['status']}")
            continue
        sp = m["spectrum"]
        print(f"  source      : {m['source']}")
        print(f"  unit        : {m['unit']}")
        print(f"  tokens      : {sp['tokens']:,}    distinct: {sp['distinct']:,}")
        for k, v in (sp.get("at_least") or {}).items():
            print(f"    >= {k:>5} occurrences : {v['pairs']:>7,} pairs  "
                  f"({v['share_of_pairs']*100:5.1f}% of pairs, {v['share_of_mass']*100:5.1f}% of mass)")
        for key in ("correct_words", "error_forms_per_word_mean", "diffs_per_sentence_mean",
                    "diffs_per_sentence_max", "error_sentences", "substitutions",
                    "substitutions_per_sentence_mean", "substitution_rate_over_characters",
                    "length_mismatched_rows"):
            if key in m:
                print(f"  {key:<34}: {m[key]}")
        if m.get("non_injective"):
            print(f"  non-injective               : {json.dumps(m['non_injective'], ensure_ascii=False)[:150]}")
        print()

    if args.json:
        out = args.json if args.json.is_absolute() else (REPO_ROOT / args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        try:
            shown = out.relative_to(REPO_ROOT)
        except ValueError:
            shown = out
        print(f"  wrote {shown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
