"""docpipe.render -- the mathematics pipeline: one configuration, its assets, and TeX to OMML.

WHY THIS MODULE EXISTS SEPARATELY
    Rules.md names it as the place where the cache-keying rule is enforced, and it was named before it existed:
    the anchor guard caught the document promising a file that was not there. The right response was to create
    the module rather than to edit the promise, because a package whose documentation describes a structure it
    does not have is the same defect one level up.

WHAT LIVES HERE
    MATH_CONFIG       the single mathematics configuration, as a document expects it inline
    copy_math_assets  place the renderer AND its fonts; returns the version string
    mml_to_omml       MathML to OMML, via Office's own XSLT rather than a reimplementation
    tex_spans         the mathematics spans a markdown source declares

THE RULE THIS ENFORCES (docpipe/RULES.md, rule 3)
    Conversions are keyed by the EXPRESSION'S OWN TEXT, never by its position. A position-keyed map is valid
    only while a document's spans keep the order they had at harvest time; edit a section and the lookup for
    span i returns the mathematics of whatever used to sit at i, while the build reports success because an
    entry exists. Text keys make that impossible - a changed expression is simply absent, falls back, and is
    reported.
"""

from __future__ import annotations

import pathlib
import re

from docpipe import load

__all__ = ["MATH_CONFIG", "copy_math_assets", "mml_to_omml", "tex_spans", "MATHJAX_FILE"]

MATHJAX_FILE = "tex-mml-chtml.js"

_INLINE = re.compile(r"(?<!\$)\$(?!\$)(?!\s)[^\n$]*?(?<!\s)\$(?!\$)")
_DISPLAY = re.compile(r"\$\$.+?\$\$", re.S)
_ANY = re.compile(r"(\$\$.+?\$\$|(?<!\$)\$(?!\$)(?!\s)[^\n$]*?(?<!\s)\$(?!\$))", re.S)


def MATH_CONFIG() -> str:
    """The one configuration. Two renderers meant two configurations and two failure modes."""
    return load("si_render.py").MATHJAX_SCRIPTS


def copy_math_assets(dest: pathlib.Path) -> str:
    """Place the renderer and its fonts; return the version string.

    The fonts are the part that failed silently here: a renderer without them does not error, it SUBSTITUTES,
    and the variables stop being italic while the page continues to look like a page.
    """
    dest = pathlib.Path(dest)
    ver = load("si_render.py").copy_mathjax(dest)
    fd = dest / "output" / "chtml" / "fonts" / "woff-v2"
    n = len([f for f in fd.glob("*") if f.suffix in (".woff", ".woff2")]) if fd.is_dir() else 0
    if n == 0:
        raise RuntimeError(
            f"the renderer was copied to {dest} but its font directory is empty. The page would still load, "
            f"every symbol would silently substitute, and the variables would lose their italic. Refusing to "
            f"produce a document in that state.")
    return ver


def tex_spans(md: str) -> list[str]:
    """Every mathematics span a markdown source declares, in order.

    This is what makes the artefact checks possible: the expected equation count is DERIVED from the source
    rather than typed in, so a checker cannot drift from the document it checks.
    """
    return _ANY.findall(md)


def mml_to_omml(mml: str | None) -> str | None:
    """MathML to OMML through Office's own stylesheet. Returns None so the caller FALLS BACK and REPORTS."""
    if not mml:
        return None
    return load("omml.py").mml_to_omml(mml)
