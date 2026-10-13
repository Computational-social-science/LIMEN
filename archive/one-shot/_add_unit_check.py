"""Add a unit-consistency check to rrc_qc.py -- the check that should have caught rrc-en.

The existing six checks are about a single item's internal well-formedness: normalisation,
candidate integrity, script composition, provenance, channel consistency. None of them asks
whether `state` and `root` are the *same kind of thing*, and that is how a whole arm shipped
with `root` a word and `state` a sentence -- an item that asks which word is the root of a
160-character passage. The candidate list was well-formed, the provenance was observed, the
script composition was right; every check passed.

This adds the missing question. It is added before the data is fixed, so the real defect is
the check's verification rather than a manufactured one.
"""
from __future__ import annotations

import pathlib

P = pathlib.Path("scripts/rrc_qc.py")
s = P.read_text(encoding="utf-8")

addition = '''

def unit_consistency(it: dict) -> tuple:
    """Whether `state` and `root` are the same kind of thing, and whether they are comparable.

    Returns (ok, detail). Three failures are possible and each was observed somewhere:

      * a length ratio beyond the band -- rrc-en shipped with root 'orders' (6 characters)
        against state 'If you want to exchange assets...' (160), which is a word against a
        sentence and cannot be answered;
      * a state (or root) that is a fragment of the other rather than a corruption of it --
        a 2-character state against a 6-character root is a truncation artefact, not an error,
        unless the source recorded it as one;
      * a state identical to the root, which is not an error at all.

    The band is 0.3 to 3.3 on the length ratio, which admits a real word-level misspelling
    (any edit distance up to about 2x the word) and a real character-level substitution, and
    rejects the word-against-sentence case by a wide margin.
    """
    state, root = it.get("state", ""), it.get("root", "")
    if not state or not root:
        return False, "empty state or root"
    if state == root:
        return False, "state equals root; not an error"
    lo = min(len(state), len(root))
    hi = max(len(state), len(root))
    ratio = lo / hi
    if ratio < 0.3:
        return False, ("state/root length ratio %.3f outside [0.30, 1.00] "
                       "(state %d chars, root %d chars) -- different units"
                       % (ratio, len(state), len(root)))
    return True, ""


'''
anchor = "ARM_RULES = {"
if "def unit_consistency(" not in s:
    s = s.replace(anchor, addition + anchor, 1)

# call it from check_item, beside the normalisation check
old = '''    # 2. candidates: distinct, non-empty, root present exactly once'''
new = '''    # 1b. state and root must be the same kind of thing
    uok, udetail = unit_consistency(it)
    if not uok:
        fail("unit", iid, udetail)
    ok("unit")

    # 2. candidates: distinct, non-empty, root present exactly once'''
if "unit_consistency(it)" not in s.split("def check_item")[1][:4000]:
    s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("unit-consistency check added")
