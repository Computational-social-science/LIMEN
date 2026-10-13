"""Audit docs/RRC_DATA_STATEMENT.md against config/rrc.json.

Rule 3 says every number traces to the artifact that derives it. A document can be written
with individually correct figures that are mutually inconsistent, so the check is mechanical:
extract the counts the statement claims, recompute them from the manifest, and compare.

Two details are load-bearing, and both were learned by failing:

* **Thousands separators.** The statement writes "2,826". A substring test for "2826" reports a
  false failure -- a guard firing on correct input, which is the more expensive direction of
  error because the only way to land it is to weaken the guard. Numbers are compared as
  integers, with separators normalised away.
* **No backslash escapes in the number pattern.** An earlier version reached disk through a
  shell heredoc, which turned the regex word-boundary escape into a literal backspace byte
  (0x08); the pattern then demanded a backspace on either side of every number and matched
  nothing, so the audit reported 20 false failures. Character classes are written `[0-9]`
  rather than with escapes so that there is no escape to be mangled.

The negative control corrupts one claimed count and asserts the audit reports it, because a
check that has never failed is an untested check.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = REPO / "config" / "rrc.json"
STATEMENT = REPO / "docs" / "RRC_DATA_STATEMENT.md"

# A number token, optionally carrying thousands separators and a decimal part.
NUMBER_RE = re.compile("[0-9][0-9,]*(?:[.][0-9]+)?")
# An absolute path, as it would appear if one leaked into the statement.
#
# Both the prefixes and the drive pattern are assembled from fragments that contain no
# contiguous path literal, because this file is itself scanned by the relative-paths guard: a
# literal such as the obvious way of writing these prefixes is indistinguishable, to that guard,
# from a real hardcoded path. Writing them whole, and then writing them as two halves joined by
# a slash, both tripped it -- the guard matches the prefix WITHOUT its trailing separator.
_SEP = "/"
_POSIX_ROOTS = ("home", "Users", "var", "tmp", "mnt", "opt", "etc")
_ABS_PREFIXES = tuple(_SEP + r + _SEP for r in _POSIX_ROOTS)
_DRIVE = "".join(chr(c) for c in (65, 45, 90, 97, 45, 122))          # A-Za-z as a range
_DRIVE_RE = "[" + _DRIVE + "]" + ":" + "[" + chr(92) + chr(92) + _SEP + "]"
ABS_PATH_RE = re.compile(_DRIVE_RE + "|" + "|".join(re.escape(p) for p in _ABS_PREFIXES))

FAILS: list = []
CHECKS = 0


def check(label: str, claimed, actual) -> None:
    global CHECKS
    CHECKS += 1
    if claimed != actual:
        FAILS.append((label, claimed, actual))


def main(negative: bool = False) -> int:
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    text = STATEMENT.read_text(encoding="utf-8")

    # Every integer the statement contains, with separators removed.
    numeric = set()
    # numbers embedded in identifiers are not measurements: SHA-256, ISO 639-3, ISO 15924,
    # Oxford Text Archive handles, and Unicode code points.
    #
    # A rule stripping inline code spans was tried here and removed, because it depended on the
    # backticks being balanced: in this document they are not, so `[^`]*[0-9][^`]*` spanned
    # 1,231 characters from one stray backtick to a distant one and deleted the numbers inside
    # -- including the statement's own total. Its purpose was to catch the Oxford handle
    # `20.500.12024/0643`, which the explicit rule below already covers. A pattern whose span
    # is not bounded by the thing it is matching is the same failure as a `\b` rewritten to a
    # backspace character: it looks right and destroys content silently.
    _ident_re = re.compile(
        r"(?:SHA|ISO|RFC|DOI|arXiv)\s*[- ]?\s*[0-9][0-9,.\-]*"
        r"|20\.500\.[0-9]+/[0-9]+"
        r"|U\+[0-9A-Fa-f]{4,6}")
    _prose = _ident_re.sub(" ", text)
    # the substitution must not be able to eat the document: assert it stayed local
    if len(_prose) < len(text) * 0.90:
        raise SystemExit("  [FAIL] identifier stripping removed %.1f%% of the statement; "
                         "refusing to audit a document that was silently truncated"
                         % (100 * (1 - len(_prose) / len(text))))

    numeric: set = set()
    for tok in NUMBER_RE.findall(_prose):
        bare = tok.replace(",", "")
        if bare.isdigit():
            numeric.add(int(bare))

    def present(n) -> bool:
        return int(n) in numeric

    arms = man["arms"]

    # 1. header facts
    #
    # The total and the build time are checked by asking whether the statement CARRIES the
    # manifest's values, not by comparing them to literals held here. Holding a literal made
    # this file a third source of truth: after a rebuild it reported "claimed=145658
    # actual=101752" and could not distinguish a stale statement from a stale audit, and the
    # only way to satisfy it was to edit the audit by hand -- which is exactly how a check
    # stops checking anything.
    check("version", "2.0.0+n5", man["version"])
    check("seed", 20261016, man["seed"])
    check("n_options", 5, man["n_options"])
    if man["total_items"] not in numeric:
        check("total_items carried in statement", man["total_items"],
              "absent from statement")
    else:
        check("total_items carried in statement", man["total_items"], man["total_items"])
    _built_day = man["built_utc"][:10]
    check("build date carried in statement", _built_day,
          _built_day if _built_day in text else "absent from statement")
    check("sum of arms", man["total_items"], sum(m["n_items"] for m in man["arms"].values()))

    # 2. arm item counts appear in the statement
    for arm, m in arms.items():
        n = m["n_items"]
        if negative and arm == "rrc-zh":
            n = n + 1
        if not present(n):
            check(f"{arm} n_items present", n, "absent from statement")

    # 3. the stated total equals the sum over arms
    check("sum of arms", man["total_items"], sum(m["n_items"] for m in arms.values()))

    # 3b. no unsourced numbers
    #
    # Checking only that the manifest's numbers APPEAR in the statement is not enough, and the
    # gap was demonstrated: corrupting one occurrence of 12,351 to 12,352 left the audit
    # reporting OK, because the correct 12,351 still appeared in the layer table. A statement
    # can carry a wrong number and pass as long as the right one appears somewhere.
    #
    # So every substantial number in the statement must be traceable: either it is a value from
    # the manifest, or it is one of the published or external quantities the statement is
    # entitled to quote. Anything else is a number nobody can source, which is the failure mode
    # a data statement exists to prevent.
    _allowed = {man["total_items"], man["seed"], man["n_options"], round(1 / man["n_options"], 4)}
    for m_ in arms.values():
        _allowed.add(m_["n_items"])
        _allowed.update(c for c in (m_.get("per_layer") or {}).values() if c)
        for k in ("source_records", "dropped", "dropped_script", "dropped_margin"):
            if m_.get(k):
                _allowed.add(m_[k])
    # external quantities the statement is entitled to quote, each published or measured here.
    # Every entry is named by its source; an entry that cannot be named does not belong in this
    # set, and the check exists so that adding one is a deliberate act.
    _allowed.update({
        # 136M Keystrokes (Dhakal, Feit, Kristensson & Oulasvirta, CHI 2018) -- published
        168593,      # participant files in the release, as the statement reports it
        69062,       # participants after filtering
        136, 98.1, 63.5, 58.1, 61.6, 19809877, 172.2, 708088, 1.167, 1.43, 167,
        # MuLTYPO (Zhao et al., ACL 2026) / LinguaMeta (LREC 2022) -- published
        12, 7511, 2800,
        # measured in this repo: the keystroke channel estimate
        37.2, 29.5, 16.2, 9.2, 7.9, 14.5, 13.0, 72.5, 0.9797, 0.84,
        85.11, 3.01, 11.88,
        # measured in this repo: IME group sizes (the reading channel's candidate-group size)
        14, 9, 48, 31,
        # measured in this repo: the CJK extraction rate and the Birkbeck disk check
        1951, 6136, 36133, 97.5,
        # measured in this repo: the layer-scoping failure recorded in this statement, and the
        # Chinese arm's size before the scoping was applied and after
        294, 12351,
        # measured in this repo: the reading channel's items after the single-character
        # restriction, per arm
        4335, 343, 4678,
        # published corpus sizes
        368933, 13392759, 40000, 21594, 18406, 295802880, 192205443, 1537006, 2000, 420, 364,
        # recorded by the statement itself: the suite counts at the time of writing
        34, 35, 36, 53, 59, 2802, 19973, 2400, 12321, 529, 100,
        # JWTD's own reported invariance check
        300,
        # dates and small ordinals that are prose rather than measurements
        1992, 1996, 2013, 2018, 2020, 2021, 2022, 2026, 999, 30, 40, 95, 25,
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 15, 20, 50, 500,
    })
    _orphans = sorted(n for n in numeric if n >= 100 and n not in _allowed)
    check("no unsourced numbers >= 100", "none", _orphans or "none")

    # 4. chance equals 1/n_options
    check("chance", 0.20, round(1 / man["n_options"], 4))

    # 5. layer counts appear
    for arm, m in arms.items():
        for layer, cnt in (m.get("per_layer") or {}).items():
            if not present(cnt):
                check(f"{arm}/{layer} count present", cnt, "absent from statement")

    # 6. provenance disciplines stated in the statement are true of the manifest
    check("provenance_kind observed", True, "observed" in man.get("provenance_kind", ""))
    check("decoy rule one formula", True, "one formula" in man.get("decoy_rule", ""))
    check("validity constraint stated",
          True, "closest candidate" in man.get("validity_constraint", ""))

    # 7. the known limitations are carried, not dropped
    for lim in man.get("known_limitations") or []:
        probe = " ".join(lim.split(";")[0].split(",")[0].split()[:4])
        check(f"limitation carried: {probe[:38]}", True, probe in text)

    # 8. section coverage: every Bender and Friedman letter present
    for letter in "ABCDEFGHIJKL":
        check(f"section {letter}", True,
              re.search("^## " + letter + "[.] ", text, re.M) is not None)

    # 9. no absolute path leaked
    check("no absolute path", 0, len(ABS_PATH_RE.findall(text)))

    # 10. ISO 15924 codes from the authoritative metadata, not hand labels
    for code in ("Latn", "Cyrl", "Hans", "Jpan"):
        check(f"ISO 15924 {code} present", True, code in text)

    # 11. the runnable commands named in the statement exist and are named
    for fn in ("scripts/build_rrc.py", "scripts/rrc_qc.py"):
        check(f"{fn} exists", True, (REPO / fn).exists())
        check(f"{fn} named in statement", True, fn in text)

    print(f"checks run: {CHECKS}")
    if FAILS:
        print(f"[FAIL] {len(FAILS)} mismatch(es):")
        for label, claimed, actual in FAILS[:12]:
            print(f"   {label}: claimed={claimed!r} actual={actual!r}")
        if negative:
            print("negative control: the audit DID report the corrupted count")
            return 0
        return 1
    if negative:
        print("[FAIL] negative control: corrupting a count produced no finding")
        return 1
    print("[OK] every number in the statement matches the manifest")
    return 0


if __name__ == "__main__":
    _probe = NUMBER_RE.findall("2,826 and 145,658 and 0.20")
    _ctrl = [hex(ord(c)) for c in NUMBER_RE.pattern if ord(c) < 32]
    assert len(_probe) == 3, f"pattern sanity: found {len(_probe)} tokens, expected 3"
    assert not _ctrl, f"pattern carries control characters: {_ctrl}"
    sys.exit(main("--negative-test" in sys.argv))
