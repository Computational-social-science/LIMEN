"""Archive the v1 evidence into a DURABLE, tracked location before deletion.

WHY THIS STEP EXISTS
The removal the owner asked for cannot be a bare delete, because the v1 artefacts
are the evidence a written audit cites, and most of them are NOT in git anywhere:

  data/processed/keystroke_stats/keystroke_session_stats.parquet   17.2 MB  untracked
  _legacy_v1/.../public/keystroke_session_stats.parquet            17.2 MB  untracked
  _legacy_v1/gh.msi + gh.zip                                       26.6 MB  untracked

HANDOVER_AUDIT.md asserts "157,314 rows; 0 backspaces; 114,683,620 keystrokes;
88,249 edits; the v1 parquet is 17,162,399 bytes". Delete those files and every
one of those claims becomes unverifiable -- the audit would cite evidence that no
longer exists. That is precisely the failure CURRENT_OBJECT.md records for R1,
where "the R1 archival moved the files and left the authority document promising
them".

So: keep what a claim needs, in a form small enough to track, and drop what
nothing needs.

WHAT IS KEPT (tracked, ~200 KB)
  * the v1 Parquet's SCHEMA and its full column statistics, as JSON -- enough to
    re-verify every number the audit states, without the 17 MB payload
  * the sha256 of the v1 Parquet, so identity is checkable
  * the row count, null counts, and the two defect signatures (0 backspaces;
    157,314 rows = one per participant FILE)

WHAT IS DROPPED
  * the 17 MB v1 Parquet (twice), the 26.6 MB GitHub installers, the stale
    embedded dist/, the v1 Python package, the deployment scripts, the two stray
    redirect fragments, and the pre-rebuild tree copy.
"""
from __future__ import annotations
import hashlib, json, pathlib, shutil, sys
import pandas as pd

REPO = pathlib.Path(__file__).resolve().parents[1]
OUT = REPO / "evidence" / "v1_superseded"
V1 = REPO / "data" / "processed" / "keystroke_stats" / "keystroke_session_stats.parquet"

def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    if not V1.exists():
        print(f"  [SKIP] {V1} is already gone; nothing to archive")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"reading {V1} ({V1.stat().st_size:,} B) ...")
    df = pd.read_parquet(V1)

    # 1) the defect signatures the audit states, recomputed here so they are not
    #    copied from the audit (a claim verified against its own source proves nothing)
    sig = {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "participants_distinct": int(df["participant_id"].nunique()),
        "total_keystrokes": int(df["n_keystrokes"].sum()),
        "total_backspaces": int(df["n_backspace"].sum()),
        "total_edits": int(df["edits"].sum()),
        "rows_equal_participants": bool(len(df) == df["participant_id"].nunique()),
        "parquet_bytes": V1.stat().st_size,
        "parquet_sha256": sha256(V1),
    }
    (OUT / "v1_defect_signatures.json").write_text(
        json.dumps(sig, indent=2), encoding="utf-8")

    # 2) schema + per-column summary: enough to re-derive every headline number
    cols = []
    for c in df.columns:
        s = df[c]
        entry = {"name": c, "dtype": str(s.dtype), "nulls": int(s.isna().sum())}
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            entry.update({"min": float(s.min()), "max": float(s.max()),
                          "mean": float(s.mean()), "sum": float(s.sum())})
        else:
            # `top_letters` holds dicts per row; nunique() cannot hash them, and a
            # dict column has no useful cardinality anyway. Record the shape instead.
            try:
                entry["n_unique"] = int(s.nunique())
            except TypeError:
                entry["n_unique"] = None
                entry["note"] = "unhashable (per-row object); cardinality not computed"
        cols.append(entry)
    (OUT / "v1_column_summary.json").write_text(
        json.dumps({"rows": len(df), "columns": cols}, indent=2), encoding="utf-8")

    # 3) a few raw rows, so the schema claim is checkable without the payload
    # 3 rows is what the schema claim needs. Values are TRUNCATED because
    # `top_letters` is a per-row dict whose string form is ~200 KB a row: the full
    # head was 1.0 MB of payload masquerading as evidence. The truncation is
    # recorded in the file so a reader knows the sample is abridged.
    head = []
    for rec in df.head(3).astype(str).to_dict(orient="records"):
        head.append({k: (v[:160] + "...[truncated]" if len(v) > 160 else v)
                     for k, v in rec.items()})
    (OUT / "v1_sample_rows.json").write_text(json.dumps({"_note": "values truncated to 160 chars", "rows": head}, indent=2), encoding="utf-8")

    for f in sorted(OUT.iterdir()):
        print(f"  wrote {f.name}  {f.stat().st_size:,} B")
    print(f"\n  v1 sha256 : {sig['parquet_sha256']}")
    print(f"  rows={sig['rows']:,}  backspaces={sig['total_backspaces']}  "
          f"rows==participants: {sig['rows_equal_participants']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
