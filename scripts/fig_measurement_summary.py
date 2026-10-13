"""Figure: the measurement, at a glance -- four panels, one claim each.

The report carried the measurement as tables (16 of them) and no figure, so the four claims §5 makes
had to be assembled by the reader from numbers in different sections. This figure is the assembly:

  (a) WITHIN AN ARM: the ranked layer against the unrelated-form control, paired by state, McNemar.
      This is the design's own contrast -- the same states, the same candidates' surface form, only
      the decoy rule changed -- so it is the only contrast here that needs no arm-to-arm assumption.
  (b) BETWEEN SCRIPTS: accuracy on the identical control layer, six arms, one axis. The control layer
      is the only layer every arm has, which is why the comparison is drawn there and not on accuracy
      overall (section 5.4 states the same restriction).
  (c) AGAINST RECOVERABILITY: accuracy against the probability the model assigns the correct
      candidate. The corpus is built to carry this axis, so the figure shows whether the model's
      behaviour follows it.
  (d) SILENT FAILURE: accuracy against the probability assigned to whatever the model DID choose.
      The protocol's dependent variable is the pair (wrong, confident), and this panel is where that
      pair would be visible. A point far above the diagonal is a layer the model is confident about
      and wrong on.

Every number is read from the analyser's artefacts, so a panel cannot disagree with the table it
illustrates. Sampling scheme is stated per panel because it differs by design: (a) and (b) need whole
states for the pairing, (c) and (d) are per-item rates under the balanced scheme.
"""
from __future__ import annotations

import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

import nature_style as NS   # the shared specification: widths, type sizes, tick weights, outputs

try:
    import scienceplots  # noqa: F401
    STYLE = ["science", "nature", "no-latex"]
except Exception:  # noqa: BLE001
    STYLE = ["seaborn-v0_8-whitegrid"]

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "measurement" / "out"
# BOTH point at the reproducible corpus (docs/METHODS_LOG.md §1). The `_bs`/`_bal` pair was
# measured before the Chinese candidate lists were made reproducible, so a figure drawn from
# them would put the withdrawn numbers back beside prose that has been corrected to disown them.
SRC_BS = OUT / "measurement_report_fix.json"
SRC_BAL = OUT / "measurement_report_fix.json"
FIG_DIR = REPO / "viz" / "figures"
CHANCE = 0.20

# One visual channel per arm, and the same channel in every panel.
ARM_COLOR = {"rrc-en": "#1b3a6b", "rrc-en-word": "#5b8ac4", "rrc-ru": "#2e7d5b",
             "rrc-ja": "#8a6d1f", "rrc-zh": "#b4520f", "rrc-zh-gh": "#d98b4a"}
ARM_LABEL = {"rrc-en": "rrc-en", "rrc-en-word": "rrc-en-word", "rrc-ru": "rrc-ru",
             "rrc-ja": "rrc-ja", "rrc-zh": "rrc-zh", "rrc-zh-gh": "rrc-zh-gh"}
LAYER_MARK = {"L1": "o", "L2": "s", "L2c": "^", "L4": "D"}


def load(p: pathlib.Path) -> dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    bs, bal = load(SRC_BS), load(SRC_BAL)
    if not bal:
        print("  [FAIL] no balanced artefact at %s" % SRC_BAL)
        print("         run scripts/analyze_measurement.py --rows _fix first")
        return 1
    paired = bs.get("paired_ranked_vs_L4") or []
    cross = bs.get("cross_arm_L4") or []
    acc = bal.get("accuracy") or []
    proot = bal.get("p_root") or []
    if not (paired and cross and acc and proot):
        print("  [FAIL] an artefact is missing a block: paired=%d cross=%d acc=%d p_root=%d"
              % (len(paired), len(cross), len(acc), len(proot)))
        return 1

    # join recoverability onto accuracy by (arm, layer)
    pmap = {(e["arm"], e["layer"]): e for e in proot}

    with plt.style.context(STYLE):
        plt.rcParams.update(NS.rcparams())   # the specification overrides the style sheet
        fig, axes = plt.subplots(2, 2, figsize=(NS.DOUBLE_COL, 5.5))
        ax_a, ax_b, ax_c, ax_d = axes.ravel()

        # ---- (a) within-arm paired contrast
        ord_a = sorted(paired, key=lambda e: e["drop"])
        y = np.arange(len(ord_a))
        for i, e in enumerate(ord_a):
            col = ARM_COLOR.get(e["arm"], "#444")
            ax_a.barh(i, e["drop"], height=0.6, color=col,
                      edgecolor="#222", linewidth=0.4)
            # the test statistic is printed rather than the word "significant": the chi-square is
            # what a reader can check, and one arm here is not significant, which the label must say.
            tag = ("chi2=%.1f" % e["mcnemar_chi2"]) if e.get("significant") else \
                  ("chi2=%.2f, n.s." % e["mcnemar_chi2"])
            # One arm's drop is negative, so its bar runs left of zero; anchoring every label to the
            # bar's tip put that one inside the y tick labels. Labels are anchored to zero and pushed
            # outward, so they all clear the axis corner regardless of sign.
            if e["drop"] >= 0:
                ax_a.text(e["drop"] + 0.006, i, " %s  n=%d" % (tag, e["n_pairs"]),
                          va="center", fontsize=5.0, color="#333")
            else:
                ax_a.text(0.006, i, " %s  n=%d " % (tag, e["n_pairs"]),
                          va="center", ha="left", fontsize=5.0, color="#333")
        ax_a.axvline(0, color="#333", linewidth=0.7)
        ax_a.set_yticks(y)
        ax_a.set_yticklabels(["%s\n(%s vs L4)" % (ARM_LABEL.get(e["arm"], e["arm"]),
                                                  e["ranked_layer"]) for e in ord_a], fontsize=5.4)
        ax_a.set_xlim(0, max(e["drop"] for e in ord_a) * 1.46)
        ax_a.set_xlabel("accuracy drop on the ranked layer\n(paired by state, McNemar)")
        ax_a.set_title("the decoy rule is what costs\naccuracy within each arm", fontsize=NS.BASE_PT)
        NS.style_axes(ax_a)

        # ---- (b) between scripts on the shared control layer
        # Ordered by each arm's own L4 accuracy, so the vertical position IS the measurement and the
        # connector only carries the test outcome. Pairs that the test separated are solid.
        l4 = {a: acc_of(acc, a, "L4") for a in ARM_COLOR}
        hi = sorted([a for a in ARM_COLOR if l4[a]], key=lambda a: -l4[a][0])
        rank = {a: i for i, a in enumerate(hi)}
        n_arms = len(hi)
        sep = {(min(rank[e["a"]], rank[e["b"]]), max(rank[e["a"]], rank[e["b"]]))
               for e in cross if e.get("separated")
               and e["a"] in rank and e["b"] in rank}
        for i in range(n_arms):
            for j in range(i + 1, n_arms):
                is_sep = (i, j) in sep
                ax_b.plot([0, 1], [n_arms - 1 - i, n_arms - 1 - j],
                          color=("#2e7d5b" if is_sep else "#bbb"),
                          linewidth=(1.0 if is_sep else 0.5),
                          linestyle=("-" if is_sep else (0, (2, 2))), zorder=1)
        for a in hi:
            k = n_arms - 1 - rank[a]
            col = ARM_COLOR.get(a, "#444")
            ax_b.plot([0], [k], marker="o", markersize=4.0, color=col, zorder=3)
            ax_b.plot([1], [k], marker="o", markersize=4.0, color=col, zorder=3)
            ax_b.text(1.06, k, "%s  %.2f (n=%d)" % (a, l4[a][0], l4[a][1]),
                      va="center", fontsize=5.2, color="#333")
        ax_b.set_xlim(-0.07, 1.78)
        ax_b.set_ylim(-0.7, n_arms - 0.3)
        ax_b.set_xticks([0, 1])
        ax_b.set_xticklabels(["chance\n(0.20)", "measured"], fontsize=5.6)
        ax_b.set_yticks([])
        ax_b.set_title("on the one layer every arm has,\nthe scripts separate", fontsize=NS.BASE_PT)
        NS.style_axes(ax_b)
        ax_b.spines["left"].set_visible(False)   # no y ticks to carry on this panel
        ax_b.text(-0.05, -0.58, "solid = the two arms' accuracies differ (|z|>1.96); dotted = not",
                  fontsize=NS.MIN_PT, color="#555")

        # ---- (c) recoverability against accuracy
        for e in acc:
            p = pmap.get((e["arm"], e["layer"]))
            if not p or not p.get("n"):
                continue
            col = ARM_COLOR.get(e["arm"], "#444")
            mk = LAYER_MARK.get(e["layer"], "o")
            ax_c.errorbar(p["p50"], e["accuracy"],
                          yerr=[[max(0.0, e["accuracy"] - e["ci95"][0])],
                                [max(0.0, e["ci95"][1] - e["accuracy"])]],
                          fmt=mk, markersize=3.6, color=col, ecolor=col, elinewidth=0.7,
                          capsize=1.2, markeredgecolor="#222", markeredgewidth=0.3)
        ax_c.axhline(CHANCE, linestyle=(0, (4, 3)), linewidth=0.9, color="#999")
        ax_c.text(0.62, CHANCE + 0.012, "chance", fontsize=5.0, color="#777")
        ax_c.set_xlim(0, 1.0)
        ax_c.set_ylim(0, 1.02)
        # No 0.0 tick on the x axis: at the origin a centred x label and a right-aligned y label meet
        # and overlap, and neither 0.0 carries information here (the axis limit says it).
        ax_c.set_xticks([0.25, 0.5, 0.75, 1.0])
        ax_c.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax_c.set_xlabel("median probability on the correct candidate")
        ax_c.set_ylabel("accuracy")
        ax_c.set_title("the model tracks the recoverability\nthe corpus carries", fontsize=NS.BASE_PT)
        NS.style_axes(ax_c)

        # ---- (d) silent failure
        for e in acc:
            col = ARM_COLOR.get(e["arm"], "#444")
            mk = LAYER_MARK.get(e["layer"], "o")
            ax_d.plot(e["accuracy"], e["p_max_median"], marker=mk, markersize=3.6, color=col,
                      markeredgecolor="#222", markeredgewidth=0.3)
        ax_d.plot([0, 1], [0, 1], linestyle=(0, (4, 3)), linewidth=0.9, color="#999")
        ax_d.text(0.52, 0.545, "confidence = accuracy", fontsize=5.0, color="#777", rotation=34)
        ax_d.axvline(CHANCE, color="#ccc", linewidth=0.7)
        # the region that names the failure: wrong more often than chance yet confident
        ax_d.axhspan(0.5, 1.0, xmin=0.0, xmax=CHANCE, color="#b4520f", alpha=0.06, zorder=0)
        ax_d.text(0.012, 0.93, "wrong and\nconfident", fontsize=5.0, color="#b4520f", va="top")
        ax_d.set_xlim(0, 1.0)
        ax_d.set_ylim(0, 1.0)
        ax_d.set_xticks([0.25, 0.5, 0.75, 1.0])   # see the note in panel (c) on the missing 0.0
        ax_d.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax_d.set_xlabel("accuracy")
        ax_d.set_ylabel("median probability on the candidate chosen")
        ax_d.set_title("every layer sits above the diagonal:\nwrong answers still carry confidence",
                       fontsize=NS.BASE_PT)
        NS.style_axes(ax_d)

        # Panel labels, bold lowercase at the specification's size. They are placed as a separate
        # mark rather than as a "(a)" prefix in the title, which is what the journals set.
        for _ax, _letter in ((ax_a, "a"), (ax_b, "b"), (ax_c, "c"), (ax_d, "d")):
            NS.panel_label(_ax, _letter)

        # one legend for the arm colours, in the figure margin rather than in a panel
        handles = [plt.Line2D([], [], marker="o", linestyle="none", markersize=4,
                              color=ARM_COLOR[a], markeredgecolor="#222", markeredgewidth=0.3,
                              label=ARM_LABEL[a]) for a in sorted(ARM_COLOR)]
        lh = [plt.Line2D([], [], marker=m, linestyle="none", markersize=4, color="#444",
                         label=("reading layer (L2c)" if k == "L2c" else k))
              for k, m in LAYER_MARK.items()]
        fig.legend(handles=handles, loc="lower center", ncol=6, frameon=False, fontsize=5.4,
                   bbox_to_anchor=(0.34, -0.035), title="arm", title_fontsize=5.4)
        fig.legend(handles=lh, loc="lower center", ncol=4, frameon=False, fontsize=5.4,
                   bbox_to_anchor=(0.83, -0.035), title="marker", title_fontsize=5.4)
        # No figure title inside the image: the journals set the title in the caption, so a burned-in
        # one duplicates text the document already owns and cannot be restyled or reflowed.
        fig.tight_layout(rect=(0, 0.045, 1, 1))

    out = FIG_DIR / "fig_measurement_summary.png"
    NS.save_nature(fig, FIG_DIR / "fig_measurement_summary")
    plt.close(fig)

    print("  (a) paired arms      : %d" % len(paired))
    for e in ord_a:
        print("      %-12s %-4s drop=%+.4f  chi2=%6.2f  n=%d  %s"
              % (e["arm"], e["ranked_layer"], e["drop"], e["mcnemar_chi2"], e["n_pairs"],
                 "sig" if e["significant"] else "n.s."))
    print("  (b) cross-arm pairs  : %d, separated %d"
          % (len(cross), sum(1 for e in cross if e.get("separated"))))
    print("  (c)/(d) arm-layer pts: %d" % sum(1 for e in acc if (e["arm"], e["layer"]) in pmap))
    print("  wrote %s" % out)
    return 0


def acc_of(acc: list[dict], arm: str, layer: str):
    for e in acc:
        if e["arm"] == arm and e["layer"] == layer:
            return (e["accuracy"], e["n"])
    return None


if __name__ == "__main__":
    sys.exit(main())
