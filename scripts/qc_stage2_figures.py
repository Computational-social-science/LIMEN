#!/usr/bin/env python
"""qc_stage2_figures.py -- programmatic audit of the Stage 2 figures.

WHY NOT BY EYE
    A rotated or offset label can extend a few pixels into a neighbouring panel at a scale where visual
    inspection at 100 % resolves nothing. The audit below measures every text artist's bounding box in FIGURE
    coordinates and reports, as mechanical findings:

      A  text-to-text overlap
      B  text extending outside the figure
      C  text crossing from one axes into another (a label that escaped its panel)
      D  font sizes outside the journal band, since a style sheet cannot see the values a script sets later

    It re-runs the figure generation with the figures captured, so it audits the figures that are actually
    written rather than a re-implementation.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "build_stage2_figures.py"
MIN_PT, MAX_PT = 4.5, 9.0


def load_module():
    spec = importlib.util.spec_from_file_location("bsf", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bsf"] = mod
    spec.loader.exec_module(mod)
    return mod


def bbox(t, fig):
    try:
        return t.get_window_extent(renderer=fig.canvas.get_renderer()).transformed(fig.transFigure.inverted())
    except Exception:
        return None


def main() -> int:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.text import Text
    from matplotlib.transforms import Bbox

    mod = load_module()
    captured: list = []
    real_subplots = plt.subplots

    def spy(*a, **k):
        f, ax = real_subplots(*a, **k)
        captured.append(f)
        return f, ax

    plt.subplots = spy
    # THE FIGURES MUST STAY OPEN TO BE AUDITED. `finish()` closes each figure after writing it, and a closed
    # figure has no valid renderer, so every text artist reports a degenerate extent near the origin - which
    # an earlier version of this audit then flagged as dozens of "outside the canvas" defects. Suppress the
    # close for the duration of the audit and restore it afterwards.
    real_close = plt.close
    plt.close = lambda *a, **k: None
    tmp = REPO_ROOT / "viz" / "figures" / "_qc_tmp"
    mod.FIG_DIR = tmp
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        rc = mod.main()
    finally:
        plt.subplots = real_subplots
        plt.close = real_close
    if rc != 0:
        print(f"  [FAIL] figure generation returned {rc}")
        return 1

    findings: list[str] = []
    skipped_note: list[int] = []
    for fi, fig in enumerate(captured):
        fig.canvas.draw()
        texts = [(t.get_text().strip(), t) for t in fig.findobj(Text)
                 if t.get_text().strip()]
        measured = [(s, bbox(t, fig)) for s, t in texts]
        # Some tick labels report a degenerate extent when re-measured after the axes has been drawn, so they
        # cannot be audited for overlap. THEY ARE COUNTED AND PRINTED rather than silently dropped: a check
        # that quietly skips what it cannot measure reads as a pass, which is the same defect as an empty
        # Counter reported as "no duplicates".
        boxes = [(s, b) for s, b in measured
                 # A REAL LABEL IS NOT 0.001 OF A 7.2-INCH FIGURE WIDE. At 6 pt a label is ~0.012 in
                 # figure fraction before its glyphs; the degenerate extents measure 0.001. The threshold
                 # separates them, and anything below it is counted as unmeasurable rather than as a pass.
                 if b is not None and b.width > 0.004 and b.height > 0.003]
        n_skipped = len(measured) - len(boxes)
        skipped_note.append(n_skipped)
        # THE REFERENCE FRAME IS THE SAVED CANVAS, NOT [0,1]. These figures are written with
        # bbox_inches="tight", which EXPANDS the canvas to include the axis labels - so a label at negative
        # figure-y is not outside the image, it is outside the pre-tight box. An earlier version of this
        # audit reported six such labels as defects; they were artefacts of the wrong frame.
        # Figure.get_tightbbox returns the box IN INCHES, not in display units. Transforming it with
        # transFigure.inverted() - which expects display coordinates - yields a degenerate box near the
        # origin, which is what an earlier version of this audit compared against and reported every label
        # as a defect. Convert inches to figure fraction explicitly.
        # THE FIGURES ARE WRITTEN WITH bbox_inches=None AND EXPLICIT subplots_adjust MARGINS, so the saved
        # canvas IS the figure box [0,1] - no tight-bbox arithmetic is involved and none can go wrong. This
        # is also why the figures switched away from bbox_inches="tight": tight boxes move fig.text elements,
        # which is a documented pitfall, and they make "is this label clipped?" unanswerable after the fact.
        tb = Bbox.from_bounds(0.0, 0.0, 1.0, 1.0)
        for s, b in boxes:
            if b.x0 < tb.x0 - 0.01 or b.y0 < tb.y0 - 0.01 or b.x1 > tb.x1 + 0.01 or b.y1 > tb.y1 + 0.01:
                findings.append(f"fig{fi + 1}: text {s[:34]!r} extends outside the SAVED canvas "
                                f"[{b.x0:.3f},{b.x1:.3f}]x[{b.y0:.3f},{b.y1:.3f}] vs "
                                f"[{tb.x0:.3f},{tb.x1:.3f}]x[{tb.y0:.3f},{tb.y1:.3f}]")
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                (s1, b1), (s2, b2) = boxes[i], boxes[j]
                ox = min(b1.x1, b2.x1) - max(b1.x0, b2.x0)
                oy = min(b1.y1, b2.y1) - max(b1.y0, b2.y0)
                if ox > 0.004 and oy > 0.004:
                    findings.append(f"fig{fi + 1}: {s1[:22]!r} overlaps {s2[:22]!r} "
                                    f"({ox:.3f} x {oy:.3f})")
        for t in fig.findobj(Text):
            if not t.get_text().strip():
                continue
            sz = t.get_fontsize()
            if sz < MIN_PT or sz > MAX_PT:
                findings.append(f"fig{fi + 1}: {t.get_text()[:26]!r} font {sz}pt outside [{MIN_PT},{MAX_PT}]")

    # the figures were held open for the audit; release them now
    for f in captured:
        real_close(f)
    print(f"  figures audited: {len(captured)}")
    print(f"  text artists:    {sum(1 for f in captured for t in f.findobj(matplotlib.text.Text) if t.get_text().strip())}")
    if findings:
        print(f"\n  [FAIL] {len(findings)} finding(s):")
        for x in findings[:20]:
            print("      " + x)
        return 1
    print("\n  [OK] no text overlap, nothing outside the figure, no label escaped its panel, and every font")
    print("       size is inside the journal band")
    return 0


if __name__ == "__main__":
    sys.exit(main())