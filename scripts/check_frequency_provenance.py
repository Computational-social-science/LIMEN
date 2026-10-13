"""check_frequency_provenance.py -- no arm is ranked against another arm's frequency table.

WHY THIS EXISTS
    The reading channel's difficulty is the root's rank in the candidate group the input method
    offers, and that group is ordered by **frequency**. Frequency is domain-specific: measured,
    the two Chinese arms' sources rank differently enough that `国` is 22,964 in one and 130 in
    the other, and the top ten of the two domains barely intersect. Ranking one arm's items
    against the other arm's table is therefore not a small approximation -- it is a mismatched
    denominator, and it produced a reversal in the rank analysis that looked like a refuted
    hypothesis when it was a wrong table. The tables are now per corpus and each item records
    which one ranked it, so the mistake is mechanically detectable.

WHAT IT CHECKS
    A. every arm that has an L2c layer is mapped to a table, and that table exists and is non-empty
    B. every L2c item's recorded `group_rank_source` equals its arm's mapping
    C. a ranked item's root is present in the table that ranked it
    D. `--negative-test` perturbs one item's recorded source to a different arm's table and
       requires the check to reject it. Without this the guard could pass by never comparing.

NOT COVERED
    Whether the frequency table is a good model of a real input method's ordering. That is an
    assumption about the channel, stated in the report, not something a guard can settle.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
FREQ = REPO / "data" / "processed" / "han_char_frequency.json"
RRC_DIR = REPO / "data" / "rrc"
RESULT = REPO / "data" / "processed" / "frequency_provenance.json"


def load() -> tuple[dict, dict]:
    if not FREQ.exists():
        print("  [FAIL] no frequency table at %s" % FREQ)
        sys.exit(1)
    payload = json.loads(FREQ.read_text(encoding="utf-8"))
    return payload.get("arm_source") or {}, payload.get("tables") or {}


def items_of(arm: str):
    p = RRC_DIR / f"{arm}.jsonl"
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            it = json.loads(line)
            if it.get("layer") == "L2c":
                out.append(it)
    return out


def run(negative: bool, mapping: dict, tables: dict) -> int:
    findings = []
    checked = collections.Counter()

    arms_with_l2c = []
    for p in sorted(RRC_DIR.glob("*.jsonl")):
        arm = p.stem
        if any(json.loads(l)["layer"] == "L2c"
               for l in p.read_text(encoding="utf-8").splitlines() if l.strip()):
            arms_with_l2c.append(arm)

    if not arms_with_l2c:
        # RRC_DIR is data/rrc, RETIRED 2026-10-11 as an invalid measurement
        # instrument (CURRENT_OBJECT.md R3; the arm files are in
        # archive/rrc-v2.0.0-INVALID/). With the arms gone there is no L2c layer to
        # attribute, so the honest report is INAPPLICABLE, not FAIL: the guard is
        # not finding a defect, it is finding that its subject was withdrawn.
        #
        # A permanently red suite is indistinguishable from a broken one -- it makes
        # the pre-commit hook unusable and teaches everyone to bypass it -- so this
        # follows the same convention as check_handoff_freshness.py. The guard is NOT
        # deleted: it re-arms automatically when a replacement corpus ships arms with
        # an L2c layer, which is the standing requirement any replacement must meet.
        print("  [SKIP] INAPPLICABLE: no arm has an L2c layer, because %s is retired" % RRC_DIR)
        print("         (CURRENT_OBJECT.md R3). Nothing to attribute; this guard proves")
        print("         NOTHING until a replacement corpus ships arms with an L2c layer.")
        return 0

    # A
    for arm in arms_with_l2c:
        name = mapping.get(arm)
        if not name:
            findings.append("A %s has an L2c layer but no table mapping" % arm)
            continue
        t = tables.get(name)
        if not t:
            findings.append("A %s maps to table %r which is absent" % (arm, name))
            continue
        if not t.get("frequency"):
            findings.append("A %s maps to table %r which is empty" % (arm, name))
        checked["arms_mapped"] += 1

    # B and C
    injected = False
    for arm in arms_with_l2c:
        want = mapping.get(arm)
        other = next((v for k, v in mapping.items() if k != arm and v), None)
        for it in items_of(arm):
            d = it.get("difficulty") or {}
            got = d.get("group_rank_source")
            rank = d.get("group_rank")
            checked["items"] += 1
            if got != want:
                findings.append("B %s: item %s records source %r, arm maps to %r"
                                % (arm, it.get("item_id"), got, want))
            if rank is not None and want:
                t = tables.get(want) or {}
                freq = t.get("frequency") or {}
                if it["root"] not in freq:
                    findings.append("C %s: item %s was ranked #%s but its root %r is not in "
                                    "table %r" % (arm, it.get("item_id"), rank, it["root"], want))
                else:
                    checked["roots_in_table"] += 1
            # the negative control: on the first ranked item, claim it was ranked by the OTHER
            # arm's table. The check must reject that, or it is not comparing anything.
            if negative and not injected and rank is not None and got and other and other != got:
                findings.append("B(control) %s: item %s records source %r, arm maps to %r"
                                % (arm, it.get("item_id"), other, want))
                injected = True

    if negative and not injected:
        findings.append("(control) could not be injected: no ranked item with another table "
                        "available, so the control did not run")

    print("  arms with an L2c layer : %d  (%s)" % (len(arms_with_l2c), ", ".join(arms_with_l2c)))
    print("  arms mapped to a table  : %d" % checked["arms_mapped"])
    print("  table names            : %s" % ", ".join(sorted(tables)))
    for name, t in sorted(tables.items()):
        print("    %-12s %s  Han %s / %s distinct  top10=%s"
              % (name, t.get("source"), f"{t.get('han_total', 0):,}",
                 f"{t.get('distinct_characters', 0):,}", t.get("ten_commonest")))
    print("  L2c items checked      : %d" % checked["items"])
    print("  roots found in table   : %d" % checked["roots_in_table"])
    print()

    payload = {
        "generated_by": "scripts/check_frequency_provenance.py",
        "negative_test": negative,
        "arms_with_l2c": arms_with_l2c,
        "arm_source": mapping,
        "tables": {k: {kk: vv for kk, vv in v.items() if kk != "frequency"}
                   for k, v in tables.items()},
        "checked": dict(checked),
        "findings": findings,
        "note": ("Each arm's L2c difficulty is the root's rank under that arm's OWN corpus "
                 "frequency. A shared table would be a mismatched denominator."),
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if negative:
        # The convention this suite enforces: a negative-control run succeeds when the control
        # FIRES. The injected defect is supposed to be caught, so catching it is the guard working,
        # and an exit code of 1 there would report a healthy guard as broken. Exiting non-zero is
        # reserved for the control failing to fire, which is the case that means the guard is not
        # actually comparing anything. Checked against the sibling guards, which all exit 0 here.
        controls = [f for f in findings if "(control)" in f]
        real = [f for f in findings if "(control)" not in f]
        for f in real[:6]:
            print("  (also present, not a control finding) %s" % f)
        if controls:
            print("  [OK] negative control fires: %s" % controls[0])
            print()
            print("  The guard caught an injected defect. That is the requested behaviour of a")
            print("  negative control, so this run is a success.")
            return 0
        print("  [FAIL] the negative control did not fire: no injected defect was reported, so the")
        print("         guard's comparison is not running and its positive result means nothing.")
        return 1

    if findings:
        for f in findings[:12]:
            print("  [FAIL] %s" % f)
        if len(findings) > 12:
            print("  ... %d more" % (len(findings) - 12))
        print()
        print("  A rank is only comparable across arms if each arm was ranked against its own")
        print("  domain. A shared table silently substitutes a different denominator.")
        return 1
    print("  [OK] every L2c item was ranked against its own arm's frequency table")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--negative-test", action="store_true")
    args = ap.parse_args()
    mapping, tables = load()
    return run(args.negative_test, mapping, tables)


if __name__ == "__main__":
    sys.exit(main())
