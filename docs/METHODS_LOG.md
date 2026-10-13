# Methods log

Process record for the RRC build and the measurement runs. This is deliberately **not** part of the
technical report: the report states results and the reasoning that supports them, and a reader who
wants the result should not have to walk past the history of how it was obtained. What is here is the
part that is true, load-bearing for reproducibility, and not a result.

---

## 1. Build order does not affect the output; the sampling scheme does

The report states that two measurement draws differ on the `rrc-zh` rank-1 contrast (z = −2.31 → −1.87,
crossing 0.05) and that the shape is what is relied on. An earlier draft attributed the difference to a
shared random stream: "adding British arms to a run shifts every later draw."

**That attribution is wrong**, and the corrected account is narrower than "the builds are
order-independent" — I wrote that first after testing one arm, and a second arm falsified it.

`rng = random.Random(SEED)` is constructed *inside* `build_arm` (`scripts/build_rrc.py [retired 2026-10-11 with R3]:848`), so each
arm's stream is fresh rather than shared. Measured, single arm against the full build:

| arm | invocation | single-arm sha256 | in full build | verdict |
|---|---|---|---|---|
| `rrc-ja` | `--arms rrc-ja` | `626d109d1f136541` | `626d109d1f136541` | byte-identical |
| `rrc-zh` | `--arms rrc-zh` | `a37c87b45339770c` | `cc36daea723c3454` | **differs** |

So the arm that carries the Han frequency tables and the input-method channel does **not** reproduce
from a single-arm invocation, while the arm that only uses the alphabetic path does. The two differ in
what they read: the Chinese arms rank candidates through `han_frequency()` / `han_channel_rank()`,
whose inputs are the arm's own frequency table and the reading-group index.

**Resolved — it was nondeterminism, and the cause was one line.** The discriminator ran:
`--arms rrc-zh` twice under the same conditions gave `a37c87b45339770c` and `f3cd8dee1fde020c`, against
`cc36daea723c3454` in the full build. Three builds, three hashes: not order-dependence, which would at
least be stable per arm, but ordinary run-to-run irreproducibility.

The site is `build_arm`, in the construction of the Han reading index:

```python
chars = set()                                    # a set of str
for r in records:
    chars.update(c for c in r["state"] + r["root"] if _HAN_RE.match(c))
reading_index = han_reading_index(chars)         # iterates it
```

Python randomizes string hashing per process, so `chars` iterates in a different order each run.
`han_reading_index()` builds each reading's character list in that order, and
`han_channel_candidates()` takes the **first n** of that list. The candidate set therefore changed
between rebuilds, and with it the items.

The alphabetic path does not have this problem and never did: `candidates_for()` sorts before it caps,
and its docstring states the requirement explicitly ("so the same state always yields the same
candidates and rebuilds stay reproducible"). The Chinese path was written later and missed it.

**Fix**: `han_reading_index(sorted(chars))`. One call, one fixed order.

**Verified on both arms, and the verification path had a flaw worth recording.**

| arm | build 1 | build 2 | |
|---|---|---|---|
| `rrc-zh` | `832e89ebff55da9d` | `832e89ebff55da9d` | identical |
| `rrc-zh-gh` | `854bf164a0e04b3d` | `854bf164a0e04b3d` | identical |

Both rebuilt twice with no `PYTHONHASHSEED` set. The defect is cleared on both arms that carried it.

An earlier attempt to confirm the mechanism by pinning `PYTHONHASHSEED=0` appeared to *refute* the fix:
two runs gave `9bca9392ca436afa` and `832e89ebff55da9d`. That test was invalid, because the patch was
applied to `build_rrc.py` **while the experiment was running**, so its first build used the old code and
its second the new one. The tell is that the second hash equals the two hashes from the post-fix test:
the "refutation" was measuring my own edit, not nondeterminism. **Do not edit the source under test
while a verification is in flight**; a long-running check must pin the revision it is testing.

**What the fix moved, and what it did not.** Items are stable — the `item_id` set and the layer
distribution (L1 1603, L2c 4335, L4 5652) are identical before and after. The **candidate lists** are
not: the `rrc-zh` L2c items offer different characters, because that is exactly what the slice was
changing. Since the candidate list *is* the measurement surface, the Chinese L2c accuracies must be
re-measured against the fixed build. An earlier statement in this log — that no published number moves
— was wrong for that reason and is withdrawn.

**Why no existing guard caught it, which is the part worth keeping.** Every guard in the suite compares
a build against a *specification* — conservation identities, layer agreement, frequency provenance. None
compared a build against *itself*. A pipeline can satisfy every identity and still emit different bytes
on every run. the build-reproducibility checker (retired 2026-10-11 with R3; see CURRENT_OBJECT.md) closes that gap: it builds one arm under two
different `PYTHONHASHSEED` values and requires the bytes to match, using two seeds rather than two runs
so the comparison is deterministic rather than a matter of luck. It uses `rrc-zh-gh`, the cheapest arm
that exercises the Han path — an alphabetic arm would pass the check while the defect remained.

**The rest of the class was audited and is clean.** Three functions in the builder return a `set`; each
was checked against every call site for an order-dependent use:

| helper | call sites | how the value is used | verdict |
|---|---|---|---|
| `script_profile()` | 1 | validity check, membership and counts | safe |
| `bigrams()` | 3 | `intersection()`; `sorted(seen)`; per-bigram lists appended in sorted-root order | safe |
| `adjacent_keys()` | 1 | `in` — set membership, not ordering | safe |

The audit's own detector raised a false positive on `adjacent_keys()`, flagging `diffs[0][1]` because it
matched a subscript pattern; that index belongs to a different expression. **`x in <set>` cannot be
order-dependent.** Worth recording because a detector that flags a safe call site invites a pointless
"fix", and an unnecessary edit to a working path is how a second defect gets introduced (the same
session produced two: a fabricated identifier and a broken JS string, both from edits that were not
needed).

The defect was therefore not a pattern waiting to recur elsewhere — it was one missed `sorted()` on one
path, now closed.

**Effect on published numbers.** Items are stable and the L2c accuracies are not. The `item_id` set and
the layer distribution (L1 1603, L2c 4335, L4 5652) are identical before and after, but the candidate
lists differ — that is precisely what the slice was changing — and the candidate list is the measurement
surface. **The Chinese L2c measurements were therefore re-run against the fixed corpus, not assumed
unchanged.** An earlier draft of this paragraph claimed no published number moved; that was wrong and is
withdrawn (see above). The four arms that do not use the Han path rebuilt to byte-identical hashes
(`rrc-en` `07d76e28`, `rrc-en-word` `fdf1c27a`, `rrc-ja` `626d109d`, `rrc-ru` `a1028ce5`), which confirms
the change is confined to the two Chinese arms.


The report's §5.10 originally said the two draws differed because of a shared random stream. That is
wrong for a different reason: the two draws used **different sampling schemes** (state-unit against
rank-unit), which select different items from the same corpus. A contrast moving across z = 0.05
between them is therefore expected and is not by itself evidence of nondeterminism.

---

## 2. Sampling unit must match comparison unit

Three schemes are in use, each for a named comparison, and mixing them produced a real error:

| scheme | unit of sampling | used for |
|---|---|---|
| `--by-state` | the record (`state`) | within-arm layer comparisons (L2c vs L4) |
| `--per-rank` / `--per-margin` | the difficulty value | cross-channel difficulty curves |
| `--per-layer` | the layer | cross-arm comparisons |

The L4-versus-L1 within-arm comparison originally failed not because of a weak effect but because the
two layers' state lengths are completely separated (`rrc-en` L4 tokens ∈ [62, 68] against L1 ∈ [69, 70],
zero overlap). A logistic fit on that separation returns a coefficient of 1e28 — the signature of
separation, not of an effect. Sampling by state removed it.

Cross-channel difficulty curves were initially unfair in the other direction: the Chinese arm used a
balanced quota while the English arm used its natural distribution, so §5.11 compared two different
sampling schemes. `--per-margin` now applies one scheme to all four arms.

---

## 3. Frequency-table provenance

The `rrc-zh` and `rrc-zh-gh` arms are ranked against **different** Han frequency tables — CSCD
(news/legal register) and GitHub Han (code register). Measured for 国: rank 22,964 in one table against
130 in the other, a 176× difference. Using one table for both arms inverted the rank effect on one of
them. `check_frequency_provenance.py` guards this in both directions: forward it confirms all 4,668
ranked items sit in the range of their own arm's table, and its negative control injects a defect and
requires it to be reported.

---

## 4. Two fabricated identifiers, found in the same session

Both were written from memory into a citation entry and both were wrong. Neither was visible to any
guard that existed at the time, and both were found only by fetching the address.

| entry | what was written | what the address actually serves |
|---|---|---|
| `kernighan1990` | `aclanthology.org/C90-2030`, pages 205–210 | a different paper (Lambek-calculus theorem proving); the Anthology records no page range for the real entry, `C90-2036` |
| `bender2013` | DOI `10.2200/S00509ED1V01Y201305HLT020` | nothing — HTTP 404, checked twice |

Two guards now exist for this class and neither was sufficient alone:

* `check_citation_links.py` — proves every in-text citation resolves to an entry, and every source in
  `config/datasets.json` appears in the reference list. Set comparison; it caught `zhao2026` sitting in
  a table cell with no resolvable link.
* `verify_reference_urls.py` — fetches each address and requires the page to identify itself as the
  work named. **Not in the guard suite**: it depends on remote hosts and a suite that fails when arXiv
  is slow teaches its operator to ignore it. Run it before circulating.

Neither would have caught the other's failure mode. A citation can resolve perfectly to an entry that
is entirely false.

---

## 5. A conversion that passed three guards while being invalid JavaScript

The reference list was converted from an array of strings to an array of `{key, text}` objects so a
citation could resolve to an entry. The second attempt consumed each entry's closing quote: all 27
values ended unquoted. The reference list was invalid JavaScript and would not have rendered.

`check_report_js_helpers.py`, `qc_report_structure.py` and `qc_report_citations.py` **all passed it**.
Three guards, for a document written in JavaScript, and not one of them parsed JavaScript.

`node` was on PATH throughout. `check_report_js_syntax.py` now extracts every inline `<script>` block
and runs `node --check` on it, with a negative control that requires an unquoted value to be rejected.
It caught the next occurrence of the same class within one run: an edit adding `book's` to an entry
terminated the string, and the guard named the block and the line.

The general lesson, which recurs four times in this session: **a check that does not parse the artifact
it audits will pass an artifact that cannot run.** Textual guards read a JavaScript document as prose.

This is also an argument for extracting the inline script to `viz/report/report.js`. A 64 KB blob inside
an HTML file cannot be linted, diffed or cached, and that invisibility is what let the breakage survive.

## 2026-10-11 — RRC v2.0.0 retired; the corpus-dependent toolchain went with it

`CURRENT_OBJECT.md` gains **R3**: the Root Recovery Corpus is retired as an invalid measurement
instrument (a knowledge-free Levenshtein pick selected the designated root on 72.9 % of 100,838 items,
99.7 % on `rrc-en`, against chance 0.20; 0 of 17 cells usable). `docs/POSTMORTEM_RRC_VALIDITY.md` holds
the mechanism.

Retired with it, because they exist only to serve it: the corpus files and manifest, the construction
code, the corpus configuration, ten corpus-specific scripts (profile, QC, data-statement regeneration,
measurement analysis, the d1 evaluator, the reproduction checker, the instrument-manifest builder, the
report-state exporter, the ranked-layers checker), and `docs/RRC_DATA_STATEMENT.md [retired 2026-10-11 with R3]` [retired 2026-10-11 with R3]. All are under
`archive/rrc-v2.0.0-INVALID/` with per-file sha256.

**Kept deliberately:** `scripts/audit_item_validity.py` — the check that condemned the corpus, now
pointed at the archive, and the standing gate any replacement must pass before it is used.

**Phase I is untouched.** The instrument (`measurement/item_bank.jsonl`, `measurement/typo_noise.py`,
`measurement/run_phase1.py`) never depended on the corpus, and Phase I's blockers remain O1 and O3.

**A second failure, distinct from the invalid instrument:** the corpus was Phase II material built while
Phase I is unsealed, which the live object's own sequencing forbids.
