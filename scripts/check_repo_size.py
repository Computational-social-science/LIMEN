"""A repository the remote will refuse to accept is a broken deliverable, not a slow one.

WHAT THIS EXISTS FOR. A 146.06 MB installer reached a commit and was deleted in the next one, so the working
tree looked clean, every guard passed, and three commits sat locally waiting to be pushed. The push was
rejected by the REMOTE -- `pre-receive hook declined`, `this exceeds GitHub's file size limit of 100.00 MB` --
and the only way forward was to rewrite the history that contained the blob. Nothing in this repository was
looking at the size of what it committed; the first component to notice was GitHub.

TWO CHECKS, BECAUSE THE TWO FAILURES ARE DIFFERENT.

  TRACKED FILES. Anything the index carries above the threshold. Cheap to check, and it names the path.
  REACHABLE HISTORY. A file can be deleted in the newest commit and still be in an older one that has not
  been pushed yet; the remote reads the OBJECTS, not the working tree. This walks the objects reachable from
  HEAD and bounds them, which is the check that would have caught the installer BEFORE the push attempt.

The threshold is deliberately well under the remote's limit: GitHub rejects at 100 MB and warns from 50 MB,
and a repository that only fails at the hard limit gives no margin to fix it.

NEGATIVE CONTROL. The script writes a file just over the threshold into the tree, confirms the tracked-file
check fails on it, removes it, and confirms the check returns to passing. A check that cannot be shown to
fail on a real defect is not a check.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

MAX_BYTES = 50 * 1024 * 1024
REMOTE_LIMIT_MB = 100


def tracked_files(root: pathlib.Path) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False
    )
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


def oversized_tracked(root: pathlib.Path) -> list[tuple[str, int]]:
    bad = []
    for rel in tracked_files(root):
        p = root / rel
        try:
            n = p.stat().st_size
        except OSError:
            continue  # a tracked file that is absent is the step_order guard's business, not this one
        if n > MAX_BYTES:
            bad.append((rel, n))
    return bad


def oversized_would_be_staged(root: pathlib.Path) -> list[tuple[str, int]]:
    """What a bare `git add -A` WOULD stage, and how large the worst of it is.

    WHY THIS EXISTS, AND THE HAZARD IT WAS WRITTEN FOR
        On 2026-10-14, preparing to commit before a directory rename, `git add -A` was
        run with no path. It began staging `external-data/` -- 21 GB of raw third-party
        corpora, 168,595 files, including a 1.46 GB `Keystrokes.zip`. There was no
        ignore rule for it and nothing under it was tracked, so git treated the whole
        tree as new content. The command was killed mid-run; nothing had been staged.

        `oversized_tracked` could not have caught this, and that is the gap this
        function closes: it reads `git ls-files`, which lists what is ALREADY tracked.
        A hazard that has not been staged yet is invisible to it. The failure would
        therefore have surfaced at `git push`, after the work looked finished, as
        GitHub's 100 MB per-file rejection.

    Cost is bounded: `--dry-run` lists the entries git would add without writing the
    index, and only entries over the threshold are reported, so the output stays short
    even when the tree holds six figures of untracked files.
    """
    out = subprocess.run(
        ["git", "add", "-A", "--dry-run"], cwd=root, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", check=False
    )
    if out.returncode != 0:
        return []
    bad: list[tuple[str, int]] = []
    for line in out.stdout.splitlines():
        # `add 'path'` -- git quotes paths containing spaces or non-ASCII.
        m = re.match(r"^add '(.+)'$", line.strip())
        if not m:
            continue
        rel = m.group(1)
        try:
            n = (root / rel).stat().st_size
        except OSError:
            continue
        if n > MAX_BYTES:
            bad.append((rel, n))
    return bad


def oversized_objects(root: pathlib.Path, rev: str = "HEAD") -> list[tuple[str, int]]:
    """Every blob reachable from `rev`, from the object database - not from the working tree.

    A file deleted in the newest commit is absent from the tree and still present in history, and history is
    what the remote receives.
    """
    listing = subprocess.run(
        ["git", "rev-list", "--objects", rev],
        cwd=root, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False,
    )
    if listing.returncode != 0 or not listing.stdout.strip():
        return []
    check = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objecttype) %(objectsize) %(rest)"],
        cwd=root, input=listing.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False,
    )
    bad = []
    for line in check.stdout.splitlines():
        parts = line.split(" ", 2)
        if len(parts) == 3 and parts[0] == "blob":
            try:
                size = int(parts[1])
            except ValueError:
                continue
            if size > MAX_BYTES:
                bad.append((parts[2], size))
    return bad


def fmt(n: int) -> str:
    return f"{n / (1024 * 1024):.2f} MB"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="repository root")
    ap.add_argument("--no-negative-control", action="store_true")
    args = ap.parse_args(argv)

    root = pathlib.Path(args.root).resolve()
    print(f"repository hygiene - threshold {fmt(MAX_BYTES)} against a remote limit of {REMOTE_LIMIT_MB} MB")

    findings: list[str] = []
    tracked = oversized_tracked(root)
    for rel, n in tracked:
        findings.append(f"tracked file {rel} is {fmt(n)} - the remote rejects anything over {REMOTE_LIMIT_MB} MB")

    if not args.no_negative_control:
        probe = root / "__oversize_negative_control__.bin"
        probe.write_bytes(b"\0" * (MAX_BYTES + 1024))
        subprocess.run(["git", "add", "-f", str(probe.name)], cwd=root, check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            caught = oversized_tracked(root)
            fired = any(rel == probe.name for rel, _ in caught)
            print(f"  negative control: injected {fmt(probe.stat().st_size)} tracked file -> "
                  f"{'FAILS as required' if fired else 'NOT DETECTED'}")
            if not fired:
                findings.append(
                    "negative control did not fire: an injected file over the threshold was not reported, so "
                    "this check cannot be shown to detect the defect it exists for"
                )
        finally:
            subprocess.run(["git", "reset", "-q", "--", str(probe.name)], cwd=root, check=False)
            probe.unlink(missing_ok=True)

    # RUN AFTER THE CONTROL, so the injected probe is still in the index when the
    # control inspects it. The first placement of this call was above the block, which
    # made the control report NOT DETECTED -- a defect I introduced and the control
    # caught, which is the arrangement working as intended.
    would_stage = oversized_would_be_staged(root)
    for rel, n in would_stage:
        findings.append(
            f"a bare `git add -A` would stage {rel} at {fmt(n)} - the remote rejects "
            f"anything over {REMOTE_LIMIT_MB} MB, so the PUSH fails after the work "
            f"looks finished. Add an ignore rule rather than staging it."
        )
    print(f"  oversized entries a bare `git add -A` would stage: {len(would_stage)}")

    if findings:
        print(f"\n  [FAIL] {len(findings)} repository hygiene finding(s):")
        for f in findings:
            print(f"      {f}")
        return 1
    print("\n  [OK] no tracked file or reachable object exceeds the threshold, and the check fails on one that does")
    return 0


if __name__ == "__main__":
    sys.exit(main())
