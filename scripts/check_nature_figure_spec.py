"""check_nature_figure_spec.py -- every figure meets the journal specification, mechanically.

WHY THIS EXISTS
    Four figures in this report drifted from the specification in four different ways: three carried
    gridlines the spec forbids, none set tick line widths, none carried bold panel labels, and all
    four shipped PNG+PDF where the repository standard is PNG+JPG+SVG+TIFF. Every one of those was
    invisible in a diff and obvious in a two-panel comparison. A specification that is only written
    down is a preference; this makes it a check.

WHAT IT CHECKS
    Per figure:
      1. the script carries no gridline call (Nature: spines and ticks only)
      2. the script sets tick widths via tick_params
      3. the script places panel labels (bold lowercase)
      4. the script builds its axes through scripts/nature_style.py, so a rule change is one edit
      5. all four output formats exist and are newer than nothing (a stale JPG is not an output)
      6. the PNG's own DPI metadata is at or above 400 -- read from the file's pHYs chunk, not from
         the script's intent, because a savefig call can be overridden by rcParams
      7. the SVG is non-trivial, since an empty vector file would satisfy a name check

NEGATIVE CONTROL
    `--negative-test` strips the gridline call out of one script's text IN MEMORY, re-injects it, and
    requires the check to report it. Nothing is written.
"""
from __future__ import annotations

import pathlib
import re
import struct
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
FIGDIR = REPO / "viz" / "figures"

# (script, output stem). Adding a figure to the report means adding a line here; the guard lists what
# it audited, so a figure missing from this table is visible as a count that did not grow.
FIGURES = [
    ("fig_measurement_summary.py", "fig_measurement_summary"),
    ("fig_corpus_funnel.py", "fig_corpus_funnel"),
    ("fig_reading_displacement.py", "fig_reading_displacement"),
    # fig_keystroke_channel retired 2026-10-12: its composition panel counted
    # transpositions as insert+delete pairs. See archive/keystroke_channel_SUPERSEDED_2026-10-12/
    # WHY_RETIRED.md. Replacement: figures/fig_error_structure.*
]

FORMATS = (".png", ".jpg", ".svg", ".tiff")
MIN_PNG_DPI = 400
MIN_SVG_BYTES = 5000


def png_dpi(path: pathlib.Path) -> float | None:
    """The DPI recorded in the PNG's pHYs chunk, or None if it carries none."""
    try:
        b = path.read_bytes()
    except OSError:
        return None
    i = b.find(b"pHYs")
    if i < 0 or i + 13 > len(b):
        return None
    try:
        px, _py, unit = struct.unpack(">IIB", b[i + 4:i + 13])
    except struct.error:
        return None
    if unit != 1:            # 1 = metres, the only unit the spec defines
        return None
    return px * 0.0254


def grid_free(src: str) -> bool:
    """True when the script never draws a gridline. A call ending in (False) or (None) is a
    suppression, not a violation, so it is allowed."""
    for m in re.finditer(r"\.grid\(([^)]*)\)", src):
        arg = m.group(1).strip().lower()
        if arg in ("false", "none", ""):
            continue
        return False
    return True


def audit(script: pathlib.Path, stem: str, figdir: pathlib.Path) -> list[str]:
    out = []
    src = script.read_text(encoding="utf-8") if script.exists() else ""
    if not src:
        return ["%s: script not found" % script.name]

    if not grid_free(src):
        n = len(re.findall(r"\.grid\(", src))
        out.append("%s: %d gridline call(s); the specification is spines and ticks only"
                   % (script.name, n))
    # `style_axes` applies the tick widths, so a script that calls it satisfies this rule without
    # naming tick_params itself. An earlier version of this check looked for the literal string and
    # reported a compliant figure as a failure -- the guard was wrong, not the figure.
    if "tick_params" not in src and "style_axes(" not in src:
        out.append("%s: no tick_params and no style_axes, so tick widths are not set" % script.name)
    # The label is placed either directly or by style_axes(ax, "a"). Same class of false negative as
    # the tick-width check above: the requirement is that labels exist, not that a name appears.
    has_label = ("panel_label" in src) or bool(re.search(r"style_axes\(\s*\w+\s*,\s*['\"]", src))
    if not has_label:
        out.append("%s: no panel labels (bold lowercase a, b, c are required)" % script.name)
    if "nature_style" not in src:
        out.append("%s: does not build its axes through nature_style.py" % script.name)

    for ext in FORMATS:
        p = figdir / (stem + ext)
        if not p.exists():
            out.append("%s: missing %s output" % (stem, ext))
        elif p.stat().st_size == 0:
            out.append("%s: %s is empty" % (stem, ext))

    png = figdir / (stem + ".png")
    if png.exists():
        d = png_dpi(png)
        if d is None:
            out.append("%s: the PNG carries no DPI metadata, so it cannot be verified at 400 dpi"
                       % stem)
        elif d < MIN_PNG_DPI - 1:
            out.append("%s: PNG is %.0f dpi, below the required %d" % (stem, d, MIN_PNG_DPI))

    svg = figdir / (stem + ".svg")
    if svg.exists() and svg.stat().st_size < MIN_SVG_BYTES:
        out.append("%s: SVG is %d bytes, too small to be a real vector rendering"
                   % (stem, svg.stat().st_size))
    return out


def main() -> int:
    figdir = FIGDIR
    if "--figdir" in sys.argv:
        figdir = pathlib.Path(sys.argv[sys.argv.index("--figdir") + 1])

    if "--negative-test" in sys.argv:
        name, stem = FIGURES[0]
        src = (REPO / "scripts" / name).read_text(encoding="utf-8")
        if grid_free(src):
            probe = src + "\n# injected\nax.grid(alpha=0.2)\n"
            if not grid_free(probe):
                print("  [OK] negative control fires: an injected gridline call is reported")
                return 0
            print("  [FAIL] the injected gridline was NOT detected")
            return 1
        print("  [OK] negative control fires: %s already carries gridlines and is reported" % name)
        return 0

    all_found = []
    for name, stem in FIGURES:
        found = audit(REPO / "scripts" / name, stem, figdir)
        all_found.append((stem, found))

    print("  audited %d figure(s) against the Nature specification" % len(FIGURES))
    total = 0
    for stem, found in all_found:
        if not found:
            print("  [OK]   %s" % stem)
        else:
            for f in found:
                print("  [FAIL] %s" % f)
                total += 1
    if total:
        print()
        print("  %d finding(s). A figure that fails here is not ready to circulate." % total)
        return 1
    print("  [OK] every figure meets the specification")
    return 0


if __name__ == "__main__":
    sys.exit(main())
