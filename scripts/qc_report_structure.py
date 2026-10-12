"""Structural check of the technical report: are the requested sections actually present?"""
import pathlib
import re

h = pathlib.Path("viz/report/technical-report.html").read_text(encoding="utf-8")
# THE DOCUMENT IS HTML *AND* THE SCRIPTS IT LOADS. The report's consumer moved out of the HTML into
# report.js, and twenty of these checks then failed -- not because the report lost anything, but
# because the markers they search for moved to a file this guard was not reading. Text checks are
# substring searches, so adding the script can only restore matches that the extraction removed; it
# cannot hide a marker that is present in the markup.
for _src in re.findall(r"""<script[^>]*\bsrc=["']([^"']+)["'][^>]*>""", h, re.I):
    _ext = (pathlib.Path("viz/report") / _src).resolve()
    # SAME DIRECTORY ONLY: ../mathjax/ is a vendored bundle, not this report's code.
    if _ext.parent == pathlib.Path("viz/report").resolve() and _ext.suffix == ".js" and _ext.exists():
        h += "\n" + _ext.read_text(encoding="utf-8")

# Prose assertions must not depend on where the line wraps. The source is wrapped at ~95 columns for
# readability, so a phrase like "is not robust and is not relied on here" can straddle a newline and
# fail a substring test that the document actually satisfies -- which is exactly what happened, and
# the failure looked like a missing sentence rather than a brittle check. `hn` collapses every run of
# whitespace to a single space, and prose checks read `hn`. Structural checks keep reading `h`, since
# they test markup where whitespace can matter.
hn = re.sub(r"\s+", " ", h)

CAPTION_RE = re.compile(r"<figcaption>(.*?)</figcaption>", re.S | re.I)


def table_spec(html: str) -> list[str]:
    """A Nature table is three rules: above the header, below it, and at the foot.

    The report's tables carried a rule under every row and a shaded, uppercased header. Neither is
    what the journals set, and both are load-bearing on appearance only, so nothing else in the suite
    would have caught them. Checked in the CSS, because the tables are generated at runtime and the
    stylesheet is the single thing that decides how all of them look.
    """
    out = []
    m = re.search(r"<style[^>]*>(.*?)</style>", html, re.S)
    css = m.group(1) if m else ""
    if not css:
        return ["no stylesheet found, so the table specification cannot be verified"]
    if not re.search(r"table\{[^}]*border-top\s*:", css):
        out.append("tables carry no top rule")
    if not re.search(r"thead\s+th\{[^}]*border-bottom\s*:", css):
        out.append("no rule below the header row")
    if not re.search(r"table\{[^}]*border-bottom\s*:", css):
        out.append("tables carry no foot rule")
    if re.search(r"th\s*,\s*td\{[^}]*border-bottom\s*:", css):
        out.append("a rule under every row: a three-line table has none")
    if re.search(r"th\{[^}]*background\s*:", css):
        out.append("shaded header: Nature tables are unshaded")
    if re.search(r"th\{[^}]*text-transform\s*:\s*uppercase", css):
        out.append("uppercased header: Nature tables use sentence case")
    if "<thead>" not in html:
        out.append("no <thead> anywhere, so the header rule cannot attach")
    return out


def caption_typed_numbers(html: str) -> list[str]:
    """A measurement typed into a caption is a copy nothing keeps in step with the artefact.

    Two captions here were written with their numbers typed in, and both were wrong or
    about to drift: the keyboard validation quoted a rate whose field had been renamed, and the
    summary caption quoted a pair count before the balanced run changed it. The caption is prose, so
    no arithmetic check covers it. This one does: strip the parts that legitimately carry a value --
    code spans, elements with an id (those are the rendered ones) and the file paths -- and look for
    a number left in what remains.
    """
    out = []
    for i, body in enumerate(CAPTION_RE.findall(html), 1):
        t = re.sub(r"<code>.*?</code>", " ", body, flags=re.S)
        t = re.sub(r'<span[^>]*\bid="[^"]*"[^>]*>.*?</span>', " ", t, flags=re.S)
        t = re.sub(r"<[^>]+>", " ", t)
        t = re.sub(r"&[a-zA-Z]+;", " ", t)
        hits = []
        if re.search(r"[0-9]+(?:\.[0-9]+)?\s*%", t):
            hits.append("a percentage")
        if re.search(r"\b0\.[0-9]{2,}\b", t):
            hits.append("a decimal")
        if re.search(r"\b[0-9]+\s+of\s+[0-9]{1,3}\b", t):
            hits.append("an 'x of y' count")
        for what in hits:
            out.append("caption %d: %s" % (i, what))
    return out

want = [
    ("S1 sources carries a citation row", "s.citation" in hn),
    ("S2 formal framework heading", "2 \u00b7 Formal framework" in hn),
    ("2.1 Bayes posterior", r"P(r \mid s)" in hn),
    ("2.2 fixed-choice elicitation", r"P(s \mid a)" in hn),
    ("2.3 margin definition", r"m(s) \;=\; d(r, s)" in hn),
    ("2.4 proposition stated", "Proposition" in hn),
    ("2.4 proof with both cases", "Case 1" in hn and "Case 2" in hn),
    ("2.4 proof closed", r"\square" in hn),
    ("2.5 frequency-ordered group", r"G(\rho) = (c_1" in hn),
    ("2.5 rank definition", r"\mathrm{rank}(r)" in hn),
    ("2.5 corollary numeric", "0.071" in hn),
    ("2.6 product space", r"\underbrace" in hn),
    ("2.7 depth is hypothesis not label", "a property this corpus encodes" in hn),
    ("2.8 cannot-support statement", r"\text{RRC does not support }" in hn),
    ("S3 filtration funnel element", 'id="funnel"' in hn),
    ("S4.3 length ladders element", 'id="lenTable"' in hn),
    ("S4.5 IME card element", 'id="imeCard"' in hn),
    ("S5 significance element", 'id="sigChannel"' in hn),
    ("S5.3 falsifiers subsection", "would falsify" in hn),
    ("S8 references block", 'id="refs"' in hn and "const REFS" in hn),
    # instruments and dependencies: the report must show what computes, not only what supplies
    ("S1.2 instruments section", 'id="instruments"' in hn and "INS.instruments" in hn),
    # the introduction: motivation, construction, significance and limits all stated up front
    ("Introduction section", "<h2>Introduction</h2>" in hn),
    ("Introduction states motivation", "<strong>Motivation.</strong>" in hn),
    ("Introduction states the frame", "The object is the channel, not the error." in hn),
    ("Introduction says why observed", "Why observed rather than generated." in hn),
    ("Introduction defines the corpus", "What the corpus is." in hn),
    ("Introduction states testability", "What it makes testable." in hn),
    ("Introduction states what is NOT claimed", "What it does not claim." in hn),
    ("Introduction gives a roadmap", "How to read this report." in hn),
    # the measurement: instrument, cross-arm control layer, p_root, diagnostics, paired test
    ("S5.5 measurement section", 'id="meas-summary"' in hn and "MS.n_rows" in hn),
    ("S5.6 cross-arm control layer", 'id="meas-crossarm"' in hn and "MS.cross_arm_L4" in hn),
    ("S5.7 p_root section", 'id="meas-proot"' in hn and "exact_zero_frac" in hn),
    ("S5.8 instrument diagnostics", 'id="meas-diagnostics"' in h
        and "position_diagnostic" in hn and "len_overlap_tokens" in hn),
    ("S5.9 paired contrast", 'id="meas-paired"' in hn and "paired_ranked_vs_L4" in h
        and "mcnemar" in hn),
    ("S7.1 timing section", 'id="repro-timing"' in hn and "items_per_s" in h
        and "flash-attention" in hn),
    ("S5.10 rank analysis", 'id="meas-f2"' in hn and "f2_rank_effect" in h
        and "rank_1_ci95" in hn),
    ("S5.10 frequency preference", 'id="meas-pref"' in hn and "candidate_preference" in h
        and "uniform_null_rank_mean" in hn),
    ("S5.10 state displacement", 'id="meas-shift"' in hn and "state_displacement" in h
        and "corr_state_rank_vs_picked_rank" in hn),
    ("S5.10 displacement figure", 'fig_reading_displacement.png' in hn and 'id="fig-note"' in h
        and "figcaption" in hn),
    ("S5.10 figure caption is self-contained", "displacement, not a preference" in h
        and "chance" in hn and "rank falsifier itself" in hn),
    ("S5.10 balanced rank curve", "balanced quota per rank value" in h
        and "non-monotone" in hn),
    ("S5.10 two-scheme merge is declared", "measurement_report_rk.json" in h
        and "measurement_report_bs.json" in hn),
    ("S5.11 cross-channel margin test", 'id="meas-margin"' in hn and "margin_effect" in h
        and "corr_margin_correct" in hn),
    ("S5.11 states what the displacement does and does not explain",
     "does not separate the arms that track" in hn and "direction of preference" in hn),
    ("S5.11 four arms under one scheme", "the same sampling scheme" in h
        and "would compare the schemes" in hn),
    # The requirement is that §5.10 DISCLOSES the rank-1 contrast as unstable and not relied on.
    # It previously keyed on the literal "crossing 0.05", which encoded one measurement rather than
    # the disclosure: when the Chinese candidate lists were made reproducible (docs/METHODS_LOG.md §1)
    # the numbers changed, the paragraph was rewritten to explain the instability rather than merely
    # report it, and the guard failed on a section that discharges the requirement better than before.
    # State the property, not the number that happened to express it.
    ("S5.10 discloses the rank-1 contrast as not relied on",
     "not relied on" in hn and "rank-1" in hn),
    ("S5 embeds the measurement summary figure", "../figures/fig_measurement_summary.png" in hn),
    ("S5 summary caption is rendered from state",
        'id="sum-paired"' in hn and 'id="sum-cross"' in hn),
    # The measured keystroke-channel figure was retired 2026-10-12: its composition
    # panel scored every transposition as one insertion plus one deletion. The
    # replacement is figures/fig_error_structure.* -- see
    # archive/keystroke_channel_SUPERSEDED_2026-10-12/WHY_RETIRED.md.
    # ("S4.6 embeds the measured keystroke channel figure",
    #     "../figures/fig_keystroke_channel.png" in hn),
    ("S4.6 caption numbers are rendered from state",
        'id="kbd-validate"' in hn and 'id="kbd-compose"' in hn),
    ("no figure caption carries a typed measurement",
        not caption_typed_numbers(h)),
    ("S3 embeds the corpus funnel figure", "../figures/fig_corpus_funnel.png" in hn),
    ("S3 funnel is accounted in two stages", "Stage 1 — record level" in hn
        and "Stage 2 — item level" in hn),
    ("S3 funnel self-checks its own arithmetic", "does not reconcile" in hn),
    ("S3 funnel caption numbers are rendered", 'id="fun-note"' in hn),
    ("tables meet the Nature three-line specification", not table_spec(h)),
    ("S1.2 renders purpose and version", "r.purpose" in hn and "r.version" in hn),
    ("S1.3 internal modules section", 'id="internal"' in hn),
    ("S1.4 artefacts section", 'id="artefacts"' in hn and "a.exists" in hn),
    ("S1.4 vendored section", 'id="vendored"' in hn),
    ("MathJax vendored path", "../mathjax/tex-mml-chtml.js" in hn),
    ("no external network refs", not re.search(r"https?://", h.split("<script src=")[1].split(">")[0] or "")),
    # navigation: the rail exists and is BUILT FROM the headings rather than hand-listed, so it
    # cannot describe a structure the document does not have
    ("nav rail element", 'id="toc"' in hn and 'id="toc-list"' in hn),
    ("reading-progress element", 'id="progress"' in hn),
    ("toc built from the document's headings", "querySelectorAll('.wrap h2, .wrap h3')" in hn),
    ("toc active-section tracking", "classList.toggle('active'" in hn),
    ("nav collapses on narrow screens", ".collapsed" in hn and "max-width:820px" in hn),
    ("nav hidden when printing", "#toc,#progress{display:none}" in hn),
]

bad = 0
for name, ok in want:
    if not ok:
        bad += 1
    print("  [%s] %s" % ("OK  " if ok else "FAIL", name))

disp = h.count("$$") // 2
inl = len(re.findall(r"(?<!\$)\$(?!\$)", h)) // 2
print()
print("  display maths: %d  |  inline maths: %d" % (disp, inl))
print("  report size  : %d chars" % len(h))
print("  references   : %d entries" % h.count("<em>"))
print()
print("  VERDICT: %s" % ("all structural checks pass" if bad == 0 else "%d FAILED" % bad))
raise SystemExit(1 if bad else 0)
