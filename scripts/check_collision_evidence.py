#!/usr/bin/env python
"""check_collision_evidence.py -- the guard on the impossibility theorem's antecedent.

WHY THIS GUARD IS HERE
    the formalisation's `SilentError.lean` (sibling repository `lean-nhb`, `NHB/PhaseII/`) proves, in three lines, that a channel collision at a gate-confident output
    makes a silent error unavoidable for every decoder. The Lean file states that all of the difficulty is in
    the antecedent. **A proved implication resting on an unguarded measurement is more dangerous than an
    unguarded argument, because the theorem invites the reader to think the conclusion is already secured.**

    The antecedent is a measured share: the fraction of observed Chinese character substitutions whose typed
    ROMANISATION is identical, so the keystrokes carried no error and two distinct intended messages produced
    the same observable. This guard keeps that number honest in two directions -- that the config matches a
    fresh measurement, and that the documents quote the config rather than a remembered variant.

WHAT IT FOUND WHEN IT WAS FIRST RUN, RECORDED BECAUSE IT IS THE POINT
    The documents said **81.5 %**. The config, computed over all three splits rather than the training split
    alone, says **81.4 %** (12,334 of 15,143 pooled: 0.8143). The earlier figure came from the training split
    with four unromanisable pairs excluded from the denominator. Both are defensible and they are NOT the same
    number, and nothing said which was meant. The guard now requires the documents to quote the pooled value
    with its scope, so a reader cannot inherit an unlabelled variant.

RUN
    python scripts/check_collision_evidence.py
    python scripts/check_collision_evidence.py --negative-test
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = REPO_ROOT / "config" / "collision_evidence.json"

# Documents that rest on the antecedent and must therefore quote it correctly.
DOCUMENTS = (
    REPO_ROOT / "docs" / "MAIN_PROPOSITION_AND_HYPOTHESES.md",
    REPO_ROOT / "docs" / "THEORETICAL_ANCHOR.md",
    REPO_ROOT / "docs" / "UNAVOIDABILITY_PREMISE.md",
    REPO_ROOT / "docs" / "RELATED_WORK_AND_GAPS.md",
)


def audit() -> list[str]:
    findings: list[str] = []
    if not CONFIG.exists():
        return [f"{CONFIG.relative_to(REPO_ROOT)} is missing; run scripts/measure_collision_evidence.py"]

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    quoted = cfg.get("quoted_in_documents_as")
    share = cfg.get("pooled", {}).get("share_identical_romanisation")
    if quoted is None or share is None:
        return [f"{CONFIG.relative_to(REPO_ROOT)} has no pooled measurement"]

    # The retired variant: the training-split-only figure the documents used to carry. Named explicitly so the
    # guard fails on it rather than silently accepting a number that is close enough to look right.
    stale = "81.5"
    for doc in DOCUMENTS:
        if not doc.exists():
            findings.append(f"{doc.relative_to(REPO_ROOT)} is missing")
            continue
        text = doc.read_text(encoding="utf-8")
        if stale in text and quoted not in text:
            findings.append(
                f"{doc.relative_to(REPO_ROOT)} quotes {stale} % (the training-split variant) and not "
                f"{quoted} (the pooled value) -- the theorem's antecedent must be quoted with its scope")
    return findings


def measure_fresh() -> dict:
    """Recompute rather than trust, because a guard that reads the file it is guarding proves nothing."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import measure_collision_evidence as m
    return m.measure()


def negative_test() -> int:
    """Prove the guard fails on the exact defect it exists for."""
    print("negative control:")
    target = REPO_ROOT / "docs" / "UNAVOIDABILITY_PREMISE.md"
    if not target.exists():
        print("  [MISS] cannot run: the document is absent")
        return 1
    original = target.read_text(encoding="utf-8")
    try:
        # Reinstate the retired training-split variant and remove the pooled one, which is precisely the state
        # the guard was written after finding.
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        pooled = cfg["quoted_in_documents_as"]
        broken = original.replace(pooled, "81.5 %")
        if broken == original:
            print(f"  [MISS] could not find {pooled} to corrupt -- the control cannot run")
            return 1
        target.write_text(broken, encoding="utf-8")
        caught = any("81.5" in f for f in audit())
        print(f"  [{'OK' if caught else 'MISS'}] a document quoting the retired variant is caught")
        if not caught:
            print("\n  CONTROL FAILURE - this check cannot fail, so its pass means nothing")
            return 1
    finally:
        target.write_text(original, encoding="utf-8", newline="")

    restored = target.read_text(encoding="utf-8") == original
    print(f"  [{'OK' if restored else 'MISS'}] document restored byte-for-byte")
    return 0 if restored else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--negative-test", action="store_true")
    args = ap.parse_args()

    if args.negative_test:
        return negative_test()

    fresh = measure_fresh()
    on_disk = json.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {}
    findings: list[str] = []
    if on_disk.get("pooled") != fresh.get("pooled"):
        findings.append(f"config disagrees with a fresh measurement: disk {on_disk.get('pooled')} vs "
                        f"fresh {fresh.get('pooled')}")
    findings.extend(audit())

    print(f"  config      : {CONFIG.relative_to(REPO_ROOT)}")
    print(f"  antecedent  : {fresh.get('quoted_in_documents_as')} pooled, "
          f"({fresh.get('pooled', {}).get('identical_romanisation'):,} of "
          f"{fresh.get('pooled', {}).get('substitutions'):,})")
    for name, v in (fresh.get("splits") or {}).items():
        print(f"    {name:<6} {v['share_identical_romanisation']:.4f}")
    print()
    if findings:
        print(f"  [FAIL] {len(findings)} finding(s):")
        for f in findings:
            print(f"      {f}")
        return 1
    print(f"  [OK] the theorem's antecedent is measured, stable across splits, and quoted with its scope")
    return 0


if __name__ == "__main__":
    sys.exit(main())
