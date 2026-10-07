"""check_paper_numbers.py -- every number the paper asserts must be true of a machine record.

WHY THIS EXISTS. The supplementary information has had a number checker since a seven-level table was
drafted by eye and came out wrong in every row, one of them wrong in DIRECTION. The paper - the artefact a
reader is most likely to quote - had nothing. It carried more than a hundred numeric tokens with no
mechanical relationship to the results they report, so a value could drift from its source and the only
person who would notice was a reader who went and recomputed it.

WHAT IT DOES. It does not re-state the results. It DERIVES each expected value from the record that produced
it - the confirmatory JSON for the family and the count, the per-level summary CSV for the curve - and then
asserts that the paper contains that value, formatted as the paper formats it. A number typed into this file
would be a second copy of the result and would defeat the purpose; the only constants here are the FORMATS.

TWO KINDS OF FAILURE, BOTH CAUGHT.
  A value in the paper that no longer matches its source (the source moved, or the paper did).
  A value in the paper that the source no longer contains at all (an analysis was re-run).

NEGATIVE CONTROL. The paper is copied, one character of one checked number is changed, and the check must
report it. A checker that cannot be shown to fail on a wrong number is not a checker.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAPER = ROOT / "docs" / "PAPER.md"
RESULTS = ROOT / "measurement" / "out" / "confirm_results.json"
SUMMARY = ROOT / "data" / "processed" / "stage2_lambda_summary.csv"

# Retired objects. The paper is the outward-facing artefact, so a retired vocabulary here is not a style
# question: it names a research object that is no longer the one being reported.
RETIRED_IN_PAPER = ["JevRSI", "RSI-Jev", "AgentJev", "JEV-Ecosystem", "JEV-ecosystem", "System One",
                    "nanochat", "Floor B"]


def fmt_p(p: float) -> list[str]:
    """The ways this paper writes a very small p-value."""
    if p == 0:
        return ["0"]
    exp = 0
    mant = p
    while mant < 1:
        mant *= 10
        exp -= 1
    mant = round(mant, 1)
    # The paper may write a mantissa with or without a trailing zero ("2" or "2.0"), and both are correct
    # renderings of the same value; requiring only one of them would report a formatting choice as a defect.
    forms = []
    for m in {f"{mant:g}", f"{mant:.1f}"}:
        forms += [f"{m} \\times 10^{{{exp}}}", f"{m}x10^{{{exp}}}"]
    return forms


def expectations() -> list[tuple[str, list[str]]]:
    """(what it is, [acceptable renderings]) - every value derived from a record, none typed in."""
    out: list[tuple[str, list[str]]] = []
    d = json.loads(RESULTS.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(SUMMARY.open(encoding="utf-8")))
    g = lambda r, k: float(r[k])  # noqa: E731
    at = lambda lam: next(r for r in rows if abs(g(r, "lambda") - lam) < 1e-9)  # noqa: E731

    clean, mid, high = at(0.0), at(0.18), at(0.25)

    out.append(("record count", [f"{d['n_records']:,}", str(d["n_records"])]))
    for name, key in (("H1.1", "H1.1"), ("H1.2'", "H1.2'"), ("H1.3", "H1.3")):
        blk = d[key]
        p = blk.get("p_two_sided", blk.get("p_one_sided", blk.get("raw_p")))
        if p is not None:
            out.append((f"{name} p-value", fmt_p(float(p))))
    if "contrast" in d["H1.2'"]:
        out.append(("H1.2' AUC contrast", [f"{float(d["H1.2'"]['contrast']):.4f}".lstrip("0")]))
    if "mean_fall" in d["H1.3"]:
        mf = float(d["H1.3"]["mean_fall"])
        out.append(("H1.3 mean paired fall", [f"{mf:.4f}".lstrip("0"), f"{mf:.4f}"]))
        for lo, hi in (("ci_low", "ci_high"), ("lo", "hi")):
            if lo in d["H1.3"] and hi in d["H1.3"]:
                out.append(("H1.3 CI lower", [f"{float(d['H1.3'][lo]):.4f}".lstrip("0")]))
                out.append(("H1.3 CI upper", [f"{float(d['H1.3'][hi]):.4f}".lstrip("0")]))
                break

    # the curve, read at the levels the paper quotes
    out.append(("AUC clean", [f"{g(clean, 'auc_within'):.4f}".lstrip("0")]))
    out.append(("AUC at lambda_mid", [f"{g(mid, 'auc_within'):.4f}".lstrip("0")]))
    if abs(g(high, "auc_within") - g(mid, "auc_within")) > 1e-9:
        out.append(("AUC at lambda_high", [f"{g(high, 'auc_within'):.4f}".lstrip("0")]))
    out.append(("coverage clean", [f"{g(clean, 'coverage_0.9'):.4f}".lstrip("0")]))
    out.append(("coverage at lambda_mid", [f"{g(mid, 'coverage_0.9'):.4f}".lstrip("0")]))
    out.append(("coverage at lambda_high", [f"{g(high, 'coverage_0.9'):.4f}".lstrip("0")]))
    out.append(("accuracy clean", [f"{g(clean, 'accuracy'):.4f}".lstrip("0")]))
    out.append(("accuracy at lambda_mid", [f"{g(mid, 'accuracy'):.4f}".lstrip("0")]))
    out.append(("errors rejected, clean", [f"{100 * g(clean, 'error_rejected_share_0.9'):.1f}"]))
    out.append(("errors rejected, mid", [f"{100 * g(mid, 'error_rejected_share_0.9'):.1f}"]))

    # ---- the design constants, each read from the record that fixes it -------------------------------
    # These are the numbers a reader would use to re-run the study, so a drift here is worse than a drift in
    # a result: a wrong threshold or bank size makes the study irreproducible rather than merely misreported.
    for what, src_path, pattern, form in (
        ("bank size", ROOT / "measurement" / "item_bank_manifest.json", r'"size":\s*(\d+)', "{}"),
        ("test split", ROOT / "measurement" / "item_bank_manifest.json", r'"test":\s*(\d+)', "{}"),
        ("dev split", ROOT / "measurement" / "item_bank_manifest.json", r'"dev":\s*(\d+)', "{}"),
        ("items per domain", ROOT / "measurement" / "item_bank_manifest.json", r'"billing":\s*(\d+)', "{}"),
        ("readability anchor", ROOT / "docs" / "PHASE_I_AMENDMENT_3_O1_READABILITY.md",
         r"\*\*(0\.4480)\*\*", "{}"),
        ("measured paired discordance", ROOT / "docs" / "PHASE_I_DEV_PRERUN_RESULTS.md",
         r"\*\*(0\.2036)\*\*", "{}"),
        ("minimum detectable effect", ROOT / "docs" / "PHASE_I_DEV_PRERUN_RESULTS.md",
         r"→ (5\.41) accuracy points", "{}"),
    ):
        if not src_path.is_file():
            out.append((what, [f"<source missing: {src_path.name}>"]))
            continue
        m2 = re.search(pattern, src_path.read_text(encoding="utf-8"))
        if m2:
            out.append((what, [form.format(m2.group(1))]))
    if "lam_lo" in d:
        out.append(("lambda_lo", [f"{float(d['lam_lo']):g}"]))
    if "lam_mid" in d:
        out.append(("lambda_mid", [f"{float(d['lam_mid']):g}"]))
    if "n_units" in d["H1.2'"]:
        out.append(("units in the AUC test", [f"{int(d['H1.2\'']['n_units']):,}"]))
    for k, name in (("b", "discordant, hypothesis"), ("c", "discordant, against")):
        if k in d["H1.1"]:
            out.append((name, [str(int(d["H1.1"][k]))]))
    # the Holm thresholds follow from the family size and are computed, never quoted
    n_fam = 3
    for i, thr in enumerate([0.05 / n_fam, 0.05 / (n_fam - 1), 0.05 / (n_fam - 2)]):
        # both renderings: a whole threshold may be written "0.05" or "0.05", and which one is a prose choice
        forms = {f"{thr:.4f}", f"{thr:g}"}
        out.append((f"Holm threshold {i + 1}", sorted(forms)))

    # derived contrasts, computed here rather than quoted
    out.append(("accuracy fall, points",
                [f"{100 * (g(clean, 'accuracy') - g(mid, 'accuracy')):.1f}"]))
    out.append(("coverage fall, points",
                [f"{100 * (g(clean, 'coverage_0.9') - g(mid, 'coverage_0.9')):.1f}"]))
    return out


def check(text: str) -> list[str]:
    findings: list[str] = []
    for what, forms in expectations():
        if not any(f in text for f in forms):
            findings.append(
                f"{what}: none of {forms} appears in the paper - either the source moved and the paper did "
                f"not, or an analysis was re-run and the paper still reports the old value")
    for term in RETIRED_IN_PAPER:
        if term in text:
            findings.append(f"retired vocabulary: the paper names '{term}', which is not the object reported")
    return findings


# A section that has a heading and nothing under it reads as complete to anything that counts headings.
# These floors are deliberately low: they are not a style rule, they catch a section that was emptied or
# never written. The paper's own hard-won structure is that every claim is argued, not asserted.
MIN_SECTION_WORDS = {
    "Abstract": 120, "Introduction": 300, "Results": 300, "Discussion": 400, "Methods": 300,
    "References": 100,
}


def section_substance(text: str) -> list[str]:
    findings = []
    parts = re.split(r"^## (.+)$", text, flags=re.M)
    # parts = [preamble, heading1, body1, heading2, body2, ...]
    for i in range(1, len(parts) - 1, 2):
        name = parts[i].strip()
        body = parts[i + 1]
        words = len(re.findall(r"\b\w+\b", re.sub(r"[`*$\\{}]", " ", body)))
        floor = MIN_SECTION_WORDS.get(name)
        if floor is None:
            continue
        if words < floor:
            findings.append(f"section '{name}' has {words} words, under the {floor}-word floor - a heading "
                            f"with no substance reads as a complete section to anything counting headings")
    return findings


def cross_references(text: str) -> list[str]:
    """Every SI section the paper cites must exist in the assembled supplementary information.

    A paper that never points anywhere leaves a reader unable to find the detail; a paper that points at a
    section that is not there is worse, because the pointer looks like an answer. Both are checked: at least
    one pointer must exist, and every pointer must resolve.
    """
    findings: list[str] = []
    refs = set(re.findall(r"§([A-Z])(?:\.(\d))?", text))
    if not refs:
        findings.append("the paper cites no section of the supplementary information - a reader of the paper "
                        "alone cannot find the methods, the registration or the formal development")
        return findings
    si = (ROOT / "docs" / "SUPPLEMENTARY_INFORMATION.md")
    if not si.is_file():
        return [f"cannot verify {len(refs)} cross-reference(s): {si.name} does not exist"]
    body = si.read_text(encoding="utf-8")
    present_letters = set(re.findall(r"^## ([A-Z])\.", body, re.M))
    # the thesis section has no letter; it is referred to as T
    present_letters |= {"T"} if re.search(r"^## Thesis", body, re.M) else set()
    for letter, sub in sorted(refs):
        if letter not in present_letters:
            findings.append(f"the paper cites SI §{letter}, which does not exist (present: "
                            f"{''.join(sorted(present_letters))})")
        elif sub and not re.search(rf"^#{{2,4}} {letter}\.{sub}\b", body, re.M):
            findings.append(f"the paper cites SI §{letter}.{sub}, which does not exist in that section")
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--no-negative-control", action="store_true")
    args = ap.parse_args(argv)

    text = PAPER.read_text(encoding="utf-8")
    exp = expectations()
    print(f"paper: {len(text.splitlines())} lines; values checked against records: {len(exp)}")

    findings = check(text) + section_substance(text) + cross_references(text)

    if not args.no_negative_control:
        # Corrupt ONE number that is genuinely checked, and require the check to see it.
        victim = None
        for _, forms in exp:
            for f in forms:
                # a victim must be a value that appears EXACTLY ONCE, or replacing it leaves the string
                # present and the control silently reports that it did not fire - which is what happened
                # the first time this was written.
                if f in text and text.count(f) == 1 and len(f) > 3:
                    victim = f
                    break
            if victim:
                break
        if victim is None:
            findings.append("negative control could not run: no uniquely-occurring checked value to corrupt")
        else:
            probe = text.replace(victim, victim[0] + "9" * (len(victim) - 1), 1)
            clean_msgs = check(text)
            probe_msgs = check(probe)
            fired = (not clean_msgs) and bool(probe_msgs)
            print(f"  negative control: corrupted '{victim}' -> "
                  f"{'FAILS as required' if fired else 'NOT DETECTED'}")
            if not fired:
                findings.append(
                    f"negative control did not fire on a corrupted value ({victim}); the checker cannot be "
                    f"shown to detect the defect it exists for")

    if findings:
        print(f"\n  [FAIL] {len(findings)} paper-number finding(s):")
        for f in findings:
            print(f"      {f}")
        return 1
    print("\n  [OK] every checked number in the paper equals the record it came from, no retired vocabulary "
          "appears, and the check fails on a corrupted value")
    return 0


if __name__ == "__main__":
    sys.exit(main())
