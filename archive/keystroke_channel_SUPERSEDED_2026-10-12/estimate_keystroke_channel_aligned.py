"""Estimate the keyboard channel from 136M Keystrokes with a proper alignment.

The previous version compared target and produced text position by position, restricted to
equal-length pairs. That is wrong in a way that inflates one class silently: a single
uncorrected deletion shifts every later character, and each shifted character is then recorded
as a substitution. Measured that way, 72.5% of the errors were unclassified "other" -- a
figure that cannot be interpreted, because part of it is alignment artefact rather than error.

This version aligns the two strings first, using difflib's opcodes, and classifies the edit
operations the alignment actually reports:

  * `replace` of equal-length blocks -> substitutions, each classified as shift-state (same
    letter, different case), key-adjacency (the two keys are adjacent on US QWERTY), or other;
  * `insert` -> an inserted character;
  * `delete` -> a deleted character.

Insertions and deletions are counted as their own classes rather than smeared over the rest of
the string, which is what makes the composition interpretable.

The published figure for comparison remains 1.167% uncorrected errors per keystroke
(Dhakal, Feit, Kristensson & Oulasvirta, CHI 2018, SD 1.43%).
"""
from __future__ import annotations

import collections
import difflib
import json
import pathlib
import random
import sys
import zipfile

ZIP = pathlib.Path("external-data/136Mkeystrokes/Keystrokes.zip")
OUT = pathlib.Path("data/processed/keystroke_channel.json")

# US QWERTY rows, used only to decide whether a substitution is between adjacent keys.
QWERTY_ROWS = ["1234567890-=", "qwertyuiop[]", "asdfghjkl;'", "zxcvbnm,./"]
ADJ = set()
for _row in QWERTY_ROWS:
    for _a, _b in zip(_row, _row[1:]):
        ADJ.add(frozenset((_a, _b)))
    # the half-key stagger: a key is also adjacent to the two below/above it
for _i in range(len(QWERTY_ROWS) - 1):
    _up, _dn = QWERTY_ROWS[_i], QWERTY_ROWS[_i + 1]
    for _c, _ch in enumerate(_up):
        for _nc in (_c, _c + 1):
            if _nc < len(_dn):
                ADJ.add(frozenset((_ch.lower(), _dn[_nc].lower())))


def classify(want: str, got: str) -> str:
    if want != got and want.lower() == got.lower():
        return "shift_state"
    if frozenset((want.lower(), got.lower())) in ADJ:
        return "key_adjacency"
    return "other_substitution"


def main(n_files: int = 1500) -> int:
    if not ZIP.exists():
        raise SystemExit("corpus not found: %s" % ZIP)

    with zipfile.ZipFile(ZIP) as Z:
        names = [n for n in Z.namelist() if n.endswith("_keystrokes.txt")]
        random.seed(20261016)
        sample = random.sample(names, min(n_files, len(names)))

        sections = exact = 0
        chars_target = 0
        cls = collections.Counter()
        subst = collections.Counter()
        per_char = collections.defaultdict(lambda: [0, 0])
        users = set()

        for nm in sample:
            rows = Z.read(nm).decode("utf-8", "replace").splitlines()
            if len(rows) < 2:
                continue
            hdr = rows[0].split("\t")
            need = ("TEST_SECTION_ID", "SENTENCE", "USER_INPUT", "PARTICIPANT_ID")
            if any(k not in hdr for k in need):
                continue
            i = {k: hdr.index(k) for k in need}
            n = len(hdr)
            seen = {}
            for L in rows[1:]:
                p = L.split("\t")
                if len(p) == n:
                    seen[p[i["TEST_SECTION_ID"]]] = (p[i["SENTENCE"]], p[i["USER_INPUT"]])
            if not seen:
                continue
            users.add(rows[1].split("\t")[i["PARTICIPANT_ID"]])

            for target, produced in seen.values():
                sections += 1
                chars_target += len(target)
                if produced == target:
                    exact += 1
                    continue
                sm = difflib.SequenceMatcher(a=target, b=produced, autojunk=False)
                for op, a0, a1, b0, b1 in sm.get_opcodes():
                    if op == "equal":
                        continue
                    if op == "replace":
                        block_a = target[a0:a1]
                        block_b = produced[b0:b1]
                        m = min(len(block_a), len(block_b))
                        for k in range(m):
                            w, g = block_a[k], block_b[k]
                            per_char[w][1] += 1
                            if w != g:
                                c = classify(w, g)
                                cls[c] += 1
                                subst[(w, g)] += 1
                                per_char[w][0] += 1
                        cls["delete"] += len(block_a) - m
                        cls["insert"] += len(block_b) - m
                    elif op == "delete":
                        cls["delete"] += a1 - a0
                    elif op == "insert":
                        cls["insert"] += b1 - b0

    total_edits = sum(cls.values())
    subs_total = sum(cls[k] for k in ("shift_state", "key_adjacency", "other_substitution"))
    rate = subs_total / max(chars_target, 1)

    print("136M Keystrokes -- keyboard channel, alignment-based")
    print("  participant files           : %d" % len(sample))
    print("  distinct participants       : %d" % len(users))
    print("  test sections               : %d" % sections)
    print("  identical target/produced   : %d (%.2f%%)"
          % (exact, 100 * exact / max(sections, 1)))
    print("  target characters           : %d" % chars_target)
    print()
    print("  edit operations from the alignment, by class:")
    for k in ("shift_state", "key_adjacency", "other_substitution", "insert", "delete"):
        print("    %-20s %7d   %6.2f%% of edits   rate %.4f%% of target chars"
              % (k, cls[k], 100 * cls[k] / max(total_edits, 1), 100 * cls[k] / max(chars_target, 1)))
    print("    %-20s %7d" % ("TOTAL edits", total_edits))
    print()
    print("  substitution error rate = %.4f%% of target characters" % (100 * rate))
    print("    published per-keystroke = 1.1670%%  (SD 1.43%%)   ratio %.2fx"
          % (rate / 0.01167))
    print()
    print("  substitution matrix, most frequent intended -> observed:")
    for (w, g), c in subst.most_common(12):
        print("    %-4r -> %-4r  n=%-6d p=%.4f" % (w, g, c, c / max(subs_total, 1)))

    result = {
        "source": "136M Keystrokes (Dhakal et al., CHI 2018)",
        "method": "difflib alignment of SENTENCE vs USER_INPUT; all sections",
        "files": len(sample), "participants": len(users), "sections": sections,
        "identical": exact, "target_chars": chars_target,
        "edits": {k: cls[k] for k in
                  ("shift_state", "key_adjacency", "other_substitution", "insert", "delete")},
        "edits_total": total_edits,
        "substitutions_total": subs_total,
        "substitution_rate": rate,
        "published_rate": 0.01167,
        "substitution_fraction_of_edits": (subs_total / total_edits) if total_edits else 0.0,
        "top_substitutions": [[w, g, c] for (w, g), c in subst.most_common(40)],
        "per_intended_char": {k: {"errors": v[0], "n": v[1]} for k, v in per_char.items()},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print()
    print("  wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
