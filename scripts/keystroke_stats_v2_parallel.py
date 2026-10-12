#!/usr/bin/env python
"""Chunked parallel driver for keystroke_stats_v2.

Submitting one future per corpus file (168,593) costs more in IPC than the
parsing itself, so the corpus is split into a few hundred chunks; each worker
writes its own Parquet part and they are concatenated once at the end.
"""
from __future__ import annotations

import argparse, hashlib, json, os, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from keystroke_stats_v2 import CORPUS, ZIP, process_file  # noqa: E402

# Published values (Dhakal et al., CHI 2018, Table 3, "All" column; means only).
PAPER = {
    "wpm_mean": 51.56,
    "iki_mean_ms": 238.66,
    "keypress_duration_mean_ms": 116.25,
    "uncorrected_error_rate_pct": 1.167,
    "error_corrections_pct": 6.31,
    "kspc_mean": 1.173,
    "participants": 168960,
    "keystrokes": 136857600,
}


def run_chunk(args):
    index, paths, parts_dir = args
    rows, malformed, unreadable = [], 0, 0
    for p in paths:
        res = process_file(p)
        malformed += res["malformed"]
        if res["error"]:
            unreadable += 1
        rows.extend(res["rows"])
    if rows:
        pd.DataFrame(rows).to_parquet(Path(parts_dir) / f"part-{index:05d}.parquet",
                                      compression="zstd", index=False)
    return {"index": index, "files": len(paths), "rows": len(rows),
            "malformed": malformed, "unreadable": unreadable}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 4))
    ap.add_argument("--chunks-per-worker", type=int, default=4)
    ap.add_argument("--outdir", type=Path,
                    default=Path(r"E:\2026-AI4S\autoresearch\data\processed\keystroke_stats_v2"))
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    files = sorted(str(p) for p in CORPUS.glob("*_keystrokes.txt"))
    if args.limit:
        files = files[: args.limit]
    if not files:
        print("no corpus files found", file=sys.stderr)
        return 2

    outdir: Path = args.outdir
    parts = outdir / "parts"
    if parts.exists():
        for old in parts.glob("*.parquet"):
            old.unlink()
    parts.mkdir(parents=True, exist_ok=True)

    n_chunks = max(args.workers, args.workers * args.chunks_per_worker)
    size = max(1, (len(files) + n_chunks - 1) // n_chunks)
    chunks = [(i, files[i * size:(i + 1) * size], str(parts))
              for i in range((len(files) + size - 1) // size)]

    print(f"files   : {len(files):,}\nworkers : {args.workers}\n"
          f"chunks  : {len(chunks):,} (~{size:,} files each)\noutput  : {outdir}", flush=True)
    t0 = time.time()
    malformed = unreadable = rows_total = 0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for n, res in enumerate(ex.map(run_chunk, chunks), 1):
            malformed += res["malformed"]
            unreadable += res["unreadable"]
            rows_total += res["rows"]
            el = time.time() - t0
            if n % 10 == 0 or n == len(chunks):
                done_files = min(n * size, len(files))
                print(f"  chunk {n}/{len(chunks)}  files={done_files:,}  rows={rows_total:,}  "
                      f"{el/60:.1f} min  eta {(len(files)-done_files)/max(done_files/el,1e-9)/60:.1f} min",
                      flush=True)

    print("concatenating parts ...", flush=True)
    df = pd.concat([pd.read_parquet(p) for p in sorted(parts.glob("*.parquet"))],
                   ignore_index=True)
    order = ["participant_id", "test_section_id", "file_name", "n_sections_in_file"]
    df = df[order + [c for c in df.columns if c not in order]]
    df = df.sort_values(["participant_id", "test_section_id"], kind="stable").reset_index(drop=True)

    parquet = outdir / "keystroke_section_stats.parquet"
    df.to_parquet(parquet, compression="zstd", index=False)

    elapsed = time.time() - t0
    manifest = {
        "schema_version": 2,
        "unit_of_analysis": "(participant_id, test_section_id) - one transcribed sentence",
        "replaces": "keystroke_session_stats.parquet (v1: one participant FILE per row)",
        "metric_source": "Dhakal, Feit, Kristensson & Oulasvirta, CHI 2018, p.4 Performance Measures",
        "corpus_root": str(CORPUS),
        "corpus_zip": str(ZIP),
        "corpus_zip_sha256": hashlib.sha256(ZIP.read_bytes()).hexdigest() if ZIP.exists() else None,
        "files_processed": len(files),
        "files_unreadable": unreadable,
        "malformed_rows_skipped": malformed,
        "sections": int(len(df)),
        "participants": int(df["participant_id"].nunique()),
        "columns": list(df.columns),
        "elapsed_seconds": round(elapsed, 1),
        "workers": args.workers,
        "python": sys.version.split()[0],
        "pandas": pd.__version__,
        "parquet_sha256": hashlib.sha256(parquet.read_bytes()).hexdigest(),
        "parquet_bytes": parquet.stat().st_size,
    }
    (outdir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    summary = {
        "sections": int(len(df)),
        "participants": int(df["participant_id"].nunique()),
        "total_keystrokes": int(df["n_keystrokes"].sum()),
        "total_backspaces": int(df["n_backspace"].sum()),
        "total_deletes": int(df["n_delete"].sum()),
        "sections_exact_match_pct": round(100 * float(df["is_exact_match"].mean()), 2),
        "wpm_mean": round(float(df["wpm"].mean()), 2),
        "wpm_median": round(float(df["wpm"].median()), 2),
        "wpm_sd": round(float(df["wpm"].std()), 2),
        "iki_mean_of_means_ms": round(float(df["iki_mean_ms"].mean()), 2),
        "keypress_duration_mean_of_means_ms": round(float(df["keypress_duration_mean_ms"].mean()), 2),
        "uncorrected_error_rate_mean_pct": round(100 * float(df["uncorrected_error_rate"].mean()), 3),
        "error_corrections_mean_pct": round(float(df["error_corrections_pct"].mean()), 2),
        "kspc_mean": round(float(df["kspc"].mean()), 4),
    }
    summary["paper_comparison"] = {
        "wpm_mean": {"ours": summary["wpm_mean"], "paper": PAPER["wpm_mean"]},
        "iki_mean_ms": {"ours": summary["iki_mean_of_means_ms"], "paper": PAPER["iki_mean_ms"]},
        "keypress_duration_mean_ms": {"ours": summary["keypress_duration_mean_of_means_ms"],
                                      "paper": PAPER["keypress_duration_mean_ms"]},
        "uncorrected_error_rate_pct": {"ours": summary["uncorrected_error_rate_mean_pct"],
                                       "paper": PAPER["uncorrected_error_rate_pct"]},
        "error_corrections_pct": {"ours": summary["error_corrections_mean_pct"],
                                  "paper": PAPER["error_corrections_pct"]},
        "kspc_mean": {"ours": summary["kspc_mean"], "paper": PAPER["kspc_mean"]},
    }
    (outdir / "SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
