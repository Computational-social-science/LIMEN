# Reference audit — the manuscript's bibliography, verified against fetched records

**Date:** 2026-10-07. **Scope:** the 15 works cited in `docs/PAPER.md`, plus the same bibliography as it
appears in `docs/SUPPLEMENTARY_INFORMATION.md`.

**Method:** every factual field — authors, title, journal, volume, issue, pages, year, identifier — compared
against a record fetched from the registry native to its literature. No field was taken from memory, and no
field was accepted because it "looked right". Sources: arXiv API (abs records), Crossref, PubMed E-utilities,
OpenLibrary.

## Field layer — 15 of 15 verified

| # | Work | Verified against | Verdict |
|---|---|---|---|
| 1 | Chhikara 2025 | arXiv 2502.11028 | OK |
| 2 | Green & Swets 1966 | OpenLibrary (work OL31575577W), corroborated by the 1967 *Science* review | OK |
| 3 | Hua et al. 2025 | arXiv 2509.01790 | OK |
| 4 | Kirichenko et al. 2025 | arXiv 2506.09038 | OK |
| 5 | Lee & See 2004 | Crossref 10.1518/hfes.46.1.50_30392 | OK |
| 6 | Parasuraman & Riley 1997 | Crossref 10.1518/001872097778543886 | OK |
| 7 | Phillips et al. 2026 | arXiv 2603.21172 | OK |
| 8 | Rayner et al. 2006 | PubMed PMID 16507057 (the work has no Crossref record reachable; see below) | OK |
| 9 | Shannon 1948 | Crossref 10.1002/j.1538-7305.1948.tb01338.x | OK |
| 10 | Shannon 1959 | Crossref 10.1109/9780470544242.ch21 (the reprint's own metadata names the original venue) | OK |
| 11 | Soni 2026 | arXiv 2607.04686 | OK |
| 12 | Wiener 1948 | OpenLibrary (work OL4307531W) | OK |
| 13 | Wu 2026 | arXiv 2606.14589 | OK |
| 14 | Xie et al. 2026 | arXiv 2608.20349 | OK |
| 15 | Zhao et al. 2025 | arXiv 2510.09536 | OK |

**Author lists were checked in full, not against a remembered short form.** Xie et al. carries nine authors
ending in Kaishun Wu; the manuscript lists all nine. No truncated list, no invented co-author, no merged
surname.

**No FIX was required at the field layer.** That is a result, not a formality: the bibliography had been
assembled from fetched records, and the audit confirms it rather than repairing it.

## A DOI guess that would have shipped a wrong citation

Rayner et al. 2006 carries no DOI in the manuscript. A plausible one was constructed from memory —
`10.1111/j.1467-9280.2006.01686.x` — and **resolved to a different paper in the same journal, volume and
issue** ("The Malleable Meaning of Subjective Ease", pp. 200–206, against the intended pp. 192–193). One
character in the suffix.

The record was then obtained properly, from PubMed: **PMID 16507057**, *Psychological Science* 17(3) 192–3
(2006), Rayner K; White SJ; Johnson RL; Liversedge SP — the real DOI is `...01684.x`. **This is the trap the
verification discipline names outright: a syntactically valid identifier pointing at the wrong work is
invisible to every string comparison.**

## Claim layer — one FIX, and it mattered

**INFLATED / misattributed.** The manuscript, the Supplementary information and two SI sections all stated
that the noise levels were *"anchored on a published human result … the interior-scrambled condition of
Rayner et al. (2006), **in which readers recovered the intended word 0.4480 of the time**."*

That sentence attributes to Rayner's readers a number Rayner never reported. The project's own source states
the provenance exactly:

> `scripts/o1_recoverability.py` — *"This is the MEASURED value of that condition **under this index**
> (interior-scrambled variant, the harsher of the two), and it is what `lo` has to clear."*

**0.4480 is what this project's recoverability index returns when it is applied to Rayner's published
stimulus manipulation.** Rayner et al. report comprehension accuracy and reading time for that condition; the
paper's title is a claim about reading cost. A number produced here was carried into the manuscript wearing
the authority of a published human result, which is precisely the defect this repository refuses everywhere
else — and it was load-bearing, because the anchor is what selects λ_lo and λ_mid.

**Fix applied (5 places in 4 documents):** the phrasing now says the anchor is a published human
**manipulation** *measured under this index rather than quoted from the paper*, and it states what Rayner
reported instead. The anchor's numerical value is unchanged — this corrects an attribution, not a
measurement.

**Flagged, not fixed (no action taken):** the specific figure "~11% slower" appears in a code comment as
Rayner's reported reading-time cost. The PubMed record for a two-page report carries no abstract, so the
figure could not be verified against a registry record and is **not** asserted in the rewritten prose. It
needs the full text before it can be used.

## What this audit could not do

**It cannot certify that a cited work says what the sentence says except where the record carries the claim.**
Xie et al., Hua et al., Kirichenko et al., Phillips et al., Soni, Wu and Zhao were verified at the field layer
and their abstract-level claims match the sentences attached to them; a claim deeper than an abstract needs
the full text. **The Rayner entry is the case in point** — the field layer passed and the claim layer did not,
and only the claim layer could have found it.

## Standing rule

Listed here so it is not rediscovered: **a kernel name, a DOI, a page range and a recovered-value anchor are
all the same kind of assertion — each is a promise that something exists as described.** Only the first is
mechanically guarded (`scripts/check_lean_citations.py`). The others are checked by running this audit, and it
has to be run rather than remembered.
