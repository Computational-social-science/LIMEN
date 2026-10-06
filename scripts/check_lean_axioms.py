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


def module_and_prefix(lean_file: pathlib.Path) -> tuple[str, str]:
    """The module to import and the namespace its theorems live in - BOTH READ FROM THE FILE.

    These were hardcoded to Core.lean's values (`import NHB.PhaseI.Core`, prefix `PhaseI.Selective`), which was
    correct for exactly one file. The moment the checker covered a second one, the query was built correctly
    and asked for theorems under the WRONG namespace, so Lean reported every one of them as an unknown
    constant - and the checker refused to interpret empty output as "axiom-free", which is why this was
    visible instead of silently passing.
    """
    stem = lean_file.stem
    module = f"NHB.PhaseI.{stem}"
    text = lean_file.read_text(encoding="utf-8")
    namespaces = re.findall(r"^namespace\s+(\S+)", text, re.M)
    return module, ".".join(namespaces)


def print_axioms(lean_file: pathlib.Path, lean_root: pathlib.Path,
                 prefix: str | None = None) -> dict[str, list[str]]:
    """Ask Lean itself which axioms each theorem depends on.

    `lean_root` is the project root (the directory holding lakefile.lean) and is passed in rather
    than derived: the first version computed `lean_file.parent.parent`, which for a file at
    the file at NHB/PhaseI/Core.lean lives two levels down, so `parent.parent` is `NHB/` and not
    the lean-nhb project root; LEAN_PATH pointed one level too deep
    and the import failed. Deriving a path from a file's location is only correct when you know how
    deep the file sits; here that is a property of the caller, not of the file.
    """
    module, found_prefix = module_and_prefix(lean_file)
    if prefix is None:
        prefix = found_prefix
    query = [f"import {module}"]
    for n in theorem_names(lean_file):
        query.append(f"#print axioms {prefix}.{n}" if prefix else f"#print axioms {n}")
    script = "\n".join(query) + "\n"

    scratch = lean_file.parent / "__axiom_query__.lean"
    scratch.write_text(script, encoding="utf-8")

    env = lean_env(lean_root)
    lake = lake_bin()

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


def lean_env(lean_root: pathlib.Path) -> dict:
    """The environment `lake` needs on this host, built in ONE place.

    `lake env lean` alone does NOT put the project's own build output on the search path, so
    `import NHB.PhaseI.Core` fails with "unknown module prefix" and the query returns NOTHING. Absent
    output reads exactly like "axiom-free" - a false green, which is the one failure mode this check
    exists to prevent. LEAN_PATH is therefore set explicitly to the build output, and an empty result
    raises rather than passing silently.
    """
    env = dict(os.environ)
    env["PATH"] = str(pathlib.Path.home() / ".elan" / "bin") + os.pathsep + env.get("PATH", "")
    env["LEAN_PATH"] = str(lean_root / ".lake" / "build" / "lib" / "lean")
    return env


def lake_bin() -> pathlib.Path:
    """`lake`, resolved by absolute path - never by PATH lookup, and never silently defaulted.

    On Windows the executable is `lake.exe`; asking for `lake` makes subprocess raise WinError 2,
    because PATH lookup there does not append PATHEXT. A first version of this check silently found NO
    axioms for every theorem, which reads exactly like "the proofs are axiom-free".

    THIS FUNCTION EXISTS BECAUSE THE SAME BUG SURVIVED IN A SECOND PLACE. `check` resolved the toolchain
    correctly, but the negative control called `subprocess.run(["lake", ...])` by bare name. That works
    only when the caller's PATH happens to contain elan - which is true in an interactive shell that
    exported it, and false in a fresh runner. The control therefore passed for a reason unrelated to what
    it was testing, and went red the moment the environment changed. A guard whose NEGATIVE CONTROL
    depends on the caller's environment stops validating without anyone noticing, which is worse than a
    guard that fails. Resolution now lives here and both callers use it.

    It raises rather than falling back to a bare name: if the toolchain is not where it is expected, the
    guard cannot validate anything, and it must say so instead of invoking whatever `lake` PATH offers.
    """
    candidates = (pathlib.Path.home() / ".elan" / "bin" / "lake.exe",
                  pathlib.Path.home() / ".elan" / "bin" / "lake")
    found = next((p for p in candidates if p.exists()), None)
    if found is None:
        raise RuntimeError(
            "no `lake` under ~/.elan/bin. The Lean toolchain is not where this host keeps it, so this "
            "check cannot run at all - and a check that cannot run must not report a green.")
    return found


def check(lean_root: pathlib.Path, lean_file: pathlib.Path, prefix: str = "NHB.PhaseI") -> list[str]:
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
        # Must rebuild so the olean reflects the sorry theorem, through the SAME resolved toolchain and
        # environment the check itself uses. Calling `lake` by bare name here is what made this control
        # depend on the caller's PATH.
        build = subprocess.run([str(lake_bin()), "build"], cwd=lean_root, env=lean_env(lean_root),
                               capture_output=True, text=True, timeout=600)
        if build.returncode != 0:
            tail = (build.stdout + build.stderr).strip()
            print("  [note] the injected sorry did not build, so the check below runs against a STALE "
                  "olean and its MISS is not evidence about the catch:")
            print("      " + (tail.splitlines()[-1][:150] if tail else "(no output)"))
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
    phase = root / "NHB" / "PhaseI"
    # EVERY KERNEL SOURCE, NOT ONE FILE. This checker read only Core.lean, so ScaleFree.lean - whose theorem
    # is the design justification for a pre-registered hypothesis, and whose zero-axiom status is the strongest
    # claim in the formalisation - was outside every guard. A claim that no check enforces is the defect class
    # this repository exists to prevent, and it had been sitting inside the repository's own verification path.
    sources = sorted(p for p in phase.glob("*.lean") if not p.name.startswith("__"))
    core = phase / "Core.lean"

    if not core.exists():
        print(f"[FAIL] {core} not found")
        return 1
    if not sources:
        print(f"[FAIL] no .lean source found under {phase}")
        return 1

    if args.negative_test:
        return negative_test(root)

    total = 0
    findings: list[str] = []
    per_file: list[tuple[pathlib.Path, int]] = []
    for f in sources:
        names = theorem_names(f)
        fs = check(root, f)
        per_file.append((f, len(names)))
        total += len(names)
        findings += [f"{f.name}: {x}" for x in fs]

    if findings:
        print(f"AXIOM FAIL: {len(findings)} finding(s) over {total} theorem(s) in {len(sources)} file(s)")
        for f in findings:
            print("  " + f)
        return 1

    # THE FIRST LINE IS A PARSE CONTRACT: three other scripts read `OK: N theorem(s), none depends on`.
    # Adding ` in 2 file(s)` in the middle of it broke all three at once - a checker whose output shape is
    # consumed elsewhere has an interface, and changing the interface is a change to every consumer.
    print(f"OK: {total} theorem(s), none depends on {FORBIDDEN}; "
          f"allowed axioms only {sorted(ALLOWED)}")
    for f, k in per_file:
        print(f"    {f.name}: {k} theorem(s), kernel-checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())