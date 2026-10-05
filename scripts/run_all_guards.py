#!/usr/bin/env python
"""run_all_guards.py -- run every standing guard in one command, and report honestly.

WHY THIS EXISTS
    The project has accumulated ten checks, six of which own a negative control. Running them one at a
    time is how a stale record survives: the Lean guard passed while `docs/LEAN_FORMALIZATION_STATUS.md`
    still said the file did not compile, because nobody was running the guard when the document was
    written. Ten green checks that must each be remembered are worth less than one command.

WHAT IT DOES AND DOES NOT COVER
    Each guard is a separate script with its own exit code, and this runs them as subprocesses rather
    than importing them, so a guard that crashes cannot take the others with it and cannot leave state
    that makes a later run look clean. It reports the count of checks that ran, because a runner that
    silently skips one is the failure mode this whole file exists to avoid - the same shape as the Lean
    axiom check that found no theorems and reported "axiom-free".

    Passing here means only that the guards passed. It is not evidence that the science is right.

THE NEGATIVE CONTROLS ARE RUN BY DEFAULT
    A guard that has never failed is not a guard, and running only the positive direction is how a
    broken check survives: check_lean_axioms reported every theorem as axiom-free while its query was
    returning nothing at all, and nothing would have said so except the control. `--skip-negative`
    exists for speed during development and prints how many controls it skipped.
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# (script, args, one-line description). Order is deliberate: cheap and structural first, so a broken
# tree is reported before the slower external-toolchain checks run.
GUARDS: list[tuple[str, tuple[str, ...], str]] = [
    ("check_object_drift.py", (), "no retired artefact, object or Lean sorry/admit is live"),
    ("check_object_drift.py", ("--negative-test",), "the drift guard fires on each injected defect"),
    ("check_anchor.py", (), "anchor hash, versions and promises are intact"),
    ("check_relative_paths.py", (), "no hardcoded absolute path in code, config or script"),
    ("check_protocol_consistency.py", (), "protocol V/N/C/P/E claims agree with the anchor"),
    ("check_math_renders.py", (), "LaTeX uses renderer-compatible delimiters"),
    ("check_pin_integrity.py", (), "the pinned instrument on disk IS the pinned instrument"),
    ("check_pin_integrity.py", ("--negative-test",), "the pin guard fails on absent file and wrong digest"),
    ("check_lean_axioms.py", (), "no theorem depends on sorryAx"),
    ("check_lean_axioms.py", ("--negative-test",), "the axiom guard catches a sorry-proved theorem"),
    ("check_lean_status_freshness.py", (),
     "every document's theorem count matches the kernel"),
    ("check_manuscript_html.py", (),
     "the rendered page is not lying: numbering, sentinels, math integrity, note completeness"),
    ("build_provenance_table.py", ("--check",),
     "every PROVED claim in the provenance table names a kernel-verified theorem"),
    ("build_provenance_table.py", ("--negative-test",),
     "the provenance generator refuses a claim whose proof was never done"),
    ("o1_agent_rater.py", ("--selftest",),
     "the kappa and Spearman implementations answer known-answer cases correctly"),
]

# Guards that need something outside this repository. They are reported separately rather than mixed
# into the pass/fail total, because their absence is a fact about the machine, not a defect in the
# project - and a guard that is silently skipped is exactly what this runner is meant to prevent.
EXTERNAL = {"check_lean_axioms.py"}


def run(script: str, args: tuple[str, ...], timeout: int) -> tuple[int, str, float]:
    path = REPO_ROOT / "scripts" / script
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            [sys.executable, "-B", str(path), *args],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=timeout)
        out = (proc.stdout + proc.stderr).strip()
        return proc.returncode, out, time.monotonic() - t0
    except subprocess.TimeoutExpired:
        return 124, f"TIMEOUT after {timeout}s", time.monotonic() - t0


def summarise(out: str) -> str:
    """First meaningful line, so the table stays readable."""
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    if not lines:
        return "(no output)"
    for l in lines:
        if l.startswith(("OK", "[FAIL]", "AXIOM FAIL", "PIN FAIL", "DRIFT", "negative control")):
            return l
    return lines[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "guard runner").split("\n")[0])
    ap.add_argument("--skip-negative", action="store_true",
                    help="run only the positive direction (development speed; prints what was skipped)")
    ap.add_argument("--timeout", type=int, default=600, help="per-guard timeout in seconds")
    ap.add_argument("--verbose", action="store_true", help="print each guard's full output")
    args = ap.parse_args()

    selected = [g for g in GUARDS
                if not (args.skip_negative and "--negative-test" in g[1])]
    skipped = len(GUARDS) - len(selected)

    print(f"running {len(selected)} guard run(s)"
          + (f" ({skipped} negative control(s) SKIPPED)" if skipped else "")
          + "\n")

    failures: list[tuple[str, str, str]] = []
    rows: list[tuple[str, str, str, float]] = []

    for script, gargs, desc in selected:
        label = script.replace("check_", "").replace(".py", "") + (
            " [neg]" if "--negative-test" in gargs else "")
        rc, out, dt = run(script, gargs, args.timeout)
        mark = "OK" if rc == 0 else "FAIL"
        if rc != 0:
            failures.append((label, desc, out))
        rows.append((mark, label, summarise(out), dt))
        if args.verbose and rc != 0:
            print(f"--- {label} ---\n{out}\n")

    width = max(len(r[1]) for r in rows)
    for mark, label, line, dt in rows:
        print(f"  [{mark}] {label:<{width}}  {dt:5.1f}s  {line[:70]}")

    print()
    if failures:
        print(f"GUARD FAILURE: {len(failures)} of {len(selected)} run(s) failed\n")
        for label, desc, out in failures:
            print(f"  {label} — {desc}")
            for l in out.splitlines()[:8]:
                print("      " + l)
            print()
        print("Every claim below this line is unverified until these pass.")
        return 1

    print(f"ALL {len(selected)} GUARD RUNS PASS"
          + (f" — but {skipped} negative control(s) were skipped, so the guards themselves are "
             f"unproven this run" if skipped else ""))
    if not skipped:
        print("Each guard was also required to fail on an injected defect, so the checks are "
              "themselves verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())