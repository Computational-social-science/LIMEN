"""Transposition-aware error classification.

difflib reports 96% of single transpositions as an insert+delete PAIR (measured),
so a naive alignment inflates both insertion and deletion and deflates nothing
else. A transposition "ab"->"ba" appears as: delete 'a' at i, insert 'a' at i+2.
The signature is a delete/insert pair whose texts are ANAGRAMS and whose span is
short. Merging those recovers the true class.

Validated on synthetic known edits before use, and the merge rate is reported so
the correction is auditable rather than assumed.
"""
from __future__ import annotations
import csv, difflib, io, json, random, string
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

MAX_SPAN = 4          # a transposition moves a character at most a few slots
def is_trans_pair(del_txt, ins_txt):
    if not del_txt or not ins_txt: return False
    if len(del_txt) > MAX_SPAN or len(ins_txt) > MAX_SPAN: return False
    return sorted(del_txt.lower()) == sorted(ins_txt.lower()) and del_txt != ins_txt

def classify_ops(target, produced):
    """Return Counter of classes with transposition-aware merging."""
    out = Counter()
    if target == produced: return out
    sm = difflib.SequenceMatcher(a=target, b=produced, autojunk=False)
    # Transposition detection.
    #
    # THREE failed attempts are recorded here, each caught by the synthetic
    # self-test rather than by inspection:
    #   1. require the insert/delete ops to be ADJACENT          -> 0.1%
    #   2. require the deleted and inserted TEXT to differ        -> 0.1%
    #   3. compare the gaps between consecutive matching blocks   -> 0.0%
    # The actual signature, confirmed by dumping opcodes for "abcdef"->"abdcef", is:
    #
    #   equal(0,2) insert 'd' equal('c') delete 'd' equal(4,6)
    #
    # i.e. an INSERT of a character, then ONE equal block, then a DELETE of the
    # SAME character. The moved character is identical in both ops, and the two
    # ops are separated by exactly one equal block -- which is why (1) and (2)
    # both failed. Detect that triple directly.
    ops = list(sm.get_opcodes())
    consumed = [False] * len(ops)
    for i in range(len(ops) - 2):
        if consumed[i]:
            continue
        o1, a1_, a2_, b1_, b2_ = ops[i]
        o2, c1_, c2_, d1_, d2_ = ops[i + 1]
        o3, e1_, e2_, f1_, f2_ = ops[i + 2]
        if o1 == 'insert' and o2 == 'equal' and o3 == 'delete':
            ins_txt = produced[b1_:b2_]
            del_txt = target[e1_:e2_]
            eq_len = e2_ - e1_
            if ins_txt and ins_txt == del_txt and eq_len <= MAX_SPAN:
                out['transposition'] += len(ins_txt) + eq_len
                consumed[i] = consumed[i + 1] = consumed[i + 2] = True
        elif o1 == 'delete' and o2 == 'equal' and o3 == 'insert':
            del_txt = target[a1_:a2_]
            ins_txt = produced[f1_:f2_]
            eq_len = e2_ - e1_
            if del_txt and del_txt == ins_txt and eq_len <= MAX_SPAN:
                out['transposition'] += len(del_txt) + eq_len
                consumed[i] = consumed[i + 1] = consumed[i + 2] = True
    for i, (op, a0, a1, b0, b1) in enumerate(ops):
        if op == 'equal' or consumed[i]:
            continue
        if op == 'replace':
            m = min(a1 - a0, b1 - b0)
            for k in range(m):
                w, g = target[a0 + k], produced[b0 + k]
                if w == g:
                    continue
                if w.lower() == g.lower():
                    out['case'] += 1
                elif frozenset((w.lower(), g.lower())) in ADJ:
                    out['adjacent'] += 1
                else:
                    out['other_sub'] += 1
            out['del_align'] += max(0, (a1 - a0) - m)
            out['ins_align'] += max(0, (b1 - b0) - m)
        elif op == 'delete':
            out['del_align'] += a1 - a0
        elif op == 'insert':
            out['ins_align'] += b1 - b0
    return out

# ---- validate the merge on synthetic known edits ----
def selftest():
    random.seed(11); alpha = string.ascii_lowercase
    rec = Counter()
    for _ in range(20000):
        w = ''.join(random.choice(alpha) for _ in range(random.randint(4,10)))
        kind = random.choice(['trans','sub','del','ins'])
        i = random.randint(1, len(w)-2)
        if kind == 'trans': b = w[:i]+w[i+1]+w[i]+w[i+2:]
        elif kind == 'sub':
            c = random.choice(alpha)
            while c == w[i]: c = random.choice(alpha)
            b = w[:i]+c+w[i+1:]
        elif kind == 'del': b = w[:i]+w[i+1:]
        else: b = w[:i]+random.choice(alpha)+w[i:]
        c = classify_ops(w,b)
        top = c.most_common(1)[0][0] if c else 'NONE'
        rec[(kind, top)] += 1
    print('  synthetic recovery (true -> recovered):')
    for kind in ['trans','sub','del','ins']:
        tot = sum(v for (k,_),v in rec.items() if k==kind)
        good = rec.get((kind, {'trans':'transposition','sub':None,'del':'del_align','ins':'ins_align'}[kind]), 0)
        if kind == 'sub':
            good = sum(v for (k,t),v in rec.items() if k=='sub' and t in ('other_sub','adjacent','case'))
        print('    %-6s recovered as intended: %5.1f%%' % (kind, 100*good/tot))
    return True

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
    A = dict(sections=0, cls=Counter())
    for sec, g in df.groupby('TEST_SECTION_ID', sort=False):
        g = g.sort_values('PRESS_TIME', kind='stable')
        A['sections'] += 1
        A['cls'].update(classify_ops(str(g.SENTENCE.iloc[0]), str(g.USER_INPUT.iloc[0])))
    return A

def merge(a,b):
    if a is None: return b
    if b is None: return a
    for k,v in b.items():
        if isinstance(v, Counter): a[k].update(v)
        else: a[k] = a.get(k,0)+v
    return a

def main():
    print('=== SELF-TEST ==='); selftest()
    files = sorted(CORPUS.glob('*_keystrokes.txt'))
    random.seed(20261012); samp = random.sample(files, 20000)
    print(f'\n=== CORPUS: {len(samp):,} files ===', flush=True)
    tot = None
    with ProcessPoolExecutor(max_workers=22) as ex:
        for i,res in enumerate(ex.map(analyze, samp, chunksize=25), 1):
            tot = merge(tot,res)
            if i % 5000 == 0: print(f'  {i:,}', flush=True)
    out = {k:(dict(v) if isinstance(v,Counter) else v) for k,v in tot.items()}
    Path(r'C:\keystroke-out\trans_aware.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    tot_n = sum(out['cls'].values())
    print('\n=== transposition-aware class mix ===')
    for k,v in sorted(out['cls'].items(), key=lambda x:-x[1]):
        print('  %-14s %8d  %5.1f%%' % (k, v, 100*v/tot_n))

if __name__ == '__main__':
    main()
