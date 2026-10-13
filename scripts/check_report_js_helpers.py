"""check_report_js_helpers.py -- every function the report calls must exist.

WHY THIS EXISTS
    The report renders its numbers in JavaScript. A helper that is called but never defined does not
    raise: the expression evaluates to `NaN` and the page prints "NaN%", or to a ReferenceError that
    only fires when that branch runs. A guard written during this build added a call to a helper for
    two-decimal percentages that did not exist -- the existing one rendered one decimal, and the
    reason for adding it was that one decimal hides the agreement being cited (1.19 % and 1.17 %
    both render "1.2%"). Nothing in the suite would have noticed.

WHAT IT CHECKS
    Every identifier called as `name(...)` inside the report's inline scripts is either defined in
    that script (`const`/`let`/`var`/`function`) or a JavaScript or DOM builtin from a fixed list.
    Method calls (`obj.m(...)`) are excluded, since they are resolved on the object.

NEGATIVE CONTROL
    `--negative-test` writes a copy of the report with a call to a name that is defined nowhere and
    points the check at it; the check must report that name. The copy is made in the scratch
    directory, so a real file is never edited to test a guard.
"""
from __future__ import annotations

import pathlib
import re
import shutil
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
REPORT = REPO / "viz" / "report" / "technical-report.html"

# Names that are not defined in the file and do not need to be: language builtins and DOM globals.
BUILTINS = {
    "document", "window", "console", "navigator", "location", "history", "localStorage",
    "Number", "String", "Boolean", "Math", "JSON", "Object", "Array", "Date", "RegExp", "Error",
    "parseInt", "parseFloat", "isNaN", "isFinite", "alert", "confirm", "prompt",
    "setTimeout", "setInterval", "clearTimeout", "clearInterval", "requestAnimationFrame",
    "encodeURIComponent", "decodeURIComponent", "encodeURI", "decodeURI", "fetch", "structuredClone",
    "Intl", "Set", "Map", "WeakMap", "Promise", "Symbol", "BigInt", "Proxy", "Reflect",
    "Infinity", "NaN", "undefined", "globalThis", "MutationObserver", "IntersectionObserver",
    "getComputedStyle", "matchMedia", "URL", "Blob", "FileReader",
    # keywords that can precede a parenthesis and are not calls
    "if", "for", "while", "switch", "catch", "return", "typeof", "function", "new", "do", "else",
    "in", "of", "delete", "void", "case", "break", "continue", "throw", "yield", "await", "async",
    "class", "try", "finally", "super", "this", "import", "export", "default", "extends",
    "instanceof", "with", "get", "set", "static",
}

DEF_RE = re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=", re.UNICODE)
DEF_FN_RE = re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(", re.UNICODE)
# Only a parameter-like list counts. This set can only MASK a real finding (a name treated as defined
# when it is not), so it is kept narrow: `(see 2.4) {` in prose must not define `see`.
DEF_PARAM_RE = re.compile(
    r"(?:function\s*)?\(\s*([A-Za-z_$][\w$]*(?:\s*,\s*[A-Za-z_$][\w$]*)*\s*)\)\s*(?:=>|\{)",
    re.UNICODE)
DEF_ARROW_RE = re.compile(r"(?:^|[,(\s])([A-Za-z_$][\w$]*)\s*=>", re.UNICODE)
# No whitespace before the paren. JavaScript in this file is written `foo(x)`, while English prose
# inside the rendered strings is written "the term (see 2.4)" -- an earlier version allowed `\s*\(`
# and read eight ordinary words as calls. Method calls (`obj.m(`) are excluded by the lookbehind.
CALL_RE = re.compile(r"(?<![\w$.])([A-Za-z_$][\w$]*)\(", re.UNICODE)
SCRIPT_RE = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.S | re.I)


def code_only(src: str) -> str:
    """Blank out string, template-literal and comment CONTENT, keeping `${...}` as code.

    Prose is written inside template literals in this report, and prose is full of parentheses:
    "the correlation (corr(...))", "(var(x)) if ...". Scanning the raw text reads those words as
    calls. A call can only exist in code, so the scan runs on a version where everything that is not
    code has been replaced by spaces of the same length -- which keeps offsets stable and lets the
    error messages point at real line numbers if that is ever added. Expressions inside `${}` are
    code and are kept.
    """
    out: list[str] = []
    i, n = 0, len(src)
    # stack of "brace depth seen when this template began"; a template ends at its own backtick
    while i < n:
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(" " * (j - i))
            i = j
            continue
        c = src[i]
        if c in "\"'":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            j = min(j + 1, n)
            out.append(" " * (j - i))
            i = j
            continue
        if c == "`":
            # template literal: keep the delimiters and any ${...} expressions, blank the prose
            out.append("`")
            i += 1
            depth = 0
            while i < n:
                if src.startswith("${", i):
                    depth += 1
                    out.append("${")
                    i += 2
                    continue
                if depth and src[i] == "}":
                    depth -= 1
                    out.append("}")
                    i += 1
                    continue
                if depth == 0 and src[i] == "`":
                    out.append("`")
                    i += 1
                    break
                if depth and src[i] in "\"'`" or src.startswith("//", i) or src.startswith("/*", i):
                    # a nested literal inside an expression: blank it, keep the delimiters
                    if depth:
                        seg_start = i
                        if src[i] == "`" or src[i] in "\"'":
                            q = src[i]
                            j = i + 1
                            while j < n and src[j] != q:
                                j += 2 if src[j] == "\\" else 1
                            j = min(j + 1, n)
                        elif src.startswith("//", i):
                            j = src.find("\n", i)
                            j = n if j < 0 else j
                        else:
                            j = src.find("*/", i + 2)
                            j = n if j < 0 else j + 2
                        inner = src[i:j]
                        keep = "".join(ch if ch in "\"'`${}" else " " for ch in inner)
                        out.append(keep)
                        i = j
                        continue
                out.append(src[i] if depth else " ")
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def scripts(html: str) -> list[str]:
    return SCRIPT_RE.findall(html)


def analyse(html: str) -> tuple[set[str], set[str]]:
    defined: set[str] = set()
    called: set[str] = set()
    for raw in scripts(html):
        src = code_only(raw)
        for m in DEF_RE.finditer(src):
            defined.add(m.group(1))
        for m in DEF_FN_RE.finditer(src):
            defined.add(m.group(1))
        for m in DEF_PARAM_RE.finditer(src):
            for p in m.group(1).split(","):
                p = p.strip().lstrip("...")
                if re.fullmatch(r"[A-Za-z_$][\w$]*", p):
                    defined.add(p)
        for m in DEF_ARROW_RE.finditer(src):
            defined.add(m.group(1))
        for m in CALL_RE.finditer(src):
            called.add(m.group(1))
    return defined, called


def report_missing(html: str) -> list[str]:
    defined, called = analyse(html)
    return sorted(n for n in called - defined - BUILTINS)


def main() -> int:
    path = REPORT
    if "--path" in sys.argv:
        path = pathlib.Path(sys.argv[sys.argv.index("--path") + 1])
    html = path.read_text(encoding="utf-8")
    defined, called = analyse(html)
    missing = report_missing(html)
    print("  %s: %d inline script block(s), %d defined names, %d called names"
          % (path.name, len(scripts(html)), len(defined), len(called)))

    if "--negative-test" in sys.argv:
        scratch = pathlib.Path(__import__("os").environ.get("TMPDIR", "."))
        probe = scratch / "probe_report_undefined_helper.html"
        # a call to a name defined nowhere and not a builtin
        injected = html.replace("</body>", "<script>zzUndefinedHelper(1);</script></body>", 1)
        if injected == html:
            print("  [FAIL] the control could not be injected: no </body> in the report")
            return 1
        probe.write_text(injected, encoding="utf-8")
        try:
            found = report_missing(injected)
            if "zzUndefinedHelper" in found:
                print("  [OK] negative control fires: the injected call is reported (%s)"
                      % ", ".join(found))
                return 0
            print("  [FAIL] the injected undefined call was NOT reported: %s" % (found or "none"))
            return 1
        finally:
            probe.unlink(missing_ok=True)

    if missing:
        print()
        for n in missing:
            print("  [FAIL] %s() is called but never defined in the report's scripts" % n)
        print()
        print("  This does not raise at load: the branch renders NaN or throws only when reached.")
        return 1
    print("  [OK] every called name is defined in the report or is a builtin")
    return 0


if __name__ == "__main__":
    sys.exit(main())
