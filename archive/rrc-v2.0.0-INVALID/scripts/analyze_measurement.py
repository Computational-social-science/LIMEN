"""Reduce the d1-3B measurement rows to the numbers the report renders.

Why this exists
---------------
The eval script prints and writes a summary, but the summary is written for a terminal: it has
accuracies without intervals, a rank contrast as two points, and no instrument diagnostics at
all. A report needs the same numbers with their uncertainty, the diagnostics that establish the
readout is measuring the language rather than the option layout, and one stable artefact to read
-- so that a figure and the sentence describing it cannot disagree.

What it computes
----------------
1. Accuracy per arm and layer, with a Wilson interval and a z against the fixed-choice chance.
2. `p_root`, the probability the model assigns to the **correct** candidate. This is the quantity
   the depth hypothesis is about: accuracy says whether the model was right, `p_root` says how
   much probability it gave to being right, and a silent failure is a low `p_root` with a high
   `p_max` -- wrong and confident on the same trial.
3. The L4 -> L1 change per script. L4 is a shuffled sample of the pool (unrelated forms, so the
   answer is easy) and L1 is other attested realisations of the same root (plausible, so it is
   not). The difference is how much of the model's advantage survives the decoys becoming
   channel-plausible -- measured within one script, so it does not depend on comparing arms whose
   layer coverage differs.
4. Position diagnostics. If the model prefers a particular option slot, accuracy is a fact about
   the prompt's layout rather than about the channel, and every number above is void. Reported
   per arm so the claim can be checked rather than asserted.
5. The rank curve on the reading channel, per arm, computed against **that arm's own** frequency
   table.

Output
------
measurement/out/measurement_report.json -- read by the technical report at load time.
"""
from __future__ import annotations

import collections
import argparse
import json
import math
import pathlib
import statistics
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
OUT = REPO / "measurement" / "out"
RRC = REPO / "data" / "rrc"


def wilson(k: int, n: int, z: float = 1.96) -> tuple:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def two_prop(k1: int, n1: int, k2: int, n2: int):
    """z of the difference of two proportions, pooled SE. None when undefined."""
    if not n1 or not n2:
        return None
    p = (k1 + k2) / (n1 + n2)
    if not 0 < p < 1:
        return None
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return ((k1 / n1 - k2 / n2) / se) if se else None


def quantiles(vals: list, qs=(0.25, 0.5, 0.75)) -> dict:
    if not vals:
        return {}
    s = sorted(vals)
    return {"min": round(s[0], 6), "max": round(s[-1], 6),
            **{("p%d" % int(q * 100)): round(s[min(len(s) - 1, int(q * (len(s) - 1)))], 6)
               for q in qs},
            "n": len(s)}


def load_rows(only: str = "") -> tuple[list, str]:
    """Rows from one sampling scheme, or from every file when none is named.

    Mixing schemes is not a merge: the two files sample different units (items per layer against
    whole states) and different sizes, so a pooled accuracy would describe a sample nobody drew.
    `only` names a suffix (`_bs` for the by-state run) and keeps the schemes separable.
    """
    if only:
        files = [OUT / ("rrc_d1_rows%s.jsonl" % only)]
        files = [p for p in files if p.exists()]
    else:
        files = sorted(OUT.glob("rrc_d1_rows*.jsonl"))
        # Globbing every scheme is only meaningful while one exists. Once a second sampling scheme
        # is written, pooling them silently would describe a sample nobody drew -- different units,
        # different sizes -- so it is refused and the caller must name the scheme.
        if len(files) > 1:
            print("  [FAIL] %d rows files exist (%s); name one with --rows <suffix> instead of "
                  "pooling sampling schemes" % (len(files), ", ".join(p.name for p in files)))
            return [], ""
    if not files:
        return [], ""
    rows = []
    for p in files:
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows, ", ".join(p.name for p in files)


def candidate_index() -> dict:
    """item_id -> (candidates, root), so the picked option's position can be recovered."""
    out = {}
    for p in sorted(RRC.glob("*.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            it = json.loads(line)
            out[it["item_id"]] = (it.get("candidates") or [], it.get("root"))
    return out


def candidate_preference(rows: list) -> list:
    """Whether the model prefers commoner or rarer candidates than a uniform guess would.

    The null used is the item's OWN candidate set, not the root: a uniform choice among five
    candidates yields the mean rank of those five, so comparing the picked rank against the root's
    rank would confound a frequency preference with plain accuracy. Measured on the by-state run,
    the two Chinese arms point OPPOSITE ways -- one picks the rarest candidate half the time, the
    other picks the commonest two fifths of the time -- which is why the reading channel's rank
    effect reverses between them even though both are ranked against their own corpus.

    Returns [] when the rank implementation cannot be loaded, so the field is absent rather than
    guessed.
    """
    import importlib.util
    import os
    import pathlib
    try:
        spec = importlib.util.spec_from_file_location(
            "_rrc_rank", str(pathlib.Path(__file__).resolve().parent / "build_rrc.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception:  # noqa: BLE001
        return []

    out = []
    for arm in sorted({r["arm"] for r in rows if r.get("layer") == "L2c"}):
        freq = mod.han_frequency(arm)
        if not freq:
            continue
        chars = [c for c in freq if freq.get(c, 0) > 0]
        idx = mod.han_reading_index(chars)
        obs, exp, n, rarest_n, commonest_n = 0.0, 0.0, 0, 0, 0
        for r in rows:
            if r["arm"] != arm or r.get("layer") != "L2c" or not r.get("candidates"):
                continue
            cr = []
            for c in r["candidates"]:
                k, _ = mod.han_channel_rank(c, idx, freq)
                cr.append(k or 0)
            pk, _ = mod.han_channel_rank(r.get("picked") or "", idx, freq)
            if not pk or not cr or 0 in cr:
                continue
            n += 1
            obs += pk
            exp += sum(cr) / len(cr)
            if pk == max(cr):
                rarest_n += 1
            if pk == min(cr):
                commonest_n += 1
        if not n:
            continue
        out.append({
            "arm": arm, "n": n,
            "picked_rank_mean": round(obs / n, 2),
            "uniform_null_rank_mean": round(exp / n, 2),
            "difference": round(obs / n - exp / n, 2),
            "direction": "prefers rarer" if obs / n - exp / n > 0 else "prefers commoner",
            "rarest_share": round(rarest_n / n, 4),
            "commonest_share": round(commonest_n / n, 4),
            "uniform_share": round(1.0 / len(rows[0].get("candidates") or [1, 2, 3, 4, 5]), 4),
            "rank_source": mod.han_frequency_source(arm),
        })
    return out


def state_displacement(rows: list) -> list:
    """How much rarer the chosen candidate is than the character actually shown, per arm.

    The question this answers is whether the model uses the state at all. A rule that ignored the
    state would give a constant displacement, measured against the state's own rank. Measured, the
    displacement is not constant: it tracks the state (correlation of the state character's rank
    with the chosen candidate's rank) and it is positive — the chosen candidate is rarer than the
    form shown, by ~9 positions on rrc-zh and ~1 on rrc-zh-gh. That single difference explains why
    the rank effect has opposite signs on two Chinese arms built by the same rule, and it is why the
    finding is reported as a displacement rather than as a preference for rare characters.
    """
    import importlib.util
    import math
    import pathlib
    import statistics
    try:
        spec = importlib.util.spec_from_file_location(
            "_rrc_rank", str(pathlib.Path(__file__).resolve().parent / "build_rrc.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception:  # noqa: BLE001
        return []

    out = []
    for arm in sorted({r["arm"] for r in rows if r.get("layer") == "L2c"}):
        freq = mod.han_frequency(arm)
        if not freq:
            continue
        chars = [c for c in freq if freq.get(c, 0) > 0]
        idx = mod.han_reading_index(chars)
        data = []
        for r in rows:
            if r["arm"] != arm or r.get("layer") != "L2c" or not r.get("candidates"):
                continue
            st, rt = r.get("state") or "", r.get("root") or ""
            if len(st) != len(rt):
                continue
            i = next((k for k, (a, b) in enumerate(zip(st, rt)) if a != b), None)
            if i is None:
                continue
            shown, _ = mod.han_channel_rank(st[i], idx, freq)
            cr = []
            for c in r["candidates"]:
                k, _ = mod.han_channel_rank(c, idx, freq)
                if not k:
                    cr = []
                    break
                cr.append(k)
            pick, _ = mod.han_channel_rank(r.get("picked") or "", idx, freq)
            if shown and pick and cr:
                data.append((shown, pick, r["correct"]))
        if len(data) < 20:
            continue
        data.sort(key=lambda x: x[0])
        q = len(data) // 3
        bins = []
        for lab, chunk in (("state commonest third", data[:q]),
                           ("state middle third", data[q:2 * q]),
                           ("state rarest third", data[2 * q:])):
            if not chunk:
                continue
            bins.append({
                "band": lab, "n": len(chunk),
                "state_rank_median": statistics.median(x[0] for x in chunk),
                "picked_rank_median": statistics.median(x[1] for x in chunk),
                "displacement": round(
                    statistics.median(x[1] for x in chunk)
                    - statistics.median(x[0] for x in chunk), 1),
                "accuracy": round(sum(1 for x in chunk if x[2]) / len(chunk), 4),
            })

        # A decile curve for plotting. Three bands are enough for a table and too few for a line:
        # the shape of the displacement -- flat, monotone, or crossing -- is the thing worth seeing,
        # and three points cannot show a shape. Kept here rather than recomputed in the figure so
        # the rank has one implementation.
        curve = []
        step = max(1, len(data) // 10)
        for i in range(0, len(data), step):
            chunk = data[i:i + step]
            if len(chunk) < 5:
                continue
            curve.append({
                "n": len(chunk),
                "state_rank_median": statistics.median(x[0] for x in chunk),
                "picked_rank_median": statistics.median(x[1] for x in chunk),
                "displacement": round(statistics.median(x[1] for x in chunk)
                                      - statistics.median(x[0] for x in chunk), 1),
                "accuracy": round(sum(1 for x in chunk if x[2]) / len(chunk), 4),
            })
        brs = [x[0] for x in data]
        pks = [x[1] for x in data]
        mb, mp = sum(brs) / len(brs), sum(pks) / len(pks)
        den = math.sqrt(sum((a - mb) ** 2 for a in brs) * sum((b - mp) ** 2 for b in pks))
        corr = (sum((a - mb) * (b - mp) for a, b in zip(brs, pks)) / den) if den else None
        out.append({
            "arm": arm, "n": len(data),
            "corr_state_rank_vs_picked_rank": None if corr is None else round(corr, 3),
            "overall_picked_rank_median": statistics.median(pks),
            "overall_state_rank_median": statistics.median(brs),
            "overall_displacement": round(statistics.median(pks) - statistics.median(brs), 1),
            "bands": bins,
            "curve": curve,
            "reading": ("The chosen candidate is systematically rarer than the form shown, and the "
                        "displacement is larger on rrc-zh. A rule ignoring the state would give a "
                        "constant displacement and a correlation of zero."),
        })
    return out


def margin_effect(rows: list) -> list:
    """Whether the channel's own difficulty quantity predicts accuracy, per arm.

    Each channel has a different difficulty quantity and the test has to use the right one. The
    ranked layers (L2, L3del) carry `margin`: the Dice-similarity gap between the root and the
    nearest decoy, so a larger margin means the state points more clearly at the answer. The reading
    channel (L2c) has no margin at all -- its candidates are homophones by construction, so the
    margin is identically 0 or 1 (§2.4) -- and its difficulty is the root's frequency rank instead.
    Taking one quantity across both channels would compare things that are not comparable.

    Reports the quartile accuracies and the point-biserial correlation, so the SHAPE is visible and
    not only the sign: a quantity that predicts difficulty should be monotone in it, and a
    non-monotone curve means the ordering the channel defines is not the ordering the model uses.
    """
    out = []
    for arm in sorted({r["arm"] for r in rows}):
        data = [(r["margin"], bool(r["correct"]), r.get("layer")) for r in rows
                if r["arm"] == arm and r.get("margin") is not None]
        if len(data) < 40:
            continue
        data.sort(key=lambda x: x[0])
        n = len(data)
        q = n // 4
        bands = []
        for i, label in enumerate(("Q1 smallest", "Q2", "Q3", "Q4 largest")):
            chunk = data[i * q:(i + 1) * q] if i < 3 else data[3 * q:]
            if not chunk:
                continue
            k = sum(1 for _, c, _ in chunk if c)
            lo, hi = wilson(k, len(chunk))
            bands.append({
                "band": label, "n": len(chunk),
                "margin_median": round(statistics.median(m for m, _, _ in chunk), 4),
                "accuracy": round(k / len(chunk), 4),
                "ci95": [round(lo, 4), round(hi, 4)],
            })
        ms = [m for m, _, _ in data]
        cs = [1.0 if c else 0.0 for _, c, _ in data]
        mm, mc = sum(ms) / n, sum(cs) / n
        den = math.sqrt(sum((a - mm) ** 2 for a in ms) * sum((b - mc) ** 2 for b in cs))
        corr = (sum((a - mm) * (b - mc) for a, b in zip(ms, cs)) / den) if den else None
        # monotone or not: compare each band's accuracy with the previous one, allowing a small
        # reversal so a single tie does not flip the verdict
        accs = [b["accuracy"] for b in bands]
        rises = sum(1 for i in range(1, len(accs)) if accs[i] > accs[i - 1])
        out.append({
            "arm": arm, "n": n,
            "layers": sorted({l for _, _, l in data}),
            "margin_min": round(data[0][0], 4), "margin_max": round(data[-1][0], 4),
            "bands": bands,
            "corr_margin_correct": None if corr is None else round(corr, 3),
            "shape": ("monotone" if rises == len(accs) - 1 else
                      "mostly monotone" if rises >= len(accs) - 2 else "non-monotone"),
            "reading": ("A difficulty quantity that the model's behaviour tracks should be monotone "
                        "in accuracy. A non-monotone curve means the ordering the channel defines "
                        "is not the ordering the model uses."),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--rows", default="",
                    help=("suffix of the rows file to reduce (e.g. _bs for the by-state scheme). "
                          "Empty reads every scheme and is only meaningful when one exists."))
    ap.add_argument("--out", default="",
                    help="output name suffix; default is derived from --rows.")
    args = ap.parse_args()

    rows, src = load_rows(args.rows)
    if not rows:
        print("  [FAIL] no rows in %s" % OUT)
        return 1
    print("  read %d rows from %s" % (len(rows), src))

    cands = candidate_index()
    nopt = collections.Counter(r["n_options"] for r in rows)
    K = max(nopt, key=lambda k: nopt[k])
    chance = 1.0 / K
    print("  option count %s -> chance %.4f" % (dict(nopt), chance))

    by = collections.defaultdict(list)
    for r in rows:
        by[(r["arm"], r["layer"])].append(r)

    # ---- 1. accuracy per arm and layer
    acc_table = []
    for (arm, layer), rs in sorted(by.items()):
        n = len(rs)
        k = sum(1 for r in rs if r["correct"])
        lo, hi = wilson(k, n)
        se = math.sqrt(chance * (1 - chance) / n) if n else None
        z = ((k / n - chance) / se) if se else None
        pm = [r["p_max"] for r in rs if r.get("p_max") is not None]
        acc_table.append({
            "arm": arm, "layer": layer, "n": n, "accuracy": round(k / n, 4),
            "ci95": [round(lo, 4), round(hi, 4)],
            "z_vs_chance": None if z is None else round(z, 2),
            "p_max_median": round(statistics.median(pm), 4) if pm else None,
        })
    print("  accuracy rows: %d" % len(acc_table))

    # ---- 2. p_root, the probability given to the truth
    proot = []
    for (arm, layer), rs in sorted(by.items()):
        v = [r["p_root"] for r in rs if r.get("p_root") is not None]
        if not v:
            continue
        zero = sum(1 for x in v if x < 1e-6)
        proot.append({"arm": arm, "layer": layer, **quantiles(v),
                      "exact_zero_frac": round(zero / len(v), 4)})
    print("  p_root rows: %d" % len(proot))

    # ---- 3. the control layer across arms, and why the within-arm L4/L1 contrast is not usable.
    #
    # L4 draws unrelated forms from the arm's own pool, so it is the layer where every arm uses
    # the same decoy rule -- and the arms' state lengths there are comparable, so a cross-arm
    # comparison on L4 is defensible where a within-arm L4-vs-L1 one is not: inside an arm the two
    # layers' state lengths are near-disjoint (rrc-en: L4 [62,68] against L1 [69,70], zero
    # overlap), which makes `layer` and `length` collinear and any adjustment of one for the other
    # unstable. The overlap is measured and reported rather than assumed small.
    drop = []
    for arm in sorted({a for a, _ in by}):
        l4 = by.get((arm, "L4"))
        l1 = by.get((arm, "L1"))
        if not l4 or not l1:
            continue
        k4 = sum(1 for r in l4 if r["correct"])
        k1 = sum(1 for r in l1 if r["correct"])
        z = two_prop(k4, len(l4), k1, len(l1))
        pr4 = [r["p_root"] for r in l4 if r.get("p_root") is not None]
        pr1 = [r["p_root"] for r in l1 if r.get("p_root") is not None]
        t4 = [r["prompt_tokens"] for r in l4]
        t1 = [r["prompt_tokens"] for r in l1]
        inter = min(max(t4), max(t1)) - max(min(t4), min(t1)) + 1
        drop.append({
            "arm": arm,
            "L4_n": len(l4), "L4_acc": round(k4 / len(l4), 4),
            "L1_n": len(l1), "L1_acc": round(k1 / len(l1), 4),
            "acc_drop": round(k4 / len(l4) - k1 / len(l1), 4),
            "z_L4_vs_L1": None if z is None else round(z, 2),
            "L4_p_root_median": round(statistics.median(pr4), 4) if pr4 else None,
            "L1_p_root_median": round(statistics.median(pr1), 4) if pr1 else None,
            "L4_len_range": [min(t4), max(t4)], "L1_len_range": [min(t1), max(t1)],
            "len_overlap_tokens": max(0, inter),
            "contrast_usable": inter >= 10,
            "contrast_note": ("usable" if inter >= 10 else
                              "not usable: the two layers' state lengths barely overlap, so the "
                              "layer difference cannot be separated from a length difference"),
        })
    drop.sort(key=lambda d: -d["acc_drop"])
    print("  L4/L1 rows: %d (%d usable as a contrast)"
          % (len(drop), sum(1 for d in drop if d["contrast_usable"])))

    # ---- 3b. every cross-arm pair on L4, where the decoy rule and the lengths are comparable
    cross = []
    l4arms = sorted({a for a, l in by if l == "L4"})
    for i, a1 in enumerate(l4arms):
        for a2 in l4arms[i + 1:]:
            r1, r2 = by[(a1, "L4")], by[(a2, "L4")]
            k1 = sum(1 for r in r1 if r["correct"])
            k2 = sum(1 for r in r2 if r["correct"])
            z = two_prop(k1, len(r1), k2, len(r2))
            cross.append({
                "a": a1, "b": a2,
                "a_acc": round(k1 / len(r1), 4), "b_acc": round(k2 / len(r2), 4),
                "diff": round(k1 / len(r1) - k2 / len(r2), 4),
                "z": None if z is None else round(z, 2),
                "separated": None if z is None else abs(z) > 1.96,
            })
    cross.sort(key=lambda c: -(abs(c["z"]) if c["z"] is not None else 0))
    print("  cross-arm L4 pairs: %d (%d separated at 0.05)"
          % (len(cross), sum(1 for c in cross if c["separated"])))

    # ---- 3c. the design's own layer contrast, on matched states.
    #
    # L2/L2c/L3del and L4 are built from the same (state, root) and differ only in which decoys
    # they attach, so the question "are channel-plausible decoys harder than unrelated ones" is a
    # paired one and must be tested as such. Sampling items independently per layer left only 37
    # pairs for rrc-en and 8 for rrc-zh, far too few; sampling states instead (--by-state) gives
    # hundreds. McNemar is used rather than a two-proportion test because the two conditions are
    # the same item: only the discordant pairs carry information.
    ranked_of = {"rrc-zh": "L2c", "rrc-zh-gh": "L2c"}
    paired = []
    for arm in sorted({a for a, _ in by}):
        ranked = ranked_of.get(arm, "L2")
        # pair on the state text, which is what makes the comparison matched. The state is carried
        # in every row precisely so this does not depend on a corpus file that may be rebuilt.
        st: dict = collections.defaultdict(dict)
        for r in by_items(by, arm):
            if r.get("state") is None:
                continue
            st[(r["state"], r["root"])][r["layer"]] = r
        a = [v[ranked] for v in st.values() if ranked in v and "L4" in v]
        b = [v["L4"] for v in st.values() if ranked in v and "L4" in v]
        if len(a) < 20:
            continue
        ka = sum(1 for r in a if r["correct"])
        kb = sum(1 for r in b if r["correct"])
        b01 = sum(1 for x, y in zip(a, b) if not x["correct"] and y["correct"])
        b10 = sum(1 for x, y in zip(a, b) if x["correct"] and not y["correct"])
        chi = ((abs(b10 - b01) - 1) ** 2 / (b10 + b01)) if (b10 + b01) else None
        lo1, hi1 = wilson(ka, len(a))
        lo2, hi2 = wilson(kb, len(b))
        pra = sorted(r["p_root"] for r in a if r.get("p_root") is not None)
        prb = sorted(r["p_root"] for r in b if r.get("p_root") is not None)
        paired.append({
            "arm": arm, "ranked_layer": ranked, "n_pairs": len(a),
            "ranked_acc": round(ka / len(a), 4), "ranked_ci95": [round(lo1, 4), round(hi1, 4)],
            "L4_acc": round(kb / len(b), 4), "L4_ci95": [round(lo2, 4), round(hi2, 4)],
            "drop": round(kb / len(b) - ka / len(a), 4),
            "mcnemar_b10": b10, "mcnemar_b01": b01,
            "mcnemar_chi2": None if chi is None else round(chi, 3),
            "significant": None if chi is None else chi > 3.84,
            "ranked_p_root_median": round(statistics.median(pra), 4) if pra else None,
            "L4_p_root_median": round(statistics.median(prb), 4) if prb else None,
        })
    paired.sort(key=lambda p: -p["drop"])
    print("  paired ranked-vs-L4 rows: %d (%d significant at 0.05)"
          % (len(paired), sum(1 for p in paired if p["significant"])))

    # ---- 4. position diagnostics: the readout must not be about the option slot
    pos = []
    for arm in sorted({a for a, _ in by}):
        c: collections.Counter = collections.Counter()
        tot = 0
        for r in by_items(by, arm):
            pair = cands.get(r["item_id"])
            if not pair:
                continue
            cl, _ = pair
            if r["picked"] in cl:
                c[cl.index(r["picked"])] += 1
                tot += 1
        if not tot:
            continue
        dist = {i: round(c[i] / tot, 4) for i in range(K)}
        pos.append({"arm": arm, "n": tot, "distribution": dist,
                    "max_share": round(max(dist.values()), 4),
                    "expected": round(chance, 4),
                    "verdict": ("no bias" if max(dist.values()) < 0.40
                                else "POSITION BIAS -- accuracy is about the layout")})
    print("  position rows: %d" % len(pos))

    # ---- 5. RRC's own cardinality, so the report's counts come from one place too
    rrc = {}
    for p in sorted(RRC.glob("*.jsonl")):
        lay: collections.Counter = collections.Counter()
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                lay[json.loads(line)["layer"]] += 1
        rrc[p.stem] = {"n": sum(lay.values()), "layers": dict(sorted(lay.items()))}

    # The run's own reported throughput, when the summary recorded it. Not derived from the log:
    # a rate retyped from a log is a second copy of a number that already exists in an artefact.
    rate = {}
    for cand in (OUT / ("rrc_d1_summary%s.json" % args.rows), OUT / "rrc_d1_summary.json"):
        if cand.exists() and not rate:
            try:
                s = json.loads(cand.read_text(encoding="utf-8"))
                if s.get("rate"):
                    rate = dict(s["rate"])
                    rate["source_file"] = cand.name
                    rate["sampling"] = s.get("sampling")
                    rate["by_state"] = s.get("by_state")
                    rate["per_rank"] = s.get("per_rank")
            except Exception:  # noqa: BLE001
                pass

    # The rank curve and the arm's frequency preference, taken from the run's own summary rather
    # than recomputed here: rank and its source are properties of the measurement, and a second
    # implementation of the same quantity is a second thing that can disagree.
    f2 = []
    pref = {}
    for cand in (OUT / ("rrc_d1_summary%s.json" % args.rows), OUT / "rrc_d1_summary.json"):
        if cand.exists() and not f2:
            try:
                s = json.loads(cand.read_text(encoding="utf-8"))
                f2 = s.get("f2_rank_effect") or []
                pref = s.get("candidate_preference") or {}
            except Exception:  # noqa: BLE001
                pass

    payload = {
        "generated_by": "scripts/analyze_measurement.py",
        "rows_files": src, "n_rows": len(rows), "n_options": K, "chance": round(chance, 4),
        "instrument": "LiquidAI/d1-3B (native, bfloat16, offline)",
        "rate": rate,
        "f2_rank_effect": f2,
        "candidate_preference": (candidate_preference(rows) or pref),
        "state_displacement": state_displacement(rows),
        "margin_effect": margin_effect(rows),
        "accuracy": acc_table,
        "p_root": proot,
        "L4_to_L1_drop": drop,
        "cross_arm_L4": cross,
        "paired_ranked_vs_L4": paired,
        "position_diagnostic": pos,
        "rrc_cardinality": rrc,
        "interpretation_note": (
            "p_root is the probability assigned to the correct candidate and p_max the probability "
            "assigned to whichever candidate was chosen. A silent failure is the pair (low p_root, "
            "high p_max): wrong and confident on the same trial. Accuracy alone cannot show it."),
    }
    path = OUT / ("measurement_report%s.json" % (args.out or args.rows))
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print()
    print("  wrote %s (%s bytes)" % (path, f"{path.stat().st_size:,}"))
    print()
    print("  ══ L4 -> L1 within an arm (usable only where the lengths overlap) ══")
    for d in drop:
        print("    %-12s L4 %.3f -> L1 %.3f   drop %+.3f  z=%s  |  len overlap %d  %s"
              % (d["arm"], d["L4_acc"], d["L1_acc"], d["acc_drop"],
                 "n/a" if d["z_L4_vs_L1"] is None else "%+.1f" % d["z_L4_vs_L1"],
                 d["len_overlap_tokens"], "USABLE" if d["contrast_usable"] else "<-- NOT USABLE"))
    print()
    print("  ══ cross-arm pairs on L4 (same decoy rule, comparable lengths) ══")
    for c in cross[:8]:
        print("    %-12s %.3f  vs  %-12s %.3f   diff %+.3f  z=%s %s"
              % (c["a"], c["a_acc"], c["b"], c["b_acc"], c["diff"],
                 "n/a" if c["z"] is None else "%+.2f" % c["z"],
                 "SEPARATED" if c["separated"] else ""))
    print()
    print("  ══ paired ranked-vs-L4 (matched states; McNemar) ══")
    for p in paired:
        print("    %-12s %-4s %.3f [%.3f,%.3f]  vs  L4 %.3f [%.3f,%.3f]  n=%d  drop %+.3f  "
              "McNemar chi2=%s %s"
              % (p["arm"], p["ranked_layer"], p["ranked_acc"], p["ranked_ci95"][0],
                 p["ranked_ci95"][1], p["L4_acc"], p["L4_ci95"][0], p["L4_ci95"][1],
                 p["n_pairs"], p["drop"],
                 "n/a" if p["mcnemar_chi2"] is None else "%.2f" % p["mcnemar_chi2"],
                 "SIGNIFICANT" if p["significant"] else ""))
    print()
    print("  ══ position diagnostic (must be ~uniform) ══")
    for p in pos:
        print("    %-12s n=%4d max=%.3f (expected %.2f)  %s"
              % (p["arm"], p["n"], p["max_share"], p["expected"], p["verdict"]))
    return 0


def by_items(by, arm):
    out = []
    for (a, _), rs in by.items():
        if a == arm:
            out += rs
    return out


if __name__ == "__main__":
    sys.exit(main())
