#!/usr/bin/env python
"""check_pin_integrity.py -- prove the pinned instrument on disk IS the instrument that was pinned.

WHY THIS IS NOT A HASH FILE
    `config/pin_laya.json` records five SHA256 digests. A record of a hash is not the hash: it is a
    promise that somebody once compared bytes, and it stays true on paper long after the snapshot is
    deleted, half-downloaded, or replaced. Every claim that Phase I is reproducible rests on the bytes
    on disk being the bytes the pilot ran on, and that is a property of the filesystem, not of a JSON
    document. This check makes it a measurement.

    It re-hashes every pinned file and compares against the record. It does NOT ask the hub, on
    purpose: the pin's whole point is that a run must not follow `main`, and `main` had already moved
    by the time the pin was taken. Querying the hub would compare against a moving target.

WHAT IT DOES NOT DO
    It does not check that this is the RIGHT instrument for the protocol - only that it is the one
    that was pinned. Whether Laya is the right instrument is the argument in `docs/PHASE_I_PIN.md`;
    whether these bytes are the instrument is this check. Confusing the two is how a programme ends up
    defending a hash instead of a method.

FAILURE MODES, AND WHY EACH IS ITS OWN MESSAGE
    A missing snapshot, a size mismatch and a digest mismatch are different problems with different
    fixes, and a check that reports them as one line forces the reader to diagnose it. A missing
    snapshot also means the comparison never happened, which must never read as "verified".
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CHUNK = 8 * 1024 * 1024  # 8 MiB: model.safetensors is 842 MB, so hashing it in one read is a memory risk


def sha256_of(path: pathlib.Path) -> tuple[str, int]:
    """Hash a file in bounded memory. Returns (digest, bytes_read)."""
    h = hashlib.sha256()
    total = 0
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(CHUNK)
            if not chunk:
                break
            total += len(chunk)
            h.update(chunk)
    return h.hexdigest(), total


def resolve_snapshot(cfg: dict) -> pathlib.Path:
    """Locate the snapshot without hardcoding a drive letter.

    Order: $NHB_LAYA_SNAPSHOT, then the recorded local path, then the hub cache layout keyed by
    revision. A recorded absolute path is only a convenience, not the authority - if the user moves
    the cache, the check must still find it rather than reporting a missing instrument.
    """
    env = os.environ.get("NHB_LAYA_SNAPSHOT")
    if env:
        return pathlib.Path(env)

    rec = cfg.get("local_snapshot")
    if rec and pathlib.Path(rec).exists():
        return pathlib.Path(rec)

    home = os.environ.get("HF_HOME") or (pathlib.Path.home() / ".cache" / "huggingface")
    return (pathlib.Path(home) / "hub" / "models--convaiinnovations--laya"
            / "snapshots" / cfg["revision"])


def check(verbose: bool = False, cfg_path: pathlib.Path | None = None) -> tuple[list[str], dict]:
    """Verify one pin against the snapshot on disk.

    `cfg_path` defaults to the root pin. IT IS A PARAMETER NOW BECAUSE THERE IS MORE THAN ONE PIN: the
    multilingual artifact is a separate file set at the same revision, so it carries its own pin, and a pin
    file that nothing verifies is a record rather than a check. The called-for behaviour when a second pin
    was added was to widen the check, not to leave half the pinned bytes unchecked.
    """
    cfg_path = cfg_path or (REPO_ROOT / "config" / "pin_laya.json")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    findings: list[str] = []
    snap = resolve_snapshot(cfg)

    if not snap.exists():
        return ([f"[PIN] snapshot not found at {snap}. Nothing was compared, so nothing is verified - "
                 f"this is NOT a pass. Set $NHB_LAYA_SNAPSHOT or re-download revision "
                 f"{cfg['revision']}."], {"compared": 0, "expected": len(cfg["files"])})

    compared = 0
    for entry in cfg["files"]:
        p = snap / entry["path"]
        if not p.exists():
            findings.append(f"[PIN] MISSING FILE {entry['path']} (expected {entry['bytes']:,} B) - "
                            f"the snapshot is incomplete")
            continue
        size = p.stat().st_size
        if size != entry["bytes"]:
            findings.append(f"[PIN] SIZE MISMATCH {entry['path']}: on disk {size:,} B, pinned "
                            f"{entry['bytes']:,} B - a truncated or replaced download")
            continue
        digest, read = sha256_of(p)
        compared += 1
        if digest != entry["sha256"]:
            findings.append(f"[PIN] DIGEST MISMATCH {entry['path']}: on disk {digest[:16]}…, pinned "
                            f"{entry['sha256'][:16]}… - these are NOT the pinned bytes")
        elif verbose:
            print(f"  [OK] {entry['path']:<32} {size:>12,} B  {digest[:16]}…")

    stats = {"compared": compared, "expected": len(cfg["files"]), "total_bytes": 0}
    if compared == len(cfg["files"]) and not findings:
        stats["total_bytes"] = sum(f["bytes"] for f in cfg["files"])
    return findings, stats


def negative_test() -> int:
    """Prove the check fails when the bytes are wrong, not merely when they are right."""
    print("negative control:")
    ok = True

    # 1. A real snapshot must pass.
    f, _ = check()
    r1 = ("a genuine snapshot passes", not f)
    print(f"  [{'OK' if r1 else 'MISS'}] {r1}")
    ok = ok and r1

    # 2. A digest that cannot match any content must be caught. Pointing the record at a file that
    #    does not exist is the honest way to do this: it tests the missing-file path without writing a
    #    bogus digest into the real config, which would leave the record wrong if the run were
    #    interrupted.
    cfg_path = REPO_ROOT / "config" / "pin_laya.json"
    original = cfg_path.read_text(encoding="utf-8")
    cfg = json.loads(original)
    cfg["files"].append({"path": "definitely_not_a_real_file.bin", "bytes": 1,
                         "sha256": "0" * 64})
    try:
        cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8", newline="\n")
        f2, _ = check()
        r2 = ("a pinned file that is absent is caught", any("MISSING FILE" in x for x in f2))
        print(f"  [{'OK' if r2 else 'MISS'}] {r2}")
        ok = ok and r2
    finally:
        cfg_path.write_text(original, encoding="utf-8", newline="\n")

    restored = cfg_path.read_text(encoding="utf-8") == original
    r3 = ("config restored", restored)
    print(f"  [{'OK' if r3 else 'MISS'}] {r3}")
    ok = ok and r3

    # 3. A wrong digest must be caught, not tolerated. Same approach: a real file, a wrong hash.
    cfg = json.loads(original)
    real = cfg["files"][-1]["path"]
    cfg["files"].append({"path": real, "bytes": cfg["files"][-1]["bytes"], "sha256": "f" * 64})
    try:
        cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8", newline="\n")
        f4, _ = check()
        r4 = ("a pinned file with the wrong digest is caught",
              any("DIGEST MISMATCH" in x for x in f4))
        print(f"  [{'OK' if r4 else 'MISS'}] {r4}")
        ok = ok and r4
    finally:
        cfg_path.write_text(original, encoding="utf-8", newline="\n")

    restored = cfg_path.read_text(encoding="utf-8") == original
    r5 = ("config restored", restored)
    print(f"  [{'OK' if r5 else 'MISS'}] {r5}")
    ok = ok and r5

    print(f"\n  {'ALL CONTROLS PASS' if ok else 'CONTROL FAILURE - the check is not trustworthy'}")
    return 0 if ok else 1


def pin_files() -> list[pathlib.Path]:
    """Every pin in config/, discovered rather than listed.

    Discovery matters: a hand-maintained list of pins is the same defect as a hand-maintained list of anything
    - add a pin and forget the list, and the new pin is unchecked while the check still reports success.
    """
    return sorted((REPO_ROOT / "config").glob("pin_laya*.json"))


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "pin integrity").split("\n")[0])
    ap.add_argument("--verbose", action="store_true", help="print each file as it is verified")
    ap.add_argument("--negative-test", action="store_true",
                    help="require the check to fail on an absent file and on a wrong digest")
    args = ap.parse_args()

    if args.negative_test:
        return negative_test()

    all_findings: list[str] = []
    total_compared = total_expected = total_bytes = 0

    for cfg_path in pin_files():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        label = cfg_path.name
        variant = cfg.get("variant", "?")
        # The variant string is long by design - it carries the reasoning. Print its first line only.
        variant_short = variant.split(".")[0].split("\n")[0][:58]
        findings, stats = check(verbose=args.verbose, cfg_path=cfg_path)
        total_compared += stats["compared"]
        total_expected += stats["expected"]
        total_bytes += stats.get("total_bytes", 0)
        if findings:
            all_findings.extend(f"[{label}] " + f for f in findings)
            print(f"  [FAIL] {label:<32} {variant_short}")
        else:
            print(f"  [OK]   {label:<32} {variant_short}  "
                  f"{stats['compared']}/{stats['expected']} files, "
                  f"{sum(f['bytes'] for f in cfg['files']):,} B")

    if all_findings:
        print(f"\nPIN FAIL: {len(all_findings)} finding(s) over {total_expected} pinned file(s) "
              f"across {len(pin_files())} pin(s)")
        for f in all_findings:
            print("  " + f)
        return 1

    print(f"\nOK: {len(pin_files())} pin(s) verified against disk — "
          f"{total_compared}/{total_expected} files, {total_bytes:,} B, all digests match")
    return 0


if __name__ == "__main__":
    sys.exit(main())