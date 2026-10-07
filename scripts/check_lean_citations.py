#!/usr/bin/env python
"""check_lean_citations.py -- every kernel name a document cites must exist in the Lean source.

WHY THIS EXISTS, AND THE EXACT FAILURE IT WAS WRITTEN FOR
    A Phase II pre-registration drafted in this repository cited, in a load-bearing sentence, a theorem
    named `silent_error_count_antitone`. The sentence was correct in substance - a fixed-threshold
    silent-error count IS non-increasing in its threshold - and the name was INVENTED. It had the shape
    of a kernel name, it described the result it was attached to, and it existed nowhere.

    This is the failure mode the reference-checking discipline names outright: an entry drafted from
    memory is not a degraded citation, it is a FABRICATION WITH CORRECT FORMATTING. It was caught by
    hand, by listing the Lean source's 27 theorem names and looking for it. That is not a mechanism. The
    real names were `risk_mono` and, better, `protocol_said_nondecreasing_is_FALSE` - a theorem whose
    own name carries the refutation.

    A cited kernel name is a CHECKABLE CLAIM. This makes it checked.

WHY THE FALSE-POSITIVE RATE IS THE WHOLE DESIGN PROBLEM
    Documents here mention many snake_case tokens that are NOT kernel names: `item_id`,
    `answer_confidence`, `huggingface_hub`, pack names. A check that flags every backticked identifier
    against the Lean source produced 47 findings on this repository, of which the great majority were
    data fields and package names - a check that cries wolf 47 times is a check that gets disabled.

    So the pattern is narrowed to the ONE form in which a document UNDERTAKES a citation: a markdown
    table row whose first cell is exactly one backticked identifier. That is the form the status record
    uses (`| `risk_mono` | a <= b implies Risk b xs <= Risk a xs |`) and the form the supplementary
    information uses. Elsewhere, an identifier in prose is a mention; in this table it is a promise that
    the theorem exists, and it is verified as one.

WHAT IT DOES NOT CHECK
    It does not check that the theorem SAYS what the row claims - that is the claim layer, and it needs a
    reader. It checks that the name exists, which is the layer that can be mechanised and the layer that
    was actually wrong.

EXIT
    0  every cited name exists        1  at least one cited name does not
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# WHERE THE FORMALISATION LIVES, resolved the way the other Lean guards resolve it - not with a path literal.
# A first version of this file carried `Path("E:/2026-AI4S/lean-nhb/NHB/PhaseI")` and `check_relative_paths.py`
# refused it, correctly: the project forbids absolute paths in code, and the formalisation lives in a SIBLING
# repository that cannot be named relative to this one either. The established order is the environment
# variable first, then the sibling directory - the same one `check_lean_axioms.py` and
# `check_lean_status_freshness.py` use, so a moved checkout is one variable rather than three edits.

# A markdown table row whose FIRST cell is exactly one backticked identifier.
CITATION_ROW = re.compile(r"^\|\s*`([A-Za-z_][A-Za-z0-9_']*)`\s*\|")

# THE SCOPE IS DECLARED, BECAUSE THE PATTERN ALONE IS NOT SPECIFIC ENOUGH. `| `name` | description |` is also
# how a data schema is written - item-bank field rows (`item_id`, `domain`, `escalate`) and item ids
# (`pos_04`, `neg_06`) are the same shape and neither is a kernel citation. Running the pattern repository-wide
# produced 17 findings of which every one was a field name, and a check that cries wolf gets disabled. So the
# documents that UNDERTAKE kernel citations are listed here, and the run PRINTS the list - an unchecked
# document is not a pass, and a silent omission reads exactly like a verified one. Adding a document that cites
# the formal core means adding a row.
# NOT INCLUDED, and the reason is stated rather than left to look like an omission:
#   docs/THEORETICAL_FOUNDATIONS.md maps Shannon NOTATION to protocol terms (`P_e`, `R`, `C`) in the same
#   table form. Those are symbols, not declarations, and including the document produced a finding against
#   `P_e`. A document belongs here when it UNDERTAKES that a theorem exists - not when it borrows a symbol.
CITING_DOCS = (
    "docs/LEAN_FORMALIZATION_STATUS.md",
    "docs/SUPPLEMENTARY_INFORMATION.md",
    "docs/si/B_formal_framework.md",
    "docs/PAPER.md",
    "docs/PHASE_II_PREREGISTRATION.md",
    "docs/SCIENTIFIC_SPINE.md",
    "docs/PHASE_I_AMENDMENT_2.md",
    "docs/PHASE_I_AMENDMENT_3_O1_READABILITY.md",
    "docs/REGISTERED_REPORT_STAGE1.md",
    "docs/GAP_VERDICT.md",
)

# The name must be a DECLARATION, not merely mentioned, so the scan reads declarations.
DECL = re.compile(r"^(?:theorem|lemma|def|abbrev|structure|inductive)\s+([A-Za-z_][A-Za-z0-9_']*)", re.M)


def lean_dir() -> pathlib.Path | None:
    import os

    if os.environ.get("NHB_LEAN_ROOT"):
        root = pathlib.Path(os.environ["NHB_LEAN_ROOT"])
    else:
        root = REPO_ROOT.parent / "lean-nhb"
    d = root / "NHB" / "PhaseI"
    return d if d.is_dir() and list(d.glob("*.lean")) else None


def declared_names(d: pathlib.Path) -> set[str]:
    names: set[str] = set()
    for f in d.glob("*.lean"):
        names |= set(DECL.findall(f.read_text(encoding="utf-8", errors="ignore")))
    return names


def cited_rows(extra: list[str] | None = None) -> list[tuple[str, int, str]]:
    """(document, line number, cited name) for every table-row citation in scope.

    `extra` exists for the negative control. WHEN THE SCOPE WAS NARROWED to a declared document list, the
    probe file the negative test writes stopped being scanned - so the main check passed and the control that
    proves it CAN fail stopped failing. A guard that cannot fail proves nothing, and the thing that caught it
    was the negative control itself. The probe is now named explicitly rather than relying on being in scope.
    """
    out: list[tuple[str, int, str]] = []
    for rel in list(CITING_DOCS) + list(extra or []):
        f = REPO_ROOT / rel
        if not f.exists():
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            m = CITATION_ROW.match(line)
            if m:
                out.append((rel, i, m.group(1)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--negative-test", action="store_true",
                    help="inject a citation of a theorem that does not exist, require this check to fail")
    args = ap.parse_args()

    d = lean_dir()
    if d is None:
        print("  [FAIL] the Lean source was not found in any known location; the citations cannot be checked")
        return 1
    names = declared_names(d)
    if not names:
        print(f"  [FAIL] no declarations parsed from {d}; a check with nothing to compare against passes vacuously")
        return 1

    if args.negative_test:
        probe = REPO_ROOT / "docs" / "_negative_control_citation.md"
        probe.write_text("| `a_theorem_that_was_never_proved` | injected |\n", encoding="utf-8")
        try:
            rc = subprocess.run([sys.executable, __file__], capture_output=True, text=True).returncode
        finally:
            probe.unlink(missing_ok=True)
        if rc == 0:
            print("  [FAIL] negative control was NOT caught - the check cannot fail and proves nothing")
            return 1
        print("  [OK]   negative control: injected citation of a non-existent theorem -> FAILS as required")
        return 0

    rows = cited_rows(["docs/_negative_control_citation.md"])
    bad = [(f, i, n) for f, i, n in rows if n not in names]
    scanned = [r for r in CITING_DOCS if (REPO_ROOT / r).exists()]
    print(f"  lean source: {d}")
    print(f"  declarations parsed: {len(names)}")
    print(f"  documents scanned: {len(scanned)} of {len(CITING_DOCS)} declared")
    for r in CITING_DOCS:
        if not (REPO_ROOT / r).exists():
            print(f"      (declared but absent, NOT checked: {r})")
    print(f"  table-row citations found: {len(rows)}")
    if bad:
        print(f"\n  [FAIL] {len(bad)} cited kernel name(s) do not exist in the Lean source:")
        for f, i, n in bad[:10]:
            near = [x for x in names if n[:7] in x][:2]
            hint = f"  (did you mean: {', '.join('`'+x+'`' for x in near)}?)" if near else ""
            print(f"      {f}:{i}  `{n}`{hint}")
        print("\n  A name with the shape of a kernel name and no theorem behind it is a fabrication with")
        print("  correct formatting. Cite the theorem that exists, or state the claim without a name.")
        return 1
    print(f"\n  [OK] every cited kernel name resolves to a declaration in the Lean source")
    return 0


if __name__ == "__main__":
    sys.exit(main())
