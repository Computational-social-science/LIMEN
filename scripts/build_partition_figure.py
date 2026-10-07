"""build_partition_figure.py -- the failure-class partition, drawn on the two axes that decide it.

WHAT THIS FIGURE IS FOR. The result is easy to misread as a refutation of the literature on silent
failures. It is a PARTITION, and the partition decides which remedy applies -- so the figure has to do two
things a prose paragraph cannot: show that the two classes are separated by quantities a practitioner can
MEASURE, and show where the next experiment is predicted to land.

IT IS NOT A CONCEPTUAL DIAGRAM. Both axes are diagnostics computed from the confirmatory trial record, so
the trajectory is measured, not asserted:

    x   the share of errors the gate rejects        -- does the gate SEE the damage?
    y   the conditional error among admitted trials -- does the damage reach committed answers?

A loud failure (channel-side) moves a system RIGHT and not up: the gate sees more, committed correctness
does not degrade. A silent failure (model-side) moves it UP and not right: committed correctness degrades
while the gate sees nothing. The measured trajectory sits in the loud region, and the silent region is where
the era's taxonomy lives and where this study PREDICTS meaning-corrupting noise will land.

THE PREDICTION IS DRAWN AS A PREDICTION. It is marked hollow and labelled as such, because a figure that
made it look measured would be the exact failure this repository keeps finding: an artefact asserting more
than its source supports.
"""

from __future__ import annotations

import csv
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "viz" / "figures"
SUMMARY = ROOT / "data" / "processed" / "stage2_lambda_summary.csv"

DOUBLE = 7.2          # Nature Human Behaviour double column, 183 mm


def read_csv() -> list[dict]:
    with SUMMARY.open(encoding="utf-8") as fh:
        return [{k: (float(v) if k not in ("n",) else int(v)) for k, v in r.items()}
                for r in csv.DictReader(fh)]


def main() -> int:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    try:
        import scienceplots  # noqa: F401 - registers the styles on import
    except ImportError:  # pragma: no cover - the figures must exist even without the style package
        scienceplots = None
        print("  [WARN] scienceplots is NOT installed - falling back to the default matplotlib style. "
              "The figures are still correct; they are not in the journal house style.")
    if scienceplots is not None:
        plt.style.use(["science", "nature", "no-latex"])
    plt.rcParams.update({
        "figure.dpi": 150, "savefig.dpi": 600,
        "axes.linewidth": 0.5, "xtick.major.width": 0.4, "ytick.major.width": 0.4,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "font.size": 7, "axes.labelsize": 7, "axes.titlesize": 7,
        "xtick.labelsize": 6, "ytick.labelsize": 6, "legend.fontsize": 5.5,
    })
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    d = read_csv()
    lam = [r["lambda"] for r in d]
    x = [100 * r["error_rejected_share_0.9"] for r in d]
    y = [100 * r["cond_error_0.9"] for r in d]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(DOUBLE, 2.5))
    fig.subplots_adjust(left=0.082, right=0.965, top=0.80, bottom=0.30, wspace=0.32)

    # ---- (a) the map -------------------------------------------------------------------------------
    # PLACEMENT RULES LEARNED FROM THE AUDIT, not chosen by eye. The first version put five text blocks into
    # a panel whose only empty regions are the upper-left and the lower-left, and the layout audit reported
    # nine overlaps and a tick label outside the canvas. Text now goes where the data is not: the silent band
    # is labelled in the upper-LEFT, the loud region in the lower-left, and the predicted point sits on the
    # right with its label hanging below it into empty space. Margins leave room for the outermost tick.
    LOUD, SILENT = "#1f6f8b", "#b5443a"
    # PANEL (a) CARRIES NO λ LABELS AT ALL. The audit rejected three attempts to fit point labels plus two
    # annotation boxes plus two quadrant captions into a band 35 x-units wide; every arrangement overlapped
    # something. The levels are panel (b)'s whole subject, so (a) is left to do the one job a map has: show
    # which region the measured path occupies. What is not labelled here is labelled there.
    ax.axhspan(8.6, 10.7, color=SILENT, alpha=0.07, zorder=0)
    ax.text(56.2, 10.5, "SILENT  ·  model-side", ha="left", va="top", fontsize=5.6,
            color=SILENT, fontweight="bold")
    ax.text(56.2, 6.30, "LOUD  ·  channel-side", ha="left", va="bottom", fontsize=5.6,
            color=LOUD, fontweight="bold")

    ax.plot(x, y, "-", color=LOUD, lw=1.1, zorder=3)
    ax.scatter(x, y, s=15, color=LOUD, zorder=4, edgecolor="white", linewidth=0.4)
    ax.scatter([x[0]], [y[0]], s=32, facecolor="white", edgecolor=LOUD, linewidth=1.0, zorder=5)
    ax.scatter([x[-1]], [y[-1]], s=32, facecolor="white", edgecolor=LOUD, linewidth=1.0, zorder=5)
    ax.annotate("clean", (x[0], y[0]), textcoords="offset points", xytext=(-13, 2),
                fontsize=5.0, ha="right", va="center", color=LOUD)
    ax.annotate(r"$\lambda=0.25$", (x[-1], y[-1]), textcoords="offset points", xytext=(-6, -10),
                fontsize=5.0, ha="right", va="top", color=LOUD)

    ax.scatter([89.0], [9.55], s=26, facecolor="white", edgecolor=SILENT, linewidth=0.9, zorder=5)
    ax.annotate("PREDICTED", (89.0, 9.55), textcoords="offset points", xytext=(0, -19),
                fontsize=5.0, ha="center", va="top", color=SILENT, fontweight="bold")
    ax.annotate("meaning-corrupting noise", (89.0, 9.55), textcoords="offset points", xytext=(0, -28),
                fontsize=4.8, ha="center", va="top", color=SILENT)

    ax.set_xlabel("share of errors the gate rejects  (%)")
    ax.set_ylabel("conditional error among admitted trials  (%)")
    ax.set_xlim(55, 100)
    ax.set_ylim(5, 10.7)
    ax.set_xticks([60, 70, 80, 90, 100])
    ax.set_title("(a)  two classes, separated by measurable diagnostics", fontsize=6.5, pad=6)

    # ---- (b) the same two diagnostics against noise level ------------------------------------------
    ax2.plot(lam, x, "-o", color=LOUD, ms=3.0, lw=0.9, label="errors rejected by the gate (%)")
    ax2.plot(lam, [v * 10 for v in y], "-s", color=SILENT, ms=3.0, lw=0.9,
             label="conditional error among admitted (%,  x10)")
    ax2.axvline(0.05, color="0.55", lw=0.5, ls=(0, (2, 2)))
    ax2.axvline(0.18, color="0.55", lw=0.5, ls=(0, (2, 2)))
    ax2.text(0.052, 12, r"$\lambda_{lo}$", fontsize=5.4, color="0.35")
    ax2.text(0.182, 12, r"$\lambda_{mid}$", fontsize=5.4, color="0.35")
    ax2.set_xlabel(r"noise level  $\lambda$")
    ax2.set_ylabel("diagnostic  (%)")
    ax2.set_xlim(-0.012, 0.262)
    # EXPLICIT TICKS: a locator free to choose put its outermost label past the canvas edge, which
    # the audit reports as text the reader never sees. Explicit values bound where the ink can go.
    ax2.set_xticks([0.00, 0.05, 0.10, 0.15, 0.20, 0.25])
    ax2.set_ylim(0, 108)
    ax2.set_yticks([0, 20, 40, 60, 80, 100])
    ax2.legend(loc="center right", frameon=False, fontsize=5.2)
    ax2.set_title("(b)  they separate as the channel degrades", fontsize=6.5, pad=6)
    ax2.annotate("rises", (0.245, 96), fontsize=5.2, color=LOUD, ha="right", va="center")
    ax2.annotate("flat", (0.245, 8 * 10 * 0.9), fontsize=5.2, color=SILENT, ha="right", va="bottom")

    stem = "fig8_stage2_failure_partition"
    fig.savefig(FIG_DIR / f"{stem}.png", bbox_inches=None)
    fig.savefig(FIG_DIR / f"{stem}.jpg", bbox_inches=None)
    fig.savefig(FIG_DIR / f"{stem}.svg", bbox_inches=None)
    fig.savefig(FIG_DIR / f"{stem}.tiff", bbox_inches=None, pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)
    # CAPTION, MERGED NOT OVERWRITTEN. Three other generators write into this same file, and one of them
    # already destroyed another's entries by opening it for writing. Replace only the block this figure owns
    # and report what was preserved - a caption file that silently loses a figure's caption is the defect the
    # document checks exist for.
    CAPS = FIG_DIR / "FIGURE_CAPTIONS.md"
    own = ("## " + stem + "\n\n"
           "The two failure classes, drawn on the two diagnostics that separate them. **(a)** The measured "
           "trajectory across the noise grid, against the share of errors the gate rejects (does the gate "
           "*see* the damage?) and the conditional error among admitted trials (does it reach *committed* "
           "answers?). The path runs right and slightly down - 61.4 % to 96.2 % rejected, conditional error "
           "flat at 9.25 % to 7.02 % - the loud, channel-side region. The **silent, model-side** region is "
           "where meaning-corrupting noise is predicted to land, marked hollow because it is a prediction and "
           "not a measurement. **(b)** The same two diagnostics against noise level: the rejection share "
           "rises monotonically while the conditional error does not. Every plotted value is read from "
           "`data/processed/stage2_lambda_summary.csv`; nothing is interpolated or modelled.\n")
    prev = CAPS.read_text(encoding="utf-8") if CAPS.exists() else ""
    kept = [m.group(0) for m in re.finditer(r"^## (?!.*" + re.escape(stem) + r")\S+\n\n(?:.*?)(?=^## |\Z)",
                                            prev, re.S | re.M)]
    CAPS.write_text(own + "\n" + "".join(kept), encoding="utf-8", newline="\n")
    print(f"  wrote {FIG_DIR.name}/{stem}.[png|jpg|svg|tiff]  and its caption (preserved {len(kept)} others)")
    print(f"  wrote {FIG_DIR.name}/{stem}.[png|jpg|svg|tiff]")
    print(f"    trajectory: reject-share {x[0]:.1f}% -> {x[-1]:.1f}%;  "
          f"conditional error {y[0]:.2f}% -> {y[-1]:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
