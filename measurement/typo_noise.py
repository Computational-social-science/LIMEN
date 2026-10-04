"""English typo-noise process N_en (Phase I deterministic generator).

Protocol reference: "Orthographic Channels and Input Noise as Structural
Disturbances in Human-Model Interaction", v1.1, section 4.2 (English typo
process N_en) and section 3.5 (JSONL trial record, field "typo_ops").

Contract
--------
typo_noise(text, item_id, lam, seed) is a pure function: the same
(text, item_id, lam, seed) input always returns the same perturbed text and
the same ordered list of applied operations.  This upholds the pre-registered
seed policy ("noise_seed in {0,1,2} per item and lambda, every triple
appearing exactly once": see SEEDS and LAMBDA_LADDER).

lam is the TARGET MEAN NUMBER OF APPLIED EDITS PER CHARACTER of text (so
0.08 asks for roughly 8% corruption).  The realised rate after one call is
len(ops) / len(text); realised_edit_rate() computes it.

Edit classes (protocol section 4.2, all four implemented):
  1. "adj"   - adjacent-key substitution on QWERTY (undirected neighbour map)
  2. "trans" - character transposition (swap with a neighbouring letter)
  3. "del"   - deletion of a letter
  4. "ins"   - insertion (a QWERTY-adjacent letter, or a random alphabet
               letter)

Each op is formatted "<class>:<before>-><after>", where <before> and <after>
are the whitespace-delimited token containing the edit, before and after that
edit; ops appear in application order.  The returned ops list is placed
verbatim into the JSONL "typo_ops" field (protocol section 3.5).

Documented judgement calls (the protocol leaves these open):
  * Only ASCII letters a-zA-Z are editable.  Whitespace and non-letter
    characters are never modified, so whitespace runs and token boundaries
    survive EXACTLY (the protocol asks only that they "generally survive" at
    low lambda).
  * The rate denominator is the full character count of text, spaces
    included, matching "edits per character".
  * Insertion "adjacent" means the inserted character is drawn from the
    QWERTY neighbours of the anchor character; double-press duplication is
    not emitted.
  * Default class mix is 0.35 adj / 0.25 trans / 0.20 del / 0.20 ins
    (DEFAULT_CLASS_WEIGHTS); freeze it in the pre-registration.
  * Protocol section 3.5 renders the op arrow as U+2192; this module emits
    ASCII "->" as required by the task specification and by the JSONL-shape
    regex ^(adj|trans|del|ins):.+->.*$ .  OP_ARROW is the single place to
    switch the arrow if the protocol rendering is preferred.
  * lam domain is [0.0, 4.0]; the pre-registered ladder tops out at 0.25.

Self-tests: run "python typo_noise.py" (exit code 0 = all self-tests pass).
"""

from __future__ import annotations

import hashlib
import math
import random
import re
import sys

__version__ = "1.0.0"

__all__ = [
    "typo_noise",
    "realised_edit_rate",
    "CLASS_NAMES",
    "DEFAULT_CLASS_WEIGHTS",
    "LAMBDA_LADDER",
    "SEEDS",
    "OP_ARROW",
]

#: Pre-registered readability ladder used to calibrate lambda_lo / lambda_mid.
LAMBDA_LADDER = (0.0, 0.03, 0.05, 0.08, 0.12, 0.18, 0.25)

#: Pre-registered seed policy: exactly one variant per (item, lambda, seed).
SEEDS = (0, 1, 2)

#: Arrow used inside the "typo_ops" strings.
OP_ARROW = "->"

#: Highest accepted lambda (per-character edit rate); ladder max is 0.25.
_LAM_DOMAIN_MAX = 4.0

# ---------------------------------------------------------------------------
# QWERTY keyboard model
# ---------------------------------------------------------------------------

QWERTY_ROWS = ("qwertyuiop", "asdfghjkl", "zxcvbnm")
_ROW_X_OFFSETS = (0.0, 0.5, 1.0)
_ADJACENCY_TOLERANCE = 1.2  # in units of key pitch


def _build_qwerty_neighbours() -> dict:
    """Undirected QWERTY adjacency: Euclidean distance <= 1.2 key pitches.

    Coordinates: x = column index + row offset, y = row index.  The offsets
    (0.0, 0.5, 1.0) reproduce the standard row stagger; the 1.2 tolerance
    includes horizontal and diagonal neighbours and excludes two-away keys.
    """
    coords = {}
    for y, (row, x_off) in enumerate(zip(QWERTY_ROWS, _ROW_X_OFFSETS)):
        for x, ch in enumerate(row):
            coords[ch] = (x + x_off, float(y))
    neighbours = {}
    for a, (ax, ay) in coords.items():
        near = []
        for b, (bx, by) in coords.items():
            if b == a:
                continue
            if math.hypot(ax - bx, ay - by) <= _ADJACENCY_TOLERANCE:
                near.append(b)
        neighbours[a] = tuple(sorted(near))
    return neighbours


_KEY_NEIGHBOURS = _build_qwerty_neighbours()

ALPHABET = "abcdefghijklmnopqrstuvwxyz"

CLASS_ADJ = "adj"
CLASS_TRANS = "trans"
CLASS_DEL = "del"
CLASS_INS = "ins"
CLASS_NAMES = (CLASS_ADJ, CLASS_TRANS, CLASS_DEL, CLASS_INS)

#: Default class mix (sums to 1.0); freeze this value in the pre-registration.
DEFAULT_CLASS_WEIGHTS = {
    CLASS_ADJ: 0.35,
    CLASS_TRANS: 0.25,
    CLASS_DEL: 0.20,
    CLASS_INS: 0.20,
}

# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------


def _is_ascii_letter(ch: str) -> bool:
    return ("a" <= ch <= "z") or ("A" <= ch <= "Z")


def _has_alnum(s: str) -> bool:
    return any(ch.isalnum() for ch in s)


def _token_span(s: str, i: int) -> tuple:
    """Span (start, end) of the whitespace-delimited token containing index i."""
    n = len(s)
    a = i
    while a > 0 and not s[a - 1].isspace():
        a -= 1
    b = i
    while b < n and not s[b].isspace():
        b += 1
    return a, b


def _count_letters(s: str, a: int, b: int) -> int:
    return sum(1 for ch in s[a:b] if _is_ascii_letter(ch))


def _editable_positions(s: str) -> list:
    return [i for i, ch in enumerate(s) if _is_ascii_letter(ch)]


def _derive_rng(item_id: str, lam: float, seed: int) -> random.Random:
    """Deterministic RNG for the (item_id, lambda, seed) triple.

    The seed comes from SHA-256 over a canonical UTF-8 rendering of the
    triple, so the stream is identical across calls and across processes.
    """
    payload = "N_en|{}|{}|{}".format(str(item_id), repr(float(lam)), int(seed))
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _poisson(rng: random.Random, mu: float) -> int:
    """Poisson(mu) sample, standard library only, deterministic per rng state.

    Knuth's multiplication method for mu <= 250; normal approximation
    (Box-Muller on the same rng) above that.  Expected value = mu in both
    branches.
    """
    if mu <= 0.0:
        return 0
    if mu > 250.0:
        u1 = max(rng.random(), 1e-300)
        u2 = rng.random()
        z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return max(0, int(round(mu + math.sqrt(mu) * z)))
    limit = math.exp(-mu)
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= limit:
            return k - 1


def _pick_weighted_class(rng: random.Random) -> str:
    draw = rng.random()
    acc = 0.0
    for cls in CLASS_NAMES:
        acc += DEFAULT_CLASS_WEIGHTS[cls]
        if draw < acc:
            return cls
    return CLASS_NAMES[-1]


def _format_op(cls: str, before: str, after: str) -> str:
    return "{0}:{1}{2}{3}".format(cls, before, OP_ARROW, after)


def _candidate_sets(working: str):
    """Feasible edit positions per class for the current working string.

    Returns None when the string contains no ASCII letter at all (no edit is
    possible).  Feasibility rules:
      adj  : any letter (every letter has at least one QWERTY neighbour)
      ins  : any letter (insertion anchor)
      trans: a neighbouring index with a DIFFERENT letter (so the swap always
             changes the string)
      del  : the token must keep at least one letter after the deletion
    """
    letters = _editable_positions(working)
    if not letters:
        return None
    n = len(working)
    trans_pos = []
    for i in letters:
        ch = working[i]
        for j in (i - 1, i + 1):
            if 0 <= j < n and _is_ascii_letter(working[j]) and working[j] != ch:
                trans_pos.append(i)
                break
    del_pos = []
    for i in letters:
        a, b = _token_span(working, i)
        if _count_letters(working, a, b) >= 2:
            del_pos.append(i)
    return {
        CLASS_ADJ: letters,
        CLASS_TRANS: trans_pos,
        CLASS_DEL: del_pos,
        CLASS_INS: letters,
    }


def _apply_one_edit(rng: random.Random, working: str):
    """Apply one sampled edit to working; return (new_text, op) or None.

    Returns None when no edit can be applied without violating the
    degenerate-output guards.
    """
    sets = _candidate_sets(working)
    if sets is None:
        return None
    feasible = [cls for cls in CLASS_NAMES if sets[cls]]
    if not feasible:
        return None

    cls = _pick_weighted_class(rng)
    if not sets[cls]:
        cls = feasible[rng.randrange(len(feasible))]
    positions = sets[cls]
    i = positions[rng.randrange(len(positions))]

    a, b = _token_span(working, i)
    n = len(working)

    if cls == CLASS_ADJ:
        original = working[i]
        options = _KEY_NEIGHBOURS[original.lower()]
        repl = options[rng.randrange(len(options))]
        if original.isupper():
            repl = repl.upper()
        new = working[:i] + repl + working[i + 1:]
        op = _format_op(cls, working[a:b], new[a:b])
    elif cls == CLASS_TRANS:
        partners = [
            j for j in (i - 1, i + 1)
            if 0 <= j < n and _is_ascii_letter(working[j]) and working[j] != working[i]
        ]
        j = partners[rng.randrange(len(partners))]
        lo, hi = (i, j) if i < j else (j, i)
        chars = list(working)
        chars[lo], chars[hi] = chars[hi], chars[lo]
        new = "".join(chars)
        op = _format_op(cls, working[a:b], new[a:b])
    elif cls == CLASS_DEL:
        new = working[:i] + working[i + 1:]
        op = _format_op(cls, working[a:b], new[a:b - 1])
    else:  # CLASS_INS
        anchor = working[i]
        near = _KEY_NEIGHBOURS[anchor.lower()]
        if near and rng.random() < 0.5:
            ins = near[rng.randrange(len(near))]
        else:
            ins = ALPHABET[rng.randrange(len(ALPHABET))]
        p = i if rng.random() < 0.5 else i + 1
        new = working[:p] + ins + working[p:]
        op = _format_op(cls, working[a:b], new[a:b + 1])

    # Degenerate-output guards: commit an edit only if the text stays
    # non-empty, keeps at least one alphanumeric character, and no token is
    # emptied (deletions never remove the last letter of a token).
    if not new or not _has_alnum(new):
        return None
    if cls == CLASS_DEL and _count_letters(new, a, b - 1) < 1:
        return None
    return new, op


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------


def typo_noise(text: str, item_id: str, lam: float, seed: int) -> tuple:
    """Apply N_en to text; return (perturbed_text, ordered_ops).

    Pure function of (text, item_id, lam, seed): identical inputs always give
    identical outputs.  lam is the target mean edits per character; the
    number of edits is drawn as Poisson(lam * len(text)), so the expected
    realised rate equals lam.  lam == 0.0 (or a text with no ASCII letters)
    returns (text, []).
    """
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    lam = float(lam)
    if lam < 0.0:
        raise ValueError("lam must be >= 0.0 (got {!r})".format(lam))
    if lam > _LAM_DOMAIN_MAX:
        raise ValueError(
            "lam = {!r} exceeds the supported domain [0.0, 4.0]".format(lam)
        )
    if lam == 0.0 or not text:
        return text, []

    rng = _derive_rng(item_id, lam, seed)
    n_edits = _poisson(rng, lam * len(text))

    working = text
    ops = []
    for _ in range(n_edits):
        applied = _apply_one_edit(rng, working)
        if applied is None:
            break
        working, op = applied
        ops.append(op)

    if _has_alnum(text) and not _has_alnum(working):
        raise RuntimeError("internal invariant violated: all alphanumeric content lost")
    return working, ops


def realised_edit_rate(clean_text: str, ops: list) -> float:
    """Realised edits per character: len(ops) / len(clean_text)."""
    if not clean_text:
        return 0.0
    return len(ops) / len(clean_text)


# ===========================================================================
# self-tests
# ===========================================================================

# Short service / routing intents (protocol section 4.3 domain: billing,
# access, urgency, info).  Used only by the self-tests below.
_ITEM_TEXTS = [
    "Please update the billing address on my account before the next invoice.",
    "I cannot access my workspace after the password reset this morning.",
    "My card was charged twice for the same subscription renewal yesterday.",
    "Urgent: the production database is unreachable and the site is down.",
    "Where can I download the invoice for last month's hosting plan?",
    "Please cancel the trial subscription before it renews next week.",
    "The verification email never arrived, so I am locked out of my account.",
    "Can you confirm whether my refund request has been approved yet?",
    "I need a copy of the contract for our records before Friday.",
    "The mobile app keeps crashing whenever I open the reports section.",
    "Please transfer this ticket to the billing department as soon as possible.",
    "Our team needs read-only access to the analytics dashboard.",
    "The payment failed even though the card details are correct.",
    "How do I change the email address linked to my profile?",
    "This is the second reminder about the broken link in the welcome guide.",
    "Please escalate this issue because the customer is waiting on a call.",
    "I would like to upgrade the storage plan for the shared drive.",
    "The two-factor code is not accepted on the new device.",
    "Can I get a receipt sent to the finance team for this purchase?",
    "Access to the archived projects was removed without any notice.",
    "The printer on the third floor shows an error about the toner cartridge.",
    "Please check why the order status has not changed since last Tuesday.",
    "We need the security report delivered before the audit begins.",
    "The webinar link expired, and I missed the first session.",
]

_OP_RE = re.compile(r"^(adj|trans|del|ins):.+->.*$")


def _make_items(count: int) -> list:
    """Deterministic bank of (item_id, text) pairs for the self-tests."""
    return [
        ("item_{:04d}".format(k), _ITEM_TEXTS[k % len(_ITEM_TEXTS)])
        for k in range(count)
    ]


def test_determinism() -> None:
    print("T1 DETERMINISM: 200 random (item_id, lambda, seed) triples, each called twice")
    chooser = random.Random(20261004)  # test-data rng, independent of N_en
    items = _make_items(32)
    digest = hashlib.sha256()
    mismatches = 0
    nonzero_ops = 0
    for _ in range(200):
        item_id, text = items[chooser.randrange(len(items))]
        lam = LAMBDA_LADDER[chooser.randrange(len(LAMBDA_LADDER))]
        seed = SEEDS[chooser.randrange(len(SEEDS))]
        out_a, ops_a = typo_noise(text, item_id, lam, seed)
        out_b, ops_b = typo_noise(text, item_id, lam, seed)
        if out_a != out_b or ops_a != ops_b:
            mismatches += 1
        if ops_a:
            nonzero_ops += 1
        digest.update(
            "{}|{}|{}|{}|{}\n".format(item_id, lam, seed, out_a, " ".join(ops_a)).encode("utf-8")
        )
    assert mismatches == 0, "{} of 200 triples were not reproducible".format(mismatches)
    print("  triples checked: 200; mismatches: 0; triples with >=1 op: {}".format(nonzero_ops))
    print("  DIGEST sha256: " + digest.hexdigest())


def test_seed_independence() -> None:
    print("T2 INDEPENDENCE BY SEED: 24 items at lambda=0.12")
    items = _make_items(24)
    differing = 0
    for item_id, text in items:
        out_0a, ops_0a = typo_noise(text, item_id, 0.12, 0)
        out_0b, ops_0b = typo_noise(text, item_id, 0.12, 0)
        assert out_0a == out_0b and ops_0a == ops_0b, (
            "seed 0 not reproducible for " + item_id
        )
        out_1, _ = typo_noise(text, item_id, 0.12, 1)
        if out_0a != out_1:
            differing += 1
    assert differing >= 20, "only {} of 24 items differed between seed 0 and 1".format(differing)
    print("  seed 0 twice identical: 24/24")
    print("  seed 0 vs seed 1 different text: {}/24 (required >= 20)".format(differing))


def test_monotonicity() -> None:
    print("T3 MONOTONICITY OF INTENSITY: realised edits per character across the ladder")
    items = _make_items(120)
    print(
        "  items: {}; variants per level: {} items x {} seeds = {}".format(
            len(items), len(items), len(SEEDS), len(items) * len(SEEDS)
        )
    )
    print("  rate = len(ops)/len(text); denominator = full character count (spaces included)")
    print("  {:>9} | {:>12} | {:>12} | {:>9}".format("requested", "mean(K/len)", "pooled(K)/len", "delta_pp"))
    means = []
    for lam in LAMBDA_LADDER:
        rates = []
        total_edits = 0
        total_chars = 0
        for item_id, text in items:
            for seed in SEEDS:
                _, ops = typo_noise(text, item_id, lam, seed)
                rates.append(len(ops) / len(text))
                total_edits += len(ops)
                total_chars += len(text)
        mean_rate = sum(rates) / len(rates)
        pooled = total_edits / total_chars
        means.append(mean_rate)
        print(
            "  {:>9.2f} | {:>12.5f} | {:>12.5f} | {:>+9.2f}".format(
                lam, mean_rate, pooled, (mean_rate - lam) * 100.0
            )
        )
    assert means[0] == 0.0, "lambda=0 mean rate must be exactly 0"
    for k in range(1, len(means)):
        assert means[k] > means[k - 1], (
            "mean rate not strictly increasing between {} and {}".format(
                LAMBDA_LADDER[k - 1], LAMBDA_LADDER[k]
            )
        )
    max_dev = 0.0
    for lam, mean_rate in zip(LAMBDA_LADDER, means):
        dev = abs(mean_rate - lam)
        max_dev = max(max_dev, dev)
        assert dev <= 0.02, (
            "realised {:.5f} deviates from requested {} by more than 2 pp".format(mean_rate, lam)
        )
    print(
        "  strictly increasing: yes; max |delta| = {:.2f} pp (limit 2.00 pp): yes".format(
            max_dev * 100.0
        )
    )


def test_class_coverage() -> None:
    print("T4 CLASS COVERAGE: per-class operation counts across the ladder")
    items = _make_items(40)
    counts = {cls: 0 for cls in CLASS_NAMES}
    total = 0
    for item_id, text in items:
        for lam in LAMBDA_LADDER[1:]:
            for seed in SEEDS:
                _, ops = typo_noise(text, item_id, lam, seed)
                for op in ops:
                    counts[op.split(":", 1)[0]] += 1
                    total += 1
    print("  total ops: {}".format(total))
    for cls in CLASS_NAMES:
        share = counts[cls] / total if total else 0.0
        print("  {:>5}: {:>6} ({:5.1f}%)".format(cls, counts[cls], 100.0 * share))
    for cls in CLASS_NAMES:
        assert counts[cls] > 0, "class '{}' never occurred".format(cls)


def test_lambda_zero() -> None:
    print("T5 LAMBDA=0 IS A NO-OP")
    items = _make_items(40)
    checked = 0
    for item_id, text in items:
        for seed in SEEDS:
            out, ops = typo_noise(text, item_id, 0.0, seed)
            assert out == text, "lambda=0 changed the text for " + item_id
            assert ops == [], "lambda=0 returned ops for " + item_id
            checked += 1
    print("  {} (item, seed) pairs checked: text unchanged, ops empty".format(checked))


def test_jsonl_shape() -> None:
    print("T6 JSONL SHAPE: every op matches ^(adj|trans|del|ins):.+->.*$")
    items = _make_items(40)
    checked = 0
    for item_id, text in items:
        for lam in LAMBDA_LADDER[1:]:
            for seed in SEEDS:
                _, ops = typo_noise(text, item_id, lam, seed)
                for op in ops:
                    assert _OP_RE.match(op), "op does not match schema: {!r}".format(op)
                    checked += 1
    print("  ops checked against the schema regex: {}".format(checked))


def test_whitespace_structure() -> None:
    print("T7 WHITESPACE SURVIVAL: whitespace runs and token counts unchanged")
    items = _make_items(40)
    checked = 0
    for item_id, text in items:
        for lam in LAMBDA_LADDER[1:]:
            for seed in SEEDS:
                out, _ = typo_noise(text, item_id, lam, seed)
                ws_in = [c for c in text if c.isspace()]
                ws_out = [c for c in out if c.isspace()]
                assert ws_in == ws_out, "whitespace sequence changed for " + item_id
                assert len(text.split()) == len(out.split()), (
                    "token count changed for " + item_id
                )
                checked += 1
    print("  variants checked: {}; whitespace identical in every one".format(checked))


def test_degenerate_guard() -> None:
    print("T8 DEGENERACY GUARD AT EXTREME INTENSITY")
    texts = ["a", "I", "hi", "ok ?", "a a a", "No.", "cat dog", "hello world!", "Q", "aaaa"]
    lams = (0.25, 0.5, 1.0, 2.0, 4.0)
    checked = 0
    for t_i, text in enumerate(texts):
        for lam in lams:
            for seed in SEEDS:
                out, _ = typo_noise(text, "stress_{}_{}".format(t_i, lam), lam, seed)
                assert out != "", "empty output from {!r} at lam={}".format(text, lam)
                assert _has_alnum(out), "lost all alphanumeric content: {!r} -> {!r}".format(text, out)
                assert [c for c in out if c.isspace()] == [c for c in text if c.isspace()]
                checked += 1
    print(
        "  variants checked: {} (texts={}, lam in {}, seeds={})".format(
            checked, len(texts), list(lams), list(SEEDS)
        )
    )
    print("  no empty / alphanumeric-free / whitespace-mangled output")


def _run_self_tests() -> int:
    print("=" * 74)
    print("N_en self-tests (typo_noise v{}, python {})".format(__version__, sys.version.split()[0]))
    print("=" * 74)
    failures = 0
    tests = (
        ("T1 determinism", test_determinism),
        ("T2 independence by seed", test_seed_independence),
        ("T3 monotonicity of intensity", test_monotonicity),
        ("T4 class coverage", test_class_coverage),
        ("T5 lambda=0 no-op", test_lambda_zero),
        ("T6 JSONL shape", test_jsonl_shape),
        ("T7 whitespace survival", test_whitespace_structure),
        ("T8 degeneracy guard", test_degenerate_guard),
    )
    for name, fn in tests:
        try:
            fn()
            print("[PASS] " + name)
        except AssertionError as exc:
            failures += 1
            print("[FAIL] {}: {}".format(name, exc))
    print("-" * 74)
    if failures:
        print("SELF-TESTS FAILED: {} of {} failed".format(failures, len(tests)))
        return 1
    print("SELF-TESTS PASSED: {} of {}".format(len(tests), len(tests)))
    return 0


if __name__ == "__main__":
    raise SystemExit(_run_self_tests())
