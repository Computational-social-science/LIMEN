#!/usr/bin/env python
"""Keystroke statistics v2 -- correct unit of analysis AND paper-faithful metrics.

WHY THIS REPLACES scripts/keystroke_stats_pipeline.py
-----------------------------------------------------
v1 treated ONE RAW FILE as ONE SESSION. A corpus file holds ONE participant but
exactly 15 sentences (TEST_SECTION_ID), and SENTENCE/USER_INPUT are constant
within a section. v1 took the first section's text (.iloc[0]) yet computed
IKI/hold/duration/WPM across all 15 concatenated, so its "sessions" were really
participant files and its timing mixed inter-sentence gaps into inter-key
intervals.

This version emits ONE ROW PER (participant_id, test_section_id) and computes
every statistic WITHIN a section.

Metric definitions follow Dhakal, Feit, Kristensson & Oulasvirta, CHI 2018
("Observations on Typing from 136 Million Keystrokes"), p.4 "Performance
Measures", quoted so the choices are auditable:

  WPM      "calculated for each typed sentence as the length of the string
           transcribed (in words, where one word consists of any five
           characters) divided by the time from the first to the last keypress"
           -> words = len(USER_INPUT)/5 ; span = last PRESS_TIME - first PRESS_TIME

           TIME BASIS: first press -> last RELEASE (see active_ms below). The
           paper's prose says "last keypress", but its published AVG_WPM_15 is
           reproduced by the release basis.

           CAUTION -- per-sentence WPM is NOT directly comparable to the paper's
           headline. The paper's own `metadata_participants.txt` ships AVG_WPM_15,
           and the arithmetic that reproduces it (r = 0.9999) is POOLED over the
           participant: sum(words over the 15 sentences) / sum(typing time).
           Averaging the 15 per-sentence WPM values instead is biased upward
           (54.3 vs 49.2 on a 250-file sample) because a short sentence with a
           fast rate carries the same weight as a long one. Per-sentence `wpm`
           and `active_ms`/`typed_chars` are therefore both emitted, so the
           pooled figure is reconstructible: sum(typed_chars)/5 divided by
           sum(active_ms).
  IKI      "the difference in timestamps between two keypress events. For
           IKI-based analysis, we removed keystrokes that were typed more than
           5000 ms after the previous keystroke."
           -> press-to-press; IKIs > 5000 ms are EXCLUDED from IKI statistics
              and counted separately (iki_gt_5s)
  KEYPRESS DURATION
           "how long a key is kept pressed, computed as the difference in
           timestamps between the key-down and key-up events" -> RELEASE - PRESS
           (the paper never says "hold time"; rollover makes it overlap with IKI)
           Rows where RELEASE < PRESS (a corrupt timestamp, ~1 in 175,000) are
           excluded from this metric and counted in
           keypress_duration_invalid_rows -- one such row would otherwise drive a
           whole section's mean negative.
  UNCORRECTED ERROR RATE
           "the Levenshtein edit distance between the string presented and the
           transcribed string, divided by the larger number of characters
           between the two strings"
           -> Levenshtein(SENTENCE, USER_INPUT) / max(len(SENTENCE), len(USER_INPUT))
  ERROR CORRECTIONS (%)
           "the percentage of keypresses using the Backspace (BKSP) or Delete
           (DEL) key during typing" -> 100*(n_bksp + n_del)/n_keystrokes
           NOTE: the paper gives NO formula for a "corrected error rate"; this
           is the measure it actually publishes, and it is named accordingly.
  KSPC     keystrokes per character -> n_keystrokes / len(USER_INPUT)

Participant-level exclusions from the paper (p.4) are NOT applied here; they are
recorded as flags (flag_error_gt_25pct, flag_iki_gt_50s) so the section file
stays complete and the filtered view is reproducible downstream.

Data-integrity handling (observed, not assumed):
  * tab-separated with NO quoting; text contains apostrophes, so the default CSV
    quotechar corrupts rows -> quoting=QUOTE_NONE
  * ~1 file in 200 is not valid UTF-8 -> encoding_errors='replace'
  * a few rows carry 10 fields instead of 9 -> skipped and COUNTED
  * keys are identified by KEYCODE; LETTER uses 'BKSP' (never 'BACKSPACE'),
    and is sometimes empty, so LETTER is not used for key identification

READ-ONLY on the corpus. Writes only to the output directory.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from rapidfuzz.distance import Levenshtein

# Corpus location. E: is a USB-attached disk; concurrent random reads from many
# workers thrash it (observed: CPU 8%, no progress for 17 min). The NVMe copy is
# preferred when present; override with KEYSTROKE_CORPUS.
def _corpus_root() -> Path:
    """Preferred corpus root: env override, then NVMe copy, then the USB original.

    `Path("")` resolves to "." which IS a directory, so an unset/blank override
    must be filtered out explicitly rather than by truthiness.
    """
    override = os.environ.get("KEYSTROKE_CORPUS", "").strip()
    candidates = []
    if override:
        candidates.append(Path(override))
    candidates.append(Path(r"C:\keystroke-corpus\files"))
    candidates.append(Path(r"E:\2026-AI4S\autoresearch\external-data\Keystrokes\Keystrokes\files"))
    for candidate in candidates:
        if candidate.is_dir() and any(candidate.glob("*_keystrokes.txt")):
            return candidate
    return candidates[-1]


CORPUS = _corpus_root()
# The corpus archive. Note the two candidate paths: the extracted tree lives under
# Keystrokes/, but the archive itself is the 136Mkeystrokes/ copy. Hashing a
# non-existent path silently produced corpus_zip_sha256: null before.
_ZIP_CANDIDATES = [
    Path(r"E:\2026-AI4S\autoresearch\external-data\136Mkeystrokes\Keystrokes.zip"),
    Path(r"E:\2026-AI4S\autoresearch\external-data\Keystrokes\Keystrokes.zip"),
]
ZIP = next((z for z in _ZIP_CANDIDATES if z.is_file()), _ZIP_CANDIDATES[0])
OUTDIR = Path(r"E:\2026-AI4S\autoresearch\data\processed\keystroke_stats_v2")

COLS = ["PARTICIPANT_ID", "TEST_SECTION_ID", "SENTENCE", "USER_INPUT",
        "KEYSTROKE_ID", "PRESS_TIME", "RELEASE_TIME", "LETTER", "KEYCODE"]

KC_BACKSPACE, KC_TAB, KC_ENTER = 8, 9, 13
KC_SHIFT, KC_CTRL, KC_ALT, KC_CAPSLOCK, KC_ESC = 16, 17, 18, 20, 27
KC_SPACE, KC_DELETE = 32, 46
MODIFIER_CODES = {KC_SHIFT, KC_CTRL, KC_ALT, KC_CAPSLOCK, KC_ESC, 91, 92}
NON_CHAR_CODES = MODIFIER_CODES | {KC_BACKSPACE, KC_DELETE, KC_ENTER, KC_TAB}

IKI_OUTLIER_MS = 5000      # paper: IKIs above this are excluded from IKI analysis
IKI_DISTRACTED_MS = 50000  # paper: participant exclusion signal
ERROR_EXCLUDE = 0.25       # paper: exclude participants with error rate > 25%

# Mis-decoded punctuation seen when UTF-8 text is read as cp1252; normalised so
# alignment measures typing, not encoding.
MOJIBAKE = {"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
            "\u2014": "-", "\u2013": "-", "\u00a0": " ", "\u2026": "..."}


def clean(text: str) -> str:
    for bad, good in MOJIBAKE.items():
        text = text.replace(bad, good)
    return text


def repair_rows(text: str):
    """Rebuild logical 9-field rows from a participant file.

    Two corpus quirks break a naive line-per-row read, both observed:

    * **LETTER is sometimes a literal newline** (an ENTER keystroke written as a
      real ``\\n``). The row is then split across two physical lines -- the first
      ends after RELEASE_TIME, the second is ``"\\t13"``. Concatenating the pair
      restores one 9-field row. Without this, pandas fails the int cast on the
      empty PARTICIPANT_ID and **aborts the entire file**, which silently
      dropped 113 participants (168,480 instead of 168,593).
    * **LETTER is sometimes a literal tab**, producing 10 fields with an empty
      field in the LETTER region. Those rows are collapsed back to 9.

    Returns ``(rows, repaired_split, repaired_extra, trailing_partial)``.
    """
    lines = text.splitlines()
    # The first line is the column header and must NOT be treated as data.
    rows, buf = [], None
    split_fixed = extra_fixed = 0
    for line in lines[1:]:
        joined = buf is not None
        buf = line if buf is None else buf + line
        n = buf.count("\t") + 1
        if n == 9:
            if joined:
                split_fixed += 1
            rows.append(buf)
            buf = None
        elif n > 9:
            parts = buf.split("\t")
            # Keep the first seven columns, the LETTER column, and the final
            # KEYCODE; interior empties are the artefact.
            rows.append("\t".join(parts[:7] + [parts[7], parts[-1]]))
            extra_fixed += 1
            buf = None
    trailing = buf is not None
    return rows, split_fixed, extra_fixed, trailing


def read_section_file(path: Path):
    """Parse one participant file. Returns (DataFrame|None, malformed_row_count)."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, 0
    physical = text.splitlines()
    rows, split_fixed, extra_fixed, trailing = repair_rows(text)
    if not rows:
        return None, max(0, len(physical) - 1)
    try:
        df = pd.read_csv(
            io.StringIO("\n".join(rows)),
            sep="\t", names=COLS, header=None,
            quoting=csv.QUOTE_NONE, na_filter=False,
            dtype={"PARTICIPANT_ID": "int64", "TEST_SECTION_ID": "int64",
                   "KEYSTROKE_ID": "int64", "PRESS_TIME": "int64",
                   "RELEASE_TIME": "int64", "KEYCODE": "int32"},
            engine="c", on_bad_lines="skip",
        )
    except Exception:
        return None, max(0, len(physical) - 1)
    if df.empty:
        return None, max(0, len(physical) - 1)
    # Physical lines consumed beyond one-per-row: the split-row repairs, plus any
    # trailing fragment that never completed a row.
    # Rows that actually needed repair, plus any trailing fragment. Counting
    # physical lines instead (the old behaviour) over-reports, because
    # str.splitlines() also breaks on \x0b \x0c \x1c-\x1e \x85 \u2028 \u2029,
    # which occur INSIDE LETTER fields in this corpus.
    malformed = split_fixed + extra_fixed + (1 if trailing else 0)
    return df, max(0, malformed)


def _dist_stats(a: np.ndarray) -> dict:
    if a.size == 0:
        return {"mean": 0.0, "std": 0.0, "median": 0.0, "q25": 0.0,
                "q75": 0.0, "p95": 0.0, "max": 0.0}
    return {"mean": float(np.mean(a)), "std": float(np.std(a)),
            "median": float(np.median(a)),
            "q25": float(np.percentile(a, 25)), "q75": float(np.percentile(a, 75)),
            "p95": float(np.percentile(a, 95)), "max": float(np.max(a))}


def section_stats(g: pd.DataFrame) -> dict:
    """Every statistic for ONE sentence/section, computed within the section."""
    g = g.sort_values("PRESS_TIME", kind="stable")
    pt = g["PRESS_TIME"].to_numpy(dtype="int64")
    rt = g["RELEASE_TIME"].to_numpy(dtype="int64")
    kc = g["KEYCODE"].to_numpy(dtype="int64")

    target = clean(str(g["SENTENCE"].iloc[0]))
    produced = clean(str(g["USER_INPUT"].iloc[0]))

    # ---- timing, strictly within this sentence ----
    iki_raw = np.diff(pt)
    iki = iki_raw[iki_raw <= IKI_OUTLIER_MS]          # paper's IKI filter
    iki_excluded = int(np.sum(iki_raw > IKI_OUTLIER_MS))
    kpd_raw = rt - pt                                  # keypress duration
    # A small number of rows record a RELEASE before their own PRESS (~1 in
    # 175,000 rows; 4 of 290,830 sampled). The delta is then a large negative
    # number, and because it enters a MEAN, a single bad row poisons the whole
    # section: the worst observed section mean was -1,450.8 ms from one -46,986 ms
    # row. Those rows are unusable for this metric, so they are EXCLUDED and
    # counted (never clamped, which would silently bias the mean downward).
    kpd_valid_mask = kpd_raw >= 0
    kpd = kpd_raw[kpd_valid_mask]
    kpd_invalid = int(np.sum(~kpd_valid_mask))
    span_ms = int(pt[-1] - pt[0]) if pt.size else 0    # first press -> last press
    # WPM time basis. The paper's prose says "first to the last keypress", but its
    # published per-participant AVG_WPM_15 is reproduced by first press -> last
    # RELEASE: ratio 1.0021 vs 1.0137 on a 400-file sample (both r ~ 0.9999).
    # The release basis is therefore used for WPM; the press-only span is kept as
    # `span_ms` for reference so the two readings stay separable.
    # Robust span: max release minus min press. Using rt[-1] (the release of the
    # LAST-PRESSED key) is not safe -- a handful of rows in this corpus record a
    # release before its own press (4 of 290,830 sampled, 0.0014%), which can put
    # the last row's release INSIDE the sentence and even make the span negative
    # (observed minimum -302 ms). rt.max() - pt.min() is immune to that and
    # matches the authors' AVG_WPM_15 just as well (ratio 1.0016 vs 1.0021).
    active_ms = int(rt.max() - pt.min()) if pt.size else 0

    iki_s, kpd_s = _dist_stats(iki), _dist_stats(kpd)

    # ---- key counts by physical key ----
    n_keys = int(len(g))
    n_backspace = int(np.sum(kc == KC_BACKSPACE))
    n_delete = int(np.sum(kc == KC_DELETE))
    n_printable = int(np.sum(~np.isin(kc, list(NON_CHAR_CODES))))

    # ---- paper-faithful metrics ----
    words = len(produced) / 5.0
    wpm = (words / (active_ms / 60000.0)) if active_ms > 0 else 0.0

    lev = Levenshtein.distance(target, produced)
    err_denom = max(len(target), len(produced))
    uncorrected = (lev / err_denom) if err_denom > 0 else 0.0

    # Error corrections. The paper's PROSE says "percentage of keypresses", but
    # its PUBLISHED value (6.31%, SD 4.48) is per CHARACTER -- confirmed against
    # the corpus authors' own metadata_participants.txt, whose `ECPC` column
    # ("Error Corrections per Character") reproduces 6.31 exactly as 100*ECPC.
    # Both are emitted so the discrepancy is visible rather than hidden:
    #   error_corrections_pct            -> per character (comparable to 6.31)
    #   error_corrections_per_key_pct    -> per keypress (the prose definition)
    n_corr = n_backspace + n_delete
    error_corrections_pct = (100.0 * n_corr / len(produced)) if produced else 0.0
    error_corrections_per_key_pct = (100.0 * n_corr / n_keys) if n_keys else 0.0
    kspc = (n_keys / len(produced)) if produced else 0.0

    return {
        "sentence_length": len(target),
        "user_input_length": len(produced),
        "n_keystrokes": n_keys,
        "n_printable": n_printable,
        "n_backspace": n_backspace,
        "n_delete": n_delete,
        "n_modifier": int(np.sum(np.isin(kc, list(MODIFIER_CODES)))),
        "levenshtein_edits": int(lev),
        "uncorrected_error_rate": uncorrected,
        "error_corrections_pct": error_corrections_pct,
        "error_corrections_per_key_pct": error_corrections_per_key_pct,
        "kspc": kspc,
        "is_exact_match": bool(produced == target),
        "wpm": wpm,
        "typed_chars": len(produced),
        "active_ms": active_ms,
        "span_ms": span_ms,
        "duration_s": span_ms / 1000.0,
        "iki_mean_ms": iki_s["mean"], "iki_std_ms": iki_s["std"],
        "iki_median_ms": iki_s["median"], "iki_q25_ms": iki_s["q25"],
        "iki_q75_ms": iki_s["q75"], "iki_p95_ms": iki_s["p95"],
        "iki_max_ms": iki_s["max"],
        # Unfiltered maximum, so the paper's >50 s "distracted participant"
        # condition is actually computable. `iki_max_ms` cannot serve: it is
        # capped at IKI_OUTLIER_MS by construction.
        "iki_max_unfiltered_ms": float(np.max(iki_raw)) if iki_raw.size else 0.0,
        "iki_gt_5s": iki_excluded,
        "keypress_duration_mean_ms": kpd_s["mean"],
        "keypress_duration_std_ms": kpd_s["std"],
        "keypress_duration_median_ms": kpd_s["median"],
        "keypress_duration_invalid_rows": kpd_invalid,
        "target_sha1": hashlib.sha1(target.encode("utf-8")).hexdigest()[:16],
    }


def section_flags(rows):
    """Participant-level exclusion signals the paper applies (p.4).

    Emitted as flags rather than applied, so the section table stays complete and
    the filtered view is reproducible downstream. This is what the module
    docstring has always promised.
    """
    if not rows:
        return
    # Both flags are PARTICIPANT-level: the paper excludes a participant who
    # trips the condition in any sentence. Computed from the real thresholds --
    # IKI_DISTRACTED_MS was previously defined and never used, which made
    # `flag_iki_gt_50s` a duplicate of the 5 s filter.
    err_flagged = any(r["uncorrected_error_rate"] > ERROR_EXCLUDE for r in rows)
    iki_flagged = any(r["iki_max_unfiltered_ms"] > IKI_DISTRACTED_MS for r in rows)
    for r in rows:
        r["flag_error_gt_25pct"] = err_flagged
        r["flag_iki_gt_50s"] = iki_flagged
    return None


def process_file(path_str: str):
    path = Path(path_str)
    df, malformed = read_section_file(path)
    if df is None:
        return {"file": path.name, "rows": [], "malformed": malformed, "error": "unreadable"}
    rows = []
    n_sec = int(df["TEST_SECTION_ID"].nunique())
    pid = int(df["PARTICIPANT_ID"].iloc[0])
    for sec_id, g in df.groupby("TEST_SECTION_ID", sort=False):
        rec = section_stats(g)
        rec["participant_id"] = pid
        rec["test_section_id"] = int(sec_id)
        rec["file_name"] = path.name
        rec["n_sections_in_file"] = n_sec
        rows.append(rec)
    section_flags(rows)
    return {"file": path.name, "rows": rows, "malformed": malformed, "error": None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    ap.add_argument("--outdir", type=Path, default=OUTDIR)
    ap.add_argument("--sample-seed", type=int, default=None)
    args = ap.parse_args()

    files = sorted(CORPUS.glob("*_keystrokes.txt"))
    if not files:
        print(f"no corpus files under {CORPUS}", file=sys.stderr)
        return 2
    if args.limit:
        if args.sample_seed is None:
            files = files[: args.limit]
        else:
            import random
            random.seed(args.sample_seed)
            files = sorted(random.sample(files, args.limit))

    outdir: Path = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    print(f"corpus  : {CORPUS}\nfiles   : {len(files):,}\nworkers : {args.workers}\noutput  : {outdir}")
    t0 = time.time()

    all_rows, malformed_total, unreadable, done = [], 0, 0, 0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(process_file, str(f)): f for f in files}
        for fut in as_completed(futs):
            res = fut.result()
            done += 1
            malformed_total += res["malformed"]
            if res["error"]:
                unreadable += 1
            all_rows.extend(res["rows"])
            if done % 5000 == 0 or done == len(files):
                el = time.time() - t0
                print(f"  {done:,}/{len(files):,}  {done/el:,.0f} files/s", flush=True)

    df = pd.DataFrame(all_rows)
    if df.empty:
        print("no sections produced", file=sys.stderr)
        return 3

    order = ["participant_id", "test_section_id", "file_name", "n_sections_in_file"]
    df = df[order + [c for c in df.columns if c not in order]]
    df = df.sort_values(["participant_id", "test_section_id"], kind="stable").reset_index(drop=True)

    parquet = outdir / "keystroke_section_stats.parquet"
    df.to_parquet(parquet, compression="zstd", index=False)

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
        "malformed_rows_skipped": malformed_total,
        "sections": int(len(df)),
        "participants": int(df["participant_id"].nunique()),
        "columns": list(df.columns),
        "elapsed_seconds": round(time.time() - t0, 1),
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
        "iki_mean_of_means_ms": round(float(df["iki_mean_ms"].mean()), 1),
        "keypress_duration_mean_of_means_ms": round(float(df["keypress_duration_mean_ms"].mean()), 1),
        "uncorrected_error_rate_mean_pct": round(100 * float(df["uncorrected_error_rate"].mean()), 3),
        "error_corrections_mean_pct": round(float(df["error_corrections_pct"].mean()), 2),
        "kspc_mean": round(float(df["kspc"].mean()), 3),
    }
    (outdir / "SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
