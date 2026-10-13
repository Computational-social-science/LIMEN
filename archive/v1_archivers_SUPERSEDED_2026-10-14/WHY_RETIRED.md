# Why these three scripts are retired

**Retired:** 2026-10-14

`archive_v1_evidence.py`, `archive_v1_pages.py`, `archive_v1_rows.py` were one-shot
scripts written on 2026-10-13 to preserve the v1 keystroke-observatory scaffold's
evidence before it was deleted. They ran once, succeeded, and are now dead code.

## Why they are dead

Three reasons, each sufficient:

1. **Their output moved to another project.** They write to
   `LIMEN/evidence/v1_superseded/`, and that directory no longer exists here: the
   evidence belongs to `keystroke-observatory`, which is an independent project, and it
   moved there on 2026-10-14. Running them now would recreate a directory in the wrong
   repository.

2. **The paths they read are gone.** They reference
   `keystroke-observatory-PRE-REBUILD-BACKUP-20261012-181735/` and
   `keystroke-observatory/_legacy_v1/`, both deleted during the cleanup. Every one of
   their inputs no longer exists, so they cannot run at all.

3. **Their work is verifiably complete.** The outputs are present in the owning project:

       keystroke-observatory/evidence/v1_superseded/v1_defect_signatures.json
       keystroke-observatory/evidence/v1_superseded/v1_column_summary.json
       keystroke-observatory/evidence/v1_superseded/v1_row_facts.json
       keystroke-observatory/evidence/v1_superseded/v1_pages_snapshot/

   and `check_handoff.py`'s check A verifies that archive by content hash, so its
   integrity is checked by the project that owns it rather than by a script here.

## Why they are kept rather than deleted

The same reason the v1 material itself is kept: they document how the evidence was
produced. A reader asking "where did `v1_row_facts.json` come from?" gets an answer
instead of silence. They are in `archive/` so no guard scans them and no reader mistakes
them for live code.

## Not a loss

Nothing here is needed to run LIMEN. The evidence is verified in the project that owns
it, and LIMEN's science reads the corpus directly -- it never consumed these files.
