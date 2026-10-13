# RRC v2.0.0 — RETIRED as an invalid measurement instrument

**Status:** retired 2026-10-11. Not a draft, not pending revision. **Do not use these files as data.**
Do not report a number computed from them. Do not build on them without a new corpus and a new
validity audit.

Files are in this directory with per-file sha256 in `MANIFEST.json`. 6 arms, 100,838 items.

## Why it was retired

Every structural guard passed — conservation through the gates, script purity, unit consistency,
provenance, rendering — and the corpus was still scientifically empty. **No guard asked whether an
ITEM is a valid measurement instrument**, so a corpus that cannot support its own claim passed 83
checks.

`scripts/audit_item_validity.py` asks that question, on every item, with no new data:

```
arm           layer       n  marginOK    edit   prefix  decoys0
rrc-en-word   L1      28217      0.0%   54.1%    59.9%     8.7%
rrc-en-word   L2      19668    100.0%   92.8%    52.8%     0.0%
rrc-en-word   L4      36116      0.0%   93.4%    88.1%    41.5%
rrc-en        L2       1106    100.0%   99.7%    74.5%     0.8%
rrc-zh        L2c      4335      0.0%   14.6%    14.6%    73.0%
rrc-zh        L1       1603      0.0%   20.1%    20.1%   100.0%
   ... 17 cells in total

POOLED over 100,838 items:  edit 72.9 %   prefix 63.9 %   length 38.9 %   substr 12.7 %
                            (chance = 20 %)
```

`edit` is a plain Levenshtein pick with **no linguistic knowledge of any kind**. It selects the root on
72.9 % of items, and on `rrc-en` on 99.7 %. The task as built does not measure root recovery; it
measures string distance.

**0 of 17 (arm, layer) cells are usable**, and the two failure modes are mutually exclusive:

| regime | signature | what it means |
|---|---|---|
| **solvable** | margin defined, `edit` 93–100 % | trivial — surface similarity IS the answer |
| **unanswerable** | margin undefined, `edit` 14–20 % (below chance) | no gradient at all; the fields point away from the root |

No cell satisfies both "the item is non-trivial" and "the difficulty is defined".

## The root cause: the decoys were drawn against the ROOT, not the STATE

A valid item requires **several candidates each of which could plausibly have produced the observed
state** — so that surface similarity cannot discriminate and only knowledge of the error channel can.
The corpus instead drew candidates from the root's surface neighbourhood, which admits exactly two
outcomes, both useless:

- decoys far from the state → "which candidate is nearest the state" is the answer. **Trivial.**
- decoys unrelated to the state → similarity is 0 for all of them → **no gradient, margin undefined.**

Two items from the same source record, `scrapy docs/intro/install.rst`, showing both regimes:

```
rrc-en-L2-00921   state 'Jessue' -> root 'Jessie'
   cands: Jessie, classified, easiest, Access, tries
   root->state 0.6   decoys->state [0.1818, 0.2222, 0.1429, 0.4]   margin 0.2  [defined]

rrc-en-L4-01013   same state, same root, same source record
   cands: confirmation, fundamental, Jessie, presenting, maintenance
   root->state 0.6   decoys->state [0.0, 0.1429, 0.0, 0.0]         margin None [undefined]
```

In the L2 entry the decoys `easiest`, `Access`, `tries` share letters and bigrams with the state and
carry no relation to it of any other kind. **The selection optimised for surface overlap — which is
precisely the dimension a string-distance heuristic reads.**

The same observation also appears in two layers, so the arms are not independent: n is inflated and
layer comparisons share observations.

## What a replacement must satisfy

1. **Candidates are generated from the state's perspective.** For an observed state `S`, enumerate
   every candidate `R_i` for which `P(S | R_i)` is non-negligible under the measured channel.
2. **Exactly one candidate may have a non-negligible channel probability.** If two or more do, the
   item is ambiguous and must be discarded, not kept as "hard".
3. **Difficulty is the gap between channel probabilities, not between surface similarities.** A
   surface-similarity margin is what makes a knowledge-free heuristic sufficient; a channel margin is
   what makes the measurement informative.
4. **The validity audit runs before any measurement.** `edit` must be near chance, `margin` must be
   defined, and both must hold in the same item.
5. **One observation yields one item**, or the layers must be shown to be independent.

## Consequence for the report

The measured accuracies taken with `LiquidAI/d1-3B` on this corpus (0.82–0.93 against a chance of
0.25) **cannot be reported as root-recovery ability.** A knowledge-free heuristic reaches 72.9 %
pooled and 99.7 % on `rrc-en`. Those figures are withdrawn, not qualified.
