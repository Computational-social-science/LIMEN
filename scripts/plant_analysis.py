"""Planted-truth control: paired analysis, and what it says about the harness.

The plant PREDICTED accuracy(content) < accuracy(function). The run gave the
opposite sign. Two questions follow, and they are different questions:

  Q1. Does the harness detect a difference at matched damage rate at all?
      (the positive-control question -- this is what licenses the earlier null)
  Q2. Is the observed direction real, or noise?
"""
import json, pathlib, random, math
from collections import defaultdict

P = pathlib.Path(r"E:\2026-AI4S\autoresearch\measurement\out\prop_a_planted.jsonl")
rows = [json.loads(l) for l in P.read_text(encoding="utf-8").splitlines() if l.strip() and '"correct"' in l]
by = defaultdict(dict); dmg = defaultdict(list)
for r in rows:
    by[r["item_id"]][r["arm"]] = r
    dmg[r["arm"]].append(r["damage_rate"])
items = [k for k, v in by.items() if len(v) == 3]
print("paired items:", len(items))
print()
print("=== damage matching (the control's precondition) ===")
for a in ["clean","content","function"]:
    print("  %-9s mean damage %.4f" % (a, sum(dmg[a])/len(dmg[a])))
mc = sum(dmg["content"])/len(dmg["content"]); mf = sum(dmg["function"])/len(dmg["function"])
print("  matched to within %.4f" % abs(mc-mf))
print()
print("=== marginals ===")
for a in ["clean","content","function"]:
    acc = sum(by[i][a]["correct"] for i in items)/len(items)
    cov = sum(1 for i in items if by[i][a]["action"]["0.8"]=="answer")/len(items)
    cc = [by[i][a]["c"] for i in items if by[i][a].get("c") is not None]
    print("  %-9s acc=%.4f  cov@0.8=%.4f  mean_c=%.4f" % (a, acc, cov, sum(cc)/len(cc)))
print()
def paired(a,b,key):
    d=[]
    for i in items:
        ra,rb = by[i][a], by[i][b]
        if key=="accuracy": va,vb = ra["correct"], rb["correct"]
        elif key.startswith("cov"):
            t=key.split("@")[1]; va,vb = ra["action"][t]=="answer", rb["action"][t]=="answer"
        elif key=="mean_c":
            if ra.get("c") is None or rb.get("c") is None: continue
            va,vb = ra["c"], rb["c"]
        d.append(float(va)-float(vb))
    return d
def boot(d,B=8000,seed=5):
    rng=random.Random(seed); n=len(d); out=[]
    for _ in range(B):
        s=[d[rng.randrange(n)] for _ in range(n)]; out.append(sum(s)/n)
    out.sort()
    return sum(d)/n, out[int(.025*B)], out[int(.975*B)]
def mcnemar(a,b):
    n01=sum(1 for i in items if by[i][a]["correct"] and not by[i][b]["correct"])
    n10=sum(1 for i in items if not by[i][a]["correct"] and by[i][b]["correct"])
    n=n01+n10
    if n==0: return n01,n10,1.0
    k=min(n01,n10)
    p=min(1.0, 2*sum(math.comb(n,j) for j in range(k+1))*(0.5**n))
    return n01,n10,p
print("=== Q1: does the harness detect a difference at matched damage? ===")
for key in ["accuracy","cov@0.8","mean_c"]:
    d = paired("content","function",key)
    m,lo,hi = boot(d)
    sig = "CI EXCLUDES 0" if not (lo<=0<=hi) else "includes 0"
    print("  content - function  %-9s %+.4f  [%+.4f, %+.4f]  %s" % (key, m, lo, hi, sig))
n01,n10,p = mcnemar("content","function")
print("  McNemar (accuracy): content-only-right=%d  function-only-right=%d  p=%.4f" % (n01,n10,p))
print()
print("=== Q2: and against clean, is the damage real? ===")
for arm in ["content","function"]:
    d = paired(arm,"clean","accuracy")
    m,lo,hi = boot(d)
    n01,n10,p = mcnemar(arm,"clean")
    print("  %-9s - clean  acc %+.4f [%+.4f, %+.4f]  McNemar p=%.4f  (arm-only-right=%d, clean-only-right=%d)"
          % (arm, m, lo, hi, p, n01, n10))
