"""Corrected reading: DETECTION and POWER are different statements.

My first pass labelled an effect "below MDE" whenever |observed| < MDE. That
conflates two different things and is wrong:

  * MDE = the smallest TRUE effect the design detects with 80% probability.
  * An OBSERVED effect smaller than the MDE can still be significant, because the
    observed value is itself a random draw. What |observed| < MDE tells you is
    that the design has < 80% power FOR AN EFFECT OF THAT SIZE.

So each comparison gets three separate numbers: the observed difference, its CI,
and the achieved power at that effect size. "Detected" and "well-powered for this
size" are reported separately.
"""
import json, pathlib, math, random
from collections import defaultdict

def load(p):
    rows = [json.loads(l) for l in pathlib.Path(p).read_text(encoding="utf-8").splitlines()
            if l.strip() and '"correct"' in l]
    by = defaultdict(dict)
    for r in rows: by[r["item_id"]][r["arm"]] = r
    return {k: v for k, v in by.items() if len(v) == 3}

def phi(x): return 0.5*(1+math.erf(x/math.sqrt(2)))

def paired(by, a, b, key):
    d = []
    for i in by:
        ra, rb = by[i][a], by[i][b]
        if key == "accuracy": va, vb = ra["correct"], rb["correct"]
        elif key.startswith("cov"):
            t = key.split("@")[1]
            va, vb = ra["action"][t] == "answer", rb["action"][t] == "answer"
        else: continue
        d.append(float(va) - float(vb))
    return d

def counts(by, a, b, key):
    n01 = n10 = 0
    for i in by:
        ra, rb = by[i][a], by[i][b]
        if key == "accuracy": va, vb = ra["correct"], rb["correct"]
        else:
            t = key.split("@")[1]
            va, vb = ra["action"][t] == "answer", rb["action"][t] == "answer"
        if va and not vb: n01 += 1
        if not va and vb: n10 += 1
    return n01, n10

def analyze(title, path, comps):
    by = load(path); n = len(by)
    print("=" * 92)
    print("%s   (n = %d paired items)" % (title, n))
    print("=" * 92)
    print("%-26s %9s %-22s %7s %8s %9s %s" % ("comparison","obs diff","95% CI","MDE","p","power@obs","verdict"))
    for a, b, label in comps:
        for key in ["accuracy", "cov@0.8"]:
            d = paired(by, a, b, key)
            rng = random.Random(5); m = sum(d)/len(d)
            bs = sorted(sum(d[rng.randrange(len(d))] for _ in range(len(d)))/len(d) for _ in range(4000))
            lo, hi = bs[100], bs[3899]
            n01, n10 = counts(by, a, b, key)
            nn = n01 + n10
            pv = 1.0 if nn == 0 else min(1.0, 2*sum(math.comb(nn,j) for j in range(min(n01,n10)+1))*(0.5**nn))
            # discordance-based SE and MDE
            pi = nn/n
            se = math.sqrt(pi/n) if pi > 0 else float('nan')
            mde = 2.801585 * se if pi > 0 else float('nan')
            # achieved power for the OBSERVED effect
            power = (1 - phi(1.959964 - abs(m)/se) + phi(-1.959964 - abs(m)/se)) if se and se > 0 else float('nan')
            detected = not (lo <= 0 <= hi)
            verdict = "DETECTED" if detected else "not detected"
            if detected and power < 0.80: verdict += " (power<80% for this size)"
            if not detected and abs(m) < mde: verdict += " (below MDE)"
            print("%-26s %+9.4f [%+.4f,%+.4f] %7.4f %8.4f %8.2f  %s"
                  % (label+" "+key.split("@")[0], m, lo, hi, mde, pv, power, verdict))
        print()

OUT = pathlib.Path(__file__).resolve().parents[1] / "measurement" / "out"
analyze("A. FAMILY, n=280", OUT/"prop_a_powered_family.jsonl",
        [("geometry","structure","geometry-structure"),
         ("geometry","clean","geometry-clean"),
         ("structure","clean","structure-clean")])
analyze("B. CALIBRATED PLANT, n=280 (content words, 0.30 vs 0.15)", OUT/"prop_a_powered_plant.jsonl",
        [("content_hi","content_lo","hi-lo  [PLANT]"),
         ("content_lo","clean","lo-clean"),
         ("content_hi","clean","hi-clean")])
