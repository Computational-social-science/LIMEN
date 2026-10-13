r"""check_inputs.py -- LIMEN's declared inputs are present, correct and not borrowed.

WHY THIS EXISTS
    LIMEN is an independent project, but its inputs are large third-party corpora and a
    pinned model, none of which can be tracked in git. So independence has to mean
    three things, and this script is all three:

      1. DECLARED. `inputs.json` states every input, its expected size and hash, and
         where to look. A reader can obtain the data without reading the code.

      2. VERIFIED. Existence, byte count and sha256. A file that is present but WRONG
         is worse than one that is missing, because the analysis would use it and every
         number derived from it would carry a false provenance claim.

      3. NOT BORROWED. Where an input exists both inside this project and in a sibling
         directory, the project's own copy must come first in the search order. Three
         scripts resolved `external-data` as `REPO_ROOT.parent / "external-data"` --
         E:\2026-AI4S\external-data, a DIFFERENT tree (1.1 GB) from LIMEN's own
         (21.4 GB). It worked only because both happen to hold the same three datasets.
         That is the failure this check exists for: correct output, wrong reason, and
         nothing to notice it by.

USAGE
    python scripts/check_inputs.py
    python scripts/check_inputs.py --json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

PROJECT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = PROJECT / "inputs.json"

#: A sibling checkout's directory is not this project's input. LIMEN's own
#: external-data/ is fine; a path into another PROJECT is not.
FORBIDDEN_PREFIXES = ("E:/2026-AI4S/keystroke-observatory", "E:\\2026-AI4S\\keystroke-observatory")


def sha256_file(path: pathlib.Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def expand(p: str) -> pathlib.Path:
    if p.startswith("<project>"):
        return PROJECT / p[len("<project>/"):]
    return pathlib.Path(p)


def resolve(entry: dict) -> pathlib.Path | None:
    for cand in entry["search_order"]:
        path = expand(cand)
        if entry["kind"] == "directory":
            if path.is_dir() and any(path.glob(entry.get("pattern", "*"))):
                return path
        elif path.is_file():
            return path
    return None


def is_sibling_checkout(cand: str) -> bool:
    """True when a path points into a DIFFERENT project sitting beside this one.

    Two kinds of non-project path look identical in a search order, and conflating them
    makes the guard fire on correct behaviour:

      * a MACHINE-LOCAL data root -- `C:/keystroke-corpus/files`. The corpus lives on the
        NVMe disk because E: is USB-attached and concurrent reads thrash it. Legitimate,
        deliberate, and on an entirely different root.
      * a SIBLING CHECKOUT -- `E:/2026-AI4S/external-data`, i.e. under the same parent
        directory as this project but not inside it. That is another project's tree. It
        works only while both sit side by side, and it breaks silently.

    The distinction is the parent directory: a path under PROJECT.parent that is not
    under PROJECT is a sibling. A path on another root is a machine-local choice.
    """
    if cand.startswith("<project>"):
        return False
    try:
        p = pathlib.Path(cand).resolve()
    except OSError:
        return False
    parent = PROJECT.parent.resolve()
    return parent in p.parents and PROJECT.resolve() not in p.parents and p != PROJECT.resolve()


def own_first(entry: dict, findings: list[str], name: str) -> None:
    """The project's own copy must be tried before any SIBLING copy."""
    order = entry.get("search_order", [])
    first_own = next((i for i, c in enumerate(order) if c.startswith("<project>")), None)
    first_sib = next((i for i, c in enumerate(order) if is_sibling_checkout(c)), None)
    if first_own is not None and first_sib is not None and first_sib < first_own:
        findings.append(
            f"{name}: the search order tries a SIBLING CHECKOUT ({order[first_sib]}) "
            f"before the project's own copy. A lookup that succeeds from a sibling breaks "
            f"when the sibling moves, and it breaks silently.")


def verify_entry(name: str, entry: dict, findings: list[str], notes: list[str],
                 resolved: dict[str, str]) -> None:
    path = resolve(entry)
    if path is None:
        tried = "\n".join(f"           {c}" for c in entry["search_order"])
        findings.append(f"{name}: NOT FOUND -- {entry['description']}\n         searched:\n{tried}")
        return
    resolved[name] = str(path)

    if entry["kind"] == "directory":
        got = len(list(path.glob(entry.get("pattern", "*"))))
        want = entry.get("expected_count")
        if want is not None and got != want:
            findings.append(f"{name}: {path} holds {got} matching entries, expected {want}")
        else:
            notes.append(f"{name}: {path} -- {got} entries")
        return

    size = path.stat().st_size
    if "bytes" in entry and size != entry["bytes"]:
        findings.append(f"{name}: {path} is {size:,} bytes, expected {entry['bytes']:,}")
        return
    if "sha256" in entry:
        got = sha256_file(path)
        if got != entry["sha256"]:
            findings.append(f"{name}: {path} sha256 {got[:16]}..., expected {entry['sha256'][:16]}...")
            return
    notes.append(f"{name}: {path} -- {size:,} bytes")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if not CONTRACT.exists():
        print(f"  [FAIL] {CONTRACT.name} is absent -- the inputs are not declared")
        return 1
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    findings: list[str] = []
    notes: list[str] = []
    resolved: dict[str, str] = {}

    text = CONTRACT.read_text(encoding="utf-8")
    for pref in FORBIDDEN_PREFIXES:
        if pref in text:
            findings.append(
                f"inputs.json names another project's directory ({pref}). An input "
                f"reached from a sibling checkout is not this project's input.")

    for section in contract.values() if isinstance(contract, dict) else []:
        if not isinstance(section, dict) or "files" not in section:
            continue
        for name, entry in section["files"].items():
            own_first(entry, findings, name)
            verify_entry(name, entry, findings, notes, resolved)

    if args.json:
        print(json.dumps({"findings": findings, "notes": notes, "resolved": resolved}, indent=2))
        return 1 if findings else 0

    for n in notes:
        print(f"  OK    {n}")
    if findings:
        print(f"\n  [FAIL] {len(findings)} input finding(s):")
        for f in findings:
            print(f"    {f}")
        return 1
    print(f"\n  [OK] all {len(notes)} declared input(s) present, and each search order "
          f"tries the project's own copy first")
    return 0


if __name__ == "__main__":
    sys.exit(main())
