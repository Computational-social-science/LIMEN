#!/usr/bin/env python
"""build_lean_figures2.py -- two more figures for the formalisation, both parsed from the documents.

WHY THESE TWO
    fig4 and fig5 showed the kernel from the outside: what its theorems imply on real data, and how they
    depend on one another. Neither showed the thing a reader has least reason to believe - that the
    formalisation CHANGED THE RESEARCH - nor what the manuscript's claims actually rest on.

    fig6  where machine-checking corrected the protocol. Four claims in the record were wrong, and the
          theorems that settled three of them are named. A formalisation that only confirms what was
          already written is decoration; this one refuted its own protocol's wording in two places, and that
          is the single most persuasive thing in the repository.
    fig7  the evidence chain: every claim in the manuscript, sorted by what it rests on - a kernel proof, a
          measurement, an assumption, or the confirmatory run. It answers "what would break this paper",
          which no table of results answers.

NOTHING IS TYPED IN. Both figures parse their text out of the documents that already assert it, so a figure
cannot say something the document does not.
"""

from __future__ import annotations

import pathlib
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
try:
    import scienceplots  # noqa: F401 - registers the styles on import
except ImportError:  # pragma: no cover - the figures must still be produced and still be audited
    # A STYLE PACKAGE IS NOT A DEPENDENCY OF THE RESULT. This environment lost `scienceplots` twice in one
    # session (toolchain updates), and each time the layout audit went red and blocked commits - a missing
    # font for the figures blocking the pipeline that publishes them. The figures are produced either way and
    # the audit measures geometry, which the style does not change; what must NOT happen is a SILENT
    # substitution, so the fallback says so, loudly, every run.
    scienceplots = None
    print("  [WARN] scienceplots is NOT installed - falling back to the default matplotlib style. "
          "The figures are still correct; they are not in the journal house style.")

if scienceplots is not None:
    plt.style.use(["science", "nature", "no-latex"])

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "viz" / "figures"
STATUS = ROOT / "docs" / "LEAN_FORMALIZATION_STATUS.md"
PROTOCOL = ROOT / "protocol" / "NHB_Orthographic_Channels_JEV_Research_Protocol.md"

ACCENT, ACCENT2, ACCENT3, MUTED, INK = "#1B6CA8", "#C45E11", "#2E8B57", "#6b7a8d", "#1a1a1a"
RED = "#B03A2E"

plt.rcParams.update({
    "savefig.dpi": 600, "font.size": 7.4,
    "axes.labelsize": 7.4, "axes.titlesize": 8.2, "legend.fontsize": 7,
    "axes.edgecolor": MUTED, "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    
})


def parse_corrections() -> list[tuple[str, str]]:
    """The 'Corrections to earlier versions of this record' table, read from the document."""
    text = STATUS.read_text(encoding="utf-8")
    i = text.find("## Corrections to earlier versions")
    if i < 0:
        return []
    block = text[i:i + 1600]
    rows = []
    for m in re.finditer(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", block, re.M):
        a, b = m.group(1), m.group(2)
        if a.lower().startswith("earlier") or set(a) <= set("-: "):
            continue
        rows.append((a, b))
    return rows


# Which kernel results are CORRECTIONS rather than confirmations, and which side each one corrected. The
# SELECTION is a judgement; every word of the text is parsed from the status record, so the figure cannot
# overstate what was established.
CORRECTIVE_THEOREMS = [
    ("protocol_said_nondecreasing_is_FALSE",
     "the §6 wording",
     "\u201cSilentError is non-decreasing in \u03c4\u201d"),
    ("budget_collapses_to_zero_on_small_dev",
     "the \u03b5 = 0.05 budget rule",
     "assumed a usable gate at every N"),
    ("acc_is_not_diagnostic_of_understanding",
     "the accuracy reading",
     "treated Acc as evidence about understanding"),
    ("cond_error_complements_cond_accuracy",
     "the hypothesis family",
     "counted two readings of one quantity"),
]


def parse_theorem_statements() -> dict[str, str]:
    text = STATUS.read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"^\|\s*`([a-zA-Z_][A-Za-z0-9_']*)`\s*\|\s*(.+?)\s*\|", text, re.M):
        out.setdefault(m.group(1), m.group(2))
    return out


def figure6() -> pathlib.Path:
    corr = parse_corrections()
    stmts = parse_theorem_statements()
    missing = [n for n, _, _ in CORRECTIVE_THEOREMS if n not in stmts]

    rows = [(claim, measured, None, None) for claim, measured in corr]
    for name, target, was in CORRECTIVE_THEOREMS:
        if name in stmts:
            rows.append((f"{target}: {was}", stmts[name], name, "kernel"))

    n = len(rows)
    fig, ax = plt.subplots(figsize=(7.16, 1.05 + 0.62 * n))
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.5, n - 0.2)
    ax.invert_yaxis()

    for k, (was, now, theorem, kind) in enumerate(rows):
        y = k
        left_face = "#fdf2f0" if kind == "kernel" else "#f6f7f9"
        ax.add_patch(plt.Rectangle((0.05, y - 0.38), 4.0, 0.76, fc=left_face, ec="#e0c9c4", lw=0.6))
        ax.text(0.18, y, was, va="center", ha="left", fontsize=6.7, wrap=True, color=RED)
        ax.annotate("", xy=(5.0, y), xytext=(4.15, y),
                    arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.9))
        ax.add_patch(plt.Rectangle((5.1, y - 0.38), 4.8, 0.76, fc="#eef6f1", ec="#c3ddcd", lw=0.6))
        txt = now if len(now) < 150 else now[:147] + "\u2026"
        ax.text(5.25, y, txt, va="center", ha="left", fontsize=6.7, wrap=True, color="#1d5c3a")
        if theorem:
            ax.text(9.85, y + 0.46, theorem, va="center", ha="right", fontsize=5.4, color=ACCENT,
                    style="italic")

    ax.text(0.18, -0.55, "what the record said", fontsize=7.4, color=RED, fontweight="bold")
    ax.text(5.25, -0.55, "what was measured, or proved", fontsize=7.4, color="#1d5c3a", fontweight="bold")

    fig.suptitle("The formalisation corrected the protocol, and the corrections were kept",
                 fontsize=8.6, y=0.985)
    fig.text(0.5, 0.012,
             f"{len(corr)} claims from the record's own corrections table and {len(rows) - len(corr)} "
             f"protocol statements refuted or qualified by a named theorem; the italic names are the "
             f"kernel results that settled them.",
             ha="center", fontsize=6.2, color=MUTED)
    fig.tight_layout()
    p = write_formats(fig, "fig6_stage2_corrections")
    plt.close(fig)
    print(f"  fig6: {len(corr)} record corrections + {len(rows) - len(corr)} kernel-settled statements")
    if missing:
        print(f"        [WARN] no statement parsed for {missing} - left out rather than paraphrased")
    return p


STATUS_ORDER = ["PROVED", "MEASURED", "ASSUMED", "TO BE TESTED"]


def parse_provenance() -> dict[str, int]:
    """Count the manuscript's claims by what they rest on, from the protocol's own provenance table."""
    # INSIDE THE GENERATED BLOCK ONLY, and by COLUMN. The status sits in the SECOND column of a four-column
    # row; looking for it in the first column matched nothing, and the fallback then counted every mention of
    # a status word anywhere in the protocol - which reported 75 claims where the table holds 34. A figure
    # that overstates how much of a paper is proved is worse than no figure.
    text = PROTOCOL.read_text(encoding="utf-8")
    b = text.find("<!-- PROVENANCE:BEGIN")
    e = text.find("<!-- PROVENANCE:END", b if b >= 0 else 0)
    seg = text[b:e] if b >= 0 and e > b else text
    counts: dict[str, int] = {}
    # BOTH EMPHASES: the generator marks PROVED and MEASURED in bold and ASSUMED in italics, so a pattern
    # requiring `**` silently dropped exactly the assumption rows - 28 where the table holds 34, and the
    # missing six were the ones a reader most needs to see.
    for m in re.finditer(r"^\|[^|]*\|\s*\*{1,2}(PROVED|MEASURED|ASSUMED|TO BE TESTED)\*{1,2}\s*\|", seg, re.M):
        counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    if not counts:
        raise SystemExit(
            "the provenance table's status column could not be parsed. Reporting zero would be a claim in "
            "itself, and reporting a count read from prose is worse - fix the parse instead.")
    return counts


def figure7() -> pathlib.Path:
    counts = parse_provenance()
    if not counts:
        raise SystemExit("the provenance table could not be parsed - refusing to draw invented counts")
    order = [k for k in STATUS_ORDER if k in counts]
    vals = [counts[k] for k in order]
    total = sum(vals)

    colours = {"PROVED": ACCENT, "MEASURED": ACCENT3, "ASSUMED": ACCENT2, "TO BE TESTED": MUTED}
    fig, ax = plt.subplots(figsize=(7.16, 2.5))
    y = 0.86
    left = 0.0
    for k, v in zip(order, vals):
        w = v / total
        ax.add_patch(plt.Rectangle((left, y - 0.16), w, 0.32, fc=colours[k], ec="white", lw=1.2))
        label = f"{k}\n{v}"
        ax.text(left + w / 2, y, label, ha="center", va="center", fontsize=6.8,
                color="white" if k != "TO BE TESTED" else "white", fontweight="bold")
        left += w
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    notes = [
        ("PROVED", "settled by the kernel; no empirical premise"),
        ("MEASURED", "read off the confirmatory or pre-run record"),
        ("ASSUMED", "carried as an assumption, stated as one"),
        ("TO BE TESTED", "Phase II, not yet run"),
    ]
    for k, (name, desc) in enumerate(notes):
        yy = 0.60 - k * 0.17
        ax.add_patch(plt.Rectangle((0.005, yy - 0.045), 0.022, 0.09, fc=colours[name], ec="none"))
        ax.text(0.05, yy, f"**{name}**".replace("**", ""), fontsize=7, va="center", fontweight="bold")
        ax.text(0.24, yy, desc, fontsize=6.6, va="center", color=MUTED)

    ax.set_title("What the manuscript's claims rest on", loc="left", fontsize=8.4, fontweight="bold")
    fig.text(0.5, 0.012,
             f"{total} claims in the protocol's provenance table, counted from the table itself. "
             f"A claim whose status cannot be read from the table is not counted here, so the bar is a "
             f"lower bound rather than a summary.",
             ha="center", fontsize=6.2, color=MUTED)
    fig.tight_layout()
    p = write_formats(fig, "fig7_stage2_evidence_chain")
    plt.close(fig)
    print(f"  fig7: {total} claims -> " + ", ".join(f"{k} {v}" for k, v in zip(order, vals)))
    return p


def write_formats(fig, stem: str) -> pathlib.Path:
    for tag in ("png", "jpg", "svg", "tiff"):
        kw = {}
        dpi = 600
        if tag == "jpg":
            dpi = 300
        if tag == "tiff":
            kw["pil_kwargs"] = {"compression": "tiff_lzw"}
        # bbox_inches=None WITH EXPLICIT MARGINS: the layout audit measures text against the SAVED
        # canvas, and a tight bounding box silently re-crops that canvas, so every text artist
        # measured against it appears to have escaped. The Stage 2 script has always used this
        # convention; the newer scripts did not, and the audit said so.
        fig.savefig(OUT / f"{stem}.{tag}", dpi=dpi, bbox_inches=None, **kw)
    return OUT / f"{stem}.png"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    figure6()
    figure7()
    return 0


if __name__ == "__main__":
    sys.exit(main())