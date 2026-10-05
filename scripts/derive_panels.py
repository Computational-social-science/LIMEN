#!/usr/bin/env python
"""derive_panels.py -- derive the manuscript's data panels FROM THE ANCHOR, never by hand.

THE RULE THIS FILE EXISTS TO ENFORCE
    Every number and every status shown in a `.stat-card` or a `.ck` row must be READ OUT of the
    anchor, and every card must name the section it came from. A hand-typed figure on a manuscript
    page is a claim with no provenance, and a claim with no provenance is the exact failure this
    repository exists to prevent - it is how a model count of 18 survives for forty edits after the
    data became 42.

    So a field that cannot be derived is rendered as an em dash with its missing pattern recorded.
    A visible gap is honest; an invented value is not. The build prints both, so a silent gap is
    impossible.

WHY NOT PARSE THE CHECKLIST AS PROSE
    The pre-registration checklist in section 12 is a Markdown table whose State column is maintained
    by hand in the anchor. Reading it structurally - row by row - rather than by keyword means a row
    that changes its wording cannot silently change which badge it gets: the state string is mapped by
    an explicit table below, and an unrecognised state is reported rather than defaulted to green.

THE BADGE MAPPING IS EXPLICIT
    yes  = the requirement is frozen
    part = frozen in part, with the remainder named
    no   = not yet decided, and the blocking item is named
    A state string that matches none of these is a FAILURE of this script, not a default. Defaulting an
    unknown state to "yes" would turn a wording change into a false claim of completeness.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
ANCHOR = ROOT / "protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md"

# Explicit state -> badge. An unmatched state is reported, never assumed.
STATE_MAP = [
    ("FIXED — as `intent` alone", "yes", "frozen; `ok` and `escalate` dropped"),
    ("FIXED", "yes", "frozen"),
    ("BUILT", "part", "built; human pass outstanding"),
    ("CLASSES FIXED · λ PENDING", "part", "classes frozen; λ pending on the readability calibration"),
    ("FROZEN", "yes", "frozen"),
]

MISSING = []


def _grab(pattern, text, label, group=1, flags=re.S):
    m = re.search(pattern, text, flags)
    if not m:
        MISSING.append(label)
        return None
    return m.group(group).strip()


def stat_cards(text):
    """The scalar design parameters, each traceable to the section that fixes it."""
    ver = _grab(r"\*\*Version:\*\*\s*([0-9.]+)", text, "version")
    ntest = _grab(r"FROZEN: N_test = (\d+)", text, "N_test")
    bank = _grab(r"\*\*BUILT\*\* \((\d+) items", text, "bank size")
    seeds = _grab(r"seeds ∈ \{([0-9,\s]+)\}", text, "seeds")
    eps = _grab(r"\\varepsilon\s*=\s*([0-9.]+)", text, "epsilon")
    # The corrected discordance lives in the section-12 row for N_item, written as "the corrected
    # pi_d is 0.1833". The symbol there is Greek PI followed by "_d", so it is matched as an
    # arbitrary short token rather than as a LaTeX name - a pattern written for the LaTeX form
    # ("\pi_d") does not match the rendered character, which is how this card first came out as a
    # dash and had to be traced back to the source rather than guessed at.
    pid = _grab(r"the corrected\s+\S{0,3}\s*is\s+([0-9.]+)", text, "pi_d")

    def card(val, label, src):
        v = val if val else "—"
        return ('<div class="stat-card"><div class="stat-val">' + v + "</div>"
                '<div class="stat-lbl">' + label
                + '<br><span style="opacity:.7">' + src + "</span></div></div>")

    cards = [
        card(ver, "protocol version", "§14"),
        card(ntest, "test items N (frozen)", "§12 · O2 + Erratum 1"),
        card(bank, "item bank", "§12 · O3"),
        card(seeds.replace(" ", "") if seeds else None, "noise seeds", "§12 item 3"),
        card(eps, "coverage budget ε", "§12 item 7"),
        card(pid, "corrected discordance π<sub>d</sub>", "Erratum 1"),
    ]
    return cards


def checklist(text):
    """The section 12 table, row by row, with an explicit badge per state."""
    m = re.search(r"^## 12\..*?^\| # \|.*?\n((?:^\|[^\n]*\n)+)", text, re.S | re.M)
    if not m:
        MISSING.append("section 12 checklist table")
        return []
    rows = []
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or set(cells[0]) <= set("-: "):
            continue
        num, req, state, where = cells[0], cells[1], cells[2], cells[3]
        plain = re.sub(r"\*\*", "", state)
        badge, why = None, ""
        for key, b, note in STATE_MAP:
            if plain.startswith(key.split("—")[0].strip()) and key.split("—")[0].strip() in plain:
                badge, why = b, note
                break
        if badge is None:
            for key, b, note in STATE_MAP:
                if plain == key:
                    badge, why = b, note
                    break
        if badge is None:
            MISSING.append("unmapped checklist state: " + plain[:48])
            badge, why = "part", "state string not in the explicit mapping"
        mark = "✓" if badge == "yes" else ("△" if badge == "part" else "○")
        rows.append(
            '<li><span class="' + ("ic-ok" if badge == "yes" else "ic-warn") + '">' + mark + "</span>"
            '<span><b>' + re.sub(r"\*\*", "", num) + ".</b> "
            + req.replace("**", "")
            + ' <span class="badge b-' + badge + '">' + badge.upper() + "</span>"
            + "<br><span style=\'font-size:7.6pt;color:var(--text3)\'>"
            + why + " &middot; " + where.replace("**", "") + "</span></span></li>")
    return rows


def build():
    text = ANCHOR.read_text(encoding="utf-8")
    cards = stat_cards(text)
    rows = checklist(text)
    if MISSING:
        raise SystemExit("derive_panels: fields that could NOT be derived (rendered as —, "
                         "never invented):\n  " + "\n  ".join(MISSING))
    grid = '<div class="stat-grid">' + "".join(cards) + "</div>"
    return grid, rows, len(cards), len(rows)


if __name__ == "__main__":
    g, r, nc, nr = build()
    print("  stat cards : " + str(nc))
    print("  checklist  : " + str(nr) + " rows")
    print("  missing    : 0")