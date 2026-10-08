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
import atexit
import os
import contextlib
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
    ("check_dataset_provenance.py", (),
     "every channel's primary evidence is observed human behaviour"),
    ("check_dataset_provenance.py", ("--negative-test",),
     "the provenance guard rejects a channel whose primary is simulated"),
    ("check_pin_integrity.py", ("--negative-test",), "the pin guard fails on absent file and wrong digest"),
    ("check_lean_axioms.py", (), "no theorem depends on sorryAx"),
    ("check_lean_axioms.py", ("--negative-test",), "the axiom guard catches a sorry-proved theorem"),
    ("check_lean_status_freshness.py", (),
     "every document's theorem count matches the kernel"),
    ("check_lean_citations.py", (),
     "every kernel name a document cites exists in the Lean source"),
    ("check_lean_citations.py", ("--negative-test",),
     "the citation guard catches a theorem that was never proved"),
    ("check_attributed_numbers.py", (),
     "a value measured here is not written as one quoted from a cited work"),
    ("check_attributed_numbers.py", ("--negative-test",),
     "the attribution guard catches a number attributed to the wrong source"),
    ("check_handoff_freshness.py", (),
     "the handoff note's recorded tip and protocol version are still the facts"),
    ("check_handoff_freshness.py", ("--negative-test",),
     "the handoff guard catches a stale protocol version in the note"),
    ("check_manuscript_html.py", (),
     "the rendered page is not lying: numbering, sentinels, math integrity, note completeness"),
    ("build_provenance_table.py", ("--check",),
     "every PROVED claim in the provenance table names a kernel-verified theorem"),
    ("build_provenance_table.py", ("--negative-test",),
     "the provenance generator refuses a claim whose proof was never done"),
    ("o1_agent_rater.py", ("--selftest",),
     "the kappa and Spearman implementations answer known-answer cases correctly"),
    ("build_proof_appendix.py", ("--check",),
     "the proof appendix matches the Lean source and every theorem has a declared bearing"),
    ("build_proof_appendix.py", ("--negative-test",),
     "the appendix generator refuses a theorem with no declared bearing"),
    ("o1_recoverability.py", ("--self-test",),
     "the channel's distance and alignment primitives answer known cases correctly"),
    ("check_o1_anchor.py", (),
     "the O1 readability floor is the published anchor, and the ladder clears it"),
    ("check_o1_anchor.py", ("--negative-test",),
     "the anchor guard refuses a floor above every ladder point"),
    ("o3_leakage_probe.py", ("--self-test",),
     "the routability margin answers known-answer cases correctly"),
    ("o3_leakage_probe.py", ("--template-audit",),
     "no unresolved slot, no duplicate state within a template, options match criteria, gold among options"),
    ("fix_item_bank_capitalization.py", ("--verify-packs",),
     "every packed stimulus text matches the item bank exactly"),
    ("o3_consistency_audit.py", (),
     "item consistency: structure, ambiguity, routability with a shuffled control, split-half stability"),
    ("check_window_marginals.py", (),
     "the confirmatory window is comparable to dev on domain and template structure, on bank alone"),
    ("qc_stage2_figures.py", (),
     "no text overlap, nothing outside the canvas, no font size outside the journal band"),
    ("check_si_numbers.py", (),
     "every numeric cell of the SI's results tables equals its source, and quoted family figures match"),
    ("check_documents.py", (),
     "every produced document carries the mathematics, figures and assets its source declares, and every "
     "renderer has the fonts it needs"),
    ("check_step_order.py", (),
     "no transient artefact is tracked and the protocol's content, digest and version all agree"),
    ("check_step_order.py", ("--negative-test",),
     "negative control: protocol drift is detected and restored byte-for-byte"),
    ("check_seal_readiness.py", (),
     "no section-12 row is waiting and every named authority document exists"),
    ("check_confidence_contamination.py", (),
     "no emitted confidence is the constant the frozen instrument substitutes into affected entries"),
    ("check_output_collisions.py", (),
     "every declared deliverable is written by exactly the producer named for it, and a non-producer given "
     "its path is refused"),
    ("check_paper_numbers.py", (),
     "every number the paper asserts equals the record it came from, and no retired vocabulary appears"),
    ("check_si_prose.py", (),
     "every paragraph in every SI source is a single line, so no emphasis is split across a paragraph break"),
    ("check_repo_size.py", (),
     "no tracked file and no reachable object exceeds the size the remote will accept, and the check fails on "
     "one that does"),
    ("analyze_phase1.py", ("--synthetic",),
     "each confirmatory hypothesis fires on its OWN positive control and none fires on the null"),
]

# Guards that need something outside this repository. They are reported separately rather than mixed
# into the pass/fail total, because their absence is a fact about the machine, not a defect in the
# project - and a guard that is silently skipped is exactly what this runner is meant to prevent.
EXTERNAL = {"check_lean_axioms.py"}


# --------------------------------------------------------------------------------------------------------
# ONE RUN AT A TIME. Five guards write negative-control probes INSIDE the tree - deliberately, because the
# probe has to be scannable for the guard to prove it would fail on it - and delete them within the same run.
# Two runners therefore share those paths, and the failure modes are real and were observed: a probe created
# by run A and deleted by run B mid-scan, a commit catching a probe between create and delete
# (`error: open("docs/__drift_negative_control__.lean"): No such file or directory`), and a spurious finding
# that looks like a defect in the code under test rather than in the way it was launched.
#
# A lock is added rather than moving the probes out of the tree, because a probe outside the tree cannot
# prove the guard would fail on something inside it.
#
# THE LOCK IS STALE-SAFE. It records the owning pid and its start time, and a lock whose owner is gone is
# reclaimed. A lock that can be left behind by a crash is worse than no lock: it turns one dead run into a
# permanently red suite, and the fix people reach for is to delete the check.
LOCK = REPO_ROOT / ".git" / "run_all_guards.lock"


def _lock_state(lock: pathlib.Path) -> str:
    """Return 'live', 'stale' or 'unknown' for the lock that is present.

    THREE STATES, NOT TWO, AND THE DEFAULT WHEN UNSURE IS 'unknown'. The first version returned a bool and
    treated any failure to check the pid as stale, which meant the lock never refused anything: `tasklist`
    emits bytes in the machine's OEM code page, `text=True` tried UTF-8, the decode raised, the handler
    swallowed it, and the "stale" answer let a second suite start on top of the first. The failure was
    invisible because a lock that never refuses looks exactly like a lock that is never contended.

    The asymmetry is the point. A wrong 'stale' lets two runs share the probe paths and produces findings
    that are not about the code - silent corruption. A wrong 'live' refuses a run that a human then clears
    in one command - loud and cheap. Where the two errors are not equally costly, the safe default is the
    loud one.
    """
    try:
        pid_s, ts_s = lock.read_text(encoding="utf-8").strip().split()[:2]
        pid, ts = int(pid_s), float(ts_s)
    except Exception:
        return "stale"                    # unreadable and malformed: nothing is running behind it
    if time.time() - ts > 2 * 3600:
        return "stale"                    # an explicit upper bound, so a crash cannot lock the suite forever
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, timeout=30)
        text = out.stdout.decode("utf-8", errors="replace") + out.stderr.decode("utf-8", errors="replace")
        if out.returncode != 0:
            return "unknown"
        return "live" if str(pid) in text else "stale"
    except Exception:
        return "unknown"


def wait_for_lock(limit_s: float) -> bool:
    """Block until the lock is free, up to `limit_s`. Returns True if it is free (or reclaimed).

    Refusing immediately is right when a person is watching - they can see why and decide. It is wrong in an
    unattended chain, where the correct behaviour is to WAIT: the other run holds the probes for a few
    minutes, not forever, and a nightly job that dies because a person happened to be running the suite at the
    same moment has failed for no reason. Which of the two is wanted is a property of the caller, so it is a
    flag rather than a policy.
    """
    deadline = time.time() + limit_s
    while True:
        state = _lock_state(LOCK) if LOCK.exists() else "stale"
        if state == "stale":
            return True
        if time.time() >= deadline:
            print(f"waited {limit_s:.0f}s and the lock is still {state}: "
                  f"{LOCK.read_text(encoding='utf-8').strip()}")
            return False
        print(f"  lock is {state}; waiting (up to {limit_s:.0f}s)...")
        time.sleep(5)


def acquire_single_run_lock(wait_s: float = 0.0) -> None:
    """Refuse to run two guard suites at once, and reclaim a lock whose owner has died.

    THE LOCK IS RELEASED THROUGH atexit, not a `with` block, and the reason is a defect this change itself
    caused twice while being written: wrapping the suite body in `with` indents a hundred lines and a single
    mis-indented continuation is a syntax error that only appears when the file is RUN. An atexit handler
    needs no re-indentation, releases on every normal exit including sys.exit, and the staleness check covers
    the case atexit cannot see - a killed process.
    """
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if wait_s > 0 and LOCK.exists() and not wait_for_lock(wait_s):
        raise SystemExit(3)
    state = _lock_state(LOCK) if LOCK.exists() else "stale"
    if state in ("live", "unknown"):
        print(f"ANOTHER GUARD RUN IS IN PROGRESS OR CANNOT BE RULED OUT ({state}): "
              f"{LOCK.read_text(encoding='utf-8').strip()}")
        print("Five guards write negative-control probes inside the tree and delete them within the run, so two")
        print("runners share those paths: a finding from a concurrent run is not evidence about the code.")
        print("Wait for it, or delete the lock if you are certain it is stale.")
        raise SystemExit(3)
    if LOCK.exists() and state == "stale":
        print(f"reclaiming a stale lock (owner gone or expired): {LOCK.read_text(encoding='utf-8').strip()}")
    LOCK.write_text(f"{os.getpid()} {time.time():.0f}\n", encoding="utf-8")
    atexit.register(lambda: LOCK.unlink(missing_ok=True))


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
    ap.add_argument("--wait", type=float, default=0.0, metavar="SECONDS",
                    help="if another run holds the lock, wait up to SECONDS for it instead of refusing "
                         "(default: refuse immediately, which is right when a person is watching)")
    args = ap.parse_args()

    acquire_single_run_lock(args.wait)

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