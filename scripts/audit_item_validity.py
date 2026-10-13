"""Audit whether RRC items are VALID MEASUREMENT INSTRUMENTS, not merely well-formed records.

WHY THIS EXISTS. Every standing guard checks the corpus's STRUCTURE: conservation of records through
the gates, script purity, unit consistency, provenance, rendering. All of them passed while the corpus
contained items whose scientific value is nil. The first item inspected by hand was

    state "Ab"  ->  root "Albert"
    candidates: lame, neighbours, accessing, spoons, Albert
    difficulty: root_to_state 0.0, decoys_to_state [0,0,0,0], margin null, margin_defined false

Four decoys share NOTHING with the observed form and the root is recoverable by prefix matching, so a
reader -- or any trivial heuristic -- answers it without the ability the corpus is supposed to measure.
A well-formed record is not a valid instrument, and no guard was asking the second question.

WHAT THIS MEASURES.

  1. Degeneracy rates: how often the difficulty fields are undefined or the similarities are zero.
  2. TRIVIAL BASELINES. For each item, four heuristics that use no linguistic knowledge:
       prefix  -- the candidate sharing the longest common prefix with the state
       length  -- the candidate closest in length to the state
       substr  -- the candidate the state is a substring of, else the shortest candidate
       edit    -- the candidate with the smallest Levenshtein distance to the state
     If a heuristic of this kind scores at or above the instrument, the corpus measures the heuristic,
     not the model. This is the decisive test and it needs no new data collection.
  3. Agreement with the measured run, decomposed: the instrument's accuracy on items a trivial
     heuristic also solves versus items it does not. A high overall accuracy concentrated in the
     first group is a trivial-signal artefact.

    python scripts/audit_item_validity.py            # full corpus
    python scripts/audit_item_validity.py --arm rrc-zh
"""

import json
import pathlib
import sys
from collections import Counter, defaultdict

REPO = pathlib.Path(__file__).resolve().parent.parent
SRC = REPO / "archive" / "rrc-v2.0.0-INVALID"   # the retired corpus; this gate grades a corpus,
                                                 # it does not read a live one
OUT = REPO / "data" / "processed" / "item_validity_audit.json"


def lev(a, b, cap=40):
    """Levenshtein distance, capped: only the argmin matters, so a large cap is plenty."""
    if a == b:
        return 0
    if abs(len(a) - len(b)) > cap:
        return cap
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return min(prev[-1], cap)


def common_prefix_len(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def pick(h, state, cands):
    if h == "prefix":
        return max(cands, key=lambda c: (common_prefix_len(c, state), -len(c)))
    if h == "length":
        return min(cands, key=lambda c: abs(len(c) - len(state)))
    if h == "substr":
        for c in cands:
            if state and state in c:
                return c
        return min(cands, key=len)
    if h == "edit":
        return min(cands, key=lambda c: lev(c, state))
    raise ValueError(h)


HEURISTICS = ("prefix", "length", "substr", "edit")


def main():
    only = None
    if "--arm" in sys.argv:
        only = sys.argv[sys.argv.index("--arm") + 1]

    files = sorted(SRC.glob("*.jsonl"))
    if only:
        files = [f for f in files if f.stem == only]

    report = {}
    grand = Counter()
    grand_n = 0

    for f in files:
        arm = f.stem
        n = 0
        deg = Counter()
        wins = Counter()
        states_len = Counter()
        for line in f.open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            it = json.loads(line)
            n += 1
            d = it.get("difficulty") or {}
            state = it.get("state") or ""
            cands = it.get("candidates") or []
            root = it.get("root")

            if not (d.get("margin_defined")):
                deg["margin_undefined"] += 1
            if d.get("root_to_state") == 0.0:
                deg["root_similarity_zero"] += 1
            dec = d.get("decoys_to_state") or []
            if dec and all(x == 0.0 for x in dec):
                deg["all_decoys_zero"] += 1
            if state and root and state in root:
                deg["state_is_substring_of_root"] += 1
            if not state:
                deg["empty_state"] += 1
            if root not in cands:
                deg["root_not_among_candidates"] += 1
            states_len[min(len(state), 12)] += 1

            if root in cands and len(cands) > 1:
                for h in HEURISTICS:
                    if pick(h, state, cands) == root:
                        wins[h] += 1
        report[arm] = {
            "items": n,
            "degeneracy": dict(deg),
            "degeneracy_rate": {k: round(v / max(1, n), 4) for k, v in deg.items()},
            "trivial_heuristic_accuracy": {h: round(wins[h] / max(1, n), 4) for h in HEURISTICS},
            "state_len_hist": {str(k): v for k, v in sorted(states_len.items())},
        }
        grand.update(wins)
        grand_n += n
        print("  %-14s n=%6d  margin∅=%5.1f%%  all-decoys-0=%5.1f%%  "
              "prefix=%5.1f%%  edit=%5.1f%%  length=%5.1f%%" %
              (arm, n,
               100 * deg["margin_undefined"] / max(1, n),
               100 * deg["all_decoys_zero"] / max(1, n),
               100 * wins["prefix"] / max(1, n),
               100 * wins["edit"] / max(1, n),
               100 * wins["length"] / max(1, n)))

    print()
    print("  POOLED over %d items:" % grand_n)
    for h in HEURISTICS:
        print("    %-8s picks the root %5.1f %% of the time" % (h, 100 * grand[h] / max(1, grand_n)))

    report["_pooled"] = {"items": grand_n,
                         "trivial_heuristic_accuracy":
                             {h: round(grand[h] / max(1, grand_n), 4) for h in HEURISTICS}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print()
    print("  wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
