# Erratum 1 to Amendment 1 — π_d was over-counted, and N is therefore conservative

**Filed:** 2026-10-04, **before** the pre-registration is sealed and **before** any confirmatory data
exists. **Amends:** `docs/PHASE_I_AMENDMENT_1.md` §A2. **Found by:** an independently written replay of
the pilot through the new `predict -> JSONL` runner (`measurement/run_phase1.py`), not by re-reading the
pilot's own report.

## What was wrong

Amendment 1 froze **`N_test = 652`** from **π_d = 0.2083 (25/120)**.

That figure counted **three kinds of item together**:

| Change, clean → mid | n | Is it a **discordant pair**? |
|---|---|---|
| correct → wrong | 16 | **yes** |
| wrong → correct | 6 | **yes** |
| `argmax` changed but the binary outcome did not ("relabel") | 3 | **no** |
| unchanged | 95 | **no** |

A relabel is an item that was **already wrong and remained wrong** — it simply became wrong in a
different way (its argmax moved to another non-gold option). **McNemar's π_d is the proportion of pairs
whose *binary outcome* differs.** A pair that is wrong on both sides is not discordant, and counting it
inflates π_d.

## The corrected figure

```
π_d = (16 + 6) / 120 = 22/120 = 0.1833     ->  N_test = 574,  bank = 819
```

## Why the frozen N is nevertheless KEPT at 652

**Because 652 is larger than 574, and in this formula a larger π_d demands a larger N.** With
α = 0.05 two-sided, power = 0.80, δ = 0.05:

| π_d | N_test |
|---|---|
| 0.1333 | 417 |
| **0.1833 (correct)** | **574** |
| 0.2083 (as filed) | 652 |

So the over-count pushed N **upwards**, and the frozen **652 exceeds the requirement at the correct
π_d**. The error is therefore in the **conservative** direction: no power is lost, and 78 extra items
are carried.

**Decision: keep `N_test = 652`.** Re-freezing downward would buy 78 items and cost a re-derivation;
the conservative figure is already frozen and remains valid. **The stated π_d is corrected to 0.1833
and the conservatism is recorded, so that a reader of the sealed document can see the arithmetic rather
than having to reconstruct it.**

## The error that was in the other direction, and the discipline that caught it

The replay script's **first** attempt computed π_d as the **correct → wrong count alone** = 16/120 =
**0.1333**, which would give **N_test = 417** — **below the requirement**, i.e. an under-powered design.

Both errors were **definitional, not observational**: the two independent implementations agreed on
every raw count (16 correct→wrong, 6 wrong→correct, 3 relabels, 104/120 clean accuracy **exactly**). The
disagreement was only ever about *which of those counts enters π_d*.

**That is the finding worth keeping.** A cross-implementation check that compares only a headline number
(`N`) would have shown a mismatch and told us nothing. The check that worked compared the **raw counts
item by item**, and both implementations agreed there — which is what localised the difference to a
definition rather than to the data. Clean accuracy reproduced to the item (104/120, difference +0.0000);
that agreement is what licenses trusting the rest of the comparison.

## Consequence for the analysis, stated before the run

**π_d must be defined in the analysis code, not left implicit**, and the definition is: *the proportion
of items whose binary outcome differs between the two conditions being compared*. Any item-level
breakdown reported alongside it must separate the four categories above, because collapsing them is
exactly how this error arose the first time.

## What is NOT changed

- `N_test = 652`, `bank = 932`, δ = 5 pp, α = 0.05, power = 0.80 — **all still frozen**.
- The decision rule, the endpoints, τ, ε, and every other Amendment 1 item.
- The zero-floor analysis of `SilentError@0.9` (Amendment 1 §A3), which does not depend on π_d.

**This erratum is the last change to O2.** After it, the pre-registration's sample size is closed.
