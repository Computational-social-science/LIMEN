"""Build RRC -- the Root Recovery Corpus.

What this dataset is, and why it is a contribution rather than a by-product.

The study needs a task in which a decision model must recover a ROOT form from the
corrupted form that was actually observed, with several candidates in play. No such
dataset exists as a ready artefact, and one cannot be simulated: a generator's errors
are evidence about the generator (project rule 17), while what this study reasons about
is what people actually typed. So every item here is built from an observed human-error
corpus and states its source.

What makes the construction non-trivial, and therefore worth recording:

  * the answer side of each pair is established from the corpus itself, not assumed --
    Birkbeck's `$` line introduces the correct spelling, JWTD's `post_loss < pre_loss`
    holds for every kept revision, and CSCD's 0/1 label is exactly the discriminant
    between identical and differing text columns;
  * decoys are real forms of the same language drawn from the same corpus, so a
    candidate cannot be identified by being the only well-formed string;
  * the same construction is applied to three writing systems that span the
    orthographic-depth axis (alphabetic / syllabic / logographic), which is what makes
    an across-arm comparison meaningful;
  * every item carries its provenance, so any downstream number can be traced to the
    record it came from.

Determinism. One seed drives decoy selection and shuffling, so the file hashes are
reproducible and a rebuild either matches the manifest or has changed the construction.

v1.1. Version 1 drew decoy candidates at random from the corpus, which made the task
structurally trivial: an unrelated sentence is distinguishable from the state by surface
similarity alone, so a model could answer without any orthographic knowledge, and the
measured accuracies (0.82-0.93 against a 0.25 chance floor) reflected the easiness of the
construction rather than the ability under study. A candidate set that is not confusable
cannot measure recoverability, so decoys are now the *most similar* other roots: the set of
forms the state could plausibly have come from.

Similarity is a character-level Dice coefficient, computed by the same formula for every
arm, so the three arms are not given differently-shaped tasks. That is what keeps them
comparable: in an alphabetic script the corrupted form differs from its root at the
letters, while in a logographic script it can share the root's keystrokes and differ only
at the point of candidate selection -- which is the difference the study is about.

Two constraints make an item valid, and both are enforced rather than assumed:

  * every decoy differs from the root and from the other decoys;
  * the root is the *closest* candidate to the state. If a decoy is closer the item has no
    defensible answer and is dropped, with the drop counted so the loss is visible.

"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sys
import unicodedata

try:
    import regex as _regex
except Exception:  # noqa: BLE001
    _regex = None

# Standards-based infrastructure. Each of these replaces something that was hand-written and
# measurably wrong: the script *type* labels were asserted rather than looked up, and the
# keyboard neighbour table was a hand-drawn QWERTY that is the wrong instrument for French
# (whose first row is `a z e r t y u i o p`, not `q w e r t y u i o p`) and for Cyrillic.
try:
    from keyboard_channel import neighbours as _kb_neighbours, flick_groups as _kb_flicks
except Exception:  # noqa: BLE001
    _kb_neighbours = _kb_flicks = None

try:
    from alphabetic import WritingSystem as _WS
    _WS_SINGLETON = _WS()
except Exception:  # noqa: BLE001
    _WS_SINGLETON = None
import tarfile
from datetime import datetime, timezone

try:
    from GlotScript import sc as _script_of
except Exception:  # noqa: BLE001
    _script_of = None

# Paths are relative to the repository root, per the project's path rule.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPORA = os.environ.get("RRC_CORPORA_DIR") or os.path.join(os.path.dirname(REPO), "external-data")
OUT_DIR = os.path.join(REPO, "data", "rrc")
MANIFEST = os.path.join(REPO, "config", "rrc.json")

DATASET = "RRC"
VERSION = "2.0.0"
SEED = 20261016
# The largest span a word-level item may occupy. Beyond this the pair is not a word
# correction and the item cannot be made comparable across arms.
WORD_LEVEL_MAX = 24

N_OPTIONS = 5  # candidates per item; override with --options
LAYERS = ("L1", "L2", "L3", "L4")  # see the docstring; an item carries its layer

# Script composition is measured, not asserted. It is read from GlotScript (LREC 2024),
# which maps characters to ISO 15924 codes, because a hand-written label such as
# "syllabic (Japanese)" is not checkable and was in fact wrong: JWTD text is
# Hani+Hira+Kana mixed, and the GitHub Russian lines carry ~30% Latin from identifiers
# in code comments. Each arm declares which scripts may dominate and the gate below keeps
# only items that satisfy it; the measured composition is recorded on every item.
#   Zyyy is Unicode "Common" (spaces, punctuation) and is excluded from the shares.
ARM_SCRIPT_RULE = {
    "rrc-en":      {"dominant": {"Latn"}, "min_share": 0.90},
    "rrc-en-word": {"dominant": {"Latn"}, "min_share": 0.90},
    "rrc-ru":      {"dominant": {"Cyrl"}, "min_share": 0.90},
    "rrc-zh":      {"dominant": {"Hani"}, "min_share": 0.90},
    "rrc-zh-gh":   {"dominant": {"Hani"}, "min_share": 0.90},
    # Japanese is genuinely mixed; require a real kana presence and forbid foreign scripts.
    "rrc-ja":      {"dominant": {"Hani", "Hira", "Kana"}, "min_share": 0.95,
                    "require_any": {"Hira", "Kana"}, "min_require_share": 0.15},
}


def script_profile(text: str) -> dict:
    """ISO 15924 code -> share of non-Common characters."""
    if _script_of is None:
        return {}
    try:
        parts = _script_of(text)
    except Exception:  # noqa: BLE001
        return {}
    counts: dict = {}
    for code, chunk in parts.items():
        if code == "Zyyy":
            continue
        counts[code] = counts.get(code, 0) + len(chunk)
    total = sum(counts.values())
    if not total:
        return {}
    return {k: round(v / total, 4) for k, v in counts.items()}


def script_ok(arm: str, profile: dict) -> bool:
    rule = ARM_SCRIPT_RULE.get(arm)
    if not rule or not profile:
        return bool(profile)  # unmeasurable profile is not accepted
    share = sum(v for k, v in profile.items() if k in rule["dominant"])
    if share < rule["min_share"]:
        return False
    if "require_any" in rule:
        req = sum(v for k, v in profile.items() if k in rule["require_any"])
        if req < rule["min_require_share"]:
            return False
    return True
DECOY_POOL = 80  # similar roots considered per item, then the closest are taken

ARMS = {
    "rrc-en": {"script": "alphabetic", "language": "English", "depth": "shallow",
               "lang_code": "en",
               "corpus": "GitHub Typo Corpus prose (.md/.rst), lexicon-validated"},
    "rrc-en-word": {"script": "alphabetic", "language": "English", "depth": "shallow",
                    "lang_code": "en",
                    "corpus": "Birkbeck missp.dat (word-level; retained for comparison)"},
    "rrc-ru": {"script": "alphabetic (Cyrillic)", "language": "Russian",
               "depth": "shallow (segmental, non-Latin)", "lang_code": "ru",
               "corpus": "GitHub Typo Corpus, Cyrillic lines"},
    "rrc-ja": {"script": "syllabic", "language": "Japanese", "depth": "deep",
               "lang_code": "ja",
               "corpus": "JWTD test.jsonl (kana/kanji revisions)"},
    "rrc-zh": {"script": "logographic", "language": "Chinese", "depth": "deepest",
               "lang_code": "zh",
               "corpus": "CSCD all.tsv (IME errors)"},
    "rrc-zh-gh": {"script": "logographic", "language": "Chinese", "depth": "deepest",
                  "lang_code": "zh",
                  "corpus": "GitHub Typo Corpus, Han lines"},
}


def minimal_span(state: str, root: str) -> tuple:
    """The differing span of two strings that share a large common context.

    The observed Chinese pairs are whole sentences in which one word is wrong. Comparing
    them position by position assumes equal length and scattering the difference across the
    sentence, which is how an early version produced "replacements" like a 60-character
    sentence mapping to a single character: the pair had been aligned wrongly, not measured
    wrongly. Trimming the common prefix and suffix isolates the word that actually changed,
    which is the unit the channel operates on.
    """
    n = min(len(state), len(root))
    pre = 0
    while pre < n and state[pre] == root[pre]:
        pre += 1
    suf = 0
    while suf < n - pre and state[len(state) - 1 - suf] == root[len(root) - 1 - suf]:
        suf += 1
    return root[pre:len(root) - suf], state[pre:len(state) - suf]


def word_level_pair(state: str, root: str, max_len: int = 8) -> tuple:
    """(root_word, error_word) if a single short span accounts for the difference."""
    rw, ew = minimal_span(state, root)
    if not rw or not ew or rw == ew:
        return None
    if len(rw) > max_len or len(ew) > max_len:
        return None
    return rw, ew


def trim(text: str, limit: int = 64) -> str:
    return re.sub(r"\s+", " ", text).strip()[:limit]


def similarity(a: str, b: str) -> float:
    """Character-level Dice coefficient: 2|shared bigrams| / (|bigrams a| + |bigrams b|).

    Defined identically for Latin, kana and Han text -- it counts character bigrams and
    needs no word boundaries, which the logographic arm does not have. One formula
    everywhere is what keeps the arms comparable.
    """
    if unicodedata.normalize("NFC", a) == unicodedata.normalize("NFC", b):
        return 1.0
    ba, bb = bigrams(a), bigrams(b)
    if not ba or not bb:
        return 0.0
    return 2 * len(ba.intersection(bb)) / (len(ba) + len(bb))


def graphemes(text: str) -> list:
    """The text as user-perceived characters, after Unicode normalization.

    Two separate faults are handled here, and both are real rather than theoretical.

    Indexing. Python indexes code points, so "e" + U+0301 is two positions and slicing at
    an index can split it -- `len("é")` is 6 when the text has 5 graphemes. Every string
    measure below (bigrams, the Dice coefficient, the edit operations) slices, so the
    segmentation has to happen once, here.

    Normalization. Grouping alone is not enough: a grapheme cluster keeps whichever code
    points it was written with, so an NFD "é" and an NFC "é" segment correctly into one
    cluster each and still compare unequal, and their bigrams then disagree. NFC is
    applied first so that equivalent sequences become identical strings. Measured before
    the fix: identical-looking text scored 0.75 against itself.

    Falls back to code points if `regex` is absent, which the docstring records rather
    than hiding.
    """
    text = unicodedata.normalize("NFC", text)
    if _regex is None:
        return list(text)
    return _regex.findall(r"\X", text)


def _nfc(text: str) -> str:
    """Canonical form for anything that gets written out.

    The GitHub Typo Corpus contains CJK Compatibility Ideographs -- U+FA08 for 行, for
    instance -- which are legacy encodings of characters that Unicode also has in unified
    form. Without normalizing, the two are different strings to every measure here, so a
    compatible-ideograph line looks like it differs from its repair when it does not. The
    quality-control pass caught this on the emitted data, which is why the fix belongs at
    construction rather than only inside the similarity function.
    """
    return unicodedata.normalize("NFC", text)


def bigrams(text: str) -> set:
    """Character bigrams over grapheme clusters; a short string yields its clusters."""
    g = graphemes(text)
    if len(g) < 2:
        return set(g)
    return {g[i] + g[i + 1] for i in range(len(g) - 1)}


def bigram_index(roots: list[str]) -> dict:
    """bigram -> the roots containing it.

    Decoy selection needs, per state, the roots most similar to it. Computing that
    similarity against every root is quadratic -- with ~36k states and ~36k roots it is
    about 1.3e9 comparisons and made each build take minutes, which is too slow to
    iterate on the construction. Similar strings share bigrams, so the index restricts
    the comparison to roots that share at least one bigram with the state, and only falls
    back to the full list when that set is too thin to yield decoys.
    """
    index: dict = {}
    for r in roots:
        for b in bigrams(r):
            index.setdefault(b, []).append(r)
    return index


def candidates_for(state: str, roots: list, index: dict, want: int) -> list:
    """A bounded set of roots sharing a bigram with `state`.

    Bigram overlap is a cheap filter but not a tight one: a 120-character sentence shares
    some bigram with a large fraction of a 7k-sentence corpus, so ranking every survivor
    by similarity is still expensive once the objects are sentences rather than words.
    The set is therefore capped, and the cap is applied by a deterministic stride so the
    same state always yields the same candidates and rebuilds stay reproducible.
    """
    seen: set = set()
    for b in bigrams(state):
        for r in index.get(b, ()):
            seen.add(r)
    if len(seen) < want:
        return roots
    ordered = sorted(seen)
    cap = max(want * 25, 400)
    if len(ordered) > cap:
        stride = len(ordered) / cap
        ordered = [ordered[int(i * stride)] for i in range(cap)]
    return ordered


# "Is this a real word?" is answered by a frequency lexicon rather than a word list,
# because the arms are in different languages and wordfreq gives one interface for all.
# 3.0 zipf is roughly the top 100k forms: high enough that a misspelling never passes.
REAL_WORD_ZIPF = 3.0
NOT_A_WORD_ZIPF = 1.0


def is_real_word(word: str, lang: str) -> bool:
    from wordfreq import zipf_frequency
    return zipf_frequency(str(word).lower(), lang) >= REAL_WORD_ZIPF


def is_nonword(form: str, lang: str) -> bool:
    from wordfreq import zipf_frequency
    return zipf_frequency(str(form).lower(), lang) < NOT_A_WORD_ZIPF


# QWERTY rows, for the keyboard layer: a substitution to a key physically adjacent to the
# one typed. Meaningful for alphabetic scripts only -- a logographic error is usually a
# candidate-selection error at identical keystrokes, which no key-adjacency model expresses.
KEYBOARD_ROWS = ("qwertyuiop", "asdfghjkl", "zxcvbnm")


# The keyboard neighbour table per language, from the CLDR LDML layouts via
# keyboard_channel. Hand-written QWERTY was wrong for every non-English arm.
_KEYBOARD_CACHE: dict = {}


def adjacent_keys(ch, lang: str = "en") -> set:
    """Characters adjacent to `ch` on that language's layout, or empty if unavailable."""
    if _kb_neighbours is None or lang not in ("en", "ru", "fr", "pt", "bn", "sa"):
        return set()
    if lang not in _KEYBOARD_CACHE:
        try:
            _KEYBOARD_CACHE[lang] = _kb_neighbours(lang)
        except Exception:  # noqa: BLE001
            _KEYBOARD_CACHE[lang] = {}
    return set(_KEYBOARD_CACHE[lang].get(ch, ()))


def script_type_of(text: str) -> str:
    """The writing-system type, from the `alphabetic` module rather than asserted.

    The arms previously carried the words alphabetic / syllabic / logographic as prose. The
    module answers the same question from a table, and its answer for the Japanese arm is
    empty: the text mixes kanji and kana, so no single type applies -- which is the correct
    reading and corrects the arm's original "syllabic" label.
    """
    if _WS_SINGLETON is None:
        return "unknown"
    for t in ("logographic", "syllabary", "abugida", "abjad", "alphabet"):
        try:
            if getattr(_WS_SINGLETON, f"is_{t}")(text):
                return t
        except Exception:  # noqa: BLE001
            continue
    return "mixed" if text.strip() else "empty"


def keyboard_substitution(a: str, b: str, lang: str = "en") -> bool:
    """True when two equal-length forms differ at exactly one adjacent-key position.

    `lang` matters: the same two characters are neighbours on one layout and not on another,
    so a substitution is only a keystroke error with respect to the layout of the language
    being written.
    """
    if len(a) != len(b) or a == b:
        return False
    diffs = [(x, y) for x, y in zip(a.lower(), b.lower()) if x != y]
    return len(diffs) == 1 and diffs[0][1] in adjacent_keys(diffs[0][0], lang)


# ----------------------------------------------------- channel-based candidate layers

# Each script's confusable candidates must come from that script's own channel. Applying
# one string-similarity measure to all three was the earlier mistake: it is not that the
# measure was wrong, but that the three arms do not share a channel, so no single measure
# defines difficulty for all of them.
#
#   Hani        the channel is pinyin followed by candidate selection. A typo and its root
#               are phonetically identical -- 可服用度 / 可复用度 both read "ke fu yong du"
#               -- so the root is not recoverable from the surface at all, only by knowing
#               which character belongs. Candidates are the characters sharing the reading.
#   Latn/Cyrl   the channel is the keystroke; candidates are adjacent-key substitutions.
#   Hira/Kana   the channel is the kana reading, as for Hani.
#
# Measured spread of the Hani channel: one reading reaches 364 characters (yi), then
# ji 296, yu 280, xi 244, zhi 242. That count is the operational content of "depth" here.

try:
    from pypinyin import pinyin as _pinyin, Style as _PinyinStyle
except Exception:  # noqa: BLE001
    _pinyin = None

_HAN_RE = re.compile(r"[一-鿿]")
_CHAR_READING_CACHE: dict = {}


def han_char_reading(ch: str):
    """The pinyin of one Han character, or None."""
    if _pinyin is None:
        return None
    if ch in _CHAR_READING_CACHE:
        return _CHAR_READING_CACHE[ch]
    try:
        r = _pinyin(ch, style=_PinyinStyle.NORMAL)
        val = r[0][0] if r and r[0] else None
    except Exception:  # noqa: BLE001
        val = None
    _CHAR_READING_CACHE[ch] = val
    return val


def han_reading_index(chars) -> dict:
    """reading -> the characters that have it. Built once per arm."""
    index: dict = {}
    for ch in chars:
        r = han_char_reading(ch)
        if r:
            index.setdefault(r, []).append(ch)
    return index


# Character frequency per source corpus, built by scripts/build_han_frequency.py.
# Loaded lazily and once per source, because the reading-channel rank below needs it for every
# item -- and because the two Chinese arms do NOT share a frequency table: CSCD is news/legal
# prose (的一在中国人有是日了) while the GitHub slice is software prose (的用一是个数在以中有可这).
# Ranking one arm's items against the other arm's domain is a mismatched denominator, and it
# produced an apparent contradiction in the rank analysis that was an artefact of the table.
_HAN_FREQ_CACHE: dict = {}
_HAN_FREQ_SOURCE: dict = {}


def han_frequency(arm: str = "") -> dict:
    """character -> count in **this arm's own** source corpus.

    The IME layer's candidates share their reading by construction, so no string-similarity
    measure can rank them: the character-bigram coefficient is 0 for any two distinct single
    characters, and a reading-based measure is 1 for every pair because sharing the reading is
    the membership condition. What does discriminate is that an input method offers its
    candidates **ordered by frequency**. The root's rank in that order is the channel's
    difficulty for the item, and it is measurable from the same corpus the items are drawn from
    -- which is also the correct denominator, since the channel's difficulty is defined relative
    to the domain the writer is typing in, not to Chinese in general.

    `arm` selects the table: the file maps each arm to its source, and an arm with no mapping
    gets no table rather than another arm's. Returns an empty dict when the table is absent, so
    callers record the field as absent rather than as a fabricated value.
    """
    if arm in _HAN_FREQ_CACHE:
        return _HAN_FREQ_CACHE[arm]
    path = os.path.join(REPO, "data", "processed", "han_char_frequency.json")
    if not os.path.exists(path):
        _HAN_FREQ_CACHE[arm] = {}
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        tables = payload.get("tables") or {}
        mapping = payload.get("arm_source") or {}
        name = mapping.get(arm)
        if name is None and len(tables) == 1:
            # legacy single-table file: usable, but only if it is the only one there is
            name = next(iter(tables))
        table = tables.get(name) or {}
        _HAN_FREQ_CACHE[arm] = table.get("frequency") or {}
        _HAN_FREQ_SOURCE[arm] = name or "(none)"
    except Exception:  # noqa: BLE001
        _HAN_FREQ_CACHE[arm] = {}
        _HAN_FREQ_SOURCE[arm] = "(unreadable)"
    return _HAN_FREQ_CACHE[arm]


def han_frequency_source(arm: str = "") -> str:
    """The table name this arm was ranked against, or '(none)'. Recorded per item."""
    if arm not in _HAN_FREQ_SOURCE:
        han_frequency(arm)
    return _HAN_FREQ_SOURCE.get(arm, "(none)")


def _freq_table_summary() -> dict:
    """Provenance and cardinality of each frequency table, for the manifest.

    Read from the table file rather than restated, so the manifest cannot describe a table other
    than the one the ranks were actually computed from.
    """
    path = os.path.join(REPO, "data", "processed", "han_char_frequency.json")
    if not os.path.exists(path):
        return {"(absent)": {"error": "table file not found"}}
    try:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception:  # noqa: BLE001
        return {"(unreadable)": {"error": "table file could not be parsed"}}
    out = {}
    for name, t in (payload.get("tables") or {}).items():
        out[name] = {
            "source": t.get("source"),
            "detail": t.get("detail"),
            "rows_read": t.get("rows_read"),
            "rows_with_han": t.get("rows_with_han"),
            "han_total": t.get("han_total"),
            "distinct_characters": t.get("distinct_characters"),
            "ten_commonest": t.get("ten_commonest"),
        }
    return out


def han_channel_rank(root: str, reading_index: dict, freq: dict) -> tuple:
    """(rank, group_size) of `root` in its reading group ordered by corpus frequency.

    rank 1 means the input method would offer this character first for that reading, which makes
    the choice nearly free; a rank equal to the group size means it would be offered last. The
    two are returned together because a rank without its group size is not interpretable --
    being 9th of 9 is the hardest case and being 9th of 500 is not.

    Returns (None, group_size) when the frequency table is unavailable **or when the root was
    never observed in the table's corpus**, so the item records an absent field rather than a
    plausible-looking guess. The second case matters: a character absent from the table has count
    0, so it sorts to the end of its group by the code-point tie-break, and returning that position
    reports a rank decided by the character's Unicode value. That is not a measurement of what the
    input method would offer -- the method's order is a fact about usage, and there is no usage
    evidence for a character the corpus never contains. A guard checks this and found ~12 such
    items in rrc-zh before the case was handled.
    """
    rd = han_char_reading(root)
    group = reading_index.get(rd) or []
    if not group:
        return None, 0
    if not freq:
        return None, len(group)
    if freq.get(root, 0) <= 0:
        return None, len(group)
    ordered = sorted(group, key=lambda c: (-freq.get(c, 0), c))
    if root not in ordered:
        return None, len(group)
    return ordered.index(root) + 1, len(group)


def han_channel_candidates(state: str, root: str, reading_index: dict, n: int = 4) -> list:
    """Characters that could stand at the errored position because they share its reading.

    The position is located by comparing the state with the root. Candidates come from that
    one position's reading -- gathering them across every differing position mixes readings
    (an early version returned 叁 san with 时 shi) and produces a candidate set that is not
    a channel set at all. This is the IME candidate list, which is the layer a human
    actually chooses from at the keyboard.
    """
    if not reading_index or len(state) != len(root):
        return []
    for i, (a, b) in enumerate(zip(state, root)):
        if a == b:
            continue
        want = han_char_reading(root[i])
        if not want:
            return []
        out = [c for c in reading_index.get(want, ()) if c != root[i]]
        return out[:n]
    return []


# ---------------------------------------------------------- GitHub Typo Corpus

GH_PATH = os.environ.get("RRC_GH_TYPO") or os.path.join(
    os.path.dirname(REPO), "external-data", "GitHub_Typo_Corpus",
    "github-typo-corpus.v1.0.0.jsonl")
GH_PROSE_EXT = {"md", "rst", "txt", "adoc"}
WORD_RE = re.compile(r"[A-Za-z]{3,}")
HAN_RE = re.compile(r"[一-鿿]")
CYR_RE = re.compile(r"[Ѐ-ӿ]")


def _github_iter(script: str):
    """Yield (state, root, errored_form, prob_typo, source_record) from the GitHub corpus.

    The corpus marks an edit `is_typo`, but that label does not separate a spelling
    mistake from a formatting change -- `function(){` -> `function() {` carries
    prob_typo 0.939. So the label is not used. An edit is taken only when it is a single
    character substitution inside one word, the errored form is not a word, and the
    repaired form is a common one; those conditions are what make it a spelling error.
    """
    if not os.path.exists(GH_PATH):
        return
    seen = set()
    with open(GH_PATH, encoding="utf-8") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            for e in (d.get("edits") or []):
                src = e.get("src") or {}
                tgt = e.get("tgt") or {}
                st, tt = src.get("text") or "", tgt.get("text") or ""
                if not st or st == tt or len(st) > 200:
                    continue
                path = src.get("path") or ""
                m = re.search(r"\.([A-Za-z0-9]{1,6})$", path)
                ext = m.group(1).lower() if m else ""

                if script == "en":
                    if ext not in GH_PROSE_EXT or HAN_RE.search(st) or CYR_RE.search(st):
                        continue
                    a, b = st.split(), tt.split()
                    if len(a) != len(b):
                        continue
                    diffs = [(x, y) for x, y in zip(a, b) if x != y]
                    if len(diffs) != 1:
                        continue
                    x, y = diffs[0]
                    if len(x) != len(y) or not (WORD_RE.fullmatch(x) and WORD_RE.fullmatch(y)):
                        continue
                    if sum(c != d for c, d in zip(x, y)) != 1:
                        continue
                    xc = x.strip(".,;:!?()[]{}'\"`*|_#-")
                    yc = y.strip(".,;:!?()[]{}'\"`*|_#-")
                    # the errored form is not a word and the repair is a common one
                    if not (is_nonword(xc, "en") and is_real_word(yc, "en")):
                        continue
                    key = (st, yc)
                    if key in seen:
                        continue
                    seen.add(key)
                    yield {"state": st[:180], "root": yc, "err": xc,
                           "lang": "en",
                           "source_record": f"{d.get('repo','')[:60]} {src.get('path','')}",
                           "prob_typo": e.get("prob_typo")}
                elif script == "zh":
                    if not (HAN_RE.search(st) or HAN_RE.search(tt)):
                        continue
                    if HAN_RE.search(st) and not HAN_RE.search(tt):
                        continue
                    key = (st, tt)
                    if key in seen:
                        continue
                    seen.add(key)
                    yield {"state": st[:180], "root": tt[:180], "err": "",
                           "lang": "zh",
                           "source_record": f"{d.get('repo','')[:60]} {src.get('path','')}",
                           "prob_typo": e.get("prob_typo")}
                elif script == "ru":
                    if not (CYR_RE.search(st) and CYR_RE.search(tt)) or st == tt:
                        continue
                    key = (st, tt)
                    if key in seen:
                        continue
                    seen.add(key)
                    yield {"state": st[:180], "root": tt[:180], "err": "",
                           "lang": "ru",
                           "source_record": f"{d.get('repo','')[:60]} {src.get('path','')}",
                           "prob_typo": e.get("prob_typo")}


def source_github_en():
    return list(_github_iter("en"))


def source_github_zh():
    return list(_github_iter("zh"))


def source_github_ru():
    return list(_github_iter("ru"))




# ----------------------------------------------------- the measured keyboard channel

# The substitution set actually observed in human typing, estimated from 136M Keystrokes
# (Dhakal, Feit, Kristensson & Oulasvirta, CHI 2018) over 1,500 participants. Each entry is
# (intended character, observed character, count). Using the measured set rather than a
# declared layout is the difference between a channel and a hypothesis about one.
_CHANNEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "processed", "keystroke_channel.json")

try:
    with open(_CHANNEL_PATH, encoding="utf-8") as _fh:
        _CHANNEL_RAW = json.load(_fh)
    MEASURED_CHANNEL = [(w, g, n) for w, g, n in _CHANNEL_RAW.get("top_substitutions", [])]
    MEASURED_CHANNEL_SOURCE = _CHANNEL_RAW.get("source", "unknown")
except Exception:  # noqa: BLE001
    MEASURED_CHANNEL = []
    MEASURED_CHANNEL_SOURCE = "unavailable"

# Arms that can carry an L3 layer: eligible on provenance AND word-level. Currently EMPTY,
# and both halves of that condition are why.
#
# Measured over 1,500 participants, deletion (37.2%) and insertion (29.5%) together are two
# thirds of human typing errors, so L3 should be generated from those classes. It cannot be,
# here, for a structural reason rather than a coding one:
#
#   * rrc-en (GitHub prose) is eligible on provenance -- prose typed at a keyboard -- but its
#     roots are SENTENCES. Removing one character from a sentence yields a sentence with a
#     character missing, and the candidate set is then unrelated words, so the item cannot be
#     answered. Generated that way the layer produced 1,356 items, every one of that shape
#     (state: "...atomic orderr are the way to go.", cands: After/Added/Cashier/Bearer).
#   * rrc-en-word (Birkbeck) is word-level and would support the layer, but its errors are
#     word-level misspellings from a collection whose compiler describes it as including young
#     children and extremely poor spellers. It is not a keyboard corpus, so labelling it with
#     a keyboard mechanism would assert a provenance the corpus does not have.
#
# The layer is therefore disabled rather than left emitting unanswerable items. Enabling it is
# a data acquisition task -- a word-level English corpus of keyboard-origin errors -- and not
# a code change.
L3_ELIGIBLE_ARMS: set = set()


def deletion_states(root: str, min_len: int = 5) -> list:
    """The root with one character removed -- an observed deletion, at every position.

    Deletion is the largest single error class in human typing (37.2% of edits, measured over
    1,500 participants), so this is the class the L3 layer is generated from rather than the
    substitution class, which is under a tenth of errors and dominated by case pairs.
    """
    if len(root) < min_len:
        return []
    return [root[:i] + root[i + 1:] for i in range(len(root))]


def insertion_states(root: str, alphabet: str = "abcdefghijklmnopqrstuvwxyz") -> list:
    """The root with one extra character -- an observed insertion (29.5% of edits)."""
    return [root[:i] + c + root[i:] for i in range(len(root) + 1) for c in alphabet]


def measured_channel_candidates(root: str, limit: int) -> list:
    """Real words reachable from `root` by one substitution the channel actually contains.

    Substitutions are tried in descending channel count, so the decoys a model faces are the
    confusions that happen most in real typing rather than the ones that are merely
    string-close.
    """
    if not MEASURED_CHANNEL:
        return []
    out, seen = [], set()
    for pos, ch in enumerate(root):
        for intended, observed, _n in MEASURED_CHANNEL:
            if intended.lower() != ch.lower() or observed == intended:
                continue
            cand = root[:pos] + observed + root[pos + 1:]
            if cand == root or cand in seen:
                continue
            seen.add(cand)
            out.append(cand)
            if len(out) >= limit * 4:
                return out
    return out

def source_english():
    """Birkbeck: a `$` line introduces the correct spelling; following lines misspell it."""
    pairs, cur = [], None
    with open(os.path.join(CORPORA, "birkbeck", "missp.dat"), encoding="latin-1") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("$"):
                cur = line[1:].strip()
            elif cur:
                pairs.append({"state": line, "root": cur, "err": line,
                              "lang": "en", "source_record": f"${cur}"})
    return pairs


def source_japanese():
    """JWTD: pre_text carries the human error, post_text is the repair."""
    out = []
    path = os.path.join(CORPORA, "jwtd", "jwtd.tar.gz")
    with tarfile.open(path, "r:") as tf:
        members = [m for m in tf.getmembers() if m.name.endswith("test.jsonl")]
        if not members:
            return out
        handle = tf.extractfile(members[0])
        if handle is None:
            return out
        with handle as fh:
            for raw in fh:
                try:
                    d = json.loads(raw.decode("utf-8"))
                except Exception:  # noqa: BLE001
                    continue
                pre, post = d.get("pre_text"), d.get("post_text")
                pl, po = d.get("pre_loss"), d.get("post_loss")
                if not pre or not post or pre == post:
                    continue
                if pl is None or po is None or not (po < pl):
                    continue
                out.append({"state": trim(pre, 120), "root": trim(post, 120), "err": "",
                            "lang": "ja",
                            "source_record": f"page={d.get('page')} cat={d.get('category')}",
                            "prob_typo": None})
    return out


def source_chinese():
    """CSCD: label 1 marks a pair whose columns differ; column 2 is the errored side."""
    out = []
    with open(os.path.join(CORPORA, "cscd", "all.tsv"), encoding="utf-8") as fh:
        for i, raw in enumerate(fh):
            p = raw.rstrip("\n").split("\t")
            if len(p) != 3 or p[0] != "1" or not p[1] or p[1] == p[2]:
                continue
            out.append({"state": p[1].strip(), "root": p[2].strip(), "err": "",
                        "lang": "zh", "source_record": f"CSCD-NS row {i}",
                        "prob_typo": None})
    return out


SOURCES = {
    "rrc-en": source_github_en,
    "rrc-en-word": source_english,
    "rrc-ru": source_github_ru,
    "rrc-ja": source_japanese,
    "rrc-zh": source_chinese,
    "rrc-zh-gh": source_github_zh,
}


def build_arm(arm: str, records: list[dict], stats: dict) -> list[dict]:
    """Emit items at every layer a record supports; the layer is recorded on the item.

    Earlier versions pinned one candidate rule and filtered out any item where a decoy sat
    closer to the state than the root did. That filter was the wrong response to the right
    observation. A decoy closer to the surface form is not a broken item -- it is the
    informative one, because preferring the root there requires the source model
    P(root) rather than surface similarity to the observation. So nothing is dropped for
    that reason; the margin is recorded and the analysis stratifies on it.

    Layers, each harder than the one before:

      L1  other observed error realisations of the same root   (corpus-internal, ~18% of items)
      L2  real words one character substitution from the root  (source model vs surface)
      L3  real words one adjacent-key substitution away        (the keyboard channel)
      L4  unrelated real words                                 (the easy control)
    """
    rng = random.Random(SEED)
    lang = ARMS[arm].get("lang_code", "en")

    # Normalize once, at the boundary where records enter, rather than at each place that
    # writes them out. The GitHub corpus carries CJK Compatibility Ideographs (U+FA08 for
    # 行), so the same character arrives in two different spellings; normalizing only at
    # emission left the root normalized but the candidate list built from the un-normalized
    # form, and the quality-control pass rejected the item because the root was then absent
    # from its own candidates. One boundary normalizes the whole chain below it.
    records = [{**r,
                "state": _nfc(r["state"]),
                "root": _nfc(r["root"]),
                "err": _nfc(r.get("err") or "")}
               for r in records]

    # Reduce every record to the span that actually differs, so `state` and `root` are the
    # same kind of thing in every arm. Two problems are fixed here at once:
    #
    #   * rrc-en stored the whole sentence as `state` and the corrected word as `root`, an
    #     item asking which word is the root of a 160-character passage -- 92% of that arm;
    #   * the arms disagreed on the unit (word-level for rrc-en-word, sentence-level for the
    #     rest), so cross-arm comparison would have compared units as much as scripts.
    #
    # The extraction is `word_level_pair`, which trims the common prefix and suffix. It is
    # already used for the Chinese arms, where it recovers the word pair for 97.5% of items.
    # A record whose difference no short span accounts for cannot be made word-level and is
    # dropped here and counted, rather than emitted in the old shape.
    reduced, dropped_unit = [], 0
    for r in records:
        # Prefer the loader's own word-level error when it has one. For rrc-en the loader
        # already extracted it (`err='orderr'` for root 'orders'); the defect was that
        # `state` was set to the sentence instead. Deriving the span from the sentence and
        # the word gives a span the size of the sentence, which is why the first version of
        # this fix dropped 1,309 of 1,499 records.
        err = (r.get("err") or "").strip()
        root = r["root"]
        if err and err != root and len(err) <= WORD_LEVEL_MAX and len(root) <= WORD_LEVEL_MAX:
            reduced.append({**r, "state": err, "root": root})
            continue
        pair = word_level_pair(r["state"], r["root"])
        if pair is not None:
            root_word, error_word = pair
            reduced.append({**r, "root": root_word, "state": error_word,
                            "err": err or error_word})
            continue
        if len(root) <= WORD_LEVEL_MAX and len(r["state"]) <= WORD_LEVEL_MAX:
            reduced.append(r)
        else:
            dropped_unit += 1
    records = reduced
    stats["dropped_unit"] = stats.get("dropped_unit", 0) + dropped_unit

    roots = sorted({r["root"] for r in records})

    # L1 needs a root observed with more than one distinct error.
    variants: dict = {}
    for rec in records:
        err = rec.get("err") or ""
        if err:
            variants.setdefault(rec["root"], set()).add(err)

    # L4's pool: real words from this arm, for unrelated decoys.
    l4_pool = [r for r in roots if is_real_word(r, lang)] if lang in ("en", "ru") else roots
    # The bigram index keeps the nearest-neighbour ranking below from going quadratic.
    index = bigram_index(roots)
    # For a logographic arm the channel is the reading, so the candidate set comes from a
    # reading index over the characters this arm actually uses.
    reading_index: dict = {}
    if lang == "zh":
        # SORTED, NOT A BARE SET. `chars` was a set of str, and Python randomizes string hashing
        # per process, so han_reading_index() built each reading's character list in a different
        # order on every run. han_channel_candidates() takes the first n of that list, so the
        # candidate set -- and therefore rrc-zh and rrc-zh-gh -- changed from one rebuild to the
        # next: three builds gave three hashes (cc36daea, a37c87b4, f3cd8dee). The alphabetic
        # path was already order-independent and candidates_for() documents that requirement;
        # this arm was missed. Sorting gives one fixed order and makes the arm reproducible.
        chars = set()
        for r in records:
            chars.update(c for c in r["state"] + r["root"] if _HAN_RE.match(c))
        reading_index = han_reading_index(sorted(chars))

    items: list[dict] = []
    seen: set = set()
    dropped = 0
    dropped_script = 0
    dropped_margin = 0
    dropped_duplicate = 0
    dropped_no_layer = 0
    records_with_layer = 0
    items_attempted = 0
    layer_offered: dict[str, int] = {}
    for rec in records:
        state, root = rec["state"], rec["root"]
        if root in ("", None) or state == root:
            dropped += 1
            continue
        profile = script_profile(state)
        if not script_ok(arm, profile):
            dropped_script += 1
            continue

        cand_sets: list[tuple[str, list[str]]] = []

        # L1: other error realisations of the SAME root, as observed in the corpus.
        others = sorted(variants.get(root, set()) - {rec.get("err", "")})
        if len(others) >= N_OPTIONS - 1:
            cand_sets.append(("L1", others[:N_OPTIONS - 1]))

        # The logographic channel layer: characters sharing the reading of the errored
        # position. This is the layer an IME offers, and the layer the human error came
        # from, so it is the one the arm should be measured on.
        #
        # Restricted to single-character roots, because the channel as implemented is
        # character-level. `han_char_reading` on a multi-character string returns the reading of
        # its FIRST character only (三十 -> 'san', 可服用度 -> 'ke'), so constructing this layer
        # for a multi-character root drew candidates from an unrelated character's homophone
        # group -- candidates that are not candidates for the error at all. Measured before the
        # restriction, 761 of 5,096 L2c items were in that shape, and every one of them was also
        # the set whose frequency rank came back undefined. A multi-character reading channel is
        # a different construction and is not silently approximated here.
        if lang == "zh" and reading_index and len(root) == 1:
            ch_cands = han_channel_candidates(state, root, reading_index, N_OPTIONS - 1)
            if len(ch_cands) >= N_OPTIONS - 1:
                cand_sets.append(("L2c", ch_cands[:N_OPTIONS - 1]))

        # L2/L3 are ranked rather than thresholded. Requiring an exact edit distance of 1
        # yields fewer than one candidate for most words ("hexadecimal" has almost no
        # one-character real-word neighbour), so the layer is defined by how close the
        # decoys are instead: the nearest real words, taken in order of similarity.
        pool_for_rank = [r for r in candidates_for(state, l4_pool, index, DECOY_POOL) if r != root]
        near = sorted(pool_for_rank,
                      key=lambda r: similarity(r, root), reverse=True)[:max(DECOY_POOL, 40)]
        if lang in ("en", "ru") and len(near) >= N_OPTIONS - 1:
            # L2: the nearest real words by similarity, whatever their edit distance.
            cand_sets.append(("L2", near[:N_OPTIONS - 1]))
            # L3: generated from the deletion and insertion classes, which together are two
            # thirds of observed typing errors. The state is the root with one character
            # removed; the candidates are real words one character from that state, so the
            # item asks which word the typist meant -- the question the channel poses.
            #
            # Not built from the substitution set: measured, that class is under a tenth of
            # real errors and is dominated by shift-state pairs, so applying it produced decoys
            # differing from the root only in case (`rEceive`), which are trivially separable.
            # The class composition is in data/processed/keystroke_channel.json.
            if arm in L3_ELIGIBLE_ARMS:
                for l3_state, l3_layer in ((c, "L3del") for c in deletion_states(root)):
                    l3c = [w for w in candidates_for(l3_state, l4_pool, index, DECOY_POOL)
                           if w != root]
                    if len(l3c) >= N_OPTIONS - 1:
                        cand_sets.append((l3_layer, l3c[:N_OPTIONS - 1]))
                        break

        if len(l4_pool) > N_OPTIONS:
            pool = [w for w in l4_pool if w != root]
            rng.shuffle(pool)
            cand_sets.append(("L4", pool[:N_OPTIONS - 1]))

        # A record that survived the record-level gates can still yield nothing, because every layer
        # is conditional: L1 needs N_OPTIONS-1 other observed errors of the same root, L2c needs a
        # reading index and a single-character root, L2 needs enough similar roots in the pool. That
        # loss was not counted, and it is the largest single stage on some arms -- rrc-ja reads 7,701
        # records, drops 2,126 on the script gate and ships 1,076 items, so most of the 5,575 it kept
        # produced no layer at all. A funnel that omits its largest stage is not a funnel, and a
        # reader comparing arms would attribute the difference to the gates that happen to be
        # instrumented.
        if not cand_sets:
            dropped_no_layer += 1
            continue
        # How many records each layer was available for. A record can offer several layers, so these
        # sum above the record count; the point is to show WHICH layer is the bottleneck on an arm,
        # which the item counts alone do not.
        records_with_layer += 1
        for _l, _d in cand_sets:
            layer_offered[_l] = layer_offered.get(_l, 0) + 1
        items_attempted += len(cand_sets)

        for layer, decoys in cand_sets:
            key = (layer, state, root)
            if key in seen:
                # The second uninstrumented stage, found by the conservation assertion on its first
                # run: rrc-en attempted 2,828 items and accounted for only 2,447, and these are the
                # 381. The same (layer, state, root) triple can be offered twice when a corpus
                # records the same correction under more than one source line, and only the first is
                # kept. Counted rather than merely skipped, because an item-level funnel that omits
                # its dedupe stage does not close either.
                dropped_duplicate += 1
                continue
            seen.add(key)
            # The validity constraint, scoped to the layers it can apply to.
            #
            # The manifest states the rule flatly -- an item is kept only if the root is the
            # closest candidate to the state -- and a flat application of it is wrong, because
            # the layers are not the same kind of layer:
            #
            #   L2, L2c, L3del  candidates are RANKED against the state (nearest real words;
            #                   characters sharing the reading; words one character from the
            #                   deletion state). Here "the root must be closest" is the right
            #                   test, and an item failing it has no answer under the stated
            #                   metric.
            #   L1              candidates are OTHER OBSERVED ERROR REALISATIONS of the same
            #                   root, taken from the corpus. Nothing ranks them; they are not
            #                   decoys at all but alternative attested outcomes, and the root
            #                   is not expected to be nearest.
            #   L4              candidates are a RANDOM SHUFFLE OF THE POOL -- the unrelated-form
            #                   control. Applying the test here would be a category error: the
            #                   root is not supposed to be nearest, and requiring it would
            #                   destroy the control.
            #
            # Applying it flatly was tried and the cost is recorded: it cut rrc-zh from 12,351
            # items to 294, because the Chinese arm is almost entirely L2c, L4 and L1.
            # L2c is the IME channel, and its candidates are homophones BY CONSTRUCTION --
            # they share the reading of the errored position, which is the whole mechanism the
            # layer models. Neither a character-bigram margin nor a reading-based margin is
            # meaningful here: the first is 0 for every pair of distinct single characters, and
            # the second is 1 for every pair, because sharing the reading is the membership
            # condition. A ranked-similarity test would therefore admit nothing (margin exactly
            # 0 throughout) or everything.
            #
            # The quantity that does characterise difficulty for a frequency-ordered channel is
            # the SIZE of the candidate group: how many characters the IME offers for that
            # reading. That is recorded as the item's difficulty instead of a margin, and this
            # is why the manifest's margin field is null for L2c rather than zero.
            RANKED_LAYERS = ("L2", "L3del", "L3")
            root_sim = similarity(root, state)
            dec_sims = [similarity(d, state) for d in decoys]
            margin = (root_sim - max(dec_sims)) if dec_sims else None
            if layer in RANKED_LAYERS and margin is not None and margin <= 0:
                dropped_margin += 1
                continue
            if layer in RANKED_LAYERS:
                # margin is only defined where candidates are ranked against the state
                pass
            else:
                # L1 (other attested errors of the same root) and L4 (a shuffled sample of the
                # pool -- the unrelated-form control) are not ranked, so a margin is not
                # defined for them. The raw similarities remain in root_to_state and
                # decoys_to_state, so nothing is lost; only the derived difference is nulled,
                # because a null is the accurate value where the quantity has no meaning.
                margin = None
            if layer == "L2c":
                _rank, _gsize = han_channel_rank(root, reading_index, han_frequency(arm))
                group_rank = _rank
                group_size = _gsize or len(decoys) + 1
            else:
                group_rank = None
                group_size = None
            options = [root] + list(decoys)
            rng.shuffle(options)
            items.append({
                "item_id": f"{arm}-{layer}-{sum(1 for i in items if i['layer'] == layer):05d}",
                "arm": arm,
                "layer": layer,
                "script_type": script_type_of(root),
                "script": ARMS[arm]["script"],
                "language": ARMS[arm]["language"],
                "state": _nfc(state),
                "candidates": options,
                "root": _nfc(root),
                "n_options": N_OPTIONS,
                "difficulty": {
                    "root_to_state": round(root_sim, 4),
                    "decoys_to_state": [round(d, 4) for d in dec_sims],
                    # positive = the root is the closest candidate; negative = a decoy is
                    # closer, which is the case that requires the source model.
                    # None where the field is not defined for the layer: the unrelated-form
                    # control (L4) and the observed-variant layer (L1) are not ranked, and for
                    # the IME layer (L2c) the candidates are homophones by construction, so a
                    # similarity margin is either 0 or 1 throughout and carries nothing.
                    # `group_size` is the IME layer's equivalent and is the size of the
                    # character group the channel offers for that reading.
                    "margin": (round(margin, 4) if margin is not None else None),
                    "margin_defined": layer in ("L2", "L3del", "L3"),
                    # The IME channel's difficulty. `group_size` is how many characters the
                    # channel offers for that reading and `group_rank` is where the root sits in
                    # that group when it is ordered by corpus frequency, which is the order an
                    # input method presents. Rank 1 is the easiest possible item on this channel;
                    # rank == group_size is the hardest. The pair is recorded because a rank
                    # alone is not interpretable.
                    "group_size": group_size,
                    "group_rank": group_rank,
                    "group_rank_source": han_frequency_source(arm) if layer == "L2c" else None,
                },
                "script_profile": profile,
                "provenance": {
                    "kind": "observed",
                    "corpus": ARMS[arm]["corpus"],
                    "source_record": rec.get("source_record", ""),
                    "prob_typo": rec.get("prob_typo"),
                },
            })

    per_layer = {}
    for it in items:
        per_layer[it["layer"]] = per_layer.get(it["layer"], 0) + 1
    # CONSERVATION. Every record the loader returns leaves through exactly one record-level door:
    # the unit-consistency filter, empty-or-identical, the script gate, no-layer-available, or it
    # carries a question. And every item attempted leaves shipped, margin-dropped or duplicate.
    #
    # THE BASE MATTERS. `records` was rebound at the top of this function to the unit-filtered list,
    # so len(records) here is post-filter. An earlier version asserted against that and passed on
    # every arm while the manifest -- which publishes the count the LOADER returned -- did not
    # reconcile on four of six. Adding dropped_unit back reconstructs the loader's count, which is
    # the only base against which the identity is complete. A manifest-level guard is what caught
    # this, because it cannot be fooled by a rebinding inside the function.
    _n_in = len(records) + dropped_unit
    _shipped = sum(per_layer.values())
    _rec_sum = (dropped_unit + dropped + dropped_script + dropped_no_layer + records_with_layer)
    assert _n_in == _rec_sum, (
        "%s: record-level loss does not reconcile -- in=%d but unit=%d + dropped=%d + script=%d + "
        "no_layer=%d + with_layer=%d = %d"
        % (arm, _n_in, dropped_unit, dropped, dropped_script, dropped_no_layer,
           records_with_layer, _rec_sum))
    assert _shipped + dropped_margin + dropped_duplicate == items_attempted, (
        "%s: item-level loss does not reconcile -- shipped=%d + margin_dropped=%d + duplicate=%d "
        "= %d but attempted=%d"
        % (arm, _shipped, dropped_margin, dropped_duplicate,
           _shipped + dropped_margin + dropped_duplicate, items_attempted))
    assert _shipped == len(items), (
        "%s: per_layer tallies %d items but %d were built" % (arm, _shipped, len(items)))

    stats[arm] = {"dropped": dropped, "dropped_script": dropped_script,
                  "dropped_margin": dropped_margin, "dropped_duplicate": dropped_duplicate,
                  "dropped_no_layer": dropped_no_layer,
                  # The unit-consistency filter removes records BEFORE the loop this function counts
                  # in, so it was invisible to the record-level identity: `records` is rebound to the
                  # filtered list at the top, and the assertion below therefore compared against a
                  # smaller base and passed while the manifest, which measures the ORIGINAL list,
                  # did not reconcile. Found by the manifest-level guard, which is not fooled by the
                  # rebinding. The identity is complete only with this term in it.
                  "dropped_unit": dropped_unit,
                  "records_with_layer": records_with_layer, "items_attempted": items_attempted,
                  "layer_offered": layer_offered, "per_layer": per_layer}
    return items


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    global N_OPTIONS, VERSION
    if "--options" in sys.argv:
        N_OPTIONS = int(sys.argv[sys.argv.index("--options") + 1])
        # The option count is a build parameter and belongs in the version as a suffix; the BASE
        # does not. An earlier version of this line read `VERSION = f"1.2.0+n{N_OPTIONS}"`,
        # hard-coding a second base that disagreed with the module's own `VERSION = "2.0.0"`, so
        # the dataset carried one version in its code and another in its manifest, and the
        # statement audit held a third. One base, derived suffix.
        VERSION = f"{VERSION}+n{N_OPTIONS}"
    os.makedirs(OUT_DIR, exist_ok=True)
    manifest: dict = {
        "dataset": DATASET,
        "version": VERSION,
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed": SEED,
        "n_options": N_OPTIONS,
        "question_form": ("state is the observed corrupted form; choose which candidate "
                          "is its root"),
        "decoy_rule": ("on the ranked layers, the most character-similar other roots (Dice "
                       "bigram coefficient), one formula across the alphabetic arms; the IME "
                       "layer's candidates come from the reading index instead -- the characters "
                       "sharing the reading of the errored position -- and the unrelated-form "
                       "control (L4) draws a shuffled sample of the pool"),
        "validity_constraint": (
            "on the ranked layers (L2, L3del, L3) an item is kept only if the root is the "
            "closest candidate to the state under the arm's measure, so every retained item "
            "has a positive margin; the constraint does NOT apply to L1 (other attested error "
            "realisations of the same root -- not ranked, not decoys) or to L4 (a shuffled "
            "sample of the pool -- the unrelated-form control, where the root is not expected "
            "to be nearest). For the IME layer (L2c) the candidates are homophones by "
            "construction, so a similarity margin is 0 or 1 throughout and is recorded as null; "
            "that layer's difficulty is measured instead, by `group_size` (how many characters "
            "the channel offers for the reading) and `group_rank` (where in that group the root "
            "falls when the group is ordered by corpus frequency, which is the order an input "
            "method actually presents). Applying the constraint to every layer without "
            "this scoping cut rrc-zh from 12,351 items to 294."),
        "frequency_tables": {
            "why": ("Frequency is domain-specific, so each Chinese arm is ranked against its own "
                    "source rather than against a shared list. Measured top tens differ almost "
                    "completely between the two domains, and ranking one arm against the other's "
                    "domain produced an apparent contradiction in the rank analysis that was an "
                    "artefact of a mismatched denominator."),
            "per_arm": {arm: han_frequency_source(arm) for arm in ARMS},
            "tables": _freq_table_summary(),
        },
        "provenance_kind": "observed human error only; no simulated noise",
        "arms": {},
        "files": {},
        "known_limitations": [
            "Confusability is character-level; a proxy for the linguistic confusability "
            "the depth axis describes, not a measurement of it.",
            "Birkbeck states are single tokens while JWTD and CSCD states are sentence-length, "
            "so the arms differ in object size even with a shared decoy rule.",
            "Birkbeck is a pre-LLM-era spelling corpus; its errors are not keyboard-shaped.",
        ],
    }
    stats: dict = {}
    total = 0
    only = set()
    if "--arms" in sys.argv:
        only = {a.strip() for a in sys.argv[sys.argv.index("--arms") + 1].split(",") if a.strip()}
    # A partial rebuild must not rewrite the manifest as if it were the whole dataset: the arms
    # that were not rebuilt keep their previous entry, so a rerun of one arm cannot silently drop
    # the other five from the record.
    prev: dict = {}
    if only and os.path.exists(MANIFEST):
        try:
            with open(MANIFEST, encoding="utf-8") as fh:
                prev = (json.load(fh).get("arms") or {})
        except Exception:  # noqa: BLE001
            prev = {}
    for arm, loader in SOURCES.items():
        if only and arm not in only:
            if arm in prev:
                manifest["arms"][arm] = prev[arm]
                total += prev[arm].get("n_items") or 0
            continue
        records = loader()
        items = build_arm(arm, records, stats)
        path = os.path.join(OUT_DIR, f"{arm}.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for it in items:
                fh.write(json.dumps(it, ensure_ascii=False) + "\n")
        meta: dict[str, object] = dict(ARMS[arm])
        meta["n_items"] = len(items)
        meta["source_records"] = len(records)
        meta["file"] = os.path.relpath(path, REPO).replace("\\", "/")
        meta["sha256"] = sha256_file(path)
        meta["chance"] = round(1 / N_OPTIONS, 4)
        meta["dropped"] = stats[arm]["dropped"]
        meta["dropped_script"] = stats[arm]["dropped_script"]
        meta["dropped_margin"] = stats[arm].get("dropped_margin")
        # The two item-level stages besides the margin gate. The dedupe one was invisible until the
        # conservation assertion went in and refused to pass.
        meta["dropped_duplicate"] = stats[arm].get("dropped_duplicate")
        # The record-level stage that fired before the counting loop and was therefore absent from
        # the funnel: unit-consistency filtering. Published so the manifest's record account closes.
        meta["dropped_unit"] = stats[arm].get("dropped_unit")
        # The stage that was missing. Carried into the manifest so the figure and the tables read it
        # from the same place as every other count rather than from a recollection of it.
        meta["dropped_no_layer"] = stats[arm].get("dropped_no_layer")
        meta["records_with_layer"] = stats[arm].get("records_with_layer")
        meta["items_attempted"] = stats[arm].get("items_attempted")
        meta["layer_offered"] = stats[arm].get("layer_offered")
        meta["per_layer"] = stats[arm]["per_layer"]
        manifest["arms"][arm] = meta
        total += len(items)
        print(f"  {arm:<12} {len(items):>7} items  layers={stats[arm]['per_layer']}  "
              f"sha256={meta['sha256'][:12]}…", flush=True)
    manifest["total_items"] = total
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print(f"\n{DATASET} v{VERSION}: {total} items across {len(ARMS)} arms")
    print(f"manifest -> {os.path.relpath(MANIFEST, REPO)}")


if __name__ == "__main__":
    main()
