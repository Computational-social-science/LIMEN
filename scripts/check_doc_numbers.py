"""check_doc_numbers.py -- a document's quoted numbers must match their source artefact.

WHY THIS EXISTS, AND THE EXACT FAILURE IT WAS WRITTEN FOR
    A session added seven measurement documents over two days. Each new run
    corrected a number in an older one, and the older one was left in place with
    only an inline note -- or, worse, with nothing at all:

      * `docs/PARADIGM_TYPING_AS_REGULATED_PROCESS.md` section 3 quoted the class mix
        under the 2-opcode convention (transposition 8.9%) while section 10 of the
        SAME document quoted one event per error (4.6%). A reader taking the first
        section as current got a number the document itself contradicted 330 lines
        later.
      * The retired keyboard-channel estimate sat in `data/processed/` for two days
        after its replacement shipped, and a live figure read it.
      * A `PROPOSITION_A_MODEL_SIDE.md` scored accuracy and concluded "no effect"
        while the control-law endpoint showed p = 0.002 on the same data.

    None of these announced themselves. The repository's own rule is that a rule
    nothing enforces is not a rule, so this guard enforces the narrow, checkable
    part of it: **for each registered (document, claim, source) triple, recompute
    the number from the source artefact and require the document to carry it.**

    It is deliberately NOT a general "is this document stale" checker -- that is not
    mechanically decidable. It checks the claims that were actually wrong before,
    so the same class of drift cannot recur silently.

WHAT IT DOES NOT DO
    It cannot tell whether a document's PROSE is still the right interpretation, and
    it does not try. It checks numbers against artefacts. A document whose numbers
    all check out can still be superseded in argument, which is why each registered
    document also carries a `superseded_by` field: when that is set, the guard
    requires the named successor to exist and to be newer.
"""
from __future__ import annotations

import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]

#: (document, {claim label: (expected value, source artefact key)})
#: The expected values are RECOMPUTED below from the artefacts, never hardcoded.
CLAIMS = [
    # The class mix, one event per error, from the transposition-aware measurement.
    # PARADIGM section 3 quoted these under a different convention and contradicted
    # its own section 10; the numbers here are the ones the figure uses.
    ("docs/PARADIGM_TYPING_AS_REGULATED_PROCESS.md",
     "figures/data/trans_aware.json",
     "cls",
     {"deletion": ("del_align", 100.0), "insertion": ("ins_align", 100.0),
      "case": ("case", 100.0), "transposition": ("transposition", 50.0),
      "adjacent": ("adjacent", 100.0), "other_sub": ("other_sub", 100.0)}),
]

#: Documents whose numbers are current but whose ARGUMENT is superseded.
#: `superseded_by` must exist and be at least as new, or the guard fails.
SUPERSEDED = {
    "docs/PROPOSITION_A_MODEL_SIDE.md": "docs/PROPOSITION_A_CONTROL_LAW.md",
}

#: Numbers that must NOT appear in a live document, because they were retracted.
#: (document, forbidden literal, why)
RETRACTED = [
    ("docs/PARADIGM_TYPING_AS_REGULATED_PROCESS.md", "| transposition | 25% | 8.9% |",
     "the 2-opcode convention; the document itself uses one event per error in section 10"),
    ("docs/PROPOSITION_A_CONTROL_LAW.md", "the families are not separable",
     "superseded by a licensed bound; see docs/PROPOSITION_A_POWERED.md"),
]

TOL = 0.06   # percentage points; documents round to one decimal


def main() -> int:
    findings = []

    # ---- A: registered claims must match their artefact ----
    for doc, src, key, mapping in CLAIMS:
        dpath, spath = REPO / doc, REPO / src
        if not dpath.exists():
            findings.append(f"A {doc}: registered document is missing")
            continue
        if not spath.exists():
            findings.append(f"A {doc}: source artefact {src} is missing")
            continue
        counts = json.loads(spath.read_text(encoding="utf-8"))[key]
        # A transposition is stored as TWO aligned opcodes (an insert plus a delete
        # of the same character), so converting to one-event-per-error scales it by
        # 0.5 BEFORE the share is taken. My first version scaled after normalising
        # and reported 4.4% where the artefact and the figure both say 4.6% -- the
        # guard caught its own arithmetic, which is the point of recomputing rather
        # than hardcoding.
        scaled = {}
        for label, (src_key, scale) in mapping.items():
            scaled[label] = counts[src_key] * (scale / 100.0)
        total = sum(scaled.values())
        text = dpath.read_text(encoding="utf-8")
        for label in mapping:
            want = 100.0 * scaled[label] / total
            # accept the value at 1 dp, as the documents print it
            for cand in (f"{want:.1f}%", f"{want:.1f} %"):
                if cand in text:
                    break
            else:
                src_key = mapping[label][0]
                findings.append(
                    f"A {doc}: carries no value within {TOL} of {want:.1f}% for "
                    f"'{label}' (recomputed from {src}[{src_key}])")

    # ---- B: a superseded document must name a successor that exists ----
    for doc, succ in SUPERSEDED.items():
        dpath, spath = REPO / doc, REPO / succ
        if not dpath.exists():
            findings.append(f"B {doc}: registered as superseded but is missing")
            continue
        if not spath.exists():
            findings.append(f"B {doc}: names successor {succ}, which does not exist")
            continue
        if spath.stat().st_mtime < dpath.stat().st_mtime:
            findings.append(f"B {doc}: successor {succ} is OLDER than the document it "
                            f"supersedes")
        text = dpath.read_text(encoding="utf-8")
        head = "\n".join(text.splitlines()[:12])
        if succ not in head:
            findings.append(f"B {doc}: the successor {succ} is not named in the first 12 "
                            f"lines, where a reader looks first")

    # ---- C: retracted numbers must not survive in a live document ----
    for doc, literal, why in RETRACTED:
        dpath = REPO / doc
        if not dpath.exists():
            continue
        if literal in dpath.read_text(encoding="utf-8"):
            findings.append(f"C {doc}: still carries the retracted text {literal!r} -- {why}")

    if findings:
        print(f"  [FAIL] {len(findings)} stale-number finding(s):")
        for f in findings:
            print("    " + f)
        return 1
    print(f"  [OK] {len(CLAIMS)} claim set(s) match their artefacts, "
          f"{len(SUPERSEDED)} supersession chain(s) resolve, "
          f"{len(RETRACTED)} retracted number(s) absent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
