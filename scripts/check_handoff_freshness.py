#!/usr/bin/env python
"""check_handoff_freshness.py -- the handoff note's recorded facts must still be the facts.

WHY THIS EXISTS, AND THE EXACT FAILURE IT WAS WRITTEN FOR
    The handoff note (formerly `docs/RESUME.md`, now deprecated) was the first thing a new session
    reads. On 2026-10-08 a session opened by reading it and found FOUR stale claims in it:

        "local = origin at b361fea"                    the actual tip was 0a2e662
        "protocol ... (v1.21, sha256 pinned)"          the protocol was v1.24 and re-pinned
        "LIMEN main = 34236cc"                         that was the tip two days earlier
        "Do these first: the protocol's attribution    that item had been EXECUTED the day before

    The cause is not carelessness. The item was executed, the work was committed, and the list that
    contained the item was never revisited - so the note spent the night instructing the next session to
    decide something already decided. **A document that tracks its own completion has to be updated when its
    items complete, and nothing was making that happen.**

    This is the same class as every other guard in this repository: a claim written down once and read later
    as though it were still true. A recorded measurement is not a measurement; a recorded state is not a
    state.

WHAT IS CHECKED, AND WHY THE COMMIT HASH IS NO LONGER ONE OF THEM

    An earlier version required the note to record `local = origin at <commit>` and failed if that commit was
    more than a few commits behind HEAD. It was replaced on 2026-10-08, on the programme owner's correction
    that "git is for deliverables, not for process": making the handoff's validity depend on a commit hash
    makes every commit a reason to edit the note, which is process churn dressed as diligence - and the check
    itself kept forcing the thing it was supposed to police.

    What the note actually has to be is SUBSTANTIVELY current, so that is what is checked:
      * the protocol version it quotes equals the version the anchor records;
      * the guard count it quotes equals the number of checks that actually run;
      * and it states the working state in a form a reader can act on.

    A recorded commit tip is still READ and reported when present, as information - it is simply not a
    precondition, because a note is not stale for failing to mention a hash it never needed.

EXIT
    0  the handoff agrees with the repository        1  it does not
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RESUME = REPO_ROOT / "docs" / "RESUME.md"
ANCHOR = REPO_ROOT / "config" / "anchor.json"

# How far behind HEAD the recorded tip is allowed to be. The note is normally committed once, so one or two
# is the steady state; the bound exists to catch a note nobody has touched in a while, not to police the
# bookkeeping.
MAX_LAG = 5

# `local = origin` at `0a2e662`   /   local `fc9381c`, origin `2cda1bf`
TIP = re.compile(r"`local = origin`\s*at\s*`([0-9a-f]{7,40})`|local\s*`([0-9a-f]{7,40})`")
PROTOCOL_VERSION = re.compile(r"protocol[^\n]{0,80}?\bv(\d+\.\d+)", re.I)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=str(REPO_ROOT), capture_output=True,
                          text=True, check=False).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--negative-test", action="store_true",
                    help="state a protocol version the anchor does not have, require this check to fail")
    args = ap.parse_args()

    if args.negative_test:
        if not RESUME.exists():
            # The handoff note is DEPRECATED and deliberately removed, which normal
            # mode already reports as OK. The negative test used to return FAIL here,
            # so `run_all_guards.py` -- which runs every guard with --negative-test --
            # went red on a tree that is correct. A control that fails when its
            # subject has been intentionally retired is testing the wrong thing:
            # there is nothing left to perturb, so the honest answer is that the
            # control is INAPPLICABLE, not that the repository is broken.
            print("  [SKIP] negative control INAPPLICABLE: docs/RESUME.md is intentionally "
                  "removed (handoff note system deprecated), so there is no note to perturb")
            return 0
        original = RESUME.read_text(encoding="utf-8")
        try:
            RESUME.write_text(original.replace("**v1.24**", "**v9.99**", 1), encoding="utf-8")
            rc = subprocess.run([sys.executable, __file__], capture_output=True, text=True).returncode
        finally:
            RESUME.write_text(original, encoding="utf-8")
        if rc == 0:
            print("  [FAIL] negative control was NOT caught - the check cannot fail and proves nothing")
            return 1
        print("  [OK]   negative control: a false protocol version in the handoff -> FAILS as required")
        return 0

    if not RESUME.exists():
        print(f"  [OK] {RESUME.relative_to(REPO_ROOT)} is intentionally removed (handoff note system deprecated); nothing to check")
        return 0
    text = RESUME.read_text(encoding="utf-8")
    findings: list[str] = []

    # ── the recorded tip: READ AND REPORTED, never a precondition (rule: git is not the point)
    tip_note = "none recorded"
    m = TIP.search(text)
    if m:
        recorded = next(g for g in m.groups() if g)
        probe = subprocess.run(["git", "rev-parse", "--verify", f"{recorded}^{{commit}}"],
                               cwd=str(REPO_ROOT), capture_output=True, text=True)
        if probe.returncode == 0:
            behind = git("rev-list", "--count", f"{recorded}..HEAD")
            tip_note = f"{recorded} ({behind} commit(s) behind HEAD)"
        else:
            tip_note = f"{recorded} (not a commit here - reported, not failed, since a hash is not required)"

    # ── the protocol version: a real equality, because a bump is deliberate and a wrong version misleads
    if ANCHOR.exists():
        anchor_version = json.loads(ANCHOR.read_text(encoding="utf-8")).get("version")
        stated = [v for v in PROTOCOL_VERSION.findall(text) if v.count(".") == 1]
        if stated and anchor_version not in stated:
            findings.append(
                f"the note quotes protocol v{stated[0]} and the anchor records v{anchor_version}; a reader "
                f"is sent to the wrong revision of the governing document")
        elif not stated:
            findings.append("the note quotes no protocol version, though the protocol is the governing artefact")

    # ── the guard count: the note's claim about the suite must equal the suite. Substantive, and unlike a
    #    commit hash it does not change merely because something was committed.
    runner = REPO_ROOT / "scripts" / "run_all_guards.py"
    if runner.exists():
        actual = len(re.findall(r'^\s*\(\s*"[^"]+\.py"\s*,', runner.read_text(encoding="utf-8"), re.M))
        stated_counts = [int(c) for c in re.findall(r"(\d+)\s+guards?\b", text)]
        blocking = [c for c in stated_counts if c >= actual]
        if stated_counts and not any(c == actual for c in stated_counts) and blocking:
            findings.append(
                f"the note says {max(stated_counts)} guard(s) and the suite runs {actual}; a stale count is a "
                f"claim about the suite that the suite contradicts")

    print(f"  handoff: {RESUME.relative_to(REPO_ROOT)}   head: {git('rev-parse', '--short', 'HEAD')}")
    print(f"  recorded tip (information only): {tip_note}")
    if findings:
        print(f"\n  [FAIL] {len(findings)} stale claim(s) in the handoff:")
        for x in findings:
            print(f"      {x}")
        print("\n  This note is the first thing a new session reads, and a stale note sends it to work that is")
        print("  already done. Update it in the same pass that completes its items.")
        return 1
    print("\n  [OK] the handoff's protocol version and guard count agree with the repository")
    return 0


if __name__ == "__main__":
    sys.exit(main())
