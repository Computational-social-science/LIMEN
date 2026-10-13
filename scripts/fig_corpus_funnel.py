"""Figure: what went in, where it was lost, and what came out -- as TWO stages, not one.

FIRST ATTEMPT AND WHY IT WAS WRONG. This figure was first drawn as a single cumulative bar per arm:
records read, minus script drops, minus margin drops, = items shipped. The bars did not reconcile --
rrc-en-word reads 36,133 records with 16,448 margin drops and ships 84,001 items, so "shipped" came
out larger than its own input. The reason is that the counts are in two different units: a record is a
pair read from a source corpus, an item is one multiple-choice question, and one record can yield up
to three items (an L1, an L2 and an L4 question about the same error). Drawing a funnel across the
two is a category error, and it hid the bigger problem underneath: records that cleared BOTH
record-level gates and then produced no layer at all were counted nowhere. On rrc-ja that is the
largest single loss in the corpus.

So the figure is two stages, each internally conserving:

  STAGE 1, record level (panel a): records read -- dropped as empty-or-identical -- dropped by the
      script gate -- dropped because no layer was available -- the rest produced at least one item.
      A 100% stacked bar, because the arms differ by two orders of magnitude and the question is
      where each corpus's loss concentrates, not how big it is.
  STAGE 2, item level (panel b): of the items a kept record could support, how many the margin gate
      removed. This is the gate the ranked layers are subject to, and stating it as a fraction of
      attempted items is what gives "110 drops" a base.
  (c) what actually shipped, by layer, on a log axis -- because the layer sets are NOT equal across
      arms, and that is a finding the report states, best seen in one place.

Every count is read from the manifest by way of the report state. If a count this figure needs is
missing, the figure FAILS rather than drawing a zero: a stale manifest would otherwise render a
plausible-looking panel in which a whole loss stage is invisible, which is the exact defect this
figure exists to expose.
"""
from __future__ import annotations

import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

import nature_style as NS   # shared journal specification
try:
    import scienceplots  # noqa: F401
    STYLE = ["science", "nature", "no-latex"]
except Exception:  # noqa: BLE001
    STYLE = ["seaborn-v0_8-whitegrid"]

REPO = pathlib.Path(__file__).resolve().parent.parent
STATE = REPO / "viz" / "report" / "state.js"
FIG_DIR = REPO / "viz" / "figures"

# Stage 1, in the order the builder applies it. The FIRST entry fires before the loop the other
# counters live in, which is why it was invisible for three builds: `build_arm` rebinds `records` to
# the unit-filtered list, so a count taken inside the loop cannot see it.
REC_STAGES = [("dropped_unit", "dropped: unit consistency", "#c9d3e0"),
              ("dropped", "dropped: empty or identical", "#dfe6ef"),
              ("dropped_script", "dropped: script gate", "#9db4d0"),
              ("dropped_no_layer", "dropped: no layer available", "#e0954a"),
              ("records_with_layer", "produced at least one question", "#1b3a6b")]
LAYER_COLOR = {"L1": "#8aa8c8", "L2": "#1b3a6b", "L3": "#4b6fa8", "L3del": "#6b8ab8",
               "L2c": "#b4520f", "L4": "#c9c9c9"}


def read_state(p: pathlib.Path) -> dict:
    s = p.read_text(encoding="utf-8")
    return json.loads(s[s.index("{"):s.rindex("}") + 1])


def main() -> int:
    if not STATE.exists():
        print("  [FAIL] no report state at %s; run export_report_state.py first" % STATE)
        return 1
    S = read_state(STATE)
    A = S.get("arms") or {}
    order = S.get("arm_order") or sorted(A)
    if not A:
        print("  [FAIL] the state carries no arms block")
        return 1

    # Loud failure rather than a drawn zero. These fields were added when the missing stages were
    # found; a manifest written before that has no value for them and must not be plotted.
    NEEDED = ("dropped_unit", "dropped_no_layer", "records_with_layer", "items_attempted",
              "dropped_duplicate")
    absent = [(a, k) for a in order for k in NEEDED if A.get(a, {}).get(k) is None]
    if absent:
        print("  [FAIL] %d arm(s) lack the fields this figure needs:" % len({a for a, _ in absent}))
        for a, k in absent:
            print("      %s: %s is None" % (a, k))
        print("      the manifest predates the record-level stage; rebuild RRC, then re-export state")
        return 1

    # Independently re-derive the identities here, so the figure cannot draw a stage that the
    # manifest itself does not reconcile.
    for a in order:
        e = A[a]
        got = ((e.get("dropped_unit") or 0) + (e.get("dropped") or 0)
               + (e.get("dropped_script") or 0) + (e.get("dropped_no_layer") or 0)
               + (e.get("records_with_layer") or 0))
        if (e.get("source_records") or 0) != got:
            print("  [FAIL] %s: record stage does not reconcile: source_records=%d vs the five "
                  "doors summing to %d" % (a, e.get("source_records") or 0, got))
            return 1
        att = e.get("items_attempted") or 0
        shp = e.get("n_items") or 0
        acc = shp + (e.get("dropped_margin") or 0) + (e.get("dropped_duplicate") or 0)
        if acc != att:
            print("  [FAIL] %s: item stage does not reconcile: shipped+margin+duplicate=%d but "
                  "attempted=%d" % (a, acc, att))
            return 1

    with plt.style.context(STYLE):
        plt.rcParams.update(NS.rcparams())
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(NS.DOUBLE_COL, 2.95))
        y = np.arange(len(order))

        # ---- (a) record level, 100% stacked
        for i, a in enumerate(order):
            e = A[a]
            total = sum((e.get(k) or 0) for k, _l, _c in REC_STAGES)
            if not total:
                continue
            left = 0.0
            for k, _l, col in REC_STAGES:
                v = e.get(k) or 0
                if not v:
                    continue
                w = 100.0 * v / total
                ax1.barh(i, w, left=left, height=0.62, color=col, edgecolor="#444", linewidth=0.3)
                # in-bar label only where the segment is wide enough to hold it without colliding
                if w >= 13.0:
                    ax1.text(left + w / 2, i, "%.0f%%" % w, ha="center", va="center",
                             fontsize=5.0, color="#111")
                left += w
            ax1.text(101.5, i, "%s rec." % format(e.get("source_records") or 0, ","),
                     va="center", fontsize=5.0, color="#333")
        ax1.set_yticks(y)
        ax1.set_yticklabels(order, fontsize=5.6)
        ax1.set_xlim(0, 100)
        ax1.set_xticks([25, 50, 75, 100])   # no 0 tick: it would collide with the y tick labels
        ax1.set_xticklabels(["25", "50", "75", "100"], fontsize=5.4)
        ax1.set_xlabel("share of records read (%)")
        ax1.set_title("Record level: where each corpus's\nrecords are lost", fontsize=7.4, loc="left")
        NS.style_axes(ax1, 'a')

        # ---- (b) item level, 100% stacked over attempted items
        for i, a in enumerate(order):
            e = A[a]
            att = e.get("items_attempted") or 0
            if not att:
                continue
            ship = e.get("n_items") or 0
            drop = e.get("dropped_margin") or 0
            dup = e.get("dropped_duplicate") or 0
            ws = 100.0 * ship / att
            wd = 100.0 * drop / att
            wu = 100.0 * dup / att
            ax2.barh(i, ws, height=0.62, color="#1b3a6b", edgecolor="#444", linewidth=0.3)
            if wd > 0:
                ax2.barh(i, wd, left=ws, height=0.62, color="#e0954a", edgecolor="#444",
                         linewidth=0.3)
            if wu > 0:
                ax2.barh(i, wu, left=ws + wd, height=0.62, color="#9db4d0", edgecolor="#444",
                         linewidth=0.3)
            if wd >= 13.0:
                ax2.text(ws + wd / 2, i, "%.0f%%" % wd, ha="center", va="center", fontsize=5.0,
                         color="#111")
            ax2.text(101.5, i, "%s items" % format(att, ","), va="center", fontsize=5.0,
                     color="#333")
        ax2.set_yticks(y)
        ax2.set_yticklabels([])
        ax2.set_xlim(0, 100)
        ax2.set_xticks([25, 50, 75, 100])
        ax2.set_xticklabels(["25", "50", "75", "100"], fontsize=5.4)
        ax2.set_xlabel("share of the items a kept record\ncould support (%)")
        ax2.set_title("Item level: the margin gate\nbites where there are ranked layers", loc="left",
                      fontsize=7.4)
        NS.style_axes(ax2, 'b')

        # ---- (c) what shipped, by layer
        layers = []
        for arm in order:
            for k in (A.get(arm, {}).get("layers") or {}):
                if k not in layers:
                    layers.append(k)
        layers.sort()
        for i, a in enumerate(order):
            lay = A.get(a, {}).get("layers") or {}
            left = 0.0
            for k in layers:
                v = lay.get(k) or 0
                if not v:
                    continue
                ax3.barh(i, v, left=left, height=0.62, color=LAYER_COLOR.get(k, "#999"),
                         edgecolor="#444", linewidth=0.3)
                left += v
            if left:
                ax3.text(left * 1.15, i, format(left, ","), va="center", fontsize=5.0, color="#222")
        top = max([(A[a].get("n_items") or 0) for a in order] + [1])
        tks = [t for t in (10, 100, 1000, 10000, 100000) if t <= top * 1.8]
        ax3.set_xscale("log")
        ax3.set_yticks(y)
        ax3.set_yticklabels([])
        ax3.set_xticks(tks)
        ax3.set_xticklabels([format(t, ",") for t in tks], fontsize=5.4)
        ax3.set_xlim(1, top * 2.2)
        ax3.set_xlabel("items shipped (log scale)")
        ax3.set_title("What shipped, by layer --\nand the layer sets are not equal", fontsize=7.4, loc="left")
        NS.style_axes(ax3, 'c')
        lh = [Rectangle((0, 0), 1, 1, facecolor=LAYER_COLOR.get(k, "#999"), edgecolor="#444",
                        linewidth=0.3, label=("L2c reading" if k == "L2c" else k)) for k in layers]
        ax3.legend(handles=lh, fontsize=5.0, frameon=False, ncol=max(1, len(layers)),
                   loc="lower right")

        # one shared legend for panel (a)'s stages plus the item-level drop, in the figure margin
        rh = [Rectangle((0, 0), 1, 1, facecolor=c, edgecolor="#444", linewidth=0.3, label=l)
              for _k, l, c in REC_STAGES]
        rh.append(Rectangle((0, 0), 1, 1, facecolor="#e0954a", edgecolor="#444", linewidth=0.3,
                            label="margin-dropped (item level, panel b)"))
        rh.append(Rectangle((0, 0), 1, 1, facecolor="#9db4d0", edgecolor="#444", linewidth=0.3,
                            label="duplicate (item level, panel b)"))
        fig.legend(handles=rh, loc="lower center", ncol=3, frameon=False, fontsize=5.2,
                   bbox_to_anchor=(0.5, -0.11))

        d = S.get("dataset", {})
        fig.suptitle("%s %s across %d arms: %s records in, %s questions out"
                     % (d.get("name", "RRC"), d.get("version", ""), len(order),
                        format(sum((A[a].get("source_records") or 0) for a in order), ","),
                        format(d.get("total_items") or 0, ",")), fontsize=8.6, y=1.02)
        fig.tight_layout(rect=(0, 0.05, 1, 1))

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / "fig_corpus_funnel.png"
    NS.save_nature(fig, out.with_suffix(""))
    plt.close(fig)

    print("  %-12s %8s %6s %6s %7s %8s %10s %8s %8s"
          % ("arm", "read", "unit", "empty", "script", "noLayer", "withLayer", "attempt", "shipped"))
    for a in order:
        e = A.get(a, {})
        print("  %-12s %8s %6s %6s %7s %8s %10s %8s %8s"
              % (a, format(e.get("source_records") or 0, ","),
                 format(e.get("dropped_unit") or 0, ","),
                 format(e.get("dropped") or 0, ","),
                 format(e.get("dropped_script") or 0, ","),
                 format(e.get("dropped_no_layer") or 0, ","),
                 format(e.get("records_with_layer") or 0, ","),
                 format(e.get("items_attempted") or 0, ","),
                 format(e.get("n_items") or 0, ",")))
    print("  record level: read = unit + empty + script + noLayer + withLayer"
          "    item level: attempt = shipped + margin + duplicate")
    print("  wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
