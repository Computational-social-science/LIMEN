"""Two decisive tests.

TEST 1 -- TRUNCATION. Is the word-last / sentence-end error elevation real, or
an artefact of participants who stopped typing early? A truncated transcription
registers as a run of deletions at the end of the target, which would produce
exactly the observed pattern.

TEST 2 -- CORRECTION LATENCY (the paradigm question). The corpus logs BACKSPACE
as a keystroke with a timestamp, so the delay between an error and its repair is
directly measurable. If error handling were a single low-level motor loop, the
latency distribution would be unimodal. Two processes -- a fast motor monitor
and a slower deliberate check -- predict separable modes. Nobody has measured
this on this corpus.
"""
from __future__ import annotations
import csv, difflib, io, json, random
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np, pandas as pd

CORPUS = Path(r'C:\keystroke-corpus\files')
COLS = ["PARTICIPANT_ID","TEST_SECTION_ID","SENTENCE","USER_INPUT","KEYSTROKE_ID","PRESS_TIME","RELEASE_TIME","LETTER","KEYCODE"]
KC_BS, KC_DEL, KC_ENTER, KC_TAB = 8, 46, 13, 9
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

def classify(w,g):
    if w==g: return None
    if w.lower()==g.lower(): return "case"
    if frozenset((w.lower(),g.lower())) in ADJ: return "adjacent"
    return "other_sub"

def pos_of(k, word_of, wstart, wlen):
    wi = word_of.get(k)
    if wi is None: return None
    p = k - wstart[k]; L = wlen[wi]
    return "first" if p==0 else ("last" if p==L-1 else "middle")

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

    A = dict(
        # truncation test
        sections=0, trunc_sections=0, trunc_chars_lost=0,
        pos_err_all=Counter(), pos_tot_all=Counter(),
        pos_err_clean=Counter(), pos_tot_clean=Counter(),
        dec_err_all=Counter(), dec_tot_all=Counter(),
        dec_err_clean=Counter(), dec_tot_clean=Counter(),
        cls_all=Counter(), cls_clean=Counter(),
        # correction latency
        lat=Counter(), lat_n=0,
    )
    for sec, g in df.groupby('TEST_SECTION_ID', sort=False):
        g = g.sort_values('PRESS_TIME', kind='stable')
        target = str(g.SENTENCE.iloc[0]); produced = str(g.USER_INPUT.iloc[0])
        A['sections'] += 1
        # --- is this a truncated transcription? ---
        is_trunc = (produced != target) and target.startswith(produced)
        if is_trunc:
            A['trunc_sections'] += 1
            A['trunc_chars_lost'] += len(target) - len(produced)

        word_of, wstart, wlen = {}, {}, {}
        off = 0
        for wi, w in enumerate(target.split()):
            s = target.find(w, off); off = s + len(w); wlen[wi] = len(w)
            for j in range(s, s+len(w)): word_of[j] = wi; wstart[j] = s
        n = len(target); dec = max(1, n//10)

        for k in range(n):
            p = pos_of(k, word_of, wstart, wlen)
            if p: A['pos_tot_all'][p] += 1
            A['dec_tot_all'][min(9,k//dec)] += 1
            if not is_trunc:
                if p: A['pos_tot_clean'][p] += 1
                A['dec_tot_clean'][min(9,k//dec)] += 1

        sm = difflib.SequenceMatcher(a=target, b=produced, autojunk=False)
        for op, a0, a1, b0, b1 in sm.get_opcodes():
            if op == 'equal': continue
            if op == 'replace':
                m = min(a1-a0, b1-b0)
                for k in range(m):
                    c = classify(target[a0+k], produced[b0+k])
                    if c is None: continue
                    A['cls_all'][c] += 1
                    if not is_trunc: A['cls_clean'][c] += 1
                    p = pos_of(a0+k, word_of, wstart, wlen)
                    if p: A['pos_err_all'][p] += 1
                    A['dec_err_all'][min(9,(a0+k)//dec)] += 1
                    if not is_trunc:
                        if p: A['pos_err_clean'][p] += 1
                        A['dec_err_clean'][min(9,(a0+k)//dec)] += 1
                A['cls_all']['del_align'] += max(0,(a1-a0)-m)
                A['cls_all']['ins_align'] += max(0,(b1-b0)-m)
                if not is_trunc:
                    A['cls_clean']['del_align'] += max(0,(a1-a0)-m)
                    A['cls_clean']['ins_align'] += max(0,(b1-b0)-m)
            elif op == 'delete':
                A['cls_all']['del_align'] += a1-a0
                if not is_trunc: A['cls_clean']['del_align'] += a1-a0
                for k in range(a0,a1):
                    p = pos_of(k, word_of, wstart, wlen)
                    if p: A['pos_err_all'][p] += 1
                    A['dec_err_all'][min(9,k//dec)] += 1
                    if not is_trunc:
                        if p: A['pos_err_clean'][p] += 1
                        A['dec_err_clean'][min(9,k//dec)] += 1
            elif op == 'insert':
                A['cls_all']['ins_align'] += b1-b0
                if not is_trunc: A['cls_clean']['ins_align'] += b1-b0

        # --- TEST 2: latency from the last real keystroke to the first backspace ---
        pt = g.PRESS_TIME.to_numpy(); kc = g.KEYCODE.to_numpy()
        is_bs = (kc == KC_BS)
        idx = np.flatnonzero(is_bs)
        if idx.size:
            starts = idx[np.r_[True, np.diff(idx) > 1]]   # first backspace of each run
            for s_i in starts:
                # previous keystroke that is NOT a backspace
                j = s_i - 1
                while j >= 0 and is_bs[j]: j -= 1
                if j < 0: continue
                gap = int(pt[s_i] - pt[j])
                if 0 <= gap <= 60000:
                    A['lat'][min(gap//50, 1200)] += 1   # 50 ms bins, capped at 60 s
                    A['lat_n'] += 1
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
    Path(r'C:\keystroke-out\decisive.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('written')

if __name__ == '__main__':
    main()
