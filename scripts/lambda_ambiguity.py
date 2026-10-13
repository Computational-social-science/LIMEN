"""Quantify the lambda ambiguity: what is "the human error rate" for this channel?

The protocol fixes lambda_lo / lambda_mid as "target mean edits per token or per
character" with "e.g. ~5-8% character corruption" for lo and "~12-18%" for mid.
The generator applies Poisson(lambda * len(text)) edits to the CLEAN text.

So lambda names a rate of edits APPLIED TO THE INPUT. The question this script
answers with numbers: which human rate should lambda be calibrated to?

  (a) SURVIVING rate  -- errors visible in the final text. This is what the
      published paper reports (1.167%) and what any residual-text analysis can
      measure.
  (b) PRODUCED rate   -- errors the typist actually made, including those the
      typist's own monitor repaired. The corpus logs backspace with a timestamp,
      so this is measurable, and it is the rate that matches "input noise".

If (a) and (b) differ by a large factor, then a lambda calibrated on the published
number is NOT the typist's error rate, and every downstream conclusion inherits
that gap.
"""
import json, pathlib, sys
import pandas as pd, numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
C = pathlib.Path(r"C:\keystroke-out")

# surviving errors, from the transposition-aware measurement over 300,000 sentences
ta = json.loads((REPO/"figures"/"data"/"trans_aware.json").read_text(encoding="utf-8"))
dec = json.loads((REPO/"figures"/"data"/"decisive.json").read_text(encoding="utf-8"))
es2 = json.loads((REPO/"figures"/"data"/"error_structure2.json").read_text(encoding="utf-8"))

sections = es2["sections"]
target_chars = dec["pos_tot_clean"]["first"] + dec["pos_tot_clean"]["middle"] + dec["pos_tot_clean"]["last"]
surviving_edits = sum(ta["cls"].values())
backspaces = es2["backspaces"]

print("=== corpus basis (300,000 sentences) ===")
print("  sections                : %d" % sections)
print("  target characters       : %d" % target_chars)
print("  surviving errors        : %d" % surviving_edits)
print("  backspaces (repairs)    : %d" % backspaces)
print()
print("=== the two candidate rates, per target character ===")
r_surv = surviving_edits / target_chars
r_bs   = backspaces / target_chars
r_prod = (surviving_edits + backspaces) / target_chars
print("  (a) SURVIVING rate      : %.5f  (%.3f%%)" % (r_surv, 100*r_surv))
print("  (b) PRODUCED rate       : %.5f  (%.3f%%)   [= surviving + repairs]" % (r_prod, 100*r_prod))
print("      of which repairs    : %.5f  (%.3f%%)" % (r_bs, 100*r_bs))
print()
print("  ratio (b)/(a)           : %.2fx" % (r_prod/r_surv))
print()
print("=== what the published number measures ===")
print("  paper's uncorrected error rate : 1.167%%  (this is a SURVIVING rate)")
print("  our surviving rate             : %.3f%%   -> ratio to paper %.3f" % (100*r_surv, r_surv/0.01167))
print("  our produced rate              : %.3f%%   -> ratio to paper %.3f" % (100*r_prod, r_prod/0.01167))
print()
print("=== consequence for the frozen ladder ===")
print("  lambda_lo  = 0.05, lambda_mid = 0.18  (Amendment 3 v3)")
for name, lam in [("lo", 0.05), ("mid", 0.18)]:
    print("  lambda_%s = %.2f  -> %.1fx the SURVIVING rate, %.1fx the PRODUCED rate"
          % (name, lam, lam/r_surv, lam/r_prod))
print()
print("=== interpretation ===")
print("  The ladder sits ~4x ABOVE the surviving human rate and ~0.8x the produced")
print("  rate. So the ladder's INTENT is consistent with modelling produced noise,")
print("  while the paper number it is often compared against measures survivors.")
print("  A lambda calibrated on 1.167%% would be %.1fx too small for produced noise."
      % (r_prod/r_surv))
