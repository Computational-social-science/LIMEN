"""Character frequency per source corpus, for the IME channel's difficulty.

Why this exists
---------------
The IME layer's candidates are the characters that share the reading of the errored position.
They are homophones *by construction*, which means no string-similarity measure can rank them:
the character-bigram Dice coefficient is 0 between any two distinct single characters, and a
reading-based measure is 1 for every pair, because sharing the reading IS the membership
condition. So "the root is the nearest candidate" -- the constraint that applies to the ranked
layers -- is not merely inapplicable to this layer, it is not expressible on it.

What does characterise an input method is that it offers its candidates **ordered by frequency**.
The root's position in that order is the channel's difficulty for that item: if the root is the
first character the IME offers for the reading, choosing it is nearly free; if it is the last of
fourteen, the choice is genuinely uncertain.

Why per corpus
--------------
Frequency is domain-specific, and the two Chinese arms come from different domains. Measured:

    CSCD        (news/legal prose)     的一在中国人有是日了
    GitHub Han  (software prose)       的用一是个数在以中有可这

`用` is second and `个` fourth in the GitHub slice and neither appears in the CSCD top ten. A
table from one corpus is therefore not a proxy for the other -- and using it as one produced a
contradiction in the rank analysis that looked like a failed hypothesis but was a mismatched
denominator. Each arm is now ranked against its own source, and the table it used is recorded
per arm.

Provenance
----------
CSCD counts come from its **training split only**, so a quantity describing the channel is not
estimated on rows designated for evaluation. The GitHub counts come from the typo corpus's own
edit pairs, which is the same release the arm draws its items from -- unavoidable, because that
release IS the arm's source, and it is stated rather than glossed. The GitHub slice is thin:
about four thousand of 203,000 lines carry Han characters, and that is a limitation of the arm
reported alongside the table rather than hidden by it.

Output
------
data/processed/han_char_frequency.json -- one table per source, each with its own counts, total,
distinct-character count and provenance, plus the arm -> source mapping.
"""
import collections
import json
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
CORPORA = pathlib.Path(os.environ.get("RRC_CORPORA_DIR") or (REPO.parent / "external-data"))
OUT = REPO / "data" / "processed" / "han_char_frequency.json"

CSCD_TRAIN = CORPORA / "cscd" / "train.tsv"
CSCD_WHOLE = CORPORA / "cscd" / "all.tsv"
GH_TYPO = CORPORA / "GitHub_Typo_Corpus" / "github-typo-corpus.v1.0.0.jsonl"

# which arm is ranked against which table
ARM_SOURCE = {"rrc-zh": "cscd", "rrc-zh-gh": "github_han"}


def is_han(ch: str) -> bool:
    return "\u4e00" <= ch <= "\u9fff"


def from_cscd() -> dict:
    src = CSCD_TRAIN if CSCD_TRAIN.exists() else CSCD_WHOLE
    if not src.exists():
        return {"error": "no CSCD file at %s or %s" % (CSCD_TRAIN, CSCD_WHOLE)}
    freq: collections.Counter = collections.Counter()
    rows = 0
    with open(src, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            rows += 1
            for ch in line:
                if is_han(ch):
                    freq[ch] += 1
    return {
        "source": "cscd/train.tsv" if src is CSCD_TRAIN else "cscd/all.tsv",
        "detail": "training split only" if src is CSCD_TRAIN else "whole release (train absent)",
        "rows_read": rows, "frequency": dict(freq.most_common()),
    }


def from_github_han() -> dict:
    if not GH_TYPO.exists():
        return {"error": "no GitHub Typo Corpus at %s" % GH_TYPO}
    freq: collections.Counter = collections.Counter()
    rows = 0
    han_rows = 0
    with open(GH_TYPO, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            rows += 1
            try:
                rec = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            blob = []
            for e in (rec.get("edits") or []):
                for side in ("src", "tgt"):
                    t = (e.get(side) or {}).get("text")
                    if t:
                        blob.append(t)
            h = [c for c in " ".join(blob) if is_han(c)]
            if h:
                han_rows += 1
                freq.update(h)
    return {
        "source": "GitHub_Typo_Corpus/github-typo-corpus.v1.0.0.jsonl",
        "detail": ("the arm's own release. Not a held-out split: this release IS the arm's "
                   "source, so the frequency and the items share rows. Stated, not glossed."),
        "rows_read": rows, "rows_with_han": han_rows, "frequency": dict(freq.most_common()),
    }


def main() -> int:
    tables = {}
    for name, fn in (("cscd", from_cscd), ("github_han", from_github_han)):
        t = fn()
        if "error" in t:
            print("  [FAIL] %s: %s" % (name, t["error"]))
            return 1
        freq = t.pop("frequency")
        total = sum(freq.values())
        if total == 0:
            print("  [FAIL] %s: no Han characters counted; refusing to write an empty table" % name)
            return 1
        t["han_total"] = total
        t["distinct_characters"] = len(freq)
        t["frequency"] = freq
        top = [c for c, _ in collections.Counter(freq).most_common(10)]
        t["ten_commonest"] = "".join(top)
        tables[name] = t

        # The file has to have been read as Chinese prose. The threshold is a majority of the ten
        # commonest characters of Chinese in general, not all ten, because frequency is
        # domain-specific -- which is the whole point of building one table per source.
        generic = set("的一是在了人我他有")
        if len(generic & set(top)) < 5:
            print("  [FAIL] %s: the commonest characters are %s, which is not Chinese prose"
                  % (name, "".join(top)))
            return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "arm_source": ARM_SOURCE,
        "note": ("One frequency table per source corpus. The IME layer's candidates are homophones "
                 "by construction, so a similarity measure cannot rank them; the input method "
                 "orders them by frequency, and the root's rank in that order is the layer's "
                 "difficulty. Frequency is domain-specific, so each arm is ranked against its own "
                 "source rather than against a shared list."),
        "tables": tables,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    for name, t in tables.items():
        print("  %-12s %s" % (name, t["source"]))
        print("               rows %s%s" % (f"{t['rows_read']:,}",
              (" (%s with Han)" % f"{t['rows_with_han']:,}") if t.get("rows_with_han") else ""))
        print("               Han %s across %s distinct"
              % (f"{t['han_total']:,}", f"{t['distinct_characters']:,}"))
        print("               commonest: %s" % t["ten_commonest"])
    print()
    print("  arm mapping  : %s" % json.dumps(ARM_SOURCE))
    print("  wrote %s (%s bytes)" % (OUT, f"{OUT.stat().st_size:,}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
