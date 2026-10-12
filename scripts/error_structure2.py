"""Stage 2: error STRUCTURE with correct denominators and the decisive tests.

Fixes a denominator bug in stage 1: the position denominators were accumulated
only for sections containing at least one error (the loop sat after a
`continue`), so every reported rate was conditional on an error existing. The
ratios survived but the rates did not. Denominators are now accumulated for
EVERY section.

The decisive question: is human typing error ONE motor process (keyboard
geometry) or TWO separable processes (motor execution + linguistic planning)?

Test A -- class mix by word position. A single motor process predicts the class
mixture is position-independent. If the mixture changes with position, the
processes are separable.
Test B -- case errors by position. Capital letters occur at word starts; if case
errors cluster there, case is a real class and the measurement is valid.
Test C -- adjacency rate by position. Motor slips should not care about word
boundaries.
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
    if p == 0: return "first"
    if p == L-1: return "last"
    return "middle"

def analyze(path):
    try:
        txt = path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return None
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
    except Exception:
        return None
    if df.empty: return None

    A = dict(
        sections=0, target_chars=0, typed_printable=0, backspaces=0, sections_with_bs=0,
        # class mix overall and by position (Test A)
        cls=Counter(), cls_by_pos=Counter(), pos_tot=Counter(),
        # case by position (Test B)
        case_by_pos=Counter(),
        # word-initial vs internal (characters preceded by space vs letter)
        prev_err=Counter(), prev_tot=Counter(),
        # sentence decile
        dec_err=Counter(), dec_tot=Counter(),
        # corrected-error proxy: backspaces per section vs surviving errors
        bs_hist=Counter(), surv_hist=Counter(),
    )
    for sec, g in df.groupby('TEST_SECTION_ID', sort=False):
        g = g.sort_values('PRESS_TIME', kind='stable')
        target = str(g.SENTENCE.iloc[0]); produced = str(g.USER_INPUT.iloc[0])
        kc = g.KEYCODE.to_numpy()
        n_bs = int((kc==KC_BS).sum())
        n_print = int(np.sum(~np.isin(kc, list(NONCHAR))))
        A['sections'] += 1; A['target_chars'] += len(target)
        A['typed_printable'] += n_print; A['backspaces'] += n_bs
        if n_bs: A['sections_with_bs'] += 1

        word_of, wstart, wlen = {}, {}, {}
        off = 0
        for wi, w in enumerate(target.split()):
            s = target.find(w, off); off = s + len(w); wlen[wi] = len(w)
            for j in range(s, s+len(w)): word_of[j] = wi; wstart[j] = s
        n = len(target); dec = max(1, n//10)

        # ---- denominators for EVERY section (the stage-1 bug) ----
        for k in range(n):
            p = pos_of(k, word_of, wstart, wlen)
            if p: A['pos_tot'][p] += 1
            A['prev_tot']['space' if (k == 0 or target[k-1] == ' ') else 'letter'] += 1
            A['dec_tot'][min(9, k//dec)] += 1

        sm = difflib.SequenceMatcher(a=target, b=produced, autojunk=False)
        n_err = 0
        for op, a0, a1, b0, b1 in sm.get_opcodes():
            if op == 'equal': continue
            if op == 'replace':
                m = min(a1-a0, b1-b0)
                for k in range(m):
                    c = classify(target[a0+k], produced[b0+k])
                    if c is None: continue
                    n_err += 1
                    A['cls'][c] += 1
                    p = pos_of(a0+k, word_of, wstart, wlen)
                    if p: A['cls_by_pos'][(p, c)] += 1
                    if c == 'case' and p: A['case_by_pos'][p] += 1
                    A['prev_err']['space' if (a0+k == 0 or target[a0+k-1] == ' ') else 'letter'] += 1
                    A['dec_err'][min(9, (a0+k)//dec)] += 1
                A['cls']['del_align'] += max(0,(a1-a0)-m); n_err += max(0,(a1-a0)-m)
                A['cls']['ins_align'] += max(0,(b1-b0)-m); n_err += max(0,(b1-b0)-m)
            elif op == 'delete':
                A['cls']['del_align'] += a1-a0; n_err += a1-a0
                for k in range(a0,a1):
                    p = pos_of(k, word_of, wstart, wlen)
                    if p: A['cls_by_pos'][(p,'del_align')] += 1
                    A['dec_err'][min(9,k//dec)] += 1
            elif op == 'insert':
                A['cls']['ins_align'] += b1-b0; n_err += b1-b0
                # Attribute an insertion to the target position it sits before,
                # clamped into range, so per-position shares are complete.
                for k in range(b0, b1):
                    t = min(max(a0, 0), max(len(target)-1, 0))
                    pp = pos_of(t, word_of, wstart, wlen)
                    if pp: A['cls_by_pos'][(pp, 'ins_align')] += 1
        A['bs_hist'][min(n_bs, 20)] += 1
        A['surv_hist'][min(n_err, 20)] += 1
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
    def ser(v):
        if isinstance(v, Counter):
            # cls_by_pos keys are (position, class) tuples; flatten for JSON.
            return {"|".join(map(str, k)) if isinstance(k, tuple) else k: n for k, n in v.items()}
        return v
    out = {k: ser(v) for k, v in tot.items()}
    Path(r'C:\keystroke-out\error_structure2.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    main()
