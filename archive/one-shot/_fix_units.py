"""Make every arm word-level at the ingestion boundary of build_arm.

Two defects are repaired by one change, which is why the change belongs at the boundary
rather than in each loader.

**rrc-en is malformed.** Its loader stores `root` as the corrected *word* and `state` as the
whole *sentence*: measured, 368 of 400 sampled items have state/root length ratios of 0.04 to
0.08, so the item asks which word is the root of a 160-character passage. The loader already
computes the word-level correction (`err`), and the state simply was not set to it.

**The arms disagree on the unit.** rrc-en-word is word-level (root median 8 characters); rrc-ru,
rrc-ja, rrc-zh and rrc-zh-gh are sentence-level (medians 46 to 79). Items from arms with
different units are not the same task, so a cross-arm comparison over them would compare units
as much as scripts.

Applying the existing word-level extraction at the boundary fixes both: every arm's state and
root become the differing span of the sentence pair, which is the word the error occurred in.
The extraction is the same `minimal_span`/`word_level_pair` already used for the Chinese arms,
where it recovers the word pair for 97.5% of items.

Items where no short span accounts for the difference cannot become word-level items and are
dropped and counted, rather than being emitted in the old shape.
"""
from __future__ import annotations

import pathlib

P = pathlib.Path("scripts/build_rrc.py")
s = P.read_text(encoding="utf-8")

old = '''    records = [{**r,
                "state": _nfc(r["state"]),
                "root": _nfc(r["root"]),
                "err": _nfc(r.get("err") or "")}
               for r in records]'''
new = '''    records = [{**r,
                "state": _nfc(r["state"]),
                "root": _nfc(r["root"]),
                "err": _nfc(r.get("err") or "")}
               for r in records]

    # Reduce every record to the span that actually differs, so `state` and `root` are the
    # same kind of thing in every arm. Two problems are fixed here at once:
    #
    #   * rrc-en stored the whole sentence as `state` and the corrected word as `root`, an
    #     item asking which word is the root of a 160-character passage -- 92% of that arm;
    #   * the arms disagreed on the unit (word-level for rrc-en-word, sentence-level for the
    #     rest), so cross-arm comparison would have compared units as much as scripts.
    #
    # The extraction is `word_level_pair`, which trims the common prefix and suffix. It is
    # already used for the Chinese arms, where it recovers the word pair for 97.5% of items.
    # A record whose difference no short span accounts for cannot be made word-level and is
    # dropped here and counted, rather than emitted in the old shape.
    reduced, dropped_unit = [], 0
    for r in records:
        pair = word_level_pair(r["state"], r["root"])
        if pair is None:
            # already word-level, or the difference is not a short span
            if len(r["root"]) <= WORD_LEVEL_MAX and len(r["state"]) <= WORD_LEVEL_MAX:
                reduced.append(r)
            else:
                dropped_unit += 1
            continue
        root_word, error_word = pair
        reduced.append({**r, "root": root_word, "state": error_word,
                        "err": r.get("err") or error_word})
    records = reduced
    stats["dropped_unit"] = stats.get("dropped_unit", 0) + dropped_unit'''
if old in s:
    s = s.replace(old, new, 1)
    print("boundary extraction applied")
else:
    print("ANCHOR NOT FOUND -- no change")
    raise SystemExit(1)

# declare the word-level ceiling next to the other module constants
anchor2 = "N_OPTIONS = "
i = s.index(anchor2)
s = s[:i] + ("# The largest span a word-level item may occupy. Beyond this the pair is not a word\n"
             "# correction and the item cannot be made comparable across arms.\n"
             "WORD_LEVEL_MAX = 24\n\n") + s[i:]
P.write_text(s, encoding="utf-8")
print("WORD_LEVEL_MAX declared")
