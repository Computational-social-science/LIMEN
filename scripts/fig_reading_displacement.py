"""Figure: the displacement the model applies to the reading channel, per Chinese arm.

Nature-style, drawn with scienceplots. Two panels, one claim each:

  (a) the character shown against the candidate chosen. Both axes are frequency rank within the
      reading group, so the diagonal is "picked exactly what was shown" and the vertical distance
      from it is the displacement. This is the measurement: the model does not ignore the state --
      the line rises with it -- but it sits above the diagonal by an amount that differs by arm.
  (b) accuracy against the shown rank, per arm. This is what the displacement costs: where the
      displacement is large and the root is common, the answer is pushed out of reach.

WHY IT IS THIS AND NOT A RANK CURVE. The first analysis asked whether rank-1 items are easier than
late items and got opposite answers from two arms of the same script. The displacement is the
quantity underneath that, and it is one number per arm rather than a sign that flips: rrc-zh shifts
its answer about nine rank positions rarer than the form shown, rrc-zh-gh about one. A figure that
shows the shift shows why the two arms disagree without either of them being wrong.

Every axis carries its unit, the two arms are distinguished by one visual channel, and the caption
written into the file is self-contained. Data comes from the analyser's artefact, not from a
recomputation here, so the figure and the tables in section 5.10 cannot disagree.
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
try:
    import scienceplots  # noqa: F401
    STYLE = ["science", "nature", "no-latex"]
except Exception:  # noqa: BLE001
    STYLE = ["seaborn-v0_8-whitegrid"]

REPO = pathlib.Path(__file__).resolve().parent.parent
SRC = REPO / "measurement" / "out" / "measurement_report_fix.json"
# BOTH panels now read the reproducible corpus. The `_bs` artifact was measured before the Chinese
# candidate lists were made reproducible (docs/METHODS_LOG.md §1); replotting from it would put the
# withdrawn curve back beside prose that has been corrected to disown it.
SRC_RANK = REPO / "measurement" / "out" / "measurement_report_fix.json"
FIG_DIR = REPO / "viz" / "figures"

ARM_COLOR = {"rrc-zh": "#1b3a6b", "rrc-zh-gh": "#b4520f"}
ARM_LABEL = {"rrc-zh": "rrc-zh (CSCD prose)", "rrc-zh-gh": "rrc-zh-gh (GitHub prose)"}
CHANCE = 0.20


def main() -> int:
    if not SRC.exists():
        print("  [FAIL] no measurement artefact at %s" % SRC)
        print("         run scripts/analyze_measurement.py --rows _bs first")
        return 1
    payload = json.loads(SRC.read_text(encoding="utf-8"))
    disp = payload.get("state_displacement") or []
    if not disp:
        print("  [FAIL] the artefact carries no state_displacement block")
        return 1
    # The rank curve lives in the per-rank artefact, not this one: the curve's sampling unit is the
    # rank value, and reading it from the state-based artefact would draw the unbalanced curve the
    # report's section 5.10 explains cannot show the shape.
    rank_src = None
    f2 = []
    if SRC_RANK.exists():
        rank_src = SRC_RANK
        f2 = (json.loads(SRC_RANK.read_text(encoding="utf-8")).get("f2_rank_effect") or [])

    with plt.style.context(STYLE):
        plt.rcParams.update(NS.rcparams())
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(NS.DOUBLE_COL, 2.72))

        # ---- (a) shown against chosen
        lo, hi, ymax = 1e9, 0.0, 0.0
        for e in disp:
            cur = e.get("curve") or []
            if not cur:
                continue
            x = np.array([c["state_rank_median"] for c in cur], dtype=float)
            y = np.array([c["picked_rank_median"] for c in cur], dtype=float)
            lo, hi = min(lo, x.min()), max(hi, x.max())
            ymax = max(ymax, y.max())
            ax1.plot(x, y, marker="o", markersize=3.2, linewidth=1.4,
                     color=ARM_COLOR.get(e["arm"], "#444"),
                     label="%s (shift %+d)" % (ARM_LABEL.get(e["arm"], e["arm"]),
                                               int(e["overall_displacement"])))
            # the displacement as a vertical segment, at the first and last point only, so the
            # gap is legible without drawing a second curve over the first
            for k in (0, len(cur) - 1):
                ax1.annotate("", xy=(x[k], y[k]), xytext=(x[k], x[k]),
                             arrowprops=dict(arrowstyle="->", lw=0.9, color="#666"))
        ax1.plot([lo, hi], [lo, hi], linestyle=(0, (4, 3)), linewidth=0.9, color="#999",
                 label="chosen = shown (no shift)")
        # Rank spans more than two orders of magnitude across the two arms (1 to a few hundred), so
        # the axes are logarithmic AND carry explicit ticks. Three earlier attempts are each a
        # lesson: letting matplotlib choose gave a -10 tick (not a rank); log scale WITHOUT explicit
        # ticks let the locator add 10^3 against a maximum in the hundreds; a linear axis crowded
        # 1, 2, 3, 5 to a -7 pt gap. Log spacing with hand-chosen ticks satisfies all three.
        top = max(ymax, hi, 10.0) * 1.06
        niced = [t for t in (1, 2, 3, 5, 10, 20, 30, 50, 100, 200) if t <= top]
        ax1.set_xscale("log")
        ax1.set_yscale("log")
        ax1.set_xlim(1.0, top)
        ax1.set_ylim(1.0, top)
        ax1.set_xticks(niced)
        ax1.set_yticks(niced)
        ax1.set_xticklabels([str(t) for t in niced])
        ax1.set_yticklabels([str(t) for t in niced])
        ax1.set_xlabel("rank of the character shown\n(1 = commonest for its reading)")
        ax1.set_ylabel("rank of the candidate chosen")
        ax1.set_title("(a) the choice tracks the form shown,\nbut shifted toward rarer characters",
                      fontsize=7.4)
        ax1.legend(fontsize=5.4, frameon=False, loc="upper left")
        NS.style_axes(ax1, 'a')

        # ---- (b) what the shift costs
        arms = [e["arm"] for e in disp]
        xs = np.arange(len(arms))
        w = 0.36
        for i, e in enumerate(disp):
            cur = e.get("curve") or []
            if not cur:
                continue
            x = np.array([c["state_rank_median"] for c in cur], dtype=float)
            a = np.array([c["accuracy"] for c in cur], dtype=float)
            ax2.plot(x, a, marker="s", markersize=3.2, linewidth=1.4,
                     color=ARM_COLOR.get(e["arm"], "#444"),
                     label=ARM_LABEL.get(e["arm"], e["arm"]))
        ax2.axhline(CHANCE, linestyle=(0, (4, 3)), linewidth=0.9, color="#999",
                    label="chance (1 of 5)")
        ax2.set_xscale("log")
        ax2.set_xlim(1.0, top)
        ax2.set_xticks(niced)
        ax2.set_xticklabels([str(t) for t in niced])
        ax2.set_ylim(0.0, 0.45)
        ax2.set_yticks([0.1, 0.2, 0.3, 0.4])
        ax2.set_xlabel("rank of the character shown")
        ax2.set_ylabel("accuracy")
        ax2.set_title("(b) the cost, against the rank\nof the form shown", fontsize=7.4)
        ax2.legend(fontsize=5.4, frameon=False)
        NS.style_axes(ax2, 'b')

        # ---- (c) the rank falsifier itself: accuracy against the ROOT's rank, balanced per rank
        # value. Panel (b) is against the rank of the form shown; this is against the rank of the
        # answer, which is the quantity the input-method model says should order difficulty.
        if f2:
            rmax = 1.0
            for e in f2:
                cur = [c for c in (e.get("curve") or []) if c.get("n", 0) >= 5]
                if not cur:
                    continue
                x = np.array([c["rank"] for c in cur], dtype=float)
                y = np.array([c["acc"] for c in cur], dtype=float)
                rmax = max(rmax, x.max())
                ax3.plot(x, y, marker="o", markersize=3.0, linewidth=1.3,
                         color=ARM_COLOR.get(e["arm"], "#444"),
                         label="%s (%s)" % (ARM_LABEL.get(e["arm"], e["arm"]),
                                            e.get("direction", "")))
            ax3.axhline(CHANCE, linestyle=(0, (4, 3)), linewidth=0.9, color="#999",
                        label="chance (1 of 5)")
            rtop = max(rmax, 10.0) * 1.06
            rt = [t for t in (1, 2, 3, 5, 10, 20, 50) if t <= rtop]
            ax3.set_xscale("log")
            ax3.set_xlim(1.0, rtop)
            ax3.set_xticks(rt)
            ax3.set_xticklabels([str(t) for t in rt])
            ax3.set_ylim(0.0, 0.5)
            ax3.set_yticks([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
            ax3.set_xlabel("rank of the answer\n(1 = the input method's first offer)")
            ax3.set_ylabel("accuracy")
            ax3.set_title("(c) the rank falsifier\na balanced quota per rank", fontsize=7.4)
            ax3.legend(fontsize=5.0, frameon=False, loc="upper right")
            NS.style_axes(ax3, 'c')
        else:
            ax3.axis("off")
            ax3.text(0.5, 0.5, "no per-rank artefact", ha="center", va="center",
                     fontsize=6.5, color="#888", transform=ax3.transAxes)

        tot = sum(e["n"] for e in disp)
        fig.suptitle("The reading channel: a displacement, not a preference", fontsize=8.6, y=1.03)
        fig.tight_layout()

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / "fig_reading_displacement.png"
    NS.save_nature(fig, out.with_suffix(""))
    plt.close(fig)

    print("  arms        : %s" % ", ".join(arms))
    print("  items       : %d" % tot)
    for e in disp:
        print("  %-12s corr=%+.3f  shift=%+.1f rank positions  (%d bins)"
              % (e["arm"], e["corr_state_rank_vs_picked_rank"], e["overall_displacement"],
                 len(e.get("curve") or [])))
    print("  wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
