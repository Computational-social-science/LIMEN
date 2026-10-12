"""POPULATION-LEVEL test: is the double dissociation a property of the population?

The previous analysis pooled 300,000 sentences across 20,000 participants. A
pooled rate is NOT a population parameter: it can be produced entirely by
between-participant heterogeneity while no individual shows the effect
(Simpson's paradox), and it can be dominated by a minority of prolific typists.

A population-level claim requires the participant to be the unit of inference:
compute the effect WITHIN each participant, then ask how the effect is
distributed ACROSS participants. This script emits one row per participant so
every subsequent statistic can be computed at that level.

Effect measured per participant:
    r_class = rate per character in LONG words (>=8 chars)
              -------------------------------
              rate per character in SHORT words (<=4 chars)
for adjacent-key substitution, deletion and insertion separately.

Adjacent-key should give r ~ 1 (geometry is blind to word length).
Deletion and insertion should give r > 1 (chunk structure scales with length).
A paradigm requires this to hold for most participants, not just in aggregate.

Also emits per-participant repair latency, so the 450 ms median can be checked
at population level rather than as a pooled event average.
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

SHORT_MAX, LONG_MIN = 4, 8

def classify_positions(target, produced):
    """Return per-(class, length-band) error counts and character exposure."""
    err = Counter(); expo = Counter()
    words = target.split()
    # character -> (word length band)
    band_of = {}
    off = 0
    for w in words:
        s_ = target.find(w, off); off = s_ + len(w)
        band = 'short' if len(w) <= SHORT_MAX else ('long' if len(w) >= LONG_MIN else 'mid')
        for j in range(s_, s_+len(w)):
            band_of[j] = band
            expo[band] += 1
    if produced == target:
        return err, expo
    sm = difflib.SequenceMatcher(a=target, b=produced, autojunk=False)
    ops = list(sm.get_opcodes()); cons=[False]*len(ops)
    # transposition-aware: insert X / equal / delete X
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
                w,g = target[a0+k], produced[b0+k]
                if w==g or w.lower()==g.lower(): continue
                cls = 'adjacent' if frozenset((w.lower(),g.lower())) in ADJ else 'other_sub'
                if cls=='other_sub': continue
                bd = band_of.get(a0+k)
                if bd: err[(cls,bd)] += 1
            d_ = max(0,(a1-a0)-m)
            for k in range(a1-d_, a1):
                bd = band_of.get(k)
                if bd: err[('deletion',bd)] += 1
        elif op=='delete':
            for k in range(a0,a1):
                bd = band_of.get(k)
                if bd: err[('deletion',bd)] += 1
        elif op=='insert':
            t = min(max(a0,0), max(len(target)-1,0))
            bd = band_of.get(t)
            if bd: err[('insertion',bd)] += 1
    return err, expo

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

    err = Counter(); expo = Counter(); lat = []; n_bs = 0; n_chars = 0; n_sent = 0
    for sec, g in df.groupby('TEST_SECTION_ID', sort=False):
        g = g.sort_values('PRESS_TIME', kind='stable')
        target = str(g.SENTENCE.iloc[0]); produced = str(g.USER_INPUT.iloc[0])
        # exclude prefix-truncated transcriptions
        if produced != target and target.startswith(produced):
            continue
        n_sent += 1; n_chars += len(target)
        e, x = classify_positions(target, produced)
        err.update(e); expo.update(x)
        pt = g.PRESS_TIME.to_numpy(); kc = g.KEYCODE.to_numpy()
        is_bs = (kc == KC_BS); n_bs += int(is_bs.sum())
        idx = np.flatnonzero(is_bs)
        if idx.size:
            starts = idx[np.r_[True, np.diff(idx) > 1]]
            for si in starts:
                j = si - 1
                while j >= 0 and is_bs[j]: j -= 1
                if j < 0: continue
                gap = int(pt[si] - pt[j])
                if 0 <= gap <= 60000: lat.append(gap)
    pid = int(df.PARTICIPANT_ID.iloc[0])
    return dict(participant_id=pid, sentences=n_sent, chars=n_chars, backspaces=n_bs,
                n_lat=len(lat), lat_median=float(np.median(lat)) if lat else None,
                **{f'e_{c}_{b}': err.get((c,b),0) for c in ['adjacent','deletion','insertion'] for b in ['short','mid','long']},
                **{f'x_{b}': expo.get(b,0) for b in ['short','mid','long']})

def main():
    files = sorted(CORPUS.glob('*_keystrokes.txt'))
    random.seed(20261012); samp = random.sample(files, 20000)
    print(f'sampling {len(samp):,} participant files', flush=True)
    recs = []
    with ProcessPoolExecutor(max_workers=22) as ex:
        for i, r in enumerate(ex.map(analyze, samp, chunksize=25), 1):
            if r: recs.append(r)
            if i % 5000 == 0: print(f'  {i:,}', flush=True)
    df = pd.DataFrame(recs)
    out = Path(r'C:\keystroke-out\per_participant.parquet')
    df.to_parquet(out, index=False)
    print(f'wrote {out}  rows={len(df)}')
    print(df[['sentences','chars','backspaces','n_lat','lat_median']].describe().to_string())

if __name__=='__main__':
    main()
