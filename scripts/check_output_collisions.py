"""check_output_collisions.py -- no script may write into another artefact's home.

THE DEFECT THIS GENERALISES. `viz/manuscript.html` was produced by the protocol renderer. Then a real paper
was authored and built to the same path. Two scripts then owned one path, and running the older one silently
replaced the newer artefact with a protocol rendering - no error, no diff, nothing to notice, because both
files were "the manuscript". It was found by asking which script writes the file, not by any check.

Then the same defect was found a SECOND time: a superseded builder sitting in the repository with the same
default output. Fixing the site twice and leaving the class is how a repository accumulates the same bug in
new places.

WHAT IT ASSERTS. `check_documents.py` declares every document set and its paths - that declaration is the map
of who owns what. This reads that map and, for each declared path, finds the scripts that mention it, and
requires that only the declared producer could write it. A script that merely READS a path (a verifier, a
renderer that copies an asset) is not a producer and is listed separately rather than reported.

A negative control gives a non-producer the default output path and requires the check to fire.
"""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

# Which script produces which declared artefact. Every path in `check_documents.DOC_SETS` must appear here,
# so adding a deliverable without declaring its producer is itself a failure.
PRODUCERS = {
    # Markdown SOURCES are authored by hand, not written by a script, and the entry says so explicitly
    # rather than leaving them unnamed - an unowned path is one nothing stops a script from overwriting.
    "docs/PAPER.md": {"<authored>"},
    "docs/SUPPLEMENTARY_INFORMATION.md": {"assemble_supplementary_information.py"},
    "viz/manuscript.html": {"build_paper_html.py"},
    "viz/manuscript.pdf": {"build_paper_html.py"},
    # The DOCX for BOTH documents comes from one renderer: `build_docx.py` takes --src and --out and holds
    # the OMML pipeline (MathJax MathML -> Office MML2OMML), which was debugged against real defects and is
    # not worth a second implementation. Its NAME is now misleading - it renders any markdown - and this line
    # is where that shows up. Naming the real producer is the point: a path with no declared owner is one
    # nothing stops a second script from writing.
    "viz/manuscript.docx": {"build_docx.py"},
    "viz/supplementary_information_mml_map.json": {"build_docx.py"},
    "viz/manuscript_mml_map.json": {"build_docx.py"},
    "viz/supplementary_information.html": {"build_si_documents.py"},
    "viz/supplementary_information.pdf": {"build_si_documents.py"},
    "viz/supplementary_information.docx": {"build_si_documents.py"},
    "viz/protocol.html": {"build_manuscript_html.py"},
}

# A script that names a path in order to READ it - a verifier, or a builder copying an asset - is not
# competing for the file. These markers mean the mention is a read or a declaration, not a write.
# This checker names every deliverable path in its own tables, so it matches itself. Exempting it BY NAME is
# the same treatment `check_object_drift.py` needed: a rule scanner that reports itself is turned off.
SELF_EXEMPT = {"check_output_collisions.py"}

WRITE_MARKERS = re.compile(
    r"(--out|--output|--print-to-pdf|write_text|open\([^)]*['\"]w|OUT_HTML|OUT_PDF|OUT_DOCX|out_path|dst\b)")


def doc_set_paths() -> dict[str, str]:
    spec = importlib.util.spec_from_file_location("cd_", SCRIPTS / "check_documents.py")
    if spec is None or spec.loader is None:
        raise ImportError("cannot load check_documents.py to read its DOC_SETS")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    paths: dict[str, str] = {}
    for name, spec_dict in mod.DOC_SETS.items():
        for kind in ("md", "html", "docx", "pdf"):
            v = spec_dict.get(kind)
            if v:
                paths[str(v)] = name
    return paths


def mentions_of(path: str) -> list[tuple[str, bool]]:
    """(script, looks_like_a_write) for every script naming the path."""
    out = []
    for f in sorted(SCRIPTS.glob("*.py")):
        text = f.read_text(encoding="utf-8", errors="replace")
        if path not in text:
            continue
        writes = False
        for line in text.splitlines():
            if path in line and WRITE_MARKERS.search(line):
                writes = True
                break
        out.append((f.name, writes))
    return out


def scan(extra_producers: dict[str, set[str]] | None = None) -> list[str]:
    findings: list[str] = []
    prod = {k: set(v) for k, v in PRODUCERS.items()}
    for path, who in (extra_producers or {}).items():
        prod.setdefault(path, set()).update(who)

    declared = doc_set_paths()
    for path, doc_name in sorted(declared.items()):
        allowed = prod.get(path)
        if allowed == {"<authored>"}:
            continue                     # a hand-authored source has no script producer by design
        if allowed is None:
            findings.append(
                f"{path} is a declared deliverable of '{doc_name}' but no producer is named in this check's "
                f"PRODUCERS map - an unowned deliverable is one nothing stops a second script from writing")
            continue
        for script, writes in mentions_of(path):
            if script in allowed or script in SELF_EXEMPT or not writes:
                continue
            findings.append(
                f"{script} appears to write {path}, which is the deliverable of '{doc_name}' produced by "
                f"{sorted(allowed)} - two writers on one path means running the wrong one silently replaces it")
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--no-negative-control", action="store_true")
    args = ap.parse_args(argv)

    declared = doc_set_paths()
    print(f"declared deliverable paths: {len(declared)}; producers named: {len(PRODUCERS)}")
    findings = scan()

    if not args.no_negative_control:
        # Give a NON-producer the default output of a real deliverable, in a live scratch script that this
        # check can see, and require a finding.
        probe = SCRIPTS / "__collision_negative_control__.py"
        probe.write_text(
            'import argparse\n'
            'ap = argparse.ArgumentParser()\n'
            'ap.add_argument("--out", default="viz/manuscript.html")\n',
            encoding="utf-8")
        try:
            fired = any("__collision_negative_control__" in f for f in scan())
            print(f"  negative control: a non-producer given 'viz/manuscript.html' -> "
                  f"{'FAILS as required' if fired else 'NOT DETECTED'}")
            if not fired:
                findings.append("negative control did not fire: a non-producer writing a declared path passed")
        finally:
            probe.unlink(missing_ok=True)

    if findings:
        print(f"\n  [FAIL] {len(findings)} output-collision finding(s):")
        for f in findings:
            print(f"      {f}")
        return 1
    print("\n  [OK] every declared deliverable is written by exactly the producer named for it, and the check "
          "fires when a non-producer is given its path")
    return 0


if __name__ == "__main__":
    sys.exit(main())
