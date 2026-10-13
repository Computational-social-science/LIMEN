"""check_citation_links.py -- a citation must resolve, and a source must be in the reference list.

WHY THIS EXISTS, IN ONE SENTENCE. A paper that does not exist sat in this report's reference list
supporting the taxonomy that structures its whole formal framework, and a 71-run guard suite never
noticed, because nothing connected an in-text citation to an entry.

WHY IT IS A SET COMPARISON AND NOT A REGEX. An auditor for this was written three times in one session
and was wrong twice, both times in the direction that flatters the report: once it found a single
in-text citation in the entire document because its pattern assumed one author before the year, and
once it scraped every capitalised word followed by a year out of the reference block. Fuzzy matching
on prose is the wrong instrument for a fact. So the link is explicit -- each entry carries a key, each
citation carries the same key in `data-cite`, and the check compares two sets, which cannot be wrong.

WHAT IT CHECKS
  1. every `data-cite="K"` in the document resolves to an entry `{ k: 'K', ... }`. A dangling citation
     is an unsupported claim and fails.
  2. every source in config/datasets.json carries a citation whose lead surname appears in the
     reference list. Those citations are rendered into the report at runtime by the §1.1 table, so no
     static check of the HTML could see them; this reads the source of truth instead.
  3. every entry's rendered id is derivable from its key, so a cross-reference cannot point nowhere.

NEGATIVE CONTROL
    Injects a `data-cite` naming a key that does not exist and requires the check to report it. The
    control ASSERTS that its injection applied -- an earlier control in this project silently stopped
    firing when a reformat removed its literal target, and reported success while testing nothing.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
REPORT = REPO / "viz" / "report" / "technical-report.html"
DATASETS = REPO / "config" / "datasets.json"

KEY_DEF = re.compile(r"\{\s*k:\s*'([^']+)'")
CITE_DEF = re.compile(r'data-cite="([^"]+)"')


def refs_block(src: str) -> str:
    i = src.find("  const REFS = [")
    j = src.find("  ];", i)
    return src[i:j] if i >= 0 and j > i else ""


def audit(src: str) -> tuple[list[str], set[str], list[str]]:
    """Returns (failures, entry keys, entry keys never cited)."""
    fails: list[str] = []
    block = refs_block(src)
    if not block:
        return (["the REFS array was not found, so nothing can be resolved"], set(), [])
    keys = set(KEY_DEF.findall(block))
    cited = set(CITE_DEF.findall(src))
    if not keys:
        fails.append("no entry keys found; the array is not in the {k, t} form this check requires")

    for c in sorted(cited):
        if c not in keys:
            fails.append("data-cite=%r names no entry in the reference list" % c)

    # The render must build the item id from the key, or a citation cannot be followed.
    # Written with quote-free markers on purpose: an escaped quote here is read by
    # check_relative_paths as a hardcoded Windows path, so the check would flag its own source.
    if 'id="ref-' not in src or "r.k" not in src:
        fails.append("the reference list does not build an id from the key, so a citation cannot "
                     "point at its entry")

    # sources render their citation at runtime; verify against the source of truth, not the HTML
    if DATASETS.exists():
        try:
            data = json.loads(DATASETS.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            fails.append("config/datasets.json could not be parsed: %s" % exc)
            data = {}
        raw = data.get("sources") or data
        # `sources` is a LIST of records in this project, not a mapping; accept either shape rather
        # than assume, because a guard that crashes on its own input reports nothing at all.
        if isinstance(raw, dict):
            pairs = list(raw.items())
        elif isinstance(raw, list):
            pairs = [(e.get("name") or e.get("id") or "?", e) for e in raw if isinstance(e, dict)]
        else:
            pairs = []
        if not pairs:
            fails.append("config/datasets.json carries no sources, so source citations cannot be "
                         "verified")
        for name, entry in pairs:
            cit = entry.get("citation") if isinstance(entry, dict) else None
            if not cit:
                continue
            m = re.search(r"([A-Z][A-Za-z\u00c0-\u017f'-]{2,})", cit)
            surname = m.group(1) if m else None
            if surname and surname not in block:
                fails.append("source %r cites %r, whose lead surname %r is absent from the "
                             "reference list" % (name, cit[:54], surname))
    else:
        fails.append("config/datasets.json not found, so source citations cannot be verified")

    return fails, keys, sorted(keys - cited)


def main() -> int:
    if not REPORT.exists():
        print("  [FAIL] report not found: %s" % REPORT)
        return 1
    src = REPORT.read_text(encoding="utf-8")
    # THE DOCUMENT INCLUDES THE SCRIPTS IT LOADS. The reference list moved out of the HTML into
    # report.js, and the citation keys that bind in-text citations to entries live in that array --
    # so this check found `entries: 0` and reported only the citations it could still see, which is
    # a silent downgrade rather than a failure. Same-directory scripts only: ../mathjax/ is vendored.
    for _ref in re.findall(r"""<script[^>]*\bsrc=["']([^"']+)["'][^>]*>""", src, re.I):
        _ext = (REPORT.parent / _ref).resolve()
        if _ext.parent == REPORT.parent.resolve() and _ext.suffix == ".js" and _ext.exists():
            src += "\n" + _ext.read_text(encoding="utf-8")

    if "--negative-test" in sys.argv:
        probe = src + '\n<span class="cite" data-cite="no_such_entry_xyz">x</span>\n'
        if probe == src:
            print("  [FAIL] the negative control could not inject anything: the control is INERT")
            return 1
        fails, _keys, _uncited = audit(probe)
        if any("no_such_entry_xyz" in f for f in fails):
            print("  [OK] negative control fires: a citation to a non-existent entry is reported")
            return 0
        print("  [FAIL] the injected dangling citation was NOT reported -- the control is inert")
        return 1

    fails, keys, uncited = audit(src)
    print("  entries: %d | citations bound with data-cite: %d"
          % (len(keys), len(set(CITE_DEF.findall(src)))))
    if fails:
        print()
        for f in fails:
            print("  [FAIL] %s" % f)
        print()
        print("  A citation that resolves to nothing is an unsupported claim.")
        return 1
    if uncited:
        print("  entries with no in-text citation: %d" % len(uncited))
        print("      %s" % ", ".join(uncited))
        print("      (informational: data sources are cited through the §1.1 table, which is rendered")
        print("       at runtime from config/datasets.json and is checked above)")
    print("  [OK] every citation resolves to an entry, and every source is in the reference list")
    return 0


if __name__ == "__main__":
    sys.exit(main())
