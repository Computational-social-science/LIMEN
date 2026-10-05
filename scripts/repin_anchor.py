#!/usr/bin/env python
"""repin_anchor.py -- recompute the anchor's identity after an intentional edit to the protocol.

WHY THIS IS A SCRIPT AND NOT A RECIPE
    `config/anchor.json` records the protocol's sha256, byte count, line count and VERSION, and the
    consistency guard compares all four against the file. Re-pinning by hand has now been done four
    times in this project and was done wrong once - the hash was updated and the version was not, and
    the guard then reported a mismatch that looked like a protocol defect rather than a bookkeeping
    one. A five-line recipe that must be remembered is a five-line recipe that will eventually be
    misremembered; this is the same operation with the order fixed.

WHAT IT DOES NOT DO
    It does not decide WHETHER the protocol should change. It records a change that has already been
    made and reviewed. Running it on a protocol whose content nobody has read is how the anchor stops
    meaning anything - so it prints the version transition and refuses if the header's version does not
    parse, rather than guessing.

WHY THE VERSION IS READ FROM THE DOCUMENT
    The version lives in three places - the header, §14 and the end marker - and the consistency guard
    requires all three to agree. Reading the header and writing it into the anchor keeps the anchor
    subordinate to the document: the protocol states what it is, and the record follows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROTOCOL = REPO_ROOT / "protocol" / "NHB_Orthographic_Channels_JEV_Research_Protocol.md"
ANCHOR = REPO_ROOT / "config" / "anchor.json"


def read_version(text: str) -> str:
    m = re.search(r"\*\*Version:\*\*\s*([0-9]+\.[0-9]+)", text)
    if not m:
        raise SystemExit("cannot read the version from the protocol header - refusing to guess it")
    return m.group(1)


def read_version_markers(text: str) -> dict:
    """The three places the consistency guard compares."""
    out = {"header": read_version(text)}
    m = re.search(r"\|\s*Version\s*\|\s*\*\*([0-9]+\.[0-9]+)\*\*\s*\|", text)
    out["section_14"] = m.group(1) if m else None
    m = re.search(r"End of protocol v([0-9]+\.[0-9]+)", text)
    out["end_marker"] = m.group(1) if m else None
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "repin").split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="report what would change, write nothing")
    args = ap.parse_args()

    raw = PROTOCOL.read_bytes()
    text = PROTOCOL.read_text(encoding="utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    markers = read_version_markers(text)

    cfg = json.loads(ANCHOR.read_text(encoding="utf-8"))
    before = {k: cfg.get(k) for k in ("sha256", "bytes", "lines", "version")}

    consistent = len({v for v in markers.values() if v}) == 1
    if not consistent:
        print(f"[FAIL] the protocol's own version markers disagree: {markers}")
        print("       fix the document before re-pinning it - the anchor must not encode a confusion.")
        return 1

    new = {
        "sha256": digest,
        "bytes": len(raw),
        "lines": len(text.splitlines()),
        "version": markers["header"],
    }
    cfg.update(new)
    cfg["version_consistency"] = {
        "header": markers["header"],
        "section_14": markers["section_14"],
        "end_marker": markers["end_marker"],
        "consistent": True,
    }

    print(f"  protocol : {PROTOCOL.name}")
    print(f"  version  : {before['version']} -> {new['version']}"
          + ("   (unchanged)" if before["version"] == new["version"] else "   <- BUMPED"))
    print(f"  sha256   : {str(before['sha256'])[:16]}... -> {digest[:16]}...")
    print(f"  bytes    : {before['bytes']} -> {new['bytes']}")
    print(f"  lines    : {before['lines']} -> {new['lines']}")

    if args.dry_run:
        print("\n  --dry-run: nothing written")
        return 0

    ANCHOR.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8", newline="\n")
    print(f"\n  anchor re-pinned: {ANCHOR.relative_to(REPO_ROOT)}")
    print("  next: rebuild the manuscript so its stamp carries the new hash, then run the guards.")
    return 0


if __name__ == "__main__":
    sys.exit(main())