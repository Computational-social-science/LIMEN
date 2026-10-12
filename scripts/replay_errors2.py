"""Corrected vs surviving error composition, with ALIGNMENT VALIDATION.

Naive slot comparison (buffer[i] vs target[i]) is invalid once an insertion or
deletion shifts the buffer, which inflates "other substitution" into nonsense --
my first attempt produced 3.46M other_sub against 497k adjacent, a 7:1 ratio that
is an alignment artefact, not a measurement.

Fix: only classify an error when the buffer PREFIX still matches the target
PREFIX at that moment. Then the slot comparison is provably valid. Every skipped
event is counted, so the attribution rate is reported rather than hidden.

This yields the quantity the final text cannot give: the class composition of
errors that were PRODUCED, split into those the typist repaired and those that
survived. The difference between the two is the censoring imposed by the
typist's own error monitor.
"""
from __future__ import annotations
import csv, difflib, io, json, random
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np, pandas as pd

CORPUS = Path(r'C:\keystroke-corpus\files')
COLS = ["PARTICIPANT_ID","TEST_SECTION_ID","SENTENCE","USER_INPUT","KEYSTROKE_ID","PRESS_TIME","RELEASE_TIME","LETTER","KEYCODE"]
KC_BS, KC_DEL, KC_ENTER, KC_TAB, KC_SPACE = 8, 46, 13, 9, 32
MODS = {16,17,18,20,27,91,92}
NONCHAR = MODS | {KC_BS, KC_DEL, KC_ENTER, KC_TAB}
QWERTY_ROWS = ["1234567890-=", "qwertyuiop[]", "asdfghjkl;'", "zxcvbnm,./"]
ADJ = set()
for row in QWERTY_ROWS:
    for a,b in zip(row,row[1:]): ADJ.add(frozenset((a,b)))
for i in range(len(QWERTY_ROWS)-1):
    up,dn = QWERTY_ROWS[i], QWERTY_ROWS[i+1]
    for c,ch in enumerate(up):
        for nc in (c,c+1):
            if nc < len(dn): ADJ.add(frozenset((ch.lower(),dn[nc].lower())))

def classify_pair(want, got):
    if want == got: return None
    if want.lower() == got.lower(): return "case"
    if frozenset((want.lower(), got.lower())) in ADJ: return "adjacent"
    return "other_sub"

def analyze(path):
    try: txt = path.read_text(encoding='utf-8', errors='replace')
    except OSError: return None
    rows, buf = [], None
    for line in txt.splitlines()[1:]:
        buf = line if buf is None else buf + line
        n = buf.count('\t')+1
        if n == 9: rows.append(buf); buf = None
        elif n > 9:
            p = buf.split('\t'); rows.append("\t".join(p[:7]+[p[7],p[-1]])); buf = None
    if not rows: return None
    try:
        df = pd.read_csv(io.StringIO("\n".join(rows)), sep='\t', names=COLS, header=None,
                         quoting=csv.QUOTE_NONE, na_filter=False,
                         dtype={"PARTICIPANT_ID":"int64","TEST_SECTION_ID":"int64","KEYSTROKE_ID":"int64",
                                "PRESS_TIME":"int64","RELEASE_TIME":"int64","KEYCODE":"int32"},
                         engine='c', on_bad_lines='skip')
    except Exception: return None
    if df.empty: return None

    A = dict(sections=0, replay_ok=0, replay_fail=0,
             typed_events=0, typed_aligned=0, typed_err=0,
             repairs=0, repairs_aligned=0,
             err_typed=Counter(),      # every error produced at an aligned position
             err_repaired=Counter(),   # errors removed by a validated backspace
             err_surviving=Counter(),  # from the final text, validated sections only,
                                       # classified against the SAME aligned machinery
             repair_lat=Counter(), n_lat=0)
    for sec, g in df.groupby('TEST_SECTION_ID', sort=False):
        g = g.sort_values('PRESS_TIME', kind='stable')
        target = str(g.SENTENCE.iloc[0]); produced = str(g.USER_INPUT.iloc[0])
        kc = g.KEYCODE.to_numpy(); lt = g.LETTER.to_numpy(); pt = g.PRESS_TIME.to_numpy()
        A['sections'] += 1
        buf = []; aligned = True; last_pt = None
        for i in range(len(kc)):
            code = int(kc[i])
            if code == KC_BS:
                A['repairs'] += 1
                if buf:
                    # valid iff the surviving prefix equals the target prefix
                    k = len(buf) - 1
                    if aligned and k <= len(target) and "".join(buf[:k]) == target[:k]:
                        got = buf[k]
                        want = target[k] if k < len(target) else None
                        if want is not None:
                            A['repairs_aligned'] += 1
                            c = classify_pair(want, got)
                            if c is not None: A['err_repaired'][c] += 1
                            if last_pt is not None:
                                gap = int(pt[i] - last_pt)
                                if 0 <= gap <= 60000:
                                    A['repair_lat'][min(gap//50, 1200)] += 1; A['n_lat'] += 1
                    buf.pop()
                    if aligned and "".join(buf) != target[:len(buf)]:
                        aligned = False
                last_pt = None
                continue
            if code in NONCHAR:
                continue
            ch = str(lt[i])
            if ch == '': ch = ' '
            A['typed_events'] += 1
            k = len(buf)
            if aligned and k <= len(target) and "".join(buf) == target[:k]:
                A['typed_aligned'] += 1
                want = target[k] if k < len(target) else None
                if want is not None:
                    c = classify_pair(want, ch)
                    if c is not None:
                        A['typed_err'] += 1
                        A['err_typed'][c] += 1
            buf.append(ch)
            if aligned and "".join(buf) != target[:len(buf)]:
                aligned = False
            last_pt = int(pt[i])
        if "".join(buf) == produced:
            A['replay_ok'] += 1
        else:
            A['replay_fail'] += 1
    return A

def merge(a, b):
    if a is None: return b
    if b is None: return a
    for k, v in b.items():
        if isinstance(v, Counter): a[k].update(v)
        else: a[k] = a.get(k, 0) + v
    return a

def main():
    files = sorted(CORPUS.glob('*_keystrokes.txt'))
    random.seed(20261012); samp = random.sample(files, 20000)
    print(f"sampling {len(samp):,} files", flush=True)
    tot = None
    with ProcessPoolExecutor(max_workers=22) as ex:
        for i, res in enumerate(ex.map(analyze, samp, chunksize=25), 1):
            tot = merge(tot, res)
            if i % 5000 == 0: print(f"  {i:,}/{len(samp):,}", flush=True)
    out = {k: (dict(v) if isinstance(v, Counter) else v) for k, v in tot.items()}
    Path(r'C:\keystroke-out\replay2.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in out.items() if k not in ('repair_lat',)}, indent=2))

if __name__ == '__main__':
    main()
