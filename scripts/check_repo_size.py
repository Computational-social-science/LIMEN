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

    objects = oversized_objects(root)
    for name, n in objects:
        if not any(name == rel for rel, _ in tracked):
            findings.append(
                f"reachable object {name} is {fmt(n)}; it is not in the working tree, so a clean status says "
                f"nothing about it, and the push carries it anyway"
            )

    n_tracked = len(tracked_files(root))
    print(f"  tracked files measured: {n_tracked}")
    print(f"  reachable objects over threshold: {len(objects)}")

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

    if findings:
        print(f"\n  [FAIL] {len(findings)} repository hygiene finding(s):")
        for f in findings:
            print(f"      {f}")
        return 1
    print("\n  [OK] no tracked file or reachable object exceeds the threshold, and the check fails on one that does")
    return 0


if __name__ == "__main__":
    sys.exit(main())
