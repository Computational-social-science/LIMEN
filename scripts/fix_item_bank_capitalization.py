#!/usr/bin/env python
"""fix_item_bank_capitalization.py -- capitalise the first letter of item states that start lowercase.

WHY THIS IS A DEFECT AND NOT A STYLE PREFERENCE
    `scripts/o3_leakage_probe.py --template-audit` reported 69 of 932 states beginning with a lowercase
    letter. All 69 begin with the word `the`, all are filled from three templates (`urgency:k01`, `k06`,
    `k10`), and every one of them is in ONE domain - urgency.

    That localisation is what makes it a defect rather than a cosmetic wart. A sentence-initial lowercase
    token is not the same input as its capitalised form: it tokenises differently and it is not a normal
    way to open written English. If the model behaves differently on it, then three urgency templates carry
    a systematic difference from the other three domains, which is exactly the shape of a confound - a
    domain-by-formatting artefact that would be read as a domain effect.

    The correction is semantics-preserving: it changes one character per affected state and nothing else -
    not the gold, not the intent, not the option set, not the criteria.

WHY IT COSTS NOTHING DOWNSTREAM - measured, not assumed
    The stimulus packs draw from the dev split, and **0 of the 60 items in the packs are among the 69**.
    So the packs, the estimated channel, the published anchor and every recoverability number stand
    unchanged. This script verifies that rather than trusting it: `--verify-packs` re-checks the packs
    against the corrected bank and refuses if any packed item's text moved.

WHAT IT REFUSES
    It refuses if a state would change in any position other than index 0, if the corrected text is not
    exactly one character longer-or-same with only the first character differing, or if a state that
    already begins with a capital would be touched at all. A mechanical correction is only safe if it is
    mechanically bounded, so the bounds are asserted rather than described.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BANK = REPO_ROOT / "measurement" / "item_bank.jsonl"
PACKS = REPO_ROOT / "measurement" / "o1_packs"


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--apply", action="store_true", help="write the corrected bank (default: dry run)")
    ap.add_argument("--verify-packs", action="store_true",
                    help="assert that no packed item's clean text changed, then exit")
    args = ap.parse_args()

    rows = [json.loads(l) for l in BANK.read_text(encoding="utf-8").splitlines()]
    packed: dict[str, str] = {}
    for pk in sorted(PACKS.glob("o1_*_lam*_raterA.csv")):
        for r in csv.DictReader([l for l in pk.read_text(encoding="utf-8").splitlines()
                                 if not l.startswith("#")]):
            packed[r["item_id"]] = r["clean"]

    if args.verify_packs:
        by_id = {r["item_id"]: r["state"] for r in rows}
        moved = [i for i, clean in packed.items() if i in by_id and by_id[i] != clean]
        if moved:
            print(f"  [FAIL] {len(moved)} packed item(s) differ from the bank: {moved[:5]}")
            return 1
        print(f"  [OK] all {len(packed)} packed item texts match the bank exactly")
        return 0

    fixed = []
    touched_templates = collections.Counter()
    for r in rows:
        s = r["state"]
        if not s or not s[:1].isascii() or not s[:1].isalpha() or s[:1].isupper():
            continue
        new = s[:1].upper() + s[1:]
        # the bounds: only index 0 may differ, and the result must be the same length
        assert len(new) == len(s), f"{r['item_id']}: length changed"
        assert new[1:] == s[1:], f"{r['item_id']}: a character past index 0 changed"
        assert new[0] != s[0], f"{r['item_id']}: nothing changed"
        fixed.append((r["item_id"], r["template_id"], r["split"]))
        touched_templates[r["template_id"]] += 1

    print(f"  states beginning lowercase: {len(fixed)} of {len(rows)}")
    if not fixed:
        print("  nothing to do")
        return 0
    print(f"  templates touched: {dict(touched_templates)}")
    print(f"  split: {dict(collections.Counter(s for _, _, s in fixed))}")
    overlap = [i for i, _, _ in fixed if i in packed]
    print(f"  packed items affected: {len(overlap)}"
          f"{' -> ' + str(overlap[:5]) if overlap else '  (the instrument chain is untouched)'}")

    if not args.apply:
        print("\n  dry run; re-run with --apply to write")
        return 0

    idx = {r["item_id"]: r for r in rows}
    for iid, _, _ in fixed:
        r = idx[iid]
        r["state"] = r["state"][:1].upper() + r["state"][1:]
    BANK.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                    encoding="utf-8", newline="\n")
    print(f"\n  corrected {len(fixed)} state(s) in {BANK.relative_to(REPO_ROOT)}")
    print("  next: re-run `o3_leakage_probe.py --template-audit` and `--verify-packs`")
    return 0


if __name__ == "__main__":
    sys.exit(main())