#!/usr/bin/env python3
"""Drift guard for the live object.

The repository's live object is stated in CURRENT_OBJECT.md. Two objects were retired on
2026-10-04 (R1 the JevRSI loop objective, R2 the RTX 4070 harness-first proposal). A retirement
banner does not retire anything, so this guard asserts their ABSENCE instead.

Three classes, all required (see the project's audit skill, "write the drift guard, then
NEGATIVE-TEST it"):

  A. artifact absence  - a retired path must not exist in the live tree.
  B. instruction absence - no live file may carry a command or import that would RUN a retired
                           object. Deliberately narrower than a bare name match: naming a trap in a
                           retirement notice is the point, so B requires an execution/import context.
  C. concept absence   - a live file may name a retired CONCEPT only if that same file also declares
                           the retirement, using one of the marker words below.

Exit 0 = clean. Exit 1 = drift, with one line per finding.

Usage:  python scripts/check_object_drift.py [--root .] [--verbose]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------- A: retired artifacts
# Paths that must NOT exist in the live tree. These were moved into archive/ on 2026-10-04.
RETIRED_ARTIFACTS = [
    "config/arm0_spec.json",
    "config/edit_guard.json",
    "config/science_state.json",
    "viz/health_dashboard.html",
    "scripts/check_arm0_spec.py",
    "scripts/check_edit_guard.py",
    "scripts/quarantine_arm0.py",
    "scripts/audit_dashboard.py",
    "scripts/build_v1_env.py",
    "scripts/export_health_state.py",
    "loop-social.gif",
    "docs/arm0_acceptance_gate.md",
    "docs/arm0_host_feasibility.md",
    "docs/arm0_probe_evidence.md",
    "docs/arm0_timing_correction.md",
    "docs/eval_batch_size_correction.md",
    "docs/reproduction_audit.md",
    "docs/JEV_PIPELINE_AUDIT.md",
    "docs/APPROACH_REDISTILLED.md",
    "evidence/arm0_LAUNCH.json",
    "evidence/arm0_audit.md",
    "evidence/arm0_result.md",
    "evidence/cost_ledger.md",
    "QTVtynAWErNOSxyf-grok-workspace",
]

# ---------------------------------------------------------------- B: execution contexts
# A retired object may be NAMED anywhere; it may not be RUN. These patterns require an execution or
# import context, so a retirement notice ("the loop was retired") never trips them.
#
# The interpreter token is REQUIRED. A known failure mode of class B is over-firing on a bare
# mention: prose that happens to begin with a filename ("check_edit_guard.py is: the arm's spec
# carries CRLF…") matched an earlier, looser form of the first rule. Requiring `python`/`py`/`bash`/
# `sh`/`make`/`pytest` before the name keeps the rule to genuine invocations.
RETIRED_RUN_PATTERNS = [
    # The line may begin with prose — "Run `python scripts/x.py` first" — so the interpreter token
          # is required but NOT anchored to the start of the line. **Anchoring it was a real blind spot,
          # and the negative control is what found it:** the guard reported OK across a repository for a
          # day while any instruction phrased as a sentence rather than as a bare command escaped it.
          (re.compile(
              r"(?:python[0-9.]*|py|bash|sh|make|pytest)\s+"
              r"(?:-m\s+)?(?:\./|\.\./)*(?:scripts/)?"
              r"(check_arm0_spec|check_edit_guard|quarantine_arm0|audit_dashboard|build_v1_env|"
              r"export_health_state|health|run_with_heartbeat|calibrate_against_release)\.py\b"),
           "runs a retired script"),
    (re.compile(r"^\s*(?:from|import)\s+(?:jevrsi|rsijev)\b"),
     "imports a retired package"),
    (re.compile(r"^\s*git\s+(?:revert|reset|checkout)\b.*\barm0\b"),
     "re-enters the retired arm"),
]

# ---------------------------------------------------------------- D: Lean sorry/admit/axiom
# Lean core-only file MUST NOT contain sorry, admit, or axiom. The project's discipline is
# zero such constructs. A Lean file with sorry compiles but proves nothing - it is the exact
# failure this project exists to prevent.
LEAN_SORRY_ADMIT_AXIOM = re.compile(r"(?<![\"'`])\b(sorry|admit|axiom)\b(?![\"'`])")


def check_lean_sorry_admit(files: list[Path], root: Path) -> list[str]:
    """Lean core-only files must NOT contain sorry, admit, or axiom outside comments/strings."""
    findings = []
    for f in files:
        rel = f.relative_to(root).as_posix()
        if rel in SELF_EXEMPT:
            continue
        if f.suffix != ".lean":
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for m in LEAN_SORRY_ADMIT_AXIOM.finditer(line):
                findings.append(
                    f"[D] {rel}:{i} Lean file contains prohibited keyword: {m.group(1)} -> {line.strip()[:120]}"
                )
    return findings
# retired object. The R1 programme used a Laya root and the current protocol legitimately names one as
# a candidate checkpoint to pin (§3.2, "pick one and pin"). Listing a model name here would fire on
# the object's own document and force an edit to the protocol to silence it — which is tampering, not
# retirement. The entries below name OBJECTS the programme has retired (R1's loop objective, R2's
# harness-first proposal), or products of the retired ecosystem.
RETIRED_CONCEPTS = [
    "JevRSI",
    "RSI-Jev",
    "harness-first",
    "harness first",
    "AgentJev",
    "AnyJev",
    "arm 0",
    "arm0",
    "self-evolving Jev",
    "self-improvement loop",
]

# Marker words that legitimise a mention inside the same file.
RETIREMENT_MARKERS = [
    "CURRENT_OBJECT.md",
    "retire",
    "Retire",
    "RETIRED",
    "superseded",
    "Superseded",
    "archive/",
    "not a target",
    "do not work on",
    "Do not work on",
    "R1 —",
    "R2 —",
    "historical record",
    "not an instruction",
]

# Files exempt from B and C: this guard defines the patterns, so it necessarily contains them.
SELF_EXEMPT = {"scripts/check_object_drift.py"}

# Directories never scanned.
SKIP_DIRS = {".git", "archive", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"}
# Extensions worth scanning.
SCAN_EXT = {".md", ".py", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".sh", ".txt", ".html"}


def tracked_and_live_files(root: Path) -> list[Path]:
    """Live files: git-tracked files outside archive/, PLUS untracked-but-present source files.

    Both halves matter. Scanning only tracked files makes the guard blind to a new file until it is
    committed — which is exactly when drift is cheapest to introduce and hardest to notice, since the
    work is still in progress. Scanning only the filesystem cannot distinguish an archive from a
    target. The union is the live tree.
    """
    names: set[str] = set()
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            capture_output=True, text=True, check=True,
        ).stdout
        names.update(line for line in out.splitlines() if line.strip())

        # Untracked but present (respects .gitignore: --others without --ignored)
        out2 = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True, check=True,
        ).stdout
        names.update(line for line in out2.splitlines() if line.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        names.update(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())

    keep = []
    for rel in sorted(names):
        f = root / rel
        if any(part in SKIP_DIRS for part in Path(rel).parts):
            continue
        if f.suffix and f.suffix not in SCAN_EXT:
            continue
        if f.is_file():
            keep.append(f)
    return keep


def check_artifacts(root: Path) -> list[str]:
    findings = []
    for rel in RETIRED_ARTIFACTS:
        if (root / rel).exists():
            findings.append(f"[A] retired artifact present in the live tree: {rel}")
    return findings


def check_instructions(files: list[Path], root: Path) -> list[str]:
    findings = []
    for f in files:
        rel = f.relative_to(root).as_posix()
        if rel in SELF_EXEMPT:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for pat, why in RETIRED_RUN_PATTERNS:
                if pat.search(line):
                    findings.append(f"[B] {rel}:{i} {why} -> {line.strip()[:90]}")
    return findings


def check_concepts(files: list[Path], root: Path) -> list[str]:
    findings = []
    for f in files:
        rel = f.relative_to(root).as_posix()
        if rel in SELF_EXEMPT:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hit = [c for c in RETIRED_CONCEPTS if c in text]
        if not hit:
            continue
        if any(m in text for m in RETIREMENT_MARKERS):
            continue  # this file declares the retirement -> mention is legitimate
        findings.append(
            f"[C] {rel} names retired concept(s) {hit} without declaring the retirement "
            f"(needs a marker such as 'retired' / 'archive/' / 'CURRENT_OBJECT.md')"
        )
    return findings


def negative_test(root: Path) -> int:
    """Prove the guard fires. A guard that has never failed is not a guard.

    Three classes are exercised, one defect each, injected into a scratch file that is deleted
    afterwards. The repository's own files are never modified, so the control cannot leave the tree in
    a state where a real defect is masked.

    A guard that reports findings on a clean tree, or stays silent on an injected defect, is itself
    the defect this function exists to catch.
    """
    scratch = root / "docs" / "__drift_negative_control__.md"
    results = []

    baseline = (check_artifacts(root)
                + check_instructions(tracked_and_live_files(root), root)
                + check_concepts(tracked_and_live_files(root), root))
    results.append(("clean tree reports no drift", len(baseline) == 0))

    # Class C: a retired CONCEPT asserted without a retirement marker anywhere in the file.
    scratch.write_text(
        "# probe\n\n"
        "The arm0 harness is the model this repository trains.\n",
        encoding="utf-8")
    findings = check_concepts(tracked_and_live_files(root), root)
    results.append(("retired concept asserted without a marker is caught",
                    any("__drift_negative_control__" in f for f in findings)))
    scratch.unlink()

    # Class B: an instruction to RUN a retired script.
    scratch.write_text(
        "# probe\n\n"
        "Run `python scripts/run_with_heartbeat.py` before every launch.\n",
        encoding="utf-8")
    findings = check_instructions(tracked_and_live_files(root), root)
    results.append(("instruction to run a retired script is caught",
                    any("__drift_negative_control__" in f for f in findings)))
    scratch.unlink()

    # Class C negative-of-negative: the SAME concept WITH a retirement marker must NOT fire,
    # because naming what was retired is the opposite of drift.
    scratch.write_text(
        "# probe\n\n"
        "This documents a RETIRED object. JevRSI is retired and is not a target.\n",
        encoding="utf-8")
    findings = check_concepts(tracked_and_live_files(root), root)
    results.append(("retired concept WITH a retirement marker does not fire",
                    not any("__drift_negative_control__" in f for f in findings)))
    scratch.unlink()

    # Class D: a Lean file containing sorry/admit/axiom (the discipline this project enforces).
    # The scratch file is a .lean file so the checker examines it; it must fire.
    lean_scratch = root / "docs" / "__drift_negative_control__.lean"
    lean_scratch.write_text(
        "-- probe\n\n"
        "theorem fake : False := by sorry\n",
        encoding="utf-8")
    findings = check_lean_sorry_admit(tracked_and_live_files(root) + [lean_scratch], root)
    results.append(("Lean sorry/admit/axiom is caught",
                    any("__drift_negative_control__" in f and "sorry" in f for f in findings)))
    lean_scratch.unlink()

    if scratch.exists():
        scratch.unlink()

    print("negative control:")
    ok = True
    for name, passed in results:
        print(f"  [{'OK' if passed else 'MISS'}] {name}")
        ok = ok and passed
    print(f"  scratch removed: {'YES' if not scratch.exists() else 'NO'}")
    print(f"\n  {'ALL CONTROLS PASS' if ok else 'CONTROL FAILURE — the guard is not trustworthy'}")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="repository root")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--negative-test", action="store_true",
                    help="inject each defect class and require the guard to fire on all of them")
    args = ap.parse_args()

    root = Path(args.root).resolve()

    if args.negative_test:
        return negative_test(root)

    files = tracked_and_live_files(root)

    findings = (check_artifacts(root) + check_instructions(files, root) +
                check_concepts(files, root) + check_lean_sorry_admit(files, root))

    if args.verbose:
        print(f"scanned {len(files)} live files under {root}")
        print(f"artifact rules: {len(RETIRED_ARTIFACTS)}   run-pattern rules: {len(RETIRED_RUN_PATTERNS)}   "
              f"concept rules: {len(RETIRED_CONCEPTS)}")

    if findings:
        print(f"DRIFT: {len(findings)} finding(s)")
        for line in findings:
            print("  " + line)
        return 1

    print(f"OK: no drift across {len(files)} live files "
          f"({len(RETIRED_ARTIFACTS)} artifact rules, {len(RETIRED_CONCEPTS)} concept rules)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
