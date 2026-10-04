# Corpus location — an uncorrected claim, and what is actually known

**Correction, recorded 2026-10-04.** A previous turn reported "11,279 `.jsonl.gz` candidates on D:".
**That was wrong.** The command was a three-way `find ... -o ... -o ...` whose `*.jsonl.gz` branch
returned **nothing**; the count 11,279 came from the other two patterns, and I advanced a judgement on an
unverified number. A later, correctly-parenthesised search returns **zero** `.jsonl.gz` files under
`/d/2026-AI4S`. The correction is recorded rather than quietly fixed because the wrong figure was
already used to reason about where the corpus lives.

## What is actually established

| Claim | Status |
|---|---|
| `E:/2026-AI4S/c4_redownload` holds a corpus | **FALSE.** 35 MB, 9 files, all `.lock` / `.incomplete` / cache — an **interrupted download**, no corpus. |
| `D:/2026-AI4S/nhb-llm-mistranslation/c4_fdlh` holds a corpus | **FALSE.** 195 KB, 19 `.py` — that is the **pipeline code**, not data. |
| `*.jsonl.gz` files exist under `D:/2026-AI4S` | **FALSE** — zero. |
| A C4 governance record exists | **TRUE.** `E:/2026-AI4S/shard_health_registry.json`: generated `2026-08-08T16:28:19`, **21,504 shards expected**, languages `['ar','zh','fr','ru','es','en']`. **This is an operational record of what was planned, not evidence that the shards are on disk.** |
| Corpus-shaped directories exist on `E:` | **TRUE, but unverified in content**: `temporal_index_duckdb` (213 MB), `temporal_ngram_frequencies` (107 MB), `corpus_rsijev`. |

## What this means for the sense inventory

**The construct-validity claim in `docs/reviews/review_1_nature_2026.md` needs a corpus-built sense
inventory, and its falsification condition cannot be evaluated without one.** The inventory is therefore
**not yet available**, and no part of that claim may be presented as empirically supported.

**Consequences accepted:**

1. The review's **falsification condition stays untested** — already stated in that record, and this
   status confirms it rather than changing it.
2. C4 is **the natural source** (web text, English) and would need to be **downloaded**, not merely
   located. A sense inventory does not need TB-scale: expansion-frequency counts over a large-but-bounded
   English sample would suffice, so the 21,504-shard governance machinery is **not** a prerequisite
   and starting it would be the wrong move.
3. The prior scientific conclusions of that pipeline are **not** inherited. C4 would be used as **raw
   text**, nothing more.

## The one open question, for the owner

**Is there a usable English text corpus already on this machine that I have not found, or should a
bounded sample be downloaded?**

`D:` is at 98 % (177 GB free) and holds ~7.2 TB that the timed-out `du` did not enumerate from
`/d/2026-AI4S`; `E:` has 2.8 TB free. If a corpus exists elsewhere on `D:`, pointing at it saves a
download; if not, the inventory needs a bounded download to `E:`. **I am not going to start a
multi-terabyte download on the strength of a guess about which is cheaper** — that is the owner's call,
and the bounded option is likely sufficient.
