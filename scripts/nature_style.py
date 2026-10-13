"""Nature submission style -- one place, so every figure meets the same specification.

WHY A SHARED MODULE. The four figures in this report drifted: three carried gridlines the
specification forbids, none set tick line widths, none carried bold panel labels, and all four
shipped PNG+PDF while the rest of the repository ships PNG+JPG+SVG+TIFF. Four separate styles is four
standards, and a reviewer comparing two panels would see the difference before reading either. Every
figure now imports this module, so a change to the specification is one edit and the guard that
audits compliance has a single thing to check against.

THE SPECIFICATION (Nature / Nature Human Behaviour):
  width       89 mm single column, 114 / 140 mm intermediate, 183 mm double column. Nothing between.
  height      247 mm maximum.
  type        sans-serif, 7 pt base, 5-5.5 pt tick labels, nothing below 5 pt.
  panel labels bold lowercase a, b, c ...
  spines      top and right removed; bottom and left kept.
  gridlines   NONE. Nature's figures are read by gridline light; spines and ticks only.
  ticks       major 0.4 pt, minor 0.3 pt.
  colour      Okabe-Ito, the standard colour-blind-safe palette.
  raster      400 dpi minimum; vector (SVG) always, since it is resolution-independent.
  output      PNG + JPG + SVG + TIFF, the repository's standing set: PNG for the web report, JPG for
              submission systems that reject PNG, SVG for typesetting, TIFF for the printer.

A note on what this module deliberately does NOT do: it does not put a title or a caption inside the
image. A journal figure carries no caption -- the caption is set in the page's own type by the
typesetting system, so it can be restyled and reflowed, and a burned-in caption duplicates text the
document already owns. Panel titles are kept, because they name the panel; the figure title lives in
the caption.
"""
from __future__ import annotations

import pathlib

# ---- geometry, in inches. Nature's widths, exactly, with no invented intermediate.
MM = 1.0 / 25.4
SINGLE_COL = 89 * MM          # 3.504 in
ONE_HALF_COL = 114 * MM       # 4.488 in
MID_COL = 140 * MM            # 5.512 in
DOUBLE_COL = 183 * MM         # 7.205 in
MAX_HEIGHT = 247 * MM         # 9.724 in

# ---- type, in points
BASE_PT = 7.0
TICK_PT = 5.5
PANEL_PT = 7.5
MIN_PT = 5.0                  # nothing in a figure may be smaller than this

# ---- line weights, in points
MAJOR_TICK_W = 0.4
MINOR_TICK_W = 0.3
SPINE_W = 0.5

# ---- colour: Okabe-Ito, colour-blind safe, extended with the two project colours already in use so
# the report's established arm colours do not have to change to become accessible.
OKABE_ITO = {
    "blue": "#0072B2", "orange": "#D55E00", "green": "#009E73", "yellow": "#F0E442",
    "sky": "#56B4E9", "vermillion": "#D55E00", "purple": "#CC79A7", "grey": "#999999",
}
PROJECT = {
    "navy": "#1b3a6b", "mid_blue": "#5b8ac4", "pale_blue": "#8aa8c8",
    "green": "#2e7d5b", "ochre": "#8a6d1f", "rust": "#b4520f", "amber": "#d98b4a",
    "light": "#c9c9c9", "warm_light": "#e0954a", "ink": "#333333", "dim": "#6b7a8d",
}

DPI = 400
JPG_QUALITY = 95


def rcparams() -> dict:
    """The rcParams every figure runs under. Pass to plt.rcParams.update()."""
    return {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": BASE_PT,
        "axes.labelsize": BASE_PT,
        "axes.titlesize": BASE_PT,
        "axes.linewidth": SPINE_W,
        "xtick.labelsize": TICK_PT,
        "ytick.labelsize": TICK_PT,
        "legend.fontsize": TICK_PT,
        "figure.dpi": 150,          # on-screen preview speed; the save dpi is what matters
        "savefig.dpi": DPI,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,         # Nature: no gridlines
        "grid.alpha": 0.0,
        "pdf.fonttype": 42,         # embed as Type 42, so the glyphs stay editable in a PDF
        "ps.fonttype": 42,
        "svg.fonttype": "none",     # keep text as text in the SVG, not paths
        "figure.autolayout": False,
    }


def style_axes(ax, letter: str | None = None) -> None:
    """Apply the part of the specification that lives on the axes object.

    Pass the panel letter to place the bold lowercase label in the same call, so a figure cannot
    satisfy the spine and tick rules and then forget the label.
    """
    ax.grid(False)
    for s in ("top", "right"):
        if s in ax.spines:
            ax.spines[s].set_visible(False)
    for s in ("bottom", "left"):
        if s in ax.spines:
            ax.spines[s].set_linewidth(SPINE_W)
    ax.tick_params(axis="both", which="major", width=MAJOR_TICK_W, length=3.0)
    ax.tick_params(axis="both", which="minor", width=MINOR_TICK_W, length=1.6)
    if letter:
        panel_label(ax, letter)


def panel_label(ax, letter: str, dx: float = -0.085, dy: float = 1.015) -> None:
    """A bold lowercase panel label, placed above the axes' top-left corner.

    Uses offset points rather than axes fractions so the label sits at the same visual distance
    whatever the axes is resized to -- axes-fraction coordinates move when a layout changes.
    """
    if not letter.islower() or len(letter) != 1:
        raise ValueError("panel labels are single bold lowercase letters, not %r" % letter)
    ax.annotate(letter, xy=(0, 1), xycoords="axes fraction",
                xytext=(dx * 100, 4), textcoords="offset points",
                fontsize=PANEL_PT, fontweight="bold", ha="left", va="bottom", color="#111")


def save_nature(fig, stem: pathlib.Path | str, dpi: int = DPI) -> list[pathlib.Path]:
    """Write the repository's standing output set: PNG, JPG, SVG, TIFF.

    Four formats because they are used by four different consumers: PNG for the HTML report, JPG for
    submission portals that refuse PNG, SVG for typesetting, TIFF for print. Writing one and
    converting later loses the vector text.
    """
    stem = pathlib.Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    out = []
    png = stem.with_suffix(".png")
    fig.savefig(png, dpi=dpi, bbox_inches="tight")
    out.append(png)
    jpg = stem.with_suffix(".jpg")
    fig.savefig(jpg, dpi=dpi, bbox_inches="tight", pil_kwargs={"quality": JPG_QUALITY})
    out.append(jpg)
    svg = stem.with_suffix(".svg")
    fig.savefig(svg, bbox_inches="tight")
    out.append(svg)
    tif = stem.with_suffix(".tiff")
    fig.savefig(tif, dpi=dpi, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
    out.append(tif)
    # PDF is written too, and the reason is a defect this addition fixes rather than a consumer
    # requesting it. `viz/figures/*.pdf` had been sitting in the tree since an earlier version of
    # this function wrote one, and nothing referenced them, so nothing noticed they had gone stale:
    # the PDFs were hours older than the PNGs beside them (16:54 against 21:38) and a reader taking
    # the PDF for typesetting would have been using a figure the report had since corrected. Either
    # write every format or write none; a format that exists but is never regenerated is a stale
    # artifact wearing the appearance of a current one.
    pdf = stem.with_suffix(".pdf")
    fig.savefig(pdf, bbox_inches="tight")
    out.append(pdf)
    return out


def audit_fonts(fig) -> list[str]:
    """Every text artist must be at or above MIN_PT. Returns a list of violations."""
    bad = []
    for t in fig.findobj(match=lambda o: hasattr(o, "get_fontsize") and hasattr(o, "get_text")):
        try:
            txt = t.get_text()
            size = float(t.get_fontsize())
        except Exception:  # noqa: BLE001
            continue
        if txt and size < MIN_PT - 1e-9:
            bad.append("%.1f pt: %r" % (size, txt[:44]))
    return bad
