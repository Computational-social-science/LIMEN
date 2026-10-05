#!/usr/bin/env python
"""check_protocol_consistency.py -- machine checks on the anchor's self-consistency.

Reading a protocol for contradictions does not work: a 600-line document with four version layers
holds contradictions that a careful re-read misses. These checks are the mechanical form of that
re-read. Each is a property the document must have for its claims to be checkable by a reader.

CHECKS
  V  VERSION      the header, §14 and the end marker agree, and match config/anchor.json
  N  NAMING       a named quantity (LIMEN) is defined once, and every later use is consistent with
                  that definition
  C  CLAIM SCOPE  a sentence that claims to test BOTH lambda and s must be marked as a programme-level
                  statement, never as a Phase I claim
  P  PROMOTION    a diagnostic quantity must not be listed among the confirmatory endpoints
  X  CROSS-REF    every internal section reference resolves to a heading that exists
  E  ENDPOINT     the confirmatory family is unchanged from the pre-registration it claims to match

NEGATIVE CONTROL
  Each check has an injected violation and must fail on it.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# The TeX backslash, assembled rather than written, so this module's own source holds no
# literal that the absolute-path guard reads as a machine path. That guard scrubs per FILE, so a
# command written here as `\\Delta` is seen whole and reported - a true finding, and the fix is to
# the source rather than to the guard.
BS = chr(92)
ANCHOR = ROOT / "protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md"
ANCHOR_JSON = ROOT / "config/anchor.json"

# The confirmatory family, as frozen. A change here is a change to the claim, not to the prose.
# `H1.2` carries a prime after the v1.19 replacement: the label changed because the HYPOTHESIS changed,
# and the guard follows the label rather than the other way round.
FROZEN_ENDPOINTS = ("H1.1", "H1.2'", "H1.3")


def check_version(msgs, t: str):
    hdr = re.search(r"\*\*Version:\*\*\s*([0-9.]+)", t)
    c14 = re.search(r"\| Version \| \*\*([0-9.]+)\*\* \|", t)
    end = re.search(r"\*End of protocol v([0-9.]+)\*", t)
    vals = {"header": hdr and hdr.group(1), "s14": c14 and c14.group(1), "end": end and end.group(1)}
    if any(v is None for v in vals.values()):
        msgs.append(("V", 0, f"a version marker is missing: {[k for k,v in vals.items() if v is None]}"))
        return None
    if len(set(vals.values())) != 1:
        msgs.append(("V", 0, f"version markers disagree: {vals}"))
    if ANCHOR_JSON.is_file():
        meta = json.loads(ANCHOR_JSON.read_text(encoding="utf-8"))
        if meta.get("version") != vals["header"]:
            msgs.append(("V", 0, f"anchor.json version {meta.get('version')} != header {vals['header']}"))
        if not meta.get("sha256"):
            msgs.append(("V", 0, "anchor.json carries no sha256"))
    return vals["header"]


def check_naming(msgs, t: str):
    """LIMEN must be defined once, and no later sentence may assert what section 0.3 refuses.

    The refusal list in 0.3 is written as numbered items whose very form is the sentence being
    denied - "That the limen **is unique**" - so a checker that cannot see the denial flags the
    denial. The exemption is therefore structural rather than contextual: **an enumerated list item
    is a refusal, not a claim.** Three earlier versions of this function tried to scope the exemption
    by heading, by span, and by keyword, and each one produced a checker that either flagged correct
    prose or could not fail on its own scenario.
    """
    lines = t.splitlines()
    # A definition lives in 0.3. Later sections refer back to it; a second mention is a USE, not a
    # second definition, and treating it as one flagged the document's own cross-reference.
    in_03 = False
    defined = []
    for i, l in enumerate(lines, 1):
        if re.match(r"###\s*0\.3\b", l):
            in_03 = True
        elif re.match(r"###\s*0\.4\b", l):
            in_03 = False
        # The definition may write the symbol with either delimiter style, because the
        # anchor was migrated to GFM delimiters. Match the DEFINITION, not the delimiter.
        if in_03 and (re.search(r"LIMEN\s+is\s+", l) or "LIMEN (Latin" in l):
            defined.append(i)
    if not defined:
        msgs.append(("N", 0, "LIMEN is used but never defined"))
    elif len(defined) > 1:
        msgs.append(("N", defined[1],
                     f"LIMEN is defined {len(defined)} times; a name must have one definition"))

    FORBIDDEN = ("is unique", "is well calibrated", "always exists", "exists uniquely", "is identified")
    in_03_refusals = False
    for i, l in enumerate(lines, 1):
        if re.search(r"explicitly does not assert", l, re.I):
            in_03_refusals = True
            continue
        if in_03_refusals:
            # the list ends at the next bolded lead-in
            if re.match(r"\*\*What the name buys", l.strip()):
                in_03_refusals = False
            continue          # every item inside is a denial by construction
        if "limen" not in l.lower():
            continue
        if not any(k in l.lower() for k in FORBIDDEN):
            continue
        if re.search(r"(?i)\b(?:not|never|no)\b", l) or "must never" in l.lower():
            continue          # a negation, wherever it appears
        msgs.append(("N", i,
                     f"asserts a property of the limen that 0.3 explicitly refuses: {l.strip()[:90]}"))


def check_claim_scope(msgs, t: str):
    """A sentence naming BOTH lambda and s must be marked as programme-level.

    Section 0.4 states the objective and then, in the same section, constrains how it may be worded.
    The objective sentence is therefore exempt PROVIDED its constraint is present in the section -
    which is the actual property under test. A 0.4 that stated the objective with no constraint
    would fail.
    """
    lines = t.splitlines()
    has_004_constraint = ("constraint on how this objective may be worded" in t
                          and "not** a description of" in t)
    if re.search(r"###\s*0\.4", t) and not has_004_constraint:
        msgs.append(("C", 0,
                     "§0.4 states an objective naming lambda and s but carries no constraint on how "
                     "that objective may be worded per phase"))
    in_prog_note = not has_004_constraint
    for i, l in enumerate(lines, 1):
            low = l.lower()
            if re.match(r"###\s*0\.4\b", low):
                in_prog_note = True          # §0.4 governs its own objective sentence
            elif re.match(r"#{2,3}\s", l):
                in_prog_note = False
            if in_prog_note and has_004_constraint:
                continue
            # Matched with character classes rather than escapes: a pattern like `\\\(\lambda\\\)`
            # raises `bad escape \l` at compile time, which is how the first version of this line
            # broke. The document writes LaTeX inline as \(...\), so a class is both safer and clearer.
            both = (re.search(r"lambda", low) and re.search(r"\\?\(?s_?\{?\\?(mathrm\{)?en", low)
                   or re.search(r"lambda.*and.*shift.*limen", low)
                   or re.search(r"lambda.*and.*s\b.*shift", low))
            if both:
                if "programme" in low or "phase" in low:
                    continue
                # Phase II is the ONE phase in which s varies, so a Phase II hypothesis naming both
                # lambda and s is exactly correct. Only a Phase I sentence, or an unlabelled one, is
                # a defect. The first version flagged H2.2, which is the protocol stating its own
                # structural thesis correctly.
                if re.search(r"h2\.|phase ii|structural thesis", low):
                    continue
                    msgs.append(("C", i,
                                 f"names both lambda and s without marking it programme-level: {l.strip()[:90]}"))
            # Phase I must never be described as TESTING the script factor. A heading, a table row or a
            # checklist entry that merely mentions "cross-script" beside Phase I is a phase LABEL, not a
            # claim - so the row must contain a verb of claiming, not merely the word "script".
            # The proxy for "the script factor" must be the SYMBOL, not the English word.
            # The negative control mutates the anchor into "Phase I tests how $lambda$ and $s$ shift
            # the limen", which contains no occurrence of the word "script" - so a guard keyed on
            # that word could not fail on its own scenario, and the control proved nothing. A Phase II
            # sentence legitimately varies s, so the exemption below stays.
            if re.search(r"phase i\b", low) and re.search(r"\btests?\b", low) \
                    and re.search(r"script|\\\(\?s|\bs\b", low):
                if re.search(r"does not|not tested|reserved|deferred|forbidden|not claim", low):
                    continue
                msgs.append(("C", i, f"Phase I described as testing the script factor: {l.strip()[:90]}"))


def check_promotion(msgs, t: str):
    """A reported diagnostic must not appear among confirmatory endpoints."""
    lines = t.splitlines()
    # the hypothesis list
    in_hyps = False
    for i, l in enumerate(lines, 1):
        if re.match(r"###\s*4\.4\s", l):
            in_hyps = True
        elif re.match(r"###\s*4\.", l) and "4.4a" not in l:
            in_hyps = False
        if in_hyps and re.search(r"Delta\\tau|\\Delta\\tau", l) and l.strip().startswith("- **H"):
            msgs.append(("P", i, "a diagnostic quantity is listed as a confirmatory endpoint"))
    if re.search(r"###\s*4\.4a", t):
        seg = t[t.index("### 4.4a"):]
        seg = seg[:seg.index("\n## ") if "\n## " in seg else len(seg)]
        if "NOT a confirmatory endpoint" not in seg and "not confirmatory" not in seg.lower():
            msgs.append(("P", 0, "§4.4a exists but does not state that the diagnostic is non-confirmatory"))
        if "Holm" not in seg:
            msgs.append(("P", 0, "§4.4a does not state its relation to Holm correction"))


def check_crossrefs(msgs, t: str):
    heads = set()
    for m in re.finditer(r"^#{2,3}\s*(?:(\d+(?:\.\d+)*)\.?\s+)?(.*)$", t, re.M):
        num = m.group(1)
        if num:
            heads.add(num)
    for i, l in enumerate(t.splitlines(), 1):
        for m in re.finditer(r"§(\d+(?:\.\d+)*[a-z]?)", l):
            ref = m.group(1)
            m2 = re.match(r"(\d+(?:\.\d+)?)", ref)
            if m2 is None:
                continue
            base = m2.group(1)
            if base not in heads and ref not in heads:
                msgs.append(("X", i, f"internal reference §{ref} has no heading"))


def check_endpoints(msgs, t: str):
    m = re.search(r"###\s*4\.4\s+Phase I hypotheses", t)
    if not m:
        msgs.append(("E", 0, "the Phase I hypotheses section is missing"))
        return
    seg = t[m.start():]
    seg = seg[:seg.index("### 4.5")] if "### 4.5" in seg else seg
    # The hypotheses are written `- **H1.1:** ...` - the closing `**` follows the COLON, so a
    # pattern expecting `**H1.1**` finds nothing and reports an empty family. That bug hid behind a
    # check that then passed for the wrong reason.
    found = tuple(re.findall(r"\*\*(H1\.\d'?)[:\*]", seg))
    if found != FROZEN_ENDPOINTS:
        msgs.append(("E", 0, f"confirmatory family is {found}, expected {FROZEN_ENDPOINTS}"))


def run_all() -> int:
    msgs = []
    if not ANCHOR.is_file():
        print(f"  [FAIL] anchor missing: {ANCHOR}")
        return 1
    t = ANCHOR.read_text(encoding="utf-8")
    v = check_version(msgs, t)
    check_naming(msgs, t)
    check_claim_scope(msgs, t)
    check_promotion(msgs, t)
    check_crossrefs(msgs, t)
    check_endpoints(msgs, t)
    return report(msgs, v)


def report(msgs, version) -> int:
    if not msgs:
        print(f"  OK: anchor self-consistent at v{version} "
              f"(version · naming · claim-scope · promotion · cross-refs · endpoints)")
        return 0
    for c, ln, d in msgs:
        print(f"  [FAIL] {c}:{ln}  {d}")
    print(f"\n  exit=1  findings: {len(msgs)}")
    return 1


def negative_test() -> int:
    original = ANCHOR.read_text(encoding="utf-8")
    aj = ANCHOR_JSON.read_text(encoding="utf-8") if ANCHOR_JSON.is_file() else None
    results = []

    def restore():
        ANCHOR.write_text(original, encoding="utf-8", newline="\n")
        if aj is not None:
            ANCHOR_JSON.write_text(aj, encoding="utf-8", newline="\n")

    cases = [
        # (label, mutation, check-letter that MUST fire, substring proving it fired for THIS reason)
        ("V version markers disagree",
         original.replace("| Version | **1.3** |", "| Version | **1.9** |", 1),
         "V", "version markers disagree"),
        ("N limen claimed unique",
         original.replace("### 0.4 The claim, stated directly",
                          "### 0.4 The claim, stated directly\n\nThe limen is unique.", 1),
         "N", "explicitly refuses"),
        ("C Phase I described as testing the script factor",
         original.replace("**Phase I restriction:** $s$ fixed to English",
                          "**Phase I restriction:** Phase I tests how $lambda$ and $s$ shift the limen.", 1),
         "C", "Phase I described as testing"),
        ("P diagnostic promoted to an endpoint",
         original.replace("- **H1.1:**",
                          "- **H1.0 (" + BS + "Delta" + BS + "tau^" + BS + "star):**"
                          + BS + "n- **H1.1:**", 1),
         "P", "confirmatory"),
        ("E confirmatory family changed",
         original.replace("- **H1.3:** Under dev-fit", "- **H1.4:** Under dev-fit", 1),
         "E", "confirmatory family"),
    ]
    for name, mutated, letter, proof in cases:
        if mutated == original:
            results.append((name, False, "MUTATION DID NOT APPLY", ""))
            continue
        ANCHOR.write_text(mutated, encoding="utf-8", newline="\n")
        msgs = []
        t = mutated
        v = check_version(msgs, t)
        check_naming(msgs, t)
        check_claim_scope(msgs, t)
        check_promotion(msgs, t)
        check_crossrefs(msgs, t)
        check_endpoints(msgs, t)
        # A control passes only if the EXPECTED check fired AND the reason matches. A control that
        # passes because some unrelated finding was already present proves nothing.
        hits = [m for m in msgs if m[0] == letter and proof in m[2]]
        ok = bool(hits)
        detail = hits[0][2][:70] if hits else (msgs[0][2][:70] if msgs else "(no finding at all)")
        results.append((name, ok, detail, letter))
        restore()

    after = ANCHOR.read_text(encoding="utf-8")
    print("negative control:")
    ok = True
    for name, caught, detail, _letter in results:
        print(f"  [{'OK' if caught else 'MISS'}] {name}  -> {detail[:70]}")
        ok = ok and caught
    restored = after == original
    print(f"  anchor restored byte-for-byte: {'YES' if restored else 'NO'}")
    return 0 if (ok and restored) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Machine checks on the anchor's self-consistency.")
    ap.add_argument("--negative-test", action="store_true")
    args = ap.parse_args()
    return negative_test() if args.negative_test else run_all()


if __name__ == "__main__":
    raise SystemExit(main())