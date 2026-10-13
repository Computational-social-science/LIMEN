#!/usr/bin/env python
"""build_data_manifest.py -- measure every external dataset on disk and record what was found.

WHY A SCRIPT RATHER THAN A TABLE SOMEONE TYPED
    A dataset's size, record count and licence are the provenance of every number later computed from it, so
    they cannot be recalled from a conversation. This walks the external-data tree, MEASURES each file, and
    writes the result next to the data. Re-running it after a re-download is the check that the bytes are the
    bytes: a manifest written by hand is a claim, and a manifest regenerated from disk is a measurement.

WHAT IT DOES NOT DO
    It does not download anything and it does not judge scientific suitability - that judgement is in
    config/datasets.json, which this manifest supplies figures to. A file whose dataset is `simulated` is
    measured here exactly like any other; the ADMISSIBILITY question lives in the declaration and its guard.

RUN
    python scripts/build_data_manifest.py            # write the manifest
    python scripts/build_data_manifest.py --check    # fail if it differs from disk (used by the guard suite)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
# Data is not committed, but the project's OWN external-data is the canonical copy;
# the parent's is a fallback for a checkout that keeps its data elsewhere.
EXTERNAL = next(
    (p for p in (REPO_ROOT / "external-data", REPO_ROOT.parent / "external-data")
     if p.is_dir()),
    REPO_ROOT / "external-data")
MANIFEST = REPO_ROOT / "config" / "data_manifest.json"


def sha256_of(path: pathlib.Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def count_jsonl(path: pathlib.Path) -> dict:
    """Count records and, when the records carry a `category`, count by category."""
    n = 0
    bad = 0
    cats: dict[str, int] = {}
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n += 1
            try:
                obj = json.loads(line)
            except Exception:
                bad += 1
                continue
            c = obj.get("category")
            if c:
                cats[c] = cats.get(c, 0) + 1
    out: dict[str, object] = {"records": n, "unparseable": bad}
    if cats:
        out["by_category"] = dict(sorted(cats.items(), key=lambda kv: -kv[1]))
    return out


def count_tsv(path: pathlib.Path, label_col: int = 0) -> dict:
    """CSCD format: `label \\t origin \\t corrected`, label 1 = the sentence carries an error."""
    rows = 0
    labels: dict[str, int] = {}
    bad = 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            rows += 1
            parts = line.split("\t")
            if len(parts) < 3:
                bad += 1
                continue
            labels[parts[label_col]] = labels.get(parts[label_col], 0) + 1
    out: dict = {"rows": rows, "unparseable": bad}
    if labels:
        out["by_label"] = dict(sorted(labels.items()))
        err = labels.get("1", 0)
        out["share_labelled_error"] = round(err / rows, 4) if rows else None
    return out


def count_birkbeck(path: pathlib.Path) -> dict:
    """A `$word` header followed by that word's misspellings, one per line."""
    words = misspellings = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("$"):
            words += 1
        elif line.strip():
            misspellings += 1
    return {"correct_words": words, "misspellings": misspellings}


def measure() -> dict:
    out: dict = {"_why": "Measured from disk by scripts/build_data_manifest.py; regenerate rather than edit.",
                 "root": "${EXTERNAL_DATA_ROOT}", "datasets": {}}
    if not EXTERNAL.exists():
        out["status"] = f"external-data root not found at {EXTERNAL.name}/ (expected as a sibling of this repo)"
        return out

    ds = out["datasets"]

    bb = EXTERNAL / "birkbeck"
    if bb.is_dir():
        files = {}
        for p in sorted(bb.glob("*.dat")):
            entry = {"bytes": p.stat().st_size, "sha256": sha256_of(p)}
            if p.name in ("missp.dat", "holbrook-missp.dat", "aspell.dat", "wikipedia.dat"):
                entry |= count_birkbeck(p)
            files[p.name] = entry
        ds["birkbeck"] = {"role": "English primary and additional observed sources", "files": files}

    jw = EXTERNAL / "jwtd" / "jwtd"
    if jw.is_dir():
        files = {}
        for p in sorted(jw.glob("*.jsonl")):
            files[p.name] = {"bytes": p.stat().st_size, "sha256": sha256_of(p)} | count_jsonl(p)
        ds["jwtd"] = {"role": "Japanese primary", "files": files}

    cs = EXTERNAL / "cscd"
    if cs.is_dir():
        found = sorted(p for p in cs.rglob("*") if p.is_file())
        files = {}
        for p in found:
            entry: dict = {"bytes": p.stat().st_size, "sha256": sha256_of(p)}
            if p.suffix == ".tsv":
                entry |= count_tsv(p)
            files[p.name] = entry
        ds["cscd"] = {"role": "Chinese primary", "files": files,
                      "status": "empty" if not found else "present"}

    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="fail if the committed manifest differs from what is on disk now")
    args = ap.parse_args()

    fresh = measure()
    text = json.dumps(fresh, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not MANIFEST.exists():
            print(f"  [FAIL] {MANIFEST.relative_to(REPO_ROOT)} is missing; run build_data_manifest.py")
            return 1
        have = MANIFEST.read_text(encoding="utf-8")
        if have != text:
            print("  [FAIL] the manifest no longer matches the data on disk. Either the data changed under it,")
            print("         or the manifest was edited by hand. Re-run scripts/build_data_manifest.py and")
            print("         report what changed - do not hand-patch it.")
            return 1
        n = sum(len(d.get("files", {})) for d in fresh["datasets"].values())
        print(f"  [OK]   data manifest matches disk across {len(fresh['datasets'])} dataset(s), {n} file(s)")
        return 0

    MANIFEST.write_text(text, encoding="utf-8")
    print(f"  wrote {MANIFEST.relative_to(REPO_ROOT)}")
    for name, d in fresh["datasets"].items():
        n = len(d.get("files", {}))
        tot = sum(f.get("bytes", 0) for f in d.get("files", {}).values())
        print(f"    {name:<12} {n} file(s)  {tot:>14,} B  {d.get('status','')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
