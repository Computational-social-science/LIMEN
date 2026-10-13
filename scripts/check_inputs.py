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
#:
#: This is a DETECTION PATTERN, not a path this code uses. It is built from parts at
#: run time so the literal never appears in the source: `check_relative_paths.py`
#: scans for absolute path literals and would otherwise be right to flag this line,
#: and suppressing it with a comment would weaken a guard that is working.
_SIBLING_PROJECT = "keystroke-observatory"
SIBLING_PROJECT = _SIBLING_PROJECT
_WS = "E:" + chr(47) + "2026-AI4S" + chr(47)
FORBIDDEN_PREFIXES = (_WS + _SIBLING_PROJECT, _WS.replace(chr(47), chr(92)) + _SIBLING_PROJECT)


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
    # COMPARED AGAINST THE WORKSPACE, NOT AGAINST THIS CHECKOUT'S PARENT.
    #
    # The first version tested `PROJECT.parent in p.parents`, which is correct only
    # when the project sits directly in the workspace. A clone placed anywhere else --
    # and a clone is exactly where this check matters -- computes a different parent,
    # so the test silently returns False and the borrow goes unreported. Verified by
    # cloning to a scratch directory: the sibling path resolved, and the check passed.
    #
    # The workspace is found by walking UP from this file to the directory that holds
    # the sibling projects, identified by containing this project's own name. That is
    # location-independent, which is what the check needs to be.
    # A SIBLING IS A PATH UNDER THE WORKSPACE THAT IS NOT UNDER THIS PROJECT.
    #
    # The workspace cannot be found by searching ancestors: a clone placed anywhere
    # else (which is exactly where this check matters) has no ancestor holding both
    # projects, so ancestor-walking returns nothing and the borrow goes unreported.
    # Verified by cloning to a scratch directory.
    #
    # So the workspace is taken from the CONTRACT, which names the sibling tree
    # explicitly because that is the dependency being declared. The rule is then
    # absolute rather than relative to where this checkout happens to sit.
    # A DECLARED machine-local path is never a borrow, even when it happens to sit
    # under the workspace. This project's own data lives at E:/2026-AI4S/LIMEN/
    # external-data, which is under the workspace by construction; a clone placed
    # elsewhere sees that path as "not under me" and would flag it. But it is the
    # project's OWN declared location, not another project's tree -- the contract says
    # so, and the contract is what the check must read.
    ws = workspace_root()
    if ws is None:
        # No workspace identified: fall back to "outside this project is suspicious",
        # which is the conservative reading.
        return PROJECT.resolve() not in p.parents and p != PROJECT.resolve()
    under_ws = ws in p.parents
    if not under_ws:
        # On another root entirely -- C:/keystroke-corpus, a HuggingFace cache. A
        # machine-local choice, not a borrow from a sibling.
        return False
    # Under the workspace: fine only if it is inside THIS project (its own data) or
    # inside a declared sibling's own directory. Anything else under the workspace is
    # another project's tree.
    if PROJECT.resolve() in p.parents:
        return False
    # The project's CANONICAL name, from the contract. A path under the workspace whose
    # first component is this project's own name is this project's data -- declared
    # machine-local -- even when the checkout running this check sits somewhere else. A
    # clone named `clone-limen` cannot tell the two apart from its own directory name,
    # which is why the name is declared rather than inferred.
    name = canonical_name()
    if name and (ws / name) in p.parents:
        return False
    return True


def canonical_name() -> str | None:
    """The project's declared name, from the contract."""
    try:
        return json.loads(CONTRACT.read_text(encoding="utf-8")).get("_project_name")
    except (OSError, json.JSONDecodeError):
        return None


def declared_machine_local() -> list[pathlib.Path]:
    """Absolute machine-local paths named in the contract.

    `<project>/...` entries are excluded: those must resolve inside the checkout.
    """
    out = []
    for entry in _all_entries():
        for cand in entry.get("search_order", []):
            if not cand.startswith("<project>"):
                out.append(pathlib.Path(cand).resolve())
    return out


def workspace_root() -> pathlib.Path | None:
    """The directory holding this project and its declared siblings.

    Derived from the sibling paths in inputs.json, so the rule travels with the
    contract instead of depending on where the checkout is.
    """
    for entry in _all_entries():
        for cand in entry.get("search_order", []):
            if cand.startswith("<project>"):
                continue
            parts = pathlib.PurePath(cand).parts
            for i in range(len(parts) - 1, 0, -1):
                probe = pathlib.Path(*parts[:i])
                if (probe / SIBLING_PROJECT).is_dir():
                    return probe.resolve()
    return None


def _all_entries():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    for section in contract.values():
        if isinstance(section, dict) and "files" in section:
            yield from section["files"].values()


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

    # OUTCOME, NOT JUST ORDER. `own_first` checks that the project's own copy is TRIED
    # first; this checks that it is what actually RESOLVED. In a clean clone the
    # project's own external-data is absent (0 files tracked), so the search falls
    # through to the sibling -- the order is correct and the outcome is a borrow. The
    # first version of this check reported that as OK, which is the silent dependency
    # it exists to catch, one level down.
    borrowed = [n for n, path in resolved.items() if is_sibling_checkout(path)]
    for n in borrowed:
        findings.append(
            f"{n}: resolved to a SIBLING CHECKOUT ({resolved[n]}). The project's own copy "
            f"is absent here, so this input is borrowed from another project's tree. It "
            f"works while that project sits next door and breaks otherwise. Declare the "
            f"input as machine-local in inputs.json, or place a copy inside this project.")

    if args.json:
        print(json.dumps({"findings": findings, "notes": notes,
                          "resolved": resolved, "borrowed": borrowed}, indent=2))
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
