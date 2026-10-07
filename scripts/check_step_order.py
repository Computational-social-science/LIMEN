#!/usr/bin/env python
"""check_step_order.py -- catch the one mistake this session made three times, mechanically.

WHY THIS EXISTS
    Three separate times in a single session, two steps were run in the wrong order and the result LOOKED
    FINE:

      1. a commit that included its own transient commit-message file, because the file was written before
         `git add -A`;
      2. the guard suite run in the SAME shell invocation as the commit it was supposed to gate, so a commit
         could land while the suite was red;
      3. a derived table refreshed BETWEEN a version bump and its re-pin, leaving protocol content that had
         changed while its version field and recorded digest had not.

    Only the third is invisible to every other guard in this repository, because every other guard checks
    content or consistency at a point in time - none checks whether the point in time was coherent.

WHAT IT CHECKS
  A  no TRANSIENT artefact is tracked. A commit-message temp file, an editor backup, a merge leftover or a
     bytecode cache in git means a step ran before its cleanup, and it will be cloned by everyone.
  B  the protocol's ACTUAL digest and byte count match `config/anchor.json`. If they differ, the protocol was
     edited and not re-pinned - the exact state in which two different contents can share one version number.
  C  the version recorded in the anchor matches the version in the protocol. A bump that did not reach the
     anchor, or a re-pin that did not carry the bump, is the same defect from the other side.

EXIT
  0  coherent      1  at least one ordering finding
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROTOCOL = REPO_ROOT / "protocol" / "NHB_Orthographic_Channels_JEV_Research_Protocol.md"
ANCHOR = REPO_ROOT / "config" / "anchor.json"

# Names that never belong in history. Matched against the basename of each tracked path.
TRANSIENT = (
    re.compile(r"^COMMIT_MSG.*$", re.I),
    re.compile(r"^.*\.(tmp|orig|rej|swp|swo)$", re.I),
    re.compile(r"^.*~$"),
    re.compile(r"^\.DS_Store$"),
    re.compile(r"^Thumbs\.db$", re.I),
)
TRANSIENT_DIRS = (".pyc", "__pycache__", ".pytest_cache", ".mypy_cache",
                  # SCRATCH DIRECTORIES. This list originally held only toolchain caches, and a QC run's
                  # `viz/figures/_qc_tmp/` - twelve generated files including duplicate 600-dpi renders -
                  # was committed while this guard passed. A guard is only as good as its pattern list, and a
                  # scratch directory named by its author is exactly the artefact a wrong step order leaves
                  # behind. Anything underscore-prefixed or explicitly temporary now counts.
                  "_tmp", "_scratch", "_qc", "_build", "tmp", "scratch")
# `^_` is this repository's scratch convention. TWO NAMES ARE NOT SCRATCH: a Python package's
# `__init__.py` and `__main__.py` begin with underscores because the LANGUAGE requires it. A rule that
# cannot tell a naming convention from a language keyword will forbid a package - which is what it did to
# docpipe. Named explicitly rather than by weakening the rule: every other leading underscore is refused.
TRANSIENT_RE = (re.compile(r"^_(?!_init__\.py$|_main__\.py$).*$"),
                # THE TOKEN MUST FOLLOW A SEPARATOR, AND NOT MERELY APPEAR. The second pattern was
                # `^.*(tmp|scratch|bak|old)\..*$`, unanchored and case-insensitive, and it reported
                # `MathJax_Main-Bold.woff` as a stale backup: "B-old-." contains `old.`. Five CHTML bold
                # fonts - the glyphs browsers load for `\mathbf` - were refused at commit time as transient
                # artefacts. The intent is a BACKUP SUFFIX, so the token now has to be introduced by `.`,
                # `_` or `-` (`report.md.old`, `main.py.bak`, `notes_old.txt`) rather than found anywhere
                # inside a word. `-Bold` no longer matches because nothing separates the `B` from the `old`.
                #
                # This is what a pattern list is worth: `_qc_tmp` once slipped past because the rule tested
                # EXACT membership, and now a font is caught because the rule tests SUBSTRING membership.
                # A negative control in this check's own test must still require a real `*.old` to fail.
                re.compile(r"^.*[._-](tmp|scratch|bak|old)(\.[^.]+)?$", re.I))


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        return []
    return [l for l in out.stdout.splitlines() if l.strip()]


def transient_hits() -> list[str]:
    hits = []
    for f in tracked_files():
        base = pathlib.PurePosixPath(f).name
        if any(p.match(base) for p in TRANSIENT):
            hits.append(f)
        # ANY PATH COMPONENT THAT BEGINS WITH AN UNDERSCORE, and any component that IS a known cache name.
        # The first version of this check only tested components for EXACT membership in a tuple, which the
        # generated `_qc_tmp` did not match, and applied the underscore rule to the BASENAME only - so a
        # scratch directory holding twelve generated files, including duplicate 600-dpi renders, sat in the
        # repository while this guard reported a pass. The rule is now structural, not a name list.
        parts = pathlib.PurePosixPath(f).parts
        if any(part.startswith("_") or part in TRANSIENT_DIRS for part in parts[:-1]) \
                or any(part in TRANSIENT_DIRS for part in parts):
            hits.append(f)
        elif any(r.match(base) for r in TRANSIENT_RE):
            hits.append(f)
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--negative-test", action="store_true",
                    help="tamper with the protocol, require this check to fail, then restore it")
    args = ap.parse_args()

    if not PROTOCOL.exists() or not ANCHOR.exists():
        print(f"  [FAIL] protocol or anchor missing; nothing can be checked")
        return 1

    raw = PROTOCOL.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    actual_bytes = len(raw)
    anchor = json.loads(ANCHOR.read_text(encoding="utf-8"))

    if args.negative_test:
        print("  negative control: append a byte to the protocol and require check B to fail")
        PROTOCOL.write_bytes(raw + b"\n")
        try:
            rc = main_checks(quiet=True)
        finally:
            PROTOCOL.write_bytes(raw)
        if rc == 0:
            print("  [FAIL] the control passed while the protocol was modified - the check cannot detect drift")
            return 1
        print("  [OK] negative control: drift was detected, and the protocol has been restored")
        after = hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
        if after != actual_sha:
            print("  [FAIL] the restore did not reproduce the original bytes")
            return 1
        print("  [OK] restored byte-for-byte")
        return 0

    return main_checks(quiet=False)


def main_checks(quiet: bool) -> int:
    findings: list[str] = []

    hits = transient_hits()
    if hits:
        findings.append(f"{len(hits)} transient artefact(s) tracked: " + ", ".join(hits[:5]))

    raw = PROTOCOL.read_bytes()
    anchor = json.loads(ANCHOR.read_text(encoding="utf-8"))
    sha = hashlib.sha256(raw).hexdigest()
    recorded_sha = str(anchor.get("sha256", ""))
    if recorded_sha != sha:
        findings.append(
            f"the protocol digest is {sha[:16]} but the anchor records {recorded_sha[:16]} - the protocol was "
            f"edited WITHOUT a re-pin, so two different contents can share one version number")
    if int(anchor.get("bytes", -1)) != len(raw):
        findings.append(f"byte count differs: file {len(raw)}, anchor {anchor.get('bytes')}")

    file_version = re.search(r"\*\*Version:\*\*\s*([0-9]+\.[0-9]+)", raw.decode("utf-8"))
    if not file_version:
        findings.append("no version string found in the protocol")
    elif str(anchor.get("version", "")).strip() != file_version.group(1):
        findings.append(f"version differs: protocol {file_version.group(1)}, anchor "
                        f"{anchor.get('version')} - a bump did not reach the anchor, or a re-pin did not "
                        f"carry the bump")

    if not quiet:
        print(f"  tracked files: {len(tracked_files())}")
        print(f"  protocol: version {file_version.group(1) if file_version else '?'}, "
              f"{len(raw)} bytes, sha256 {sha[:16]}")
        print(f"  anchor:   version {anchor.get('version')}, {anchor.get('bytes')} bytes, "
              f"sha256 {str(anchor.get('sha256',''))[:16]}")

    if findings:
        print(f"\n  [FAIL] {len(findings)} ordering finding(s) - two steps ran in the wrong order:")
        for f in findings:
            print("      " + f)
        print("\n  Repair: re-pin the anchor after editing the protocol, and never stage a transient file.")
        return 1
    print("\n  [OK] no transient artefact is tracked, and the protocol's content, digest, byte count and")
    print("       version all agree - the state recorded is the state on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())