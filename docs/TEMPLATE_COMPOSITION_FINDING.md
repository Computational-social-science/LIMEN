# The template imbalance is a composition fact, not a confound

**One measurement, one correction.** `scripts/template_confound_probe.py` reported the bank as 38x
imbalanced across templates, and its first verdict called that a confound requiring rebalancing. That
verdict was wrong. This document records why, with the numbers, because a wrong verdict that is merely
withdrawn is worth much less than one that is explained.

## What was measured

On the sealed 932-item bank, using the frozen generator
(`measurement/typo_noise.py:typo_noise(text, item_id, lam, seed) -> (text, ops)`, `lam` = target edits
per character, ladder of 7 values, 3 seeds):

| Check | Result |
|---|---|
| Condition completeness | **932 of 932** items appear in all **21** conditions (7 λ × 3 seeds); **0** incomplete |
| Template × λ orthogonality | **exact** — every template contributes the same item count at every λ |
| Template share of realised-rate variance | **η² = 0.0064**, i.e. **0.64 %** |

Per-domain composition is unchanged and still reported: info 38× (min 1, max 38), urgency 37×
(min 1, max 37), billing 4.83× (min 6, max 29), access 2.82× (min 11, max 31).

## Why the confound verdict was wrong

The design is **within-item**: every item is run at every λ and every seed, so a template's identity is
**constant across the contrast**. In a paired comparison, anything constant within a pair is
differenced out. Template composition is therefore a property of *which items are in the bank*, not a
property of *what varies between conditions*, and those are different questions.

The variance decomposition settles it independently of that argument: template accounts for **0.64 %**
of the variance in the realised edit rate — the only quantity through which a template could conceivably
leak into an estimate. The remaining 99.36 % is within-template, i.e. item-level, which is what the
design intends.

**And the concern is not merely overstated — it was the wrong question.** Rebuilding the bank to balance
templates would have changed 932 sealed items in response to a threat the design does not have, and
would have spent the credibility that a frozen bank is worth.

## What the imbalance does bound

Stating that it is not a confound is not the same as saying it is irrelevant. Two claims are bounded:

1. **Per-template and per-domain claims.** A statement about the `info:k04` template would rest on a
   single item. Domain-level statements are better supported but the `info` and `urgency` domains have
   thin templates, so a per-template breakdown within them is not interpretable.
2. **Generalisation beyond this bank.** The bank is four customer-service domains. Anything said about
   English typo noise in general rests on that sample being representative, and this measurement says
   the sample is unevenly drawn across its own templates.

Both belong in the manuscript's limitations, and neither requires touching a single item.

## Two negative controls that were broken and are now fixed

Both controls were checking my wording rather than my measurement, and both had to be rewritten.

- **The orthogonality control** built a bank where one template simply had more items, and the check
  correctly reported it as orthogonal — because under a within-item design template count is irrelevant
  to orthogonality. The control was testing item counts, which is not the quantity of interest. It now
  breaks the **design**: items that are not run at every λ, which is what a between-item confound
  actually looks like. This required `analyse()` to honour a per-row condition restriction, without
  which the completeness check enumerated the full grid for every row and could only ever report
  completeness — an unfalsifiable check.
- **The composition control** asserted on the string `"IMBALANCE"`, so it stopped passing the moment the
  verdict was rewritten to say what the number means. It now measures the spread itself (max/min ratio)
  and is indifferent to how the verdict is worded.

All three orthogonality controls and the composition control now pass, and the real bank is unchanged.

## Standing rule this establishes

**An imbalance in a factor's levels is not a confound until you have checked whether that factor varies
within the contrast.** The order matters: measure orthogonality first, then report composition. Doing
it the other way round produces a confident, actionable-sounding claim about a threat that was never
present — and costs a frozen artefact to act on.