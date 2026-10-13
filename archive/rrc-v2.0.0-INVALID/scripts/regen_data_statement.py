"""Regenerate the Data Statement's numeric blocks from the manifest.

Every number written here is read from config/rrc.json and the arm files. Nothing is typed from
memory, and the script asserts that the counts it writes are the counts it read.

Run after scripts/build_rrc.py. Then scripts/qc_data_statement.py audits the result.
"""
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
P = REPO / "docs" / "RRC_DATA_STATEMENT.md"
MAN = REPO / "config" / "rrc.json"

LAYER_COLS = [("L1", "L1"), ("L2", "L2"), ("L2c", "L2c (reading channel)"),
              ("L3del", "L3 (keyboard)"), ("L3", "L3 (keyboard)"), ("L4", "L4")]


def fmt(n) -> str:
    return f"{int(n):,}"


def main() -> int:
    man = json.loads(MAN.read_text(encoding="utf-8"))
    arms = man["arms"]
    s = P.read_text(encoding="utf-8")
    changed = []

    # ---- 1. the header total
    m = re.search(r"^\*\*Current total:\*\*.*$", s, re.M)
    if not m:
        # insert after the front matter block, before §A
        anchor = "\n## A."
        block = (f"**Current total:** {fmt(man['total_items'])} items across "
                 f"{len(arms)} arms, built {man['built_utc']} "
                 f"(dataset version {man['version']}, {man['n_options']} options per item, "
                 f"chance {round(1 / man['n_options'], 4)}).\n")
        if anchor in s:
            s = s.replace(anchor, "\n" + block + anchor, 1)
            changed.append("header total inserted")
    else:
        new = (f"**Current total:** {fmt(man['total_items'])} items across {len(arms)} arms, "
               f"built {man['built_utc']} (dataset version {man['version']}, "
               f"{man['n_options']} options per item, chance {round(1 / man['n_options'], 4)}).")
        if m.group(0) != new:
            s = s[:m.start()] + new + s[m.end():]
            changed.append("header total updated")

    # ---- 2. the arm-count paragraph in section I
    #
    # Replaces the whole paragraph that opens with "Items in different arms are", found by
    # paragraph boundaries rather than by an assumed tail. Two earlier patterns failed: one
    # required the literal "in object size (§K)." and the other required a blank line
    # immediately after the opening clause, while the real paragraph wraps across four lines
    # with single newlines. The stale counts (2,826 / 100,460 / 560 / 6,497 / 34,298 / 1,017)
    # survived both, and were finally caught by the unsourced-number audit rather than here.
    counts = ", ".join(f"{fmt(e['n_items'])} (`{a}`)" for a, e in arms.items())
    m = re.search(r"^Items in different arms are .*?(?=\n\s*\n)", s, re.S | re.M)
    if m:
        new_para = (f"Items in different arms are **not aligned to one another**, and this is a "
                    f"property a user must know. The arms carry {counts}. They differ in item "
                    f"count, in which candidate layers they support, and in object size (§K).")
        s = s[:m.start()] + new_para + s[m.end():]
        changed.append("section I counts updated")

    # ---- 3. the per-arm layer table
    table_re = re.compile(
        r"\| Arm \| n items \|.*?\n\|---.*?\n(?:\|.*\n)+", re.M)
    hdr = ("| Arm | n items | L1 | L2 | L2c (reading channel) | L3 (keyboard) | L4 |\n"
           "|---|---|---|---|---|---|---|\n")
    rows = []
    for arm, e in arms.items():
        lay = e.get("per_layer") or {}
        l1 = fmt(lay.get("L1", 0)) if lay.get("L1") else "—"
        l2 = fmt(lay.get("L2", 0)) if lay.get("L2") else "—"
        l2c = fmt(lay.get("L2c", 0)) if lay.get("L2c") else "—"
        l3n = (lay.get("L3del", 0) or 0) + (lay.get("L3", 0) or 0)
        l3 = fmt(l3n) if l3n else "—"
        l4 = fmt(lay.get("L4", 0)) if lay.get("L4") else "—"
        rows.append(f"| `{arm}` | {fmt(e['n_items'])} | {l1} | {l2} | {l2c} | {l3} | {l4} |")
    new_table = hdr + "\n".join(rows) + "\n"
    if table_re.search(s):
        s = table_re.sub(new_table, s, count=1)
        changed.append("layer table regenerated")

    # ---- 4. the removal counts
    m = re.search(r"Items removed at build time:.*?most mixed\.", s, re.S)
    if m:
        gate = ", ".join(f"{fmt(e.get('dropped_script') or 0)} (`{a}`)"
                         for a, e in arms.items() if (e.get("dropped_script") or 0))
        marg = ", ".join(f"{fmt(e.get('dropped_margin') or 0)} (`{a}`)"
                         for a, e in arms.items() if (e.get("dropped_margin") or 0))
        s = s[:m.start()] + (
            f"Items removed at build time: by the script-purity gate, {gate}. By the validity "
            f"constraint, which keeps an item only where the root is the nearest candidate on a "
            f"ranked layer, {marg or 'none'}. The Russian and GitHub-Chinese arms lose the "
            f"largest fractions to the script gate because their sources are the most mixed; "
            f"`rrc-ru` loses the largest fraction to the validity constraint, and that is a "
            f"narrowing of what the arm covers, not a defect.") + s[m.end():]
        changed.append("removal counts updated")

    P.write_text(s, encoding="utf-8")

    # ---- assert what was written is what was read
    txt = P.read_text(encoding="utf-8")
    nums = {int(t.replace(",", "")) for t in re.findall(r"[0-9][0-9,]*", txt)
            if t.replace(",", "").isdigit()}
    missing = []
    if man["total_items"] not in nums:
        missing.append(f"total {man['total_items']}")
    for a, e in arms.items():
        if e["n_items"] not in nums:
            missing.append(f"{a} n_items {e['n_items']}")
        for lay, c in (e.get("per_layer") or {}).items():
            if c and c not in nums:
                missing.append(f"{a}/{lay} {c}")
    print("  changes:", changed or "none")
    if missing:
        print("  [FAIL] numbers still absent from the statement: %s" % missing[:12])
        return 1
    print("  [OK] every manifest count is present in the statement")
    print("  wrote %s (%d bytes)" % (P, P.stat().st_size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
