#!/usr/bin/env python
"""check_handoff_freshness.py -- the handoff note's recorded facts must still be the facts.

WHY THIS EXISTS, AND THE EXACT FAILURE IT WAS WRITTEN FOR
    `docs/RESUME.md` is the first thing a new session reads, and its whole purpose is to be current. On
    2026-10-08 a session opened by reading it and found FOUR stale claims in it:

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

WHAT IS CHECKED, AND WHY THE COMMIT HASH CANNOT BE AN EQUALITY

    Comparing the recorded hash to HEAD would fail on every commit, because committing the updated note
    creates the very commit that moves HEAD. The useful question is not "is it equal" but "is it RECENT" -
    so the check asserts the recorded hash is an ANCESTOR of HEAD within a small distance. That catches a
    note written days and many commits ago while leaving a note written this session alone.

    The protocol version IS checked for equality, because it has no such excuse: `config/anchor.json`
    records it, a bump is a deliberate act, and a note quoting the wrong version sends a reader to the wrong
    revision of the governing document.

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
            print("  [FAIL] no handoff note to test against")
            return 1
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
        print(f"  [FAIL] {RESUME.relative_to(REPO_ROOT)} is missing; a session has nothing to read")
        return 1
    text = RESUME.read_text(encoding="utf-8")
    findings: list[str] = []

    # ── the recorded tip
    m = TIP.search(text)
    if not m:
        findings.append("the note records no commit tip, so a session cannot tell what it was written against")
    else:
        recorded = next(g for g in m.groups() if g)
        probe = subprocess.run(["git", "rev-parse", "--verify", f"{recorded}^{{commit}}"],
                               cwd=str(REPO_ROOT), capture_output=True, text=True)
        if probe.returncode != 0:
            findings.append(f"the recorded tip `{recorded}` is not a commit in this repository")
        else:
            behind = git("rev-list", "--count", f"{recorded}..HEAD")
            if behind.isdigit() and int(behind) > MAX_LAG:
                findings.append(
                    f"the recorded tip `{recorded}` is {behind} commits behind HEAD - the note describes a "
                    f"state this repository left some time ago")

    # ── the protocol version
    if ANCHOR.exists():
        anchor_version = json.loads(ANCHOR.read_text(encoding="utf-8")).get("version")
        stated = [v for v in PROTOCOL_VERSION.findall(text) if v.count(".") == 1]
        if stated and anchor_version not in stated:
            findings.append(
                f"the note quotes protocol v{stated[0]} and the anchor records v{anchor_version}; a reader "
                f"is sent to the wrong revision of the governing document")
        elif not stated:
            findings.append("the note quotes no protocol version, though the protocol is the governing artefact")

    print(f"  handoff: {RESUME.relative_to(REPO_ROOT)}   head: {git('rev-parse', '--short', 'HEAD')}")
    if findings:
        print(f"\n  [FAIL] {len(findings)} stale claim(s) in the handoff:")
        for x in findings:
            print(f"      {x}")
        print("\n  This note is the first thing a new session reads, and a stale note sends it to work that is")
        print("  already done. Update it in the same pass that completes its items.")
        return 1
    print("\n  [OK] the handoff's recorded tip and protocol version agree with the repository")
    return 0


if __name__ == "__main__":
    sys.exit(main())
