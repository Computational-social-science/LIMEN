# Environment displacement: a recurring failure, and how to recover in one command

**Occurrences:** two, on 2026-10-13 and 2026-10-15 (found)
**Status:** both recovered; no data lost either time

---

## What happens

The shared Hermes Python environment
(`C:\Users\Administrator\AppData\Local\hermes\tools\python-3.14.7+20260901-win32-x64\`)
periodically gets **displaced**: its entire `Lib\site-packages` is moved to a sibling
directory named `.reclaim-<hex>`, and a fresh near-empty `site-packages` is left in its
place holding only `pip` and `README.txt`.

`sys.path` still points at the original location, so imports resolve against the empty
directory and fail. The failure is confusing because it names a **module**, not the
resolver:

```
ModuleNotFoundError: No module named 'pytest'
```

...when pytest is installed, one directory away, in the reclaim folder.

## Observed twice

| when | reclaim directory | packages moved |
|---|---|---|
| 2026-10-13 | `.reclaim-1a2e96d03d5c4ad1a508c565519e7861` | 43 |
| 2026-10-15 (found) | `.reclaim-74250f674ee14da5b2b72fa617732b05` | 45 |

The first occurrence was caused by running `pip install` against the shared interpreter.
**The second was not**: it was found while running the end-to-end suite, when pytest
vanished mid-session after working earlier the same day. So this is not solely a
self-inflicted hazard -- it is a property of this environment, and it will recur.

## Recovery, and why it is safe

Nothing is lost: the packages are all in the reclaim directory, complete. Restoring them
is a move, not a reinstall, which matters because reinstalling into this environment is
what caused the first occurrence.

```powershell
$reclaim = <the .reclaim-* directory>
$sp      = C:\Users\Administrator\AppData\Local\hermes\tools\python-3.14.7+20260901-win32-x64\Lib\site-packages
$src     = Get-ChildItem "$reclaim\Lib\site-packages" -Force
$have    = (Get-ChildItem $sp -Force).Name
foreach ($i in $src | Where-Object { $_.Name -notin $have }) {
    Move-Item -LiteralPath $i.FullName -Destination (Join-Path $sp $i.Name) -Force
}
```

Then verify by **importing**, not by listing:

```powershell
python -c "import pytest, rapidfuzz, playwright, scienceplots, torch, laya"
```

Last recovery: 45 entries restored, 0 failed, 12 of 12 packages importable.

## The rule this implies

**Do not run `pip install` against the shared Hermes interpreter.** A missing dependency
is a finding to report, not an obstacle to clear -- and the guard that reported it
(`qc_stage2_figures` warning that `scienceplots` was absent) was telling the truth about
its own audit, not asking to be silenced.

That rule is recorded in `docs/INCIDENT_PIP_INSTALL_2026-10-13.md`. This file adds
the second half: the displacement **recurs without an install**, so a missing module in
this environment should be met with "check for a `.reclaim-*` directory" before anything
else.

## What this cost

Twice, a check failed with a misleading error and the first instinct -- install the
missing package -- would have deepened the problem. The correct first move is:

1. `Get-ChildItem C:\Users\Administrator\AppData\Local\hermes\tools -Directory -Filter '.reclaim-*'`
2. if one exists and holds the package, MOVE it back;
3. re-verify by importing.
