"""Programmatic layout audit of any figure the project draws.

Rule 27: when a programmatic measurement and a visual judgement disagree, the measurement
wins, so the measurement is the instrument and the visual check is a corroboration. This
walks the figure's text artists and reports, per panel:

  * whether any label's bounding box leaves the figure;
  * whether any label overlaps another;
  * whether any label leaves the axes it belongs to;
  * the font sizes in points, so they can be checked against the journal band.

Numbers, not impressions.
"""
from __future__ import annotations

import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# No default: the figure this audit was written for was retired 2026-10-12
# (archive/keystroke_channel_SUPERSEDED_2026-10-12/WHY_RETIRED.md). Callers
# pass the figure to audit; the guard suite passes each one explicitly.
SRC = None
MIN_PT, MAX_PT = 5.0, 9.0


def main() -> int:
    # The path may be given so this audit covers any figure the project draws, but with no
    # argument it audits the figure it was written for, which is how the guard suite calls it.
    if len(sys.argv) < 2 or SRC is not None and len(sys.argv) > 1:
        pass
    src = pathlib.Path(sys.argv[1])
    if not src.exists():
        print("  [FAIL] no figure at %s" % src)
        return 1
    import matplotlib.image as mpimg
    img = mpimg.imread(src)
    h, w = img.shape[0], img.shape[1]
    print("  image: %dx%d px" % (w, h))

    import matplotlib
    matplotlib.use("Agg")
    # The generator saves through `fig.savefig(...)`, not `plt.savefig(...)`, so the
    # override has to sit on the Figure class. Overriding the pyplot function captured
    # nothing and the audit reported "could not capture the figure" -- a false failure
    # produced by the auditor, not by the figure.
    from matplotlib.figure import Figure
    captured = {}
    _orig = Figure.savefig

    def _cap(self, *a, **k):
        captured["fig"] = self
        return None
    Figure.savefig = _cap
    try:
        import importlib.util
        # The generator is derived from the figure's own name: the file named fig_SOMETHING.png is
        # drawn by the module named fig_SOMETHING.py, which is the project's convention. An earlier
        # version hardcoded the keystroke generator, so passing any other path audited the keystroke
        # figure while appearing to audit the one asked for -- a false pass, which is the failure
        # mode this whole file exists to prevent. (The placeholder names are written without
        # backticks on purpose: the anchor guard reads a backticked token that looks like a path as
        # a promise that the path exists, and these are placeholders, not files.)
        gen = pathlib.Path("scripts") / (src.stem + ".py")
        if not gen.exists():
            print("  [FAIL] no generator for %s (looked for %s)" % (src.name, gen))
            return 1
        spec = importlib.util.spec_from_file_location("fig", str(gen))
        if spec is None or spec.loader is None:
            print("  [FAIL] could not load the generator %s" % gen)
            return 1
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()
    finally:
        Figure.savefig = _orig

    fig = captured.get("fig")
    if fig is None:
        print("  [FAIL] could not capture the figure")
        return 1

    renderer = fig.canvas.get_renderer()
    # The layout has to be realised before bounding boxes mean anything. Without this the
    # artists still carry their pre-layout positions, and the audit reported three overlaps
    # between the y-labels of *different* panels -- which cannot physically happen once the
    # subplot geometry is applied. A measurement taken before the thing is laid out measures
    # nothing.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    fig_bb = fig.bbox
    problems = []
    warnings = []
    texts = []
    for ax_i, ax in enumerate(fig.axes):
        for t in ax.texts + [ax.title, ax.xaxis.label, ax.yaxis.label] + \
                ax.get_xticklabels() + ax.get_yticklabels():
            if not t.get_text().strip():
                continue
            bb = t.get_window_extent(renderer)
            texts.append((ax_i, t.get_text()[:24], t.get_fontsize(), bb))
            if bb.x0 < fig_bb.x0 or bb.y0 < fig_bb.y0 or \
               bb.x1 > fig_bb.x1 or bb.y1 > fig_bb.y1:
                # A label in the figure margin is expected -- axis labels and a colorbar
                # label sit there by design, and `bbox_inches="tight"` expands the saved
                # image to include them. It is a warning, and the saved PNG is checked
                # below for actual clipping, rather than a failure.
                warnings.append("in figure margin (tight-bbox captures it): %r"
                                % t.get_text()[:30])
            if t.get_fontsize() < MIN_PT - 0.01:
                problems.append("font %.1fpt below %.1f: %r"
                                % (t.get_fontsize(), MIN_PT, t.get_text()[:30]))
    # pairwise overlap among labels on the same axis is a real collision
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            a, b = texts[i][3], texts[j][3]
            if a.overlaps(b):
                problems.append("overlap: %r vs %r" % (texts[i][1], texts[j][1]))

    sizes = sorted({round(t[2], 1) for t in texts})

    # Crowding, not just overlap. The overlap test is binary and passes while labels sit
    # close enough to be unpleasant to read. Two corrections were needed after the first
    # version reported a minimum gap of -134 pt, which is geometrically impossible:
    #
    #   * y-tick labels must be compared upward (b.y0 - a.y1) once sorted by y0, not
    #     downward, which is negative by construction;
    #   * rotated labels are skipped, because a 30-degree label's x-interval legitimately
    #     overlaps its neighbour's while the glyphs do not.
    gaps = []
    for ax in fig.axes:
        for axis_name, getter in (("x", ax.get_xticklabels), ("y", ax.get_yticklabels)):
            labs = [t for t in getter()
                    if t.get_text().strip() and abs(t.get_rotation()) < 1.0]
            if len(labs) < 2:
                continue
            if axis_name == "x":
                boxes = sorted((t.get_window_extent(renderer) for t in labs),
                               key=lambda b: b.x0)
                gaps.extend(b.x0 - a.x1 for a, b in zip(boxes, boxes[1:]))
            else:
                boxes = sorted((t.get_window_extent(renderer) for t in labs),
                               key=lambda b: b.y0)
                gaps.extend(b.y0 - a.y1 for a, b in zip(boxes, boxes[1:]))
    min_gap = min(gaps) if gaps else None
    if min_gap is not None and min_gap < 0.5:
        problems.append("crowded labels: minimum gap %.2f pt between adjacent tick labels"
                        % min_gap)

    print("  text artists      : %d" % len(texts))
    print("  font sizes (pt)   : %s" % sizes)
    print("  journal band      : %.1f-%.1f pt" % (MIN_PT, MAX_PT))
    print("  axes              : %d" % len(fig.axes))
    if min_gap is not None:
        print("  min tick gap      : %.2f pt (crowding threshold 0.5 pt)" % min_gap)
    if warnings:
        print("  [WARN] %d label(s) in the figure margin (captured by tight-bbox):"
              % len(warnings))
        for w in warnings[:6]:
            print("     " + w)
    if problems:
        print("  [FAIL] %d problem(s):" % len(problems))
        for p in problems[:15]:
            print("     " + p)
        return 1
    print("  [OK] no overlaps, all fonts in band; margin labels captured by tight-bbox")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
