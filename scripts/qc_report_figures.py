"""qc_report_figures.py -- the label-overlap and font-size audit the report's captions promise.

WHY THIS EXISTS. Two figure captions in the technical report stated that the guard suite audits their
figures "for label overlap and font size". Neither test was true. `qc_stage2_figures.py` audits the
stage-2 figure set (fig1-fig9), and the keyboard-channel figure was retired 2026-10-12 (see archive/);
the four figures embedded in the report had no layout audit at all. The captions were corrected to say
so, and this closes the gap rather than leaving a correction standing as a promise.

WHAT IT CHECKS
  1. no two text artists overlap, measured on their rendered bounding boxes after the canvas is drawn;
  2. every text artist is at or above MIN_PT (5.0 pt), the same band the rest of the suite enforces.

WHAT IT DELIBERATELY DOES NOT CHECK
  "Is anything outside the canvas?" is omitted, and the omission is the point. The report's figures are
  written with `bbox_inches="tight"`, which EXPANDS the saved canvas to include labels that lie outside
  the pre-tight figure box. In that frame the question has no well-defined answer: a label at negative
  figure-y is not clipped, it is in the expanded margin. `qc_stage2_figures.py` can ask it only because
  that figure set switched to `bbox_inches=None` with explicit margins. Asking it here would produce
  defects that are artefacts of the frame, which is how an earlier version of that audit came to report
  six non-existent failures. The two properties the captions name are the two checked.

HOW IT CAPTURES. The figure modules close each figure after writing it, and a closed figure has no valid
renderer, so every text artist reports a degenerate extent near the origin. The audit suppresses
`plt.close` for its duration and spies on `plt.subplots`, exactly as `qc_stage2_figures.py` does, and
points each module at a temporary directory so it cannot overwrite the deliverable it is auditing.

UNMEASURABLE ARTISTS ARE COUNTED AND PRINTED, not dropped. A check that silently skips what it cannot
measure reads as a pass.

NEGATIVE CONTROL
  --negative-test draws two labels at the same position and requires the audit to report the overlap,
  and draws one below MIN_PT and requires the font check to fire. Both must fire or the control reports
  itself inert.
"""
from __future__ import annotations

import argparse
import importlib.util
import pathlib
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
FIG_DIR = REPO / "viz" / "figures"

# The figures embedded in the report, with the attribute each declares for its output directory.
TARGETS = [
    ("fig_reading_displacement", "FIG_DIR"),
    ("fig_measurement_summary", "FIG_DIR"),
    ("fig_corpus_funnel", "FIG_DIR"),
]

# A degenerate extent is not a small label. From qc_stage2_figures: at 6 pt a real label is ~0.012 in
# figure fraction before its glyphs, while an unmeasured one reports ~0.001. Separating them keeps a
# measurement failure from being read as a pass.
MIN_W, MIN_H = 0.004, 0.003


def load_module(name: str):
    path = SCRIPTS / (name + ".py")
    spec = importlib.util.spec_from_file_location("_qcf_" + name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def audit_figures(captured: list, min_pt: float, overlap_floor: float) -> tuple[list[str], int, int]:
    """Returns (findings, artists_measured, artists_unmeasurable)."""
    from matplotlib.text import Text
    from matplotlib.transforms import Bbox

    findings: list[str] = []
    measured = 0
    skipped = 0
    for fi, fig in enumerate(captured, 1):
        fig.canvas.draw()
        boxes = []
        # ONLY matplotlib.text.Text -- BY CLASS, NOT BY PREDICATE. An earlier version matched on
        # "has get_text and get_fontsize", which also catches `TextArea` annotation boxes. A TextArea's
        # extent spans the whole box it draws, so every label placed inside it reported as overlapping
        # it: the audit produced four defects in the keyboard-channel figure that a class-restricted
        # audit of the same figure does not see. `fig.findobj(Text)` is what qc_stage2_figures.py uses,
        # and it is correct for exactly this reason.
        for t in fig.findobj(Text):
            try:
                s = t.get_text().strip()
                size = float(t.get_fontsize())
            except Exception:  # noqa: BLE001
                continue
            if not s:
                continue
            if size < min_pt - 1e-9:
                findings.append("fig %d: %r is %.2f pt, below the %.1f pt floor"
                                % (fi, s[:40], size, min_pt))
            b_renderer = fig.canvas.get_renderer()
            # THE BOX MUST BE IN FIGURE FRACTION, NOT DISPLAY UNITS. An earlier version of this audit
            # compared raw display-unit boxes (pixels) against the fraction thresholds below, so every
            # degenerate box measured ~1x1 pixels, sailed past a "<= 0.004" test, and the audit reported
            # all 1760 pairs as overlapping at "100% of the smaller box". The transform is what makes the
            # threshold mean anything, and qc_stage2_figures.py's helper does the same for the same reason.
            try:
                bb = t.get_window_extent(renderer=b_renderer).transformed(fig.transFigure.inverted())
                bb = Bbox(bb)
            except Exception:  # noqa: BLE001
                skipped += 1
                continue
            if bb.width <= MIN_W and bb.height <= MIN_H:
                skipped += 1
                continue
            measured += 1
            boxes.append((s, bb))
        # pairwise overlap, on rendered boxes
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                s1, b1 = boxes[i]
                s2, b2 = boxes[j]
                ox = min(b1.x1, b2.x1) - max(b1.x0, b2.x0)
                oy = min(b1.y1, b2.y1) - max(b1.y0, b2.y0)
                if ox <= 0 or oy <= 0:
                    continue
                area = ox * oy
                smaller = min(b1.width * b1.height, b2.width * b2.height)
                if smaller > 0 and area / smaller < overlap_floor:
                    continue  # touching boxes; not a legibility defect
                findings.append("fig %d: %r overlaps %r by %.1f%% of the smaller box"
                                % (fi, s1[:28], s2[:28], 100.0 * area / smaller if smaller else 0.0))
    return findings, measured, skipped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--negative-test", action="store_true")
    ap.add_argument("--min-pt", type=float, default=None)
    ap.add_argument("--overlap-floor", type=float, default=0.06)
    args = ap.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import nature_style as NS

    min_pt = args.min_pt if args.min_pt is not None else NS.MIN_PT
    sys.path.insert(0, str(SCRIPTS))

    if args.negative_test:
        fig, ax = plt.subplots(figsize=(3, 2))
        ax.text(0.5, 0.5, "overlapping label alpha", fontsize=7)
        ax.text(0.5, 0.5, "overlapping label beta", fontsize=7)
        ax.text(0.1, 0.1, "too small", fontsize=3)
        fig.canvas.draw()
        f, m, s = audit_figures([fig], min_pt, args.overlap_floor)
        plt.close(fig)
        hit_overlap = any("overlaps" in x for x in f)
        hit_font = any("below the" in x for x in f)
        if hit_overlap and hit_font:
            print("  [OK] negative control fires: the overlap and the sub-floor font are both reported")
            return 0
        print("  [FAIL] the control did not fire (%d finding(s), overlap=%s font=%s) -- it is inert"
              % (len(f), hit_overlap, hit_font))
        for x in f:
            print("         %s" % x)
        return 1

    captured: list = []
    real_subplots = plt.subplots

    def spy(*a, **k):
        fig, ax = real_subplots(*a, **k)
        captured.append(fig)
        return fig, ax

    plt.subplots = spy
    real_close = plt.close
    plt.close = lambda *a, **k: None

    rc = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = pathlib.Path(tmpdir)
        try:
            for name, attr in TARGETS:
                mod = load_module(name)
                if not hasattr(mod, attr):
                    print("  [FAIL] %s has no %s -- the audit cannot redirect its output, so it would "
                          "overwrite the deliverable it checks" % (name, attr))
                    rc = 1
                    continue
                setattr(mod, attr, tmp)
                r = mod.main()
                rc = rc or (r if isinstance(r, int) else 0)
        finally:
            plt.subplots = real_subplots
            plt.close = real_close

    if not captured:
        print("  [FAIL] no figure was captured -- the audit measured nothing, which is not a pass")
        return 1

    findings, measured, skipped = audit_figures(captured, min_pt, args.overlap_floor)
    print("  figures audited : %d" % len(captured))
    print("  text measured   : %d" % measured)
    print("  unmeasurable    : %d  (degenerate extent; counted, not dropped)" % skipped)
    if findings:
        print()
        for x in findings[:25]:
            print("  [FAIL] %s" % x)
        if len(findings) > 25:
            print("  ... and %d more" % (len(findings) - 25))
        return 1
    print("  [OK] no text overlap, and every font size is at or above the %.1f pt floor" % min_pt)
    return rc


if __name__ == "__main__":
    sys.exit(main())
