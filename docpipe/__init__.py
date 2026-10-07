"""docpipe -- the reusable parts of a document pipeline, with the rules written down.

WHY THIS EXISTS AS A PACKAGE RATHER THAN A FOLDER OF SCRIPTS
    This pipeline produced eleven defects that reached deliverables in one session, and every one was invisible
    in the artefact. The checks that catch them were written one at a time, against one project, and the only
    thing that made them catchable at all was that each one was DERIVED from a source rather than typed in.
    That property is what makes them reusable, and it is what this package exposes.

WHAT IS HERE
    render   the mathematics configuration and the asset copying, taken from the module that already owns them
    verify   the post-build check: expectations derived from the source, asserted against the produced file

WHAT IS DELIBERATELY NOT HERE
    The project's own prose, its manifests and its judgments. A package that encodes one paper's content cannot
    be reused by another, and the failure mode of trying is a package nobody dares change.

    The bridge modules below load the canonical implementations BY PATH rather than restating them. That is the
    one form of "shared code" that cannot drift: there is no second copy to update. See RULES.md for the seven
    rules, each with the incident that produced it.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"

__all__ = ["load", "MATH_CONFIG", "copy_math_assets", "verify_documents", "RULES"]


def load(name: str):
    """Import a project script by file name, so this package never duplicates it.

    `scripts/` is not an importable package and should not become one: making it one would force every script
    to be import-safe, which several are not because they were written as programs. Loading by path keeps the
    canonical implementation where it is and gives it a second way in.
    """
    path = _SCRIPTS / name
    if not path.is_file():
        raise FileNotFoundError(f"{path} does not exist - docpipe has nothing to bridge to")
    mod_name = "docpipe_src_" + name.replace(".py", "")
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def MATH_CONFIG() -> str:
    """The one mathematics configuration, as the HTML documents expect it inline.

    Rule 4 (one producer per output) applies to configuration as much as to files: two renderers meant two
    configurations, two asset trees and two sets of failure modes.
    """
    return load("si_render.py").MATHJAX_SCRIPTS


def copy_math_assets(dest: pathlib.Path) -> str:
    """Place the renderer and its FONTS where the document expects them; return the version string.

    The fonts are the part that failed silently in this project: a renderer without them does not error, it
    substitutes, and the variables stop being italic while the page continues to look like a page.
    """
    return load("si_render.py").copy_mathjax(pathlib.Path(dest))


def verify_documents(only: str | None = None) -> int:
    """Run the artefact checks. Returns a process-style exit code rather than raising."""
    mod = load("check_documents.py")
    argv = sys.argv
    try:
        sys.argv = ["check_documents.py"] + (["--only", only] if only else [])
        return int(mod.main())
    finally:
        sys.argv = argv


RULES = pathlib.Path(__file__).resolve().parent / "RULES.md"
