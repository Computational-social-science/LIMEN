"""Verify the technical report's citations against the PDFs on disk.

Why this exists
---------------
A citation written from memory was wrong: LinguaMeta was attributed to "Blaschke et al. (2022),
LREC 2022", and the paper on disk is Ritchie et al., LREC-COLING 2024, 10530-10538. The authors,
the year and the venue were all wrong, and nothing in the project could have caught it, because
every other check compares an artefact to another artefact while a citation is compared to nothing.

So the ground truth here is the PDF, not a table in this file. Each expected citation names a PDF;
the verifier extracts that PDF's first page, pulls the surnames, the year, the venue and the page
range out of the text, and requires the report to carry them. A citation whose PDF is absent is
reported as unverified rather than passed, because "cannot check" and "checked and correct" are
different states and conflating them is how a wrong citation survives.

The report is read as the browser assembles it: the markup PLUS the scripts it loads. The reference
list is not in the HTML at all -- the markup ends in an empty `<div class="refs" id="refs"></div>`
and report.js fills it at load time -- so a guard that read only the HTML found none of the cited
papers and reported all eight as missing citations. They were never missing.

The negative control corrupts one citation in the text the verifier reads and asserts the verifier
goes red. It locates its target structurally, through the citation's own anchor, and refuses to
report a pass when it could not change anything: a control that cannot corrupt is INERT, and an
inert control is a defect in the control rather than a result.
"""
import pathlib
import re
import sys

try:
    import pymupdf
except ImportError:  # noqa: BLE001
    pymupdf = None

REPO = pathlib.Path(__file__).resolve().parents[1]
REPORT = REPO / "viz" / "report" / "technical-report.html"
REPORT_DIR = REPORT.parent
# THE PROJECT'S OWN REFERENCE PDFS COME FIRST.
#
# This resolved `REPO.parent / "external-data"` -- E:\2026-AI4S\external-data, a SIBLING
# directory -- so the citation check read its ground truth from outside the project. The
# same accidental dependency three other scripts had, and the same reason it went
# unnoticed: the sibling happened to be there and held all 11 PDFs.
#
# Found while auditing whether that sibling tree could be deleted. The first pass said
# "nothing references it", which was wrong: this guard does, through a parent-relative
# path that no text search for the literal would have surfaced.
#
# The PDFs are 13.2 MB in total, so they now live inside the project and are TRACKED --
# unlike the corpora, this is small enough for git, which means a clone carries its own
# citation ground truth and the check works anywhere.
_PDF_CANDIDATES = (
    REPO / "external-data" / "references",
    REPO.parent / "external-data",
)
PDF_DIR = next((p for p in _PDF_CANDIDATES if p.is_dir() and any(p.glob("*.pdf"))),
               _PDF_CANDIDATES[0])

# The negative control corrupts this citation's venue, and names it by ANCHOR and by VENUE rather
# than by a literal fragment of source. A literal is a statement about how the file happens to be
# typed; an anchor is a statement about which paper the entry is. LinguaMeta (2024) is the target
# because it shares its venue with GlotScript, so a corruption that only a windowed check can see
# is exactly what the control has to prove.
CONTROL_ANCHOR = "Drummond"
CONTROL_VENUE = "LREC-COLING 2024"
CONTROL_WRONG_VENUE = "LREC 2022"
CONTROL_KEY = "linguameta"

# The reference list is a JS array of { k: '<key>', t: '<text>' } entries. Anchored on the key
# assignment so that an entry's start is unambiguous and the entry after it bounds it.
REFS_START = "  const REFS = ["
ENTRY_RE = re.compile(r"\{\s*k:\s*'([^']+)',\s*t:\s*")

# citation key -> (pdf filename or None, surnames that must appear, year, venue marker, pages)
#
# The surnames, year, venue and pages here are what the verifier REQUIRES the report to carry;
# they are checked against the PDF's own first page by first_page_text() below, so a wrong
# entry in this table is itself caught rather than trusted.
EXPECTED = [
    # (key, pdf, anchor unique to the citation, surnames, year, venue, page)
    ("github-typo-corpus", "2020-lrec-GitHub Typo Corpus.pdf",
     "Hagiwara", ["Hagiwara", "Mita"], "2020", "LREC 2020", "6761"),
    ("jwtd-paper", "jwtd_paper.pdf",
     "Tanaka", ["Tanaka", "Murawaki", "Kawahara", "Kurohashi"], "2020",
     "2020 Student Research Workshop", "230"),
    ("136m-keystrokes", "2018-CHI-Observations-on-Typing-from-136M-Keystrokes.pdf",
     "Dhakal", ["Dhakal", "Feit", "Kristensson", "Oulasvirta"], "2018", "CHI 2018", None),
    ("linguameta", "2024-LinguaMeta_lrec-main.921.pdf",
     "Drummond", ["Ritchie", "van Esch", "Okonkwo", "Vashishth", "Drummond"], "2024",
     "LREC-COLING 2024", "10530"),
    ("writingsystem-2800",
     "2022.lrec-Writing System and Speaker Metadata for 2,800+ Language Varieties.pdf",
     "Lucassen", ["van Esch", "Lucassen", "Ruder", "Caswell", "Rivera"], "2022",
     "LREC 2022", "5035"),
    ("glotscript", "2024-GlotScript_lrec-main.687.pdf",
     "Kargaran", ["Kargaran", "Yvon", "Sch"], "2024", "LREC-COLING 2024", "7774"),
    ("lespell", "2022-LeSpell_lrec-1.73.pdf",
     "Laarmann-Quante", ["Bexte", "Laarmann-Quante", "Horbach", "Zesch"], "2022",
     "LREC 2022", "697"),
    ("noiseqa", "2021-2021 EACL_NoiseQA.pdf",
     "Ravichander", ["Ravichander", "Dalmia", "Ryskina", "Metze", "Hovy", "Black"], "2021",
     "EACL 2021", "2976"),
]


def first_page_text(name: str):
    """(status, text) where status is 'ok', 'missing' or 'unreadable'.

    Conflating 'the file is not there' with 'the file is there and no text came out' made the
    verifier report a present PDF as absent, which reads as a missing source rather than as a
    PDF whose first page is not machine-readable. They are different faults and only one of
    them is about the citation.
    """
    if pymupdf is None:
        return "unreadable", ""
    p = PDF_DIR / name
    if not p.exists():
        return "missing", ""
    try:
        doc = pymupdf.open(p)
        t = re.sub(r"\s+", " ", doc[0].get_text())
        return ("ok" if t.strip() else "unreadable"), t
    except Exception:  # noqa: BLE001
        return "unreadable", ""


def deconcatenate(text: str) -> str:
    """Undo the JS string concatenation that splits a citation across source lines.

    The references live in a JavaScript array, so a citation is split across source lines:
    the source contains '<em>ACL 2020 Student ' + "\\n      " + 'Research Workshop</em>',
    and the contiguous text a reader sees does not exist in the file. Checking the raw source
    therefore reported a present venue as missing. The concatenation is removed first, so the
    comparison is against what the page renders rather than against how it is typed.
    """
    text = re.sub(r"'\s*\+\s*\n\s*'", "", text)
    text = re.sub(r'"\s*\+\s*\n\s*"', "", text)
    return text


def report_source():
    """(text, sources): the report as the browser assembles it -- markup PLUS the scripts it loads.

    THE DEFECT THIS FIXES. The reference list is not in technical-report.html. The markup ends in
    an empty `<div class="refs" id="refs"></div>` and report.js fills it at load time, so the
    eight cited papers appear in no byte of the HTML. A guard that read only the HTML found none
    of them and reported all eight as missing citations -- a false alarm about the document,
    caused entirely by reading the wrong file. The same fault was already found and fixed in
    qc_report_structure.py, which is why the same convention is reused here rather than invented:
    follow each `<script src=...>` in the markup and append the script's text.

    SAME DIRECTORY ONLY: `../mathjax/` is a vendored bundle, not this report's code, and sweeping
    it in would let a stray surname in a third-party library satisfy a citation check.

    A missing script is NOT silently ignored: it is returned so the caller can fail, because a
    guard that cannot find the reference list must say so rather than report every citation
    absent.
    """
    html = REPORT.read_text(encoding="utf-8")
    parts = [html]
    missing = []
    for src in re.findall(r"""<script[^>]*\bsrc=["']([^"']+)["'][^>]*>""", html, re.I):
        ext = (REPORT_DIR / src).resolve()
        if ext.parent != REPORT_DIR.resolve() or ext.suffix != ".js":
            continue
        if not ext.exists():
            missing.append(src)
            continue
        parts.append(ext.read_text(encoding="utf-8"))
    return deconcatenate("\n".join(parts)), missing


def refs_block(text: str) -> str:
    """The `const REFS = [...]` array out of report.js, or "" if it is not there.

    The reference list is a JavaScript array in the report's own script. Scoping to it matters:
    every anchor below also occurs in state.js (the citation strings are shipped there as JSON),
    so an unscoped search finds the wrong copy of the text first.
    """
    i = text.find(REFS_START)
    if i < 0:
        return ""
    j = text.find("  ];", i)
    return text[i:j] if j > i else ""


def citation_window(text: str, anchor: str) -> str:
    """The single reference entry that carries `anchor`, or "" when no entry does.

    TWO FAULTS ARE FIXED HERE, and the second is why the control could not fire.

    1. UNIQUENESS. Using the first surname put the van Esch (2022) citation's window inside the
       LinguaMeta (2024) entry, because "van Esch" is a co-author of both and LinguaMeta comes
       first in the list. Each entry in EXPECTED therefore names a token that occurs in exactly
       one reference, and this function verifies that claim by returning the ONE entry that
       contains the anchor.

    2. SCOPE. The window used to run from the previous single quote to the next "'," -- which,
       once the scripts were read, ran from state.js into report.js and measured ~35 000
       characters spanning three different references. Every fact was then checked against a
       region holding three papers' worth of text, so "the venue is in the window" was satisfied
       by a NEIGHBOURING citation's venue. That is the same "presence is not correctness" fault
       the comment below already claims to fix, one level down: a window that is too wide is as
       wrong as no window at all. The control proved it -- corrupting LinguaMeta's venue left
       "LREC-COLING 2024" still present in the window (GlotScript cites it), so the check passed
       on a corrupted document.

       The window is therefore the entry itself: from its `{ k: '<key>', t: '` opening to the next
       entry's opening.
    """
    block = refs_block(text)
    if not block:
        return ""
    entries = list(ENTRY_RE.finditer(block))
    for n, m in enumerate(entries):
        end = entries[n + 1].start() if n + 1 < len(entries) else len(block)
        entry = block[m.start():end]
        if anchor in entry:
            return entry
    return ""


def main(negative: bool = False) -> int:
    if not REPORT.exists():
        print("  [FAIL] report not found: %s" % REPORT)
        return 1
    text, missing_scripts = report_source()
    if missing_scripts:
        # Not a [SKIP]: the report is present, so its own reference list is checkable and its
        # absence is a fault in the report, not a subject that is gone.
        print("  [FAIL] the report loads script(s) that are not on disk: %s" % ", ".join(missing_scripts))
        print("         the reference list lives there, so no citation can be verified")
        return 1
    if not refs_block(text):
        # The reference list is the subject of this guard. If it cannot be located, saying so is
        # the only honest output: reporting eight absent citations instead would blame the
        # document for the guard's own inability to find the list.
        print("  [FAIL] the report's reference list (const REFS) was not found in the report or in")
        print("         the scripts it loads, so no citation can be verified")
        return 1

    if negative:
        # Corrupt ONE citation, in place, by ANCHOR rather than by a literal fragment of source.
        # The literal this used to key on ("LREC-COLING 2024</em>, 10530") was a statement about
        # how the entry happened to be typed; a reformatting removed it, the substitution became a
        # no-op, and the control reported success while testing nothing.
        #
        # Only the venue is altered: the authors, the year and the pages all stay correct, so a
        # check that reads the window must go red for the right reason. LinguaMeta's venue is
        # replaced with "LREC 2022", a venue that IS present elsewhere in the reference list (the
        # LeSpell and van Esch entries), so this also proves the check is windowed: a
        # document-level "does the string appear anywhere" test would still pass.
        win = citation_window(text, CONTROL_ANCHOR)
        if not win:
            print("  [FAIL] the negative control could not corrupt anything: the citation anchored on")
            print("         %r is not in the report at all, so the control is INERT." % CONTROL_ANCHOR)
            print("         An inert control is a defect in the control, not a pass.")
            return 1
        corrupted = win.replace(CONTROL_VENUE, CONTROL_WRONG_VENUE, 1)
        if corrupted == win:
            print("  [FAIL] the negative control could not corrupt anything: the citation anchored on")
            print("         %r carries no %r to replace, so the control is INERT." % (CONTROL_ANCHOR, CONTROL_VENUE))
            print("         An inert control is a defect in the control, not a pass.")
            return 1
        # The substitution is applied to the document, not just to the window copy, so the check
        # below reads exactly the corrupted text and nothing else changes.
        text = text.replace(win, corrupted, 1)
        print("  negative control: the citation anchored on %r had its venue changed from %r to %r"
              % (CONTROL_ANCHOR, CONTROL_VENUE, CONTROL_WRONG_VENUE))
        print("                    (surnames, year and pages left correct)")

    fails, checked = [], 0
    unverified, unreadable = [], []

    # A citation's facts must CO-OCCUR, not merely each appear somewhere in the document.
    # Checking the whole file for each fact in turn passed a corruption: replacing the
    # LinguaMeta venue with "LREC 2022" left "LREC-COLING 2024" present elsewhere (the GlotScript
    # reference cites the same venue), so the document-level test was satisfied by a different
    # citation's text. This is the same fault as the data statement's "presence is not
    # correctness": a string being somewhere is not the string being here.
    #
    # So the window is located first -- the single reference entry that carries the citation's
    # anchor -- and every fact is then required inside that entry. citation_window() is defined at
    # module level because the negative control needs the same window to aim its corruption.
    for key, pdf, anchor, surnames, year, venue, pages in EXPECTED:
        status, pdf_text = first_page_text(pdf)

        win = citation_window(text, anchor)
        if not win:
            fails.append((key, "no citation found for anchor %r" % anchor))
            continue

        missing = []
        for sn in surnames:
            if sn not in win:
                missing.append("surname %r" % sn)
        # THE YEAR IS CHECKED IN CITATION POSITION, as "(YYYY)". A bare substring test for the year
        # is satisfied by the entry's own KEY ('ritchie2024') and by its URL
        # ('https://aclanthology.org/2024.lrec-main.921/'), neither of which is the citation's year
        # -- so changing an entry's year from 2024 to 2021 left the check green. Presence is not
        # correctness, again: the year has to be where a year is written.
        if year and ("(%s)" % year) not in win:
            missing.append("year %s (in citation position)" % year)
        if venue and venue not in win:
            missing.append("venue %r" % venue)
        if pages and pages not in win:
            missing.append("page %s" % pages)
        if missing:
            fails.append((key, "citation window lacks: " + ", ".join(missing)))
        else:
            checked += 1

        # 2. is the expected metadata itself true of the PDF?  (checks this table too)
        if status == "missing":
            unverified.append((key, pdf))
            continue
        if status == "unreadable":
            unreadable.append((key, pdf))
            continue
        bad_meta = []
        for sn in surnames:
            if sn not in pdf_text:
                bad_meta.append("surname %r not on the PDF's first page" % sn)
        if year and year not in pdf_text:
            bad_meta.append("year %s not on the PDF's first page" % year)
        if pages and pages not in pdf_text:
            bad_meta.append("page %s not on the PDF's first page" % pages)
        if bad_meta:
            fails.append((key, "THIS FILE'S EXPECTATION is wrong: " + "; ".join(bad_meta)))

    print()
    for key, why in fails:
        print("  [FAIL] %-22s %s" % (key, why))
    for key, pdf in unverified:
        print("  [SKIP] %-22s PDF absent from disk: %s" % (key, pdf))
    for key, pdf in unreadable:
        print("  [SKIP] %-22s PDF present but its first page yields no text: %s" % (key, pdf))
    print()
    print("  citations checked against the PDFs: %d of %d" % (checked, len(EXPECTED)))
    print("  unverifiable (no usable PDF)     : %d" % (len(unverified) + len(unreadable)))

    if negative:
        # The control must catch THE CORRUPTION, not merely "something failed". Testing `if fails`
        # let any unrelated failure -- a genuinely absent citation, a wrong page number -- stand in
        # for the corruption and report a control that had not actually detected its own edit. The
        # assertion is therefore that the corrupted citation is named in the failures AND that the
        # reason is the venue, since the control changed only the venue. The failure message names
        # the venue the check EXPECTED to find, which is the one the control replaced.
        caught = [why for key, why in fails if key == CONTROL_KEY]
        if caught and "venue" in caught[0] and CONTROL_VENUE in caught[0]:
            print("  negative control: FIRED -- the verifier reported the corrupted citation:")
            print("                    %s: %s" % (CONTROL_KEY, caught[0]))
            return 0
        if caught:
            print("  [FAIL] negative control: the corruption was caught, but for the wrong reason:")
            print("         %s: %s" % (CONTROL_KEY, caught[0]))
            print("         expected a venue failure naming %r" % CONTROL_VENUE)
            return 1
        print("  [FAIL] negative control: the corruption was NOT detected -- the verifier did not")
        print("         report the altered venue of the citation anchored on %r." % CONTROL_ANCHOR)
        if fails:
            print("         (it did fail, but on other citations, which does not test the control)")
        return 1

    if fails:
        print("  [FAIL] %d citation problem(s)" % len(fails))
        return 1
    print("  [OK] every checkable citation matches its source PDF")
    return 0


if __name__ == "__main__":
    sys.exit(main("--negative-test" in sys.argv))
