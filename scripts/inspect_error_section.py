"""Read one section that contains a corrected error, with every relevant column side by side.

The column contract is still open. `LETTER` reproduces the target in only 60 of 375 sections,
and about 12% of rows carry an empty `LETTER`, and the empty rows fall on the most frequent
English characters -- which is not a property of a missing character. Printing a section that
visibly contains a corrected error, with `SENTENCE`, `USER_INPUT` and the per-keystroke
`LETTER` aligned, decides the contract in one read.

Column sets differ between participant files, so every column is looked up by name and an
absent one is simply not printed. A positional read raised KeyError on the first file, which
is why the lookup is defensive.
"""
from __future__ import annotations

import pathlib
import zipfile

ZIP = pathlib.Path("external-data/136Mkeystrokes/Keystrokes.zip")
COLS = ("TEST_SECTION_ID", "SENTENCE", "USER_INPUT", "LETTER", "KEYCODE",
        "PRESS_TIME", "RELEASE_TIME", "KEYSTROKE_ID", "PARTICIPANT_ID")


def main(want: int = 3) -> None:
    with zipfile.ZipFile(ZIP) as Z:
        names = sorted(n for n in Z.namelist() if n.endswith("_keystrokes.txt"))
        found = 0
        for nm in names:
            rows = Z.read(nm).decode("utf-8", "replace").splitlines()
            hdr = rows[0].split("\t")
            i = {k: hdr.index(k) for k in COLS if k in hdr}
            n = len(hdr)
            recs = [L.split("\t") for L in rows[1:] if len(L.split("\t")) == n]
            sec = None
            cur: list = []
            target = produced = ""
            for p in list(recs) + [None]:
                sid = p[i["TEST_SECTION_ID"]] if p is not None else None
                if sid != sec:
                    if sec is not None and cur and any(r[i["LETTER"]] == "\b" for r in cur):
                        print("=" * 78)
                        print("FILE %s  SECTION %s" % (nm.split("/")[-1], sec))
                        print("  columns   : %s" % sorted(i))
                        print("  SENTENCE  : %r" % target)
                        print("  USER_INPUT: %r" % produced)
                        print("  keystrokes:")
                        for k, r in enumerate(cur[:24]):
                            kid = r[i["KEYSTROKE_ID"]] if "KEYSTROKE_ID" in i else str(k)
                            print("    id=%10s code=%3s LETTER=%-7r press=%s rel=%s"
                                  % (kid, r[i["KEYCODE"]], r[i["LETTER"]],
                                     r[i["PRESS_TIME"]], r[i["RELEASE_TIME"]]))
                        found += 1
                    if p is None:
                        break
                    sec = sid
                    target = p[i["SENTENCE"]]
                    produced = p[i["USER_INPUT"]]
                    cur = []
                if p is None:
                    continue
                cur.append(p)
            if found >= want:
                break
        print()
        print("printed %d section(s) containing a backspace" % found)


if __name__ == "__main__":
    main()
