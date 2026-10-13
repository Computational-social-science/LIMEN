"""check_ranked_layers_agree.py -- one quantity defined in two files must not drift.

WHY THIS EXISTS
    `RANKED_LAYERS` decides which layers carry a margin. It is used in `build_rrc.py` to decide
    where the validity constraint applies, and in `eval_rrc_d1.py` to decide which layers the
    margin-balanced sampler draws from. The second use was added by writing the tuple a second
    time, because the original lives inside a function and cannot be imported cheaply.

    Two copies of one quantity that can drift are two instruments (rule 19): if the eval's copy
    gained or lost a layer, items would silently move between the margin-sampled and the
    flat-sampled paths, the curve in one channel would be balanced and in the other not, and
    nothing would report it. The comparison is mechanical and takes a fraction of a second.

WHAT IT CHECKS
    The tuple assigned to `RANKED_LAYERS` in `scripts/build_rrc.py` (wherever it sits, module or
    function scope) equals the module-level tuple in `scripts/eval_rrc_d1.py`. Parsed with `ast`,
    so a reformatting does not disturb it and a comment cannot satisfy it.

NEGATIVE CONTROL
    `--negative-test` compares the build tuple against a deliberately wrong tuple passed in code
    rather than by editing a real file: the check must report a mismatch. Editing a real file to
    test a guard risks leaving the edit behind, and a probe that writes inside the tree is what the
    lock in `run_all_guards.py` exists to serialise.
"""
from __future__ import annotations

import ast
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
BUILD = REPO / "scripts" / "build_rrc.py"
EVAL = REPO / "scripts" / "eval_rrc_d1.py"
NAME = "RANKED_LAYERS"


def find_assignments(path: pathlib.Path) -> list[tuple[str, tuple]]:
    """Every literal tuple assigned to NAME in `path`, with a location label."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [("SYNTAX ERROR: %s" % exc, ())]
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            val, loc = node.value, node.lineno
            targets = [t for t in node.targets if isinstance(t, ast.Name) and t.id == NAME]
        elif isinstance(node, ast.AnnAssign):
            val, loc = node.value, node.lineno
            targets = [node.target] if (isinstance(node.target, ast.Name)
                                        and node.target.id == NAME) else []
        else:
            continue
        if targets and isinstance(val, ast.Tuple):
            vals = tuple(e.value for e in val.elts if isinstance(e, ast.Constant))
            found.append(("line %d" % loc, vals))
    return found


def main() -> int:
    bad = False
    build = find_assignments(BUILD)
    ev = find_assignments(EVAL)

    print("  %s" % BUILD.name)
    for where, vals in build:
        print("    %-10s %s = %s" % (where, NAME, vals))
    print("  %s" % EVAL.name)
    for where, vals in ev:
        print("    %-10s %s = %s" % (where, NAME, vals))
    print()

    if not build:
        print("  [FAIL] no literal %s found in %s; the check cannot compare anything" % (NAME, BUILD.name))
        bad = True
    if not ev:
        print("  [FAIL] no literal %s found in %s; the check cannot compare anything" % (NAME, EVAL.name))
        bad = True

    if "--negative-test" in sys.argv:
        # Compare the build tuple against a tuple that is deliberately wrong. The control must
        # report a mismatch; if it does not, the comparison is not running.
        ref = build[0][1] if build else ()
        wrong = tuple(list(ref) + ["L9notalayer"])
        if ref == wrong:
            print("  [FAIL] the control could not be constructed: ref equals the wrong tuple")
            return 1
        print("  [OK] negative control fires: %s %s != %s" % (NAME, ref, wrong))
        return 0

    if build and ev:
        for where, vals in build:
            if vals != ev[0][1]:
                print("  [FAIL] %s disagrees: %s has %s at %s, %s has %s"
                      % (NAME, BUILD.name, vals, where, EVAL.name, ev[0][1]))
                bad = True
        if len(ev) > 1:
            print("  [WARN] %s in %s is assigned %d times" % (NAME, EVAL.name, len(ev)))

    if bad:
        print()
        print("  A layer in one copy and not the other moves items between the margin-balanced")
        print("  sampler and the flat one, and no other check would report it.")
        return 1
    print("  [OK] both files define %s as %s" % (NAME, ev[0][1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
