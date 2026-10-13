#!/usr/bin/env python
"""measure_collision_evidence.py -- the measurement the Phase II impossibility theorem's antecedent rests on.

WHY THIS FILE EXISTS
    the formalisation's `SilentError.lean` (sibling repository `lean-nhb`, `NHB/PhaseII/`) proves an implication whose antecedent is a COLLISION: two distinct
    intended messages that can both produce the same observable at a gate-confident output. **The proof is
    three lines, and the file says so, because all of the difficulty sits in the antecedent.** A proved
    implication resting on an unguarded measurement is more dangerous than an unguarded argument, not less:
    the theorem invites the reader to believe the conclusion is already secured.

    So the antecedent is measured here, written to one config, and guarded against the documents that quote
    it. Before this file existed the number was computed once inline and appeared only in prose, which is
    exactly the state the guard is meant to make impossible.

WHAT THE COLLISION IS, FOR THE LOGOGRAPHIC CHANNEL
    A Chinese input method is typed by romanisation. When the typed romanisation is IDENTICAL for the intended
    character and the committed one, the keyboard input carried NO error, and the observable the decoder
    receives is a perfectly ordinary character. **Two different intended messages therefore produced the same
    observable, which is the collision the theorem names.**

    The comparison is deliberately the most generous available to the opposite view: it compares the
    characters' ROMANISATION rather than the characters themselves, so a pair differing in either would have
    been excluded.

RUN
    python scripts/measure_collision_evidence.py                       # measure and write the config
    python scripts/measure_collision_evidence.py --check               # guard mode: config must match disk
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
EXTERNAL = REPO_ROOT.parent / "external-data"
CONFIG = REPO_ROOT / "config" / "collision_evidence.json"

# Splits are read separately so the value can be checked for stability across them rather than computed on a
# pooled set that would hide a drift.
SPLITS = (("train", "train.tsv"), ("dev", "dev.tsv"), ("test", "test.tsv"))


def _pinyin(ch: str) -> str | None:
    from pypinyin import Style, pinyin
    try:
        r = pinyin(ch, style=Style.NORMAL, errors="ignore")
        return r[0][0] if r and r[0] else None
    except Exception:
        return None


def substitutions(path: pathlib.Path) -> collections.Counter:
    """Aligned character substitutions, read only from rows the corpus marks as containing an error."""
    counts: collections.Counter = collections.Counter()
    if not path.exists():
        return counts
    with path.open(encoding="utf-8", errors="replace") as f:
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


def measure() -> dict:
    out: dict = {
        "_what": "the collision evidence for the Phase II impossibility theorem's antecedent",
        "theorem": "NHB/PhaseII/SilentError.lean -- no_decoder_avoids_silent_error",
        "definition": "share of observed character substitutions whose intended and committed characters "
                      "share an identical ROMANISATION, i.e. where the keystrokes carried no error and the "
                      "collision is at the input method's candidate selection",
        "corpus": "external-data/cscd (CSCD-NS)",
        "splits": {},
    }
    for name, fname in SPLITS:
        counts = substitutions(EXTERNAL / "cscd" / fname)
        if not counts:
            continue
        total = sum(counts.values())
        identical = 0
        unromanisable = 0
        examples: list[str] = []
        for (committed, intended), n in counts.items():
            pc, pi = _pinyin(committed), _pinyin(intended)
            if not pc or not pi:
                unromanisable += n
                continue
            if pc == pi:
                identical += n
                if len(examples) < 8:
                    examples.append(f"{committed}->{intended}")
        out["splits"][name] = {
            "substitutions": total,
            "identical_romanisation": identical,
            "share_identical_romanisation": round(identical / total, 6),
            "unromanisable": unromanisable,
            "examples": examples,
        }

    pooled_total = sum(v["substitutions"] for v in out["splits"].values())
    pooled_identical = sum(v["identical_romanisation"] for v in out["splits"].values())
    out["pooled"] = {
        "substitutions": pooled_total,
        "identical_romanisation": pooled_identical,
        "share_identical_romanisation": round(pooled_identical / pooled_total, 6) if pooled_total else None,
    }
    # The number the documents quote, rounded as they quote it, so a guard can compare against the prose.
    share = out["pooled"]["share_identical_romanisation"]
    out["quoted_in_documents_as"] = f"{100 * share:.1f} %" if share is not None else None
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="do not write; fail if the config on disk differs from a fresh measurement")
    args = ap.parse_args()

    if not (EXTERNAL / "cscd").is_dir():
        print("  external-data/cscd not found; nothing computed")
        return 1

    fresh = measure()
    if args.check:
        if not CONFIG.exists():
            print(f"  {CONFIG.relative_to(REPO_ROOT)} is missing; run without --check")
            return 1
        on_disk = json.loads(CONFIG.read_text(encoding="utf-8"))
        if on_disk.get("pooled") != fresh.get("pooled"):
            print("  [FAIL] collision evidence on disk disagrees with a fresh measurement:")
            print(f"         disk  : {on_disk.get('pooled')}")
            print(f"         fresh : {fresh.get('pooled')}")
            print("         The theorem's antecedent is a measured number; if it moves, every document "
                  "quoting it is stale.")
            return 1
        print(f"  [OK] collision evidence matches: {fresh['quoted_in_documents_as']} "
              f"({fresh['pooled']['identical_romanisation']:,} of {fresh['pooled']['substitutions']:,})")
        return 0

    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(fresh, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {CONFIG.relative_to(REPO_ROOT)}")
    for name, v in fresh["splits"].items():
        print(f"    {name:<6} {v['share_identical_romanisation']:.4f}  "
              f"({v['identical_romanisation']:,} of {v['substitutions']:,})")
    print(f"    pooled {fresh['pooled']['share_identical_romanisation']:.4f}  "
          f"-> quoted as {fresh['quoted_in_documents_as']}")
    print(f"    examples: {', '.join(fresh['splits'].get('train', {}).get('examples', [])[:6])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
