"""The decisive test for the paradigm claim.

CLAIM: the noise reaching a model is the RESIDUAL OF A CONTROL LOOP, not the
output of a channel. Consequence: each error class's share in surviving text is
governed by how well the typist's own monitor detects that class -- classes the
monitor catches well are UNDER-represented in residual text, classes it catches
poorly are OVER-represented.

This is testable without the corrected/surviving replay, which proved too brittle
(the buffer diverges after the first unaligned edit). The test uses a cleaner
signal: the relationship between a class's overall prevalence and its
survival share. If error were a memoryless channel, survival probability would
be class-independent. If a monitor is at work, survival probability differs
systematically by class -- and specifically, LOCAL classes (detectable from the
string alone, e.g. a wrong adjacent key) should survive LESS than classes needing
lexical knowledge.

Measured here per class: how often an error of that class is present at all
(via the keystroke stream's backspace count as the repair signal) and how often
it survives. We use a within-section design: sections are grouped by whether they
contain any backspace at all, and the residual class mix is compared between
sections with heavy correction and sections with none. If the monitor is
class-selective, the residual mix must differ between those groups.
"""
from __future__ import annotations
import csv, io, json, random
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

def classify(target, produced):
    """Class counts for one section, transposition-aware."""
    import difflib
    out = Counter()
    if target == produced: return out
    sm = difflib.SequenceMatcher(a=target, b=produced, autojunk=False)
    ops = list(sm.get_opcodes()); consumed=[False]*len(ops)
    for i in range(len(ops)-2):
        if consumed[i]: continue
        o1,a1_,a2_,b1_,b2_ = ops[i]; o2,c1_,c2_,d1_,d2_ = ops[i+1]; o3,e1_,e2_,f1_,f2_ = ops[i+2]
        if o1=='insert' and o2=='equal' and o3=='delete':
            it = produced[b1_:b2_]; dt = target[e1_:e2_]; el = e2_-e1_
            if it and it==dt and el<=4:
                out['transposition'] += len(it)+el; consumed[i]=consumed[i+1]=consumed[i+2]=True
        elif o1=='delete' and o2=='equal' and o3=='insert':
            dt = target[a1_:a2_]; it = produced[f1_:f2_]; el = e2_-e1_
            if dt and dt==it and el<=4:
                out['transposition'] += len(dt)+el; consumed[i]=consumed[i+1]=consumed[i+2]=True
    for i,(op,a0,a1,b0,b1) in enumerate(ops):
        if op=='equal' or consumed[i]: continue
        if op=='replace':
            m=min(a1-a0,b1-b0)
            for k in range(m):
                w,g = target[a0+k], produced[b0+k]
                if w==g: continue
                if w.lower()==g.lower(): out['case'] += 1
                elif frozenset((w.lower(),g.lower())) in ADJ: out['adjacent'] += 1
                else: out['other_sub'] += 1
            out['deletion'] += max(0,(a1-a0)-m); out['insertion'] += max(0,(b1-b0)-m)
        elif op=='delete': out['deletion'] += a1-a0
        elif op=='insert': out['insertion'] += b1-b0
    return out

def analyze(path):
    try: txt = path.read_text(encoding='utf-8', errors='replace')
    except OSError: return None
    rows, buf = [], None
    for line in txt.splitlines()[1:]:
        buf = line if buf is None else buf + line
        n = buf.count('\t')+1
        if n == 9: rows.append(buf); buf=None
        elif n > 9:
            p = buf.split('\t'); rows.append("\t".join(p[:7]+[p[7],p[-1]])); buf=None
    if not rows: return None
    try:
        df = pd.read_csv(io.StringIO("\n".join(rows)), sep='\t', names=COLS, header=None,
                         quoting=csv.QUOTE_NONE, na_filter=False,
                         dtype={"PARTICIPANT_ID":"int64","TEST_SECTION_ID":"int64","KEYSTROKE_ID":"int64",
                                "PRESS_TIME":"int64","RELEASE_TIME":"int64","KEYCODE":"int32"},
                         engine='c', on_bad_lines='skip')
    except Exception: return None
    if df.empty: return None
    # bucket sections by correction intensity (backspaces per typed char)
    A = dict(sections=0, cls_by_bucket=Counter(), chars_by_bucket=Counter(), bucket_n=Counter())
    for sec, g in df.groupby('TEST_SECTION_ID', sort=False):
        g = g.sort_values('PRESS_TIME', kind='stable')
        target = str(g.SENTENCE.iloc[0]); produced = str(g.USER_INPUT.iloc[0])
        kc = g.KEYCODE.to_numpy()
        n_bs = int((kc==KC_BS).sum()); n_print = int(np.sum(~np.isin(kc, list(NONCHAR))))
        A['sections'] += 1
        rate = n_bs / max(n_print,1)
        b = 0 if n_bs==0 else (1 if rate<0.05 else (2 if rate<0.15 else 3))
        A['bucket_n'][b] += 1
        A['chars_by_bucket'][b] += len(target)
        for k,v in classify(target, produced).items():
            A['cls_by_bucket'][f'{b}|{k}'] += v
    return A

def merge(a,b):
    if a is None: return b
    if b is None: return a
    for k,v in b.items():
        if isinstance(v,Counter): a[k].update(v)
        else: a[k] = a.get(k,0)+v
    return a

def main():
    files = sorted(CORPUS.glob('*_keystrokes.txt'))
    random.seed(20261012); samp = random.sample(files, 20000)
    print(f'sampling {len(samp):,}', flush=True)
    tot=None
    with ProcessPoolExecutor(max_workers=22) as ex:
        for i,res in enumerate(ex.map(analyze, samp, chunksize=25), 1):
            tot = merge(tot,res)
            if i%5000==0: print(f'  {i:,}', flush=True)
    out = {k:(dict(v) if isinstance(v,Counter) else v) for k,v in tot.items()}
    Path(r'C:\keystroke-out\monitor_test.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print('written')

if __name__=='__main__':
    main()
