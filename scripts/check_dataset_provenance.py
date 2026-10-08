#!/usr/bin/env python
"""check_dataset_provenance.py -- the primary evidence for a behavioural claim is OBSERVED.

WHY THIS EXISTS
    Global rule 17: when a study needs what people actually do, it uses a corpus of observed behaviour, never
    a simulation of it. A generated look-alike is evidence about the generator, and a study fed simulated
    errors reports a clean result about a population that does not exist - the data agrees with itself
    perfectly, so internal consistency never reveals it. The tell is not in the data, it is in the provenance.

    The rule is easy to state and easy to lose, because THE SIMULATED DATASET IS USUALLY THE MORE ATTRACTIVE
    ONE. Concretely: on the Chinese channel the two candidates sat in the same repository, and the simulated
    one was 2,000,000+ uniformly formatted samples against 40,000 real ones. A later session with a bigger
    machine and a loading bug would reach for the large one, and nothing would object. A declaration that
    nothing reads is a comment (rule 9), so this reads it.

WHAT IT ASSERTS
    1. every declared channel exposes a `primary` dataset whose `provenance` is `observed`;
    2. every channel's writing system is one of the three categories the taxonomy defines;
    3. every `rejected` entry carries a non-empty reason, and every `simulated` entry that appears anywhere in
       the file is not some channel's primary;
    4. nothing is silently skipped: the channel count and the entries examined are printed on every run, so a
       channel that fails to parse cannot read as a channel that passed.

A NEGATIVE CONTROL is included and is required to fail: `--negative-test` flips one channel's primary to
`simulated` in a temporary copy and asserts this check rejects it.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import textwrap

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATASETS = REPO_ROOT / "config" / "datasets.json"

WRITING_SYSTEMS = {"alphabetic", "syllabic", "logographic"}


def audit(path: pathlib.Path) -> tuple[list[str], dict]:
    findings: list[str] = []
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return ([f"cannot parse {path.name}: {exc}"], {"channels": 0, "entries": 0})

    channels = doc.get("channels") or {}
    if not channels:
        return (["no channels declared - an empty declaration passes vacuously, which is not a pass"],
                {"channels": 0, "entries": 0})

    entries = 0
    for name, chan in sorted(channels.items()):
        cat = chan.get("category")
        if cat not in WRITING_SYSTEMS:
            findings.append(
                f"{name}: category {cat!r} is not one of {sorted(WRITING_SYSTEMS)}. The taxonomy's three "
                f"categories are exhaustive, so a script that mixes them states the category it is assigned "
                f"and puts the mixture in `qualifier` - an enum widened for one entry admits the next one.")

        primary = chan.get("primary")
        if not primary:
            findings.append(f"{name}: no primary dataset declared")
        else:
            entries += 1
            prov = primary.get("provenance")
            if prov != "observed":
                findings.append(
                    f"{name}: primary dataset {primary.get('name')!r} has provenance {prov!r}; the primary "
                    f"evidence for a behavioural claim must be 'observed' (global rule 17)")
            if not primary.get("availability"):
                findings.append(
                    f"{name}: primary dataset {primary.get('name')!r} records no availability - a dataset "
                    f"that exists is not a dataset that can be obtained")

        for rej in chan.get("rejected") or []:
            entries += 1
            if not (rej.get("reason") or "").strip():
                findings.append(
                    f"{name}: rejected entry {rej.get('name')!r} carries no reason - a rejection without a "
                    f"stated reason is indistinguishable from an oversight, and the next session re-opens it")

    # A simulated entry must never be a primary, anywhere - checked structurally rather than by eye.
    for name, chan in sorted(channels.items()):
        for key, val in (("primary", chan.get("primary")),):
            if isinstance(val, dict) and val.get("provenance") == "simulated":
                findings.append(f"{name}.{key} is registered as simulated")

    stats = {"channels": len(channels), "entries": entries}
    return findings, stats


def negative_test() -> int:
    """Prove the check fails on the defect it exists for, not merely passes on the good file."""
    print("negative control:")
    if not DATASETS.exists():
        print("  [MISS] no datasets.json to test against")
        return 1

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="dsprov_"))
    try:
        doc = json.loads(DATASETS.read_text(encoding="utf-8"))
        first = sorted(doc["channels"])[0]
        doc["channels"][first]["primary"]["provenance"] = "simulated"
        probe = tmp / "datasets.json"
        probe.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")

        findings, _ = audit(probe)
        caught = any("must be 'observed'" in f for f in findings)
        print(f"  [{'OK' if caught else 'MISS'}] a primary flipped to 'simulated' is rejected")
        if not caught:
            print("\n  CONTROL FAILURE - this check cannot fail, so its pass means nothing")
            return 1

        # And the other direction: the genuine file must pass.
        good, stats = audit(DATASETS)
        ok_good = not good
        print(f"  [{'OK' if ok_good else 'MISS'}] the genuine declaration passes "
              f"({stats['channels']} channels, {stats['entries']} entries)")
        if not ok_good:
            for f in good:
                print("      " + f)
            return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n  ALL CONTROLS PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "dataset provenance").split("\n")[0])
    ap.add_argument("--negative-test", action="store_true",
                    help="require the check to reject a channel whose primary is simulated")
    args = ap.parse_args()

    if args.negative_test:
        return negative_test()

    if not DATASETS.exists():
        print(f"  [FAIL] {DATASETS.relative_to(REPO_ROOT)} is missing; no dataset is declared")
        return 1

    findings, stats = audit(DATASETS)
    print(f"  declaration : {DATASETS.relative_to(REPO_ROOT)}")
    print(f"  examined    : {stats['channels']} channel(s), {stats['entries']} entr(ies)")

    doc = json.loads(DATASETS.read_text(encoding="utf-8"))
    for name, chan in sorted((doc.get("channels") or {}).items()):
        p = chan.get("primary") or {}
        print(f"  [OK]   {name:<10} {chan.get('category',''):<12} "
              f"{p.get('provenance','?'):<9} {p.get('name','?')}")

    if findings:
        print(f"\n  [FAIL] {len(findings)} finding(s):")
        for f in findings:
            print("      " + f)
        return 1
    print("\n  [OK] every channel's primary evidence is observed human behaviour, "
          "and every rejection states its reason")
    return 0


if __name__ == "__main__":
    sys.exit(main())
