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
        "lines": len(text.splitlines()),
        "theorems": len(re.findall(r"^theorem\s", text, re.M)),
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
    build_lib = root / ".lake" / "build" / "lib" / "lean"   # NOT `lib`: lake nests a `lean` dir
    query = core.parent / "__freshness_query__.lean"
    names = re.findall(r"^theorem\s+([A-Za-z_][A-Za-z0-9_']*)", text, re.M)
    query.write_text("import NHB.PhaseI.Core\n"
                     + "".join(f"#print axioms PhaseI.Selective.{n}\n" for n in names),
                     encoding="utf-8")
    import os
    env = dict(os.environ)
    env["LEAN_PATH"] = str(build_lib)
    try:
        q = subprocess.run([str(lake), "env", "lean", str(query)], cwd=root, capture_output=True,
                           text=True, env=env, timeout=600)
        qout = q.stdout + q.stderr
        # `decide`-proved theorems print "does not depend on any axioms" instead of a bracketed list,
        # so counting only the bracketed form under-reports by exactly the theorems with the strongest
        # proofs. Both wordings are counted; see check_lean_axioms.py for the same fix and reason.
        got = re.findall(r"'[\w.]+' depends on axioms: \[([^\]]*)\]", qout) \
            + re.findall(r"'[\w.]+' does not depend on any axioms", qout)
        out["checked"] = len(got)
        out["sorryAx"] = sum(1 for d in got if "sorryAx" in d)
        # The number the LIVE kernel would print for the transcript quoted in the document.
        out["axioms_reported"] = len(got)
    except subprocess.TimeoutExpired:
        out["checked"] = None
    finally:
        query.unlink(missing_ok=True)

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

    m = re.search(r"Core\.lean,\s*(\d+)\s*lines", text)
    lines = int(m.group(1)) if m else None

    m = re.search(r"OK:\s*(\d+)\s*theorem\(s\), none depends on", text)
    axioms_reported = int(m.group(1)) if m else None

    return {"theorems": theorems, "checked": checked, "errors": errors,
            "sorry": sorry, "lines": lines, "axioms_reported": axioms_reported}


def compare(measured: dict, said: dict) -> list[str]:
    out: list[str] = []
    pairs = [
        ("theorems", "theorem count"),
        ("checked", "theorems machine-checked"),
        ("errors", "errors remaining"),
        ("sorry", "sorry / admit / axiom"),
        ("lines", "Core.lean line count"),
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
    findings = compare(measured, said)

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