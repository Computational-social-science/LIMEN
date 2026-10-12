"""H1 (motor) vs H2 (planning): the decisive discriminator.

Both hypotheses accept that deletion and insertion dominate RESIDUAL error. They
disagree about WHY, and the disagreement makes opposite predictions about
structure:

  H1 motor    -- deletion/insertion are motor events (missed or doubled
                 keystroke). A missed keystroke is geometrically blind: its rate
                 should be FLAT across word positions, like adjacent-key errors.
  H2 planning -- deletion/insertion are chunk/boundary events. Their rate should
                 be CONCENTRATED at word boundaries (first/last position) and
                 scale with word length, while adjacent-key rate stays flat.

The test is therefore a 2x2 contrast of rate-vs-position, per class, with word
length held separate. Everything is normalised per CHARACTER EXPOSURE at that
position, and truncation is excluded (it manufactures end-of-target deletions).
Case errors are excluded throughout: they are a capitalisation convention, not a
typing slip, and they would swamp the word-first cell.
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

def classify(target, produced):
    out = Counter()
    if target == produced: return out
    sm = difflib.SequenceMatcher(a=target, b=produced, autojunk=False)
    ops = list(sm.get_opcodes()); cons=[False]*len(ops)
    for i in range(len(ops)-2):
        if cons[i]: continue
        o1,a1_,a2_,b1_,b2_ = ops[i]; o2,c1_,c2_,d1_,d2_ = ops[i+1]; o3,e1_,e2_,f1_,f2_ = ops[i+2]
        if o1=='insert' and o2=='equal' and o3=='delete':
            it=produced[b1_:b2_]; dt=target[e1_:e2_]; el=e2_-e1_
            if it and it==dt and el<=4:
                out['transposition'] += len(it)+el; cons[i]=cons[i+1]=cons[i+2]=True
        elif o1=='delete' and o2=='equal' and o3=='insert':
            dt=target[a1_:a2_]; it=produced[f1_:f2_]; el=e2_-e1_
            if dt and dt==it and el<=4:
                out['transposition'] += len(dt)+el; cons[i]=cons[i+1]=cons[i+2]=True
    for i,(op,a0,a1,b0,b1) in enumerate(ops):
        if op=='equal' or cons[i]: continue
        if op=='replace':
            m=min(a1-a0,b1-b0)
            for k in range(m):
                w,g=target[a0+k],produced[b0+k]
                if w==g: continue
                if w.lower()==g.lower(): continue        # case excluded by design
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

    A = dict(sections=0, err=Counter(), expo=Counter(), err_by_len=Counter(), expo_by_len=Counter())
    for sec, g in df.groupby('TEST_SECTION_ID', sort=False):
        g = g.sort_values('PRESS_TIME', kind='stable')
        target = str(g.SENTENCE.iloc[0]); produced = str(g.USER_INPUT.iloc[0])
        # exclude truncated transcriptions: they manufacture end-of-target deletions
        if produced != target and target.startswith(produced):
            continue
        A['sections'] += 1
        word_of, wstart, wlen = {}, {}, {}
        off = 0
        for wi, w in enumerate(target.split()):
            s_ = target.find(w, off); off = s_ + len(w); wlen[wi] = len(w)
            for j in range(s_, s_+len(w)): word_of[j] = wi; wstart[j] = s_
        def pos(k):
            wi = word_of.get(k)
            if wi is None: return None
            p = k - wstart[k]; L = wlen[wi]
            return ('first' if p==0 else ('last' if p==L-1 else 'middle')), L
        n = len(target)
        for k in range(n):
            r = pos(k)
            if r: A['expo'][r[0]] += 1; A['expo_by_len'][r[1]] += 1
        for c,v in classify(target, produced).items():
            if c == 'other_sub': continue
            # attribute each class to positions via a second alignment walk
            sm = difflib.SequenceMatcher(a=target, b=produced, autojunk=False)
            for op,a0,a1,b0,b1 in sm.get_opcodes():
                if op=='equal': continue
                if op=='replace':
                    m=min(a1-a0,b1-b0)
                    for k in range(m):
                        w,gg = target[a0+k], produced[b0+k]
                        if w==gg or w.lower()==gg.lower(): continue
                        cls = 'adjacent' if frozenset((w.lower(),gg.lower())) in ADJ else 'other_sub'
                        if cls=='other_sub': continue
                        r = pos(a0+k)
                        if r: A['err'][(cls, r[0])] += 1; A['err_by_len'][(cls, r[1])] += 1
                    d_ = max(0,(a1-a0)-m)
                    for k in range(a1-d_, a1):
                        r = pos(k)
                        if r: A['err'][('deletion', r[0])] += 1; A['err_by_len'][('deletion', r[1])] += 1
                elif op=='delete':
                    for k in range(a0,a1):
                        r = pos(k)
                        if r: A['err'][('deletion', r[0])] += 1; A['err_by_len'][('deletion', r[1])] += 1
                elif op=='insert':
                    t = min(max(a0,0), max(n-1,0))
                    r = pos(t)
                    if r: A['err'][('insertion', r[0])] += 1; A['err_by_len'][('insertion', r[1])] += 1
            break
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
            tot=merge(tot,res)
            if i%5000==0: print(f'  {i:,}', flush=True)
    def ser(v):
        if isinstance(v, Counter):
            return {"|".join(map(str,k)) if isinstance(k,tuple) else k: n for k,n in v.items()}
        return v
    out={k: ser(v) for k,v in tot.items()}
    Path(r'C:\keystroke-out\h1h2.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print('written')

if __name__=='__main__':
    main()
