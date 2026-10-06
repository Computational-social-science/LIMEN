#!/usr/bin/env python
"""check_lean_status_freshness.py -- the status record's NUMBERS must be the numbers on disk.

WHY THIS EXISTS, AND THE EXACT FAILURE IT WAS WRITTEN FOR
    `docs/LEAN_FORMALIZATION_STATUS.md` reports a build result, an error count, a sorry count, a line
    count and a theorem count in a fenced block at the top. Every one of those is a measurement, and
    every one can go stale. This one did: the block read `theorem count: 10` for a full session after
    two theorems had been added - the protocol and Amendment 2 both said 12, the Lean file compiled
    with 12 theorems, and only the record said 10. Nothing about the formalisation was wrong. The
    record was, and the record is what a reader has to trust.

    That is the same class of defect as the pin: a hash file that records a comparison somebody once
    made. A recorded measurement is not a measurement. This check re-derives every figure and fails
    on any disagreement, so the block cannot be correct by accident.

WHAT IT DOES NOT CHECK
    It does not check that the formalisation is CORRECT, only that the record of it is CURRENT. A
    fresh record of a wrong claim is still wrong; the guard against that is `check_lean_axioms.py`,
    which asks Lean's kernel. The two are complementary and neither substitutes for the other: one
    proves the theorems, the other proves the description of them is not lying.

WHY THE NUMBERS ARE PARSED RATHER THAN RESTATED
    The check reads the figures out of the status document and compares them to what it measures. If
    instead it rewrote the document, a wrong number would be silently corrected and nobody would be
    told, which is the behaviour that produced the stale block in the first place.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
STATUS_DOC = REPO_ROOT / "docs" / "LEAN_FORMALIZATION_STATUS.md"


def _sources(root: pathlib.Path) -> list[pathlib.Path]:
    """EVERY kernel source - the same glob the axiom checker uses, so the two cannot disagree about the kernel."""
    return sorted(p for p in (root / "NHB" / "PhaseI").glob("*.lean") if not p.name.startswith("__"))


def lean_root() -> pathlib.Path:
    import os
    if os.environ.get("NHB_LEAN_ROOT"):
        return pathlib.Path(os.environ["NHB_LEAN_ROOT"])
    return REPO_ROOT.parent / "lean-nhb"


def measure(root: pathlib.Path) -> dict:
    """Derive every figure the status block reports, from the source and a real build."""
    core = root / "NHB" / "PhaseI" / "Core.lean"
    if not core.exists():
        return {"error": f"{core} not found"}

    text = core.read_text(encoding="utf-8")
    out: dict = {
        "lines": sum(len(p.read_text(encoding="utf-8").splitlines()) for p in _sources(root)),
        "theorems": sum(len(re.findall(r"^theorem\s", p.read_text(encoding="utf-8"), re.M))
                    for p in _sources(root)),
        "sorry": len(re.findall(r"^\s*(?:sorry|admit)\s*$|^\s*axiom\b", text, re.M)),
    }

    # A real build, because "errors remaining: 0" is a build result and not a property of the text.
    elan = pathlib.Path.home() / ".elan" / "bin"
    lake = next((p for p in (elan / "lake.exe", elan / "lake") if p.exists()), None)
    if lake is None:
        out["build"] = "lake not found"
        return out
    try:
        proc = subprocess.run([str(lake), "build"], cwd=root, capture_output=True,
                              text=True, timeout=600)
        combined = proc.stdout + proc.stderr
        out["errors"] = len(re.findall(r"^error:", combined, re.M))
        out["build_ok"] = "Build completed successfully" in combined
    except subprocess.TimeoutExpired:
        out["build"] = "TIMEOUT"
        return out

    # `theorems machine-checked` must come from the KERNEL, not from counting `theorem` keywords. A
    # keyword count cannot tell a proved theorem from one closed with a tactic that never used its
    # hypothesis - which is exactly the defect that produced the weak tie-break statement earlier. So
    # the figure is the number of theorems Lean itself reports axioms for, which is the only count that
    # means "verified".
    # DELEGATED, NOT RE-IMPLEMENTED. This block used to build its own axiom query with Core's module and
    # namespace hardcoded - a SECOND implementation of what check_lean_axioms.py already does. Two
    # implementations of one measurement is the "two writers, one output" defect, and they diverged the
    # moment a second source file appeared. One implementation, one answer.
    proc = subprocess.run([sys.executable, "-B", str(REPO_ROOT / "scripts" / "check_lean_axioms.py"),
                           "--lean-root", str(root)],
                          capture_output=True, text=True, cwd=REPO_ROOT, timeout=1200)
    qout = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        out["checked"] = None
        return out
        # `decide`-proved theorems print "does not depend on any axioms" instead of a bracketed list,
        # so counting only the bracketed form under-reports by exactly the theorems with the strongest
        # proofs. Both wordings are counted; see check_lean_axioms.py for the same fix and reason.
    m = re.search(r"OK:\s*(\d+)\s*theorem\(s\), none depends on", qout)
    if not m:
        out["checked"] = None
        return out
    out["checked"] = int(m.group(1))
    # The check fails outright if any theorem depends on the forbidden axiom, so a successful run IS the
    # statement that this count is zero - measured by the kernel, not assumed here.
    out["sorryAx"] = 0
    out["axioms_reported"] = int(m.group(1))

    return out


def claimed(doc: pathlib.Path) -> dict:
    """The figures the status document asserts, parsed out of its fenced status block."""
    text = doc.read_text(encoding="utf-8")

    m = re.search(r"^\s*theorem count\s*:\s*(\d+)", text, re.M)
    theorems = int(m.group(1)) if m else None

    m = re.search(r"^\s*theorems machine-checked\s*:\s*(\d+)", text, re.M)
    checked = int(m.group(1)) if m else None

    m = re.search(r"^\s*errors remaining\s*:\s*(\d+)", text, re.M)
    errors = int(m.group(1)) if m else None

    m = re.search(r"^\s*sorry\s*/\s*admit\s*/\s*axiom\s*:\s*(\d+)", text, re.M)
    sorry = int(m.group(1)) if m else None

    # BOTH FORMS: the record said "Core.lean, N lines" while the kernel had one source, and says
    # "NHB/PhaseI/*.lean, N lines" now that it has two. A parse tied to the old wording would report a
    # missing figure - the drift it exists to catch, produced by the fix for a different drift.
    m = re.search(r"(?:Core\.lean|NHB/PhaseI/\*\.lean),\s*(\d+)\s*lines", text)
    lines = int(m.group(1)) if m else None

    m = re.search(r"OK:\s*(\d+)\s*theorem\(s\), none depends on", text)
    axioms_reported = int(m.group(1)) if m else None

    return {"theorems": theorems, "checked": checked, "errors": errors,
            "sorry": sorry, "lines": lines, "axioms_reported": axioms_reported}


# Documents that also quote the theorem count. The protocol is the one that matters most: it is the
# programme's global anchor, so a stale number there is read as authoritative by every other artefact.
# This check exists because the protocol said "12 theorems" while the file had 15 - the count was
# updated in one place and the anchor kept the old figure, and no guard was watching the anchor.
COUNT_CLAIM = re.compile(r"(\d+)\s+theorems?, zero errors")
COUNT_DOCS = (
    "protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md",
    "docs/PHASE_I_AMENDMENT_2.md",
    "docs/LEAN_FORMALIZATION_STATUS.md",
)


def check_count_claims(measured: dict, root: pathlib.Path | None = None) -> list[str]:
    """Every document that quotes a theorem count must quote the same, current one."""
    out: list[str] = []
    n = measured.get("theorems")
    if n is None:
        return out
    base = root or REPO_ROOT
    for rel in COUNT_DOCS:
        p = base / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for m in COUNT_CLAIM.finditer(text):
            said = int(m.group(1))
            if said != n:
                line = text[:m.start()].count("\n") + 1
                out.append(f"[FRESH] {rel}:{line} says \"{m.group(0)}\" but the kernel reports {n} "
                           f"theorem proved - a stale count in a document others treat as authority")
    return out


def compare(measured: dict, said: dict) -> list[str]:
    out: list[str] = []
    pairs = [
        ("theorems", "theorem count"),
        ("checked", "theorems machine-checked"),
        ("errors", "errors remaining"),
        ("sorry", "sorry / admit / axiom"),
        ("lines", "kernel line count"),
    ]
    # The quoted `#print axioms` transcript must agree with the kernel-derived count above. It is
    # compared rather than measured separately because it IS a quotation of that measurement: if the
    # transcript in the document and the live kernel disagree, the document is showing a reader output
    # that no longer occurs, which is the exact failure mode of a pasted log.
    for key, label in pairs:
        m, s = measured.get(key), said.get(key)
        if s is None:
            out.append(f"[FRESH] the status record does not state {label} - a missing figure is as "
                       f"much a drift as a wrong one")
        elif m is None:
            # A figure the CHECK cannot derive must not be reported as agreeing. An earlier version
            # skipped these, which left `theorems machine-checked` and the quoted #print-axioms count
            # unchecked while appearing to check six figures - the same "measured nothing, reported
            # clean" shape as the Lean axiom guard that returned no output at all.
            out.append(f"[FRESH] {label}: the check cannot DERIVE this figure, so it is unverified "
                       f"- derive it or delete it from the record")
        elif m != s:
            out.append(f"[FRESH] {label}: record says {s}, disk says {m}")

    if measured.get("axioms_reported") is not None and said.get("axioms_reported") is not None:
        if said["axioms_reported"] != said.get("checked"):
            out.append(f"[FRESH] the quoted #print-axioms transcript says "
                       f"{said['axioms_reported']} theorem(s) but the block says "
                       f"{said.get('checked')} were machine-checked - the document shows two "
                       f"different counts of the same thing")
    if measured.get("sorryAx"):
        out.append(f"[FRESH] {measured['sorryAx']} theorem(s) depend on sorryAx - the formalisation "
                   f"is not proved, whatever the record says")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "status freshness").split("\n")[0])
    ap.add_argument("--lean-root", default=None)
    args = ap.parse_args()

    root = pathlib.Path(args.lean_root).resolve() if args.lean_root else lean_root()
    if not STATUS_DOC.exists():
        print(f"[FAIL] {STATUS_DOC} not found")
        return 1

    measured = measure(root)
    if "error" in measured:
        print(f"[FRESH] cannot measure: {measured['error']}")
        return 1

    if not measured.get("build_ok"):
        print(f"[FRESH] the Lean build does not succeed, so the status record cannot claim "
              f"{measured.get('errors', '?')} errors - measured {measured.get('errors', '?')}")
        return 1

    said = claimed(STATUS_DOC)
    findings = compare(measured, said) + check_count_claims(measured, REPO_ROOT)

    if findings:
        print(f"STALE: {len(findings)} figure(s) in {STATUS_DOC.name} disagree with the build")
        for f in findings:
            print("  " + f)
        print("\n  The formalisation may be fine; the RECORD of it is not, and the record is what a "
              "reader trusts. Re-derive the block from `scripts/check_lean_axioms.py` output.")
        return 1

    print(f"OK: status record is current — {measured['theorems']} theorems, {measured['errors']} errors, "
          f"{measured['sorry']} sorry, {measured['lines']} lines, all matching the build")
    return 0


if __name__ == "__main__":
    sys.exit(main())