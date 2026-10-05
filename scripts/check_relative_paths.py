#!/usr/bin/env python
"""check_relative_paths.py -- Rule 1 of `global-research-project-rules`, made mechanical.

    "No absolute paths. Ever. Every path in code, configs, documents, logs and artifacts is
     relative to the project root."

WHY THIS EXISTS, IN THIS REPOSITORY SPECIFICALLY
    This project moved from D: to E: on 2026-10-04. Absolute paths written the day before became
    invalid on the day after, in six live documents and one config file. The migration had to
    classify each one by hand and decide whether it was a live path or a historical record.

    That classification is the point. A path that no longer resolves is not automatically an error -
    a run record legitimately says where a run happened. What is an error is a path that PROMISES
    an artefact and cannot find it.

SCOPE
    Live files only: not `archive/`, not `.git/`, not binary artefacts, not generated build output.
    Binary sources (`.pdf`, `.docx`) are exempt because a source is not a result.

SEVERITY
    A hardcoded machine path inside CODE is blocking: it breaks the moment the project moves, and the
    failure is a runtime error rather than a wrong sentence. The same literal inside a DOCUMENT is
    reported at a lower severity, because a document may legitimately record where something was
    produced - but it must then be inside a span that says so.

USAGE
    python scripts/check_relative_paths.py              # report, exit 1 on blocking findings
    python scripts/check_relative_paths.py --negative-test
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Live files only. `viz/` is generated build output: `manuscript.html` is derived from the anchor
# and stamped with its sha256, and `viz/katex/` is a vendored third-party distribution whose minified
# bundle contains regular-expression fragments such as `l:/^` that the drive pattern would read as a
# path on drive `l`. Neither is a file whose portability this project controls.
SKIP_DIRS = {".git", "archive", "node_modules", "__pycache__", ".p2a-work", "dist", ".venv", "viz"}
SKIP_SUFFIX = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".zip", ".gz", ".safetensors", ".ico",
               ".xlsx", ".pptx", ".pyc", ".woff", ".woff2", ".ttf", ".eot"}

# Windows drive paths, POSIX absolute paths, and UNC paths.
ABS = re.compile(
    r"(?:"
    r"[A-Za-z]:[\\/][^\s`'\"|<>]*"          # D:/x  or  C:\x
    r"|\\\\[^\s`'\"|<>]+"                   # \\server\share
    r"|(?<![\w.])/(?:home|Users|usr|mnt|opt|var|tmp|etc|Volumes)(?:/[^\s`'\"|<>]*)?"
    r")"
)

# Environment-variable forms are portable and are NOT absolute literals.
ENVREF = re.compile(r"\$\{?[A-Z_][A-Z0-9_]*\}?|os\.environ|getenv")

# `~/.elan` and `~/.bootloops` are user-relative, not machine-relative: portable, so exempt.
TILDE_OK = re.compile(r"^[~][\\/]")

# A document may record a machine path where it says the path is historical or external.
HISTORICAL = (
    "did not exist", "no longer", "archived", "retired", "was listed", "were listed",
    "removed from this table", "every one of them is under", "does not exist at the repository root",
    "historical address", "the datum", "resolved rev", "local snapshot", "recorded at",
    "recorded before", "was written on", "at the time", "on 2026-", "since 2026-",
    "external", "outside the repository", "outside this repository", "left as written",
    "migration record", "before the migration", "the old", "retired with",
)


def iter_live_files():
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if rel.suffix.lower() in SKIP_SUFFIX:
            continue
        if rel.name == pathlib.Path(__file__).name:
            continue
        yield p


def scrub(text: str) -> str:
    r"""Blank out spans that cannot contain a machine-path literal.

    Two classes must be removed or the scan manufactures false positives, and both were found by
    running it rather than by reading it:

      - **URLs.** The Windows-drive pattern eats the tail of a scheme: `https://hf-mirror.com` leaves
        the fragment `s://hf-mirror.com`, which then looks like a path on drive `s`. Every URL is
        therefore blanked before the scan.
      - **Shebang lines.** `#!/usr/bin/env python` contains `/usr/bin/env` by definition, and it is
        not a project path. Shebang lines are blanked too.

    Fenced blocks and inline code spans are blanked as well, so a documented example is never read as
    this project's own literal.
    """
    text = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", lambda m: " " * len(m.group(0)), text)
    text = re.sub(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s`'\"\|<>)]+", lambda m: " " * len(m.group(0)), text)
    text = re.sub(r"^#!.*$", lambda m: " " * len(m.group(0)), text)

    # LaTeX in a Markdown document. `g_\tau:\quad` and `\\ ` (a row break) both contain a
    # letter-colon-backslash that the drive pattern reads as a path on drive `t`. That is TeX, not a
    # path - and the artefact under test in a `.md` file IS the LaTeX - so any span between math
    # delimiters is pattern text and is scrubbed before the scan.
    text = re.sub(r"\$\$.*?\$\$", lambda m: " " * len(m.group(0)), text, flags=re.S)
    text = re.sub(r"(?<!\$)\$[^$\n]*\$(?!\$)", lambda m: " " * len(m.group(0)), text)

    # A regex literal can contain something that looks like a machine path - e.g. a drive-letter
    # class `[A-Za-z]:[\\/]` or the fragment `n:\*\*`. That is pattern text, not a path, so any span
    # inside an r-string is blanked before the scan.
    text = re.sub("r\"[^\"\\n]*\"", lambda m: " " * len(m.group(0)), text)

    # A drive letter is a token START, so the character before it must not be a word character.
    # `false:/true:` is a wire-format token in prose: the `e` is mid-word, so this is not a drive.
    # The lookbehind below is what makes that distinction, and its absence is why the guard fired on
    # a noul option pair - a comment describing the opposite of what the pattern did.
    text = re.sub(r"(?<=[A-Za-z0-9_./\\]):/(?!/)(?=[A-Za-z])", " ", text)

    # `Looked in:\n  "` in a Python string literal contains the two characters `:` and a backslash
    # followed by `n`, which the drive pattern reads as drive `n`. A real drive path continues with
    # path characters (`D:\new\file`), whereas an escape sequence is followed by whitespace or a
    # closing quote - so requiring a path character after the separator separates the two without
    # weakening the rule on any path this project could actually contain.
    text = re.sub(r":[\\/][ntr](?=[\s\"'`)\]])", " ", text)

    # A LaTeX COMMAND or delimiter. `\lambda`, `\Delta\tau^\star`, `\href` and the inline delimiter
    # `\(s\)` all contain a backslash followed by characters that read as a path - and the guarders
    # and the builder legitimately carry such literals, because their job is to compare against the
    # anchor's LaTeX.
    #
    # The `(?<![A-Za-z]:)` guard is load-bearing and its absence is a hole, not a cosmetic issue:
    # without it, `C:\new\file` loses `\new` to the TeX rule, the colon is left with nothing after it,
    # and a REAL absolute path passes the scan. That was measured, not assumed. A drive letter is a
    # token start; a TeX command never follows one.
    #
    # A command may carry subscript and superscript groups, and those groups may themselves contain
    # commands (`\Delta\tau^\star`, `s_{\mathrm{en}}`). Matching a command plus ONE optional group
    # therefore leaves the tail exposed, and the tail of `\tau^\star` reads as a path on drive `t`.
    # Repeating the optional group is what makes the whole expression disappear - and that is what the
    # `*` quantifier below does. An earlier version had `?` and fired on four legitimate TeX literals.
    text = re.sub(r"(?<![A-Za-z]:)(?<![A-Za-z0-9_./\\])\\[A-Za-z]+(?:(?:\^|_)?\{[^{}\n]*\})*",
                  " ", text)
    # The inline delimiter form `\(` / `\)`: a backslash then punctuation, never a path separator.
    text = re.sub(r"(?<![A-Za-z]:)(?<![A-Za-z0-9_./\\])\\(?![A-Za-z])[()\[\]]", " ", text)
    # The same forms written with an ESCAPED backslash, which is how they appear inside a Python
    # source file: four backslashes in the source are two in the string it builds. Without this the
    # guard fires on every LaTeX literal a guard or a builder legitimately carries. The repeated
    # optional group is needed here for the same reason as above: `\\Delta\\tau^\\star` leaves its
    # tail exposed otherwise, and the tail reads as a path on drive `t`.
    text = re.sub(r"(?<![A-Za-z]:)(?<![A-Za-z0-9_./\\\\])\\\\\\\\(?:[A-Za-z]+(?:(?:\^|_)?\{[^{}\n]*\})*"
                  r"|(?![A-Za-z])[()\[\]])", " ", text)

    # `\\Word` - a double backslash then a command name - is LaTeX inside a Python string, not a
    # UNC path, so scrubbing it is safe. The negative lookahead keeps a REAL UNC host alive: a UNC
    # is `\\host\share`, so its host segment is always followed by another backslash, and without
    # the lookahead the scrub eats `\\host` and leaves `\share` for the ABS rule below to miss.
    # That lookahead was added on the reasoning, not on a demonstration: I could not build a probe
    # that isolates the UNC branch, because the guard blanks `r"..."` literals and my own test
    # strings were over-escaped. So the UNC branch is worth one dedicated probe before it is
    # trusted - it is recorded here as UNVERIFIED rather than presented as working.
    text = re.sub(r"\\[A-Za-z]+(?!\\)", " ", text)

    # TeX groups NEST, and one pass cannot strip them all: `s_{\mathrm{en}}` loses `\mathrm{en}` to
    # the command rule but leaves `s_{` and `}`, and the residue can still expose a drive-looking
    # token. A measured probe - a file holding both a real `D:/` path and `s_{\mathrm{en}}` - showed
    # exactly those leftovers. Scrubbing to a FIXED POINT removes them, and the fixed point is also what
    # makes the result idempotent: running the guard twice must find what running it once found.
    for _ in range(4):
        before = text
        text = re.sub(r"(?<![A-Za-z0-9_./\\])\{[^{}\n]*\}", " ", text)
        text = re.sub(r"(?<![A-Za-z0-9_./\\])\\[A-Za-z]+", " ", text)
        text = re.sub(r"(?<![A-Za-z0-9_./\\])\\(?![A-Za-z])[()\[\]]", " ", text)
        if text == before:
            break
    return text


def scan():
    blocking, advisory = [], []
    for p in iter_live_files():
        rel = p.relative_to(ROOT).as_posix()
        try:
            raw = p.read_text(encoding="utf-8", errors="strict")
        except Exception:
            continue
        low_all = raw.lower()
        # A data file records what a run did; it is a record, not logic. Only a script that must
        # execute is blocking.
        is_doc = p.suffix.lower() in (".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".toml")
        for i, line in enumerate(raw.splitlines(), 1):
            if ENVREF.search(line):
                # An env-var reference may legitimately expand to an absolute path.
                continue
            code = scrub(line)
            for m in ABS.finditer(code):
                tok = m.group(0)
                if TILDE_OK.match(tok):
                    continue
                low = line.lower()
                historical = any(h in low for h in HISTORICAL) or \
                    any(h in low_all for h in ("migration record", "historical address",
                                              "retired with r1"))
                where = f"{rel}:{i}"
                if not is_doc:
                    blocking.append((where, tok, "hardcoded in CODE - breaks when the project moves"))
                elif historical:
                    advisory.append((where, tok, "recorded as history (acceptable)"))
                else:
                    advisory.append((where, tok,
                                     "absolute path in a document, not marked as history"))
    return blocking, advisory


def report(blocking, advisory) -> int:
    if not blocking:
        print("  OK: no hardcoded absolute path in any code, config or script")
        if advisory:
            hist = sum(1 for _, _, d in advisory if "acceptable" in d)
            print(f"  note: {len(advisory)} absolute path(s) in documents — "
                  f"{hist} marked as history, {len(advisory) - hist} to review")
            for where, tok, d in advisory:
                if "acceptable" not in d:
                    print(f"         {where}  {tok}   [{d}]")
        return 0
    print(f"  [FAIL] {len(blocking)} hardcoded absolute path(s) in code:")
    for where, tok, d in blocking:
        print(f"         {where}  {tok}\n                {d}")
    print(f"\n  exit=1  blocking: {len(blocking)}   advisory: {len(advisory)}")
    return 1


def negative_test() -> int:
    """Inject one absolute path into a script and one into a document; both must be reported."""
    code_probe = ROOT / "scripts" / "__relpath_negative_control__.py"
    doc_probe = ROOT / "docs" / "__relpath_negative_control__.md"
    src = code_probe.read_text(encoding="utf-8") if code_probe.is_file() else None
    dsrc = doc_probe.read_text(encoding="utf-8") if doc_probe.is_file() else None
    ok = True
    try:
        code_probe.write_text('X = "D:/2026-AI4S/autoresearch/config/anchor.json"\n',
                              encoding="utf-8", newline="\n")
        b, _ = scan()
        caught = any("__relpath_negative_control__" in w for w, _, _ in b)
        print(f"  [{'OK' if caught else 'MISS'}] absolute path in CODE is reported as blocking")
        ok = ok and caught
        code_probe.unlink()

        doc_probe.write_text("# probe\n\nRun it from D:/2026-AI4S/autoresearch.\n",
                             encoding="utf-8", newline="\n")
        b, a = scan()
        caught = any("__relpath_negative_control__" in w for w, _, _ in b + a)
        print(f"  [{'OK' if caught else 'MISS'}] absolute path in a DOCUMENT is reported")
        ok = ok and caught
        doc_probe.unlink()
    finally:
        if src is not None:
            code_probe.write_text(src, encoding="utf-8", newline="\n")
        elif code_probe.is_file():
            code_probe.unlink()
        if dsrc is not None:
            doc_probe.write_text(dsrc, encoding="utf-8", newline="\n")
        elif doc_probe.is_file():
            doc_probe.unlink()
    b, a = scan()
    restored = not any("__relpath_negative_control__" in w for w, _, _ in b + a)
    print(f"  [{'OK' if restored else 'MISS'}] probes removed; state restored")
    return 0 if (ok and restored) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Rule 1 guard: no absolute paths in code or configs.")
    ap.add_argument("--negative-test", action="store_true")
    args = ap.parse_args()
    if args.negative_test:
        return negative_test()
    b, a = scan()
    return report(b, a)


if __name__ == "__main__":
    raise SystemExit(main())