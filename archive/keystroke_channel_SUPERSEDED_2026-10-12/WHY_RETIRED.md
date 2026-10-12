# WHY RETIRED — the keyboard channel estimate, 2026-10-12

**Retired**: `data/processed/keystroke_channel.json`, `scripts/estimate_keystroke_channel_aligned.py`,
`scripts/fig_keystroke_channel.py`, and the five rendered files `viz/figures/fig_keystroke_channel.*`.

**Not retired**: the question it was asking. The English keyboard channel
`P(observation | intended)` is still the right object; what is retired is this
particular estimate of it, because the estimate is wrong in a way that is now
measured rather than suspected.

---

## The defect

The estimator classified residual errors with `difflib` and had **no transposition
class**. `difflib` has none either: for a single adjacent swap it emits an
`insert` of a character, then one `equal` block, then a `delete` of the **same**
character. Measured on synthetic known edits, **93.4-100% of single transpositions
come back as an insert/delete pair.**

So every transposition in the corpus was silently scored as **one insertion plus
one deletion**, inflating both classes.

The estimator's own output shows the signature:

    edits by class: {shift_state 1804, key_adjacency 1019, other_substitution 882,
                     insert 3278, delete 4144}

`insert` + `delete` = 7,422 of 11,127 edits = **66.7%**, which is the number the
figure's panel (b) renders as "deletion 37% / insertion 29%". With transpositions
separated out, the same measurement on 300,000 sentences gives:

| class | this estimate (naive) | corrected (transposition-aware) |
|---|---|---|
| deletion | 37.0% | 34.1% |
| insertion | 30.5% | 27.2% |
| case / shift state | 16.2% | 16.5% |
| transposition | **absent** | 4.6% (8.8% if counted as 2 opcodes) |
| adjacent-key | 9.2% | 9.0% |

The composition is affected but not overturned; the **class inventory** is
missing a class, and the two largest shares are each inflated by about 3 points.

## Why it was retired rather than corrected in place

1. **The figure asserted a conclusion that is now known to be mis-stated.** Panel
   (b) reads "deletions and insertions are two-thirds of it" — which is partly an
   artefact of the missing class. The corrected figure is
   `figures/fig_error_structure.pdf`, built from a transposition-aware classifier
   validated at 96.5-100% recovery with 0% false positives on different-character
   pairs (`scripts/trans_aware.py`, with a self-test).
2. **The estimate was stale on a second axis.** It sampled 1,500 files / 22,500
   sections, whereas the replacement uses 20,000 files / 300,000 sections and
   reconciles against the corpus authors' own `metadata_participants.txt`.
3. **It was cited as a live Phase I result.** `docs/POSITIONING.md:167` said the
   English channel "was estimated in the dev pre-run
   (`scripts/estimate_keystroke_channel_aligned.py`)". Leaving the script in place
   would let that sentence keep pointing at a superseded measurement.

## What replaces it

| retired | replacement |
|---|---|
| `estimate_keystroke_channel_aligned.py` | `scripts/trans_aware.py` (transposition-aware, self-tested) |
| `keystroke_channel.json` | `figures/data/{trans_aware,h1h2,decisive,pos_all_classes,error_structure2}.json` |
| `fig_keystroke_channel.*` | `figures/fig_error_structure.{pdf,png,tiff}` + `FIG_ERROR_STRUCTURE_CAPTION.md` |
| the question, answered in prose | `docs/PARADIGM_TYPING_AS_REGULATED_PROCESS.md` |

The replacement reaches a **stronger** conclusion than the retired figure did.
The retired panel (b) argued that the published keyboard-noise generators are
built on a mechanism (key adjacency) that is under a tenth of real residual
error. That survives. What is new is that the deletion/insertion mass it
attributed to one process is in fact **two processes, double-dissociated by word
length** — geometry-indexed adjacent-key substitution is flat across word length
(0.98x from length 2 to 12) while deletion and insertion scale with it (2.5x and
4.9x; participant-clustered 95% CIs 1.07 [1.02,1.13], 1.79 [1.73,1.86], 2.83
[2.73,2.93]).

## Verification

`docs/ERROR_STRUCTURE_VERIFICATION.md` — an independent adversarial pass that
reproduced every class count, position cell and decile exactly (0 mismatches on 33
quantities) and confirmed the transposition detector against its own generator
(100% recovery, 0% false positives on different-character pairs).
