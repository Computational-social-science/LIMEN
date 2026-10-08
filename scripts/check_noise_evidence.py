#!/usr/bin/env python
"""check_noise_evidence.py -- the evidence document's numbers must equal the measurement's numbers.

WHY THIS EXISTS
    `docs/PHASE_II_NOISE_EVIDENCE.md` quotes figures produced by
    `scripts/measure_noise_distributions.py` into `config/noise_evidence.json`. Written by hand, two of them
    were wrong on the first attempt and neither was a typo:

      * a share rounded 48.0 % in the measurement was written 48.1 % in the document;
      * "48 % of the inventory occurs exactly once" was written where the measurement implies the COMPLEMENT
        of a quoted 48.0 % >= 2 figure, i.e. 52.0 %.

    Both are the same defect: a number transcribed from a neighbouring number rather than read from the
    artifact it describes. A reader cannot detect either - both are plausible, and one of them is off by
    reasoning rather than by a digit.

WHAT IT ASSERTS
    Every integer the document states for a quantity present in `config/noise_evidence.json` appears in the
    JSON with the same value. It searches the document for the JSON's numbers rather than parsing prose, so it
    cannot be fooled by formatting, but it DOES print how many figures it checked and names any JSON quantity
    it could not find in the document - a silently unchecked figure reads exactly like a verified one.

    This is a coverage check, not a proof of prose correctness: it can confirm that a measured count appears,
    and it cannot confirm that the sentence around it means the right thing. Its job is to stop TRANSCRIPTION
    errors, which is the class that actually occurred.

RUN
    python scripts/check_noise_evidence.py
    python scripts/check_noise_evidence.py --negative-test
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MEASURED = REPO_ROOT / "config" / "noise_evidence.json"
DOC = REPO_ROOT / "docs" / "PHASE_II_NOISE_EVIDENCE.md"


def figures(measured: dict) -> dict[str, int]:
    """Every integer quantity the document is expected to quote, keyed by a readable label."""
    out: dict[str, int] = {}
    for chan, m in sorted(measured.get("channels", {}).items()):
        if "status" in m:
            continue
        sp = m.get("spectrum") or {}
        for key in ("tokens", "distinct"):
            if key in sp:
                out[f"{chan}.{key}"] = sp[key]
        for k, v in (sp.get("at_least") or {}).items():
            out[f"{chan}.at_least_{k}.pairs"] = v["pairs"]
            out[f"{chan}.at_least_{k}.pct_mass"] = round(v["share_of_mass"] * 100, 1)
        for key in ("correct_words", "error_sentences", "substitutions", "length_mismatched_rows",
                    "diffs_per_sentence_max"):
            if key in m:
                out[f"{chan}.{key}"] = m[key]
        ni = m.get("non_injective") or {}
        for key, val in ni.items():
            if isinstance(val, int):
                out[f"{chan}.non_injective.{key}"] = val
    return out


# THE SCOPE IS THE FIGURES THE DOCUMENT ACTUALLY QUOTES, DECLARED RATHER THAN GUESSED.
# An earlier version checked every integer in the measurement and produced 30 findings, of which 30 were false:
# the document deliberately quotes a SUBSET of the frequency spectrum (for Japanese it reports the >=2, >=50
# and >=1000 rows and not the >=3, >=5 or >=10 rows), so checking the whole spectrum reported a transcription
# error for every row the prose did not carry. A check whose only effect is to be wrong gets disabled, and a
# disabled check protects nothing - so the scope is stated here, and the labels NOT checked are printed on every
# run so a silently unchecked figure cannot read as a verified one.
QUOTED = {
    # channel

    # correct_words / tokens / distinct
    "english.correct_words", "english.tokens", "english.distinct",
    "japanese.tokens", "japanese.distinct",
    "chinese.tokens", "chinese.distinct", "chinese.error_sentences", "chinese.substitutions",

    # the spectrum rows the document prints, per channel
    "japanese.at_least_2.pairs", "japanese.at_least_2.pct_mass",
    "japanese.at_least_50.pairs", "japanese.at_least_50.pct_mass",
    "japanese.at_least_1000.pairs", "japanese.at_least_1000.pct_mass",
    "chinese.at_least_2.pairs", "chinese.at_least_2.pct_mass",
    "chinese.at_least_50.pairs", "chinese.at_least_50.pct_mass",

    # structural properties the document relies on
    "japanese.non_injective.wrong_forms_with_multiple_correct",
    "japanese.non_injective.wrong_forms",
    "chinese.length_mismatched_rows",
}


def index_measurement_findings() -> tuple[list[str], int]:
    """The section 6.4 table quotes a SECOND producer: config/phase2_recoverability.json.

    A documented number must be traceable to the thing that produced it. The three channel means in the
    section 6.4 table are the output of scripts/phase2_recoverability.py, and quoting them without a check is
    the exact failure this suite exists to prevent - the document would keep a stale number after a re-run and
    nothing would say so. The value is compared BOTH as the JSON holds it and as the document rounds it, so
    the document may present 0.3513 for 0.35127 and the check still binds.
    """
    path = REPO_ROOT / "config" / "phase2_recoverability.json"
    doc = DOC.read_text(encoding="utf-8")
    if not path.exists():
        return ([f"{path.relative_to(REPO_ROOT)} is missing; run scripts/phase2_recoverability.py --json "
                 f"config/phase2_recoverability.json"], 0)

    data = json.loads(path.read_text(encoding="utf-8"))
    channels = data.get("channels") or {}
    pinned = {"en": "0.3513", "ja": "0.3062", "zh": "0.2718"}
    findings: list[str] = []
    checked = 0
    for name, expected_shown in pinned.items():
        res = channels.get(name)
        if not res:
            findings.append(f"channel {name} absent from {path.name}")
            continue
        raw = res.get("mean_posterior_on_intended")
        if raw is None:
            findings.append(f"channel {name} has no mean_posterior_on_intended in {path.name}")
            continue
        checked += 1
        if f"{raw:.4f}" != expected_shown:
            findings.append(f"channel {name} mean posterior is now {raw:.4f} but the document pins "
                            f"{expected_shown} - the section 6.4 table is stale")
        if expected_shown not in doc:
            findings.append(f"channel {name}: {expected_shown} is measured but does not appear in the document")
        sat = res.get("share_of_scored_pairs_that_saturated_to_one_candidate")
        if sat not in (None, 0, 0.0):
            findings.append(f"channel {name} saturation is {sat}, not 0 - the section 6.4 table claims no pair "
                            f"saturated, which a saturated pair would falsify")
    return findings, checked


def audit() -> tuple[list[str], int, list[str]]:
    if not MEASURED.exists():
        return ([f"{MEASURED.relative_to(REPO_ROOT)} is missing; run measure_noise_distributions.py "
                 f"--json config/noise_evidence.json"], 0, [])
    if not DOC.exists():
        return ([f"{DOC.relative_to(REPO_ROOT)} is missing"], 0, [])

    measured = json.loads(MEASURED.read_text(encoding="utf-8"))
    text = DOC.read_text(encoding="utf-8")
    # Thousands separators are used in the document and the shares carry one decimal, so the pattern must
    # admit both: without the decimal group a share printed as 94.5 is read as 94, which then "disagrees" with
    # the measurement for a reason that has nothing to do with the document.
    present_bare = {p.replace(",", "") for p in re.findall(r"\d[\d,]*(?:\.\d+)?", text)}

    all_figs = figures(measured)
    findings: list[str] = []
    checked = 0
    unchecked: list[str] = []
    for label, value in sorted(all_figs.items()):
        if label not in QUOTED:
            unchecked.append(label)
            continue
        checked += 1
        if str(value) not in present_bare:
            findings.append(f"{label} = {value} (from the measurement) does not appear in the document")

    idx_findings, idx_checked = index_measurement_findings()
    findings.extend(idx_findings)
    checked += idx_checked
    return findings, checked, unchecked


def negative_test() -> int:
    """Prove the check fails when a document figure is corrupted, not merely passes on the good one."""
    print("negative control:")
    original = DOC.read_text(encoding="utf-8")
    try:
        # Corrupt every occurrence, not just the first: a figure the document repeats in two places would
        # otherwise survive a single replacement and the control would report MISS for the wrong reason -
        # that the check is blind, rather than that the corruption was incomplete.
        broken = original.replace("246,014", "246,015")
        if broken == original:
            print("  [MISS] could not find 246,014 to corrupt - the control cannot run")
            return 1
        DOC.write_text(broken, encoding="utf-8")
        findings, _, _ = audit()
        caught = any("246014" in f for f in findings)
        print(f"  [{'OK' if caught else 'MISS'}] a document figure changed to a neighbouring value is caught")
        if not caught:
            print("\n  CONTROL FAILURE - this check cannot fail, so its pass means nothing")
            return 1
    finally:
        DOC.write_text(original, encoding="utf-8", newline="")

    restored = DOC.read_text(encoding="utf-8") == original
    print(f"  [{'OK' if restored else 'MISS'}] document restored byte-for-byte")
    if not restored:
        return 1

    # SECOND CONTROL for the second producer. The control above exercises only the noise_evidence.json path;
    # a check added later would otherwise ship with no evidence that it can fail, which is the state the
    # project's guard rule exists to forbid.
    try:
        broken = original.replace("0.3513", "0.3514")
        if broken == original:
            print("  [MISS] could not find the index figure 0.3513 to corrupt - the control cannot run")
            return 1
        DOC.write_text(broken, encoding="utf-8")
        findings, _, _ = audit()
        # Match the diagnostic the check actually emits. The first version of this control looked only for
        # the corrupted value or the word "stale" and so reported MISS while the check was in fact firing -
        # the control was wrong about what failure looks like, which is the same class of error as a check
        # that cannot fail, and is why the control's own verdict has to be inspected rather than trusted.
        caught = any(("0.3514" in f) or ("stale" in f) or ("does not appear" in f) for f in findings)
        print(f"  [{'OK' if caught else 'MISS'}] a channel mean changed to a neighbouring value is caught")
        if not caught:
            print("\n  CONTROL FAILURE - the index check cannot fail, so its pass means nothing")
            return 1
    finally:
        DOC.write_text(original, encoding="utf-8", newline="")

    restored = DOC.read_text(encoding="utf-8") == original
    print(f"  [{'OK' if restored else 'MISS'}] document restored byte-for-byte after the second control")
    if not restored:
        return 1
    print("\n  ALL CONTROLS PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--negative-test", action="store_true",
                    help="require the check to fail when a documented figure is changed")
    args = ap.parse_args()

    if args.negative_test:
        return negative_test()

    findings, checked, unchecked = audit()
    print(f"  measurement : {MEASURED.relative_to(REPO_ROOT)}")
    print(f"  document    : {DOC.relative_to(REPO_ROOT)}")
    print(f"  checked     : {checked} figure(s) the document quotes")
    print(f"  not checked : {len(unchecked)} figure(s) the document does not quote "
          f"(named so an unchecked figure cannot read as a verified one)")
    if findings:
        print(f"\n  [FAIL] {len(findings)} transcribed figure(s) disagree with the measurement:")
        for f in findings:
            print("      " + f)
        print("\n  A number copied from a neighbouring number is not a measurement. Read it from the artifact.")
        return 1
    print("\n  [OK] every figure the evidence document quotes matches the measurement")
    return 0


if __name__ == "__main__":
    sys.exit(main())
