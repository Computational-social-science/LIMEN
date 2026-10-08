# Unverified drafts — inputs, not findings

The two documents in this directory were produced by delegated research agents on 2026-10-08 while the Phase II
second channel was being assessed. **They are retained as provenance, and they must not be cited as findings.**

**`docs/PHASE_II_S1_CHANNEL_EVIDENCE.md` is the authoritative record of that assessment.** It was written after
checking the load-bearing claims directly against primary sources, and **it corrects three errors found in these
drafts**:

1. **"No separate pin needed — same revision, subfolder download."** Wrong. `multilingual/` carries its own
   weights, its own tokenizer and its own encoder config at the same commit, so adopting it is a re-pin under
   §5.5/§12, not a free subfolder. Verified against the repository file tree at the pinned revision.
2. **"XNLI Japanese 0.731."** A misattribution. The model card reports **0.731 as an aggregate over 14 other
   languages**, not a Japanese figure. Attributing an aggregate to one language is the same defect class the
   project already caught once, when a value this project measured was written as a value a paper published.
3. **"mmBERT-base, 322M."** The model card states **ModernBERT-large, 395M**. Both cannot be right; the card is
   the primary source and the architecture is recorded as unresolved rather than repeated.

Two further claims in the drafts were flagged as unconfirmed and are not relied on: a "four categories including
kanji-conversion" description of the JWTD corpus (the abstract confirms the kanji-input typo class and the
half-million-pair size, but not a four-category taxonomy), and an LDC 2023 frequency ratio with no DOI that the
draft itself marked unverified.

**A fourth defect, found by a guard rather than by reading.** `scripts/check_attributed_numbers.py` fired on
`task2_english_conversion_audit.md` line 95: it writes **0.4480 — a value THIS PROJECT measured under its own
recoverability index — beside an external citation**, without saying where the number came from. That is the
identical error corrected in the protocol one day earlier, committed here by a fresh agent that had no way to
know the number was ours. **It is the strongest argument in this directory for keeping the drafts**: a defect
that recurs immediately in new work, in a document whose author believed it was being careful, is evidence about
the failure mode rather than an embarrassment to hide. The check was extended to name it rather than to pass over
it, and the superseding document states the correct attribution.

**Why they are kept rather than deleted.** The corrections above are only auditable if the drafts they correct
are still readable. A directory that holds a known-wrong claim next to the record of its correction is a
stronger provenance trail than one that holds only the corrected form, and the alternative — deleting the
drafts — would leave the corrections unverifiable.
