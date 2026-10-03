"""Quarantine arm 0 in the science state, and set out the from-scratch chain.

Read-modify-write rather than a fresh literal, so the parts of the file that are already right
(the scale rows, the predictions, the cost entries) are carried through untouched. Idempotent: run
it twice and the second run reports that the quarantine is already in place.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
P = ROOT / "config" / "science_state.json"

sci = json.loads(P.read_text(encoding="utf-8"))
if sci.get("arm0_status", {}).get("verdict", "").startswith("QUARANTINED"):
    print(f"[skip] {P.name} already carries the quarantine")
    sys.exit(0)

sci["arm0_status"] = {
    "verdict": "QUARANTINED - unusable as evidence",
    "_four_independent_reasons": [
        "1. The instrument was never calibrated. The backbone was changed before the pipeline was "
        "ever asked a question whose answer was already known, so a defect anywhere in encode, "
        "readout, metric or harness would have looked like a result.",
        "2. It cannot be reproduced. The harness has no resume and the run cost 17.43 h, so no second "
        "copy of this number is obtainable at a cost anyone would pay.",
        "3. It is one seed. This project's own gate is defined on a 3-seed mean, because per-seed sd "
        "is 0.0173; a single seed does not meet the bar the project set for itself.",
        "4. It trained in a pathological regime. Arm 0 peaked at 11,807 / 12,282 MiB = 96% of VRAM, "
        "the regime this project's own check_arm0_spec.py records as allocator-thrashing, and "
        "health.py validate has been reporting [FAIL] train_seconds outside [600, 21600] all along.",
    ],
    "_any_one_is_sufficient": "Any one of the four disqualifies the number. Together they settle it.",
    "_what_the_artefacts_still_are": (
        "Evidence of what happened and of what it cost -- 17.43 h of an 18.9 h total. The weights, "
        "the records and the meta.json are kept. What is withdrawn is the number's use as a data "
        "point, not its existence as a record."
    ),
    "_what_is_not_claimed": (
        "That the weights are wrong. Measured: every layer moved, mean |dw| between 5.8e-05 and "
        "9.7e-05, consistent with lr_base 5e-6 over 1,500 cosine steps, and the metric reproduces "
        "from the records. The process is what makes it unusable, and the process is the finding."
    ),
    "_src": "docs/APPROACH_REDISTILLED.md; evidence/arm0_audit.md; health.py validate",
}

for row in sci.get("scale", {}).get("rows", []):
    if row.get("who") == "ours":
        row["status"] = "QUARANTINED as evidence (see arm0_status) - kept as a record"
        row["backbone"] = row.get("backbone", "") + "  [arm 0: unusable]"

sci["from_scratch"] = {
    "_what": "The chain, in the order that makes each step checkable by the next. Arm 0 skipped "
             "steps 1-3 and went straight to the experiment, which is why its 17.43 h bought one "
             "number of unknown standing.",
    "steps": [
        {"n": 1,
         "what": "Calibrate: evaluate the source's own released 0.8B checkpoint with our harness "
                 "against its published 0.6175 / 0.6210 / 0.2690",
         "state": "running",
         "cost": "3.7 GiB download + ~40 min",
         "settles": "whether our numbers mean what we think. A match makes everything comparable; a "
                    "mismatch finds the defect for 40 minutes instead of 17 hours"},
        {"n": 2,
         "what": "Fix the cost: find the 92x against the source's own 0.8B -- 679 s for the same "
                 "1,500 steps -- and remove what is removable",
         "state": "probe data in hand: 11 step intervals, median 65 s, no trend over the interval",
         "settles": "whether an arm is hours or a day, which decides whether any arm is runnable"},
        {"n": 3,
         "what": "Establish comparability: the source's linear-attention layers run on the fla fused "
                 "kernel and ours fall back to torch",
         "state": "measured: transformers warns 'The fast path is not available ... Falling back to "
                  "torch implementation'",
         "settles": "what part of any difference is kernel numerics rather than method, since the "
                    "source's README states numbers compare only within one kernel stack"},
        {"n": 4,
         "what": "The decisive comparison: one arm at 0.6B, outside the fitted range, with 3 seeds "
                 "because the gate is a 3-seed mean",
         "state": "NOT BEFORE 1-3",
         "settles": "whether the law extends below 0.8B"},
    ],
}

P.write_text(json.dumps(sci, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"[OK] {P.name}: arm0 quarantined, {len(sci['from_scratch']['steps'])} from-scratch steps")
print(f"     verdict: {sci['arm0_status']['verdict']}")
