"""Figure: the empirical keyboard channel measured from 136M Keystrokes.

Nature-style, drawn with scienceplots. Three panels, one claim each, in the order the
argument runs:

  (a) the corpus's own published error rate beside the rate measured here under the matching
      definition. This is the validation, and it belongs first: a reader has to see that the
      reading of the corpus reproduces the publisher's number (1.017x) before the
      decomposition of that number can be believed.
  (b) the composition of that rate. This is the new content: deletions and insertions are
      two-thirds of it, and key-adjacency -- the mechanism both published keyboard-noise
      generators are built on -- is under a tenth of it.
  (c) the substitution matrix, which is the channel itself rather than a summary.

Every axis is labelled with its unit, the palette is used for one distinction per panel, and
the caption written into the file is self-contained.
"""
from __future__ import annotations

import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import nature_style as NS   # shared journal specification
from matplotlib.patches import Rectangle

try:
    import scienceplots  # noqa: F401
    STYLE = ["science", "nature", "no-latex"]
except Exception:  # noqa: BLE001
    STYLE = ["seaborn-v0_8-whitegrid"]

REPO = pathlib.Path(__file__).resolve().parent.parent
SRC = REPO / "data" / "processed" / "keystroke_channel.json"
FIG_DIR = REPO / "viz" / "figures"

CLASS_ORDER = ["delete", "insert", "shift_state", "key_adjacency", "other_substitution"]
CLASS_LABEL = {
    "delete": "deletion",
    "insert": "insertion",
    "shift_state": "shift state",
    "key_adjacency": "key adjacency",
    "other_substitution": "other subst.",
}
CLASS_COLOR = {
    "delete": "#1b3a6b",
    "insert": "#476b9d",
    "shift_state": "#7a9bc4",
    "key_adjacency": "#b8c9de",
    "other_substitution": "#dcdcdc",
}


def main() -> int:
    d = json.loads(SRC.read_text(encoding="utf-8"))
    edits = d["edits"]
    total_edits = d["edits_total"]
    chars = d["target_chars"]
    measured = total_edits / chars
    published = d["published_rate"]
    subs = d["top_substitutions"]

    plt.style.use(STYLE)
    plt.rcParams.update(NS.rcparams())
    fig, axes = plt.subplots(1, 3, figsize=(NS.DOUBLE_COL, 2.5),
                             gridspec_kw={"wspace": 0.46})

    # (a) validation: measured under the matching definition vs published
    ax = axes[0]
    vals = [100 * measured, 100 * published]
    ax.bar([0, 1], vals, color=["#1b3a6b", "#b8c9de"], edgecolor="black", linewidth=0.4,
           width=0.55)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["measured\nhere", "published\nCHI 2018"], fontsize=5.4)
    ax.set_ylabel("uncorrected errors (% of\ntarget characters)", fontsize=5.8)
    ax.set_ylim(0, max(vals) * 1.35)
    ax.set_title("a  the published rate is reproduced", fontsize=6.0, loc="left")
    for i, v in enumerate(vals):
        ax.text(i, v * 1.03, "%.3f%%" % v, ha="center", fontsize=5.4)
    ax.text(0.5, max(vals) * 1.22, "ratio %.3f" % (measured / published),
            ha="center", fontsize=5.2, style="italic")
    NS.style_axes(ax, 'a')

    # (b) composition of the rate -- the new content
    ax = axes[1]
    shares = [100 * edits[k] / total_edits for k in CLASS_ORDER]
    bottom = 0.0
    for k, s in zip(CLASS_ORDER, shares):
        ax.bar(0, s, bottom=bottom, color=CLASS_COLOR[k], edgecolor="black",
               linewidth=0.4, width=0.5)
        if s > 7:
            ax.text(0, bottom + s / 2, "%.0f%%" % s, ha="center", va="center",
                    fontsize=5.2, color="white" if k in ("delete", "insert") else "black")
        bottom += s
    ax.set_xlim(-0.5, 0.5)
    ax.set_ylim(0, 100)
    ax.set_xticks([])
    ax.set_ylabel("share of edit operations (%)", fontsize=5.8)
    ax.set_title("b  what that rate is made of", fontsize=6.0, loc="left")
    handles = [Rectangle((0, 0), 1, 1, facecolor=CLASS_COLOR[k], edgecolor="black",
                             linewidth=0.4) for k in CLASS_ORDER]
    # BELOW THE PANEL, NOT BESIDE IT. Anchored at (1.02, 0.5) the legend sat in the gap between
    # panels (b) and (c), which is 0.090 of the figure wide, while five stacked entries need about
    # 0.10 -- so 'key adjacency' reached x=0.7118 and panel (c) starts at 0.702, putting the legend
    # text on top of that panel's 'intended' y-axis label at x=0.6688-0.6780. Measured, not guessed.
    # Under the panel the constraint is vertical, the panel has no x-ticks to collide with, and the
    # legend stays attached to the bars it names.
    ax.legend(handles, [CLASS_LABEL[k] for k in CLASS_ORDER], fontsize=NS.MIN_PT,
              loc="upper center", bbox_to_anchor=(0.5, -0.03), ncol=2, frameon=False,
              handlelength=1.1, columnspacing=0.9, labelspacing=0.35)
    NS.style_axes(ax, 'b')

    # (c) the substitution matrix
    ax = axes[2]
    top = subs[:9]
    wanted = sorted({w for w, _, _ in top})
    got = sorted({g for _, g, _ in top})
    M = np.zeros((len(wanted), len(got)))
    for w, g, n in top:
        M[wanted.index(w), got.index(g)] = n
    im = ax.imshow(M, cmap="magma_r", aspect="auto")
    ax.set_xticks(range(len(got)))
    ax.set_xticklabels(got, fontsize=5.4)
    ax.set_yticks(range(len(wanted)))
    ax.set_yticklabels(wanted, fontsize=5.4)
    ax.set_xlabel("observed", fontsize=5.8)
    ax.set_ylabel("intended", fontsize=5.8)
    ax.set_title("c  the channel itself", fontsize=6.0, loc="left")
    NS.style_axes(ax, 'c')

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / "fig_keystroke_channel.png"
    NS.save_nature(fig, out.with_suffix(""))
    plt.close(fig)

    print("  measured (all edits) : %.4f%%" % (100 * measured))
    print("  published            : %.4f%%" % (100 * published))
    print("  ratio                : %.4f" % (measured / published))
    print("  composition          : " + "  ".join(
        "%s %.1f%%" % (CLASS_LABEL[k], 100 * edits[k] / total_edits) for k in CLASS_ORDER))
    print("  wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
