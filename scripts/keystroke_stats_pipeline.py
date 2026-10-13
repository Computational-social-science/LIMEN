#!/usr/bin/env python
"""
Keystroke Statistics Pipeline — Dask Parallel Processing
==========================================================
Processes the 136M Keystrokes dataset (160,863 TSV files) in parallel using Dask.
Computes per-session statistics: WPM, IKI mean/var/quantiles, error rate, backspace count, etc.
Outputs per-session summary as Parquet (columnar, compressed) and aggregated JSON.

READ-ONLY on original data. Outputs to separate directory.
"""

import dask.dataframe as dd
import dask
from dask.diagnostics import ProgressBar
import pandas as pd
import numpy as np
import json
import pathlib
import argparse
import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────

INPUT_ROOT = Path(r"E:\2026-AI4S\autoresearch\external-data\Keystrokes\Keystrokes\files")
OUTPUT_DIR = Path(r"E:\2026-AI4S\autoresearch\data\processed\keystroke_stats")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PARQUET_OUT = OUTPUT_DIR / "keystroke_session_stats.parquet"
JSON_OUT = OUTPUT_DIR / "keystroke_aggregated_stats.json"
SCHEMA_OUT = OUTPUT_DIR / "schema.json"

# Dask configuration
N_WORKERS = 8  # adjust based on CPU cores
PARTITION_SIZE = "128MiB"  # target partition size for Dask

# ──────────────────────────────────────────────────────────────────────────────
# COLUMN SPECIFICATION
# ──────────────────────────────────────────────────────────────────────────────

# Expected columns in the TSV files
EXPECTED_COLUMNS = [
    "PARTICIPANT_ID", "TEST_SECTION_ID", "SENTENCE", "USER_INPUT",
    "KEYSTROKE_ID", "PRESS_TIME", "RELEASE_TIME", "LETTER", "KEYCODE"
]

DTYPES = {
    "PARTICIPANT_ID": "int32",
    "TEST_SECTION_ID": "int32",
    "SENTENCE": "object",
    "USER_INPUT": "object",
    "KEYSTROKE_ID": "int64",
    "PRESS_TIME": "int64",
    "RELEASE_TIME": "int64",
    "LETTER": "object",
    "KEYCODE": "int32",
}

# ──────────────────────────────────────────────────────────────────────────────
# PER-FILE STATISTICS COMPUTATION
# ──────────────────────────────────────────────────────────────────────────────

def compute_session_stats(df: pd.DataFrame) -> dict:
    """
    Compute statistics for a single session (one TSV file).
    All computations are vectorized pandas operations.
    """
    if df.empty:
        return {}
    
    # Basic identifiers
    participant_id = df["PARTICIPANT_ID"].iloc[0]
    test_section_id = df["TEST_SECTION_ID"].iloc[0]
    sentence = df["SENTENCE"].iloc[0]
    user_input = df["USER_INPUT"].iloc[0]
    
    # ─── Timing ───
    press_times = df["PRESS_TIME"].values
    release_times = df["RELEASE_TIME"].values
    
    # Inter-keystroke intervals (IKI) in milliseconds
    iki = np.diff(press_times)  # press_time[i+1] - press_time[i]
    hold_times = release_times - press_times
    
    # ─── Speed ───
    # Total time from first press to last release (ms)
    total_time_ms = release_times[-1] - press_times[0] if len(release_times) > 0 else 0
    
    # Characters typed (excluding SHIFT, etc.)
    char_keystrokes = df[~df["LETTER"].isin(["SHIFT", "CTRL", "ALT", "CAPSLOCK", "BACKSPACE", "DELETE", "ENTER", "TAB"])]
    n_chars = len(char_keystrokes)
    
    # Words = characters / 5 (standard)
    words = n_chars / 5.0
    wpm = (words / (total_time_ms / 60000.0)) if total_time_ms > 0 else 0
    
    # ─── IKI Statistics ───
    if len(iki) > 0:
        iki_mean = float(np.mean(iki))
        iki_std = float(np.std(iki))
        iki_median = float(np.median(iki))
        iki_q25 = float(np.percentile(iki, 25))
        iki_q75 = float(np.percentile(iki, 75))
        iki_min = float(np.min(iki))
        iki_max = float(np.max(iki))
    else:
        iki_mean = iki_std = iki_median = iki_q25 = iki_q75 = iki_min = iki_max = 0.0
    
    # ─── Hold Time Statistics ───
    if len(hold_times) > 0:
        hold_mean = float(np.mean(hold_times))
        hold_std = float(np.std(hold_times))
        hold_median = float(np.median(hold_times))
    else:
        hold_mean = hold_std = hold_median = 0.0
    
    # ─── Error Analysis ───
    # Backspace count
    n_backspace = int((df["LETTER"] == "BACKSPACE").sum())
    n_delete = int((df["LETTER"] == "DELETE").sum())
    
    # Error rate: Levenshtein distance between USER_INPUT and SENTENCE
    # Normalized by target length
    try:
        import difflib
        matcher = difflib.SequenceMatcher(None, sentence, user_input)
        # Count substitutions, insertions, deletions
        edits = 0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                edits += (i2 - i1)
            elif tag == 'delete':
                edits += (i2 - i1)
            elif tag == 'insert':
                edits += (j2 - j1)
        error_rate = edits / max(len(sentence), 1)
    except Exception:
        error_rate = 0.0
        edits = 0
    
    # ─── Letter-level statistics ───
    # Most frequent letters
    letter_counts = df["LETTER"].value_counts()
    top_letters = letter_counts.head(10).to_dict()
    
    # ─── Session duration ───
    session_duration_s = total_time_ms / 1000.0
    
    return {
        "participant_id": int(participant_id),
        "test_section_id": int(test_section_id),
        "sentence_length": len(sentence),
        "user_input_length": len(user_input),
        "n_keystrokes": len(df),
        "n_chars": n_chars,
        "n_backspace": n_backspace,
        "n_delete": n_delete,
        "edits": edits,
        "error_rate": error_rate,
        "wpm": wpm,
        "total_time_ms": int(total_time_ms),
        "session_duration_s": session_duration_s,
        "iki_mean_ms": iki_mean,
        "iki_std_ms": iki_std,
        "iki_median_ms": iki_median,
        "iki_q25_ms": iki_q25,
        "iki_q75_ms": iki_q75,
        "iki_min_ms": iki_min,
        "iki_max_ms": iki_max,
        "hold_mean_ms": hold_mean,
        "hold_std_ms": hold_std,
        "hold_median_ms": hold_median,
        "top_letters": top_letters,
    }


def process_file(filepath: Path) -> dict:
    """Read a single TSV file and compute statistics."""
    try:
        # Read with pandas - these are small files (~100-150 KB each)
        df = pd.read_csv(
            filepath,
            sep="\t",
            dtype=DTYPES,
            usecols=lambda c: c in EXPECTED_COLUMNS,
            engine="c",
            na_filter=False,
        )
        stats = compute_session_stats(df)
        stats["file_name"] = filepath.name
        return stats
    except Exception as e:
        return {"file_name": filepath.name, "error": str(e)}


# ──────────────────────────────────────────────────────────────────────────────
# DASK PIPELINE
# ──────────────────────────────────────────────────────────────────────────────

def build_file_list() -> list:
    """Get list of all TSV files to process."""
    files = list(INPUT_ROOT.glob("*_keystrokes.txt"))
    return files


def run_dask_pipeline(files: list, n_workers: int = N_WORKERS) -> pd.DataFrame:
    """
    Process all files using Dask delayed for parallel execution.
    Returns a pandas DataFrame with all session statistics.
    """
    from dask import delayed
    from dask.distributed import Client, LocalCluster, progress
    import multiprocessing as mp
    
    # Use local cluster for true parallelism
    cluster = LocalCluster(
        n_workers=n_workers,
        threads_per_worker=1,
        processes=True,
        memory_limit="4GB",
        silence_logs=False,
    )
    client = Client(cluster)
    print(f"Dask dashboard: {client.dashboard_link}")
    
    try:
        # Create delayed tasks
        delayed_tasks = [delayed(process_file)(f) for f in INPUT_ROOT.glob("*_keystrokes.txt")]
        print(f"Created {len(delayed_tasks)} delayed tasks")
        
        # Compute with progress bar
        results = client.compute(delayed_tasks, sync=True)
        print("All tasks completed")
        
        # Filter successful results
        valid_results = [r for r in results if "error" not in r]
        error_results = [r for r in results if "error" in r]
        
        if error_results:
            print(f"Errors in {len(error_results)} files:")
            for e in error_results[:5]:
                print(f"  {e['file_name']}: {e['error']}")
        
        # Convert to DataFrame
        df = pd.DataFrame(valid_results)
        return df
        
    finally:
        client.close()
        cluster.close()


def save_outputs(df: pd.DataFrame):
    """Save results as Parquet and aggregated JSON."""
    
    # Parquet - columnar, compressed, schema preserved
    df.to_parquet(PARQUET_OUT, compression="snappy", index=False)
    print(f"Parquet saved: {PARQUET_OUT} ({PARQUET_OUT.stat().st_size / 1024 / 1024:.1f} MB)")
    
    # Schema
    schema = {col: str(dtype) for col, dtype in df.dtypes.items()}
    SCHEMA_OUT.write_text(json.dumps(schema, indent=2))
    print(f"Schema saved: {SCHEMA_OUT}")
    
    # Aggregated statistics (across all sessions)
    agg = {
        "n_sessions": len(df),
        "n_participants": int(df["participant_id"].nunique()),
        "total_keystrokes": int(df["n_keystrokes"].sum()),
        "total_chars": int(df["n_chars"].sum()),
        "total_backspaces": int(df["n_backspace"].sum()),
        "total_deletes": int(df["n_delete"].sum()),
        "total_edits": int(df["edits"].sum()),
        "wpm": {
            "mean": float(df["wpm"].mean()),
            "std": float(df["wpm"].std()),
            "median": float(df["wpm"].median()),
            "q25": float(df["wpm"].quantile(0.25)),
            "q75": float(df["wpm"].quantile(0.75)),
        },
        "error_rate": {
            "mean": float(df["error_rate"].mean()),
            "std": float(df["error_rate"].std()),
            "median": float(df["error_rate"].median()),
        },
        "iki_ms": {
            "mean": float(df["iki_mean_ms"].mean()),
            "std": float(df["iki_std_ms"].mean()),
            "median": float(df["iki_median_ms"].median()),
        },
        "hold_ms": {
            "mean": float(df["hold_mean_ms"].mean()),
            "median": float(df["hold_median_ms"].median()),
        },
        "session_duration_s": {
            "mean": float(df["session_duration_s"].mean()),
            "std": float(df["session_duration_s"].std()),
            "median": float(df["session_duration_s"].median()),
        },
        "participants": df["participant_id"].value_counts().to_dict(),
    }
    
    JSON_OUT.write_text(json.dumps(agg, indent=2))
    print(f"Aggregated JSON saved: {JSON_OUT}")


# ──────────────────────────────────────────────────────────────────────────────
# ALTERNATIVE: PURE PANDAS + JOBLIB (SIMPLER, NO DASK OVERHEAD)
# ──────────────────────────────────────────────────────────────────────────────

def run_joblib_pipeline(files: list, n_jobs: int = N_WORKERS) -> pd.DataFrame:
    """
    Alternative using joblib for parallel processing - often faster for
    many small files because it avoids Dask scheduler overhead.
    """
    from joblib import Parallel, delayed
    
    print(f"Processing {len(files)} files with {n_jobs} workers...")
    
    results = Parallel(n_jobs=n_jobs, verbose=10, backend="multiprocessing")(
        delayed(process_file)(f) for f in files
    )
    
    valid_results = [r for r in results if "error" not in r]
    error_results = [r for r in results if "error" in r]
    
    if error_results:
        print(f"Errors in {len(error_results)} files")
        for e in error_results[:5]:
            print(f"  {e['file_name']}: {e['error']}")
    
    df = pd.DataFrame(valid_results)
    return df


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Keystroke statistics pipeline")
    parser.add_argument("--engine", choices=["dask", "joblib"], default="joblib",
                        help="Parallel engine (joblib is faster for many small files)")
    parser.add_argument("--workers", type=int, default=N_WORKERS, help="Number of workers")
    parser.add_argument("--limit", type=int, default=None, help="Limit files for testing")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Keystroke Statistics Pipeline")
    print("=" * 60)
    print(f"Input: {INPUT_ROOT}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Engine: {args.engine}")
    print(f"Workers: {args.workers}")
    
    # Get file list
    all_files = list(INPUT_ROOT.glob("*_keystrokes.txt"))
    print(f"Found {len(all_files)} files")
    
    if args.limit:
        all_files = all_files[:args.limit]
        print(f"Limited to {len(all_files)} files for testing")
    
    # Process
    if args.engine == "dask":
        df = run_dask_pipeline(all_files, n_workers=args.workers)
    else:
        df = run_joblib_pipeline(all_files, n_jobs=args.workers)
    
    print(f"\nProcessed {len(df)} sessions successfully")
    print(f"Columns: {list(df.columns)}")
    print(f"Shape: {df.shape}")
    
    # Save
    save_outputs(df)
    
    # Quick summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Sessions processed: {len(df)}")
    print(f"Participants: {df['participant_id'].nunique()}")
    print(f"Total keystrokes: {df['n_keystrokes'].sum():,}")
    print(f"Total chars: {df['n_chars'].sum():,}")
    print(f"Total backspaces: {df['n_backspace'].sum():,}")
    print(f"WPM (mean): {df['wpm'].mean():.1f}")
    print(f"Error rate (mean): {df['error_rate'].mean():.4f}")
    print(f"IKI mean (ms): {df['iki_mean_ms'].mean():.1f}")


if __name__ == "__main__":
    main()