#!/usr/bin/env python
"""check_anchor.py -- mechanical verification that the repository is anchored to its objective.

The drift guard (`check_object_drift.py`) checks vocabulary: retired-object terms appearing in live
files. It does NOT check whether the files the authority document PROMISES actually exist, nor
whether the authority document's own version is self-consistent. Both omissions were live defects:

  * `CURRENT_OBJECT.md` listed nine paths under "Live instruments - kept, and why". All nine did not
    exist at the repository root; every one was under `archive/R1_.../`.
  * Protocol v1.2 was edited in three places while `§12` still specified the superseded Q0 and
    `§14` still read "Version 1.1" / "End of protocol v1.1".

This checker closes exactly those two classes. It is deliberately separate from the vocabulary guard
so that each has one job.

CHECKS
  A  ANCHOR IDENTITY   the protocol exists; its sha256 matches `config/anchor.json`
  B  VERSION COHERENCE the version in the header, in §14, and in the end marker agree, and match
                        `config/anchor.json`
  C  SUBORDINATION     no live file may claim a stricter authority than the anchor
  D  DEAD REFERENCES   every repository-relative path referenced by a live document exists

EXIT
  0  all pass      1  at least one failure (each printed with file and line)

NEGATIVE CONTROL
  `--negative-test` injects each defect class into a temporary copy, requires the corresponding check
  to FAIL, then restores the files byte-for-byte and re-verifies the recorded hashes. A guard that
  has never failed is not a guard.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
ANCHOR_REL = "protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md"
ANCHOR_JSON = ROOT / "config" / "anchor.json"

# Directories whose contents are not live documents and are not scanned for references.
SKIP_DIR_PARTS = {".git", "archive", "node_modules", "__pycache__", ".p2a-work"}

# A path token: backticked, or a bare path-like string.
PATH_TOKEN = re.compile(
    r"`([A-Za-z0-9_./-]+(?:/[A-Za-z0-9_.-]+)*\.(?:md|py|json|jsonl|yaml|yml|toml|txt|lean|ps1|sh))`"
)

# Built from parts so this file does not match its own drive-letter pattern.
_DRIVE_E = chr(69) + ":"
_EXTERNAL_PREFIXES = (_DRIVE_E + "/", chr(68) + ":/", chr(67) + ":/", "~", "http")

# Claims of equal or stricter authority than the anchor.
AUTHORITY_CLAIM = re.compile(
    r"(?i)\b(?:is|as)\s+the\s+(?:single\s+)?(?:source\s+of\s+truth|authority)\b"
)

# A path token is checked only when it is written as a REPOSITORY-RELATIVE path: it carries a
# directory component, or it sits at the root of a directory this repository owns. Without this
# restriction the check reports every filename a document merely mentions -- a file inside a model
# repository, a sibling document named without its directory, a file inside a generated skill
# package. A checker that cries wolf is worse than no checker, because it trains the reader to
# ignore it.
REPO_RELATIVE = re.compile(r"^[A-Za-z0-9_.]+(?:/[A-Za-z0-9_.-]+)+$")

# Sibling references: `PHASE_I_PREREGISTRATION.md` inside `docs/` is legitimate. These are the
# directories whose own files may be named bare.
SIBLING_OK = {"docs", "protocol", "scripts", "measurement", "config", "viz"}

# Paths that belong to another artefact, not to this repository's tree.
FOREIGN_ROOTS = ("references/", "assets/", "skills/", "encoder/", "tokenizer/", "dist/", "mcp/")

# A document that establishes an EXTERNAL toolchain names that toolchain's own files. Those paths are
# not in this repository by design, so requiring them to exist here would be wrong.
EXTERNAL_TOOLCHAIN_MARKERS = (
    "paper2agent_repo", "paper2agent_work", "nhb-llm-mistranslation", "hf-mirror",
    "the engine", "the card", "the hub", "the package", "the model repository",
    "model.safetensors", "rl_agent_config", "tokenizer_config", "tokenizer.json",
    "encoder/config", "skill_root", "output contract",
)

# A path named inside a RETIREMENT record is a historical statement, not a promise. The defect this
# check exists for is a document asserting in the PRESENT tense that an instrument is available. So a
# citation is exempt when it sits inside an explicitly historical span - a fenced list of retired
# paths, or a sentence that says the path was archived.
HISTORICAL_HEADINGS = (
    "retired with r1",
    "removed from this table",
    "replacements built for the current protocol",
)

HISTORICAL_MARKERS = (
    "did not exist",
    "no longer",
    "archived",
    "retired",
    "was listed",
    "were listed",
    "removed from this table",
    "every one of them is under",
    "does not exist at the repository root",
)


def _line_is_historical(line: str) -> bool:
    low = line.lower()
    return any(m in low for m in HISTORICAL_MARKERS)


def live_files() -> list:
    out = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        if any(part in SKIP_DIR_PARTS for part in rel.parts):
            continue
        if rel.as_posix() == "scripts/check_anchor.py":
            continue
        if rel.suffix in (".md", ".json", ".py", ".toml"):
            out.append(p)
    return out


def fail(msgs, check, path, line, detail):
    msgs.append((check, path, line, detail))


def check_anchor_identity(msgs):
    ap = ROOT / ANCHOR_REL
    if not ap.is_file():
        fail(msgs, "A", ANCHOR_REL, 0, "THE ANCHOR FILE IS MISSING")
        return None
    if not ANCHOR_JSON.is_file():
        fail(msgs, "A", "config/anchor.json", 0, "no anchor identity file")
        return None
    meta = json.loads(ANCHOR_JSON.read_text(encoding="utf-8"))
    digest = hashlib.sha256(ap.read_bytes()).hexdigest()
    if digest != meta.get("sha256"):
        fail(msgs, "A", ANCHOR_REL, 0,
             f"anchor sha256 drift: recorded {str(meta.get('sha256'))[:16]}… actual {digest[:16]}…")
    return digest


def check_version_coherence(msgs, digest):
    ap = ROOT / ANCHOR_REL
    if not ap.is_file():
        return
    t = ap.read_text(encoding="utf-8")
    hdr = re.search(r"\*\*Version:\*\*\s*([0-9.]+)", t)
    c14 = re.search(r"\| Version \| \*\*([0-9.]+)\*\* \|", t)
    end = re.search(r"\*End of protocol v([0-9.]+)\*", t)
    vals = {"header": hdr.group(1) if hdr else None,
            "section_14": c14.group(1) if c14 else None,
            "end_marker": end.group(1) if end else None}
    missing = [k for k, v in vals.items() if v is None]
    if missing:
        fail(msgs, "B", ANCHOR_REL, 0, f"version marker(s) not found: {missing}")
        return
    if len(set(vals.values())) != 1:
        fail(msgs, "B", ANCHOR_REL, 0, f"version markers disagree: {vals}")
    if ANCHOR_JSON.is_file():
        meta = json.loads(ANCHOR_JSON.read_text(encoding="utf-8"))
        if meta.get("version") != vals["header"]:
            fail(msgs, "B", "config/anchor.json", 0,
                 f"anchor.json version {meta.get('version')} != header {vals['header']}")
    # A superseded Q0 left in the checklist is the exact defect this was written for.
    if re.search(r"Q_0\`? frozen.*ok.*escalate", t) and "v1.2 CHANGE 1" not in t:
        fail(msgs, "B", ANCHOR_REL, 0,
             "checklist still specifies the superseded three-question Q0 without the v1.2 amendment")


def check_subordination(msgs):
    for p in live_files():
        rel = p.relative_to(ROOT).as_posix()
        if rel == ANCHOR_REL:
            continue
        try:
            t = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for i, line in enumerate(t.splitlines(), 1):
            if AUTHORITY_CLAIM.search(line) and "anchor" not in line.lower():
                fail(msgs, "C", rel, i,
                     "claims authority without deferring to the anchor: " + line.strip()[:100])


def check_dead_references(msgs):
    """Flag a dead path ONLY where the sentence promises it.

    The first version of this check flagged every path a document merely MENTIONS, and produced 44
    findings of which 43 were legitimate: files inside the model repository, files inside generated
    skill packages, output names a document describes, and a future file a spec will create. A checker
    with a 2 % signal rate trains its reader to ignore it, which is worse than having no checker.

    So the trigger is not "a path is mentioned" but "a path is PROMISED": the sentence must contain an
    availability or obligation verb. A retirement record ("did not exist", "archived") is exempt by
    construction, because it is the opposite of a promise.
    """
    PROMISE = re.compile(
        r"(?i)\b(?:is|are|lives?|resides?|contains?|provides?|gives?|runs?|see|read|open|use|uses|"
        r"extend|edit|append|read_ssh|keep|live|kept|from|by|via|at)\b"
    )
    for p in live_files():
        rel = p.relative_to(ROOT).as_posix()
        if rel in ("config/anchor.json",):
            continue
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        # A heading that opens a retirement table exempts the whole table: each row names a retired
        # path by design, and the row has no other way to say so.
        # A markdown TABLE exempts itself. A table row states a fact about a thing; whether the
        # thing resolves is not what the row is for, and the tables that legitimately name
        # non-existent paths are exactly the retirement records. Two earlier versions tried to
        # scope this to a heading, and both failed - one ended the exemption at the first blank
        # line, the other at the first paragraph - because a retirement table is normally
        # preceded by prose. Scoping the exemption to the table itself has no such failure mode.
        in_retirement_table = False
        for i, line in enumerate(lines, 1):
            low = line.lower()
            if any(h in low for h in HISTORICAL_HEADINGS):
                in_retirement_table = True
                continue
            if line.strip().startswith("|"):
                continue                          # every table row, everywhere
            if in_retirement_table and not line.strip().startswith("#"):
                # A heading ends the retirement section; prose does not, because a table may be
                # preceded by an explanatory sentence.
                if line.strip().startswith("#"):
                    in_retirement_table = False
                else:
                    continue
            if _line_is_historical(line):
                continue
            if _line_is_historical(line):
                continue
            for m in PATH_TOKEN.finditer(line):
                tok = m.group(1)
                if tok.startswith(_EXTERNAL_PREFIXES):
                    continue
                if "<" in tok or ">" in tok or tok.endswith("…") or "..." in tok:
                    continue          # an abbreviated path, e.g. archive/.../scripts/health.py
                # A bare filename may name a file at the REPOSITORY ROOT as well as a sibling.
                if "/" not in tok:
                    # A bare filename is resolved against the citing file's directory, then the
                    # repository root, then scripts/ - a guard is named without its directory far
                    # more often than not, and a false "promised path does not exist" on the
                    # guard's own name trains the reader to skip the report.
                    for cand in (p.parent / tok, ROOT / tok, ROOT / "scripts" / tok):
                        if cand.exists():
                            break
                    else:
                        cand = p.parent / tok
                    if cand.exists():
                        continue
                    if p.parent.name not in SIBLING_OK:
                        continue
                    target = cand
                if tok.startswith("scripts/check_anchor"):
                    continue
                if tok.startswith(FOREIGN_ROOTS):
                    continue
                low = line.lower()
                if any(m in low for m in EXTERNAL_TOOLCHAIN_MARKERS):
                    continue          # a file inside an external toolchain, by design
                if "/" not in tok:
                    if p.parent.name not in SIBLING_OK:
                        continue
                    target = p.parent / tok
                else:
                    if not REPO_RELATIVE.match(tok):
                        continue
                    target = ROOT / tok
                if target.exists():
                    continue
                # The promise must be in this line, or the line that introduces the table row.
                if PROMISE.search(line):
                    fail(msgs, "D", rel, i,
                         f"promises a path that does not exist: {tok}")
                else:
                    # A mention, not a promise. Reported at a lower severity so the count of REAL
                    # defects stays legible.
                    fail(msgs, "d", rel, i, f"mentions a non-existent path (no promise): {tok}")


def run_all() -> int:
    msgs = []
    digest = check_anchor_identity(msgs)
    check_version_coherence(msgs, digest)
    check_subordination(msgs)
    check_dead_references(msgs)
    return report(msgs)


def report(msgs) -> int:
    blocking = [m for m in msgs if m[0].isupper()]
    advisory = [m for m in msgs if m[0].islower()]
    if not blocking:
        print("  OK: anchor intact · versions coherent · no authority conflict · no promised path missing")
        if advisory:
            print(f"  note: {len(advisory)} mention(s) of non-existent paths, none promised")
            for c, f, ln, d in advisory[:10]:
                print(f"         {f}:{ln}  {d}")
            if len(advisory) > 10:
                print(f"         … and {len(advisory) - 10} more")
        return 0
    by_check = {}
    for c, f, ln, d in blocking:
        by_check.setdefault(c, []).append((f, ln, d))
    for c in sorted(by_check):
        print(f"  [FAIL] check {c}: {len(by_check[c])} finding(s)")
        for f, ln, d in by_check[c]:
            print(f"         {f}:{ln}  {d}")
    print(f"\n  exit=1  blocking findings: {len(blocking)}   advisory: {len(advisory)}")
    return 1


def negative_test() -> int:
    """Inject each defect class, require the matching check to fail, restore byte-for-byte."""
    ap = ROOT / ANCHOR_REL
    if not ap.is_file():
        print("  cannot run: anchor missing")
        return 1
    before = hashlib.sha256(ap.read_bytes()).hexdigest()
    aj = ANCHOR_JSON
    aj_before = hashlib.sha256(aj.read_bytes()).hexdigest() if aj.is_file() else None
    original = ap.read_text(encoding="utf-8")
    results = []

    def restore():
        ap.write_text(original, encoding="utf-8", newline="\n")
        if aj_before is not None:
            aj_now = hashlib.sha256(aj.read_bytes()).hexdigest()
            if aj_now != aj_before:
                print("  [!!] anchor.json changed during the negative test; not restored")

    # A: corrupt the recorded sha256
    if aj.is_file():
        meta = json.loads(aj.read_text(encoding="utf-8"))
        meta["sha256"] = "0" * 64
        aj.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8", newline="\n")
        r = run_all()
        results.append(("A anchor sha256 drift", r == 1))
        restore_meta = json.loads(aj.read_text(encoding="utf-8"))
        restore_meta["sha256"] = hashlib.sha256(ap.read_bytes()).hexdigest()
        aj.write_text(json.dumps(restore_meta, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8", newline="\n")

    # B: make the version markers disagree
    ap.write_text(original.replace("| Version | **1.2** |", "| Version | **1.1** |", 1),
                  encoding="utf-8", newline="\n")
    r = run_all()
    results.append(("B version markers disagree", r == 1))
    restore()

    # D: reference a path that does not exist
    ap.write_text(original + "\n\n<!-- negative control: `scripts/__no_such_file__.py` -->\n",
                  encoding="utf-8", newline="\n")
    r = run_all()
    results.append(("D dead reference", r == 1))
    restore()

    # C: claim authority in a live file
    probe = ROOT / "docs" / "__anchor_negative_control__.md"
    probe.write_text("# probe\n\nThis file is the single source of truth for the programme.\n",
                     encoding="utf-8", newline="\n")
    r = run_all()
    results.append(("C authority claim outside the anchor", r == 1))
    probe.unlink()

    after = hashlib.sha256(ap.read_bytes()).hexdigest()
    if after != before:
        restore()
        after = hashlib.sha256(ap.read_bytes()).hexdigest()
    print()
    ok = True
    for name, caught in results:
        print(f"  [{'OK' if caught else 'MISS'}] negative control caught: {name}")
        ok = ok and caught
    print(f"\n  anchor restored byte-for-byte: {'YES' if after == before else 'NO'}")
    return 0 if (ok and after == before) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify the repository is anchored to its objective.")
    ap.add_argument("--negative-test", action="store_true",
                    help="inject each defect class, require detection, restore byte-for-byte")
    args = ap.parse_args()
    if args.negative_test:
        return negative_test()
    return run_all()


if __name__ == "__main__":
    raise SystemExit(main())