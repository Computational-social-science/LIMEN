#!/usr/bin/env python
"""o1_agent_rater.py -- the O1 readability rater, frozen, and the evidence that it is usable.

WHY THIS EXISTS
    O1 has to decide whether an item is human-readable at `lo` and stressed at `mid`, and the original
    Amendment 3 asked a panel of three English-native adults to do it. The decision taken instead is to
    replace the panel with an autonomous rater validated against human-annotated data. That substitution
    removes the very disagreement a kappa was meant to measure: a rater at temperature 0 agrees with
    itself perfectly, and self-agreement is not evidence of anything. So the validity evidence has to come
    from OUTSIDE - from human labels this rater never saw in training and cannot influence.

WHAT "VALIDATED" MEANS HERE, AND THE TWO MODES
    Mode A, external. jfleg ships four independent human corrections per sentence. The spread among those
    four corrections IS a human annotation of whether the intended content came through unambiguously:
    low spread means the annotators agreed on what the sentence meant, high spread means they did not.
    Tertiles of that spread give an ordered three-way human label, and the rater is scored against it.
    This is a real human annotation of a real readability question, on text corrupted by real errors.

    Mode B, sensitivity. Mode A validates the rater on somebody else's corruption. Mode B corrupts jfleg
    sentences with THIS project's frozen generator and requires the rater's difficulty to increase with
    lambda. A rater that reproduces human labels on real errors but does not respond to our manipulation
    is not an instrument for this study.

    Neither mode alone is enough: A without B is a rater that reads well but ignores our noise, B without
    A is a rater that responds to our noise in a way no human has endorsed.

THE BLIND JUDGEMENT, AND WHY IT REPLACES THE COMPARATIVE ONE
    Amendment 3 had the rater see the clean text and then the perturbed text. A real reader has no clean
    text. Judging with the answer in front of you is a different and easier task, and - decisively - it is
    the task no external dataset can validate, because jfleg has no clean original to show. The instrument
    is therefore BLIND: only the corrupted text is presented. This is both the faithful operationalisation
    and the validatable one.

THE CONFIGURATION IS PART OF THE INSTRUMENT
    Measured on this host: with reasoning enabled the rater answers `R` on a sentence where with reasoning
    disabled it answers `W`, at 28 s versus 2 s per item. A rater whose label depends on whether it is
    allowed to deliberate is two raters, and the difference must be pinned rather than discovered later.
    THE CONFIGURATION BELOW IS FROZEN. Changing any of it invalidates the validation and requires re-running
    modes A and B.

WHAT THIS SCRIPT REFUSES TO DO
    It will not report a kappa it did not compute, and it will not treat a failed validation as a result to
    work around. If Mode A's weighted kappa is below the protocol's own floor of 0.60, the rater is not
    usable and O1 cannot proceed - that is a finding about the instrument, and it is printed as one.
"""

from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import json
import os
import pathlib
import re
import statistics
import sys
import time
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
VALIDATION = REPO_ROOT / "measurement" / "o1_validation"

# ---------------------------------------------------------------------------------------------
# FROZEN INSTRUMENT CONFIGURATION. Changing any value here invalidates modes A and B.
# ---------------------------------------------------------------------------------------------
MODEL = "Qwen3.6-35B-A3B-UD-Q4_K_M"
ENDPOINT = "http://127.0.0.1:18434/v1/chat/completions"
KEY_ENV = "HERMES_LOCAL_LLAMACPP_KEY"
TEMPERATURE = 0
ENABLE_THINKING = False      # see the module docstring: this changes the label, so it is pinned
MAX_TOKENS = 64             # enough for a single letter; reasoning is off so nothing is consumed by it
WORKERS = 6
CATEGORIES = ("R", "W", "X")

PROMPT = (
    "You are judging whether a reader can recover the intended content of a short text.\n"
    "The text may contain spelling or typing errors. You are NOT shown the correct text; judge only "
    "whether the intended content comes through.\n\n"
    "Answer with exactly one letter and nothing else.\n"
    "  R = the intended content is recoverable without hesitation\n"
    "  W = the intended content is recoverable, but the reader must re-read or guess\n"
    "  X = the intended content is not recoverable\n\n"
    "TEXT: {text}\n"
    "ANSWER:"
)

PAIRWISE_PROMPT = (
    "Two short texts are shown. Both may contain spelling or typing errors, and the intended content is "
    "not given. Decide which text would be HARDER for a reader to recover the intended content from.\n\n"
    "Answer with exactly one letter and nothing else: A if TEXT A is harder, B if TEXT B is harder, "
    "S if they are equally hard.\n\n"
    "TEXT A: {a}\n"
    "TEXT B: {b}\n"
    "ANSWER:"
)

CONCORDANCE_FLOOR = 0.80    # pre-registered: a rater that cannot order pairs this well cannot scale items
KAPPA_FLOOR = 0.60           # the protocol's own floor, reused here rather than invented


def call_rater(text: str, timeout: int = 240, model: str | None = None,
               thinking: bool | None = None) -> dict:
    """One judgement. Returns {'label': 'R'|'W'|'X'|None, 'raw': str, 'secs': float}.

    `model` and `thinking` exist ONLY so the frozen configuration can be compared against alternatives
    during validation. Whatever is compared, the numbers recorded as the instrument's validation are the
    ones produced by the FROZEN defaults, and the alternative runs are written with their own names.
    """
    payload = {
        "model": model or MODEL,
        "messages": [{"role": "user", "content": PROMPT.format(text=text)}],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "chat_template_kwargs": {"enable_thinking": ENABLE_THINKING if thinking is None else thinking},
    }
    t0 = time.monotonic()
    data = _post(payload, timeout)
    raw = (data["choices"][0]["message"].get("content") or "").strip()
    m = re.search(r"\b([RWX])\b", raw.upper())
    return {"label": m.group(1) if m else None, "raw": raw[:80], "secs": time.monotonic() - t0}


def call_pairwise(a: str, b: str, timeout: int = 240, model: str | None = None,
                  thinking: bool | None = None) -> dict:
    """One pairwise judgement. Returns {'choice': 'A'|'B'|'S'|None, 'raw': str}.

    Pairwise because absolute category assignment is where the rater collapsed: Qwen3.6-35B never emitted
    `X` for any of 120 sentences and Qwen3.8-27B's concordance with the human ordering was 0.633 against a
    shuffled null of 0.499. Ordering two texts is an easier and much better-posed question for a language
    model than placing one on an absolute scale, so the scale is derived FROM the order rather than
    demanded directly.
    """
    payload = {
        "model": model or MODEL,
        "messages": [{"role": "user", "content": PAIRWISE_PROMPT.format(a=a, b=b)}],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "chat_template_kwargs": {"enable_thinking": ENABLE_THINKING if thinking is None else thinking},
    }
    data = _post(payload, timeout)
    raw = (data["choices"][0]["message"].get("content") or "").strip()
    m = re.search(r"\b([ABS])\b", raw.upper())
    return {"choice": m.group(1) if m else None, "raw": raw[:60]}


def pairwise_concordance(pairs: list[tuple[str, str, int]], model: str | None = None,
                         thinking: bool | None = None, workers: int = WORKERS,
                         swap_half: bool = True) -> dict:
    """pairs = [(harder_text, easier_text, expected)] where expected is 1 if the FIRST is truly harder.

    Half the pairs are presented with the sides swapped. An LLM asked to compare two texts has a position
    preference, and a runner that ignores it will report a concordance that is really measuring which slot
    the answer tends to land in. The swap makes that bias visible, and it is reported rather than assumed
    away.
    """
    prompts: list[tuple[str, str]] = []
    expects: list[int] = []
    for k, (hard, easy, exp) in enumerate(pairs):
        if swap_half and k % 2 == 1:
            prompts.append((easy, hard))          # harder text now in slot B
            expects.append(1 - exp)
        else:
            prompts.append((hard, easy))
            expects.append(exp)

    res: list[dict | None] = [None] * len(prompts)

    def one(i: int) -> None:
        for attempt in (1, 2):
            try:
                res[i] = call_pairwise(prompts[i][0], prompts[i][1], model=model, thinking=thinking)
                return
            except AuthFailure:
                raise
            except Exception as exc:                                  # noqa: BLE001
                if attempt == 2:
                    res[i] = {"choice": None, "raw": f"{type(exc).__name__}"}

    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, range(len(prompts))))

    pos_a = correct = ties = unparsed = 0
    for (a_text, _b), exp, r in zip(prompts, expects, res):
        ch = r["choice"] if r else None
        if ch is None:
            unparsed += 1
            continue
        if ch == "A":
            pos_a += 1
        if ch == "S":
            ties += 1
            correct += 0.5
        elif (ch == "A" and exp == 1) or (ch == "B" and exp == 0):
            correct += 1
    n = len(prompts) - unparsed
    return {"n": n, "concordance": correct / n if n else float("nan"),
            "ties": ties, "unparsed": unparsed, "position_A_rate": pos_a / n if n else float("nan")}


class AuthFailure(RuntimeError):
    """Raised when the endpoint refuses the key. Never downgraded to an 'unparseable' judgement.

    Measured on this host: launched without `HERMES_LOCAL_LLAMACPP_KEY`, every call returns HTTP 401, and
    an earlier version of this file counted all of them as 'unparsed'. A run then reports 0/120 parsed and
    a kappa it cannot compute - which reads like a rater that will not answer, when in fact the rater was
    never asked. An authentication failure is a fact about the harness, and it must stop the run rather
    than become a statistic.
    """
    def __init__(self, detail: str):
        super().__init__(
            f"the endpoint refused the key ({detail}). Export {KEY_ENV} in the environment that launches "
            f"this script; do not read the resulting empty labels as a property of the rater.")


def _post(payload: dict, timeout: int) -> dict:
    """One HTTP round trip, with 401/403 promoted to AuthFailure."""
    if not os.environ.get(KEY_ENV):
        raise AuthFailure(f"{KEY_ENV} is not set in this environment")
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {os.environ[KEY_ENV]}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as fh:
            return json.load(fh)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise AuthFailure(f"HTTP {exc.code}") from exc
        raise


def rate_many(texts: list[str], workers: int = WORKERS, model: str | None = None,
              thinking: bool | None = None) -> list[dict]:
    """Concurrent, order-preserving. One retry on a transport error; empty labels are counted, not hidden."""
    out: list[dict | None] = [None] * len(texts)

    def one(i: int) -> None:
        for attempt in (1, 2):
            try:
                out[i] = call_rater(texts[i], model=model, thinking=thinking)
                return
            except AuthFailure:
                raise
            except Exception as exc:                       # noqa: BLE001 - recorded, not swallowed
                if attempt == 2:
                    out[i] = {"label": None, "raw": f"{type(exc).__name__}: {exc}"[:80], "secs": 0.0}

    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, range(len(texts))))
    return [o if o is not None else {"label": None, "raw": "not run", "secs": 0.0} for o in out]


# ---------------------------------------------------------------------------------------------
# Statistics, in pure stdlib so nothing here can drift with a library version.
# ---------------------------------------------------------------------------------------------
def weighted_kappa(human: list[str], rater: list[str], k: int = 3) -> tuple[float, float]:
    """Linear-weighted Cohen's kappa for an ORDERED k-category scale, plus the unweighted value.

    Weighted, because R/W/X are ordered: calling a readable item `X` is a worse error than calling it `W`,
    and an unweighted kappa would score those two mistakes identically.
    """
    idx = {c: i for i, c in enumerate(CATEGORIES)}
    n = len(human)
    if n == 0:
        return float("nan"), float("nan")
    obs = [[0] * k for _ in range(k)]
    for h, r in zip(human, rater):
        obs[idx[h]][idx[r]] += 1
    hh = [sum(obs[i]) for i in range(k)]
    rr = [sum(obs[j][i] for j in range(k)) for i in range(k)]
    num_obs = num_exp = 0.0
    for i in range(k):
        for j in range(k):
            w = abs(i - j) / (k - 1)
            num_obs += w * obs[i][j]
            num_exp += w * hh[i] * rr[j] / n
    kappa_w = 1 - (num_obs / num_exp) if num_exp else float("nan")

    agree = sum(obs[i][i] for i in range(k))
    # pe is a product of two PROPORTIONS, so it divides by n^2 - not by n. Dividing by n once produced
    # an unweighted kappa of 2.0 on a systematic-disagreement control, a value the statistic cannot take.
    pe = sum(hh[i] * rr[i] for i in range(k)) / (n * n)
    kappa_u = (agree / n - pe) / (1 - pe) if pe != 1 else float("nan")
    return kappa_w, kappa_u


def spearman(a: list[float], b: list[float]) -> float:
    def rank(xs: list[float]) -> list[float]:
        order = sorted(range(len(xs)), key=lambda i: xs[i])
        r = [0.0] * len(xs)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for t in range(i, j + 1):
                r[order[t]] = avg
            i = j + 1
        return r
    ra, rb = rank(a), rank(b)
    n = len(ra)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den if den else float("nan")


def ordinal_report(spread: list[float], labels: list[str], trials: int = 400,
                   rng_seed: int = 0) -> dict:
    """Ordinal validity, with a shuffled null so the numbers have a reference point.

    WHY NOT KAPPA ALONE. The human label is a SPREAD - a relative measure of how much the four
    annotators diverged. Turning it into R/W/X by tertiles forces exactly one third of the items into
    `X`, which asserts that a third of these sentences are unrecoverable. That is not what the human data
    says; it says a third are the MOST ambiguous. Comparing an absolute rater scale against a relative
    human scale through kappa therefore charges the rater for the mapping's assumption. The order is what
    both scales actually carry, so the order is what is measured here.

    `concordance` is the fraction of sentence PAIRS, differing by at least `min_gap` in human spread,
    that the rater orders the same way. Ties in the rater are counted as half, which is the usual
    convention and is stated rather than left implicit.

    The shuffled null is the control: relabelling the rater at random must drive concordance to ~0.5 and
    Spearman to ~0, and a routine that reports neither is not measuring anything.
    """
    import random
    order = {"R": 2, "W": 1, "X": 0}
    rs = [order[l] for l in labels]
    rho = spearman(spread, [float(x) for x in rs])

    def concord(sp: list[float], sc: list[int], min_gap: float) -> tuple[float, int]:
        num = den = 0
        for i in range(len(sp)):
            for j in range(i + 1, len(sp)):
                if abs(sp[i] - sp[j]) < min_gap:
                    continue
                den += 1
                if sp[i] < sp[j]:
                    num += 1 if sc[i] > sc[j] else (0.5 if sc[i] == sc[j] else 0)
                else:
                    num += 1 if sc[i] < sc[j] else (0.5 if sc[i] == sc[j] else 0)
        return (num / den if den else float("nan")), den

    conc, pairs = concord(spread, rs, min_gap=0.05)
    rng = random.Random(rng_seed)
    null = []
    for _ in range(trials):
        sh = rs[:]
        rng.shuffle(sh)
        null.append(concord(spread, sh, min_gap=0.05)[0])
    null_mean = statistics.mean(null)
    return {"spearman": rho, "concordance": conc, "pairs": pairs,
            "null_concordance_mean": null_mean, "null_spearman": spearman(spread, [float(x) for x in range(len(spread))])}


def tertile_labels(spread: list[float]) -> list[str]:
    """Ordered three-way human label from a continuous human-spread measure.

    LOW spread -> annotators agreed on the meaning -> R. HIGH spread -> they did not -> X.
    Tertiles rather than fixed cut-offs, so the class sizes are equal by construction and the kappa
    cannot be inflated by an accidental class imbalance.
    """
    order = sorted(range(len(spread)), key=lambda i: spread[i])
    out = [""] * len(spread)
    for rank, i in enumerate(order):
        t = min(2, int(rank * 3 / len(spread)))
        out[i] = CATEGORIES[t]
    return out


def mode_external(sample: int, seed: int, model: str | None = None, thinking: bool | None = None) -> int:
    src = VALIDATION / "jfleg_human_labels.jsonl"
    rows = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines()]
    rows = [r for r in rows if r.get("sent", "").strip()]
    step = max(1, len(rows) // sample)
    rows = rows[::step][:sample]
    print(f"  mode A (external): {len(rows)} jfleg sentences, human labels from 4-annotator spread")
    print(f"    instrument: {model or MODEL}  thinking={ENABLE_THINKING if thinking is None else thinking}  temperature={TEMPERATURE}  blind")

    res = rate_many([r["sent"] for r in rows], model=model, thinking=thinking)
    ok = [(r, o) for r, o in zip(rows, res) if o["label"]]
    unparsed = len(rows) - len(ok)
    if len(ok) < 0.9 * len(rows):
        print(f"  [FAIL] only {len(ok)}/{len(rows)} judgements parsed ({unparsed} unparseable). "
              f"The instrument is not returning usable labels; the validation cannot be interpreted.")
        return 1

    human = tertile_labels([r["spread"] for r, _ in ok])
    rater = [o["label"] for _, o in ok]
    kw, ku = weighted_kappa(human, rater)
    rho = spearman([r["spread"] for r, _ in ok], [[2, 1, 0][CATEGORIES.index(o["label"])] for _, o in ok])
    conf = collections.Counter(zip(human, rater))
    mean_s = statistics.mean(o["secs"] for _, o in ok)

    print(f"    unparseable            : {unparsed}")
    print(f"    mean latency           : {mean_s:.1f}s")
    print(f"    weighted kappa (linear): {kw:.3f}")
    print(f"    unweighted kappa       : {ku:.3f}")
    print(f"    Spearman(spread, order): {rho:+.3f}   (negative = rater calls ambiguous text harder, correct)")
    ord_rep = ordinal_report([r["spread"] for r, _ in ok], rater)
    print(f"    ORDINAL: Spearman(rater order, human spread) = {ord_rep['spearman']:+.3f}")
    print(f"             pairwise concordance = {ord_rep['concordance']:.3f} over {ord_rep['pairs']} pairs"
          f"   (shuffled null {ord_rep['null_concordance_mean']:.3f})")
    print("    confusion (human row, rater col):")
    print("        " + " ".join(f"{c:>6}" for c in CATEGORIES))
    for h in CATEGORIES:
        print(f"    {h:>4}" + " ".join(f"{conf.get((h, c), 0):>6}" for c in CATEGORIES))

    with (VALIDATION / "modeA_items.jsonl").open("w", encoding="utf-8") as fh:
        for (r, o), h in zip(ok, human):
            fh.write(json.dumps({"sent": r["sent"], "spread": r["spread"], "human_tertile": h,
                                 "rater_label": o["label"]}, ensure_ascii=False) + "\n")

    (VALIDATION / "modeA_external.json").write_text(json.dumps({
        "instrument": {"model": model or MODEL,
                       "enable_thinking": ENABLE_THINKING if thinking is None else thinking,
                       "temperature": TEMPERATURE, "blind": True, "workers": WORKERS,
                       "max_tokens": MAX_TOKENS, "is_frozen_default": (model is None and thinking is None)},
        "n": len(ok), "unparseable": unparsed, "weighted_kappa": kw, "unweighted_kappa": ku,
        "spearman_spread_vs_order": rho, "mean_latency_s": mean_s,
        "confusion": {f"{h}->{c}": v for (h, c), v in conf.items()},
        "ordinal": ord_rep,
    }, indent=2), encoding="utf-8")

    if kw < KAPPA_FLOOR:
        print(f"\n  [FAIL] weighted kappa {kw:.3f} is below the protocol's floor {KAPPA_FLOOR}.")
        print("         The rater does not reproduce this human annotation well enough to stand in for it.")
        print("         That is a finding about the INSTRUMENT, not about the items - do not average it away.")
        return 1
    print(f"\n  [OK] weighted kappa {kw:.3f} >= floor {KAPPA_FLOOR}")
    return 0


def mode_sensitivity(sample: int, lambdas: tuple[float, ...]) -> int:
    src = VALIDATION / "jfleg_human_labels.jsonl"
    rows = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines()]
    rows = [r for r in rows if r.get("sent", "").strip()]
    step = max(1, len(rows) // sample)
    rows = rows[::step][:sample]

    sys.path.insert(0, str(REPO_ROOT / "measurement"))
    try:
        from typo_noise import typo_noise                                    # type: ignore
    except Exception as exc:                                                 # noqa: BLE001
        print(f"  [FAIL] cannot import the frozen generator: {type(exc).__name__}: {exc}")
        return 1

    print(f"  mode B (sensitivity): {len(rows)} sentences x {len(lambdas)} lambda, "
          f"corrupted by the FROZEN generator")
    scores = {lam: [] for lam in lambdas}
    for lam in lambdas:
        corrupted = [typo_noise(r["sent"], f"jfleg-{i}", lam, 0)[0] for i, r in enumerate(rows)]
        res = rate_many(corrupted)
        labels = [o["label"] for o in res]
        scores[lam] = [[2, 1, 0][CATEGORIES.index(x)] if x else None for x in labels]
        got = [x for x in scores[lam] if x is not None]
        mean = statistics.mean(got) if got else float("nan")
        med = statistics.median(got) if got else float("nan")
        pct = collections.Counter(x for x in labels)
        print(f"    lambda={lam:<5} mean readability={mean:.3f}  median={med:.1f}  "
              f"R/W/X = {pct.get('R',0)}/{pct.get('W',0)}/{pct.get('X',0)}")

    # Per-item monotonicity: readability must not INCREASE as lambda increases.
    lam_sorted = sorted(lambdas)
    mono_fail = mono_ok = 0
    for i in range(len(rows)):
        seq = [scores[l][i] for l in lam_sorted]
        if any(s is None for s in seq):
            continue
        if all(seq[j + 1] <= seq[j] for j in range(len(seq) - 1)):
            mono_ok += 1
        else:
            mono_fail += 1
    total = mono_ok + mono_fail
    frac = mono_ok / total if total else float("nan")
    means = [statistics.mean([x for x in scores[l] if x is not None]) for l in lam_sorted]
    rho = spearman(list(lam_sorted), means)

    print(f"    per-item monotone (readability never rises with lambda): {mono_ok}/{total} = {frac:.3f}")
    print(f"    Spearman(lambda, mean readability)                      : {rho:+.3f}   (negative required)")

    (VALIDATION / "modeB_sensitivity.json").write_text(json.dumps({
        "instrument": {"model": MODEL, "enable_thinking": ENABLE_THINKING, "temperature": TEMPERATURE},
        "n": len(rows), "lambdas": list(lambdas), "monotone_fraction": frac,
        "spearman_lambda_vs_readability": rho,
        "mean_readability_by_lambda": {str(l): m for l, m in zip(lam_sorted, means)},
    }, indent=2), encoding="utf-8")

    if not (frac >= 0.90 and rho < 0):
        print(f"\n  [FAIL] the rater does not respond monotonically to this project's manipulation "
              f"(monotone {frac:.3f}, rho {rho:+.3f}).")
        print("         A rater that reads real human errors but ignores our noise is not an instrument "
              "for this study.")
        return 1
    print(f"\n  [OK] monotone on {frac:.1%} of items, Spearman {rho:+.3f}")
    return 0


def selftest() -> int:
    """Known-answer controls for the kappa and Spearman implementations.

    Written after `rr` was found summing rows instead of columns, which produced an unweighted kappa of
    1.013 - a value the statistic cannot take, and which nothing in the run had flagged. A metric
    implementation that has never been shown a case with a known answer is not evidence.
    """
    fails = []

    perfect = (["R", "W", "X"], ["R", "W", "X"])
    kw, ku = weighted_kappa(*perfect)
    if not (abs(kw - 1.0) < 1e-9 and abs(ku - 1.0) < 1e-9):
        fails.append(f"perfect agreement gave kappa {kw:.4f}/{ku:.4f}, expected 1.0")

    # Two raters whose marginals match but who never agree: kappa must be at most 0, never above 1.
    anti = (["R", "R", "W", "W", "X", "X"], ["W", "X", "R", "X", "R", "W"])
    kw2, ku2 = weighted_kappa(*anti)
    if not (kw2 <= 0 <= 1 and ku2 <= 0 <= 1):
        fails.append(f"systematic disagreement gave kappa {kw2:.4f}/{ku2:.4f}, expected <= 0")

    for label, got, want in [("kappa in range", 0.0 <= kw <= 1.0, True),
                             ("kappa never exceeds 1", kw <= 1.0, True)]:
        if got != want:
            fails.append(f"{label}: {got} != {want}")

    rho_up = spearman([1, 2, 3, 4], [10, 20, 30, 40])
    rho_dn = spearman([1, 2, 3, 4], [40, 30, 20, 10])
    if not (abs(rho_up - 1.0) < 1e-9 and abs(rho_dn + 1.0) < 1e-9):
        fails.append(f"Spearman monotone cases gave {rho_up:.4f} / {rho_dn:.4f}, expected +1 / -1")

    if fails:
        print("  [FAIL] metric self-test:")
        for f in fails:
            print("      -", f)
        return 1
    print(f"  [OK] metric self-test: perfect agreement -> weighted {kw:.3f} unweighted {ku:.3f}; "
          f"systematic disagreement -> {kw2:.3f}/{ku2:.3f}; Spearman +1/-1 on monotone cases")
    return 0


def mode_pairwise_external(sample: int, model: str | None, thinking: bool | None) -> int:
    rows = [json.loads(l) for l in (VALIDATION / "jfleg_human_labels.jsonl")
            .read_text(encoding="utf-8").splitlines()]
    rows = [r for r in rows if r.get("sent", "").strip()]
    step = max(1, len(rows) // max(1, sample * 2))
    rows = rows[::step][: sample * 2]
    pairs = []
    for i in range(0, len(rows) - 1, 2):
        r1, r2 = rows[i], rows[i + 1]
        if abs(r1["spread"] - r2["spread"]) < 0.05:
            continue
        if r1["spread"] > r2["spread"]:
            pairs.append((r1["sent"], r2["sent"], 1))
        else:
            pairs.append((r2["sent"], r1["sent"], 1))
    print(f"  pairwise mode A: {len(pairs)} pairs, both sides presented, gap >= 0.05")
    rep = pairwise_concordance(pairs, model=model, thinking=thinking)
    print(f"    concordance with the human ordering : {rep['concordance']:.3f}  (n={rep['n']})")
    print(f"    position-A rate                     : {rep['position_A_rate']:.3f}  (0.5 = no side bias)")
    print(f"    ties / unparsed                     : {rep['ties']} / {rep['unparsed']}")
    (VALIDATION / "modeA_pairwise.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    ok = rep["concordance"] >= CONCORDANCE_FLOOR and abs(rep["position_A_rate"] - 0.5) <= 0.15
    if not ok:
        print(f"  [FAIL] pairwise concordance {rep['concordance']:.3f} < floor {CONCORDANCE_FLOOR}"
              f" or position bias {rep['position_A_rate']:.3f} out of +/-0.15")
        return 1
    print(f"  [OK] pairwise concordance {rep['concordance']:.3f} >= {CONCORDANCE_FLOOR}, no side bias")
    return 0


def mode_pairwise_lambda(sample: int, model: str | None, thinking: bool | None,
                         lo: float = 0.05, hi: float = 0.18) -> int:
    rows = [json.loads(l) for l in (VALIDATION / "jfleg_human_labels.jsonl")
            .read_text(encoding="utf-8").splitlines()]
    rows = [r for r in rows if r.get("sent", "").strip()][:: max(1, 1501 // sample)][:sample]
    sys.path.insert(0, str(REPO_ROOT / "measurement"))
    from typo_noise import typo_noise                                        # type: ignore
    pairs = []
    for i, r in enumerate(rows):
        easy = typo_noise(r["sent"], f"pw-{i}", lo, 0)[0]
        hard = typo_noise(r["sent"], f"pw-{i}", hi, 0)[0]
        pairs.append((hard, easy, 1))
    print(f"  pairwise mode B: {len(pairs)} pairs, lambda {lo} versus {hi}, same sentence")
    rep = pairwise_concordance(pairs, model=model, thinking=thinking)
    print(f"    picks the noisier text as harder    : {rep['concordance']:.3f}  (n={rep['n']})")
    print(f"    position-A rate                     : {rep['position_A_rate']:.3f}  (0.5 = no side bias)")
    (VALIDATION / "modeB_pairwise.json").write_text(json.dumps(dict(rep, lo=lo, hi=hi), indent=2),
                                                   encoding="utf-8")
    if rep["concordance"] < CONCORDANCE_FLOOR or abs(rep["position_A_rate"] - 0.5) > 0.15:
        print(f"  [FAIL] the rater does not order its OWN manipulation reliably")
        return 1
    print(f"  [OK] orders the manipulation at {rep['concordance']:.3f}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--selftest", action="store_true", help="known-answer controls for the metrics")
    ap.add_argument("--external", type=int, metavar="N", help="mode A: N jfleg sentences vs human labels")
    ap.add_argument("--sensitivity", type=int, metavar="N", help="mode B: N sentences across the ladder")
    ap.add_argument("--lambdas", default="0.05,0.12,0.18")
    ap.add_argument("--model", help="override the frozen model (comparison only)")
    ap.add_argument("--thinking", choices=("on", "off"), help="override thinking (comparison only)")
    ap.add_argument("--pairwise-external", type=int, metavar="N",
                    help="pairwise vs the human spread ordering on jfleg")
    ap.add_argument("--pairwise-lambda", type=int, metavar="N",
                    help="pairwise at two lambda levels under the frozen generator")
    ap.add_argument("--determinism", type=int, metavar="N",
                    help="repeat N items twice under the frozen config; agreement must be exact")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    if not (args.external or args.sensitivity or args.determinism
            or args.pairwise_external or args.pairwise_lambda):
        ap.print_help()
        return 2

    rc = 0
    rc |= selftest()
    try:
        return _run_modes(args, rc)
    except AuthFailure as exc:
        print(f"\n  [FAIL] {exc}")
        return 3


def _run_modes(args, rc: int) -> int:
    th = None if args.thinking is None else (args.thinking == "on")
    if args.external:
        rc |= mode_external(args.external, seed=0, model=args.model, thinking=th)
    if args.sensitivity:
        rc |= mode_sensitivity(args.sensitivity, tuple(float(x) for x in args.lambdas.split(",")))
    if args.pairwise_external:
        rc |= mode_pairwise_external(args.pairwise_external, args.model, th)
    if args.pairwise_lambda:
        rc |= mode_pairwise_lambda(args.pairwise_lambda, args.model, th)
    if args.determinism:
        rows = [json.loads(l) for l in (VALIDATION / "jfleg_human_labels.jsonl")
                .read_text(encoding="utf-8").splitlines()][::max(1, 1501 // args.determinism)][:args.determinism]
        texts = [r["sent"] for r in rows]
        a = rate_many(texts)
        b = rate_many(texts)
        agree = sum(1 for x, y in zip(a, b) if x["label"] == y["label"])
        print(f"  determinism (frozen config): {agree}/{len(texts)} identical labels")
        if agree != len(texts):
            print("  [FAIL] the frozen configuration is not deterministic; the instrument is not pinned.")
            rc |= 1
        else:
            print("  [OK] exact repeatability under the frozen configuration")
    return rc


if __name__ == "__main__":
    sys.exit(main())