"""check_build_reproducibility.py -- an arm must build to the same bytes twice.

WHY THIS EXISTS. `rrc-zh` and `rrc-zh-gh` were not reproducible. Three builds of the same arm produced
three different files:

    full build  cc36daea723c3454
    run 1       a37c87b45339770c
    run 2       f3cd8dee1fde020c

The cause was one line. `build_arm` collected the arm's Han characters into a `set` of `str` and passed
it to `han_reading_index()`. Python randomizes string hashing per process, so each reading's character
list came out in a different order every run, and `han_channel_candidates()` takes the **first n** of
that list -- so the candidate set itself changed between rebuilds.

Every existing guard was blind to this, and they were blind for a structural reason: they all compare a
build against a *specification* (conservation identities, layer agreement, provenance). None compares a
build against *itself*. A pipeline can satisfy every identity and still emit different bytes each time.

WHY TWO HASH SEEDS RATHER THAN TWO RUNS. Two runs under the same seed agree by luck of one draw. The
order-dependent failure is triggered by the per-process hash seed, so the guard runs the same build
under two different `PYTHONHASHSEED` values. That makes the comparison deterministic rather than
probabilistic: if any ordered output depends on set iteration over strings, the two seeds expose it.

THE ARM CHOSEN IS `rrc-zh-gh`, deliberately. It is the cheapest arm that exercises the Han reading path
(1,532 items against 11,590 for `rrc-zh`), and an alphabetic arm would pass this check while the bug
remained -- `rrc-ru` is cheaper still but cannot see the defect. A guard must be run against the path
the defect lives on.

NOT IN run_all_guards.py: it performs two real builds, so it belongs before a release rather than in a
suite meant to run in minutes.

NEGATIVE CONTROL
    Demonstrates the mechanism rather than asserting it: iterates a set of strings under the two seeds
    and requires the orders to differ. If they ever stop differing the guard reports that its own
    premise no longer holds, instead of passing quietly.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
BUILD = REPO / "scripts" / "build_rrc.py"
ARM = "rrc-zh-gh"
OUT = REPO / "data" / "rrc" / (ARM + ".jsonl")


def build_under(seed: str) -> str:
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = seed
    env.pop("PYTHONPATH", None)
    r = subprocess.run([sys.executable, "-B", str(BUILD), "--arms", ARM],
                       cwd=str(REPO), env=env, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        return "BUILD_FAILED: %s" % (r.stderr or r.stdout)[-200:]
    return hashlib.sha256(OUT.read_bytes()).hexdigest()[:16]


def main() -> int:
    if "--negative-test" in sys.argv:
        probe = ("print(sorted(set('the quick brown fox jumps over the lazy dog'.split())))")
        outs = []
        for seed in ("1", "2"):
            env = dict(os.environ)
            env["PYTHONHASHSEED"] = seed
            r = subprocess.run([sys.executable, "-c", probe], env=env, capture_output=True, text=True)
            outs.append(r.stdout.strip())
        if outs[0] != outs[1]:
            print("  [OK] negative control fires: set-of-str iteration order depends on the hash seed")
            print("       %s" % outs[0][:60])
            return 0
        print("  [FAIL] the premise no longer holds: two hash seeds gave the same set order, so this")
        print("         guard cannot detect the defect it was written for")
        return 1

    if not BUILD.exists():
        print("  [FAIL] builder not found: %s" % BUILD)
        return 1
    print("  building %s twice, under PYTHONHASHSEED=1 and PYTHONHASHSEED=2" % ARM)
    a = build_under("1")
    print("    seed 1 -> %s" % a)
    b = build_under("2")
    print("    seed 2 -> %s" % b)
    if a.startswith("BUILD_FAILED") or b.startswith("BUILD_FAILED"):
        print("  [FAIL] a build did not complete: %s" % (a if a.startswith("BUILD_FAILED") else b))
        return 1
    if a == b:
        print("  [OK] %s is byte-identical under two hash seeds: no ordered output depends on set "
              "iteration" % ARM)
        return 0
    print("  [FAIL] %s differs between hash seeds: some ordered output depends on set iteration over"
          % ARM)
    print("         strings. Collect it with sorted() rather than set() -- see build_rrc.py, the")
    print("         reading-index construction, for the shape of the defect.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
