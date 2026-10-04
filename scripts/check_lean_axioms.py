#!/usr/bin/env python
"""check_lean_axioms.py -- prove the Lean file is honest, not merely sorry-free.

WHY GREP IS NOT ENOUGH
    `grep sorry` proves a string is absent. It does not prove a theorem is proved. A Lean file can be
    free of the literal words and still carry an unproven term through `sorryAx`, and a theorem can be
    closed with `by omega` when `omega` was never actually given the hypothesis it needed. Those are
    the two ways this project's formalisation could lie while looking clean, so neither is the check.

WHAT THIS CHECKS
    It runs Lean's own `#print axioms` on every theorem in the file and fails if any of them depends
    on `sorryAx`. That is Lean's own accounting: a theorem proved by `sorry` is reported as depending
    on sorryAx, and a theorem proved by hand is not. There is no way to be fooled by renaming a
    tactic here, because the reporting is done by the kernel, not by a pattern match.

THE ALLOWED DEPENDENCIES, AND WHY
    `propext`, `Classical.choice` and `Quot.sound` are Lean's three standard axioms. They come with
    the kernel and are what every ordinary Lean proof uses; nothing here calls `Classical`, so
    `Classical.choice` is not expected but is allowed. The point of the check is not to forbid
    axioms - it is to forbid the ONE axiom that means "this was never proved".

NEGATIVE CONTROL
    `--negative-test` injects a scratch file containing a `sorry`-proved theorem and requires the
    check to fire on it, then removes the scratch file. A guard that has never failed is not a guard.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LEAN_ENV = pathlib.Path.home() / ".elan" / "bin"
FORBIDDEN = "sorryAx"
ALLOWED = {"propext", "Classical.choice", "Quot.sound"}


def theorem_names(lean_file: pathlib.Path) -> list[str]:
    """The fully-qualified names of every top-level theorem, in file order."""
    names = []
    for line in lean_file.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^theorem\s+([A-Za-z_][A-Za-z0-9_']*)", line)
        if m:
            names.append(m.group(1))
    return names


def print_axioms(lean_file: pathlib.Path, lean_root: pathlib.Path,
                 prefix: str = "PhaseI.Selective") -> dict[str, list[str]]:
    """Ask Lean itself which axioms each theorem depends on.

    `lean_root` is the project root (the directory holding lakefile.lean) and is passed in rather
    than derived: the first version computed `lean_file.parent.parent`, which for a file at
    the file at NHB/PhaseI/Core.lean lives two levels down, so `parent.parent` is `NHB/` and not
    the lean-nhb project root; LEAN_PATH pointed one level too deep
    and the import failed. Deriving a path from a file's location is only correct when you know how
    deep the file sits; here that is a property of the caller, not of the file.
    """
    query = ["import NHB.PhaseI.Core"]  # the lean-nhb module
    for n in theorem_names(lean_file):
        query.append(f"#print axioms {prefix}.{n}")
    script = "\n".join(query) + "\n"

    scratch = lean_file.parent / "__axiom_query__.lean"
    scratch.write_text(script, encoding="utf-8")

    env = dict(os.environ)
    elan_bin = pathlib.Path.home() / ".elan" / "bin"
    env["PATH"] = str(elan_bin) + os.pathsep + env.get("PATH", "")
    # `lake env lean` alone does NOT put the project's own build output on the search path, so
    # `import NHB.PhaseI.Core` fails with "unknown module prefix" and the query returns NOTHING.
    # Absent output reads exactly like "axiom-free" - a false green, which is the one failure mode
    # this check exists to prevent. Two things guard against it here: LEAN_PATH is set explicitly to
    # the build output, and an empty result raises rather than passing silently.
    env["LEAN_PATH"] = str(lean_root / ".lake" / "build" / "lib" / "lean")

    # On Windows the executable is `lake.exe`; asking for `lake` makes subprocess raise WinError 2,
    # because PATH lookup there does not append PATHEXT. A first version of this check silently found
    # NO axioms for every theorem - which reads exactly like "the proofs are axiom-free" unless you
    # notice the count, and would have let a sorry through.
    lake = next((p for p in (elan_bin / "lake.exe", elan_bin / "lake") if p.exists()),
                pathlib.Path("lake"))

    try:
        proc = subprocess.run(
            [str(lake), "env", "lean", str(scratch)], capture_output=True, text=True,
            cwd=lean_root, env=env, shell=False)
    finally:
        scratch.unlink(missing_ok=True)

    out = proc.stdout + proc.stderr
    if "depends on" not in out and "does not depend on" not in out:
        raise RuntimeError(
            f"`{lake} env lean` returned no `#print axioms` lines (rc={proc.returncode}). The check "
            f"would report every theorem as axiom-free by ABSENCE OF EVIDENCE, which is how a sorry "
            f"would slip through. Output was:\n{out[:800]}")

    # TWO WORDINGS, AND THE SECOND ONE MATTERS. Lean prints
    #     'name' depends on axioms: [propext, Quot.sound]
    # but for a theorem proved by `decide` with no classical reasoning it instead prints
    #     'name' does not depend on any axioms
    # A regex matching only the first form classifies the cleanest possible result as "not covered",
    # which is what happened here: protocol_said_nondecreasing_is_FALSE is a `decide` theorem, it was
    # reported as unmeasured, and the guard was reporting a gap that did not exist.
    result = {}
    for m in re.finditer(r"'([\w.]+)' depends on axioms: \[([^\]]*)\]", out):
        name = m.group(1).rsplit(".", 1)[-1]
        deps = [d.strip() for d in m.group(2).split(",") if d.strip()]
        result[name] = deps
    for m in re.finditer(r"'([\w.]+)' does not depend on any axioms", out):
        result.setdefault(m.group(1).rsplit(".", 1)[-1], [])
    return result


def check(lean_root: pathlib.Path, lean_file: pathlib.Path) -> list[str]:
    deps = print_axioms(lean_file, lean_root)
    names = theorem_names(lean_file)
    findings = []

    for n in names:
        if n not in deps:
            findings.append(f"[AX] {n}: Lean reported NO axioms at all - the file did not parse "
                            f"for this name, so the check did not actually cover it")
    for n, d in deps.items():
        if FORBIDDEN in d:
            findings.append(f"[AX] {n}: depends on {FORBIDDEN} - the theorem is NOT proved")
        extra = [x for x in d if x not in ALLOWED]
        if extra:
            findings.append(f"[AX] {n}: depends on unexpected axioms {extra}")

    return findings


def negative_test(lean_root: pathlib.Path) -> int:
    """Inject a sorry-proved theorem and require the check to catch it."""
    scratch = lean_root / "NHB" / "PhaseI" / "__axiom_negative_control__.lean"
    orig = (lean_root / "NHB" / "PhaseI" / "Core.lean").read_text(encoding="utf-8")
    print("negative control:")
    ok = True

    try:
        # 1. The real file must pass.
        f = check(lean_root, lean_root / "NHB" / "PhaseI" / "Core.lean")
        r1 = ("real file has no sorryAx dependency", not f)
        print(f"  [{'OK' if r1 else 'MISS'}] {r1}")
        ok = ok and r1

        # 2. A sorry-proved theorem must be caught. Written into the real file so that the import
        #    and the namespace resolve exactly as they do in production - a separate file would
        #    need its own module wiring and could fail for the wrong reason.
        (lean_root / "NHB" / "PhaseI" / "Core.lean").write_text(
            orig + "\ntheorem __neg_control__ : True := by sorry\n", encoding="utf-8")
        f2 = check(lean_root, lean_root / "NHB" / "PhaseI" / "Core.lean")
        r2 = ("a sorry-proved theorem is caught", any("__neg_control__" in x for x in f2))
        print(f"  [{'OK' if r2 else 'MISS'}] {r2}")
        ok = ok and r2
        if not r2:
            for x in f2[:4]:
                print("      " + x)
    finally:
        (lean_root / "NHB" / "PhaseI" / "Core.lean").write_text(orig, encoding="utf-8")
        if scratch.exists():
            scratch.unlink()

    restored = (lean_root / "NHB" / "PhaseI" / "Core.lean").read_text(encoding="utf-8") == orig
    r3 = ("real file restored", restored)
    print(f"  [{'OK' if r3 else 'MISS'}] {r3}")
    ok = ok and r3

    print(f"\n  {'ALL CONTROLS PASS' if ok else 'CONTROL FAILURE - the guard is not trustworthy'}")
    return 0 if ok else 1


def resolve_lean_root(explicit: str | None) -> pathlib.Path:
    """Locate the Lean project without hardcoding a drive letter.

    Order: explicit argument, then $NHB_LEAN_ROOT, then the sibling directory next to this
    repository. An earlier version hardcoded the drive-qualified lean-nhb path as the argparse
    default, which the project's own relative-path guard correctly flagged: a hardcoded absolute path
    in code breaks the moment the tree is cloned anywhere else, and this script ships in the repo.
    Describing the defect without repeating the literal also keeps the guard from firing on this file.
    """
    if explicit:
        return pathlib.Path(explicit)
    env = os.environ.get("NHB_LEAN_ROOT")
    if env:
        return pathlib.Path(env)
    return REPO_ROOT.parent / "lean-nhb"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lean-root", default=None,
                    help="the Lean project root (the directory containing lakefile.lean). "
                         "Default: $NHB_LEAN_ROOT, else ../lean-nhb relative to this repository. "
                         "No absolute path is hardcoded - a project that moves must not need an edit.")
    ap.add_argument("--negative-test", action="store_true")
    args = ap.parse_args()

    root = pathlib.Path(resolve_lean_root(args.lean_root)).resolve()
    core = root / "NHB" / "PhaseI" / "Core.lean"

    if not core.exists():
        print(f"[FAIL] {core} not found")
        return 1

    if args.negative_test:
        return negative_test(root)

    n = theorem_names(core)
    findings = check(root, core)
    if findings:
        print(f"AXIOM FAIL: {len(findings)} finding(s) over {len(n)} theorem(s)")
        for f in findings:
            print("  " + f)
        return 1

    print(f"OK: {len(n)} theorem(s), none depends on {FORBIDDEN}; "
          f"allowed axioms only {sorted(ALLOWED)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())