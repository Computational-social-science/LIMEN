#!/usr/bin/env python
"""build_phase2_figures.py -- the Phase II measurement figure, to the project's Nature standard.

REBUILT AFTER A STANDARD AUDIT. The first version (kept beside this one as
`build_phase2_figures.py.superseded_v1`) violated six of the project's figure rules, and each is recorded
here because each is a rule with an incident behind it:

  1. It invented a palette instead of using the project's (`#1B6CA8` blue, `#C45E11` orange, `#2E8B57`
     green, `#6A3D99` purple, `#6b7a8d` gray, `#333333` black).
  2. It wrote panel labels as "A  <sentence>" inside the title strings, rather than as bold lowercase
     `a`, `b` placed at axes fraction (-0.12, 1.02).
  3. **It burned a caption into the image** with `fig.text`. A caption belongs to the document, which is
     what lets it be restyled, translated and reused; a caption in the raster can do none of those, and it
     duplicates text the document already owns.
  4. It used `bbox_inches='tight'`, which shifts absolutely-positioned text unpredictably. The project uses
     explicit `subplots_adjust` margins with `bbox_inches=None`.
  5. It set no tick widths. The standard is major 0.4 pt, minor 0.3 pt.
  6. **It contained a hand-drawn schematic panel** -- `axis('off')`, hardcoded coordinates, and two magic
     numbers (0.305, 0.395) typed into the drawing rather than read from the config. Non-data content does
     not belong in a data figure, and the file's own docstring claimed every number came from a config
     while violating that claim. That panel is removed, and the two offsets are now read from
     `config/depth_axis.json`'s `structure` block.

WHAT THE TWO REMAINING PANELS SHOW
  (a) the measured orthographic-depth axis, 22 languages, with the cluster/outlier structure annotated from
      the config's own `structure` block; (b) the collision measurement per split, the antecedent of the
      impossibility theorem held in the sibling repository `lean-nhb` under `NHB/PhaseII/`.
Both panels are data. The caption travels in `viz/figures/FIGURE_CAPTIONS.md`, not in the image.

RUN
    python scripts/build_phase2_figures.py
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
# `FIG_DIR` is the name the project's figure audit (`qc_stage2_figures.py`) overrides to redirect a
# generator's output into a temp directory while it audits. Without it the audit cannot redirect this
# script and would write over the very deliverable it is checking -- which is what the audit itself
# reported the first time this script was registered with it. `FIGDIR` is kept as the local alias.
FIG_DIR = REPO_ROOT / "viz" / "figures"

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# ---- the project standard, applied as rcParams so no call site can drift from it ----------
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 7,
    "axes.labelsize": 7,
    "xtick.labelsize": 5.5,
    "ytick.labelsize": 5.5,
    "figure.dpi": 150,
    "savefig.dpi": 600,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.5,
    "xtick.major.width": 0.4, "xtick.minor.width": 0.3,
    "ytick.major.width": 0.4, "ytick.minor.width": 0.3,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5,
})

C_BLUE, C_ORANGE, C_GREEN = "#1B6CA8", "#C45E11", "#2E8B57"
C_PURPLE, C_GRAY, C_BLACK = "#6A3D99", "#6b7a8d", "#333333"

# Script classes map onto the PROJECT palette rather than onto invented colours. Segmental scripts take the
# palette's blue; the two non-segmental ones take its contrast pair, orange, because the figure's point is
# that they are a different kind of object rather than a further point on one scale.
CLASS_COLOUR = {
    "alphabetic": C_BLUE,
    "abjad": C_PURPLE,
    "abugida": C_GRAY,
    "syllabic/featural": C_GREEN,
    "syllabic + logographic": C_ORANGE,
    "logographic": C_ORANGE,
}

DC = 7.16  # Nature double-column width, inches


def load() -> tuple[dict, dict]:
    dpath = REPO_ROOT / "config" / "depth_axis.json"
    cpath = REPO_ROOT / "config" / "collision_evidence.json"
    for p in (dpath, cpath):
        if not p.exists():
            print(f"  {p.relative_to(REPO_ROOT)} missing; cannot build the figure")
            sys.exit(1)
    return (json.loads(dpath.read_text(encoding="utf-8")),
            json.loads(cpath.read_text(encoding="utf-8")))


def panel_label(ax, letter: str) -> None:
    """Bold lowercase panel label at axes fraction (-0.12, 1.02) -- the project's stated position."""
    ax.annotate(letter, xy=(-0.12, 1.02), xycoords="axes fraction",
                fontsize=7.5, fontweight="bold", ha="left", va="bottom",
                annotation_clip=False)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--dpi", type=int, default=600)
    args = ap.parse_args()

    depth, coll = load()
    ordered = sorted(depth["axis"], key=lambda r: r["rel"])          # deepest first
    seg = [r for r in ordered if r["code"] not in ("jpn", "zho")]
    floor = min(r["rel"] for r in seg)                               # read, never typed
    cluster_range = depth["structure"]["segmental_cluster"]["range"]
    outliers = depth["structure"]["logographic_outliers"]
    offsets = {c: outliers[f"{c}_below_cluster_floor_by"] for c in ("jpn", "zho")}

    fig = plt.figure(figsize=(DC, 6.5))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 1.0], wspace=0.40)

    # ---- (a) the depth axis
    ax = fig.add_subplot(gs[0, 0])
    ys = list(range(len(ordered)))
    ax.barh(ys, [r["rel"] for r in ordered],
            color=[CLASS_COLOUR.get(r["script"], C_GRAY) for r in ordered], height=0.72)
    ax.set_yticks(ys)
    ax.set_yticklabels([r["name"] for r in ordered])
    ax.invert_yaxis()
    ax.axvline(0.0, color=C_BLACK, lw=0.5)
    ax.axvline(floor, color=C_GRAY, lw=0.5, ls=":")
    # Placed ABOVE the topmost bar, not inside the plot: with an inverted y-axis the deep-end bars are at
    # the bottom, and an annotation anchored there lands on top of the longest bars. A visual review caught
    # it sitting on Chinese, Japanese, German and English.
    ax.annotate(f"segmental cluster spans {cluster_range:.3f}",
                xy=(floor + cluster_range / 2, -1.35),
                ha="center", va="bottom", fontsize=5.5, color=C_GRAY, annotation_clip=False)
    ax.set_ylim(len(ordered) - 0.3, -1.9)
    for c, dy in offsets.items():
        i = next(j for j, r in enumerate(ordered) if r["code"] == c)
        ax.annotate(f"{dy:.3f} below", xy=(ordered[i]["rel"], i), xytext=(3, 0),
                    textcoords="offset points", ha="left", va="center",
                    fontsize=5.5, color=C_ORANGE)
    ax.set_xlabel("orthographic transparency\n(relative to Spanish = 0; negative = deeper)")
    ax.set_xlim(floor - 0.11, 0.055)

    # ---- (b) the collision
    ax2 = fig.add_subplot(gs[0, 1])
    names = list(coll["splits"].keys())
    vals = [100 * coll["splits"][n]["share_identical_romanisation"] for n in names]
    pooled = 100 * coll["pooled"]["share_identical_romanisation"]
    ax2.bar(range(len(names)), vals, color=C_BLUE, width=0.55)
    ax2.axhline(pooled, color=C_ORANGE, lw=0.8, ls="--")
    ax2.annotate(f"pooled {pooled:.1f} %\nn = {coll['pooled']['identical_romanisation']:,}",
                 xy=(len(names) - 0.58, pooled), xytext=(0, 3), textcoords="offset points",
                 ha="right", va="bottom", fontsize=5.5, color=C_ORANGE)
    ax2.set_xticks(range(len(names)))
    ax2.set_xticklabels(names)
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("substitutions with identical\ntyped romanisation (%)")
    ax2.set_xlim(-0.6, len(names) - 0.4)

    panel_label(ax, "a")
    panel_label(ax2, "b")

    # Explicit margins and NO tight bbox: tight bbox shifts absolutely-positioned text, which is why the
    # project fixes the margins instead.
    fig.subplots_adjust(left=0.155, right=0.985, top=0.94, bottom=0.165)

    # Read FIG_DIR at the point of use, not through an alias bound at import: the audit overrides
    # this module attribute to redirect output, and an alias evaluated at import time would defeat it.
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    stem = FIG_DIR / "fig9_phase2_basis"
    for ext in ("png", "jpg", "svg"):
        p = stem.with_suffix(f".{ext}")
        if ext == "svg":
            fig.savefig(p, bbox_inches=None)
        elif ext == "jpg":
            fig.savefig(p, dpi=args.dpi, bbox_inches=None, pil_kwargs={"quality": 95})
        else:
            fig.savefig(p, dpi=args.dpi, bbox_inches=None)
        print(f"  wrote {p.relative_to(REPO_ROOT)}  ({p.stat().st_size:,} B)")
    plt.close(fig)
    print("  caption lives in viz/figures/FIGURE_CAPTIONS.md, not in the image")
    return 0


if __name__ == "__main__":
    sys.exit(main())
