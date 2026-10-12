"""Extract the keystroke corpus from the USB-hosted zip onto local NVMe.

Why: E: is a USB-attached disk (BusType USB). The pipeline's workers each read a
different region of the corpus concurrently, which thrashes USB random access --
CPU sat at 8% with no progress for 17 minutes. Reading the single zip file
sequentially and writing to NVMe removes that bottleneck entirely.
"""
import json, sys, time, zipfile
from pathlib import Path

ZIP = Path(r"E:\2026-AI4S\autoresearch\external-data\136Mkeystrokes\Keystrokes.zip")
DEST = Path(r"C:\keystroke-corpus\files")

def main() -> int:
    if not ZIP.exists():
        print(f"zip not found: {ZIP}", file=sys.stderr); return 2
    DEST.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    written = skipped = 0
    with zipfile.ZipFile(ZIP) as z:
        names = [n for n in z.namelist() if n.endswith("_keystrokes.txt")]
        total = len(names)
        print(f"entries: {total:,} -> {DEST}", flush=True)
        for i, name in enumerate(names, 1):
            target = DEST / Path(name).name
            if target.exists() and target.stat().st_size > 0:
                skipped += 1
            else:
                with z.open(name) as src, open(target, "wb") as dst:
                    dst.write(src.read())
                written += 1
            if i % 20000 == 0 or i == total:
                el = time.time() - t0
                print(f"  {i:,}/{total:,}  written={written:,} skipped={skipped:,}  "
                      f"{el/60:.1f} min  {i/max(el,1e-9):,.0f}/s", flush=True)
    print(json.dumps({"dest": str(DEST), "entries": total, "written": written,
                      "skipped": skipped, "seconds": round(time.time()-t0,1)}, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
