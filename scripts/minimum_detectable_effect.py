"""What COULD this design have detected? The minimum detectable effect.

The plant did not fire, so the question stops being "is there an effect?" and
becomes "what effect size would this design have caught?" That bound is what
licenses or forbids the family null.

Method: for each endpoint, take the observed paired discordance, and compute the
MDE -- the smallest true difference that would be detected with 80% power at
alpha = 0.05, two-sided. For a paired binary endpoint the variance of the
difference is driven by the discordance rate; for a continuous endpoint by the
observed SD of the paired differences.
"""
import json, pathlib, random, math
from collections import defaultdict

P = pathlib.Path(r"E:\2026-AI4S\autoresearch\measurement\out\prop_a_planted.jsonl")
rows = [json.loads(l) for l in P.read_text(encoding="utf-8").splitlines() if l.strip() and '"correct"' in l]
by = defaultdict(dict)
for r in rows: by[r["item_id"]][r["arm"]] = r
items = [k for k,v in by.items() if len(v)==3]
n = len(items)

def disc(a, b):
    """discordance fraction for a paired binary endpoint"""
    n01 = sum(1 for i in items if by[i][a]["correct"] and not by[i][b]["correct"])
    n10 = sum(1 for i in items if not by[i][a]["correct"] and by[i][b]["correct"])
    return (n01+n10)/n, n01, n10

def mde_binary(pi_d, n, alpha=0.05, power=0.80):
    """MDE for a paired binary difference (McNemar), normal approximation."""
    if pi_d <= 0: return float('nan')
    z_a = 1.959964; z_b = 0.8416212
    # sd of the paired difference = sqrt(pi_d / n)
    sd = math.sqrt(pi_d / n)
    return (z_a + z_b) * sd

def mde_continuous(vals, alpha=0.05, power=0.80):
    if len(vals) < 2: return float('nan')
    m = sum(vals)/len(vals)
    sd = math.sqrt(sum((v-m)**2 for v in vals)/(len(vals)-1))
    se = sd/math.sqrt(len(vals))
    return (1.959964 + 0.8416212) * se

print("=== MDE at n = %d, 80%% power, alpha = 0.05 ===" % n)
print()
print("%-34s %10s %12s" % ("comparison / endpoint","discord","MDE"))
for a, b, label in [("content","function","PLANT content vs function"),
                    ("geometry","structure","family: geometry vs structure"),
                    ("geometry","clean","noise vs clean")]:
    if a == "geometry":
        continue
    pi, n01, n10 = disc(a,b)
    print("%-34s %9.3f %11.4f" % (label+" acc", pi, mde_binary(pi, n)))
print()
print("=== the same, on the earlier endpoint run (n = 150) ===")
for rate in ["0.12","0.3","0.5"]:
    P2 = pathlib.Path(rf"E:\2026-AI4S\autoresearch\measurement\out\propa_endpoint_{rate}.jsonl")
    if not P2.exists(): continue
    rows2 = [json.loads(l) for l in P2.read_text(encoding="utf-8").splitlines() if l.strip() and '"correct"' in l]
    b2 = defaultdict(dict)
    for r in rows2: b2[r["item_id"]][r["arm"]] = r
    ks = [k for k,v in b2.items() if len(v)==3]
    n2 = len(ks)
    def disc2(a,bb):
        n01=sum(1 for i in ks if b2[i][a]["correct"] and not b2[i][bb]["correct"])
        n10=sum(1 for i in ks if not b2[i][a]["correct"] and b2[i][bb]["correct"])
        return (n01+n10)/n2
    def disc2_cov(a,bb,t="0.8"):
        n01=sum(1 for i in ks if b2[i][a]["action"][t]=="answer" and b2[i][bb]["action"][t]!="answer")
        n10=sum(1 for i in ks if b2[i][a]["action"][t]!="answer" and b2[i][bb]["action"][t]=="answer")
        return (n01+n10)/n2
    pa = disc2("geometry","structure"); pc = disc2_cov("geometry","structure")
    print("  rate %-5s family acc: discord=%.3f MDE=%.4f | cov@0.8: discord=%.3f MDE=%.4f"
          % (rate, pa, mde_binary(pa,n2), pc, mde_binary(pc,n2)))
print()
print("=== and noise vs clean, where the harness DID fire ===")
for rate in ["0.12","0.3","0.5"]:
    P2 = pathlib.Path(rf"E:\2026-AI4S\autoresearch\measurement\out\propa_endpoint_{rate}.jsonl")
    if not P2.exists(): continue
    rows2 = [json.loads(l) for l in P2.read_text(encoding="utf-8").splitlines() if l.strip() and '"correct"' in l]
    b2 = defaultdict(dict)
    for r in rows2: b2[r["item_id"]][r["arm"]] = r
    ks = [k for k,v in b2.items() if len(v)==3]; n2=len(ks)
    def dc(a,bb,t="0.8"):
        n01=sum(1 for i in ks if b2[i][a]["action"][t]=="answer" and b2[i][bb]["action"][t]!="answer")
        n10=sum(1 for i in ks if b2[i][a]["action"][t]!="answer" and b2[i][bb]["action"][t]=="answer")
        return (n01+n10)/n2
    obs = sum(1 for i in ks if b2[i]["geometry"]["action"]["0.8"]=="answer")/n2 - \
          sum(1 for i in ks if b2[i]["clean"]["action"]["0.8"]=="answer")/n2
    pi = dc("geometry","clean")
    print("  rate %-5s cov@0.8 observed diff=%+.4f  MDE=%.4f  -> %s"
          % (rate, obs, mde_binary(pi,n2), "DETECTABLE" if abs(obs)>mde_binary(pi,n2) else "below MDE"))
