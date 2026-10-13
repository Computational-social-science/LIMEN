"""Add the ROW-LEVEL facts the audit cites, from the surviving v1 copy.

The audit states two values that are properties of a single row, not of a column:
  * `iki_max_ms` for participant 100001 = 16,344 ms (the cross-sentence gap that
    exposed the v1 unit error)
  * `test_section_id` for that row = 1090979, `sentence_length` = 43

A column summary cannot answer those, which is why the handoff gate reported them
UNVERIFIED after the main Parquet was deleted. The second copy under `_legacy_v1`
still has them, so they are archived now rather than left unverifiable.

This runs BEFORE any decision about that second copy: archive first, delete later.
"""
from __future__ import annotations
import hashlib, json, pathlib, sys
import pandas as pd

REPO = pathlib.Path(r"E:\2026-AI4S\autoresearch")
V1B = (REPO / "keystroke-observatory" / "_legacy_v1" / "keystroke_observatory"
       / "dist" / "public" / "keystroke_session_stats.parquet")
OUT = REPO / "evidence" / "v1_superseded"

def main() -> int:
    if not V1B.exists():
        print(f"  [SKIP] {V1B} is gone; the row facts cannot be recovered from it")
        return 0
    df = pd.read_parquet(V1B)
    rec = df[df["participant_id"] == 100001]
    if rec.empty:
        print("  [FAIL] participant 100001 is not in this copy")
        return 1
    r = rec.iloc[0]
    # The row the audit's 16,344 ms comes from, plus its neighbours for context
    ctx = df[df["participant_id"].isin([100001, 100003, 100007])]
    facts = {
        "_why": ("Row-level facts the audit cites, which a column summary cannot "
                 "answer. Archived before any deletion of the second v1 copy."),
        "source_copy": str(V1B.relative_to(REPO)),
        "source_sha256": hashlib.sha256(V1B.read_bytes()).hexdigest(),
        "participant_100001": {
            "test_section_id": int(r["test_section_id"]),
            "sentence_length": int(r["sentence_length"]),
            "iki_max_ms": float(r["iki_max_ms"]),
            "iki_mean_ms": float(r["iki_mean_ms"]),
            "total_time_ms": int(r["total_time_ms"]),
            "n_keystrokes": int(r["n_keystrokes"]),
            "n_backspace": int(r["n_backspace"]),
            "wpm": float(r["wpm"]),
            "file_name": str(r["file_name"]),
        },
        "context_rows": ctx.to_dict(orient="records"),
    }
    (OUT / "v1_row_facts.json").write_text(json.dumps(facts, indent=2, default=str),
                                           encoding="utf-8")
    print(f"  wrote v1_row_facts.json  ({len(ctx)} context rows)")
    print(f"  participant 100001: iki_max_ms = {r['iki_max_ms']:.0f}  "
          f"test_section_id = {int(r['test_section_id'])}  "
          f"sentence_length = {int(r['sentence_length'])}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
