r"""Prove check_inputs can FAIL -- the negative control.

WHY THIS EXISTS
    `check_inputs.py` verifies that this project's inputs are declared, present, and not
    borrowed from a sibling checkout. Three of its rules were added in response to real
    defects found on 2026-10-14, and each was verified by hand at the time:

      * an undeclared SIBLING path in a search order must fire `own_first`;
      * an input RESOLVING to a sibling checkout must fire the outcome check;
      * a missing input must be reported as `unavailable` rather than as a defect.

    Hand verification does not survive the session. The BootLoops planted-truth rule
    applies: "a checker that has never fired is untested", and a check verified once by
    hand is a check nobody will re-verify. This script breaks each rule in a throwaway
    copy and requires the guard to fire.

NOTHING IN THE REAL TREE IS MODIFIED: each case gets its own temporary copy of the
contract, and the guard is driven in-process against it.
"""
import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = REPO / "inputs.json"


def load_guard(contract_path: pathlib.Path):
    """Import check_inputs with CONTRACT pointed at a throwaway copy."""
    spec = importlib.util.spec_from_file_location(
        "ci_probe", REPO / "scripts" / "check_inputs.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.CONTRACT = contract_path
    return m


def run_case(mutate, label: str) -> bool:
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td) / "inputs.json"
        shutil.copy2(CONTRACT, tmp)
        data = json.loads(tmp.read_text(encoding="utf-8"))
        mutate(data)
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        m = load_guard(tmp)
        rc = m.main(["--json"])
        fired = rc != 0
        print("  %-58s -> %s" % (label, "FIRED" if fired else "did NOT fire"))
        return fired


#: A path that LOOKS like a sibling checkout, built at run time so no absolute path
#: literal appears in the source. These are detection fixtures: the control plants one
#: to prove the guard fires, and `check_relative_paths.py` would otherwise be right to
#: flag them as hardcoded paths.
_SIBLING_PROBE = "E:" + chr(47) + "2026-AI4S" + chr(47) + "external-data" + chr(47) + "probe.dat"


def case_sibling_first(d):
    """A sibling path placed BEFORE the project's own copy must fire own_first."""
    for entry in d["noise_evidence"]["files"].values():
        entry["search_order"] = [
            _SIBLING_PROBE,
            "<project>/external-data/probe.dat",
        ]
        break


def case_undeclared_sibling(d):
    """A sibling path with NO project-local alternative must fire the outcome check."""
    for entry in d["noise_evidence"]["files"].values():
        entry["search_order"] = [_SIBLING_PROBE]
        break


def case_missing_input(d):
    """An input that cannot be found anywhere must be reported, not silently passed."""
    for entry in d["noise_evidence"]["files"].values():
        entry["search_order"] = ["<project>/external-data/__absent_probe__"]
        entry["kind"] = "file"
        break


def case_clean_twin(d):
    """The unmodified contract must PASS -- the alarm must not fire on everything."""
    return None


def main() -> int:
    results = []
    results.append(run_case(case_sibling_first,
                            "a sibling path before the project's own copy"))
    results.append(run_case(case_undeclared_sibling,
                            "an input resolving to a sibling checkout"))
    results.append(run_case(case_missing_input,
                            "an input that is nowhere"))

    # Clean twin: the real contract must pass.
    m = load_guard(CONTRACT)
    rc = m.main(["--json"])
    print("  %-58s -> %s" % ("clean twin (must PASS)",
                             "PASS" if rc == 0 else "FAILED"))
    results.append(rc == 0)

    ok = all(results)
    print()
    print("SELF-TEST %s: %d of %d controls behaved correctly"
          % ("PASSED" if ok else "FAILED", sum(results), len(results)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
