"""Prove check_doc_numbers can FAIL -- the negative control.

The BootLoops planted-truth rule: "a checker that has never fired is untested".
Each registered check class is broken once, in a throwaway copy, and must fire.
Nothing in the real tree is modified.
"""
import importlib.util, pathlib, shutil, sys, tempfile

REPO = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cdn", REPO/"scripts"/"check_doc_numbers.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def run_in_copy(mutate, label):
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        # minimal tree: the docs and artefacts the guard reads
        for rel in ["docs", "figures/data"]:
            src = REPO/rel
            if src.exists():
                shutil.copytree(src, tmp/rel)
        saved = m.REPO
        m.REPO = tmp
        try:
            mutate(tmp)
            rc = m.main()
        finally:
            m.REPO = saved
        print("  %-52s -> %s" % (label, "FIRED (exit 1)" if rc == 1 else "did NOT fire (exit 0)"))
        return rc == 1

results = []
# A: corrupt a registered number in the document
def a(t):
    p = t/"docs"/"PARADIGM_TYPING_AS_REGULATED_PROCESS.md"
    p.write_text(p.read_text(encoding="utf-8").replace("34.1%", "99.9%"), encoding="utf-8")
results.append(run_in_copy(a, "A: a registered claim number is corrupted"))

# B1: successor does not exist
def b1(t):
    p = t/"docs"/"PROPOSITION_A_CONTROL_LAW.md"
    p.unlink()
results.append(run_in_copy(b1, "B: the named successor is deleted"))

# B2: successor older than the document
def b2(t):
    p = t/"docs"/"PROPOSITION_A_MODEL_SIDE.md"
    p.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")   # touch -> newest
results.append(run_in_copy(b2, "B: the superseded doc is newer than its successor"))

# B3: successor not named in the first 12 lines
def b3(t):
    p = t/"docs"/"PROPOSITION_A_MODEL_SIDE.md"
    txt = p.read_text(encoding="utf-8")
    txt = txt.replace("docs/PROPOSITION_A_CONTROL_LAW.md", "elsewhere")
    p.write_text(txt, encoding="utf-8")
results.append(run_in_copy(b3, "B: the successor is not named at the top"))

# C: a retracted literal comes back
def c(t):
    p = t/"docs"/"PARADIGM_TYPING_AS_REGULATED_PROCESS.md"
    txt = p.read_text(encoding="utf-8")
    txt = txt.replace("| transposition | 25% | 4.6% | 0.18x |",
                      "| transposition | 25% | 8.9% |")
    p.write_text(txt, encoding="utf-8")
results.append(run_in_copy(c, "C: a retracted number is reinstated"))

# clean twin: must PASS
def clean(t): pass
with tempfile.TemporaryDirectory() as td:
    tmp = pathlib.Path(td)
    for rel in ["docs", "figures/data"]:
        src = REPO/rel
        if src.exists(): shutil.copytree(src, tmp/rel)
    saved = m.REPO; m.REPO = tmp
    try: rc = m.main()
    finally: m.REPO = saved
    print("  %-52s -> %s" % ("clean twin (must PASS)", "PASS (exit 0)" if rc == 0 else "FAILED"))
    results.append(rc == 0)

print()
print("SELF-TEST %s: %d of %d controls behaved correctly"
      % ("PASSED" if all(results) else "FAILED", sum(results), len(results)))
sys.exit(0 if all(results) else 1)
