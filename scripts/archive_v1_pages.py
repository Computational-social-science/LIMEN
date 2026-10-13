"""Preserve the ONE thing the pre-rebuild backup holds that nothing else does.

`keystroke-observatory-PRE-REBUILD-BACKUP-20261012-181735` is 34.2 MB and almost
entirely redundant with `_legacy_v1` (same DEPLOYMENT_SUMMARY, observable.config.js,
setup.py, README). But it also holds `src/` -- the v1 dashboard PAGES as they stood
before the rebuild -- and `_legacy_v1` does not have them.

HANDOVER_AUDIT.md cites line numbers in exactly those files
("v1 `src/pages/index.md:160`"). Delete the backup without this step and those
citations point at nothing.

So: copy the four source files that carry cited line numbers, record their sha256,
and let the rest go. ~20 KB replaces 34 MB.
"""
from __future__ import annotations
import hashlib, json, pathlib, shutil, sys

REPO = pathlib.Path(r"E:\2026-AI4S\autoresearch")
BACKUP = REPO / "keystroke-observatory-PRE-REBUILD-BACKUP-20261012-181735"
OUT = REPO / "evidence" / "v1_superseded" / "v1_pages_snapshot"

WANTED = ["src/pages/index.md", "src/pages/participants.md", "src/pages/sessions.md",
          "src/data/keystroke.js", "README.md", "observable.config.js"]

def main() -> int:
    if not BACKUP.exists():
        print(f"  [SKIP] {BACKUP.name} is already gone")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for rel in WANTED:
        src = BACKUP / rel
        if not src.exists():
            print(f"  [MISS] {rel}")
            continue
        dst = OUT / rel.replace("/", "__")
        shutil.copy2(src, dst)
        manifest[rel] = {"sha256": hashlib.sha256(dst.read_bytes()).hexdigest(),
                         "bytes": dst.stat().st_size,
                         "line_count": len(dst.read_text(encoding="utf-8",
                                                        errors="replace").splitlines())}
        print(f"  kept {rel:28} -> {dst.name}  ({dst.stat().st_size:,} B, "
              f"{manifest[rel]['line_count']} lines)")
    (OUT / "MANIFEST.json").write_text(json.dumps({
        "_why": ("The pre-rebuild backup held these files and nothing else did. "
                 "HANDOVER_AUDIT.md cites line numbers in them, so they are kept "
                 "verbatim; the remaining 34 MB was redundant with _legacy_v1."),
        "source": BACKUP.name, "files": manifest}, indent=2), encoding="utf-8")
    total = sum(f.stat().st_size for f in OUT.iterdir())
    print(f"\n  snapshot total: {total:,} B  (replaces 34.2 MB)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
