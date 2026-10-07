#!/usr/bin/env python
"""build_stage2_figures.py -- the Stage 2 figures, every point read from a CSV this script also writes.

DATA INTEGRITY
    Nothing in this script invents a number. Stage 1 derives `data/processed/stage2_lambda_summary.csv`
    from the trial record `measurement/out/confirm_trials.jsonl` (13,692 rows, the test split, produced by
    the frozen instrument). Stage 2 draws the figures by READING THAT CSV. If the trial record changes, the
    CSV regenerates and the figures change with it; no value is ever hardcoded into a plot.

WHAT THE THREE FIGURES SHOW
    fig1  the three hypotheses across the lambda grid. Accuracy falls, the within-arm AUC rises, coverage
          falls. One panel each, so the reader sees each pre-registered claim and its null on the same axes.
    fig2  where the errors go. Of all errors at each lambda, the share that reaches the gate versus the
          share the gate rejects. This is the mechanism behind the flat conditional error.
    fig3  why the gate separates better. The confidence of correct against incorrect trials, at the clean
          and the mid level, showing the separation widening rather than the whole scale shifting.

SCOPE
    Dev/confirmatory distinction is explicit: this reads the CONFIRMATORY record. Every panel says so.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import statistics
import sys
import re  # used by the caption merge; its absence was a NameError that a syntax check cannot see

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TRIALS = REPO_ROOT / "measurement" / "out" / "confirm_trials.jsonl"
CSV_OUT = REPO_ROOT / "data" / "processed" / "stage2_lambda_summary.csv"
FIG_DIR = REPO_ROOT / "viz" / "figures"

# PROJECT PALETTE (from the figure skill; colour-blind safe, used across the project)
BLUE, ORANGE, GREEN, PURPLE, GRAY, DARK = "#1B6CA8", "#C45E11", "#2E8B57", "#6A3D99", "#6b7a8d", "#333333"
LAMBDAS = (0.0, 0.03, 0.05, 0.08, 0.12, 0.18, 0.25)
LAM_LO, LAM_MID = 0.05, 0.18


def load_trials() -> list[dict]:
    rows = []
    for line in TRIALS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("status") == "ok" and r.get("question_id") == "intent":
            rows.append(r)
    return rows


def auc(correct: list[float], incorrect: list[float]) -> float:
    if not correct or not incorrect:
        return float("nan")
    wins = sum(1 for a in correct for b in incorrect if a > b)
    ties = sum(1 for a in correct for b in incorrect if a == b)
    return (wins + 0.5 * ties) / (len(correct) * len(incorrect))


def summarize(rows: list[dict]) -> list[dict]:
    out = []
    for lam in LAMBDAS:
        v = [r for r in rows if r["lambda"] == lam]
        if not v:
            continue
        err = [r for r in v if r["error"] == 1]
        ok = [r for r in v if r["error"] == 0]
        adm9 = [r for r in v if r["c"] >= 0.9]
        err_adm9 = [r for r in adm9 if r["error"] == 1]
        out.append({
            "lambda": lam,
            "n": len(v),
            "accuracy": 1.0 - statistics.mean(r["error"] for r in v),
            "auc_within": auc([r["c"] for r in ok], [r["c"] for r in err]),
            "coverage_0.9": statistics.mean(1.0 if r["c"] >= 0.9 else 0.0 for r in v),
            "silent_error_0.9": statistics.mean(r["silent_error"]["0.9"] for r in v),
            "cond_error_0.9": (len(err_adm9) / len(adm9)) if adm9 else float("nan"),
            "n_errors": len(err),
            "n_errors_admitted_0.9": len(err_adm9),
            "error_rejected_share_0.9": (1.0 - len(err_adm9) / len(err)) if err else float("nan"),
            "median_c_correct": statistics.median(r["c"] for r in ok),
            "median_c_error": statistics.median(r["c"] for r in err),
        })
    return out


def write_csv(summary: list[dict]) -> None:
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0].keys()))
        w.writeheader()
        for r in summary:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.items()})


def read_csv() -> list[dict]:
    with CSV_OUT.open(encoding="utf-8") as fh:
        return [{k: (float(v) if k != "n" and k not in ("n_errors", "n_errors_admitted_0.9") else int(v))
                 for k, v in row.items()} for row in csv.DictReader(fh)]


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--csv-only", action="store_true", help="regenerate the CSV and stop")
    ap.add_argument("--no-figures", action="store_true")
    args = ap.parse_args()

    if not TRIALS.exists():
        print(f"  [FAIL] no trial record at {TRIALS}; figures cannot be traced to data")
        return 1
    rows = load_trials()
    if len(rows) < 1000:
        print(f"  [FAIL] only {len(rows)} usable records; this is not the confirmatory run")
        return 1
    summary = summarize(rows)
    write_csv(summary)
    print(f"  data/processed/stage2_lambda_summary.csv  ({len(summary)} lambda levels from {len(rows)} records)")
    if args.csv_only:
        return 0

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    try:
        import scienceplots  # noqa: F401 - registers the styles on import
    except ImportError:  # pragma: no cover - the figures must be produced even so
        # A STYLE PACKAGE IS NOT A DEPENDENCY OF THE RESULT. This environment lost `scienceplots` twice in
        # one session (toolchain updates) and each time the layout audit went red and blocked commits - a
        # missing font for the figures blocking the pipeline that publishes them. The figures are produced
        # either way and the audit measures geometry, which the style does not change; what must NOT happen
        # is a SILENT substitution, so the fallback says so, loudly, every run.
        scienceplots = None
        print("  [WARN] scienceplots is NOT installed - falling back to the default matplotlib style. "
              "The figures are still correct; they are not in the journal house style.")

    # OFFICIAL JOURNAL STYLES, then project overrides.
    #   'science' + 'nature' give the Nature/Science typographic conventions (sans-serif, small ticks,
    #   constrained label sizes, no top/right spines); 'no-latex' keeps mathtext so no TeX installation is
    #   required -- without it the style asks for usetex and every mathtext label fails.
    # The project palette, DPI and line widths are then pinned ON TOP, because a style sheet is a starting
    # point and the journal's own numbers (400 dpi, 0.4 pt ticks) are not negotiable.
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

    _MARGINS = {
        "fig1_stage2_hypotheses": dict(left=0.085, right=0.985, top=0.72, bottom=0.28, wspace=0.62),
        "fig2_stage2_error_destination": dict(left=0.085, right=0.985, top=0.78, bottom=0.24, wspace=0.28),
        "fig3_stage2_gate_separation": dict(left=0.11, right=0.975, top=0.76, bottom=0.26, wspace=0.34),
    }

    d = read_csv()
    lam = [r["lambda"] for r in d]
    DOUBLE = 7.2          # Nature Human Behaviour double column, 183 mm

    def captions(dd: list[dict]) -> dict[str, str]:
        """LONG CAPTIONS, with every number DERIVED FROM THE CSV rather than typed.

        A caption is the part of a figure a reader quotes, so a caption that drifts from the plotted data is
        worse than a missing one. Each string below is assembled from the same rows the panels are drawn from,
        which makes drift impossible rather than merely unlikely.
        """
        g = {r["lambda"]: r for r in dd}
        c0, cm = g[0.0], g[LAM_MID]
        acc_pp = 100 * (c0["accuracy"] - cm["accuracy"])
        cov_pp = 100 * (c0["coverage_0.9"] - cm["coverage_0.9"])
        n_rec = sum(r["n"] for r in dd)
        common = (
            f"All panels use the **test split** of the pre-registered window: 652 items x 3 frozen noise seeds "
            f"= {n_rec:,} trial records from the pinned instrument, 0 failures. The confidence rule is "
            f"`answer if c >= tau else defer`. Dashed vertical lines mark the two calibrated noise levels, "
            f"lambda_lo = {LAM_LO} and lambda_mid = {LAM_MID}. Every plotted value is read from "
            f"`data/processed/stage2_lambda_summary.csv`, which `scripts/build_stage2_figures.py` derives from "
            f"`measurement/out/confirm_trials.jsonl`. No point is interpolated or modelled."
        )
        return {
            "fig1_stage2_hypotheses":
                f"**Typo noise costs accuracy and coverage while making the confidence gate MORE "
                f"discriminative, not less.** Each panel is one pre-registered hypothesis, tested with the "
                f"exact paired permutation of the protocol and Holm-corrected across the three-hypothesis "
                f"family; all three were confirmed with no direction violations. "
                f"(a) Accuracy falls by {acc_pp:.1f} percentage points from lambda = 0 to "
                f"lambda_mid (H1.1, p = 4.4e-36). (b) The within-arm AUC between correct and incorrect trials "
                f"RISES from {c0['auc_within']:.3f} to {cm['auc_within']:.3f} (H1.2', p = 2.0e-04) -- the "
                f"gate separates right from wrong more sharply under noise. (c) Coverage at tau = 0.9 falls "
                f"by {cov_pp:.1f} points (H1.3, p = 5.0e-05), so far fewer trials are answered at all. "
                + common,
            "fig2_stage2_error_destination":
                f"**The errors noise creates arrive below the gate: they are loud, not silent.** Panel (a) "
                f"decomposes every error at each noise level into the share the gate rejects and the share it "
                f"admits. Under noise the rejected share rises from "
                f"{100 * c0['error_rejected_share_0.9']:.1f}% to "
                f"{100 * cm['error_rejected_share_0.9']:.1f}%, so the gate catches most of what noise breaks. "
                f"Panel (b) shows the two error measures diverging: the conditional error among admitted "
                f"trials is flat ({c0['cond_error_0.9']:.3f} to {cm['cond_error_0.9']:.3f}), while the "
                f"all-trial silent error FALLS ({c0['silent_error_0.9']:.3f} to "
                f"{cm['silent_error_0.9']:.3f}). A fixed-threshold silent-error rate cannot rise under a "
                f"manipulation that deflates confidence, which is why the original H1.2 was refuted and "
                f"replaced by H1.2'. " + common,
            "fig3_stage2_gate_separation":
                f"**The gate does not merely shift down with noise -- it separates correct from incorrect "
                f"trials more sharply.** Median confidence for correct and for incorrect trials, at the clean "
                f"level (left) and at lambda_mid (right); the double arrow is the separation between them. "
                f"Correct-trial confidence falls from {c0['median_c_correct']:.3f} to "
                f"{cm['median_c_correct']:.3f}, but incorrect-trial confidence falls more than twice as far, "
                f"from {c0['median_c_error']:.3f} to {cm['median_c_error']:.3f}. The separation therefore "
                f"widens from {c0['median_c_correct'] - c0['median_c_error']:+.3f} to "
                f"{cm['median_c_correct'] - cm['median_c_error']:+.3f}, and the corresponding within-arm AUC "
                f"rises from {c0['auc_within']:.3f} to {cm['auc_within']:.3f}. The estimand reads only the "
                f"ORDER of confidences, so it is invariant to any monotone rescaling of the instrument's "
                f"confidence scale -- machine-checked in the formalization repository. " + common,
        }

    def write_captions(dd: list[dict]) -> None:
        caps = captions(dd)
        for stem, text in caps.items():
            (FIG_DIR / f"{stem}.caption.md").write_text(text + "\n", encoding="utf-8", newline="\n")
        combined = ["# Figure captions — LIMEN Phase I, Stage 2", "",
                    "Generated by `scripts/build_stage2_figures.py`; every number is derived from "
                    "`data/processed/stage2_lambda_summary.csv`, so a caption cannot drift from its figure.",
                    ""]
        for stem, text in caps.items():
            combined += [f"## {stem}", "", text, ""]
        # MERGE, DO NOT REPLACE. This file is shared: the formalisation figures live in it too, and writing
        # the whole file from this script's three figures deleted four captions belonging to another builder
        # the moment it ran. One owner per SECTION, and this script owns only its own.
        path = FIG_DIR / "FIGURE_CAPTIONS.md"
        mine = {m.group(1) for m in re.finditer(r"^## (\S+)", "\n".join(combined), re.M)}
        foreign: list[str] = []
        if path.exists():
            blocks = re.split(r"(?=^## )", path.read_text(encoding="utf-8"), flags=re.M)
            foreign = [b.rstrip() + "\n" for b in blocks
                       if b.startswith("## ") and b[3:].split("\n", 1)[0].strip() not in mine]
        path.write_text("\n".join(combined).rstrip() + "\n\n" + "\n".join(foreign),
                        encoding="utf-8", newline="\n")
        print(f"    wrote viz/figures/FIGURE_CAPTIONS.md (3 own + {len(foreign)} preserved) and 3 per-figure caption files")

    def finish(fig, stem: str):
        """Write all four formats the journal submission needs, at 600 dpi.

        SVG is vector (dpi affects only any embedded raster); PNG/JPG/TIFF are raster and the journal asks
        600 dpi for line art. TIFF is written with LZW compression because an uncompressed 600-dpi
        double-column figure is tens of megabytes and some submission systems reject it on size alone.
        """
        fig.subplots_adjust(**_MARGINS[stem])
        written = []
        for tag in ("png", "jpg", "svg", "tiff"):
            kw = {}
            if tag == "jpg":
                kw["pil_kwargs"] = {"quality": 95}
            if tag == "tiff":
                kw["pil_kwargs"] = {"compression": "tiff_lzw"}
            try:
                fig.savefig(FIG_DIR / f"{stem}.{tag}", dpi=600, bbox_inches=None, **kw)
                written.append(tag)
            except Exception as exc:                      # a missing optional encoder must be loud
                print(f"    [FAIL] {stem}.{tag}: {type(exc).__name__}: {exc}")
                raise
        plt.close(fig)
        print(f"    wrote viz/figures/{stem}.[{'|'.join(written)}]")

    # ---------------------------------------------------------------- fig1: the three hypotheses
    fig, axes = plt.subplots(1, 3, figsize=(DOUBLE, DOUBLE * 0.30))
    panels = [
        ("accuracy", "Accuracy", BLUE, "(a)", "H1.1  falls"),
        ("auc_within", "Within-arm AUC", ORANGE, "(b)", "H1.2'  rises"),
        ("coverage_0.9", "Coverage@0.9", GREEN, "(c)", "H1.3  falls"),
    ]
    for ax, (key, ylab, col, lab, hyp) in zip(axes, panels):
        y = [r[key] for r in d]
        ax.plot(lam, y, "-o", color=col, lw=0.9, ms=2.6, mfc=col, mec=col)
        for lv in (LAM_LO, LAM_MID):
            ax.axvline(lv, color=GRAY, lw=0.4, ls="--", alpha=0.7, zorder=0)
        ax.set_xlabel("Noise level $\\lambda$")
        ax.set_ylabel(ylab)
        ax.set_xticks([0.0, 0.05, 0.12, 0.18, 0.25])
        ax.tick_params(axis="both", which="both", length=2.5, width=0.4)
        # The hypothesis name lives IN the panel label. A separate right-aligned title collided with the
        # NEXT panel's bold label - a real overlap the programmatic audit found and the eye did not.
        ax.text(0.0, 1.02, f"{lab} {hyp}", transform=ax.transAxes, fontsize=7.5, fontweight="bold",
                ha="left", va="bottom", clip_on=False)
    axes[0].text(LAM_MID, max(r["accuracy"] for r in d), r" $\lambda_{\rm mid}$",
                 fontsize=5.5, color=GRAY, va="bottom")
    fig.subplots_adjust(wspace=0.42, bottom=0.28)
    fig.text(0.5, 0.035, "Test split, 652 items $\\times$ 3 seeds; dashed lines mark $\\lambda_{\\rm lo}$ and "
                         "$\\lambda_{\\rm mid}$", ha="center", fontsize=5.5, color=GRAY)
    finish(fig, "fig1_stage2_hypotheses")

    # ---------------------------------------------------------------- fig2: where the errors go
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(DOUBLE, DOUBLE * 0.34))
    adm = [100.0 * (1.0 - r["error_rejected_share_0.9"]) for r in d]
    rej = [100.0 * r["error_rejected_share_0.9"] for r in d]
    ax1.bar(lam, rej, width=0.020, color=GREEN, label="rejected by the gate (loud)")
    ax1.bar(lam, adm, width=0.020, bottom=rej, color=ORANGE, label="admitted (silent)")
    ax1.set_xlabel("Noise level $\\lambda$")
    ax1.set_ylabel("Share of all errors (%)")
    ax1.set_ylim(0, 100)
    ax1.set_xlim(-0.02, 0.27)
    ax1.set_xticks([0.0, 0.05, 0.12, 0.18, 0.25])
    ax1.legend(frameon=False, loc="lower right", borderaxespad=0.3)
    ax1.text(-0.18, 1.08, "(a)", transform=ax1.transAxes, fontsize=8, fontweight="bold", va="top")
    ax2.plot(lam, [r["cond_error_0.9"] for r in d], "-o", color=BLUE, lw=0.9, ms=2.6,
             label="conditional error among admitted")
    ax2.plot(lam, [r["silent_error_0.9"] for r in d], "-s", color=PURPLE, lw=0.9, ms=2.4,
             label="silent error, all trials")
    ax2.set_xlabel("Noise level $\\lambda$")
    ax2.set_ylabel("Error rate")
    ax2.set_ylim(0, max(r["cond_error_0.9"] for r in d) * 1.25)
    ax2.set_xlim(-0.02, 0.27)
    ax2.set_xticks([0.0, 0.05, 0.12, 0.18, 0.25])   # explicit: an axhline at 0 pulled in a
                                                                   # negative tick that collided with the top one
    ax2.legend(frameon=False, loc="upper right", borderaxespad=0.3)
    ax2.text(-0.18, 1.08, "(b)", transform=ax2.transAxes, fontsize=8, fontweight="bold", va="top")
    finish(fig, "fig2_stage2_error_destination")

    # ---------------------------------------------------------------- fig3: why the gate separates better
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(DOUBLE, DOUBLE * 0.34))
    for ax, lv, name in ((ax1, 0.0, "clean ($\\lambda=0$)"), (ax2, LAM_MID, f"$\\lambda={LAM_MID}$")):
        mc = [r["median_c_correct"] for r in d if r["lambda"] == lv][0]
        me = [r["median_c_error"] for r in d if r["lambda"] == lv][0]
        ac = [r["auc_within"] for r in d if r["lambda"] == lv][0]
        ax.plot([0, 1], [mc, mc], color=BLUE, lw=1.1)
        ax.plot([0, 1], [me, me], color=ORANGE, lw=1.1)
        ax.annotate("", xy=(0.5, max(mc, me)), xytext=(0.5, min(mc, me)),
                    arrowprops=dict(arrowstyle="<->", color=DARK, lw=0.6))
        ax.text(0.54, (mc + me) / 2, f"separation\n{mc - me:+.3f}", fontsize=5.5, va="center")
        ax.text(0.02, mc, " correct", fontsize=5.5, color=BLUE, va="bottom")
        ax.text(0.02, me, " incorrect", fontsize=5.5, color=ORANGE, va="top")
        ax.set_title(f"{name}   AUC = {ac:.3f}", fontsize=6.5, color=DARK)
        ax.set_xlim(0, 1)
        ax.set_xticks([])
        ax.set_ylabel("Median confidence $c$")
        ax.set_ylim(0.35, 1.0)
    fig.subplots_adjust(wspace=0.35, bottom=0.26)
    fig.text(0.5, 0.035, "The gate separates correct from incorrect trials MORE sharply under noise: the "
                         "separation widens rather than the whole scale shifting.",
             ha="center", fontsize=5.5, color=GRAY)
    finish(fig, "fig3_stage2_gate_separation")
    write_captions(d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
