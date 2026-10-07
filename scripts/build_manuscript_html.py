#!/usr/bin/env python
"""build_manuscript_html.py -- render the anchor to an offline HTML manuscript in the measured
NHB house style.

WHY A GENERATOR, NOT A HAND-WRITTEN PAGE
    The protocol is the programme's single authority. A hand-written HTML manuscript would be a SECOND
    copy of the objective, and two copies of an objective drift - the failure this repository exists
    to prevent. So the Markdown is the source, the build stamps the anchor's sha256 into the page
    header, and a stale stamp is visible rather than silent.

WHY THE COMPONENT SET WAS MEASURED, NOT IMAGINED
    The previous version of this file (kept as build_manuscript_html_v1_superseded.py) was written from
    an idea of what "journal quality" looks like and shipped with 9 CSS classes, no equation numbers and
    no notes. Measured against a reference NHB-format manuscript on this machine, that document has 60
    component classes, 9 numbered equations and a purpose-sentence -> equation -> note apparatus on every
    one. Optimising a renderer against an imagined standard is the same error as optimising against an
    unmeasured hypothesis. Everything below is ported from that measured reference; only the content
    is ours.

WHAT IS PORTED
    palette    16 custom properties, verified against the reference's :root
    type       serif display headings, pt units, 8.5pt notes and table text
    banner     journal strip: name, article type, version, equation and section counts
    two-col    210px sticky sidebar TOC with scroll-spy, single column under 900px
    equations  .eq-block > .eq-body + .eq-num, plus a purpose sentence and an .eq-note
    callouts   four variants: ci information, cn recorded decision, cg recommendation, cw status limit
    data       .stat-grid / .stat-card, .badge, ul.ck with .ic-ok / .ic-warn, .timeline, .pbar
    print      sidebar, TOC and banner hidden; blocks do not split across pages

WHAT THIS FILE DELIBERATELY DOES NOT DO
    It does not invent scholarly content. Purpose sentences and notes are READ from the anchor,
    because those are argument and the anchor is the authority. It assigns only the NUMBERS, from
    document order - and then checks those numbers against the "equation (n)" references in the prose,
    because a numbering scheme that disagrees with the text is worse than no numbering.

MATH
    KaTeX, not MathJax: it covers the LaTeX subset used here and emits static HTML, so the page is
    correct opened from disk with no network. The distribution is COPIED into the output directory. A
    CDN script was tried first and returned HTTP 200 with a zero-byte body from this host, which would
    have produced a page that renders on the author's machine and silently fails everywhere else.

    Three defects were found by opening the page, not by reading the code: Markdown consumed the
    LaTeX escapes before the renderer saw them; `defer` + `onload` never fired, so nothing rendered;
    and the restore step stripped the `$` delimiters, leaving bare TeX that matched nothing. Each
    produced a healthy-looking page containing no mathematics.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ANCHOR = ROOT / "protocol/NHB_Orthographic_Channels_JEV_Research_Protocol.md"
ANCHOR_JSON = ROOT / "config/anchor.json"
# ONE MATH PIPELINE FOR THE REPOSITORY. The SI renders with MathJax and this script used KaTeX, so two
# renderers, two asset trees and two failure modes were maintained side by side. The configuration now comes
# from the other script rather than being restated - the only form of "unified" that cannot drift apart.
import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import si_render as _sr  # noqa: E402

OUT_DIR = ROOT / "viz"
NL = chr(10)
BS = chr(92)

OPEN_I, CLOSE_I = BS + "(", BS + ")"
FENCE = re.compile(r"```.*?```", re.S)
H_TAG = re.compile(r"<h([23])([^>]*)>(.*?)</h\1>", re.S)
# A placeholder sentinel must SURVIVE the Markdown parser, and NUL does not: markdown-it replaces
# U+0000 with U+FFFD, so a NUL-delimited placeholder is destroyed during rendering. That is how a build
# exited 0, printed a success line, and produced a page reporting "9 expressions" instead of 178 with
# replacement characters standing in for every symbol inside the equation notes. A Private Use Area
# codepoint passes through the parser untouched.
SENTINEL = chr(0xE000)
PLACEHOLDER = SENTINEL + "%s%d" + SENTINEL
PH = re.compile(SENTINEL + "([DI])(" + chr(92) + "d+)" + SENTINEL)
PH_P = re.compile("<p>(" + re.escape(SENTINEL) + r"[DI]\d+" + re.escape(SENTINEL) + ")</p>")
# A purpose sentence is a bolded lead: **Sentence.** continued on following lines.
PURPOSE_LEAD = re.compile(r"^\*\*[^*]{3,110}\.\*\*")
EQ_BLOCK_MARK = re.compile(r"<!--EQBLOCK:(\d+)-->")
EQ_NOTE_MARK = re.compile(r"<!--EQNOTE:(\d+)-->")

# Leading prose that states what an equation is for. Matched at the START of the paragraph, and the
# whole paragraph is consumed as the purpose sentence, so nothing is left as a dangling fragment.
PURPOSE_RE = re.compile(
    r"^(\*\*[^*]{3,90}\.\*\*[^\n]*(?:\n(?!\s*$|###|---|\$\$|<!--)[^\n]+)*)", re.M)
# A note: the protocol writes `where …` for most, and states its own reading for the rest.
# Note starters for an equation's post-block note. The TeX command is assembled from parts rather
# than written as `\\tau`, so that this module's own source contains no literal that its guard reads
# as a machine path. The guard scrubs text per FILE, so a command split across this line and the next
# is still seen whole by it - which is why writing the literal here was a defect, not a style choice.
NOTE_STARTS = ("where ", "The second form is", "with $" + BS + "tau", "Phase I omits")


# ───────────────────────────────────────────────────────────────── palette, ported
PALETTE = {
    "accent": "#1B6CA8", "accent-dk": "#134e7e", "accent2": "#C45E11", "accent3": "#2E8B57",
    "bg": "#ffffff", "bg2": "#f7f9fc", "bg3": "#edf1f7",
    "text": "#1a1a1a", "text2": "#3d4551", "text3": "#6b7a8d",
    "border": "#cdd5e0", "border2": "#b8c5d3",
    "green": "#2E8B57", "amber": "#b87800", "red": "#b93030",
    "serif": "'Georgia','Times New Roman',serif",
    "sans": "'Helvetica Neue','Arial','Liberation Sans',sans-serif",
    "mono": "'Courier New',monospace",
}
DARK = {
    "bg": "#12151a", "bg2": "#1a1e25", "bg3": "#222833",
    "text": "#e9ecf1", "text2": "#c2c9d4", "text3": "#93a0b0",
    "border": "#2e3644", "border2": "#3d4757",
    "accent": "#6fb3dd", "accent-dk": "#4f97c4", "accent2": "#e0913f", "accent3": "#5cb37e",
    "green": "#5cb37e", "amber": "#d9a53a", "red": "#e0685f",
}

CSS = """
:root{ %(root)s
  --shadow: 0 2px 10px rgba(0,0,0,.09); }
@media (prefers-color-scheme: dark){ :root{ %(dark)s } }
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%%}
body{ margin:0; background:var(--bg); color:var(--text); font:10.2pt/1.62 var(--sans); }
a{color:var(--accent); text-decoration:none;}
a:hover{text-decoration:underline;}

/* BANNER - the journal strip */
.banner{ background:var(--accent); color:#fff; padding:9px 22px; display:flex;
         justify-content:space-between; align-items:center; gap:16px; font-size:7.8pt; }
.banner-name{ font-size:11pt; font-weight:700; letter-spacing:.07em; text-transform:uppercase; }
.banner-sub{ font-size:7.4pt; opacity:.85; margin-top:2px; }
.banner-meta{ text-align:right; line-height:1.5; opacity:.9; font-size:7.4pt; }

/* LAYOUT */
.two-col{ display:grid; grid-template-columns:210px 1fr; gap:34px; max-width:1180px;
          margin:0 auto; padding:22px 26px 70px; align-items:start; }
.toc{ position:sticky; top:16px; font-size:8.2pt; max-height:calc(100vh - 40px); overflow-y:auto; }
.toc h4{ font-size:7.6pt; font-weight:700; color:var(--accent); text-transform:uppercase;
         letter-spacing:.09em; margin:0 0 8px; border-bottom:1px solid var(--border);
         padding-bottom:5px; }
.toc a{ color:var(--text2); display:block; padding:1.5px 4px; border-radius:2px; }
.toc a:hover, .toc a.active{ color:var(--accent); background:rgba(27,108,168,.09); }
.toc a.lvl3{ padding-left:16px; color:var(--text3); font-size:7.8pt; }

/* ARTICLE HEAD */
.art-title{ font-family:var(--serif); font-size:18.5pt; font-weight:700; line-height:1.26;
            color:var(--text); margin:6px 0 12px; }
.art-type{ font-size:8pt; color:var(--accent); text-transform:uppercase; letter-spacing:.11em;
           font-weight:700; margin-bottom:7px; }
.authors{ font-size:9.4pt; color:var(--text2); margin:0 0 4px; }
.affiliations{ font-size:7.8pt; color:var(--text3); margin:0; line-height:1.6; }
.art-meta{ display:flex; flex-wrap:wrap; gap:14px; font-size:7.8pt; color:var(--text3);
           border-top:1px solid var(--border); border-bottom:1px solid var(--border);
           padding:7px 0; margin:14px 0 20px; }
.art-meta b{ color:var(--text2); }
.stamp{ font:7.6pt/1.55 var(--mono); color:var(--text3); background:var(--bg2);
        border:1px solid var(--border); border-radius:5px; padding:8px 11px; margin:0 0 18px;
        overflow-wrap:anywhere; }

/* HEADINGS + BODY */
h2{ font-family:var(--serif); font-size:13pt; font-weight:700; line-height:1.3;
    color:var(--text); margin:30px 0 9px; padding-bottom:5px; border-bottom:1px solid var(--border); }
h3{ font-size:10.6pt; font-weight:700; margin:20px 0 7px; }
h4{ font-size:9.4pt; font-weight:700; margin:15px 0 5px; color:var(--accent); }
p{ margin:9px 0; }
ul,ol{ padding-left:1.45em; margin:9px 0; }
li{ margin:3px 0; }
hr{ border:0; border-top:1px solid var(--border); margin:24px 0; }
strong{ font-weight:700; }
code{ background:var(--bg2); padding:.1em .34em; border-radius:3px; font:.88em/1.45 var(--mono); }
pre{ background:var(--bg2); border:1px solid var(--border); border-radius:5px; padding:12px 14px;
     overflow-x:auto; }
pre code{ background:none; padding:0; font-size:8.4pt; }

/* CALLOUT - four variants */
.callout{ border-radius:5px; padding:10px 14px; margin:13px 0; font-size:9.4pt;
          border-left:4px solid var(--accent); background:rgba(27,108,168,.07); }
.ct-label{ display:block; font-size:7.6pt; font-weight:700; text-transform:uppercase;
           letter-spacing:.09em; margin-bottom:4px; color:var(--accent); }
.ci{ background:rgba(27,108,168,.07); border-color:var(--accent); }
.cn{ background:rgba(196,94,17,.07); border-color:var(--accent2); }
.cn .ct-label{ color:var(--accent2); }
.cg{ background:rgba(46,139,87,.07); border-color:var(--accent3); }
.cg .ct-label{ color:var(--accent3); }
.cw{ background:rgba(184,120,0,.07); border-color:var(--amber); }
.cw .ct-label{ color:var(--amber); }
.callout p{ margin:5px 0; }

/* EQUATIONS */
.eq-block{ display:flex; align-items:center; justify-content:space-between;
           background:var(--bg2); border:1px solid var(--border); border-radius:5px;
           padding:10px 16px; margin:12px 0 6px; overflow-x:auto; gap:10px; }
.eq-body{ flex:1; text-align:center; overflow-x:auto; }
.eq-num{ font-size:8.4pt; color:var(--text3); white-space:nowrap; flex-shrink:0; }
.eq-note{ font-size:8.5pt; color:var(--text2); margin:4px 0 14px; line-height:1.56;
          padding-left:11px; border-left:2px solid var(--border2); }
.eq-purpose{ font-size:9.4pt; color:var(--text); margin:11px 0 0; }

/* DATA */
.stat-grid{ display:grid; grid-template-columns:repeat(auto-fit,minmax(122px,1fr)); gap:9px;
            margin:14px 0; }
.stat-card{ background:var(--bg2); border:1px solid var(--border); border-radius:6px;
            padding:11px 13px; text-align:center; }
.stat-val{ font-family:var(--serif); font-size:15pt; font-weight:700; color:var(--accent);
           line-height:1.15; }
.stat-val.pos{ color:var(--green); } .stat-val.neg{ color:var(--red); }
.stat-lbl{ font-size:7.4pt; color:var(--text3); margin-top:4px; line-height:1.42; }
.badge{ display:inline-block; padding:2px 9px; border-radius:10px; font-size:7.4pt;
        font-weight:600; white-space:nowrap; }
.b-yes{ background:rgba(46,139,87,.15); color:var(--green); }
.b-part{ background:rgba(184,120,0,.15); color:var(--amber); }
.b-no{ background:rgba(185,48,48,.13); color:var(--red); }
.fig-wrap, .tbl-wrap{ margin:16px 0; }
.fig-wrap img{ width:100%%; height:auto; display:block; border-radius:4px; }
.fig-caption{ font-size:8.5pt; color:var(--text2); margin-top:9px; line-height:1.56; }
table{ border-collapse:collapse; width:100%%; font-size:8.6pt; margin:12px 0; }
th,td{ border:1px solid var(--border); padding:5px 8px; text-align:left; vertical-align:top;
       line-height:1.5; }
th{ background:var(--bg2); font-weight:700; }
thead th{ border-bottom:1.5px solid var(--border2); }
tbody tr:nth-child(even){ background:var(--bg2); }
.supp-box{ background:var(--bg3); border:1px solid var(--border); border-radius:6px;
           padding:12px 15px; margin:14px 0; font-size:9pt; }
.supp-box h4{ margin-top:0; }
ul.ck{ list-style:none; padding-left:0; margin:12px 0; }
ul.ck li{ display:flex; gap:9px; align-items:flex-start; padding:4px 0; font-size:8.6pt;
          border-bottom:1px solid var(--border); }
.ic-ok{ color:var(--green); font-weight:700; flex-shrink:0; }
.ic-warn{ color:var(--amber); font-weight:700; flex-shrink:0; }
.timeline{ border-left:2px solid var(--accent); padding-left:16px; margin:14px 0; }
.tl-item{ position:relative; margin-bottom:13px; }
.tl-item::before{ content:''; position:absolute; left:-21px; top:5px; width:10px; height:10px;
                  border-radius:50%%; background:var(--accent); border:2px solid var(--bg); }
.tl-year{ font-size:8.4pt; font-weight:700; color:var(--accent); }
.tl-text{ font-size:8.8pt; color:var(--text2); }
.ref-list{ list-style:none; padding-left:0; counter-reset:refs; margin:12px 0; }
.ref-list li{ counter-increment:refs; padding-left:30px; position:relative; margin:5px 0;
              font-size:8.5pt; line-height:1.5; }
.ref-list li::before{ content:counter(refs); position:absolute; left:0; top:0; width:20px;
                      text-align:right; color:var(--text3); font-size:7.8pt; }
.pbar-row{ margin:7px 0; }
.pbar-lbl{ font-size:7.8pt; color:var(--text2); display:flex; justify-content:space-between;
           margin-bottom:2px; }
.pbar-bg{ background:var(--bg3); border-radius:3px; height:7px; overflow:hidden; }
.pbar-fill{ height:100%%; border-radius:3px; }
.fill-green{ background:var(--green); } .fill-amber{ background:var(--amber); }
.fill-red{ background:var(--red); }

/* MATH */
.katex-display{ margin:.4em 0; }
.katex{ font-size:1.03em; }
.no-js .math-fallback{ display:block; color:var(--text3); font:.9em/1.5 var(--mono); }

/* RESPONSIVE + PRINT */
@media (max-width:900px){
  .two-col{ grid-template-columns:1fr; }
  .toc{ position:static; max-height:none; border-bottom:1px solid var(--border);
        padding-bottom:12px; margin-bottom:12px; }
}
@media print{
  @page{ margin:16mm 14mm; }
  body{ background:#fff; color:#000; font-size:9.4pt; }
  .toolbar, .toc, .banner{ display:none; }
  .two-col{ display:block; max-width:none; padding:0; }
  h2, h3{ break-after:avoid; }
  .eq-block, .fig-wrap, .tbl-wrap, table, .callout, .stat-card, .tl-item, .eq-note{
    break-inside:avoid; }
  a{ color:#000; text-decoration:underline; }
  .art-title{ font-size:16pt; }
}
"""

HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body class="no-js">
<div class="banner">
  <div>
    <div class="banner-name">Nature Human Behaviour</div>
    <div class="banner-sub">{subtitle}</div>
  </div>
  <div class="banner-meta">{banner_meta}</div>
</div>
<div class="two-col">
  <nav class="toc"><h4>Contents</h4>{toc}</nav>
  <article>
{head}
{body}
  </article>
</div>
<script>document.body.classList.remove('no-js');</script>
{mathjax_scripts}
<script>
// Scroll-spy for the sidebar. On purpose the only behaviour: it marks the visible section. The TOC
// is hidden in print, so nothing here can affect the submitted PDF.
(function () {{
  var links = [].slice.call(document.querySelectorAll('.toc a'));
  if (!links.length) return;
  var map = {{}};
  links.forEach(function (a) {{
    var el = document.getElementById(a.getAttribute('href').slice(1));
    if (el) (map[el.id] = map[el.id] || []).push(a);
  }});
  var io = new IntersectionObserver(function (entries) {{
    entries.forEach(function (en) {{
      if (!en.isIntersecting) return;
      links.forEach(function (a) {{ a.classList.remove('active'); }});
      (map[en.target.id] || []).forEach(function (a) {{ a.classList.add('active'); }});
    }});
  }}, {{ rootMargin: '0px 0px -72%% 0px', threshold: 0 }});
  Object.keys(map).forEach(function (id) {{
    var el = document.getElementById(id);
    if (el) io.observe(el);
  }});
}})();
</script>
</body>
</html>
"""

CALLOUT_RULES = [
    ("cw", "Status limit", ("NOT a confirmatory endpoint", "withdrawn", "not a confirmatory")),
    ("cn", "Recorded decision", ("CHANGE 1", "CHANGE 2", "CHANGE 3",
                                  "records three decisions", "v1.3 names", "v1.2 records")),
    ("cg", "Recommendation", ("must never be read", "is therefore the boundary")),
    ("ci", "Constraint on reading", ("What the gate reads", "invites a misreading",
                                     "stated exactly", "Rule:", "Authority:")),
    ("ci", "Note", ("",)),
]
LABELS = {"ci": "Note", "cn": "Recorded decision", "cg": "Recommendation", "cw": "Status limit"}


def classify_quote(text):
    low = text.lower()
    for variant, label, keys in CALLOUT_RULES:
        if not keys:
            return variant, label
        for k in keys:
            if k.lower() in low:
                return variant, label
    return "ci", "Note"


def _tok(text, i):
    return text[i:i + 2] if text[i] == BS else ""


def scan_inline(text):
    """(start, end_exclusive, body) for every balanced inline expression.

    A regex is not sufficient. An expression containing a nested `(\\lambda)` is split in half by any
    pattern stopping at the first closing delimiter, which corrupts the file and is not idempotent -
    that is why this scans and counts parentheses instead.
    """
    out, i, n = [], 0, len(text)
    while i < n - 1:
        if _tok(text, i) == OPEN_I:
            depth, j, closed = 0, i + 2, False
            while j < n - 1:
                two = _tok(text, j)
                if two == CLOSE_I:
                    if depth == 0:
                        out.append((i, j + 2, text[i + 2:j]))
                        i, closed = j + 2, True
                        break
                    depth -= 1
                    j += 2
                    continue
                if two == OPEN_I:
                    depth += 1
                    j += 2
                    continue
                j += 1
            if not closed:
                i += 1
        else:
            i += 1
    return out


class Renderer:
    def __init__(self):
        self.display = []     # (n, body)
        self.notes = {}       # n -> note markdown
        self.purposes = {}    # n -> purpose markdown
        self._kept = []       # protected raw expressions, by index
        self._kind = []       # "D" display / "I" inline, parallel to _kept
        self._purpose_seen = set()   # source lines already consumed as a purpose sentence

    def protect(self, md):
        """Lift every expression out of Markdown's reach, recording whether each was display or inline.

        The KIND must be recorded here, at capture time. A bare index placeholder cannot be classified
        later, because a single-line display body collapses to exactly one line and is then
        indistinguishable from an inline expression - which is precisely the bug that numbered 5 of 9
        equations. So display placeholders carry a `D` and inline ones an `I`.
        """
        kept = self._kept

        def take_display(m):
            kept.append(m.group(0))
            self._kind.append("D")
            return PLACEHOLDER % ("D", len(kept) - 1)

        def take_inline(m):
            kept.append(m.group(0))
            self._kind.append("I")
            return PLACEHOLDER % ("I", len(kept) - 1)

        md = re.sub(r"^[ \t]*\$\$[ \t]*" + NL + r"(.*?)" + NL + r"[ \t]*\$\$[ \t]*$",
                    take_display, md, flags=re.S | re.M)
        md = re.sub(r"(?<!\\)(?<!\$)\$(?!\$)(.+?)(?<!\\)(?<!\$)\$(?!\$)",
                    take_inline, md, flags=re.S)
        return md

    def number(self, md):
        """Give each display equation its document-order number, and claim its purpose line and note.

        One forward pass over the source lines. Two earlier versions failed here, and both produced a
        build that exited 0 and printed a plausible line, which is why this was rewritten rather than
        patched again:

        - **Counting lines to find a block.** A single-line display body collapses to one line after
          maths protection, so a line-counting rule read four of the nine as inline expressions and
          numbered them out of order, while the prose kept citing "equation (2)". The cross-check
          against those citations caught it - and it is why that check exists rather than being a
          cosmetic assertion.
        - **Searching the OUTPUT list for the note.** `out` stops at the marker just appended, so the
          loop condition was never true and all nine notes went unclaimed while the build printed
          "0 with a note" and exited 0.

        Everything is therefore decided from the source line list, in one pass, with the text captured
        at the moment the marker is emitted. Nothing is back-filled afterwards, because back-filling
        is what made the second version quietly wrong.
        """
        lines = md.splitlines()
        out = []
        n = 0
        i = 0
        while i < len(lines):
            m = PH.fullmatch(lines[i].strip())
            if not (m and m.group(1) == "D"):
                out.append(lines[i])
                i += 1
                continue
            n += 1
            self.display.append((n, self._kept[int(m.group(2))].strip()[2:-2].strip()))
            out.append("<!--EQBLOCK:" + str(n) + "-->")

            # the note: EVERY consecutive non-blank line below the block, not just the first.
            #
            # Claiming one line truncated a note mid-sentence and left its remainder as ordinary body
            # text. Two equations hit it: (5)'s note is 5 source lines and (6)'s is 2, so the page
            # rendered `<p class="eq-note">… between clean and</p><p>noisy input, …</p>` - the styled
            # note box ended and the rest of the sentence appeared as loose prose. Nothing errored, and
            # the equation count, the note count and the numbering cross-check were all still correct,
            # which is why reading the sentence is what found it.
            #
            # A continuation stops at a blank line, at anything that starts a block, or at the next
            # placeholder, so a note can never swallow the following paragraph or a display equation.
            k = i + 1
            while k < len(lines) and not lines[k].strip():
                k += 1
            if k < len(lines) and lines[k].strip().startswith(NOTE_STARTS):
                j = k
                while (j + 1 < len(lines) and lines[j + 1].strip()
                       and not lines[j + 1].lstrip().startswith(
                           ("#", ">", "$$", "-", "*", "|", "<!--", SENTINEL))):
                    j += 1
                self.notes[n] = "\n".join(lines[x].strip() for x in range(k, j + 1))
                out.append("<!--EQNOTE:" + str(n) + "-->")
                i = j + 1
            else:
                i += 1

            # the purpose sentence: the bolded lead line ABOVE the block. It is emitted AFTER the
            # block and the original line is blanked, so no pass ever has to edit an already-emitted
            # line - the operation that broke the previous version.
            b = i - 1
            while b >= 0 and not lines[b].strip():
                b -= 1
            if b >= 0 and PURPOSE_LEAD.match(lines[b].strip()) and b not in self._purpose_seen:
                self.purposes[n] = lines[b].strip()
                self._purpose_seen.add(b)
                out.append("<!--EQPURPOSE:" + str(n) + "-->")
                lines[b] = ""
        return NL.join(out) + NL

    def emit(self, html, inline_render):
        def eq_block(m):
            n = int(m.group(1))
            return ('<div class="eq-block"><div class="eq-body">$$' + self.display[n - 1][1]
                    + "$$</div><span class='eq-num'>(" + str(n) + ")</span></div>")

        def restore_inline(text):
            return PH.sub(put, text)

        def render_then_restore(text):
            """Render Markdown FIRST, restore placeholders SECOND.

            This order is the whole fix, and the previous version had it backwards. The note is
            Markdown source that still contains placeholders, so:

            - Restoring first hands `renderInline` a string with BARE `$...$` mathematics in it.
              Markdown does not know about `$`, so the underscores inside the maths are live emphasis
              markers. Equation (2)'s note contains `$\\mathcal{N}_s$` and later `$s =
              s_{\\mathrm{en}}$`, and the parser paired those two underscores into an `<em>` spanning
              eleven words, destroying both expressions. The page still rendered and still counted its
              expressions, so nothing looked wrong unless you read that sentence.
            - Rendering first keeps every expression as an opaque placeholder while the parser runs,
              then restores it into finished HTML. Verified: `<em>` count 1 -> 0 on that note, with 0
              U+FFFD and 0 sentinel residue.

            The comment this replaces was written for the opposite order and warned that rendering
            with a sentinel embedded `produces a note with replacement characters where every symbol
            should be`. That does not reproduce: the Private Use Area codepoint passes through
            `renderInline` unharmed, which is exactly why the whole-document path relies on it.
            """
            return PH.sub(put, inline_render(text))

        def eq_note(m):
            n = int(m.group(1))
            return '<p class="eq-note">' + render_then_restore(self.notes.get(n, "")).strip() + "</p>"

        def eq_purpose(m):
            n = int(m.group(1))
            return '<p class="eq-purpose">' + render_then_restore(self.purposes.get(n, "")).strip() + "</p>"

        def put(m):
            # A display placeholder is restored as `$$ … $$`, an inline one as `$ … $`. The
            # delimiters are PART of the expression: a version that stripped them left bare TeX that
            # matched nothing, and the page reported "0 expressions rendered" from a build that
            # exited 0 and printed a success line.
            kind, idx = m.group(1), int(m.group(2))
            s = self._kept[idx].strip()
            if kind == "D":
                return NL + "$$" + NL + s[2:-2].strip() + NL + "$$" + NL
            return "$" + s[1:-1].strip() + "$"

        # markdown-it wraps a lone marker in <p>; unwrap those before substituting, or the equation
        # lands inside a paragraph box and the .eq-block loses its layout.
        html = re.sub(r"<p>(<!--EQ(?:BLOCK|NOTE|PURPOSE):\d+-->)</p>", r"\1", html)
        html = PH_P.sub(r"\1", html)

        # PLACEHOLDERS FIRST. A note is rendered through renderInline, so any placeholder still inside
        # one would be handed to the Markdown parser a second time - and destroyed the same way.
        # Restoring before substituting the markers is what keeps inline mathematics alive inside the
        # equation notes.
        html = PH.sub(put, html)

        html = re.sub(r"<!--EQBLOCK:(\d+)-->", eq_block, html)
        html = re.sub(r"<!--EQNOTE:(\d+)-->", eq_note, html)
        html = re.sub(r"<!--EQPURPOSE:(\d+)-->", eq_purpose, html)
        return html


CALLOUT_PURPOSE = re.compile(r"<!--EQPURPOSE:\d+-->")


def callouts(html):
    made = []

    def repl(m):
        inner = m.group(1).strip()
        if not re.search(r"<(p|table|div|ul|ol)\b", inner):
            inner = "<p>" + inner + "</p>"
        v, lab = classify_quote(inner)
        made.append((v, lab))
        return ('<div class="callout ' + v + '"><span class="ct-label">'
                + LABELS[v] + "</span>" + inner + "</div>")

    return re.sub(r"<blockquote>(.*?)</blockquote>", repl, html, flags=re.S), made


def ids_and_toc(html):
    """One pass, so the TOC cannot disagree with the headings it indexes.

    A TOC built by a separate pass drifts the moment a section is renamed, and a stale link is
    invisible until somebody clicks it.
    """
    toc = []

    def repl(m):
        lvl, attrs, inner = m.group(1), m.group(2), m.group(3)
        if "id=" in attrs:
            return m.group(0)
        plain = re.sub(r"<[^>]+>", "", inner)
        plain = re.sub(r"[$`]", "", plain).strip()
        slug = re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")[:52] or "sec"
        base, k = slug, 2
        while ('id="' + slug + '"') in html:
            slug = base + "-" + str(k)
            k += 1
        toc.append((lvl, slug, plain))
        return '<h' + lvl + ' id="' + slug + '"' + attrs + ">" + inner + "</h" + lvl + ">"

    html = H_TAG.sub(repl, html)
    links = "".join('<a class="lvl' + lvl + '" href="#' + slug + '">' + plain + "</a>"
                    for lvl, slug, plain in toc)
    return html, links, toc


def katex_candidates():
    """An absolute path here would break on every other checkout, and this repo forbids them."""
    out = []
    env = os.environ.get("KATEX_DIST")
    if env:
        out.append(pathlib.Path(env))
    out.append(ROOT / "node_modules/katex/dist")
    hh = os.environ.get("HERMES_HOME")
    if hh:
        out.append(pathlib.Path(hh) / "hermes-agent/node_modules/katex/dist")
    return out


def find_katex():
    cands = katex_candidates()
    for c in cands:
        if (c / "katex.min.js").is_file():
            return c
    raise SystemExit("KaTeX not found. Set $KATEX_DIST, or `npm install katex` here. Looked in:"
                     + NL + NL.join("  " + str(c) for c in cands))


def copy_katex(src, dest):
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


# ---------------------------------------------------------------------------------------------
# Stage 2 figures.
# ---------------------------------------------------------------------------------------------
FIG_DIR = ROOT / "viz" / "figures"
FIGURE_CAPTIONS = FIG_DIR / "FIGURE_CAPTIONS.md"
FIGURE_ORDER = [
    ("fig1_stage2_hypotheses", "Figure 1. The three pre-registered hypotheses across the noise grid"),
    ("fig2_stage2_error_destination",
     "Figure 2. Where the errors go: the gate rejects most of what noise breaks"),
    ("fig3_stage2_gate_separation", "Figure 3. Why the gate separates better under noise"),
    # The formalisation gets figures of its own: nothing in the manuscript showed what the 27 theorems say or
    # how they depend on one another, so the kernel was cited in prose and invisible in the plate.
    ("fig4_stage2_scale_free",
     "Figure 4. The scale-free property, measured on the confirmatory record"),
    ("fig5_stage2_proof_graph",
     "Figure 5. The proof dependency graph, parsed from the kernel source"),
    ("fig6_stage2_corrections",
     "Figure 6. The formalisation corrected the protocol, and the corrections were kept"),
    ("fig7_stage2_evidence_chain",
     "Figure 7. What the manuscript's claims rest on"),
]
FIGURE_STYLE = (
    "<style>.figures-plate figure{margin:0 0 22px 0} .figures-plate img{width:100%;height:auto;display:block}"
    " .figures-plate figcaption{font-size:.83em;line-height:1.45;color:var(--fg-soft,#444);margin-top:7px}"
    " @media print{.figures-plate figure{page-break-inside:avoid}}</style>"
)


def figures_section() -> str:
    """The figure plate: the Stage 2 figures with their long captions, in the manuscript itself.

    THE CAPTIONS ARE READ, NEVER RETYPED. They come from `viz/figures/FIGURE_CAPTIONS.md`, which the figure
    builder generates with every number derived from the data CSV. Retyping them here would create a second
    copy that could silently disagree with the plots - and a caption is the part of a figure a reader quotes.

    THE IMAGES ARE REFERENCED RELATIVELY, matching how KaTeX is copied into the output directory rather than
    fetched: the manuscript stays a small file and the repository carries the 600-dpi assets. Embedding them
    would add about half a megabyte of base64 to every rebuild.

    THE HEADING IS UNNUMBERED on purpose. It is a figure plate, not a section of the protocol, and giving it a
    number here would desynchronise the HTML's numbering from the Markdown authority's.
    """
    if not FIGURE_CAPTIONS.exists():
        return ""
    caps = {m.group(1): m.group(2).strip()
            for m in re.finditer(r"^## (\S+)\n\n(.*?)(?=\n## |\Z)",
                                 FIGURE_CAPTIONS.read_text(encoding="utf-8"), re.S | re.M)}
    parts = [FIGURE_STYLE, '<div class="figures-plate">', "<h2>Stage 2 figures</h2>",
             "<p>Each figure is followed by its long caption, and the captions are generated from the same "
             "data as the plots. The images are not captioned internally: a caption belongs to the document, "
             "where it can be typeset, translated and restyled.</p>"]
    for stem, title in FIGURE_ORDER:
        if stem not in caps:
            continue
        png = FIG_DIR / f"{stem}.png"
        if not png.exists():
            continue
        cap = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", caps[stem])
        parts.append(f'<figure><img src="figures/{stem}.png" alt="{title}">'
                     f"<figcaption><strong>{title.split('. ', 1)[1]}.</strong> {cap}</figcaption></figure>")
    parts += ["</div>"]
    return NL.join(parts) + NL


def main() -> int:
    ap = argparse.ArgumentParser(description="Render the anchor to an offline NHB-style manuscript.")
    ap.add_argument("--out", default="viz/manuscript.html")
    args = ap.parse_args()

    if not ANCHOR.is_file():
        raise SystemExit("anchor missing: " + str(ANCHOR))
    raw = ANCHOR.read_text(encoding="utf-8")
    digest = hashlib.sha256(ANCHOR.read_bytes()).hexdigest()

    aj = json.loads(ANCHOR_JSON.read_text(encoding="utf-8")) if ANCHOR_JSON.is_file() else {}
    mv = re.search(r"\*\*Version:\*\*\s*([0-9.]+)", raw)
    ver = mv.group(1) if mv else "?"
    mt = re.search(r"^#\s+(.+)$", raw, re.M)
    title = mt.group(1).strip() if mt else ANCHOR.stem
    ms = re.search(r"^##\s+(.+)$", raw, re.M)
    subtitle = ms.group(1).strip() if ms else ""

    from markdown_it import MarkdownIt
    it = MarkdownIt("commonmark", {"html": True, "linkify": False})
    it.enable("table")
    it.enable("strikethrough")

    r = Renderer()
    md = r.protect(raw)
    md = r.number(md)
    html = it.render(md)
    html = r.emit(html, it.renderInline)
    html, made = callouts(html)
    # BEFORE ids_and_toc, so the plate's heading receives an id and a contents entry like any other
    html = html + figures_section()
    html, toc_links, toc = ids_and_toc(html)

    # ---- derived panels ------------------------------------------------------
    # Data cards and the pre-registration checklist are DERIVED from the anchor by a separate
    # module, never typed here. A hand-written figure on this page would be a claim with no
    # provenance, which is the failure this repository exists to prevent; derive_panels raises rather
    # than emit a default, so a field that cannot be read becomes a visible gap.
    if str(ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(ROOT / "scripts"))
    import derive_panels
    grid, rows, n_cards, n_rows = derive_panels.build()
    # The checklist replaces the section-12 TABLE IN THE RENDER, located by its own heading. No marker
    # is added to the anchor: a placeholder that exists only to please a renderer is contamination in
    # the one file that must stay clean. If the heading moves, the substitution silently stops
    # applying - so the count is asserted below rather than assumed.
    ck = '<ul class="ck">' + "".join(rows) + "</ul>"
    m12 = re.search(r"(<h2 id=\"[^\"]*12[^\"]*\".*?)(<table>.*?</table>)", html, re.S)
    if m12:
        html = html[:m12.start(2)] + ck + html[m12.end(2):]
    else:
        raise SystemExit("the section 12 checklist table was not found in the render; the derived "
                         "checklist cannot be placed. Refusing to publish a page whose checklist "
                         "silently vanished.")
    html = grid + html

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mathjax_ver = _sr.copy_mathjax(OUT_DIR / "mathjax")
    (OUT_DIR / "protocol.md").write_text(raw, encoding="utf-8", newline=NL)

    stamp = ("GENERATED FILE — DO NOT EDIT.  Source of truth: protocol/" + ANCHOR.name
             + "  v" + ver + "  sha256 " + digest + "  (" + str(len(raw.splitlines()))
             + " lines).  Built " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
             + ".  Rebuild: python scripts/build_manuscript_html.py")

    head = (
        '<h1 class="art-title">' + title + "</h1>"
        '<p class="art-type">Detailed research protocol</p>'
        '<p class="authors">Pre-registered protocol · Stage 1 of a Registered Report</p>'
        '<p class="affiliations">Instrument: ' + str(aj.get("instrument", "the pinned JEV encoder"))
        + " · Licence: " + str(aj.get("licence", "see docs/PHASE_I_PIN.md"))
        + " · Phase I: English, keyboard-faithful typos, frozen parameters</p>"
        + '<div class="art-meta"><span><b>Version</b> ' + ver + "</span>"
        + "<span><b>Equations</b> " + str(len(r.display)) + " numbered</span>"
        + "<span><b>Notes</b> " + str(len(r.notes)) + "</span>"
        + "<span><b>Callouts</b> " + str(len(made)) + "</span>"
        + "<span><b>Sections</b> " + str(len(toc)) + "</span></div>"
        + '<p class="stamp">' + stamp + "</p>")

    root = NL.join("  --" + k + ": " + v + ";" for k, v in PALETTE.items())
    dark = NL.join("  --" + k + ": " + v + ";" for k, v in DARK.items())
    banner_meta = ("v" + ver + " · " + str(len(r.display)) + " equations · "
                   + str(len(toc)) + " sections · " + datetime.date.today().isoformat())

    out_html = HTML.format(mathjax_scripts=_sr.MATHJAX_SCRIPTS, title=title, subtitle=subtitle, banner_meta=banner_meta,
                           toc=toc_links, head=head, body=html,
                           css=CSS % {"root": root, "dark": dark})
    out = ROOT / args.out
    out.write_text(out_html, encoding="utf-8", newline=NL)

    cited = sorted({int(n) for n in re.findall(r"equation \((\d+)\)", raw)})
    made_nums = sorted(n for n, _ in r.display)
    print("  anchor    : protocol/" + ANCHOR.name + "  v" + ver
          + "  " + str(len(raw.splitlines())) + " lines")
    print("  sha256    : " + digest)
    print("  mathjax   : " + mathjax_ver + "  (copied locally; no network request)")
    print("  equations : " + str(len(r.display)) + " numbered, "
          + str(len(r.notes)) + " with a note, " + str(len(r.purposes)) + " with a purpose line")
    print("  prose cites equation(s): " + (", ".join(str(c) for c in cited) or "none"))
    print("  sections  : " + str(len(toc)) + " in the sidebar TOC")
    print("  panels    : " + str(n_cards) + " derived data cards, "
          + str(n_rows) + " derived checklist rows (every value read from the anchor)")
    print("  callouts  : " + str(len(made)))
    for v, lab in made:
        print("               " + v + "  " + lab)
    print("  output    : " + out.relative_to(ROOT).as_posix()
          + "  (" + format(out.stat().st_size, ",") + " B)")

    missing = [c for c in cited if c not in made_nums]
    if missing:
        print(NL + "  [FAIL] the prose cites equation number(s) " + str(missing)
              + " that the render does not produce.")
        return 1
    print("  numbering : every cited equation number exists in the render  OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())