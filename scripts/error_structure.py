"""Measure the STRUCTURE of real human typing errors from the keystroke stream.

Question: is human typing error a motor process (keyboard geometry) or a
linguistic process (word/orthographic structure), or a separable mixture?

This goes beyond the residual-text analysis everyone has done, because the
corpus records BACKSPACE as a keystroke: we can see errors that were CORRECTED,
not only those that survived. Corrected vs surviving errors is the sharpest
available discriminator between a single motor process and two processes.

Outputs aggregate counters only (no per-row data) to a JSON file.
"""
from __future__ import annotations
import csv, difflib, json, random, sys
from collections import Counter, defaultdict
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

def classify(w,g):
    if w==g: return None
    if w.lower()==g.lower(): return "case"
    if frozenset((w.lower(),g.lower())) in ADJ: return "adjacent"
    return "other_sub"

def analyze(path):
    try:
        txt = path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return None
    lines = txt.splitlines()[1:]
    rows, buf = [], None
    for line in lines:
        joined = buf is not None
        buf = line if buf is None else buf + line
        n = buf.count('\t')+1
        if n == 9:
            rows.append(buf); buf = None
        elif n > 9:
            p = buf.split('\t'); rows.append("\t".join(p[:7]+[p[7],p[-1]])); buf = None
    if not rows: return None
    try:
        df = pd.read_csv(__import__('io').StringIO("\n".join(rows)), sep='\t', names=COLS, header=None,
                         quoting=csv.QUOTE_NONE, na_filter=False,
                         dtype={"PARTICIPANT_ID":"int64","TEST_SECTION_ID":"int64","KEYSTROKE_ID":"int64",
                                "PRESS_TIME":"int64","RELEASE_TIME":"int64","KEYCODE":"int32"},
                         engine='c', on_bad_lines='skip')
    except Exception:
        return None
    if df.empty: return None

    agg = dict(
        sections=0, target_chars=0, produced_chars=0, typed_printable=0, backspaces=0,
        deletions_key=0, sections_with_bs=0,
        cls=Counter(), word_pos=Counter(), word_len_err=Counter(), word_len_tot=Counter(),
        sent_decile_err=Counter(), sent_decile_tot=Counter(),
        sub_prev=Counter(), sub_prev_tot=Counter(),
        corrected_vs_surviving=Counter(),
    )
    for sec, g in df.groupby('TEST_SECTION_ID', sort=False):
        g = g.sort_values('PRESS_TIME', kind='stable')
        target = str(g.SENTENCE.iloc[0]); produced = str(g.USER_INPUT.iloc[0])
        kc = g.KEYCODE.to_numpy()
        n_bs = int((kc==KC_BS).sum()); n_del = int((kc==KC_DEL).sum())
        n_print = int(np.sum(~np.isin(kc, list(NONCHAR))))
        agg['sections'] += 1
        agg['target_chars'] += len(target)
        agg['produced_chars'] += len(produced)
        agg['typed_printable'] += n_print
        agg['backspaces'] += n_bs
        agg['deletions_key'] += n_del
        if n_bs: agg['sections_with_bs'] += 1

        # word geometry of the target
        word_of = {}
        wstart = {}
        wlen = {}
        off = 0
        for wi, w in enumerate(target.split()):
            s = target.find(w, off); off = s + len(w)
            wlen[wi] = len(w)
            for j in range(s, s+len(w)):
                word_of[j] = wi; wstart[j] = s
                agg['word_len_tot'][len(w)] += 1
        n = len(target)
        dec = max(1, n//10)

        if produced == target:
            continue
        sm = difflib.SequenceMatcher(a=target, b=produced, autojunk=False)
        for op, a0, a1, b0, b1 in sm.get_opcodes():
            if op == 'equal': continue
            if op == 'replace':
                m = min(a1-a0, b1-b0)
                for k in range(m):
                    w, gg = target[a0+k], produced[b0+k]
                    c = classify(w, gg)
                    if c is None: continue
                    agg['cls'][c] += 1
                    wi = word_of.get(a0+k)
                    if wi is not None:
                        p = a0+k - wstart[a0+k]
                        L = wlen[wi]
                        if p == 0: agg['word_pos']['first'] += 1
                        elif p == L-1: agg['word_pos']['last'] += 1
                        else: agg['word_pos']['middle'] += 1
                        agg['word_len_err'][L] += 1
                    agg['sent_decile_err'][min(9,(a0+k)//dec)] += 1
                    # what precedes the error: space (word start) vs letter
                    agg['sub_prev']['space' if a0+k==0 or target[a0+k-1]==' ' else 'letter'] += 1
                agg['cls']['del_align'] += max(0,(a1-a0)-m)
                agg['cls']['ins_align'] += max(0,(b1-b0)-m)
            elif op == 'delete':
                agg['cls']['del_align'] += a1-a0
                for k in range(a0,a1):
                    agg['sent_decile_err'][min(9,k//dec)] += 1
                    wi = word_of.get(k)
                    if wi is not None:
                        p = k - wstart[k]; L = wlen[wi]
                        agg['word_pos']['first' if p==0 else ('last' if p==L-1 else 'middle')] += 1
                        agg['word_len_err'][L] += 1
            elif op == 'insert':
                agg['cls']['ins_align'] += b1-b0
        for k in range(n):
            agg['sent_decile_tot'][min(9,k//dec)] += 1
            wi = word_of.get(k)
            if wi is not None:
                p = k - wstart[k]; L = wlen[wi]
                agg['word_pos_tot'] = agg.get('word_pos_tot', Counter())
                agg['word_pos_tot']['first' if p==0 else ('last' if p==L-1 else 'middle')] += 1
            agg['sub_prev_tot']['space' if k==0 or target[k-1]==' ' else 'letter'] += 1
    return agg

def merge(a, b):
    if a is None: return b
    if b is None: return a
    for k, v in b.items():
        if isinstance(v, Counter): a[k].update(v)
        else: a[k] = a.get(k, 0) + v
    return a

def main():
    files = sorted(CORPUS.glob('*_keystrokes.txt'))
    random.seed(20261012)
    samp = random.sample(files, 20000)
    print(f"sampling {len(samp):,} participant files", flush=True)
    total = None
    with ProcessPoolExecutor(max_workers=22) as ex:
        for i, res in enumerate(ex.map(analyze, samp, chunksize=25), 1):
            total = merge(total, res)
            if i % 5000 == 0: print(f"  {i:,}/{len(samp):,}", flush=True)
    out = {}
    for k, v in total.items():
        out[k] = dict(v) if isinstance(v, Counter) else v
    Path(r'C:\keystroke-out\error_structure.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps({k: (dict(v) if isinstance(v, Counter) else v) for k, v in total.items()}, indent=2, default=str))

if __name__ == '__main__':
    main()
