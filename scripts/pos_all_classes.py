"""All-classes position profile, truncation excluded, case separated.

The verifier flagged that the earlier position profile silently excluded
insertions (it counted positions only in the `replace`/`delete` branches). This
recomputes with EVERY class attributed to a position, so the numerator convention
matches the overall class mix, and reports the case-excluded series too.
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

def analyze(path):
    try: txt = path.read_text(encoding='utf-8', errors='replace')
    except OSError: return None
    rows, buf = [], None
    for line in txt.splitlines()[1:]:
        buf = line if buf is None else buf + line
        n = buf.count('\t')+1
        if n==9: rows.append(buf); buf=None
        elif n>9:
            p=buf.split('\t'); rows.append("\t".join(p[:7]+[p[7],p[-1]])); buf=None
    if not rows: return None
    try:
        df = pd.read_csv(io.StringIO("\n".join(rows)), sep='\t', names=COLS, header=None,
                         quoting=csv.QUOTE_NONE, na_filter=False,
                         dtype={"PARTICIPANT_ID":"int64","TEST_SECTION_ID":"int64","KEYSTROKE_ID":"int64",
                                "PRESS_TIME":"int64","RELEASE_TIME":"int64","KEYCODE":"int32"},
                         engine='c', on_bad_lines='skip')
    except Exception: return None
    if df.empty: return None
    A = dict(sections=0, err_all=Counter(), err_nocase=Counter(), expo=Counter())
    for sec, g in df.groupby('TEST_SECTION_ID', sort=False):
        g = g.sort_values('PRESS_TIME', kind='stable')
        target = str(g.SENTENCE.iloc[0]); produced = str(g.USER_INPUT.iloc[0])
        if produced != target and target.startswith(produced):
            continue                     # truncation excluded
        A['sections'] += 1
        word_of, wstart, wlen = {}, {}, {}
        off = 0
        for wi, w in enumerate(target.split()):
            s_ = target.find(w, off); off = s_+len(w); wlen[wi] = len(w)
            for j in range(s_, s_+len(w)): word_of[j] = wi; wstart[j] = s_
        def pos(k):
            wi = word_of.get(k)
            if wi is None: return None
            p = k - wstart[k]; L = wlen[wi]
            return 'first' if p==0 else ('last' if p==L-1 else 'middle')
        n = len(target)
        for k in range(n):
            p = pos(k)
            if p: A['expo'][p] += 1
        sm = difflib.SequenceMatcher(a=target, b=produced, autojunk=False)
        ops = list(sm.get_opcodes()); cons=[False]*len(ops)
        for i in range(len(ops)-2):
            if cons[i]: continue
            o1,a1_,a2_,b1_,b2_ = ops[i]; o2,c1_,c2_,d1_,d2_ = ops[i+1]; o3,e1_,e2_,f1_,f2_ = ops[i+2]
            if o1=='insert' and o2=='equal' and o3=='delete':
                it=produced[b1_:b2_]; dt=target[e1_:e2_]; el=e2_-e1_
                if it and it==dt and el<=4: cons[i]=cons[i+1]=cons[i+2]=True
            elif o1=='delete' and o2=='equal' and o3=='insert':
                dt=target[a1_:a2_]; it=produced[f1_:f2_]; el=e2_-e1_
                if dt and dt==it and el<=4: cons[i]=cons[i+1]=cons[i+2]=True
        for i,(op,a0,a1,b0,b1) in enumerate(ops):
            if op=='equal' or cons[i]: continue
            if op=='replace':
                m=min(a1-a0,b1-b0)
                for k in range(m):
                    w,gg = target[a0+k], produced[b0+k]
                    if w==gg: continue
                    p = pos(a0+k)
                    if not p: continue
                    A['err_all'][p] += 1
                    if w.lower()!=gg.lower(): A['err_nocase'][p] += 1
                d_ = max(0,(a1-a0)-m)
                for k in range(a1-d_, a1):
                    p = pos(k)
                    if p: A['err_all'][p] += 1; A['err_nocase'][p] += 1
            elif op=='delete':
                for k in range(a0,a1):
                    p = pos(k)
                    if p: A['err_all'][p] += 1; A['err_nocase'][p] += 1
            elif op=='insert':
                t = min(max(a0,0), max(n-1,0))
                p = pos(t)
                if p: A['err_all'][p] += 1; A['err_nocase'][p] += 1
    return A

def merge(a,b):
    if a is None: return b
    if b is None: return a
    for k,v in b.items():
        if isinstance(v,Counter): a[k].update(v)
        else: a[k]=a.get(k,0)+v
    return a

def main():
    files = sorted(CORPUS.glob('*_keystrokes.txt'))
    random.seed(20261012); samp = random.sample(files, 20000)
    print(f'sampling {len(samp):,}', flush=True)
    tot=None
    with ProcessPoolExecutor(max_workers=22) as ex:
        for i,res in enumerate(ex.map(analyze, samp, chunksize=25), 1):
            tot=merge(tot,res)
            if i%5000==0: print(f'  {i:,}', flush=True)
    out={k:(dict(v) if isinstance(v,Counter) else v) for k,v in tot.items()}
    Path(r'C:\keystroke-out\pos_all_classes.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print('\nALL CLASSES, truncation excluded (per 1000 chars):')
    for p in ['first','middle','last']:
        print('  %-7s %.2f' % (p, 1000*out['err_all'][p]/out['expo'][p]))
    print('CASE EXCLUDED:')
    for p in ['first','middle','last']:
        print('  %-7s %.2f' % (p, 1000*out['err_nocase'][p]/out['expo'][p]))

if __name__=='__main__':
    main()
