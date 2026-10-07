#!/usr/bin/env python
"""build_manuscript_html.py -- render the anchor to a self-contained, offline HTML manuscript.

WHY A GENERATOR AND NOT A HAND-WRITTEN PAGE
    The protocol is the programme's single authority. An HTML manuscript that were written by hand
    would be a SECOND copy of the objective, and two copies of an objective drift - which is the
    failure this repository exists to prevent. So the HTML is DERIVED, the Markdown is the source,
    and the build stamps the anchor's sha256 into the output. If the anchor moves and the HTML is not
    rebuilt, the stamp says so.

MATH
    Rendered with KaTeX, not MathJax: KaTeX auto-render covers the LaTeX subset this protocol uses
    (`\\xrightarrow`, `\\underbrace`, `\\mathcal`, `\\mathbf`, `\\text`, alignment) and produces static
    HTML, so the page stays correct when opened from disk with no network.

    The KaTeX distribution is COPIED INTO THE OUTPUT DIRECTORY rather than loaded from a CDN. A CDN
    script was tried first and returned HTTP 200 with a zero-byte body from this host, which would have
    produced a page that renders correctly on the author's machine and silently fails everywhere else.
    Offline correctness is the requirement, so the fonts and scripts travel with the document.

    Math is rendered CLIENT-SIDE by default and the page also carries the raw TeX in the DOM, so a
    reader whose browser blocks JavaScript still sees every expression rather than an empty gap.

OUTPUT
    viz/manuscript.html   plus viz/katex/ (scripts, css, fonts) and viz/protocol.md (the source)
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import os
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ANCHOR = ROOT / "protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md"
OUT_DIR = ROOT / "viz"


def katex_candidates():
    """Where a KaTeX distribution may live, in resolution order.

    An absolute path in this source would break on every other checkout, and this repository forbids
    absolute paths outright (scripts/check_relative_paths.py). Resolution is therefore: an explicit
    environment override, a project-local install, then the Hermes agent's own copy found RELATIVE to
    $HERMES_HOME rather than to a hard-coded user directory.
    """
    out = []
    env = os.environ.get("KATEX_DIST")
    if env:
        out.append(pathlib.Path(env))
    out.append(ROOT / "node_modules/katex/dist")
    hh = os.environ.get("HERMES_HOME")
    if hh:
        out.append(pathlib.Path(hh) / "hermes-agent/node_modules/katex/dist")
    return out

CSS = """
:root{
  --fg:#1a1a1a; --muted:#5b616b; --accent:#1f5c8b; --rule:#d8dce3; --bg:#ffffff;
  --code-bg:#f5f6f8; --warn-bg:#fff8e6; --warn-br:#e0b84c;
}
@media (prefers-color-scheme: dark){
  :root{ --fg:#e8e8e8; --muted:#a0a6b0; --accent:#7fb3d8; --rule:#333a44;
         --bg:#14161a; --code-bg:#1c1f25; --warn-bg:#241f10; --warn-br:#8a6f1e; }
}
*{box-sizing:border-box}
html{ -webkit-text-size-adjust:100%; }
body{
  margin:0; background:var(--bg); color:var(--fg);
  font:16px/1.68 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",
       "Noto Sans CJK SC","Source Han Sans SC",sans-serif;
}
.wrap{ max-width:860px; margin:0 auto; padding:48px 28px 96px; }
header.doc{ border-bottom:2px solid var(--rule); padding-bottom:20px; margin-bottom:34px; }
header.doc h1{ font-size:1.72rem; line-height:1.3; margin:0 0 10px; letter-spacing:-.01em; }
header.doc .sub{ color:var(--muted); font-size:.94rem; margin:0 0 4px; }
header.doc .stamp{
  font:12px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; color:var(--muted);
  background:var(--code-bg); border:1px solid var(--rule); border-radius:6px;
  padding:8px 10px; margin-top:14px; overflow-wrap:anywhere;
}
h2{ font-size:1.24rem; margin:44px 0 12px; padding-bottom:6px; border-bottom:1px solid var(--rule); }
h3{ font-size:1.06rem; margin:28px 0 8px; }
h4{ font-size:.99rem; margin:22px 0 6px; color:var(--muted); }
p{ margin:12px 0; }
a{ color:var(--accent); }
code{ background:var(--code-bg); padding:.12em .38em; border-radius:4px;
      font:.88em/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; }
pre{ background:var(--code-bg); border:1px solid var(--rule); border-radius:8px;
     padding:14px 16px; overflow-x:auto; }
pre code{ background:none; padding:0; font-size:.86rem; }
blockquote{ margin:16px 0; padding:10px 16px; border-left:3px solid var(--accent);
            background:var(--code-bg); color:var(--fg); }
blockquote p{ margin:8px 0; }
table{ border-collapse:collapse; width:100%; margin:16px 0; font-size:.93rem;
       display:block; overflow-x:auto; }
th,td{ border:1px solid var(--rule); padding:7px 10px; text-align:left; vertical-align:top; }
th{ background:var(--code-bg); font-weight:600; }
tbody tr:nth-child(even){ background:color-mix(in srgb, var(--code-bg) 55%, transparent); }
hr{ border:0; border-top:1px solid var(--rule); margin:32px 0; }
ul,ol{ padding-left:1.5em; }
strong{ font-weight:650; }
/* ---- the formal-coupling chain and every display formula ---- */
.katex-display{ overflow-x:auto; overflow-y:hidden; padding:6px 0; margin:14px 0; }
.katex{ font-size:1.04em; }
/* A raw-TeX fallback sits behind every expression: if scripting is off, the TeX is what a reader
   sees, which is strictly better than an empty box. */
.math-fallback{ display:none; }
.no-js .math-fallback{ display:block; color:var(--muted);
  font:.92em/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; }
.math-block{ margin:14px 0; text-align:center; }
footer.doc{ margin-top:56px; padding-top:18px; border-top:1px solid var(--rule);
             color:var(--muted); font-size:.85rem; }
@media print{
  body{ background:#fff; color:#000; }
  .wrap{ max-width:none; padding:0; }
  a{ color:#000; text-decoration:underline; }
  h2{ break-after:avoid; } table,.katex-display{ break-inside:avoid; }
}
"""

HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="katex/katex.min.css">
<style>{css}</style>
</head>
<body class="no-js">
<div class="wrap">
<header class="doc">
  <h1>{title}</h1>
  <p class="sub">{subtitle}</p>
  <p class="stamp">{stamp}</p>
</header>
{body}
<footer class="doc">
  <p>Generated by <code>scripts/build_manuscript_html.py</code> from the repository's global anchor.
     Do not edit this file: edit the Markdown and rebuild, or the two will disagree.</p>
  <p>Math is rendered locally with KaTeX {katex_version}; no network request is made.</p>
</footer>
</div>
<script>document.body.classList.remove('no-js');</script>
<!-- Scripts are NOT deferred with an onload attribute: a `defer` script's onload does not fire, so
     renderMathInElement was never called in the first build. An explicit initialiser runs after the
     libraries are present, and reports whether it succeeded rather than failing silently. -->
<script src="katex/katex.min.js"></script>
<script src="katex/auto-render.min.js"></script>
<script>
(function () {{
  if (typeof renderMathInElement !== 'function') {{
    document.querySelector('.stamp').insertAdjacentHTML('afterend',
      '<p class="stamp" style="border-color:#c00">Math did not load: KaTeX is missing from ' +
      'viz/katex/. The raw TeX below is still readable.</p>');
    return;
  }}
  renderMathInElement(document.body, {{
    delimiters: [
      {{left: '$$', right: '$$', display: true}},
      {{left: '$',  right: '$',  display: false}}
    ],
    throwOnError: false,
    strict: false,
    trust: function (ctx) {{ return ctx.command !== '\\href'; }}
  }});
  var n = document.querySelectorAll('.katex').length;
  var d = document.querySelectorAll('.katex-display').length;
  var s = document.querySelector('.stamp');
  var extra = document.createElement('p');
  extra.className = 'stamp';
  extra.textContent = 'math rendered: ' + n + ' expression(s), ' + d + ' display block(s)';
  s.parentNode.insertBefore(extra, s.nextSibling);
}})();
</script>
</body>
</html>
"""


def find_katex():
    cands = katex_candidates()
    for c in cands:
        if (c / "katex.min.js").is_file():
            return c
    raise SystemExit("KaTeX distribution not found. Point $KATEX_DIST at a katex/dist directory, "
                     "or run `npm install katex` in the project root. Looked in:\n  "
                     + "\n  ".join(str(c) for c in cands))


def copy_katex(src: pathlib.Path, dest: pathlib.Path):
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("katex.min.js", "katex.min.css"):
        shutil.copy2(src / name, dest / name)
    auto = src / "contrib/auto-render.min.js"
    if auto.is_file():
        shutil.copy2(auto, dest / "auto-render.min.js")
    fonts = src / "fonts"
    if fonts.is_dir():
        if (dest / "fonts").is_dir():
            shutil.rmtree(dest / "fonts")
        shutil.copytree(fonts, dest / "fonts")
    ver = "unknown"
    pkg = src.parent / "package.json"
    if pkg.is_file():
        m = re.search(r'"version"\s*:\s*"([^"]+)"', pkg.read_text(encoding="utf-8", errors="replace"))
        if m:
            ver = m.group(1)
    return ver


def strip_anchor_banner(md: str) -> str:
    """Remove the meta blockquote that documents the anchor's own version history.

    It is governance metadata, not manuscript content: a reader of the protocol does not need to be
    told which amendment changed which section. It stays in the anchor, which governs.
    """
    out, in_banner = [], False
    for line in md.splitlines():
        if line.startswith(">"):
            out.append(line)
            continue
        if out and all(l.startswith(">") or not l.strip() for l in out[-3:]):
            pass
        out.append(line)
    # drop the FIRST contiguous blockquote block (the version table)
    res, dropped = [], False
    for line in out:
        if not dropped and line.startswith(">"):
            dropped = True
            continue
        if dropped:
            if line.startswith(">"):
                continue
            if not line.strip():
                dropped = False          # banner ends at the first blank line
                continue
        res.append(line)
    return "\n".join(res)


CDATA_OPEN = "<!--MATH-KEEP-->"
CDATA_CLOSE = "<!--/MATH-KEEP-->"


def protect_math(md: str) -> str:
    """Move every expression out of Markdown's reach BEFORE parsing, and back in after.

    THE ROOT CAUSE THIS FIXES
        `\\underbrace{i}_{\\text{intention}}` reaches the Markdown parser as ordinary text, and the
        parser eats the backslashes: `\\,`, `\\cdot`, `\\;` and `\\ ` are all escape sequences in
        Markdown, so the LaTeX arrives at the renderer already destroyed. That is why the first build
        produced a page with the source visible and zero rendered nodes - and no renderer can recover
        from it, because the damage happens before the renderer runs.

        The fix is to lift each expression out into an HTML comment, which Markdown passes through
        untouched, and restore it afterwards. The raw TeX is therefore byte-identical to the source.

    Display and inline are handled separately because they sit between different delimiters.
    """
    blocks = []

    def keep_display(m):
        blocks.append(m.group(0))
        return f"{CDATA_OPEN}{len(blocks) - 1}{CDATA_CLOSE}"

    md = re.sub(r"^[ \t]*\$\$[ \t]*\n(.*?)\n[ \t]*\$\$[ \t]*$",
                lambda m: keep_display(m), md, flags=re.S | re.M)

    def keep_inline(m):
        blocks.append(m.group(0))
        return f"{CDATA_OPEN}{len(blocks) - 1}{CDATA_CLOSE}"

    # A single `$` that is not part of `$$`, and not an escaped `\$`.
    md = re.sub(r"(?<!\\)(?<!\$)\$(?!\$)(.+?)(?<!\\)(?<!\$)\$(?!\$)",
                lambda m: keep_inline(m), md, flags=re.S)
    return md, blocks


def restore_math(text: str, blocks) -> str:
    """Put the expression back WITH ITS DELIMITERS.

    The first version stripped them: `raw[2:-2]` for a display block and `raw[1:-1]` for inline.
    That removed the `$$` and the `$` along with the fence, so KaTeX received bare TeX with no
    delimiters and matched nothing - the page reported "math rendered: 0" while looking perfectly
    healthy. The delimiters are part of the expression, not decoration around it.
    """
    def put(m):
        return blocks[int(m.group(1))]
    return re.sub(CDATA_OPEN + r"(\d+)" + CDATA_CLOSE, put, text)


def md_to_html(md: str) -> str:
    from markdown_it import MarkdownIt
    md_it = MarkdownIt("commonmark", {"html": True, "linkify": False})
    md_it.enable("table")
    md_it.enable("strikethrough")
    guarded, blocks = protect_math(md)
    html = md_it.render(guarded)
    return restore_math(html, blocks)


def main() -> int:
    ap = argparse.ArgumentParser(description="Render the anchor to an offline HTML manuscript.")
    # THIS IS A SUPERSEDED PROTOCOL RENDERER AND NO LONGER OWNS THE MANUSCRIPT PATH. Its default used to
    # be `viz/manuscript.html`, where the PAPER lives; running it replaced the paper with a protocol
    # rendering and nothing noticed, because both files were called "the manuscript".
    ap.add_argument("--out", default="viz/protocol_v1.html")
    args = ap.parse_args()

    if not ANCHOR.is_file():
        raise SystemExit(f"anchor missing: {ANCHOR}")
    raw = ANCHOR.read_text(encoding="utf-8")
    digest = hashlib.sha256(ANCHOR.read_bytes()).hexdigest()

    ver = re.search(r"\*\*Version:\*\*\s*([0-9.]+)", raw)
    ver = ver.group(1) if ver else "?"
    title_m = re.search(r"^#\s+(.+)$", raw, re.M)
    title = title_m.group(1).strip() if title_m else ANCHOR.stem
    subtitle_m = re.search(r"^##\s+(.+)$", raw, re.M)
    subtitle = subtitle_m.group(1).strip() if subtitle_m else ""

    katex_src = find_katex()
    out_dir = OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    katex_ver = copy_katex(katex_src, out_dir / "katex")
    (out_dir / "protocol.md").write_text(raw, encoding="utf-8", newline="\n")

    body = md_to_html(strip_anchor_banner(raw))

    stamp = (
        "GENERATED FILE — DO NOT EDIT.  Source of truth: "
        f"protocol/{ANCHOR.name}  v{ver}  sha256 {digest}  "
        f"({len(raw.splitlines())} lines, {len(raw)} chars).  "
        f"Built {datetime.datetime.now():%Y-%m-%d %H:%M}.  "
        "Rebuild with: python scripts/build_manuscript_html.py"
    )

    html = HTML.format(title=title, subtitle=subtitle, stamp=stamp, body=body, css=CSS,
                       katex_version=katex_ver)
    out = ROOT / args.out
    # A hard refusal, because a changed default only protects the people who do not pass --out.
    if out.resolve() in {(ROOT / "viz" / "manuscript.html").resolve(),
                         (ROOT / "viz" / "manuscript.pdf").resolve()}:
        print("REFUSING: viz/manuscript.html is produced by build_paper_html.py from docs/PAPER.md.")
        print("This script renders the protocol; write it to a protocol path.")
        return 2
    out.write_text(html, encoding="utf-8", newline="\n")

    n_display = raw.count("$$") // 2
    n_inline = len(re.findall(r"(?<!\$)\$(?!\$)", raw)) - 2 * n_display
    print(f"  anchor    : {ANCHOR.relative_to(ROOT)}  v{ver}")
    print(f"  sha256    : {digest}")
    print(f"  katex     : {katex_ver}  (copied from {katex_src})")
    print(f"  markdown  : {len(raw.splitlines())} lines -> HTML")
    print(f"  math      : {n_display} display + ~{max(n_inline,0)} inline expressions")
    print(f"  output    : {out.relative_to(ROOT)}  ({out.stat().st_size:,} B)")
    print(f"  assets    : viz/katex/  ({sum(1 for _ in (out_dir/'katex').rglob('*') if _.is_file())} files)")
    print(f"  source    : viz/protocol.md  (the exact bytes the build read)")
    print("\n  Open viz/manuscript.html — maths renders offline, with no network request.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())