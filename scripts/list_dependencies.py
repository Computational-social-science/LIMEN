r"""Derive the project's third-party imports from its own source.

WHY THIS EXISTS
    There is no dependency manifest in this repository. That is not merely untidy:
    `qc_stage2_figures.py` claims to audit "the figures that are actually written",
    but with `scienceplots` absent it silently fell back to the default matplotlib
    style and audited a DIFFERENT render -- a 276 KB re-generation against the 287 KB
    shipped file -- then reported a label collision the shipped figure does not have.
    A missing dependency became a wrong audit rather than an error, because nothing
    recorded that the dependency was needed.

    So the list is DERIVED rather than hand-written. A hand-written list drifts from
    the code; a derived one cannot. Run with --write to refresh requirements.txt.
"""
from __future__ import annotations

import argparse
import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCAN_DIRS = ["scripts", "measurement"]

#: Import name -> distribution name, where they differ. Kept explicit rather than
#: guessed, because a wrong mapping produces a requirements file that cannot install.
DIST_OVERRIDES = {
    "PIL": "Pillow",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
    "fitz": "PyMuPDF",
    "docx": "python-docx",
    "pptx": "python-pptx",
    "laya": "laya",
}

#: Imports that are this repository's own modules or the standard library. The
#: standard-library check is done by asking the interpreter, not by a list.
def stdlib_names() -> set[str]:
    return set(sys.stdlib_module_names)


def local_modules() -> set[str]:
    names = {p.stem for p in (ROOT / "scripts").glob("*.py")}
    names |= {p.stem for p in (ROOT / "measurement").glob("*.py")}
    names |= {p.name for p in ROOT.iterdir() if p.is_dir() and (p / "__init__.py").exists()}
    return names


def imported_modules() -> dict[str, set[str]]:
    """{top-level module: {files importing it}} for third-party imports only."""
    std, local = stdlib_names(), local_modules()
    found: dict[str, set[str]] = {}
    for d in SCAN_DIRS:
        for p in sorted((ROOT / d).rglob("*.py")):
            try:
                tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                mods = []
                if isinstance(node, ast.Import):
                    mods = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    mods = [node.module]
                for m in mods:
                    top = m.split(".")[0]
                    if top in std or top in local or top.startswith("_"):
                        continue
                    found.setdefault(top, set()).add(p.relative_to(ROOT).as_posix())
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="refresh requirements.txt")
    ap.add_argument("--check", action="store_true",
                    help="fail if requirements.txt has drifted from the source")
    args = ap.parse_args()

    mods = imported_modules()
    lines = [
        "# Third-party dependencies, DERIVED from the source by scripts/list_dependencies.py.",
        "# Do not hand-edit: a hand-written list drifts from the code, and a drifted list is",
        "# how qc_stage2_figures came to audit a render the project does not ship.",
        "#",
        "# The interpreter is pinned separately by .guard-python.",
        "",
    ]
    for top in sorted(mods):
        lines.append(DIST_OVERRIDES.get(top, top))
    text = "\n".join(lines) + "\n"

    print(f"  {len(mods)} third-party module(s) imported across scripts/ and measurement/:")
    for top in sorted(mods):
        dist = DIST_OVERRIDES.get(top, top)
        where = sorted(mods[top])
        note = f"  (import {top})" if dist != top else ""
        print(f"    {dist:<20}{note}  {len(where)} file(s)")

    out = ROOT / "requirements.txt"
    if args.write:
        out.write_text(text, encoding="utf-8")
        print(f"\n  wrote {out.relative_to(ROOT).as_posix()}")
        return 0

    if args.check:
        # Drift in either direction is a finding. A missing entry is the defect that
        # produced the wrong audit; an extra entry is a dependency the code no longer
        # needs, which will be installed forever by anyone who trusts this file.
        if not out.exists():
            print("\n  [FAIL] requirements.txt does not exist; run with --write")
            return 1
        committed = [l.strip() for l in out.read_text(encoding="utf-8").splitlines()
                     if l.strip() and not l.strip().startswith("#")]
        expected = [DIST_OVERRIDES.get(m, m) for m in sorted(mods)]
        missing = [d for d in expected if d not in committed]
        extra = [d for d in committed if d not in expected]
        if missing or extra:
            print("\n  [FAIL] requirements.txt has drifted from the source:")
            for d in missing:
                print(f"    MISSING  {d}  (imported but not declared -- a missing")
                print(f"             dependency makes a guard audit the wrong artefact)")
            for d in extra:
                print(f"    EXTRA    {d}  (declared but never imported)")
            return 1
        print(f"\n  [OK] requirements.txt matches the {len(expected)} module(s) the "
              f"source imports")
        return 0

    print("\n  (dry run; pass --write to refresh requirements.txt)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
